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
                            else:
                                # Copia outros assets intactos (texturas, thumbnails, etc.)
                                zout.writestr(item, zin.read(fname))

                        # Grava arquivos customizados (novas texturas e materiais)
                        for custom_path, custom_data in session.custom_zip_files.items():
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
