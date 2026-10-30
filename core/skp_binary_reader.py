"""
SketchBuild - Leitor Binário Nativo de Arquivos .SKP (Pure Python / Zero DLL)

Decodifica a topologia analítica do SketchUp diretamente do stream 'model.dat'
embutido no container ZIP (.skp). Não depende de SketchUpAPI.dll, ctypes ou
SketchUp Desktop instalado.

Descoberta de engenharia reversa:
- Tag 0x09c4 (tamanho 46B): Vértice com EntityID (uint32) e Point3D (3 doubles de 64 bits em polegadas).
- Tag 0x0bb9 / 0x0bba: StartVertex e EndVertex da Aresta (Edge).
- Tag 0x0dad (tamanho 32B): Equação cartesiana do plano 3D (Ax + By + Cz + D = 0).
- Tag 0x0fa0: Loop de arestas com flag de direção (0 ou 1) que orienta o contorno Half-Edge.
"""

from __future__ import annotations
import zlib
import struct
import os
from typing import TypedDict, Optional, Tuple, List, Dict, Any


class SkpBoundsInfo(TypedDict):
    num_vertices: int
    largura_cm: float
    profundidade_cm: float
    altura_cm: float
    min_pt_cm: Tuple[float, float, float]
    max_pt_cm: Tuple[float, float, float]
    is_empty: bool


class SkpMeshDTO(TypedDict):
    vertices: List[float]  # [x, y, z, x, y, z, ...] em cm
    normals: List[float]   # [nx, ny, nz, ...]
    indices: List[int]     # [i0, i1, i2, ...]
    num_faces: int
    num_vertices: int
    bounds: SkpBoundsInfo


class SkpBinaryReader:
    TAG_VERTEX = b"\xc4\x09\x2e\x00\x00\x00"
    TAG_EDGE_VTX = b"\xb9\x0b\x04\x00\x00\x00"
    TAG_PLANE = b"\xad\x0d\x20\x00\x00\x00"
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

        if len(data) < 30:
            return None

        model_bytes = cls._extract_model_dat(data)
        if not model_bytes or len(model_bytes) < 50:
            return None

        tag = cls.TAG_VERTEX
        idx = 0
        min_x, max_x = float("inf"), float("-inf")
        min_y, max_y = float("inf"), float("-inf")
        min_z, max_z = float("inf"), float("-inf")
        count = 0
        buf_len = len(model_bytes)

        while True:
            pos = model_bytes.find(tag, idx)
            if pos == -1 or pos + 52 > buf_len:
                break

            try:
                x, y, z = struct.unpack_from("<ddd", model_bytes, pos + 28)
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
    def extract_mesh(cls, file_path: str) -> Optional[SkpMeshDTO]:
        """Reconstrói a malha poligonal 3D completa (Vértices, Normais e Triângulos)
        diretamente do model.dat para consumo no Three.js / WebGL BufferGeometry."""
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

        # 1. Parse de Vértices: ID -> (X, Y, Z) em cm
        vertices_map: Dict[int, Tuple[float, float, float]] = {}
        idx = 0
        tag_v = cls.TAG_VERTEX
        min_x, max_x = float("inf"), float("-inf")
        min_y, max_y = float("inf"), float("-inf")
        min_z, max_z = float("inf"), float("-inf")

        while True:
            pos = model_bytes.find(tag_v, idx)
            if pos == -1:
                break
            eid = struct.unpack_from("<I", model_bytes, pos + 18)[0]
            x, y, z = struct.unpack_from("<ddd", model_bytes, pos + 28)
            if not (x != x or y != y or z != z):
                cx = x * 2.54
                cy = y * 2.54
                cz = z * 2.54
                vertices_map[eid] = (cx, cy, cz)
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
        tag_edge = cls.TAG_EDGE_VTX
        first_plane_pos = model_bytes.find(cls.TAG_PLANE)
        edge_limit = first_plane_pos if first_plane_pos != -1 else len(model_bytes)

        while True:
            pos = model_bytes.find(tag_edge, idx)
            if pos == -1 or pos >= edge_limit:
                break
            v1 = struct.unpack_from("<I", model_bytes, pos + 6)[0]
            if model_bytes[pos + 10 : pos + 16] == b"\xba\x0b\x04\x00\x00\x00":
                v2 = struct.unpack_from("<I", model_bytes, pos + 16)[0]
                edge_id = struct.unpack_from("<I", model_bytes, pos - 20)[0]
                edges_map[edge_id] = (v1, v2)
            idx = pos + 1

        # 3. Parse de Faces e Loops
        tag_p = cls.TAG_PLANE
        idx = 0
        flat_vertices: List[float] = []
        flat_normals: List[float] = []
        indices: List[int] = []
        vert_counter = 0
        face_count = 0

        while True:
            pos = model_bytes.find(tag_p, idx)
            if pos == -1:
                break
            nx, ny, nz, d = struct.unpack_from("<dddd", model_bytes, pos + 6)

            # Extrai os itens do Loop Half-Edge
            scan_off = pos + 38
            loop_edges: List[Tuple[int, int]] = []
            while scan_off < min(len(model_bytes) - 20, pos + 300):
                if model_bytes[scan_off : scan_off + 2] == b"\xa0\x0f":
                    e_id = struct.unpack_from("<I", model_bytes, scan_off + 12)[0]
                    direction = model_bytes[scan_off + 22] if scan_off + 22 < len(model_bytes) else 0
                    loop_edges.append((e_id, direction))
                    scan_off += 23
                elif model_bytes[scan_off : scan_off + 2] in [b"\xad\x0d", b"\xd0\x07"]:
                    break
                else:
                    scan_off += 1

            # Resolve contorno ordenado de vértices
            poly_coords: List[Tuple[float, float, float]] = []
            for e_id, direction in loop_edges:
                if e_id in edges_map:
                    v_start, v_end = edges_map[e_id]
                    v_actual = v_start if direction == 0 else v_end
                    if v_actual in vertices_map:
                        poly_coords.append(vertices_map[v_actual])

            if len(poly_coords) >= 3:
                face_count += 1
                base_idx = vert_counter
                # Adiciona vértices e normais da face
                for pt in poly_coords:
                    flat_vertices.extend([round(pt[0], 3), round(pt[1], 3), round(pt[2], 3)])
                    flat_normals.extend([round(nx, 3), round(ny, 3), round(nz, 3)])
                    vert_counter += 1

                # Triangulação Fan: (0, 1, 2), (0, 2, 3), ...
                for k in range(1, len(poly_coords) - 1):
                    indices.extend([base_idx, base_idx + k, base_idx + k + 1])

            idx = pos + 1

        bounds: SkpBoundsInfo = {
            "num_vertices": len(vertices_map),
            "largura_cm": round((max_x - min_x), 2),
            "profundidade_cm": round((max_y - min_y), 2),
            "altura_cm": round((max_z - min_z), 2),
            "min_pt_cm": (round(min_x, 2), round(min_y, 2), round(min_z, 2)),
            "max_pt_cm": (round(max_x, 2), round(max_y, 2), round(max_z, 2)),
            "is_empty": (face_count == 0),
        }

        return {
            "vertices": flat_vertices,
            "normals": flat_normals,
            "indices": indices,
            "num_faces": face_count,
            "num_vertices": vert_counter,
            "bounds": bounds,
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
