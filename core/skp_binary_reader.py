"""
SketchBuild - Leitor Binário Nativo de Arquivos .SKP (Pure Python / Zero DLL)

Decodifica a topologia analítica do SketchUp diretamente do stream 'model.dat'
e materiais XML embutidos no container ZIP (.skp). Não depende de SketchUpAPI.dll,
ctypes ou SketchUp Desktop instalado.

Descobertas de Engenharia Reversa (Frentes 1, 2, 3 e 6):
- Tag 0x09c4 / 0x09c5: Vértice com EntityID dinâmico (Tag 0x05de) e Point3D (3 doubles de 64 bits em polegadas).
- Tag 0x0bb9 / 0x0bba: StartVertex e EndVertex da Aresta (Edge).
- Tag 0x0dad (tamanho 32B): Equação cartesiana do plano 3D (Ax + By + Cz + D = 0).
- Tag 0x0fa0: Loop de arestas com flag de direção (0 ou 1) que orienta o contorno Half-Edge.
- Tag 0x0daf (Front Material) e 0x0db0 (Back Material) / 0x07d1: Associação com EntityID do Material.
- Tag 0x32c8 / 0x32cc: Registro de Material no model.dat mapeando EntityID -> Nome do Material.
- Tag 0x2715 (72B, 9 doubles): Matriz afim 3x3 de projeção UV para texturas mapeadas.
- Tag 0x157e: Nome legível da ComponentDefinition (Outliner).
- Tag 0x157c: Container da ComponentDefinition e Model Root Definition.
- Tag 0x1966 (104B, 13 doubles): Matriz afim 4x4 de transformação espacial da ComponentInstance.
- Tag 0x1967: Referência ao DefinitionID instanciado.
- materials/*/material.xml: Definições completas de cor RGB, transparência, texturas e PBR Metallic-Roughness.
- Tag 0x36b1 / 0x36b2: Contêiner de Dicionários de Atributos (AttributeDictionaries) associado a EntityID (0x05de).
- Tag 0x36b3 / 0x36b4: Nome do AttributeDictionary (ex: 'dynamic_attributes', 'SU_DefinitionSet', 'SU_InstanceSet').
- Tag 0x36b5 / 0x36b6: Chave de Atributo.
- Tag 0x38a4: TypedValue (Double 0x38a9, String 0x38ad, Int32 0x38a7, Bool 0x38aa).
"""

from __future__ import annotations
import zlib
import struct
import os
import zipfile
import xml.etree.ElementTree as ET
from typing import TypedDict, Optional, Tuple, List, Dict, Any, Union


SkpAttributeDictionaryDTO = Dict[str, Any]
SkpAttributeDictionariesDTO = Dict[str, SkpAttributeDictionaryDTO]


class SkpMaterialDTO(TypedDict):
    name: str
    color: List[int]        # [r, g, b] 0-255
    opacity: float          # 0.0 a 1.0
    hasTexture: bool
    texturePath: Optional[str]
    xScale: float
    yScale: float
    metalness: float
    roughness: float
    attributes: Optional[SkpAttributeDictionariesDTO]


class SkpBoundsInfo(TypedDict):
    num_vertices: int
    largura_cm: float
    profundidade_cm: float
    altura_cm: float
    min_pt_cm: Tuple[float, float, float]
    max_pt_cm: Tuple[float, float, float]
    is_empty: bool


class SkpComponentInstanceDTO(TypedDict):
    id: Optional[int]
    definition_id: Optional[int]
    definition_name: str
    translation_cm: List[float]       # [x, y, z] em cm
    matrix_4x4: List[float]           # 16 floats (column-major para Three.js)
    matrix_4x4_inches: Optional[List[float]]
    offset: Optional[int]
    attributes: Optional[SkpAttributeDictionariesDTO]


class SkpComponentDefinitionDTO(TypedDict):
    id: int
    name: str
    instances_count: int
    attributes: Optional[SkpAttributeDictionariesDTO]


class SkpHierarchyDTO(TypedDict):
    definitions: List[SkpComponentDefinitionDTO]
    instances: List[SkpComponentInstanceDTO]
    total_definitions: int
    total_instances: int
    model_attributes: Optional[SkpAttributeDictionariesDTO]


class SkpCameraDTO(TypedDict):
    eye_cm: List[float]               # [x, y, z] em cm
    target_cm: List[float]            # [x, y, z] em cm
    eye_inches: List[float]           # [x, y, z] em polegadas (para o Three.js/SketchUpAPI)
    target_inches: List[float]        # [x, y, z] em polegadas
    up: List[float]                   # [x, y, z] vetor unitário Z-up
    is_perspective: bool
    fov_degrees: float
    fov_is_height: bool
    offset: Optional[int]


class SkpTagDTO(TypedDict):
    id: Optional[int]
    name: str
    visible: bool
    is_default: bool
    material_name: Optional[str]


class SkpMeshDTO(TypedDict):
    vertices: List[float]       # [x, y, z, ...] em cm
    normals: List[float]        # [nx, ny, nz, ...]
    uvs: List[float]            # [u, v, ...] normalizados
    indices: List[int]          # [i0, i1, i2, ...]
    materials: Dict[str, SkpMaterialDTO]  # mapa de materiais do modelo
    face_materials: List[str]   # nome do material de cada face
    face_ranges: List[Dict[str, Any]]
    num_faces: int
    num_vertices: int
    bounds: SkpBoundsInfo
    hierarchy: Optional[SkpHierarchyDTO]
    camera: Optional[SkpCameraDTO]
    tags: Optional[List[SkpTagDTO]]


