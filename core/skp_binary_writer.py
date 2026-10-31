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
import math
import os
import re
import struct
import uuid
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
        camera_offset: Optional[int] = None,
        tags_offsets: Optional[Dict[str, int]] = None,
        scenes: Optional[List[Dict[str, Any]]] = None,
        active_scene_offset: Optional[int] = None,
        skp_prefix: bytes = b"",
    ):
        self.model_path: Optional[str] = file_path
        self.raw_zip_data: bytes = raw_zip_data
        self.model_bytes: bytearray = model_bytes
        self.instances_offsets: Dict[str, int] = instances_offsets
        self.camera_offset: Optional[int] = camera_offset
        self.tags_offsets: Dict[str, int] = tags_offsets or {}
        self.scenes: List[Dict[str, Any]] = scenes or []
        self.active_scene_offset: Optional[int] = active_scene_offset
        self.skp_prefix: bytes = skp_prefix
        self.modified_materials: Dict[str, Dict[str, Any]] = {}
        self.is_dirty: bool = False
        self.custom_zip_files: Dict[str, bytes] = {}
        self.section_planes: List[Dict[str, Any]] = []
        self.guide_lines: List[Dict[str, Any]] = []
        self.guide_points: List[Dict[str, Any]] = []

    def close(self) -> None:
        self.raw_zip_data = b""
        self.skp_prefix = b""
        self.model_bytes = bytearray()
        self.instances_offsets.clear()
        self.tags_offsets.clear()
        self.scenes.clear()
        self.camera_offset = None
        self.active_scene_offset = None
        self.modified_materials.clear()
        self.section_planes.clear()
        self.guide_lines.clear()
        self.guide_points.clear()
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
                raw_file_data = f.read()
        except OSError as e:
            raise ModelFileNotFoundError(f"falha ao ler {file_path}: {e}") from e

        pk_pos = raw_file_data.find(b"PK\x03\x04")
        if pk_pos != -1:
            skp_prefix = raw_file_data[:pk_pos]
            raw_zip_data = raw_file_data[pk_pos:]
        else:
            skp_prefix = b""
            raw_zip_data = raw_file_data

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

        # Extrai a câmera real e seus offsets
        camera_dto = SkpBinaryReader._parse_camera(bytes(model_bytes))
        camera_offset = camera_dto.get("offset") if camera_dto else None

        # Mapeia offsets de visibilidade das Tags (Tag 0x3c8e)
        tags_offsets: Dict[str, int] = {}
        idx = 0
        buf = bytes(model_bytes)
        buf_len = len(buf)
        while True:
            p_name = buf.find(SkpBinaryReader.TAG_LAYER_NAME, idx)
            if p_name == -1 or p_name + 6 > buf_len:
                break
            slen = struct.unpack_from("<I", buf, p_name + 2)[0]
            if 1 <= slen <= 120 and p_name + 6 + slen <= buf_len:
                tname = buf[p_name + 6 : p_name + 6 + slen].decode("utf-8", errors="replace").strip("\x00").strip()
                p_vis = buf.find(SkpBinaryReader.TAG_LAYER_VISIBILITY, p_name + 6 + slen, min(buf_len, p_name + 6 + slen + 50))
                if p_vis != -1 and tname:
                    tags_offsets[tname] = p_vis + 6
            idx = p_name + 1

        # Cenas e Cena Ativa (Tag 0x7148 e Tag 0x6d62)
        scenes = SkpBinaryReader._parse_scenes(bytes(model_bytes))
        p_act = model_bytes.find(SkpBinaryReader.TAG_SCENE_ACTIVE_EID)
        active_scene_offset = p_act if p_act != -1 else None

        session = SkpBinarySession(
            file_path=file_path,
            raw_zip_data=raw_zip_data,
            model_bytes=model_bytes,
            instances_offsets=instances_offsets,
            camera_offset=camera_offset,
            tags_offsets=tags_offsets,
            scenes=scenes,
            active_scene_offset=active_scene_offset,
            skp_prefix=skp_prefix,
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
    def duplicate_instance(
        cls,
        instance_id: str,
        new_transform_16: Optional[List[float]] = None,
        offset_delta_cm: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Duplica nativamente uma ComponentInstance existente no model.dat (Pure Python / Zero DLL).

        Gera novo EntityID livre, novo GUID binário, aplica a nova matriz 4x4, insere o bloco
        no contêiner Tag 0x138c, registra o novo EntityID na Tag 0x138e, atualiza o BoundingBox
        na Tag 0x13a0 e os contêineres pais (Tag 0x1388, Tag 0x01f6 e Tag 0x01f4).
        """
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        if instance_id == "inst_root":
            raise SceneSessionError("a raiz do modelo ('inst_root') não pode ser duplicada")

        # 1. Encontra o offset da instância
        offset = session.instances_offsets.get(instance_id)
        if offset is None:
            # Tenta busca por ID numérico ou correspondência parcial
            for key, off in session.instances_offsets.items():
                if key == instance_id or key.startswith(f"inst_{instance_id}_") or key.endswith(f"_{instance_id}"):
                    offset = off
                    instance_id = key
                    break

        if offset is None:
            raise SceneSessionError(f"instância {instance_id!r} não encontrada na sessão binária")

        mb = session.model_bytes

        # 2. Localiza o contêiner mestre da instância (Tag 0x1964)
        p_c64 = mb.rfind(b"\x64\x19", max(0, offset - 400), offset)
        if p_c64 == -1:
            raise SceneSessionError(f"contêiner binário Tag 0x1964 não localizado para {instance_id!r}")

        c64_len = struct.unpack_from("<I", mb, p_c64 + 2)[0]
        c64_total = 6 + c64_len
        inst_block = bytearray(mb[p_c64 : p_c64 + c64_total])

        # 3. Mapeia todos os EntityIDs existentes para garantir unicidade absoluta
        all_eids = set()
        p = 0
        mb_len = len(mb)
        while p + 6 <= mb_len:
            p_de = mb.find(b"\xde\x05", p)
            if p_de == -1:
                break
            l = struct.unpack_from("<I", mb, p_de + 2)[0]
            if 1 <= l <= 8 and p_de + 6 + l <= mb_len:
                eid_val = int.from_bytes(mb[p_de + 6 : p_de + 6 + l], "little")
                all_eids.add(eid_val)
            p = p_de + 1

        # Localiza o EntityID da instância no inst_block
        p_de_local = inst_block.find(b"\xde\x05")
        if p_de_local == -1:
            raise SceneSessionError("Tag 0x05de (EntityID) não encontrada no bloco da instância")

        eid_len = struct.unpack_from("<I", inst_block, p_de_local + 2)[0]

        # Escolhe um novo EntityID livre mantendo o mesmo comprimento em bytes
        if eid_len == 2:
            free_ids = [x for x in range(45100, 65535) if x not in all_eids]
            if free_ids:
                new_eid = free_ids[0]
            else:
                new_eid = max(all_eids, default=50000) + 1
                eid_len = 4
        else:
            new_eid = max(all_eids, default=50000) + 1

        new_eid_bytes = new_eid.to_bytes(eid_len, "little")
        inst_block[p_de_local + 6 : p_de_local + 6 + eid_len] = new_eid_bytes

        # 4. Atribui novo GUID binário de 16 bytes (Tag 0x1968)
        p_guid = inst_block.find(b"\x68\x19\x10\x00\x00\x00")
        if p_guid != -1:
            inst_block[p_guid + 6 : p_guid + 22] = uuid.uuid4().bytes

        # 5. Configura a nova transformação 4x4 (Tag 0x1966)
        p_tr_clone = inst_block.find(b"\x66\x19\x68\x00\x00\x00")
        if p_tr_clone == -1:
            raise SceneSessionError("Tag 0x1966 não encontrada no bloco clonado da instância")

        raw_13d = list(struct.unpack_from("<13d", inst_block, p_tr_clone + 6))
        if new_transform_16 and len(new_transform_16) >= 16:
            raw_13d = [
                float(new_transform_16[0]), float(new_transform_16[1]), float(new_transform_16[2]),
                float(new_transform_16[4]), float(new_transform_16[5]), float(new_transform_16[6]),
                float(new_transform_16[8]), float(new_transform_16[9]), float(new_transform_16[10]),
                float(new_transform_16[12]), float(new_transform_16[13]), float(new_transform_16[14]),
                float(new_transform_16[15]) if abs(new_transform_16[15]) > 1e-6 else 1.0,
            ]
        elif offset_delta_cm and len(offset_delta_cm) >= 3:
            raw_13d[9] += float(offset_delta_cm[0]) / 2.54
            raw_13d[10] += float(offset_delta_cm[1]) / 2.54
            raw_13d[11] += float(offset_delta_cm[2]) / 2.54
        else:
            # Deslocamento padrão: +50 cm em X (+19.685 polegadas)
            raw_13d[9] += 50.0 / 2.54

        struct.pack_into("<13d", inst_block, p_tr_clone + 6, *raw_13d)

        # 6. Localiza o contêiner de instâncias Tag 0x138c
        p_138c = mb.rfind(b"\x8c\x13", 0, p_c64)
        if p_138c == -1:
            raise SceneSessionError("contêiner de instâncias Tag 0x138c não localizado")

        old_138c_len = struct.unpack_from("<I", mb, p_138c + 2)[0]

        # 7. Inserção do novo bloco imediatamente após a instância de origem
        ins_pos = p_c64 + c64_total
        mb[ins_pos:ins_pos] = inst_block
        inst_delta = len(inst_block)

        # Atualiza comprimento de Tag 0x138c
        struct.pack_into("<I", mb, p_138c + 2, old_138c_len + inst_delta)

        # 8. Atualiza a lista de instâncias Tag 0x138e
        p_8e = mb.find(b"\x8e\x13", ins_pos)
        if p_8e == -1:
            raise SceneSessionError("vetor de instâncias Tag 0x138e não localizado")

        old_8e_len = struct.unpack_from("<I", mb, p_8e + 2)[0]
        old_8e_data = mb[p_8e + 6 : p_8e + 6 + old_8e_len]
        new_8e_item = bytes([eid_len]) + new_eid_bytes
        new_8e_data = old_8e_data + new_8e_item
        new_8e_len = len(new_8e_data)
        tag_8e_delta = new_8e_len - old_8e_len

        mb[p_8e + 6 : p_8e + 6 + old_8e_len] = new_8e_data
        struct.pack_into("<I", mb, p_8e + 2, new_8e_len)

        total_delta = inst_delta + tag_8e_delta

        # 9. Atualiza o BoundingBox na Tag 0x13a0 se presente
        p_13a0 = mb.find(b"\xa0\x13", ins_pos)
        if p_13a0 != -1:
            bbox = list(struct.unpack_from("<6d", mb, p_13a0 + 6))
            inst_x = raw_13d[9]
            inst_y = raw_13d[10]
            inst_z = raw_13d[11]
            bbox[0] = min(bbox[0], inst_x - 10.0)
            bbox[1] = min(bbox[1], inst_y - 10.0)
            bbox[2] = min(bbox[2], inst_z - 10.0)
            bbox[3] = max(bbox[3], inst_x + 10.0)
            bbox[4] = max(bbox[4], inst_y + 10.0)
            bbox[5] = max(bbox[5], inst_z + 10.0)
            struct.pack_into("<6d", mb, p_13a0 + 6, *bbox)

        # 10. Atualiza os contêineres pais superiores
        p_1388 = mb.rfind(b"\x88\x13", 0, p_138c)
        if p_1388 != -1:
            old_1388_len = struct.unpack_from("<I", mb, p_1388 + 2)[0]
            struct.pack_into("<I", mb, p_1388 + 2, old_1388_len + total_delta)

        p_01f6 = mb.rfind(b"\xf6\x01", 0, p_1388 if p_1388 != -1 else p_138c)
        if p_01f6 != -1:
            old_f6_len = struct.unpack_from("<I", mb, p_01f6 + 2)[0]
            struct.pack_into("<I", mb, p_01f6 + 2, old_f6_len + total_delta)

        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, old_f4_len + total_delta)

        # 11. Atualiza todos os offsets existentes na sessão que ficaram após o ponto de inserção
        for k, off in list(session.instances_offsets.items()):
            if off > ins_pos:
                session.instances_offsets[k] = off + total_delta

        if session.camera_offset is not None and session.camera_offset > ins_pos:
            session.camera_offset += total_delta

        for tag_name, tag_off in list(session.tags_offsets.items()):
            if tag_off > ins_pos:
                session.tags_offsets[tag_name] = tag_off + total_delta

        if session.active_scene_offset is not None and session.active_scene_offset > ins_pos:
            session.active_scene_offset += total_delta

        for s in session.scenes:
            if "offset" in s and s["offset"] > ins_pos:
                s["offset"] += total_delta

        # 12. Identifica o definition_id e nome
        p_def = inst_block.find(SkpBinaryReader.TAG_INSTANCE_DEF_REF)
        def_id = None
        if p_def != -1:
            dlen = struct.unpack_from("<I", inst_block, p_def + 2)[0]
            if 1 <= dlen <= 8:
                def_id = int.from_bytes(inst_block[p_def + 6 : p_def + 6 + dlen], "little")

        def_name = instance_id.split("_", 2)[-1] if "_" in instance_id else "Componente"

        # 13. Registra a nova instância na sessão
        new_inst_offset = ins_pos + p_tr_clone
        new_inst_key = f"inst_{len(session.instances_offsets)}_{def_name}"
        session.instances_offsets[new_inst_key] = new_inst_offset
        session.is_dirty = True

        # 14. Prepara o DTO de retorno
        tx = raw_13d[9] * 2.54
        ty = raw_13d[10] * 2.54
        tz = raw_13d[11] * 2.54
        mat_4x4 = [
            round(raw_13d[0], 6), round(raw_13d[1], 6), round(raw_13d[2], 6), 0.0,
            round(raw_13d[3], 6), round(raw_13d[4], 6), round(raw_13d[5], 6), 0.0,
            round(raw_13d[6], 6), round(raw_13d[7], 6), round(raw_13d[8], 6), 0.0,
            round(tx, 3), round(ty, 3), round(tz, 3), round(raw_13d[12], 6)
        ]
        mat_4x4_inches = [
            round(raw_13d[0], 6), round(raw_13d[1], 6), round(raw_13d[2], 6), 0.0,
            round(raw_13d[3], 6), round(raw_13d[4], 6), round(raw_13d[5], 6), 0.0,
            round(raw_13d[6], 6), round(raw_13d[7], 6), round(raw_13d[8], 6), 0.0,
            round(raw_13d[9], 4), round(raw_13d[10], 4), round(raw_13d[11], 4), round(raw_13d[12], 6)
        ]

        return {
            "id": new_eid,
            "instance_key": new_inst_key,
            "definition_id": def_id,
            "definition_name": def_name,
            "translation_cm": [round(tx, 2), round(ty, 2), round(tz, 2)],
            "matrix_4x4": mat_4x4,
            "matrix_4x4_inches": mat_4x4_inches,
            "offset": new_inst_offset,
            "attributes": {},
        }

    @classmethod
    def delete_instance(cls, instance_id: str) -> bool:
        """Exclui nativamente uma ComponentInstance existente no model.dat (Pure Python / Zero DLL).

        Remove o bloco Tag 0x1964 do contêiner Tag 0x138c, remove a referência de EntityID
        na Tag 0x138e, atualiza os comprimentos dos contêineres pais (Tag 0x138c, Tag 0x1388,
        Tag 0x01f6 e Tag 0x01f4) e reajusta com precisão todos os offsets subsequentes na sessão.
        """
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        if instance_id == "inst_root":
            raise SceneSessionError("a raiz do modelo ('inst_root') não pode ser excluída")

        # 1. Encontra o offset da instância
        offset = session.instances_offsets.get(instance_id)
        target_key = instance_id
        if offset is None:
            for key, off in session.instances_offsets.items():
                if key == instance_id or key.startswith(f"inst_{instance_id}_") or key.endswith(f"_{instance_id}"):
                    offset = off
                    target_key = key
                    break

        if offset is None:
            raise SceneSessionError(f"instância {instance_id!r} não encontrada na sessão binária")

        mb = session.model_bytes

        # 2. Localiza o contêiner mestre da instância (Tag 0x1964)
        p_c64 = mb.rfind(b"\x64\x19", max(0, offset - 400), offset)
        if p_c64 == -1:
            raise SceneSessionError(f"contêiner binário Tag 0x1964 não localizado para {instance_id!r}")

        c64_len = struct.unpack_from("<I", mb, p_c64 + 2)[0]
        c64_total = 6 + c64_len
        inst_block = mb[p_c64 : p_c64 + c64_total]

        # 3. Extrai o EntityID da instância para remoção da Tag 0x138e
        p_de = inst_block.find(b"\xde\x05")
        target_eid = None
        if p_de != -1:
            eid_len = struct.unpack_from("<I", inst_block, p_de + 2)[0]
            if 1 <= eid_len <= 8 and p_de + 6 + eid_len <= len(inst_block):
                target_eid = int.from_bytes(inst_block[p_de + 6 : p_de + 6 + eid_len], "little")

        # 4. Localiza o contêiner de instâncias Tag 0x138c
        p_138c = mb.rfind(b"\x8c\x13", 0, p_c64)
        if p_138c == -1:
            raise SceneSessionError("contêiner de instâncias Tag 0x138c não localizado")

        old_138c_len = struct.unpack_from("<I", mb, p_138c + 2)[0]

        # 5. Remove o bloco da instância fisicamente de model_bytes
        del mb[p_c64 : p_c64 + c64_total]
        inst_delta = c64_total

        # Atualiza o comprimento de Tag 0x138c
        struct.pack_into("<I", mb, p_138c + 2, max(0, old_138c_len - inst_delta))

        # 6. Localiza e atualiza o vetor de instâncias Tag 0x138e
        tag_8e_delta = 0
        p_8e = mb.find(b"\x8e\x13", p_c64)
        if p_8e != -1 and target_eid is not None:
            old_8e_len = struct.unpack_from("<I", mb, p_8e + 2)[0]
            old_8e_data = mb[p_8e + 6 : p_8e + 6 + old_8e_len]

            idx = 0
            found_offset_in_8e = -1
            item_size_in_8e = 0
            while idx < old_8e_len:
                l = old_8e_data[idx]
                if idx + 1 + l > old_8e_len:
                    break
                val = int.from_bytes(old_8e_data[idx + 1 : idx + 1 + l], "little")
                if val == target_eid:
                    found_offset_in_8e = idx
                    item_size_in_8e = 1 + l
                    break
                idx += 1 + l

            if found_offset_in_8e != -1:
                new_8e_data = old_8e_data[:found_offset_in_8e] + old_8e_data[found_offset_in_8e + item_size_in_8e :]
                new_8e_len = len(new_8e_data)
                tag_8e_delta = item_size_in_8e
                mb[p_8e + 6 : p_8e + 6 + old_8e_len] = new_8e_data
                struct.pack_into("<I", mb, p_8e + 2, new_8e_len)

        total_delta = inst_delta + tag_8e_delta

        # 7. Atualiza os contêineres pais superiores
        p_1388 = mb.rfind(b"\x88\x13", 0, p_138c)
        if p_1388 != -1:
            old_1388_len = struct.unpack_from("<I", mb, p_1388 + 2)[0]
            struct.pack_into("<I", mb, p_1388 + 2, max(0, old_1388_len - total_delta))

        p_01f6 = mb.rfind(b"\xf6\x01", 0, p_1388 if p_1388 != -1 else p_138c)
        if p_01f6 != -1:
            old_f6_len = struct.unpack_from("<I", mb, p_01f6 + 2)[0]
            struct.pack_into("<I", mb, p_01f6 + 2, max(0, old_f6_len - total_delta))

        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, max(0, old_f4_len - total_delta))

        # 8. Remove a instância da sessão
        del session.instances_offsets[target_key]

        # 9. Reajusta offsets na sessão
        def adjust_offset(pos: Optional[int]) -> Optional[int]:
            if pos is None:
                return None
            if p_8e != -1 and pos > p_8e:
                return pos - total_delta
            elif pos > p_c64:
                return pos - inst_delta
            return pos

        for k in list(session.instances_offsets.keys()):
            session.instances_offsets[k] = adjust_offset(session.instances_offsets[k])

        if session.camera_offset is not None:
            session.camera_offset = adjust_offset(session.camera_offset)

        for t in list(session.tags_offsets.keys()):
            session.tags_offsets[t] = adjust_offset(session.tags_offsets[t])

        if session.active_scene_offset is not None:
            session.active_scene_offset = adjust_offset(session.active_scene_offset)

        for s in session.scenes:
            if "offset" in s:
                s["offset"] = adjust_offset(s["offset"])

        session.is_dirty = True
        return True

    @classmethod
    def add_rectangle(
        cls,
        width_m: float,
        height_m: float,
        offset_xyz_cm: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Cria nativamente uma Face retangular plana no model.dat (Pure Python / Zero DLL).

        Gera os 4 vértices (Tag 0x09c4 dentro de Tag 0x1389), as 4 arestas (Tag 0x0bb8 dentro de
        Tag 0x138a), e a Face com seu plano afim (Tag 0x0dad) e loop orientado (Tag 0x0dae dentro de
        Tag 0x138b), atualizando a Tag 0x138e e contêineres superiores.
        """
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        # Dimensões e pontos em polegadas
        w_in = (float(width_m) * 100.0) / 2.54
        h_in = (float(height_m) * 100.0) / 2.54

        ox_in = (float(offset_xyz_cm[0]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 1 else 0.0
        oy_in = (float(offset_xyz_cm[1]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 2 else 0.0
        oz_in = (float(offset_xyz_cm[2]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 3 else 0.0

        pts = [
            (ox_in, oy_in, oz_in),
            (ox_in + w_in, oy_in, oz_in),
            (ox_in + w_in, oy_in + h_in, oz_in),
            (ox_in, oy_in + h_in, oz_in),
        ]

        # Alocação de novos EntityIDs
        all_eids = set()
        p = 0
        mb_len = len(mb)
        while p + 6 <= mb_len:
            p_de = mb.find(b"\xde\x05", p)
            if p_de == -1:
                break
            l = struct.unpack_from("<I", mb, p_de + 2)[0]
            if 1 <= l <= 8 and p_de + 6 + l <= mb_len:
                all_eids.add(int.from_bytes(mb[p_de + 6 : p_de + 6 + l], "little"))
            p = p_de + 1

        cur_eid = max(all_eids, default=50000)

        def alloc_eid() -> int:
            nonlocal cur_eid
            cur_eid += 1
            while cur_eid in all_eids:
                cur_eid += 1
            all_eids.add(cur_eid)
            return cur_eid

        v_ids = [alloc_eid() for _ in range(4)]
        e_ids = [alloc_eid() for _ in range(4)]
        f_id = alloc_eid()

        # 1. Bloco de Vértices (Tag 0x1389)
        v_payload = bytearray()
        for i in range(4):
            eid_bytes = v_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            pt_tag = b"\xc5\t\x18\x00\x00\x00" + struct.pack("<3d", *pts[i])
            c4_payload = dc_tag + pt_tag
            c4_tag = b"\xc4\t" + struct.pack("<I", len(c4_payload)) + c4_payload
            v_payload.extend(c4_tag)
        tag_1389 = b"\x89\x13" + struct.pack("<I", len(v_payload)) + v_payload

        # 2. Bloco de Arestas (Tag 0x138a)
        e_payload = bytearray()
        for i in range(4):
            v_start = v_ids[i]
            v_end = v_ids[(i + 1) % 4]
            eid_bytes = e_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
            d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload
            b9_tag = b"\xb9\x0b\x04\x00\x00\x00" + v_start.to_bytes(4, "little")
            ba_tag = b"\xba\x0b\x04\x00\x00\x00" + v_end.to_bytes(4, "little")
            b8_payload = d0_tag + b9_tag + ba_tag
            b8_tag = b"\xb8\x0b" + struct.pack("<I", len(b8_payload)) + b8_payload
            e_payload.extend(b8_tag)
        tag_138a = b"\x8a\x13" + struct.pack("<I", len(e_payload)) + e_payload

        # 3. Bloco de Face (Tag 0x138b)
        eid_bytes = f_id.to_bytes(4, "little")
        eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
        dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
        d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
        d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload

        # Equação do plano: normal (0, 0, 1), D = -oz_in
        dad_tag = b"\xad\x0d\x20\x00\x00\x00" + struct.pack("<4d", 0.0, 0.0, 1.0, -oz_in)

        edge_uses = bytearray()
        for i in range(4):
            fa1 = b"\xa1\x0f\x04\x00\x00\x00" + e_ids[i].to_bytes(4, "little")
            fa2 = b"\xa2\x0f\x01\x00\x00\x00\x00"
            fa0_payload = fa1 + fa2
            fa0_tag = b"\xa0\x0f" + struct.pack("<I", len(fa0_payload)) + fa0_payload
            edge_uses.extend(fa0_tag)

        tag_1195_payload = edge_uses
        tag_1195 = b"\x95\x11" + struct.pack("<I", len(tag_1195_payload)) + tag_1195_payload
        tag_1194 = b"\x94\x11" + struct.pack("<I", len(tag_1195)) + tag_1195
        dae_tag = b"\xae\x0d" + struct.pack("<I", len(tag_1194)) + tag_1194

        ac0d_payload = d0_tag + dad_tag + dae_tag
        ac0d_tag = b"\xac\r" + struct.pack("<I", len(ac0d_payload)) + ac0d_payload
        tag_138b = b"\x8b\x13" + struct.pack("<I", len(ac0d_tag)) + ac0d_tag

        geom_block = tag_1389 + tag_138a + tag_138b
        geom_delta = len(geom_block)

        # 4. Inserção antes da Tag 0x138c
        p_138c = mb.find(b"\x8c\x13")
        if p_138c == -1:
            raise SceneSessionError("contêiner de instâncias Tag 0x138c não localizado")

        ins_pos = p_138c
        mb[ins_pos:ins_pos] = geom_block

        # 5. Adiciona referências na Tag 0x138e (as 4 arestas e a face)
        p_8e = mb.find(b"\x8e\x13", ins_pos + geom_delta)
        tag_8e_delta = 0
        if p_8e != -1:
            old_8e_len = struct.unpack_from("<I", mb, p_8e + 2)[0]
            old_8e_data = mb[p_8e + 6 : p_8e + 6 + old_8e_len]
            new_entries = bytearray()
            for eid in e_ids + [f_id]:
                new_entries.append(4)
                new_entries.extend(eid.to_bytes(4, "little"))
            new_8e_data = old_8e_data + new_entries
            tag_8e_delta = len(new_entries)
            mb[p_8e + 6 : p_8e + 6 + old_8e_len] = new_8e_data
            struct.pack_into("<I", mb, p_8e + 2, len(new_8e_data))

        total_delta = geom_delta + tag_8e_delta

        # 6. Atualiza os contêineres pais superiores
        p_1388 = mb.rfind(b"\x88\x13", 0, ins_pos)
        if p_1388 != -1:
            old_1388_len = struct.unpack_from("<I", mb, p_1388 + 2)[0]
            struct.pack_into("<I", mb, p_1388 + 2, old_1388_len + total_delta)

        p_01f6 = mb.rfind(b"\xf6\x01", 0, p_1388 if p_1388 != -1 else ins_pos)
        if p_01f6 != -1:
            old_f6_len = struct.unpack_from("<I", mb, p_01f6 + 2)[0]
            struct.pack_into("<I", mb, p_01f6 + 2, old_f6_len + total_delta)

        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, old_f4_len + total_delta)

        # 7. Reajusta offsets na sessão
        for k, off in list(session.instances_offsets.items()):
            if off > ins_pos:
                session.instances_offsets[k] = off + total_delta

        if session.camera_offset is not None and session.camera_offset > ins_pos:
            session.camera_offset += total_delta

        for t, toff in list(session.tags_offsets.items()):
            if toff > ins_pos:
                session.tags_offsets[t] = toff + total_delta

        if session.active_scene_offset is not None and session.active_scene_offset > ins_pos:
            session.active_scene_offset += total_delta

        for s in session.scenes:
            if "offset" in s and s["offset"] > ins_pos:
                s["offset"] += total_delta

        session.is_dirty = True

        pts_cm = [[round(p[0] * 2.54, 2), round(p[1] * 2.54, 2), round(p[2] * 2.54, 2)] for p in pts]
        return {
            "face_id": f_id,
            "vertex_ids": v_ids,
            "edge_ids": e_ids,
            "points_cm": pts_cm,
            "width_m": float(width_m),
            "height_m": float(height_m),
            "area_m2": round(float(width_m) * float(height_m), 4),
            "plane": [0.0, 0.0, 1.0, round(-oz_in, 4)],
        }

    @classmethod
    def add_box(
        cls,
        width_m: float,
        length_m: float,
        height_m: float,
        offset_xyz_cm: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Cria nativamente um Sólido 3D Manifold (Paralelepípedo / Push-Pull) no model.dat (Zero DLL).

        Gera os 8 vértices (Tag 0x09c4 em Tag 0x1389), as 12 arestas (Tag 0x0bb8 em Tag 0x138a),
        e as 6 faces orientadas com seus planos analíticos e loops de EdgeUses (Tag 0x138b),
        atualizando a Tag 0x138e e todos os contêineres pais superiores.
        """
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        w_in = (float(width_m) * 100.0) / 2.54
        l_in = (float(length_m) * 100.0) / 2.54
        h_in = (float(height_m) * 100.0) / 2.54

        ox = (float(offset_xyz_cm[0]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 1 else 0.0
        oy = (float(offset_xyz_cm[1]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 2 else 0.0
        oz = (float(offset_xyz_cm[2]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 3 else 0.0

        pts = [
            (ox, oy, oz),               # V0
            (ox + w_in, oy, oz),        # V1
            (ox + w_in, oy + l_in, oz), # V2
            (ox, oy + l_in, oz),        # V3
            (ox, oy, oz + h_in),        # V4
            (ox + w_in, oy, oz + h_in), # V5
            (ox + w_in, oy + l_in, oz + h_in), # V6
            (ox, oy + l_in, oz + h_in), # V7
        ]

        all_eids = set()
        p = 0
        mb_len = len(mb)
        while p + 6 <= mb_len:
            p_de = mb.find(b"\xde\x05", p)
            if p_de == -1:
                break
            l = struct.unpack_from("<I", mb, p_de + 2)[0]
            if 1 <= l <= 8 and p_de + 6 + l <= mb_len:
                all_eids.add(int.from_bytes(mb[p_de + 6 : p_de + 6 + l], "little"))
            p = p_de + 1

        cur_eid = max(all_eids, default=50000)
        def alloc_eid() -> int:
            nonlocal cur_eid
            cur_eid += 1
            while cur_eid in all_eids:
                cur_eid += 1
            all_eids.add(cur_eid)
            return cur_eid

        v_ids = [alloc_eid() for _ in range(8)]
        e_ids = [alloc_eid() for _ in range(12)]
        f_ids = [alloc_eid() for _ in range(6)]

        # 1. Vértices
        v_payload = bytearray()
        for i in range(8):
            eid_bytes = v_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            pt_tag = b"\xc5\t\x18\x00\x00\x00" + struct.pack("<3d", *pts[i])
            c4_payload = dc_tag + pt_tag
            c4_tag = b"\xc4\t" + struct.pack("<I", len(c4_payload)) + c4_payload
            v_payload.extend(c4_tag)
        tag_1389 = b"\x89\x13" + struct.pack("<I", len(v_payload)) + v_payload

        # 2. Arestas
        edge_defs = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7),
        ]
        e_payload = bytearray()
        for i, (va, vb) in enumerate(edge_defs):
            eid_bytes = e_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
            d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload
            b9_tag = b"\xb9\x0b\x04\x00\x00\x00" + v_ids[va].to_bytes(4, "little")
            ba_tag = b"\xba\x0b\x04\x00\x00\x00" + v_ids[vb].to_bytes(4, "little")
            b8_payload = d0_tag + b9_tag + ba_tag
            b8_tag = b"\xb8\x0b" + struct.pack("<I", len(b8_payload)) + b8_payload
            e_payload.extend(b8_tag)
        tag_138a = b"\x8a\x13" + struct.pack("<I", len(e_payload)) + e_payload

        # 3. Faces
        face_defs = [
            (0.0, 0.0, 1.0, -(oz + h_in), [(e_ids[4], 0), (e_ids[5], 0), (e_ids[6], 0), (e_ids[7], 0)]),
            (0.0, 0.0, -1.0, oz, [(e_ids[3], 1), (e_ids[2], 1), (e_ids[1], 1), (e_ids[0], 1)]),
            (0.0, -1.0, 0.0, oy, [(e_ids[0], 0), (e_ids[9], 0), (e_ids[4], 1), (e_ids[8], 1)]),
            (0.0, 1.0, 0.0, -(oy + l_in), [(e_ids[2], 0), (e_ids[11], 0), (e_ids[6], 1), (e_ids[10], 1)]),
            (-1.0, 0.0, 0.0, ox, [(e_ids[3], 0), (e_ids[8], 0), (e_ids[7], 1), (e_ids[11], 1)]),
            (1.0, 0.0, 0.0, -(ox + w_in), [(e_ids[1], 0), (e_ids[10], 0), (e_ids[5], 1), (e_ids[9], 1)]),
        ]

        f_payload = bytearray()
        for i, (nx, ny, nz, d_val, f_edges) in enumerate(face_defs):
            eid_bytes = f_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
            d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload

            dad_tag = b"\xad\x0d\x20\x00\x00\x00" + struct.pack("<4d", nx, ny, nz, d_val)

            edge_uses = bytearray()
            for edge_eid, dir_flag in f_edges:
                fa1 = b"\xa1\x0f\x04\x00\x00\x00" + edge_eid.to_bytes(4, "little")
                fa2 = b"\xa2\x0f\x01\x00\x00\x00" + (b"\x01" if dir_flag == 1 else b"\x00")
                fa0_payload = fa1 + fa2
                fa0_tag = b"\xa0\x0f" + struct.pack("<I", len(fa0_payload)) + fa0_payload
                edge_uses.extend(fa0_tag)

            tag_1195_payload = edge_uses
            tag_1195 = b"\x95\x11" + struct.pack("<I", len(tag_1195_payload)) + tag_1195_payload
            tag_1194 = b"\x94\x11" + struct.pack("<I", len(tag_1195)) + tag_1195
            dae_tag = b"\xae\x0d" + struct.pack("<I", len(tag_1194)) + tag_1194

            ac0d_payload = d0_tag + dad_tag + dae_tag
            ac0d_tag = b"\xac\r" + struct.pack("<I", len(ac0d_payload)) + ac0d_payload
            f_payload.extend(ac0d_tag)

        tag_138b = b"\x8b\x13" + struct.pack("<I", len(f_payload)) + f_payload

        geom_block = tag_1389 + tag_138a + tag_138b
        geom_delta = len(geom_block)

        p_138c = mb.find(b"\x8c\x13")
        if p_138c == -1:
            raise SceneSessionError("contêiner de instâncias Tag 0x138c não localizado")

        ins_pos = p_138c
        mb[ins_pos:ins_pos] = geom_block

        p_8e = mb.find(b"\x8e\x13", ins_pos + geom_delta)
        tag_8e_delta = 0
        if p_8e != -1:
            old_8e_len = struct.unpack_from("<I", mb, p_8e + 2)[0]
            old_8e_data = mb[p_8e + 6 : p_8e + 6 + old_8e_len]
            new_entries = bytearray()
            for eid in e_ids + f_ids:
                new_entries.append(4)
                new_entries.extend(eid.to_bytes(4, "little"))
            new_8e_data = old_8e_data + new_entries
            tag_8e_delta = len(new_entries)
            mb[p_8e + 6 : p_8e + 6 + old_8e_len] = new_8e_data
            struct.pack_into("<I", mb, p_8e + 2, len(new_8e_data))

        total_delta = geom_delta + tag_8e_delta

        p_1388 = mb.rfind(b"\x88\x13", 0, ins_pos)
        if p_1388 != -1:
            old_1388_len = struct.unpack_from("<I", mb, p_1388 + 2)[0]
            struct.pack_into("<I", mb, p_1388 + 2, old_1388_len + total_delta)

        p_01f6 = mb.rfind(b"\xf6\x01", 0, p_1388 if p_1388 != -1 else ins_pos)
        if p_01f6 != -1:
            old_f6_len = struct.unpack_from("<I", mb, p_01f6 + 2)[0]
            struct.pack_into("<I", mb, p_01f6 + 2, old_f6_len + total_delta)

        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, old_f4_len + total_delta)

        for k, off in list(session.instances_offsets.items()):
            if off > ins_pos:
                session.instances_offsets[k] = off + total_delta

        if session.camera_offset is not None and session.camera_offset > ins_pos:
            session.camera_offset += total_delta

        for t, toff in list(session.tags_offsets.items()):
            if toff > ins_pos:
                session.tags_offsets[t] = toff + total_delta

        if session.active_scene_offset is not None and session.active_scene_offset > ins_pos:
            session.active_scene_offset += total_delta

        for s in session.scenes:
            if "offset" in s and s["offset"] > ins_pos:
                s["offset"] += total_delta

        session.is_dirty = True
        return {
            "entity_type": "Box",
            "vertex_count": 8,
            "edge_count": 12,
            "face_count": 6,
            "face_ids": f_ids,
            "edge_ids": e_ids,
            "vertex_ids": v_ids,
            "dimensions_m": [float(width_m), float(length_m), float(height_m)],
            "volume_m3": round(float(width_m) * float(length_m) * float(height_m), 4),
        }

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
    def create_textured_material(
        cls,
        material_name: str,
        image_bytes: bytes,
        image_filename: str = "texture.png",
        scale_u_cm: float = 100.0,
        scale_v_cm: float = 100.0,
        color_rgb: Optional[Tuple[int, int, int]] = None,
    ) -> Dict[str, Any]:
        """Injeta nativamente um material com textura de imagem no model.dat e no container ZIP (Zero DLL)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        # 1. Aloca novo EntityID
        all_eids = set()
        p = 0
        mb_len = len(mb)
        while p + 6 <= mb_len:
            p_de = mb.find(b"\xde\x05", p)
            if p_de == -1:
                break
            l = struct.unpack_from("<I", mb, p_de + 2)[0]
            if 1 <= l <= 8 and p_de + 6 + l <= mb_len:
                all_eids.add(int.from_bytes(mb[p_de + 6 : p_de + 6 + l], "little"))
            p = p_de + 1

        new_mat_eid = max(all_eids, default=50000) + 1
        while new_mat_eid in all_eids:
            new_mat_eid += 1
        all_eids.add(new_mat_eid)

        name_bytes = material_name.encode("utf-8")

        # 2. Constrói bloco Tag 0x32c8 no model.dat
        eid_bytes = new_mat_eid.to_bytes(4, "little")
        eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
        dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag

        cc_tag = b"\xcc2" + struct.pack("<I", len(name_bytes)) + name_bytes
        ca_tag = b"\xca2\x01\x00\x00\x00\x00"
        cb_tag = b"\xcb2\x00\x00\x00\x00"
        cd_tag = b"\xcd2\x04\x00\x00\x00\x5a\x00\x00\x00"

        c8_payload = dc_tag + cc_tag + ca_tag + cb_tag + cd_tag
        c8_tag = b"\xc82" + struct.pack("<I", len(c8_payload)) + c8_payload
        mat_delta = len(c8_tag)

        # 3. Localiza Tag 0x30d5
        p_30d5 = mb.find(b"\xd5\x30")
        if p_30d5 == -1:
            raise SceneSessionError("contêiner de materiais Tag 0x30d5 não localizado")

        old_d5_len = struct.unpack_from("<I", mb, p_30d5 + 2)[0]
        ins_pos = p_30d5 + 6 + old_d5_len
        mb[ins_pos:ins_pos] = c8_tag

        struct.pack_into("<I", mb, p_30d5 + 2, old_d5_len + mat_delta)

        p_30d4 = mb.rfind(b"\xd4\x30", 0, p_30d5)
        if p_30d4 != -1:
            old_d4_len = struct.unpack_from("<I", mb, p_30d4 + 2)[0]
            struct.pack_into("<I", mb, p_30d4 + 2, old_d4_len + mat_delta)

        p_01f7 = mb.rfind(b"\xf7\x01", 0, p_30d4 if p_30d4 != -1 else p_30d5)
        if p_01f7 != -1:
            old_f7_len = struct.unpack_from("<I", mb, p_01f7 + 2)[0]
            struct.pack_into("<I", mb, p_01f7 + 2, old_f7_len + mat_delta)

        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, old_f4_len + mat_delta)

        # 4. Reajusta offsets na sessão
        for k, off in list(session.instances_offsets.items()):
            if off > ins_pos:
                session.instances_offsets[k] = off + mat_delta

        if session.camera_offset and session.camera_offset > ins_pos:
            session.camera_offset += mat_delta

        for t, toff in list(session.tags_offsets.items()):
            if toff > ins_pos:
                session.tags_offsets[t] = toff + mat_delta

        if session.active_scene_offset and session.active_scene_offset > ins_pos:
            session.active_scene_offset += mat_delta

        for s in session.scenes:
            if "offset" in s and s["offset"] > ins_pos:
                s["offset"] += mat_delta

        # 5. XML e imagens do material
        cr, cg, cb = color_rgb if color_rgb else (200, 200, 200)
        scale_x_in = float(scale_u_cm) / 2.54
        scale_y_in = float(scale_v_cm) / 2.54

        xml_text = f'''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<materialDocument xmlns="http://sketchup.google.com/schemas/sketchup/1.0/material" xmlns:mat="http://sketchup.google.com/schemas/sketchup/1.0/material">
  <mat:material name="{material_name}" type="1" workflow="0" colorRed="{cr}" colorGreen="{cg}" colorBlue="{cb}" colorizeType="0" trans="1.0" useTrans="0" pbrPromoState="0" hasTexture="1">
    <mat:texture textureFilename="{image_filename}" xScale="{scale_x_in}" yScale="{scale_y_in}" avgColor="4284782280">
      <mat:images>
        <mat:image id="1" path="./{image_filename}" file_name="{image_filename}"/>
      </mat:images>
    </mat:texture>
    <mat:pbrMR xScale="{scale_x_in}" yScale="{scale_y_in}">
      <mat:enable_metalness>0</mat:enable_metalness>
      <mat:enable_roughness>0</mat:enable_roughness>
      <mat:roughness_texture_invert>0</mat:roughness_texture_invert>
      <mat:enable_normal>0</mat:enable_normal>
      <mat:enable_occlusion>0</mat:enable_occlusion>
      <mat:metallicFactor>1</mat:metallicFactor>
      <mat:roughnessFactor>1</mat:roughnessFactor>
      <mat:normalMapStyle>1</mat:normalMapStyle>
      <mat:normalScale>1</mat:normalScale>
      <mat:occlusionStrength>1</mat:occlusionStrength>
      <mat:baseColorFactor>4294967295</mat:baseColorFactor>
    </mat:pbrMR>
  </mat:material>
</materialDocument>
'''
        session.custom_zip_files[f"materials/{material_name}/material.xml"] = xml_text.encode("utf-8")
        session.custom_zip_files[f"materials/{material_name}/{image_filename}"] = image_bytes
        session.is_dirty = True

        return {
            "material_name": material_name,
            "entity_id": new_mat_eid,
            "has_texture": True,
            "texture_file": image_filename,
            "scale_cm": [float(scale_u_cm), float(scale_v_cm)],
        }

    @classmethod
    def set_rendering_style(
        cls,
        mode: Optional[str] = None,
        xray: Optional[bool] = None,
        profiles_width: Optional[int] = None,
        background_rgb: Optional[Tuple[int, int, int]] = None,
        sky_rgb: Optional[Tuple[int, int, int]] = None,
    ) -> Dict[str, Any]:
        """Configura nativamente os estilos de renderização e exibição visual do modelo no style.xml (Zero DLL).

        Suporta:
        - Modo de face: wireframe, hidden_line, shaded, textured, monochrome
        - Raio-X (X-Ray Mode)
        - Espessura de Perfis (Edge Profiles)
        - Cor do Fundo (Background Color)
        - Cor do Céu (Sky Color)
        """
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION

        # Localiza o style.xml no ZIP existente ou inicializa um novo
        style_filename = None
        style_xml_text = None

        if session.raw_zip_data:
            with zipfile.ZipFile(io.BytesIO(session.raw_zip_data), "r") as zin:
                for fname in zin.namelist():
                    if fname.startswith("styles/") and fname.endswith("/style.xml"):
                        style_filename = fname
                        style_xml_text = zin.read(fname).decode("utf-8", errors="replace")
                        break

        if not style_filename:
            style_filename = "styles/[Simple Style]/style.xml"
            style_xml_text = '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
<styleDocument xmlns="http://sketchup.google.com/schemas/sketchup/1.0/style" xmlns:sty="http://sketchup.google.com/schemas/sketchup/1.0/style">
  <sty:style xmlns:t="http://sketchup.google.com/schemas/1.0/types" name="[Simple Style]" desc="[Configured by SketchBuild Native]">
    <sty:item id="1000"><t:variant type="4">1</t:variant></sty:item>
    <sty:item id="1002"><t:variant type="4">1</t:variant></sty:item>
    <sty:item id="1005"><t:variant type="4">3</t:variant></sty:item>
    <sty:item id="2001"><t:variant type="4">3</t:variant></sty:item>
    <sty:item id="2004"><t:variant type="1">0</t:variant></sty:item>
    <sty:item id="4000"><t:variant type="4">-3752001</t:variant></sty:item>
    <sty:item id="4001"><t:variant type="4">-2516480</t:variant></sty:item>
    <sty:item id="4002"><t:variant type="1">1</t:variant></sty:item>
  </sty:style>
</styleDocument>'''

        def rgb_to_argb_signed(r: int, g: int, b: int) -> int:
            val = (0xFF << 24) | ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF)
            return struct.unpack("<i", struct.pack("<I", val))[0]

        def update_item(text: str, item_id: str, new_val: str, vtype: str = "4") -> str:
            pat = rf'(<sty:item id="{item_id}">\s*<t:variant type="[^"]*">)(.*?)(</t:variant>\s*</sty:item>)'
            if re.search(pat, text):
                return re.sub(pat, rf'\g<1>{new_val}\g<3>', text)
            else:
                closing = "</sty:style>"
                new_block = f'    <sty:item id="{item_id}"><t:variant type="{vtype}">{new_val}</t:variant></sty:item>\n  '
                return text.replace(closing, new_block + closing, 1)

        mode_map = {
            "wireframe": 0,
            "hidden_line": 1,
            "shaded": 2,
            "textured": 3,
            "monochrome": 4,
        }

        updated_xml = style_xml_text

        if mode is not None and mode.lower() in mode_map:
            val_code = str(mode_map[mode.lower()])
            updated_xml = update_item(updated_xml, "2001", val_code, "4")

        if xray is not None:
            x_code = "1" if xray else "0"
            updated_xml = update_item(updated_xml, "2004", x_code, "1")

        if profiles_width is not None:
            w_val = max(0, int(profiles_width))
            updated_xml = update_item(updated_xml, "1002", "1" if w_val > 0 else "0", "4")
            updated_xml = update_item(updated_xml, "1005", str(w_val), "4")

        if background_rgb is not None:
            bg_int = rgb_to_argb_signed(*background_rgb)
            updated_xml = update_item(updated_xml, "4000", str(bg_int), "4")

        if sky_rgb is not None:
            sky_int = rgb_to_argb_signed(*sky_rgb)
            updated_xml = update_item(updated_xml, "4001", str(sky_int), "4")
            updated_xml = update_item(updated_xml, "4002", "1", "1")

        session.custom_zip_files[style_filename] = updated_xml.encode("utf-8")
        session.is_dirty = True

        return {
            "style_file": style_filename,
            "mode": mode,
            "xray": xray,
            "profiles_width": profiles_width,
            "background_rgb": background_rgb,
            "sky_rgb": sky_rgb,
        }

    @classmethod
    def set_attribute_dictionary(
        cls,
        dict_name: str,
        attributes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Injeta ou atualiza um Attribute Dictionary com metadados BIM no contêiner do Modelo (Zero DLL)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        # 1. Serializa cada par chave/valor em TLV binário nativo
        items_payload = bytearray()
        for k, v in attributes.items():
            k_bytes = str(k).encode("utf-8")
            b6_tag = b"\xb66" + struct.pack("<I", len(k_bytes)) + k_bytes

            if isinstance(v, bool):
                val_tag = b"\xaa8\x01\x00\x00\x00" + (b"\x01" if v else b"\x00")
            elif isinstance(v, int):
                val_tag = b"\xa78\x04\x00\x00\x00" + struct.pack("<i", v)
            elif isinstance(v, float):
                val_tag = b"\xa98\x08\x00\x00\x00" + struct.pack("<d", v)
            else:
                s_bytes = str(v).encode("utf-8")
                val_tag = b"\xad8" + struct.pack("<I", len(s_bytes)) + s_bytes

            a4_tag = b"\xa48" + struct.pack("<I", len(val_tag)) + val_tag
            items_payload.extend(b6_tag + a4_tag)

        b5_tag = b"\xb56" + struct.pack("<I", len(items_payload)) + items_payload
        d_name_bytes = str(dict_name).encode("utf-8")
        b4_tag = b"\xb46" + struct.pack("<I", len(d_name_bytes)) + d_name_bytes

        b3_payload = b"\xb06\x00\x00\x00\x00" + b4_tag + b5_tag + b"\xb76\x04\x00\x00\x00\x00\x00\x00\x00"
        b3_tag = b"\xb36" + struct.pack("<I", len(b3_payload)) + b3_payload

        # 2. Localiza o contêiner de atributos do modelo (que contém GeoReference)
        p_geo = mb.find(b"GeoReference")
        if p_geo == -1:
            raise SceneSessionError("contêiner raiz de dicionários de atributos do modelo não encontrado")

        p_b2 = mb.rfind(b"\xb26", 0, p_geo)
        p_b1 = mb.rfind(b"\xb16", 0, p_b2)
        p_5dd = mb.rfind(b"\xdd\x05", 0, p_b1)
        p_5dc = mb.rfind(b"\xdc\x05", 0, p_5dd)
        p_7d0 = mb.rfind(b"\xd0\x07", 0, p_5dc)
        p_1388 = mb.rfind(b"\x88\x13", 0, p_7d0)
        p_1f6 = mb.rfind(b"\xf6\x01", 0, p_1388)

        old_b2_len = struct.unpack_from("<I", mb, p_b2 + 2)[0]
        ins_pos = p_b2 + 6 + old_b2_len
        dict_delta = len(b3_tag)

        # Insere b3_tag no contêiner
        mb[ins_pos:ins_pos] = b3_tag

        # Atualiza comprimentos na cadeia ascendente
        for p_tag in [p_b2, p_b1, p_5dd, p_5dc, p_7d0, p_1388, p_1f6]:
            if p_tag != -1:
                old_len = struct.unpack_from("<I", mb, p_tag + 2)[0]
                struct.pack_into("<I", mb, p_tag + 2, old_len + dict_delta)

        # Atualiza contêiner raiz offset 0 (Tag 0x01f4)
        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, old_f4_len + dict_delta)

        # Reajusta offsets na sessão
        for k, off in list(session.instances_offsets.items()):
            if off > ins_pos:
                session.instances_offsets[k] = off + dict_delta

        if session.camera_offset and session.camera_offset > ins_pos:
            session.camera_offset += dict_delta

        for t, toff in list(session.tags_offsets.items()):
            if toff > ins_pos:
                session.tags_offsets[t] = toff + dict_delta

        if session.active_scene_offset and session.active_scene_offset > ins_pos:
            session.active_scene_offset += dict_delta

        for s in session.scenes:
            if "offset" in s and s["offset"] > ins_pos:
                s["offset"] += dict_delta

        session.is_dirty = True
        return {
            "dictionary_name": dict_name,
            "num_keys": len(attributes),
            "keys": list(attributes.keys()),
            "inserted_bytes": dict_delta,
        }

    @classmethod
    def set_camera(
        cls,
        eye: List[float],
        target: List[float],
        up: Optional[List[float]] = None,
        fov_deg: Optional[float] = None,
        in_inches: bool = True,
    ) -> None:
        """Grava a orientação e posição da Câmera 3D in-place no model.dat (Zero DLL)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        if session.camera_offset is None:
            raise SceneSessionError("offset da câmera não mapeado no modelo atual")

        scale = 1.0 if in_inches else (1.0 / 2.54)
        eye_in = [float(eye[0]) * scale, float(eye[1]) * scale, float(eye[2]) * scale]
        tgt_in = [float(target[0]) * scale, float(target[1]) * scale, float(target[2]) * scale]

        # 1. Tag 0x34bd (Eye Point3D - 24 bytes)
        struct.pack_into("<3d", session.model_bytes, session.camera_offset + 6, *eye_in)

        # 2. Tag 0x34be (Target Point3D - 24 bytes)
        p_tgt = session.model_bytes.find(
            SkpBinaryReader.TAG_CAMERA_TARGET,
            session.camera_offset,
            session.camera_offset + 60,
        )
        if p_tgt != -1:
            struct.pack_into("<3d", session.model_bytes, p_tgt + 6, *tgt_in)

        # 3. Tag 0x34bf (Up Vector3D - 24 bytes)
        if up and len(up) >= 3:
            p_up = session.model_bytes.find(
                SkpBinaryReader.TAG_CAMERA_UP,
                session.camera_offset,
                session.camera_offset + 100,
            )
            if p_up != -1:
                struct.pack_into("<3d", session.model_bytes, p_up + 6, float(up[0]), float(up[1]), float(up[2]))

        # 4. Tag 0x34c4 (FOV Degrees - 8 bytes)
        if fov_deg is not None:
            p_fov = session.model_bytes.find(
                SkpBinaryReader.TAG_CAMERA_FOV,
                session.camera_offset,
                session.camera_offset + 160,
            )
            if p_fov != -1:
                struct.pack_into("<d", session.model_bytes, p_fov + 6, float(fov_deg))

        session.is_dirty = True

    @classmethod
    def set_tag_visibility(cls, tag_name: str, visible: bool) -> bool:
        """Modifica a visibilidade de uma Tag/Layer in-place no model.dat (1 byte na Tag 0x3c8e)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        vis_offset = session.tags_offsets.get(tag_name)
        if vis_offset is None:
            return False

        # 0x00 = Visível, 0x01 = Oculta
        session.model_bytes[vis_offset] = 0x00 if visible else 0x01
        session.is_dirty = True
        return True

    @classmethod
    def activate_scene(cls, scene_id_or_name: Union[str, int]) -> bool:
        """Ativa uma Cena/Página gravando o EntityID da cena ativa in-place na Tag 0x6d62 (bm\\x04\\x00\\x00\\x00)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        target_scene = None
        for s in session.scenes:
            if (
                str(s.get("id")) == str(scene_id_or_name)
                or s.get("name") == str(scene_id_or_name)
                or s.get("scene_id") == str(scene_id_or_name)
            ):
                target_scene = s
                break

        if not target_scene:
            return False

        target_eid = target_scene.get("id")
        if not target_eid:
            return False

        # Se active_scene_offset já existe (Tag 0x6d62), regrava in-place os 4 bytes do EntityID
        if session.active_scene_offset is not None:
            struct.pack_into("<I", session.model_bytes, session.active_scene_offset + 6, int(target_eid))
        else:
            last_scene_offset = max((s.get("offset", 0) for s in session.scenes), default=-1)
            if last_scene_offset != -1:
                slen = struct.unpack_from("<I", session.model_bytes, last_scene_offset + 2)[0]
                ins_pos = last_scene_offset + 6 + slen
                active_tag = b"\x62\x6d\x04\x00\x00\x00" + struct.pack("<I", int(target_eid))
                session.model_bytes[ins_pos:ins_pos] = active_tag
                session.active_scene_offset = ins_pos

        # Atualiza a flag active nas cenas em memória
        for s in session.scenes:
            s["active"] = (s.get("id") == target_eid)

        session.is_dirty = True
        return True

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
            zip_buffer_out = io.BytesIO()
            with io.BytesIO(session.raw_zip_data) as zip_buffer_in:
                with zipfile.ZipFile(zip_buffer_in, "r") as zin:
                    with zipfile.ZipFile(zip_buffer_out, "w", compression=zipfile.ZIP_DEFLATED) as zout:
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
                            elif fname in session.custom_zip_files:
                                zout.writestr(item, session.custom_zip_files[fname])
                            else:
                                # Copia outros assets intactos (texturas, thumbnails, etc.)
                                zout.writestr(item, zin.read(fname))

                        # Grava novos arquivos customizados que não existiam no ZIP original
                        existing_names = {item.filename for item in zin.infolist()}
                        for custom_path, custom_data in session.custom_zip_files.items():
                            if custom_path not in existing_names:
                                zout.writestr(custom_path, custom_data)

            final_zip_bytes = zip_buffer_out.getvalue()
            with open(tmp_target, "wb") as f_out:
                if session.skp_prefix:
                    f_out.write(session.skp_prefix)
                f_out.write(final_zip_bytes)

            # Substitui de forma atômica
            if os.path.exists(path):
                os.replace(tmp_target, path)
            else:
                os.rename(tmp_target, path)

            # Atualiza o raw_zip_data em memória para o novo fluxo ZIP
            session.raw_zip_data = final_zip_bytes

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

    @classmethod
    def add_line_edge(
        cls,
        start_xyz_m: Tuple[float, float, float],
        end_xyz_m: Tuple[float, float, float],
    ) -> Dict[str, Any]:
        """Cria nativamente uma aresta/linha 3D livre no model.dat (Frente 22 - Zero DLL)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        s_in = tuple((float(c) * 100.0) / 2.54 for c in start_xyz_m)
        e_in = tuple((float(c) * 100.0) / 2.54 for c in end_xyz_m)

        all_eids = set()
        p = 0
        mb_len = len(mb)
        while p + 6 <= mb_len:
            p_de = mb.find(b"\xde\x05", p)
            if p_de == -1:
                break
            l = struct.unpack_from("<I", mb, p_de + 2)[0]
            if 1 <= l <= 8 and p_de + 6 + l <= mb_len:
                all_eids.add(int.from_bytes(mb[p_de + 6 : p_de + 6 + l], "little"))
            p = p_de + 1

        cur_eid = max(all_eids, default=50000)

        def alloc_eid() -> int:
            nonlocal cur_eid
            cur_eid += 1
            while cur_eid in all_eids:
                cur_eid += 1
            all_eids.add(cur_eid)
            return cur_eid

        v1_id = alloc_eid()
        v2_id = alloc_eid()
        edge_id = alloc_eid()

        # 1. Vértices
        v_payload = bytearray()
        for vid, pt in [(v1_id, s_in), (v2_id, e_in)]:
            eid_bytes = vid.to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            pt_tag = b"\xc5\t\x18\x00\x00\x00" + struct.pack("<3d", *pt)
            c4_payload = dc_tag + pt_tag
            c4_tag = b"\xc4\t" + struct.pack("<I", len(c4_payload)) + c4_payload
            v_payload.extend(c4_tag)
        tag_1389 = b"\x89\x13" + struct.pack("<I", len(v_payload)) + v_payload

        # 2. Aresta
        eid_bytes = edge_id.to_bytes(4, "little")
        eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
        dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
        d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
        d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload
        b9_tag = b"\xb9\x0b\x04\x00\x00\x00" + v1_id.to_bytes(4, "little")
        ba_tag = b"\xba\x0b\x04\x00\x00\x00" + v2_id.to_bytes(4, "little")
        b8_payload = d0_tag + b9_tag + ba_tag
        b8_tag = b"\xb8\x0b" + struct.pack("<I", len(b8_payload)) + b8_payload
        tag_138a = b"\x8a\x13" + struct.pack("<I", len(b8_tag)) + b8_tag

        geom_block = tag_1389 + tag_138a
        geom_delta = len(geom_block)

        p_138c = mb.find(b"\x8c\x13")
        if p_138c == -1:
            raise SceneSessionError("contêiner de instâncias Tag 0x138c não localizado")

        ins_pos = p_138c
        mb[ins_pos:ins_pos] = geom_block

        p_8e = mb.find(b"\x8e\x13", ins_pos + geom_delta)
        tag_8e_delta = 0
        if p_8e != -1:
            old_8e_len = struct.unpack_from("<I", mb, p_8e + 2)[0]
            old_8e_data = mb[p_8e + 6 : p_8e + 6 + old_8e_len]
            new_entries = bytearray([4]) + edge_id.to_bytes(4, "little")
            new_8e_data = old_8e_data + new_entries
            tag_8e_delta = len(new_entries)
            mb[p_8e + 6 : p_8e + 6 + old_8e_len] = new_8e_data
            struct.pack_into("<I", mb, p_8e + 2, len(new_8e_data))

        total_delta = geom_delta + tag_8e_delta

        p_1388 = mb.rfind(b"\x88\x13", 0, ins_pos)
        if p_1388 != -1:
            old_1388_len = struct.unpack_from("<I", mb, p_1388 + 2)[0]
            struct.pack_into("<I", mb, p_1388 + 2, old_1388_len + total_delta)

        p_01f6 = mb.rfind(b"\xf6\x01", 0, p_1388 if p_1388 != -1 else ins_pos)
        if p_01f6 != -1:
            old_f6_len = struct.unpack_from("<I", mb, p_01f6 + 2)[0]
            struct.pack_into("<I", mb, p_01f6 + 2, old_f6_len + total_delta)

        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, old_f4_len + total_delta)

        session.is_dirty = True
        dist_m = math.sqrt(sum((end_xyz_m[i] - start_xyz_m[i]) ** 2 for i in range(3)))
        return {
            "entity_type": "Edge",
            "edge_id": edge_id,
            "vertex_ids": [v1_id, v2_id],
            "start_m": list(start_xyz_m),
            "end_m": list(end_xyz_m),
            "length_m": round(dist_m, 4),
        }

    @classmethod
    def add_polygon_face(
        cls,
        points_xyz_m: List[Tuple[float, float, float]],
    ) -> Dict[str, Any]:
        """Cria nativamente uma Face plana poligonal com N lados no model.dat (Frente 22 - Zero DLL)."""
        if len(points_xyz_m) < 3:
            raise SceneSessionError("Uma face requer pelo menos 3 pontos coplanares.")

        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        # Converte metros para polegadas
        pts_in = [tuple((float(c) * 100.0) / 2.54 for c in p) for p in points_xyz_m]
        n_pts = len(pts_in)

        # Calcula a normal analítica do polígono via produto vetorial de (P1 - P0) x (P2 - P0)
        p0 = pts_in[0]
        p1 = pts_in[1]
        p2 = pts_in[2]
        v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        nx = v1[1] * v2[2] - v1[2] * v2[1]
        ny = v1[2] * v2[0] - v1[0] * v2[2]
        nz = v1[0] * v2[1] - v1[1] * v2[0]
        norm_len = math.sqrt(nx * nx + ny * ny + nz * nz)
        if norm_len < 1e-8:
            nx, ny, nz = 0.0, 0.0, 1.0
        else:
            nx, ny, nz = nx / norm_len, ny / norm_len, nz / norm_len

        # D da equação do plano: Ax + By + Cz + D = 0 => D = -(Ax + By + Cz)
        plane_d = -(nx * p0[0] + ny * p0[1] + nz * p0[2])

        # Alocação de novos EntityIDs
        all_eids = set()
        p = 0
        mb_len = len(mb)
        while p + 6 <= mb_len:
            p_de = mb.find(b"\xde\x05", p)
            if p_de == -1:
                break
            l = struct.unpack_from("<I", mb, p_de + 2)[0]
            if 1 <= l <= 8 and p_de + 6 + l <= mb_len:
                all_eids.add(int.from_bytes(mb[p_de + 6 : p_de + 6 + l], "little"))
            p = p_de + 1

        cur_eid = max(all_eids, default=50000)

        def alloc_eid() -> int:
            nonlocal cur_eid
            cur_eid += 1
            while cur_eid in all_eids:
                cur_eid += 1
            all_eids.add(cur_eid)
            return cur_eid

        v_ids = [alloc_eid() for _ in range(n_pts)]
        e_ids = [alloc_eid() for _ in range(n_pts)]
        f_id = alloc_eid()

        # 1. Bloco de Vértices (Tag 0x1389)
        v_payload = bytearray()
        for i in range(n_pts):
            eid_bytes = v_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            pt_tag = b"\xc5\t\x18\x00\x00\x00" + struct.pack("<3d", *pts_in[i])
            c4_payload = dc_tag + pt_tag
            c4_tag = b"\xc4\t" + struct.pack("<I", len(c4_payload)) + c4_payload
            v_payload.extend(c4_tag)
        tag_1389 = b"\x89\x13" + struct.pack("<I", len(v_payload)) + v_payload

        # 2. Bloco de Arestas (Tag 0x138a)
        e_payload = bytearray()
        for i in range(n_pts):
            v_start = v_ids[i]
            v_end = v_ids[(i + 1) % n_pts]
            eid_bytes = e_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
            d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload
            b9_tag = b"\xb9\x0b\x04\x00\x00\x00" + v_start.to_bytes(4, "little")
            ba_tag = b"\xba\x0b\x04\x00\x00\x00" + v_end.to_bytes(4, "little")
            b8_payload = d0_tag + b9_tag + ba_tag
            b8_tag = b"\xb8\x0b" + struct.pack("<I", len(b8_payload)) + b8_payload
            e_payload.extend(b8_tag)
        tag_138a = b"\x8a\x13" + struct.pack("<I", len(e_payload)) + e_payload

        # 3. Bloco de Face (Tag 0x138b)
        eid_bytes = f_id.to_bytes(4, "little")
        eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
        dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
        d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
        d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload

        dad_tag = b"\xad\x0d\x20\x00\x00\x00" + struct.pack("<4d", nx, ny, nz, plane_d)

        edge_uses = bytearray()
        for i in range(n_pts):
            fa1 = b"\xa1\x0f\x04\x00\x00\x00" + e_ids[i].to_bytes(4, "little")
            fa2 = b"\xa2\x0f\x01\x00\x00\x00\x00"
            fa0_payload = fa1 + fa2
            fa0_tag = b"\xa0\x0f" + struct.pack("<I", len(fa0_payload)) + fa0_payload
            edge_uses.extend(fa0_tag)

        tag_1195 = b"\x95\x11" + struct.pack("<I", len(edge_uses)) + edge_uses
        tag_1194 = b"\x94\x11" + struct.pack("<I", len(tag_1195)) + tag_1195
        dae_tag = b"\xae\x0d" + struct.pack("<I", len(tag_1194)) + tag_1194

        ac0d_payload = d0_tag + dad_tag + dae_tag
        ac0d_tag = b"\xac\r" + struct.pack("<I", len(ac0d_payload)) + ac0d_payload
        tag_138b = b"\x8b\x13" + struct.pack("<I", len(ac0d_tag)) + ac0d_tag

        geom_block = tag_1389 + tag_138a + tag_138b
        geom_delta = len(geom_block)

        p_138c = mb.find(b"\x8c\x13")
        if p_138c == -1:
            raise SceneSessionError("contêiner de instâncias Tag 0x138c não localizado")

        ins_pos = p_138c
        mb[ins_pos:ins_pos] = geom_block

        p_8e = mb.find(b"\x8e\x13", ins_pos + geom_delta)
        tag_8e_delta = 0
        if p_8e != -1:
            old_8e_len = struct.unpack_from("<I", mb, p_8e + 2)[0]
            old_8e_data = mb[p_8e + 6 : p_8e + 6 + old_8e_len]
            new_entries = bytearray()
            for eid in e_ids + [f_id]:
                new_entries.append(4)
                new_entries.extend(eid.to_bytes(4, "little"))
            new_8e_data = old_8e_data + new_entries
            tag_8e_delta = len(new_entries)
            mb[p_8e + 6 : p_8e + 6 + old_8e_len] = new_8e_data
            struct.pack_into("<I", mb, p_8e + 2, len(new_8e_data))

        total_delta = geom_delta + tag_8e_delta

        p_1388 = mb.rfind(b"\x88\x13", 0, ins_pos)
        if p_1388 != -1:
            old_1388_len = struct.unpack_from("<I", mb, p_1388 + 2)[0]
            struct.pack_into("<I", mb, p_1388 + 2, old_1388_len + total_delta)

        p_01f6 = mb.rfind(b"\xf6\x01", 0, p_1388 if p_1388 != -1 else ins_pos)
        if p_01f6 != -1:
            old_f6_len = struct.unpack_from("<I", mb, p_01f6 + 2)[0]
            struct.pack_into("<I", mb, p_01f6 + 2, old_f6_len + total_delta)

        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, old_f4_len + total_delta)

        session.is_dirty = True
        return {
            "entity_type": "Face",
            "face_id": f_id,
            "edge_ids": e_ids,
            "vertex_ids": v_ids,
            "vertex_count": n_pts,
            "normal": [round(nx, 4), round(ny, 4), round(nz, 4)],
            "plane_d": round(plane_d, 4),
        }


    @classmethod
    def _build_and_inject_brep_mesh(
        cls,
        pts_in: List[Tuple[float, float, float]],
        edge_defs: List[Tuple[int, int]],
        face_defs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Injeta um conjunto arbitrário de vértices, arestas e faces B-Rep no model.dat (Zero DLL)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        n_v = len(pts_in)
        n_e = len(edge_defs)
        n_f = len(face_defs)

        # Coleta entity IDs existentes
        all_eids = set()
        p = 0
        mb_len = len(mb)
        while p + 6 <= mb_len:
            p_de = mb.find(b"\xde\x05", p)
            if p_de == -1:
                break
            l = struct.unpack_from("<I", mb, p_de + 2)[0]
            if 1 <= l <= 8 and p_de + 6 + l <= mb_len:
                all_eids.add(int.from_bytes(mb[p_de + 6 : p_de + 6 + l], "little"))
            p = p_de + 1

        cur_eid = max(all_eids, default=60000)
        def alloc_eid() -> int:
            nonlocal cur_eid
            cur_eid += 1
            while cur_eid in all_eids:
                cur_eid += 1
            all_eids.add(cur_eid)
            return cur_eid

        v_ids = [alloc_eid() for _ in range(n_v)]
        e_ids = [alloc_eid() for _ in range(n_e)]
        f_ids = [alloc_eid() for _ in range(n_f)]

        # 1. Vértices (Tag 0x09c4 em 0x1389)
        v_payload = bytearray()
        for i in range(n_v):
            eid_bytes = v_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            pt_tag = b"\xc5\t\x18\x00\x00\x00" + struct.pack("<3d", *pts_in[i])
            c4_payload = dc_tag + pt_tag
            c4_tag = b"\xc4\t" + struct.pack("<I", len(c4_payload)) + c4_payload
            v_payload.extend(c4_tag)
        tag_1389 = b"\x89\x13" + struct.pack("<I", len(v_payload)) + v_payload

        # 2. Arestas (Tag 0x0bb8 em 0x138a)
        e_payload = bytearray()
        for i, (va, vb) in enumerate(edge_defs):
            eid_bytes = e_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + eid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
            d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload
            b9_tag = b"\xb9\x0b\x04\x00\x00\x00" + v_ids[va].to_bytes(4, "little")
            ba_tag = b"\xba\x0b\x04\x00\x00\x00" + v_ids[vb].to_bytes(4, "little")
            b8_payload = d0_tag + b9_tag + ba_tag
            b8_tag = b"\xb8\x0b" + struct.pack("<I", len(b8_payload)) + b8_payload
            e_payload.extend(b8_tag)
        tag_138a = b"\x8a\x13" + struct.pack("<I", len(e_payload)) + e_payload

        # 3. Faces B-Rep (Tag 0x0dad / 0x0dae / 0x0dac em 0x138b)
        f_payload = bytearray()
        for i, fdef in enumerate(face_defs):
            fid_bytes = f_ids[i].to_bytes(4, "little")
            eid_tag = b"\xde\x05\x04\x00\x00\x00" + fid_bytes
            dc_tag = b"\xdc\x05\n\x00\x00\x00" + eid_tag
            d0_payload = dc_tag + b"\xd3\x07\x01\x00\x00\x00\x06"
            d0_tag = b"\xd0\x07" + struct.pack("<I", len(d0_payload)) + d0_payload

            nx, ny, nz = fdef["normal"]
            pd = fdef["plane_d"]
            dad_tag = b"\xad\x0d\x20\x00\x00\x00" + struct.pack("<4d", nx, ny, nz, pd)

            edge_uses = bytearray()
            for edge_idx, is_rev in fdef["edges"]:
                fa1 = b"\xa1\x0f\x04\x00\x00\x00" + e_ids[edge_idx].to_bytes(4, "little")
                fa2 = b"\xa2\x0f\x01\x00\x00\x00" + (b"\x01" if is_rev else b"\x00")
                fa0_payload = fa1 + fa2
                fa0_tag = b"\xa0\x0f" + struct.pack("<I", len(fa0_payload)) + fa0_payload
                edge_uses.extend(fa0_tag)

            tag_1195 = b"\x95\x11" + struct.pack("<I", len(edge_uses)) + edge_uses
            tag_1194 = b"\x94\x11" + struct.pack("<I", len(tag_1195)) + tag_1195
            dae_tag = b"\xae\x0d" + struct.pack("<I", len(tag_1194)) + tag_1194

            ac0d_payload = d0_tag + dad_tag + dae_tag
            ac0d_tag = b"\xac\r" + struct.pack("<I", len(ac0d_payload)) + ac0d_payload
            f_payload.extend(ac0d_tag)

        tag_138b = b"\x8b\x13" + struct.pack("<I", len(f_payload)) + f_payload

        geom_block = tag_1389 + tag_138a + tag_138b
        geom_delta = len(geom_block)

        p_138c = mb.find(b"\x8c\x13")
        if p_138c == -1:
            raise SceneSessionError("contêiner de instâncias Tag 0x138c não localizado")

        ins_pos = p_138c
        mb[ins_pos:ins_pos] = geom_block

        p_8e = mb.find(b"\x8e\x13", ins_pos + geom_delta)
        tag_8e_delta = 0
        if p_8e != -1:
            old_8e_len = struct.unpack_from("<I", mb, p_8e + 2)[0]
            old_8e_data = mb[p_8e + 6 : p_8e + 6 + old_8e_len]
            new_entries = bytearray()
            for eid in e_ids + f_ids:
                new_entries.append(4)
                new_entries.extend(eid.to_bytes(4, "little"))
            new_8e_data = old_8e_data + new_entries
            tag_8e_delta = len(new_entries)
            mb[p_8e + 6 : p_8e + 6 + old_8e_len] = new_8e_data
            struct.pack_into("<I", mb, p_8e + 2, len(new_8e_data))

        total_delta = geom_delta + tag_8e_delta

        p_1388 = mb.rfind(b"\x88\x13", 0, ins_pos)
        if p_1388 != -1:
            old_1388_len = struct.unpack_from("<I", mb, p_1388 + 2)[0]
            struct.pack_into("<I", mb, p_1388 + 2, old_1388_len + total_delta)

        p_01f6 = mb.rfind(b"\xf6\x01", 0, p_1388 if p_1388 != -1 else ins_pos)
        if p_01f6 != -1:
            old_f6_len = struct.unpack_from("<I", mb, p_01f6 + 2)[0]
            struct.pack_into("<I", mb, p_01f6 + 2, old_f6_len + total_delta)

        old_f4_len = struct.unpack_from("<I", mb, 2)[0]
        struct.pack_into("<I", mb, 2, old_f4_len + total_delta)

        session.is_dirty = True
        return {
            "vertex_ids": v_ids,
            "edge_ids": e_ids,
            "face_ids": f_ids,
            "vertex_count": n_v,
            "edge_count": n_e,
            "face_count": n_f,
        }

    @classmethod
    def add_circle(
        cls,
        radius_m: float,
        center_xyz_m: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        num_segments: int = 24,
    ) -> Dict[str, Any]:
        """Cria um círculo plano B-Rep com K segmentos no plano horizontal (Frente 14 - Zero DLL)."""
        if radius_m <= 0:
            raise SceneSessionError("Raio do círculo deve ser positivo.")
        k = max(int(num_segments), 3)
        cx, cy, cz = center_xyz_m
        pts = []
        for i in range(k):
            theta = 2.0 * math.pi * i / k
            x = cx + radius_m * math.cos(theta)
            y = cy + radius_m * math.sin(theta)
            pts.append((x, y, cz))
        res = cls.add_polygon_face(pts)
        res["radius_m"] = radius_m
        res["center_m"] = list(center_xyz_m)
        res["segments"] = k
        res["area_m2"] = round(math.pi * (radius_m ** 2), 4)
        return res

    @classmethod
    def add_cylinder(
        cls,
        radius_m: float,
        height_m: float,
        center_xyz_m: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        num_segments: int = 16,
    ) -> Dict[str, Any]:
        """Cria um Cilindro 3D Manifold paramétrico (Postes/Tubos Parkelô - Frente 14 - Zero DLL)."""
        if radius_m <= 0 or height_m <= 0:
            raise SceneSessionError("Raio e altura do cilindro devem ser positivos.")

        k = max(int(num_segments), 4)
        cx, cy, cz = center_xyz_m
        r_in = (float(radius_m) * 100.0) / 2.54
        h_in = (float(height_m) * 100.0) / 2.54
        cx_in = (float(cx) * 100.0) / 2.54
        cy_in = (float(cy) * 100.0) / 2.54
        cz_in = (float(cz) * 100.0) / 2.54

        # Vértices da base (0 .. k-1) e do topo (k .. 2k-1)
        pts_in = []
        for i in range(k):
            theta = 2.0 * math.pi * i / k
            pts_in.append((cx_in + r_in * math.cos(theta), cy_in + r_in * math.sin(theta), cz_in))
        for i in range(k):
            theta = 2.0 * math.pi * i / k
            pts_in.append((cx_in + r_in * math.cos(theta), cy_in + r_in * math.sin(theta), cz_in + h_in))

        # Arestas:
        # 0 .. k-1: arestas da base
        # k .. 2k-1: arestas do topo
        # 2k .. 3k-1: arestas verticais conectando V_i a T_i
        edge_defs = []
        for i in range(k):
            edge_defs.append((i, (i + 1) % k))
        for i in range(k):
            edge_defs.append((k + i, k + ((i + 1) % k)))
        for i in range(k):
            edge_defs.append((i, k + i))

        # Faces:
        # 1. Base inferior (normal -Z): loop reverso
        base_edges = [(i, True) for i in reversed(range(k))]
        face_defs = [{
            "edges": base_edges,
            "normal": (0.0, 0.0, -1.0),
            "plane_d": cz_in,
        }]

        # 2. Topo superior (normal +Z): loop direto
        top_edges = [(k + i, False) for i in range(k)]
        face_defs.append({
            "edges": top_edges,
            "normal": (0.0, 0.0, 1.0),
            "plane_d": -(cz_in + h_in),
        })

        # 3. K Faces laterais (retângulos com normais radiais unitárias)
        for i in range(k):
            next_i = (i + 1) % k
            # Arestas do retângulo: base[i], vert[next_i], topo[i] (rev), vert[i] (rev)
            lat_edges = [
                (i, False),
                (2 * k + next_i, False),
                (k + i, True),
                (2 * k + i, True),
            ]
            # Normal radial externa no ponto médio
            mid_theta = 2.0 * math.pi * (i + 0.5) / k
            nx = math.cos(mid_theta)
            ny = math.sin(mid_theta)
            nz = 0.0
            # Ponto sobre a face
            px = cx_in + r_in * nx
            py = cy_in + r_in * ny
            pd = -(nx * px + ny * py)
            face_defs.append({
                "edges": lat_edges,
                "normal": (nx, ny, nz),
                "plane_d": pd,
            })

        res = cls._build_and_inject_brep_mesh(pts_in, edge_defs, face_defs)
        res["entity_type"] = "Cylinder"
        res["radius_m"] = radius_m
        res["height_m"] = height_m
        res["center_m"] = list(center_xyz_m)
        res["segments"] = k
        res["volume_m3"] = round(math.pi * (radius_m ** 2) * height_m, 4)
        res["surface_area_m2"] = round(2.0 * math.pi * radius_m * (radius_m + height_m), 4)
        return res

    @classmethod
    def extrude_face(
        cls,
        points_xyz_m: List[Tuple[float, float, float]],
        distance_m: float,
        normal_xyz: Optional[Tuple[float, float, float]] = None,
    ) -> Dict[str, Any]:
        """Extrude uma face coplanar existente ao longo de sua normal (Push/Pull - Frente 24 - Zero DLL)."""
        n_pts = len(points_xyz_m)
        if n_pts < 3:
            raise SceneSessionError("A extrusão de face requer pelo menos 3 vértices coplanares.")
        if abs(distance_m) < 0.001:
            raise SceneSessionError("Distância de extrusão deve ser não-nula.")

        # Converte para polegadas
        pts_in = [tuple((float(c) * 100.0) / 2.54 for c in p) for p in points_xyz_m]
        dist_in = (float(distance_m) * 100.0) / 2.54

        # Se normal não informada, calcula analiticamente (P1 - P0) x (P2 - P0)
        if not normal_xyz:
            p0, p1, p2 = pts_in[0], pts_in[1], pts_in[2]
            v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
            nx = v1[1] * v2[2] - v1[2] * v2[1]
            ny = v1[2] * v2[0] - v1[0] * v2[2]
            nz = v1[0] * v2[1] - v1[1] * v2[0]
            norm_len = math.sqrt(nx * nx + ny * ny + nz * nz)
            if norm_len < 1e-9:
                raise SceneSessionError("Vértices colineares ou normais degeneradas.")
            nx /= norm_len
            ny /= norm_len
            nz /= norm_len
        else:
            nx, ny, nz = normal_xyz
            norm_len = math.sqrt(nx * nx + ny * ny + nz * nz)
            nx /= norm_len
            ny /= norm_len
            nz /= norm_len

        # Vetor de deslocamento
        dx = nx * dist_in
        dy = ny * dist_in
        dz = nz * dist_in

        # Vértices de base (0 .. n-1) e topo (n .. 2n-1)
        all_pts_in = list(pts_in)
        for p in pts_in:
            all_pts_in.append((p[0] + dx, p[1] + dy, p[2] + dz))

        # Arestas: base (0..n-1), topo (n..2n-1), verticais (2n..3n-1)
        edge_defs = []
        for i in range(n_pts):
            edge_defs.append((i, (i + 1) % n_pts))
        for i in range(n_pts):
            edge_defs.append((n_pts + i, n_pts + ((i + 1) % n_pts)))
        for i in range(n_pts):
            edge_defs.append((i, n_pts + i))

        # Faces:
        # 1. Base (normal invertida -N)
        base_pd = nx * pts_in[0][0] + ny * pts_in[0][1] + nz * pts_in[0][2]
        base_edges = [(i, True) for i in reversed(range(n_pts))]
        face_defs = [{
            "edges": base_edges,
            "normal": (-nx, -ny, -nz),
            "plane_d": base_pd,
        }]

        # 2. Topo (normal +N)
        top_p0 = all_pts_in[n_pts]
        top_pd = -(nx * top_p0[0] + ny * top_p0[1] + nz * top_p0[2])
        top_edges = [(n_pts + i, False) for i in range(n_pts)]
        face_defs.append({
            "edges": top_edges,
            "normal": (nx, ny, nz),
            "plane_d": top_pd,
        })

        # 3. N Faces laterais
        for i in range(n_pts):
            next_i = (i + 1) % n_pts
            lat_edges = [
                (i, False),
                (2 * n_pts + next_i, False),
                (n_pts + i, True),
                (2 * n_pts + i, True),
            ]
            # Normal lateral = (P_{i+1} - P_i) x Normal_Face
            p_curr = all_pts_in[i]
            p_next = all_pts_in[next_i]
            edge_v = (p_next[0] - p_curr[0], p_next[1] - p_curr[1], p_next[2] - p_curr[2])
            lat_nx = edge_v[1] * nz - edge_v[2] * ny
            lat_ny = edge_v[2] * nx - edge_v[0] * nz
            lat_nz = edge_v[0] * ny - edge_v[1] * nx
            lat_len = math.sqrt(lat_nx * lat_nx + lat_ny * lat_ny + lat_nz * lat_nz)
            if lat_len > 1e-9:
                lat_nx /= lat_len
                lat_ny /= lat_len
                lat_nz /= lat_len
            lat_pd = -(lat_nx * p_curr[0] + lat_ny * p_curr[1] + lat_nz * p_curr[2])
            face_defs.append({
                "edges": lat_edges,
                "normal": (lat_nx, lat_ny, lat_nz),
                "plane_d": lat_pd,
            })

        res = cls._build_and_inject_brep_mesh(all_pts_in, edge_defs, face_defs)
        res["entity_type"] = "Extrusion"
        res["distance_m"] = distance_m
        res["vertex_count"] = 2 * n_pts
        res["face_count"] = n_pts + 2
        res["edge_count"] = 3 * n_pts
        return res

    @classmethod
    def add_section_plane(
        cls,
        plane_abcd: Tuple[float, float, float, float],
        name: str = "Corte A-A",
        symbol: str = "A1",
    ) -> Dict[str, Any]:
        """Injeta um Plano de Corte de Seção (SectionPlane - Frente 17 - Zero DLL)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        a, b, c, d_meters = plane_abcd
        d_inches = (float(d_meters) * 100.0) / 2.54

        # Codifica tags TLV de SectionPlane:
        # Tag 0x445d: Equação analítica 4 doubles (32 bytes)
        payload_5d = struct.pack("<4d", float(a), float(b), float(c), float(d_inches))
        tag_5d = b"\x5d\x44" + struct.pack("<I", 32) + payload_5d

        # Tag 0x445e: Nome (UTF-8)
        name_bytes = name.encode("utf-8")
        tag_5e = b"\x5e\x44" + struct.pack("<I", len(name_bytes)) + name_bytes

        # Tag 0x445f: Símbolo (UTF-8)
        symbol_bytes = symbol.encode("utf-8")
        tag_5f = b"\x5f\x44" + struct.pack("<I", len(symbol_bytes)) + symbol_bytes

        # Tag 0x445c: Container do SectionPlane
        # Header de entidade (33 bytes) + tag_5d + tag_5e + tag_5f
        entity_hdr = (
            b"\xd0\x07\x14\x00\x00\x00\xdc\x05\x07\x00\x00\x00"
            b"\xde\x05\x01\x00\x00\x00\x12\xd3\x07\x01\x00\x00\x00"
            b"\x06"
        )
        sec_payload = entity_hdr + tag_5d + tag_5e + tag_5f
        tag_5c = b"\x5c\x44" + struct.pack("<I", len(sec_payload)) + sec_payload

        # Injeta logo antes do final do model.dat
        mb.extend(tag_5c)
        session.is_dirty = True

        res = {
            "entity_type": "SectionPlane",
            "plane": [float(a), float(b), float(c), float(d_meters)],
            "plane_inches": [float(a), float(b), float(c), float(d_inches)],
            "name": name,
            "symbol": symbol,
        }
        session.section_planes.append(res)
        return res

    @classmethod
    def add_guide_line(
        cls,
        start_xyz_m: Tuple[float, float, float],
        end_xyz_m: Tuple[float, float, float],
        is_infinite: bool = False,
    ) -> Dict[str, Any]:
        """Injeta uma Linha de Guia / Tape Measure (Frente 18 - Zero DLL)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        # Converte para polegadas
        p1_in = [(float(c) * 100.0) / 2.54 for c in start_xyz_m]
        p2_in = [(float(c) * 100.0) / 2.54 for c in end_xyz_m]

        # Tag 0x426a: 64 bytes (8 doubles = P1 + P2 + vetor aux)
        dx = p2_in[0] - p1_in[0]
        dy = p2_in[1] - p1_in[1]
        dz = p2_in[2] - p1_in[2]
        d8 = (p1_in[0], p1_in[1], p1_in[2], p2_in[0], p2_in[1], p2_in[2], dx, dy)
        payload_6a = struct.pack("<8d", *d8)
        tag_6a = b"\x6a\x42" + struct.pack("<I", 64) + payload_6a

        # Tag 0x426b: is_infinite (2 bytes)
        tag_6b = b"\x6b\x42" + struct.pack("<I", 2) + struct.pack("<H", 1 if is_infinite else 0)

        # Tag 0x4268: EntityHeader (26 bytes)
        tag_68 = (
            b"\x68\x42\x1a\x00\x00\x00"
            b"\xd0\x07\x14\x00\x00\x00\xdc\x05\x07\x00\x00\x00"
            b"\xde\x05\x01\x00\x00\x00\x14\xd3\x07\x01\x00\x00\x00"
            b"\x06"
        )

        line_payload = tag_68 + tag_6a + tag_6b
        tag_69 = b"\x69\x42" + struct.pack("<I", len(line_payload)) + line_payload

        mb.extend(tag_69)
        session.is_dirty = True

        res = {
            "entity_type": "GuideLine",
            "start": list(start_xyz_m),
            "end": list(end_xyz_m),
            "is_infinite": is_infinite,
        }
        session.guide_lines.append(res)
        return res

    @classmethod
    def add_guide_point(
        cls,
        point_xyz_m: Tuple[float, float, float],
    ) -> Dict[str, Any]:
        """Injeta um Ponto de Construção (Frente 18 - Zero DLL)."""
        if cls._ACTIVE_SESSION is None:
            raise SceneSessionError("nenhuma sessão binária ativa")

        session = cls._ACTIVE_SESSION
        mb = session.model_bytes

        # Converte para polegadas
        p_in = [(float(c) * 100.0) / 2.54 for c in point_xyz_m]

        # Tag 0x426d: 24 bytes (3 doubles)
        payload_6d = struct.pack("<3d", *p_in)
        tag_6d = b"\x6d\x42" + struct.pack("<I", 24) + payload_6d

        # Tag 0x4268: EntityHeader (26 bytes)
        tag_68 = (
            b"\x68\x42\x1a\x00\x00\x00"
            b"\xd0\x07\x14\x00\x00\x00\xdc\x05\x07\x00\x00\x00"
            b"\xde\x05\x01\x00\x00\x00\x14\xd3\x07\x01\x00\x00\x00"
            b"\x06"
        )
        tag_6e = b"\x6e\x42\x18\x00\x00\x00" + struct.pack("<3d", 0.0, 0.0, 0.0)
        tag_6f = b"\x6f\x42\x01\x00\x00\x00\x00"

        pt_payload = tag_68 + tag_6d + tag_6e + tag_6f
        tag_6c = b"\x6c\x42" + struct.pack("<I", len(pt_payload)) + pt_payload

        mb.extend(tag_6c)
        session.is_dirty = True

        res = {
            "entity_type": "GuidePoint",
            "position": list(point_xyz_m),
        }
        session.guide_points.append(res)
        return res

    @classmethod
    def add_offset_face(
        cls,
        points_xyz_m: List[Tuple[float, float, float]],
        distance_m: float,
        inside: bool = True,
        create_frame: bool = False,
    ) -> Dict[str, Any]:
        """Cria loop ou moldura deslocada por equidistância (Ferramenta Offset 'F' - Frente 30 - Zero DLL)."""
        from core.offset_calculator import OffsetCalculator

        offset_pts = OffsetCalculator.offset_polygon_3d(points_xyz_m, distance_m, inside=inside)

        if not create_frame:
            # Apenas a face interna/externa deslocada
            res = cls.add_polygon_face(offset_pts)
            res["entity_type"] = "OffsetFace"
            res["distance_m"] = distance_m
            res["inside"] = inside
            return res

        # Gera moldura com anel de faces conectando loop externo ao interno
        frame_faces = OffsetCalculator.generate_frame_faces(points_xyz_m, offset_pts)
        created_faces = []
        for f in frame_faces:
            res_face = cls.add_polygon_face(f)
            created_faces.append(res_face)

        return {
            "entity_type": "OffsetFrame",
            "distance_m": distance_m,
            "inside": inside,
            "outer_vertices": points_xyz_m,
            "inner_vertices": offset_pts,
            "frame_faces_count": len(created_faces),
        }
