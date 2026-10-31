"""Engine de Engenharia Reversa da Ferramenta Girar Aresta (Flip Edge Tool) da Caixa de Areia.

Inverte a diagonal comum entre dois triangulos adjacentes de uma malha TIN (AC -> BD),
alterando o sentido da crista ou fluxo de escoamento sem alterar a contagem de vertices.
"""

from __future__ import annotations
import math
from typing import Any


class FlipEdgeSandboxEngine:
    """Implementa a inversao de arestas diagonais em malhas TIN do SketchUp."""

    @staticmethod
    def _is_convex_quad(
        p0: list[float],
        p1: list[float],
        p2: list[float],
        p3: list[float]
    ) -> bool:
        """Verifica se o quadrilatero 2D no plano XY e estritamente convexo."""
        def cross2d(o: list[float], a: list[float], b: list[float]) -> float:
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        pts = [p0, p1, p2, p3]
        signs = []
        for i in range(4):
            c = cross2d(pts[i], pts[(i + 1) % 4], pts[(i + 2) % 4])
            if abs(c) > 1e-6:
                signs.append(c > 0)
        return len(signs) == 4 and (all(signs) or not any(signs))

    @classmethod
    def flip_edge(
        cls,
        tin_vertices: list[list[float]],
        tin_triangles: list[list[int]],
        edge_v0: int,
        edge_v1: int
    ) -> dict[str, Any]:
        """Inverte a diagonal (edge_v0, edge_v1) substituindo-a pelos outros 2 vertices opostos."""
        v0 = min(edge_v0, edge_v1)
        v1 = max(edge_v0, edge_v1)

        # Encontra os dois triangulos adjacentes
        adj_tris = []
        for idx, tri in enumerate(tin_triangles):
            if v0 in tri and v1 in tri:
                adj_tris.append((idx, tri))

        if len(adj_tris) != 2:
            return {
                "success": False,
                "message": f"Aresta ({v0}, {v1}) nao e compartilhada exatamente por 2 triangulos (encontrados: {len(adj_tris)})."
            }

        idx_a, tri_a = adj_tris[0]
        idx_b, tri_b = adj_tris[1]

        v_opp_a = [v for v in tri_a if v != v0 and v != v1][0]
        v_opp_b = [v for v in tri_b if v != v0 and v != v1][0]

        # Novas faces substituindo a diagonal antiga
        new_tri_1 = [v_opp_a, v_opp_b, v0]
        new_tri_2 = [v_opp_a, v1, v_opp_b]

        new_triangles = []
        for idx, tri in enumerate(tin_triangles):
            if idx == idx_a:
                new_triangles.append(new_tri_1)
            elif idx == idx_b:
                new_triangles.append(new_tri_2)
            else:
                new_triangles.append(tri)

        return {
            "success": True,
            "old_edge": [v0, v1],
            "new_edge": [min(v_opp_a, v_opp_b), max(v_opp_a, v_opp_b)],
            "replaced_triangles_indices": [idx_a, idx_b],
            "total_vertices": len(tin_vertices),
            "total_triangles": len(new_triangles),
            "vertices": tin_vertices,
            "triangles": new_triangles,
        }
