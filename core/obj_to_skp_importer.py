"""
Importador de Modelos 3D Wavefront OBJ para .SKP Nativo (Zero DLL).

Faz o parsing de arquivos .obj e gera diretamente topologia B-Rep
manifold no model.dat do SketchUp:
- Parsing de vértices ('v x y z').
- Parsing de faces ('f v1[/vt1/vn1] v2 v3 ...').
- Cálculo de equações de planos analíticos Ax + By + Cz + D = 0.
- Injeção direta no container ZIP do .SKP em Pure Python.
"""

import os
from typing import Dict, Any, List, Tuple
from core.skp_binary_writer import SkpBinaryWriter


class ObjToSkpImporter:
    """Conversor e importador nativo de arquivos OBJ para arquivos .skp."""

    @classmethod
    def parse_obj(cls, obj_text_or_path: str) -> Dict[str, Any]:
        """Faz o parsing do arquivo OBJ e extrai vértices e faces poligonais."""
        if os.path.exists(obj_text_or_path):
            with open(obj_text_or_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        else:
            lines = obj_text_or_path.splitlines()

        vertices = []
        faces = []

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            cmd = parts[0]

            if cmd == "v":
                # Vértice 3D (x, y, z)
                vx = float(parts[1])
                vy = float(parts[2])
                vz = float(parts[3])
                vertices.append((vx, vy, vz))

            elif cmd == "f":
                # Face: lista de índices de vértices (1-based no OBJ)
                face_idx = []
                for p in parts[1:]:
                    v_str = p.split("/")[0]
                    v_idx = int(v_str)
                    # Tratamento de índices negativos (relativos)
                    if v_idx < 0:
                        v_idx = len(vertices) + v_idx + 1
                    face_idx.append(v_idx - 1)  # 0-based
                if len(face_idx) >= 3:
                    faces.append(face_idx)

        return {
            "vertices": vertices,
            "faces": faces,
            "vertex_count": len(vertices),
            "face_count": len(faces),
        }

    @classmethod
    def import_obj_to_skp(cls, obj_path: str, scale: float = 1.0) -> Dict[str, Any]:
        """Importa o modelo OBJ para a sessão binária ativa do SketchBuild."""
        parsed = cls.parse_obj(obj_path)
        vertices = parsed["vertices"]
        faces = parsed["faces"]

        if not vertices or not faces:
            raise ValueError("Arquivo OBJ não contém geometria válida (vértices ou faces ausentes).")

        # Escala os vértices se necessário
        scaled_verts = [(v[0] * scale, v[1] * scale, v[2] * scale) for v in vertices]

        # Cria as faces na sessão binária
        created_faces_count = 0
        for f_indices in faces:
            face_pts = [scaled_verts[idx] for idx in f_indices]
            try:
                SkpBinaryWriter.add_polygon_face(face_pts)
                created_faces_count += 1
            except Exception:
                # Pula faces degeneradas ou colineares
                continue

        return {
            "success": True,
            "imported_vertices": len(vertices),
            "imported_faces": created_faces_count,
            "scale": scale,
        }
