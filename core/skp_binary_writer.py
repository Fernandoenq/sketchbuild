"""
SketchBuild - Gravador Binário Nativo de Arquivos .SKP (Pure Python / Zero DLL)

Permite atualizar transformações espaciais 4x4 de instâncias, cores e materiais PBR,
e empacotar/gravar arquivos .skp nativos sem requerer a SketchUpAPI.dll ou o SketchUp Desktop.

Descobertas e Regras de Serialização:
- Tag 0x1966 (104 bytes, 13 doubles): Registro de transformação afim 4x4 da ComponentInstance.
  Modificações in-place de 104 bytes preservam a estrutura exata do 'model.dat' sem alterar
  nenhum offset de faces, vértices, planos ou loops.
- materials/*/material.xml: Cores RGB (0-255) e opacidade são serializadas nos atributos
  'colorRed', 'colorGreen', 'colorBlue' e 'trans' do elemento <mat:material>.
- Container ZIP: O arquivo .skp é reconstruído com compressão Deflate padrão (zlib), mantendo
  todos os metadados, estilos e miniaturas originais.
"""

from __future__ import annotations

import io
import os
import re
import struct
import zipfile
import zlib
from typing import Dict, List, Optional, Tuple, Any

from app.domain.exceptions import (
    InvalidModelPathError,
    ModelFileNotFoundError,
    SceneOverwriteConfirmationRequiredError,
    SceneSessionError,
)
from core.skp_binary_reader import SkpBinaryReader


class SkpBinarySession:
    """Sessão de edição ativa em memória para o leitor/gravador binário nativo."""

    def __init__(
        self,
        file_path: Optional[str],
        raw_zip_data: bytes,
        model_bytes: bytearray,
        instances_offsets: Dict[str, int],
    ):
        self.model_path: Optional[str] = file_path
        self.raw_zip_data: bytes = raw_zip_data
        self.model_bytes: bytearray = model_bytes
        self.instances_offsets: Dict[str, int] = instances_offsets
        self.modified_materials: Dict[str, Dict[str, Any]] = {}
        self.is_dirty: bool = False

    def close(self) -> None:
        self.raw_zip_data = b""
        self.model_bytes = bytearray()
        self.instances_offsets.clear()
        self.modified_materials.clear()
        self.is_dirty = False


