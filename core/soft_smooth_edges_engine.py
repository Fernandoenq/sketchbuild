"""Engine de Engenharia Reversa da Caixa de Dialogo Suavizar Arestas (Soften / Smooth Edges).

Controla a suavizacao visual de arestas e o calculo de normais medias
para sombreamento Gouraud/Phong de acordo com o angulo limite diedrico.
"""

from __future__ import annotations
import math
from typing import Any


class SoftSmoothEdgesEngine:
    """Implementa o algoritmo de suavizacao de arestas (Soft/Smooth Edges) do SketchUp."""

    @staticmethod
    def _compute_face_normal(v0: list[float], v1: list[float], v2: list[float]) -> list[float]:
        """Calcula o vetor normal unitario de um triangulo 3D."""
        ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
        bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]
        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        norm = math.sqrt(nx * nx + ny * ny + nz * nz)
        if norm < 1e-12:
            return [0.0, 0.0, 1.0]
        return [nx / norm, ny / norm, nz / norm]

    @classmethod
    def process_soft_smooth(
        cls,
        vertices: list[list[float]],
        triangles: list[list[int]],
        max_angle_deg: float = 35.0,
        soften_coplanar: bool = True,
        smooth_normals: bool = True,
    ) -> dict[str, Any]:
        """Classifica arestas em suaves/duras e gera normais de vertices interpoladas."""
        if not vertices or not triangles:
            return {
                "success": False,
                "edges_soft_count": 0,
                "edges_hard_count": 0,
                "smoothed_vertex_normals": [],
            }

        # 1. Calcula normal de cada face
        face_normals = []
        for tri in triangles:
            n = cls._compute_face_normal(vertices[tri[0]], vertices[tri[1]], vertices[tri[2]])
            face_normals.append(n)

        # 2. Mapeia arestas -> faces adjacentes
        edge_to_faces: dict[tuple[int, int], list[int]] = {}
        for face_idx, tri in enumerate(triangles):
            for i in range(3):
                idx_a, idx_b = tri[i], tri[(i + 1) % 3]
                edge_key = (min(idx_a, idx_b), max(idx_a, idx_b))
                if edge_key not in edge_to_faces:
                    edge_to_faces[edge_key] = []
                edge_to_faces[edge_key].append(face_idx)

        # 3. Classifica as arestas
        rad_limit = math.radians(max_angle_deg)
        cos_limit = math.cos(rad_limit)

        soft_edges = []
        hard_edges = []

        # Mapeia quais faces compartilham suavizacao por vertice
        vertex_shared_normals: list[list[list[float]]] = [[] for _ in range(len(vertices))]

        for (v_a, v_b), faces in edge_to_faces.items():
            if len(faces) == 2:
                n1 = face_normals[faces[0]]
                n2 = face_normals[faces[1]]
                dot = max(-1.0, min(1.0, n1[0] * n2[0] + n1[1] * n2[1] + n1[2] * n2[2]))
                is_coplanar = abs(dot - 1.0) < 1e-4

                is_soft = False
                if is_coplanar and soften_coplanar:
                    is_soft = True
                elif dot >= cos_limit:
                    is_soft = True

                if is_soft:
                    soft_edges.append([v_a, v_b])
                    if smooth_normals:
                        vertex_shared_normals[v_a].extend([n1, n2])
                        vertex_shared_normals[v_b].extend([n1, n2])
                else:
                    hard_edges.append([v_a, v_b])
            else:
                # Aresta de borda (boundary)
                hard_edges.append([v_a, v_b])

        # 4. Gera normais de vertice suavizadas
        vertex_normals = []
        for v_idx in range(len(vertices)):
            normals_pool = vertex_shared_normals[v_idx]
            if normals_pool and smooth_normals:
                avg_x = sum(n[0] for n in normals_pool) / len(normals_pool)
                avg_y = sum(n[1] for n in normals_pool) / len(normals_pool)
                avg_z = sum(n[2] for n in normals_pool) / len(normals_pool)
                norm = math.sqrt(avg_x * avg_x + avg_y * avg_y + avg_z * avg_z)
                if norm > 1e-12:
                    vertex_normals.append([round(avg_x / norm, 4), round(avg_y / norm, 4), round(avg_z / norm, 4)])
                else:
                    vertex_normals.append([0.0, 0.0, 1.0])
            else:
                vertex_normals.append([0.0, 0.0, 1.0])

        return {
            "success": True,
            "max_angle_deg": float(max_angle_deg),
            "soften_coplanar": soften_coplanar,
            "smooth_normals": smooth_normals,
            "total_edges": len(edge_to_faces),
            "edges_soft_count": len(soft_edges),
            "edges_hard_count": len(hard_edges),
            "soft_edges": soft_edges,
            "hard_edges": hard_edges,
            "vertex_normals": vertex_normals,
        }
