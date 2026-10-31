"""Engine de Engenharia Reversa da Ferramenta Adicionar Detalhe (Add Detail Tool) da Caixa de Areia.

Subdivide localmente arestas e faces de malhas de relevo TIN para aumentar a resolucao
poligonal onde o modelador necessita de maior definicao organica.
"""

from __future__ import annotations
import math
from typing import Any


class AddDetailSandboxEngine:
    """Implementa o refinamento e subdivisao local de malhas TIN do SketchUp."""

    @staticmethod
    def _dist_sq_3d(p0: list[float], p1: list[float]) -> float:
        return (p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2 + (p0[2] - p1[2]) ** 2

    @classmethod
    def subdivide_edge(
        cls,
        tin_vertices: list[list[float]],
        tin_triangles: list[list[int]],
        edge_v0: int,
        edge_v1: int
    ) -> dict[str, Any]:
        """Subdivide a aresta compartilhada (edge_v0, edge_v1), criando novo vertice e 4 triangulos."""
        v_a = min(edge_v0, edge_v1)
        v_b = max(edge_v0, edge_v1)

        p_a = tin_vertices[v_a]
        p_b = tin_vertices[v_b]
        p_mid = [
            round((p_a[0] + p_b[0]) * 0.5, 4),
            round((p_a[1] + p_b[1]) * 0.5, 4),
            round((p_a[2] + p_b[2]) * 0.5, 4),
        ]

        new_vertices = [list(v) for v in tin_vertices]
        mid_idx = len(new_vertices)
        new_vertices.append(p_mid)

        # Encontra triangulos que compartilham a aresta (v_a, v_b)
        adj_tri_indices = []
        for idx, tri in enumerate(tin_triangles):
            if v_a in tri and v_b in tri:
                adj_tri_indices.append(idx)

        new_triangles = []
        for idx, tri in enumerate(tin_triangles):
            if idx in adj_tri_indices:
                # Opcional terceiro vertice do triangulo
                other_v = [v for v in tri if v != v_a and v != v_b][0]
                # Gera 2 novos triangulos preservando orientacao CCW aproximada
                new_triangles.append([v_a, mid_idx, other_v])
                new_triangles.append([mid_idx, v_b, other_v])
            else:
                new_triangles.append(tri)

        return {
            "success": True,
            "mode": "EDGE_SUBDIVISION",
            "new_vertex_index": mid_idx,
            "new_vertex_xyz": p_mid,
            "affected_triangles_count": len(adj_tri_indices),
            "total_vertices": len(new_vertices),
            "total_triangles": len(new_triangles),
            "vertices": new_vertices,
            "triangles": new_triangles,
        }

    @classmethod
    def subdivide_face_at_point(
        cls,
        tin_vertices: list[list[float]],
        tin_triangles: list[list[int]],
        triangle_index: int,
        custom_point_xyz: list[float] | None = None
    ) -> dict[str, Any]:
        """Subdivide o triangulo em 3 triangulos menores a partir do baricentro ou ponto indicado."""
        if triangle_index < 0 or triangle_index >= len(tin_triangles):
            return {
                "success": False,
                "message": f"Indice de triangulo invalido: {triangle_index}"
            }

        tri = tin_triangles[triangle_index]
        v0, v1, v2 = tri[0], tri[1], tri[2]

        if custom_point_xyz is not None:
            pt = [round(float(c), 4) for c in custom_point_xyz]
        else:
            p0, p1, p2 = tin_vertices[v0], tin_vertices[v1], tin_vertices[v2]
            pt = [
                round((p0[0] + p1[0] + p2[0]) / 3.0, 4),
                round((p0[1] + p1[1] + p2[1]) / 3.0, 4),
                round((p0[2] + p1[2] + p2[2]) / 3.0, 4),
            ]

        new_vertices = [list(v) for v in tin_vertices]
        center_idx = len(new_vertices)
        new_vertices.append(pt)

        new_triangles = []
        for idx, t in enumerate(tin_triangles):
            if idx == triangle_index:
                new_triangles.append([v0, v1, center_idx])
                new_triangles.append([v1, v2, center_idx])
                new_triangles.append([v2, v0, center_idx])
            else:
                new_triangles.append(t)

        return {
            "success": True,
            "mode": "FACE_SUBDIVISION",
            "new_vertex_index": center_idx,
            "new_vertex_xyz": pt,
            "triangle_index": triangle_index,
            "total_vertices": len(new_vertices),
            "total_triangles": len(new_triangles),
            "vertices": new_vertices,
            "triangles": new_triangles,
        }