class SkpBinaryWriter:
    """Gerenciador de gravação e serialização de arquivos .skp nativos."""

    _ACTIVE_SESSION: Optional[SkpBinarySession] = None

    @classmethod
    def get_session(cls) -> Optional[SkpBinarySession]:
        return cls._ACTIVE_SESSION

    @classmethod
    def open_session(cls, file_path: str) -> SkpBinarySession:
        """Inicializa uma sessão binária a partir de um arquivo .skp existente."""
        if not file_path or not os.path.exists(file_path):
            raise ModelFileNotFoundError(f"arquivo .skp nao encontrado: {file_path}")

        try:
            with open(file_path, "rb") as f:
                raw_zip_data = f.read()
        except OSError as e:
            raise ModelFileNotFoundError(f"falha ao ler {file_path}: {e}") from e

        model_bytes_raw = SkpBinaryReader._extract_model_dat(raw_zip_data)
        if not model_bytes_raw:
            raise SceneSessionError("não foi possível extrair o stream 'model.dat' do arquivo .skp")

        model_bytes = bytearray(model_bytes_raw)
        hierarchy = SkpBinaryReader._parse_hierarchy(bytes(model_bytes))

        instances_offsets: Dict[str, int] = {}
        for idx, inst in enumerate(hierarchy["instances"]):
            inst_id = f"inst_{idx}_{inst['definition_name']}"
            if "offset" in inst:
                instances_offsets[inst_id] = inst["offset"]

        session = SkpBinarySession(
            file_path=file_path,
            raw_zip_data=raw_zip_data,
            model_bytes=model_bytes,
            instances_offsets=instances_offsets,
        )
        cls._ACTIVE_SESSION = session
        return session

    @classmethod
    def set_instance_transform(
        cls, instance_id: str, transform_16: List[float]
    ) -> None:
        """Aplica uma nova matriz 4x4 column-major diretamente nos 104 bytes da Tag 0x1966 em memória."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        if instance_id == "inst_root":
            # inst_root é a pseudo-instância sintética da raiz do modelo
            return

        offset = session.instances_offsets.get(instance_id)
        if offset is None:
            raise SceneSessionError(f"instância {instance_id!r} não encontrada na sessão binária")

        if len(transform_16) < 16:
            raise SceneSessionError("matriz de transformação inválida (esperados 16 floats)")

        # Converte a matriz 4x4 column-major para os 13 doubles da Tag 0x1966:
        # [ m0, m1, m2,  m4, m5, m6,  m8, m9, m10,  tx_in, ty_in, tz_in, m15 ]
        raw_13d = [
            float(transform_16[0]),
            float(transform_16[1]),
            float(transform_16[2]),
            float(transform_16[4]),
            float(transform_16[5]),
            float(transform_16[6]),
            float(transform_16[8]),
            float(transform_16[9]),
            float(transform_16[10]),
            float(transform_16[12]),  # translação X em polegadas
            float(transform_16[13]),  # translação Y em polegadas
            float(transform_16[14]),  # translação Z em polegadas
            float(transform_16[15]) if abs(transform_16[15]) > 1e-6 else 1.0,
        ]

        # Tag 0x1966 tem 6 bytes de prefixo: \x66\x19\x68\x00\x00\x00
        # Os 13 doubles começam exatamente no offset + 6
        struct.pack_into("<13d", session.model_bytes, offset + 6, *raw_13d)
        session.is_dirty = True

    @classmethod
    def paint_material(
        cls, material_name: str, r: int, g: int, b: int, opacity: float = 1.0
    ) -> None:
        """Registra a alteração de cor RGB / opacidade para um material existente ou novo."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        cls._ACTIVE_SESSION.modified_materials[material_name] = {
            "r": max(0, min(255, int(r))),
            "g": max(0, min(255, int(g))),
            "b": max(0, min(255, int(b))),
            "opacity": max(0.0, min(1.0, float(opacity))),
        }
        cls._ACTIVE_SESSION.is_dirty = True

    @classmethod
    def save_session(
        cls,
        target_path: Optional[str] = None,
        overwrite_confirmed: bool = False,
    ) -> str:
        """Serializa e grava o arquivo .skp nativo com o model.dat e materiais atualizados."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        path = target_path or session.model_path
        if not path:
            raise SceneSessionError("caminho de destino não informado para gravação")

        # Trava de confirmação contra sobrescrita acidental de arquivo existente alheio
        if (
            not overwrite_confirmed
            and path != session.model_path
            and os.path.exists(path)
        ):
            size = os.path.getsize(path)
            raise SceneOverwriteConfirmationRequiredError(
                f"o arquivo {path!r} ja existe ({size} bytes). Confirmar sobrescrita?",
                existing_path=path,
                existing_size_bytes=size,
            )

        # Gravação atômica via arquivo temporário
        tmp_target = path + ".tmp"
        try:
            with io.BytesIO(session.raw_zip_data) as zip_buffer_in:
                with zipfile.ZipFile(zip_buffer_in, "r") as zin:
                    with zipfile.ZipFile(tmp_target, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                        for item in zin.infolist():
                            fname = item.filename
                            if fname == "model.dat":
                                # Grava o model.dat atualizado em memória
                                zout.writestr(item, bytes(session.model_bytes))
                            elif fname.startswith("materials/") and fname.endswith("/material.xml"):
                                # Checa se o material foi modificado
                                mat_name = fname.split("/")[1]
                                if mat_name in session.modified_materials:
                                    xml_bytes = zin.read(fname)
                                    xml_text = xml_bytes.decode("utf-8", errors="replace")
                                    mod = session.modified_materials[mat_name]
                                    # Atualiza atributos via regex mantendo namespaces e estrutura exata
                                    xml_text = re.sub(r'colorRed="[^"]*"', f'colorRed="{mod["r"]}"', xml_text)
                                    xml_text = re.sub(r'colorGreen="[^"]*"', f'colorGreen="{mod["g"]}"', xml_text)
                                    xml_text = re.sub(r'colorBlue="[^"]*"', f'colorBlue="{mod["b"]}"', xml_text)
                                    xml_text = re.sub(r'trans="[^"]*"', f'trans="{mod["opacity"]}"', xml_text)
                                    zout.writestr(item, xml_text.encode("utf-8"))
                                else:
                                    zout.writestr(item, zin.read(fname))
                            else:
                                # Copia outros assets intactos (texturas, thumbnails, etc.)
                                zout.writestr(item, zin.read(fname))

            # Substitui de forma atômica
            if os.path.exists(path):
                os.replace(tmp_target, path)
            else:
                os.rename(tmp_target, path)

            # Atualiza o raw_zip_data em memória para o novo arquivo salvo
            with open(path, "rb") as f:
                session.raw_zip_data = f.read()

            session.model_path = path
            session.is_dirty = False
            return path
        except Exception as e:
            if os.path.exists(tmp_target):
                try:
                    os.remove(tmp_target)
                except OSError:
                    pass
            raise SceneSessionError(f"falha ao serializar o arquivo .skp: {e}") from e

    @classmethod
    def close_session(cls) -> None:
        if cls._ACTIVE_SESSION is not None:
            cls._ACTIVE_SESSION.close()
            cls._ACTIVE_SESSION = None
