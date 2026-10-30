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