class SkpBinaryReader:
    TAG_VERTEX = b"\xc4\x09"
    TAG_EDGE_START = b"\xb9\x0b"
    TAG_EDGE_END = b"\xba\x0b"
    TAG_PLANE = b"\xad\x0d\x20\x00\x00\x00"
    TAG_MATERIAL_DEF = b"\xc8\x32"
    TAG_FRONT_MAT = b"\xaf\x0d"
    TAG_BACK_MAT = b"\xb0\x0d"
    TAG_UV_MATRIX = b"\x15\x27\x48\x00\x00\x00"
    TAG_DEF_NAME = b"\x7e\x15"
    TAG_DEF_ROOT = b"\x7c\x15"
    TAG_INSTANCE_TRANSFORM = b"\x66\x19\x68\x00\x00\x00"
    TAG_INSTANCE_DEF_REF = b"\x67\x19"
    TAG_ATTR_DICTS = b"\xb1\x36"
    TAG_ATTR_DICT = b"\xb3\x36"
    TAG_ATTR_DICT_NAME = b"\xb4\x36"
    TAG_ATTR_ITEMS = b"\xb5\x36"
    TAG_ATTR_KEY = b"\xb6\x36"
    TAG_ATTR_VALUE = b"\xa4\x38"
    TAG_CAMERA_EYE = b"\xbd\x34\x18\x00\x00\x00"
    TAG_CAMERA_TARGET = b"\xbe\x34\x18\x00\x00\x00"
    TAG_CAMERA_UP = b"\xbf\x34\x18\x00\x00\x00"
    TAG_CAMERA_PERSPECTIVE = b"\xc2\x34\x01\x00\x00\x00"
    TAG_CAMERA_FOV = b"\xc4\x34\x08\x00\x00\x00"
    TAG_CAMERA_FOV_IS_HEIGHT = b"\xc6\x34\x01\x00\x00\x00"
    TAG_LAYER_CONTAINER = b"\x8c\x3c"
    TAG_LAYER_NAME = b"\x8d\x3c"
    TAG_LAYER_VISIBILITY = b"\x8e\x3c"
    TAG_LAYER_MAT_NAME = b"\xcc\x32"
    ZIP_LOCAL_HEADER = b"PK\x03\x04"

    @classmethod
    def extract_bounds(cls, file_path: str) -> Optional[SkpBoundsInfo]:
        """Extrai as dimensões reais (em cm) e quantidade de vértices de um arquivo .skp
        em ~0.005s a 0.200s, sem depender da DLL da Trimble nem carregar o modelo completo."""
        if not file_path or not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception:
            return None

        model_bytes = cls._extract_model_dat(data)
        if not model_bytes:
            return None

        min_x, max_x = float("inf"), float("-inf")
        min_y, max_y = float("inf"), float("-inf")
        min_z, max_z = float("inf"), float("-inf")
        count = 0
        idx = 0

        while True:
            pos = model_bytes.find(cls.TAG_VERTEX, idx)
            if pos == -1:
                break

            de_pos = model_bytes.find(b"\xde\x05", pos, pos + 25)
            if de_pos != -1:
                id_len = struct.unpack_from("<I", model_bytes, de_pos + 2)[0]
                if 1 <= id_len <= 8:
                    c5_pos = de_pos + 6 + id_len
                    if model_bytes[c5_pos : c5_pos + 6] == b"\xc5\x09\x18\x00\x00\x00":
                        try:
                            x, y, z = struct.unpack_from("<3d", model_bytes, c5_pos + 6)
                            if not (x != x or y != y or z != z):
                                if x < min_x: min_x = x
                                if x > max_x: max_x = x
                                if y < min_y: min_y = y
                                if y > max_y: max_y = y
                                if z < min_z: min_z = z
                                if z > max_z: max_z = z
                                count += 1
                        except Exception:
                            pass

            idx = pos + 1

        if count == 0:
            return {
                "num_vertices": 0,
                "largura_cm": 0.0,
                "profundidade_cm": 0.0,
                "altura_cm": 0.0,
                "min_pt_cm": (0.0, 0.0, 0.0),
                "max_pt_cm": (0.0, 0.0, 0.0),
                "is_empty": True,
            }

        w_cm = round((max_x - min_x) * 2.54, 2)
        d_cm = round((max_y - min_y) * 2.54, 2)
        h_cm = round((max_z - min_z) * 2.54, 2)

        return {
            "num_vertices": count,
            "largura_cm": w_cm,
            "profundidade_cm": d_cm,
            "altura_cm": h_cm,
            "min_pt_cm": (round(min_x * 2.54, 2), round(min_y * 2.54, 2), round(min_z * 2.54, 2)),
            "max_pt_cm": (round(max_x * 2.54, 2), round(max_y * 2.54, 2), round(max_z * 2.54, 2)),
            "is_empty": False,
        }

    @classmethod
    def extract_materials(cls, file_path: str) -> Dict[str, SkpMaterialDTO]:
        """Extrai todos os materiais e propriedades PBR dos XMLs contidos no .skp."""
        materials: Dict[str, SkpMaterialDTO] = {}
        if not file_path or not os.path.exists(file_path):
            return materials

        try:
            with zipfile.ZipFile(file_path, "r") as z:
                for name in z.namelist():
                    if name.startswith("materials/") and name.endswith("/material.xml"):
                        try:
                            content = z.read(name)
                            root = ET.fromstring(content)
                            ns = {"mat": "http://sketchup.google.com/schemas/sketchup/1.0/material"}
                            mat = root.find(".//mat:material", ns)
                            if mat is None:
                                for elem in root.iter():
                                    if "material" in elem.tag:
                                        mat = elem
                                        break
                            if mat is not None:
                                mname = mat.attrib.get("name", "Unnamed")
                                r = int(mat.attrib.get("colorRed", 200))
                                g = int(mat.attrib.get("colorGreen", 200))
                                b = int(mat.attrib.get("colorBlue", 200))
                                trans = float(mat.attrib.get("trans", 1.0))
                                has_tex = mat.attrib.get("hasTexture") == "1"
                                tex_file = None
                                x_scale = 1.0
                                y_scale = 1.0

                                tex_elem = mat.find("mat:texture", ns)
                                if tex_elem is not None:
                                    x_scale = float(tex_elem.attrib.get("xScale", 1.0))
                                    y_scale = float(tex_elem.attrib.get("yScale", 1.0))
                                    img = tex_elem.find(".//mat:image", ns)
                                    if img is not None:
                                        p = img.attrib.get("path", "")
                                        if p.startswith("./"):
                                            tex_file = name.rsplit("/", 1)[0] + "/" + p[2:]
                                        else:
                                            tex_file = p

                                pbr_elem = mat.find("mat:pbrMR", ns)
                                metal = 0.0
                                rough = 1.0
                                if pbr_elem is not None:
                                    mf = pbr_elem.find("mat:metallicFactor", ns)
                                    if mf is not None and mf.text:
                                        metal = float(mf.text)
                                    rf = pbr_elem.find("mat:roughnessFactor", ns)
                                    if rf is not None and rf.text:
                                        rough = float(rf.text)

                                attrs = cls._parse_xml_attributes(root)

                                materials[mname] = {
                                    "name": mname,
                                    "color": [r, g, b],
                                    "opacity": trans,
                                    "hasTexture": has_tex,
                                    "texturePath": tex_file,
                                    "xScale": x_scale,
                                    "yScale": y_scale,
                                    "metalness": metal,
                                    "roughness": rough,
                                    "attributes": attrs,
                                }
                        except Exception:
                            pass
        except Exception:
            pass

        return materials

    @classmethod
    def _parse_typed_value(cls, model_bytes: bytes, curr: int, end_pos: int) -> Tuple[Any, int]:
        if curr >= end_pos or model_bytes[curr : curr + 2] != cls.TAG_ATTR_VALUE:
            return None, curr
        vcontainer_len = struct.unpack_from("<I", model_bytes, curr + 2)[0]
        vstart = curr + 6
        vend = vstart + vcontainer_len
        if vcontainer_len == 0:
            return None, vend
        subtag = model_bytes[vstart : vstart + 2]
        val: Any = None
        if subtag == b"\xa9\x38" and vcontainer_len >= 14:  # Double (IEEE 754)
            val = round(struct.unpack_from("<d", model_bytes, vstart + 6)[0], 6)
        elif subtag == b"\xad\x38":  # String
            slen = struct.unpack_from("<I", model_bytes, vstart + 2)[0]
            val = model_bytes[vstart + 6 : vstart + 6 + slen].decode("utf-8", errors="replace")
        elif subtag == b"\xa7\x38" and vcontainer_len >= 10:  # Int32
            val = struct.unpack_from("<i", model_bytes, vstart + 6)[0]
        elif subtag == b"\xaa\x38" and vcontainer_len >= 7:  # Bool
            val = bool(model_bytes[vstart + 6])
        else:
            val = model_bytes[vstart + 6 : vend].decode("utf-8", errors="replace")
        return val, vend

    @classmethod
    def _parse_model_attributes(
        cls, model_bytes: bytes
    ) -> Tuple[SkpAttributeDictionariesDTO, Dict[int, SkpAttributeDictionariesDTO]]:
        """Extrai todos os AttributeDictionaries do stream model.dat (Zero DLL),
        separando os atributos globais do modelo e os indexados por EntityID."""
        model_attrs: SkpAttributeDictionariesDTO = {}
        entity_attrs: Dict[int, SkpAttributeDictionariesDTO] = {}
        idx = 0
        buf_len = len(model_bytes)

        while True:
            p_b1 = model_bytes.find(cls.TAG_ATTR_DICTS, idx)
            if p_b1 == -1 or p_b1 + 8 > buf_len:
                break

            # Validação anti falso-positivo: o subtag imediato deve ser TAG_ATTR_INNER (0x36b2)
            if model_bytes[p_b1 + 6 : p_b1 + 8] != b"\xb2\x36":
                idx = p_b1 + 1
                continue

            b1_len = struct.unpack_from("<I", model_bytes, p_b1 + 2)[0]
            b1_end = min(buf_len, p_b1 + 6 + b1_len)

            # Procura o EntityID precedente (Tag 0x05de nos últimos 60 bytes)
            p_de = model_bytes.rfind(b"\xde\x05", max(0, p_b1 - 60), p_b1)
            eid = None
            if p_de != -1:
                eid_len = struct.unpack_from("<I", model_bytes, p_de + 2)[0]
                if 1 <= eid_len <= 8:
                    eid = int.from_bytes(model_bytes[p_de + 6 : p_de + 6 + eid_len], "little")

            dicts: SkpAttributeDictionariesDTO = {}
            curr_b3 = p_b1 + 6
            while curr_b3 < b1_end:
                p_b3 = model_bytes.find(cls.TAG_ATTR_DICT, curr_b3, b1_end)
                if p_b3 == -1:
                    break
                b3_len = struct.unpack_from("<I", model_bytes, p_b3 + 2)[0]
                b3_end = min(b1_end, p_b3 + 6 + b3_len)

                p_b4 = model_bytes.find(cls.TAG_ATTR_DICT_NAME, p_b3, min(b3_end, p_b3 + 40))
                if p_b4 != -1:
                    nlen = struct.unpack_from("<I", model_bytes, p_b4 + 2)[0]
                    dname = model_bytes[p_b4 + 6 : p_b4 + 6 + nlen].decode("utf-8", errors="replace")

                    attrs: Dict[str, Any] = {}
                    p_b5 = model_bytes.find(cls.TAG_ATTR_ITEMS, p_b4 + 6 + nlen, min(b3_end, p_b4 + 6 + nlen + 40))
                    if p_b5 != -1:
                        b5_len = struct.unpack_from("<I", model_bytes, p_b5 + 2)[0]
                        b5_end = min(b3_end, p_b5 + 6 + b5_len)
                        curr_k = p_b5 + 6
                        while curr_k < b5_end:
                            p_b6 = model_bytes.find(cls.TAG_ATTR_KEY, curr_k, b5_end)
                            if p_b6 == -1:
                                break
                            klen = struct.unpack_from("<I", model_bytes, p_b6 + 2)[0]
                            kname = model_bytes[p_b6 + 6 : p_b6 + 6 + klen].decode("utf-8", errors="replace")
                            curr_v = p_b6 + 6 + klen
                            v, next_pos = cls._parse_typed_value(model_bytes, curr_v, b5_end)
                            attrs[kname] = v
                            curr_k = next_pos
                    dicts[dname] = attrs
                curr_b3 = b3_end

            if eid is not None:
                entity_attrs[eid] = dicts
            else:
                model_attrs.update(dicts)
            idx = b1_end

        return model_attrs, entity_attrs

    @classmethod
    def _parse_xml_attributes(cls, root: ET.Element) -> SkpAttributeDictionariesDTO:
        """Extrai os AttributeDictionaries definidos nos arquivos XML (ex: materials/*/material.xml)."""
        dicts: SkpAttributeDictionariesDTO = {}
        for dict_elem in root.iter():
            if dict_elem.tag.endswith("AttributeDictionary"):
                dname = dict_elem.attrib.get("name")
                if not dname:
                    continue
                attrs: Dict[str, Any] = {}
                for attr_elem in dict_elem:
                    if attr_elem.tag.endswith("Attribute"):
                        k = attr_elem.attrib.get("key")
                        t = attr_elem.attrib.get("type", "10")
                        val_text = attr_elem.text or ""
                        val: Any = val_text
                        if t == "4":  # Int32
                            try:
                                val = int(val_text)
                            except Exception:
                                pass
                        elif t == "6":  # Double
                            try:
                                val = float(val_text)
                            except Exception:
                                pass
                        elif t == "7":  # Bool
                            val = val_text.lower() in ("1", "true")
                        if k:
                            attrs[k] = val
                dicts[dname] = attrs
        return dicts

    @classmethod
    def extract_hierarchy(cls, file_path: str) -> Optional[SkpHierarchyDTO]:
        """Extrai a árvore do Outliner: ComponentDefinitions e ComponentInstances
        com matrizes de transformação 4x4 diretamente do model.dat."""
        if not file_path or not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception:
            return None

        model_bytes = cls._extract_model_dat(data)
        if not model_bytes:
            return None

        return cls._parse_hierarchy(model_bytes)

    @classmethod
    def _parse_hierarchy(cls, model_bytes: bytes) -> SkpHierarchyDTO:
        # 0. Atributos do modelo e das entidades (Tag 0x36b1)
        model_attrs, entity_attrs = cls._parse_model_attributes(model_bytes)

        # 1. ComponentDefinitions (Tag 0x157e: Nome) + EntityID
        defs_map: Dict[int, str] = {}
        idx = 0
        while True:
            pos = model_bytes.find(cls.TAG_DEF_NAME, idx)
            if pos == -1:
                break
            slen = struct.unpack_from("<I", model_bytes, pos + 2)[0]
            if 1 <= slen <= 120:
                name = model_bytes[pos + 6 : pos + 6 + slen].decode("latin1", errors="replace")
                de_pos = model_bytes.find(b"\xde\x05", pos + 6 + slen, pos + 2500)
                if de_pos != -1:
                    id_len = struct.unpack_from("<I", model_bytes, de_pos + 2)[0]
                    if 1 <= id_len <= 8:
                        did = int.from_bytes(model_bytes[de_pos + 6 : de_pos + 6 + id_len], "little")
                        defs_map[did] = name
            idx = pos + 1

        # Identifica a Model Definition (raiz)
        p_root = model_bytes.find(cls.TAG_DEF_ROOT)
        if p_root != -1:
            de_pos = model_bytes.find(b"\xde\x05", p_root, p_root + 40)
            if de_pos != -1:
                id_len = struct.unpack_from("<I", model_bytes, de_pos + 2)[0]
                if 1 <= id_len <= 8:
                    root_did = int.from_bytes(model_bytes[de_pos + 6 : de_pos + 6 + id_len], "little")
                    defs_map[root_did] = "Model Root"

        # 2. ComponentInstances (Tag 0x1966: 13 doubles + Tag 0x1967: DefID)
        instances: List[SkpComponentInstanceDTO] = []
        inst_counts: Dict[int, int] = {}
        idx = 0

        while True:
            pos = model_bytes.find(cls.TAG_INSTANCE_TRANSFORM, idx)
            if pos == -1:
                break
            raw_m = struct.unpack_from("<13d", model_bytes, pos + 6)
            tx = raw_m[9] * 2.54
            ty = raw_m[10] * 2.54
            tz = raw_m[11] * 2.54

            # EntityID da instância (Tag 0x05de precedente)
            p_de = model_bytes.rfind(b"\xde\x05", max(0, pos - 1000), pos)
            inst_eid = None
            if p_de != -1:
                eid_len = struct.unpack_from("<I", model_bytes, p_de + 2)[0]
                if 1 <= eid_len <= 8:
                    inst_eid = int.from_bytes(model_bytes[p_de + 6 : p_de + 6 + eid_len], "little")

            inst_attrs = entity_attrs.get(inst_eid, {}) if inst_eid else {}

            p_def = model_bytes.find(cls.TAG_INSTANCE_DEF_REF, pos + 110, pos + 140)
            def_id = None
            def_name = "Componente"
            if p_def != -1:
                dlen = struct.unpack_from("<I", model_bytes, p_def + 2)[0]
                if 1 <= dlen <= 8:
                    def_id = int.from_bytes(model_bytes[p_def + 6 : p_def + 6 + dlen], "little")
                    def_name = defs_map.get(def_id, f"Def_{def_id}")
                    inst_counts[def_id] = inst_counts.get(def_id, 0) + 1

            # Matriz 4x4 column-major para consumo direto em THREE.Matrix4.fromArray()
            # (versao cm para telemetria e versao inches para o pipeline nativo do Three.js)
            mat_4x4 = [
                round(raw_m[0], 6), round(raw_m[1], 6), round(raw_m[2], 6), 0.0,
                round(raw_m[3], 6), round(raw_m[4], 6), round(raw_m[5], 6), 0.0,
                round(raw_m[6], 6), round(raw_m[7], 6), round(raw_m[8], 6), 0.0,
                round(tx, 3), round(ty, 3), round(tz, 3), round(raw_m[12], 6)
            ]
            mat_4x4_inches = [
                round(raw_m[0], 6), round(raw_m[1], 6), round(raw_m[2], 6), 0.0,
                round(raw_m[3], 6), round(raw_m[4], 6), round(raw_m[5], 6), 0.0,
                round(raw_m[6], 6), round(raw_m[7], 6), round(raw_m[8], 6), 0.0,
                round(raw_m[9], 4), round(raw_m[10], 4), round(raw_m[11], 4), round(raw_m[12], 6)
            ]

            instances.append({
                "id": inst_eid,
                "definition_id": def_id,
                "definition_name": def_name,
                "translation_cm": [round(tx, 2), round(ty, 2), round(tz, 2)],
                "matrix_4x4": mat_4x4,
                "matrix_4x4_inches": mat_4x4_inches,
                "offset": pos,
                "attributes": inst_attrs,
            })
            idx = pos + 1

        defs_list: List[SkpComponentDefinitionDTO] = [
            {
                "id": did,
                "name": dname,
                "instances_count": inst_counts.get(did, 0),
                "attributes": entity_attrs.get(did, {}),
            }
            for did, dname in defs_map.items()
        ]

        return {
            "definitions": defs_list,
            "instances": instances,
            "total_definitions": len(defs_list),
            "total_instances": len(instances),
            "model_attributes": model_attrs,
        }

    @classmethod
    def extract_attributes(cls, file_path: str) -> Optional[Dict[str, Any]]:
        """Extrai todos os dicionários de atributos e metadados de componentes dinâmicos
        (dynamic_attributes, SU_DefinitionSet, SU_InstanceSet, ModelProperties, etc)
        em milissegundos sem necessidade de carregar a malha geométrica."""
        if not file_path or not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception:
            return None

        model_bytes = cls._extract_model_dat(data)
        if not model_bytes:
            return None

        materials = cls.extract_materials(file_path)
        hierarchy = cls._parse_hierarchy(model_bytes)

        return {
            "model": hierarchy.get("model_attributes") or {},
            "definitions": {
                d["name"]: d.get("attributes", {})
                for d in hierarchy.get("definitions", [])
                if d.get("attributes")
            },
            "instances": [
                {
                    "id": inst.get("id"),
                    "definition_name": inst.get("definition_name"),
                    "translation_cm": inst.get("translation_cm"),
                    "attributes": inst.get("attributes", {}),
                }
                for inst in hierarchy.get("instances", [])
                if inst.get("attributes")
            ],
            "materials": {
                mname: mdata.get("attributes", {})
                for mname, mdata in materials.items()
                if mdata.get("attributes")
            },
        }

    @classmethod
    def extract_camera(cls, file_path: str) -> Optional[SkpCameraDTO]:
        """Extrai os parâmetros reais da Câmera 3D (Eye, Target, Up, FOV, Perspectiva)
        salvos pelo arquiteto no arquivo .skp."""
        if not file_path or not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception:
            return None
        model_bytes = cls._extract_model_dat(data)
        if not model_bytes:
            return None
        return cls._parse_camera(model_bytes)

    @classmethod
    def _parse_camera(cls, model_bytes: bytes) -> Optional[SkpCameraDTO]:
        """Decodifica a Câmera 3D diretamente do model.dat via Tag 0x34bd..0x34c6."""
        p_cam = model_bytes.find(cls.TAG_CAMERA_EYE)
        if p_cam == -1:
            return None

        # Eye Point3D (3 doubles em polegadas)
        eye_in = struct.unpack_from("<3d", model_bytes, p_cam + 6)
        eye_cm = [round(x * 2.54, 4) for x in eye_in]
        eye_inches = [round(x, 4) for x in eye_in]

        # Target Point3D (Tag 0x34be)
        target_cm = [0.0, 0.0, 0.0]
        target_inches = [0.0, 0.0, 0.0]
        p_tgt = model_bytes.find(cls.TAG_CAMERA_TARGET, p_cam, p_cam + 60)
        if p_tgt != -1:
            tgt_in = struct.unpack_from("<3d", model_bytes, p_tgt + 6)
            target_cm = [round(x * 2.54, 4) for x in tgt_in]
            target_inches = [round(x, 4) for x in tgt_in]

        # Up Vector3D (Tag 0x34bf)
        up = [0.0, 0.0, 1.0]
        p_up = model_bytes.find(cls.TAG_CAMERA_UP, p_cam, p_cam + 100)
        if p_up != -1:
            up_raw = struct.unpack_from("<3d", model_bytes, p_up + 6)
            up = [round(x, 6) for x in up_raw]

        # Perspective flag (Tag 0x34c2)
        perspective = True
        p_persp = model_bytes.find(cls.TAG_CAMERA_PERSPECTIVE, p_cam, p_cam + 130)
        if p_persp != -1:
            perspective = bool(model_bytes[p_persp + 6])

        # FOV (Tag 0x34c4)
        fov_deg = 35.0
        p_fov = model_bytes.find(cls.TAG_CAMERA_FOV, p_cam, p_cam + 160)
        if p_fov != -1:
            fov_deg = round(struct.unpack_from("<d", model_bytes, p_fov + 6)[0], 2)

        # FOV is Height (Tag 0x34c6)
        fov_is_height = True
        p_fov_h = model_bytes.find(cls.TAG_CAMERA_FOV_IS_HEIGHT, p_cam, p_cam + 180)
        if p_fov_h != -1:
            fov_is_height = bool(model_bytes[p_fov_h + 6])

        return {
            "eye_cm": eye_cm,
            "target_cm": target_cm,
            "eye_inches": eye_inches,
            "target_inches": target_inches,
            "up": up,
            "is_perspective": perspective,
            "fov_degrees": fov_deg,
            "fov_is_height": fov_is_height,
            "offset": p_cam,
        }

    @classmethod
    def extract_tags(cls, file_path: str) -> List[SkpTagDTO]:
        """Extrai as Etiquetas / Camadas (Layers / Tags) cadastradas no modelo .skp."""
        if not file_path or not os.path.exists(file_path):
            return []
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception:
            return []
        model_bytes = cls._extract_model_dat(data)
        if not model_bytes:
            return []
        return cls._parse_tags(model_bytes)

    @classmethod
    def _parse_tags(cls, model_bytes: bytes) -> List[SkpTagDTO]:
        """Varre o stream model.dat extraindo todas as Tags/Layers (Tag 0x3c8d e visibilidade 0x3c8e)."""
        tags: List[SkpTagDTO] = []
        seen_names = set()
        idx = 0
        buf_len = len(model_bytes)

        while True:
            p_name = model_bytes.find(cls.TAG_LAYER_NAME, idx)
            if p_name == -1 or p_name + 6 > buf_len:
                break

            slen = struct.unpack_from("<I", model_bytes, p_name + 2)[0]
            if 1 <= slen <= 120 and p_name + 6 + slen <= buf_len:
                raw_name = model_bytes[p_name + 6 : p_name + 6 + slen].decode("utf-8", errors="replace")
                tag_name = raw_name.strip("\x00").strip()
                if tag_name and tag_name not in seen_names:
                    seen_names.add(tag_name)

                    # Visibilidade (Tag 0x3c8e em até 50 bytes após o nome)
                    visible = True
                    p_vis = model_bytes.find(cls.TAG_LAYER_VISIBILITY, p_name + 6 + slen, min(buf_len, p_name + 6 + slen + 50))
                    if p_vis != -1:
                        # 0x00 = Visível, 0x01 = Oculta
                        visible = (model_bytes[p_vis + 6] == 0)

                    # EntityID (Tag 0x05de precedente)
                    tag_id = None
                    p_de = model_bytes.rfind(b"\xde\x05", max(0, p_name - 60), p_name)
                    if p_de != -1:
                        eid_len = struct.unpack_from("<I", model_bytes, p_de + 2)[0]
                        if 1 <= eid_len <= 8:
                            tag_id = int.from_bytes(model_bytes[p_de + 6 : p_de + 6 + eid_len], "little")

                    # Material associado (Tag 0x32cc do nome do material em até 100 bytes)
                    mat_name = None
                    p_mat = model_bytes.find(cls.TAG_LAYER_MAT_NAME, p_name + 6 + slen, min(buf_len, p_name + 6 + slen + 100))
                    if p_mat != -1:
                        mlen = struct.unpack_from("<I", model_bytes, p_mat + 2)[0]
                        if 1 <= mlen <= 120:
                            mat_name = model_bytes[p_mat + 6 : p_mat + 6 + mlen].decode("utf-8", errors="replace").strip("\x00")

                    is_default = (tag_name == "Layer0" or tag_name == "Sem etiquetas")
                    tags.append({
                        "id": tag_id,
                        "name": tag_name,
                        "visible": visible,
                        "is_default": is_default,
                        "material_name": mat_name,
                    })

            idx = p_name + 1

        return tags

    @classmethod
    def extract_mesh(cls, file_path: str) -> Optional[SkpMeshDTO]:
        """Reconstrói a malha poligonal 3D completa com UVs, Normais, Materiais
        e Árvore Hierárquica de Instâncias diretamente do .skp para Three.js / WebGL."""
        if not file_path or not os.path.exists(file_path):
            return None

        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception:
            return None

        model_bytes = cls._extract_model_dat(data)
        if not model_bytes:
            return None

        # 0. Materiais XML, Hierarquia de Instâncias, Câmera e Tags/Layers
        materials_dict = cls.extract_materials(file_path)
        hierarchy_data = cls._parse_hierarchy(model_bytes)
        camera_data = cls._parse_camera(model_bytes)
        tags_data = cls._parse_tags(model_bytes)

        # Mapeamento interno: Material EntityID -> Material Name no model.dat
        mat_id_to_name: Dict[int, str] = {}
        idx = 0
        while True:
            pos = model_bytes.find(cls.TAG_MATERIAL_DEF, idx)
            if pos == -1:
                break
            rec_len = struct.unpack_from("<I", model_bytes, pos + 2)[0]
            rec_data = model_bytes[pos + 6 : pos + 6 + rec_len]
            de_idx = rec_data.find(b"\xde\x05")
            cc_idx = rec_data.find(b"\xcc\x32")
            if de_idx != -1 and cc_idx != -1:
                id_len = struct.unpack_from("<I", rec_data, de_idx + 2)[0]
                m_id = int.from_bytes(rec_data[de_idx + 6 : de_idx + 6 + id_len], "little")
                str_len = struct.unpack_from("<I", rec_data, cc_idx + 2)[0]
                m_name = rec_data[cc_idx + 6 : cc_idx + 6 + str_len].decode("utf-8", errors="replace")
                mat_id_to_name[m_id] = m_name
            idx = pos + 1

        # 1. Parse de Vértices: ID -> (X_cm, Y_cm, Z_cm, X_in, Y_in, Z_in)
        vertices_map: Dict[int, Tuple[float, float, float, float, float, float]] = {}
        idx = 0
        min_x, max_x = float("inf"), float("-inf")
        min_y, max_y = float("inf"), float("-inf")
        min_z, max_z = float("inf"), float("-inf")

        while True:
            pos = model_bytes.find(cls.TAG_VERTEX, idx)
            if pos == -1:
                break
            de_pos = model_bytes.find(b"\xde\x05", pos, pos + 25)
            if de_pos != -1:
                id_len = struct.unpack_from("<I", model_bytes, de_pos + 2)[0]
                if 1 <= id_len <= 8:
                    eid = int.from_bytes(model_bytes[de_pos + 6 : de_pos + 6 + id_len], "little")
                    c5_pos = de_pos + 6 + id_len
                    if model_bytes[c5_pos : c5_pos + 6] == b"\xc5\x09\x18\x00\x00\x00":
                        x, y, z = struct.unpack_from("<3d", model_bytes, c5_pos + 6)
                        if not (x != x or y != y or z != z):
                            cx = x * 2.54
                            cy = y * 2.54
                            cz = z * 2.54
                            vertices_map[eid] = (cx, cy, cz, x, y, z)
                            if cx < min_x: min_x = cx
                            if cx > max_x: max_x = cx
                            if cy < min_y: min_y = cy
                            if cy > max_y: max_y = cy
                            if cz < min_z: min_z = cz
                            if cz > max_z: max_z = cz
            idx = pos + 1

        if not vertices_map:
            return None

        # 2. Parse de Arestas: EdgeID -> (StartVertexID, EndVertexID)
        edges_map: Dict[int, Tuple[int, int]] = {}
        idx = 0
        while True:
            pos = model_bytes.find(cls.TAG_EDGE_START, idx)
            if pos == -1:
                break
            de_pos = model_bytes.rfind(b"\xde\x05", max(0, pos - 30), pos)
            if de_pos != -1:
                edge_id_len = struct.unpack_from("<I", model_bytes, de_pos + 2)[0]
                if 1 <= edge_id_len <= 8:
                    edge_id = int.from_bytes(model_bytes[de_pos + 6 : de_pos + 6 + edge_id_len], "little")
                    v1_len = struct.unpack_from("<I", model_bytes, pos + 2)[0]
                    if 1 <= v1_len <= 8:
                        v1 = int.from_bytes(model_bytes[pos + 6 : pos + 6 + v1_len], "little")
                        ba_pos = pos + 6 + v1_len
                        if model_bytes[ba_pos : ba_pos + 2] == cls.TAG_EDGE_END:
                            v2_len = struct.unpack_from("<I", model_bytes, ba_pos + 2)[0]
                            if 1 <= v2_len <= 8:
                                v2 = int.from_bytes(model_bytes[ba_pos + 6 : ba_pos + 6 + v2_len], "little")
                                edges_map[edge_id] = (v1, v2)
            idx = pos + 1

        # 3. Parse de Faces, Loops, UVs e Materiais
        idx = 0
        flat_vertices: List[float] = []
        flat_normals: List[float] = []
        flat_uvs: List[float] = []
        indices: List[int] = []
        face_materials: List[str] = []
        face_ranges: List[Dict[str, Any]] = []
        vert_counter = 0
        face_count = 0

        while True:
            pos = model_bytes.find(cls.TAG_PLANE, idx)
            if pos == -1:
                break
            nx, ny, nz, d = struct.unpack_from("<dddd", model_bytes, pos + 6)

            # Material da Face: procura Tag 0x0daf (Front) ou Tag 0x07d1
            face_mat_name = "Default"
            af_pos = model_bytes.rfind(cls.TAG_FRONT_MAT, max(0, pos - 30), pos)
            if af_pos != -1:
                af_len = struct.unpack_from("<I", model_bytes, af_pos + 2)[0]
                if 1 <= af_len <= 8:
                    m_eid = int.from_bytes(model_bytes[af_pos + 6 : af_pos + 6 + af_len], "little")
                    face_mat_name = mat_id_to_name.get(m_eid, face_mat_name)
            else:
                d1_pos = model_bytes.rfind(b"\xd1\x07", max(0, pos - 30), pos)
                if d1_pos != -1:
                    d1_len = struct.unpack_from("<I", model_bytes, d1_pos + 2)[0]
                    if 1 <= d1_len <= 8:
                        m_eid = int.from_bytes(model_bytes[d1_pos + 6 : d1_pos + 6 + d1_len], "little")
                        face_mat_name = mat_id_to_name.get(m_eid, face_mat_name)

            # Matriz UV da Face
            uv_matrix: Optional[Tuple[float, ...]] = None
            next_plane = model_bytes.find(cls.TAG_PLANE, pos + 1)
            search_limit = min(pos + 1000, next_plane if next_plane != -1 else len(model_bytes))
            m_pos = model_bytes.find(cls.TAG_UV_MATRIX, pos, search_limit)
            if m_pos != -1:
                try:
                    uv_matrix = struct.unpack_from("<9d", model_bytes, m_pos + 6)
                except Exception:
                    uv_matrix = None

            x_scale = 1.0
            y_scale = 1.0
            if face_mat_name in materials_dict:
                x_scale = materials_dict[face_mat_name]["xScale"] or 1.0
                y_scale = materials_dict[face_mat_name]["yScale"] or 1.0

            # Loops Half-Edge (busca acelerada via find())
            scan_off = pos + 38
            loop_edges: List[Tuple[int, int]] = []
            loop_limit = min(len(model_bytes) - 15, pos + 500)
            while scan_off < loop_limit:
                a0_pos = model_bytes.find(b"\xa0\x0f", scan_off, loop_limit)
                if a0_pos == -1:
                    break

                # Verifica delimitadores de fim de plano antes do proximo a0_pos
                d_ad = model_bytes.find(b"\xad\x0d", scan_off, a0_pos)
                d_d0 = model_bytes.find(b"\xd0\x07", scan_off, a0_pos)
                d_ac = model_bytes.find(b"\xac\x0d", scan_off, a0_pos)
                delims = [p for p in (d_ad, d_d0, d_ac) if p != -1]
                if delims:
                    break

                a1_pos = model_bytes.find(b"\xa1\x0f", a0_pos, a0_pos + 10)
                if a1_pos != -1:
                    e_len = struct.unpack_from("<I", model_bytes, a1_pos + 2)[0]
                    if 1 <= e_len <= 8:
                        e_id = int.from_bytes(model_bytes[a1_pos + 6 : a1_pos + 6 + e_len], "little")
                        a2_pos = a1_pos + 6 + e_len
                        direction = 0
                        if model_bytes[a2_pos : a2_pos + 2] == b"\xa2\x0f":
                            direction = model_bytes[a2_pos + 6]
                            scan_off = a2_pos + 7
                        else:
                            scan_off = a2_pos
                        loop_edges.append((e_id, direction))
                        continue
                scan_off = a0_pos + 2

            poly_coords: List[Tuple[float, float, float, float, float, float]] = []
            for e_id, direction in loop_edges:
                if e_id in edges_map:
                    v_start, v_end = edges_map[e_id]
                    v_actual = v_start if direction == 0 else v_end
                    if v_actual in vertices_map:
                        poly_coords.append(vertices_map[v_actual])

            if len(poly_coords) >= 3:
                face_count += 1
                face_materials.append(face_mat_name)
                base_idx = vert_counter

                for pt in poly_coords:
                    cx, cy, cz, ix, iy, iz = pt
                    flat_vertices.extend([round(cx, 3), round(cy, 3), round(cz, 3)])
                    flat_normals.extend([round(nx, 3), round(ny, 3), round(nz, 3)])

                    if uv_matrix:
                        raw_u = uv_matrix[0] * ix + uv_matrix[3] * iy + uv_matrix[6]
                        raw_v = uv_matrix[1] * ix + uv_matrix[4] * iy + uv_matrix[7]
                        u = raw_u / x_scale
                        v = raw_v / y_scale
                    else:
                        if abs(nz) > 0.5:
                            u, v = cx / 100.0, cy / 100.0
                        elif abs(ny) > 0.5:
                            u, v = cx / 100.0, cz / 100.0
                        else:
                            u, v = cy / 100.0, cz / 100.0

                    flat_uvs.extend([round(u, 4), round(v, 4)])
                    vert_counter += 1

                tri_start = len(indices) // 3
                num_triangles = len(poly_coords) - 2
                for k in range(1, len(poly_coords) - 1):
                    indices.extend([base_idx, base_idx + k, base_idx + k + 1])

                face_ranges.append({
                    "face_id": f"face_{face_count}",
                    "triangle_start": tri_start,
                    "triangle_count": num_triangles,
                    "material_name": face_mat_name,
                })

            idx = pos + 1

        bounds: SkpBoundsInfo = {
            "num_vertices": len(vertices_map),
            "largura_cm": round((max_x - min_x), 2) if max_x != float("-inf") else 0.0,
            "profundidade_cm": round((max_y - min_y), 2) if max_y != float("-inf") else 0.0,
            "altura_cm": round((max_z - min_z), 2) if max_z != float("-inf") else 0.0,
            "min_pt_cm": (round(min_x, 2), round(min_y, 2), round(min_z, 2)) if min_x != float("inf") else (0.0, 0.0, 0.0),
            "max_pt_cm": (round(max_x, 2), round(max_y, 2), round(max_z, 2)) if max_x != float("-inf") else (0.0, 0.0, 0.0),
            "is_empty": (face_count == 0),
        }

        return {
            "vertices": flat_vertices,
            "normals": flat_normals,
            "uvs": flat_uvs,
            "indices": indices,
            "materials": materials_dict,
            "face_materials": face_materials,
            "face_ranges": face_ranges,
            "num_faces": face_count,
            "num_vertices": vert_counter,
            "bounds": bounds,
            "hierarchy": hierarchy_data,
            "camera": camera_data,
            "tags": tags_data,
        }

    @classmethod
    def _extract_model_dat(cls, data: bytes) -> Optional[bytes]:
        """Localiza e descompacta o arquivo interno 'model.dat' de dentro do container ZIP."""
        idx = 0
        sig = cls.ZIP_LOCAL_HEADER
        data_len = len(data)

        while True:
            pos = data.find(sig, idx)
            if pos == -1 or pos + 30 > data_len:
                break

            header = data[pos : pos + 30]
            comp_method, = struct.unpack_from("<H", header, 8)
            comp_size, uncomp_size, fn_len, extra_len = struct.unpack_from("<IIHH", header, 18)

            if pos + 30 + fn_len > data_len:
                break

            fn = data[pos + 30 : pos + 30 + fn_len].decode("utf-8", errors="ignore")
            if fn == "model.dat":
                data_offset = pos + 30 + fn_len + extra_len
                if data_offset + comp_size > data_len:
                    break

                raw_comp = data[data_offset : data_offset + comp_size]
                if comp_method == 8:
                    try:
                        return zlib.decompress(raw_comp, -15)
                    except Exception:
                        return None
                else:
                    return raw_comp

            idx = pos + 1

        return None
