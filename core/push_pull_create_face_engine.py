"""Engine de Engenharia Reversa do Push/Pull com Nova Face (Ctrl + Push/Pull Tool).

Reproduz a extrusao parametrica do SketchUp com a tecla modificadora Ctrl (cursor com +),
que preserva a face original como uma divisao interna estanque e sintetiza o novo solido prismatico.
"""

from __future__ import annotations
import math
from typing import Any


class PushPullCreateFaceEngine:
    """Implementa a extrusao analitica preservando a face base intacta (Ctrl + Push/Pull)."""

    @staticmethod
    def _compute_polygon_normal(polygon_vertices: list[list[float]]) -> list[float]:
        """Calcula a normal unitaria do poligono plano usando a formula de Newell."""
        nx = 0.0
        ny = 0.0
        nz = 0.0
        n = len(polygon_vertices)
        for i in range(n):
            curr_v = polygon_vertices[i]
            next_v = polygon_vertices[(i + 1) % n]
            nx += (curr_v[1] - next_v[1]) * (curr_v[2] + next_v[2])
            ny += (curr_v[2] - next_v[2]) * (curr_v[0] + next_v[0])
            nz += (curr_v[0] - next_v[0]) * (curr_v[1] + next_v[1])
        norm = math.sqrt(nx * nx + ny * ny + nz * nz)
        if norm < 1e-12:
            return [0.0, 0.0, 1.0]
        return [nx / norm, ny / norm, nz / norm]

    @classmethod
    def extrude_with_new_face(
        cls,
        face_vertices: list[list[float]],
        distance_m: float,
        create_new_face: bool = True
    ) -> dict[str, Any]:
        """Extruda a face plana gerando o solido B-Rep, mantendo a face inicial."""
        n = len(face_vertices)
        if n < 3:
            return {
                "success": False,
                "vertices": [],
                "triangles": [],
                "volume_m3": 0.0,
            }

        normal = cls._compute_polygon_normal(face_vertices)
        dist = float(distance_m)

        # 1. Base (face original)
        base_verts = [[float(c) for c in v] for v in face_vertices]

        # 2. Topo (vertices deslocados ao longo da normal)
        top_verts = []
        for v in base_verts:
            top_verts.append([
                v[0] + dist * normal[0],
                v[1] + dist * normal[1],
                v[2] + dist * normal[2],
            ])

        all_vertices = base_verts + top_verts
        triangles = []

        # Face base (se create_new_face=True, fecha a base com triangulacao invertida para fora)
        if create_new_face:
            for i in range(1, n - 1):
                triangles.append([0, i + 1, i])

        # Face superior (topo)
        for i in range(1, n - 1):
            triangles.append([n, n + i, n + i + 1])

        # Faces laterais (2 triangulos por aresta lateral)
        for i in range(n):
            next_i = (i + 1) % n
            b0 = i
            b1 = next_i
            t0 = n + i
            t1 = n + next_i

            triangles.append([b0, b1, t1])
            triangles.append([b0, t1, t0])

        # Area da base via formula vetorial de Newell
        t1 = sum((base_verts[i][1] - base_verts[(i+1)%n][1]) * (base_verts[i][2] + base_verts[(i+1)%n][2]) for i in range(n))
        t2 = sum((base_verts[i][2] - base_verts[(i+1)%n][2]) * (base_verts[i][0] + base_verts[(i+1)%n][0]) for i in range(n))
        t3 = sum((base_verts[i][0] - base_verts[(i+1)%n][0]) * (base_verts[i][1] + base_verts[(i+1)%n][1]) for i in range(n))
        base_area = 0.5 * math.sqrt(t1 * t1 + t2 * t2 + t3 * t3)
        volume = abs(base_area * dist)

        return {
            "success": True,
            "ctrl_modifier_active": create_new_face,
            "extrusion_distance_m": dist,
            "normal_vector": [round(c, 4) for c in normal],
            "base_area_m2": round(base_area, 4),
            "volume_m3": round(volume, 4),
            "total_vertices": len(all_vertices),
            "total_triangles": len(triangles),
            "vertices": [[round(c, 4) for c in pt] for pt in all_vertices],
            "triangles": triangles,
        }
