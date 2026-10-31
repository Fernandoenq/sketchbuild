"""Engine de Engenharia Reversa da Ferramenta Carimbo (Stamp Tool) da Caixa de Areia (Sandbox).

Reproduz a criacao de plato nivelado e saia/talude de transicao sobre
malhas triangulares (TIN) de terreno, conforme o comportamento da ferramenta
oficial do SketchUp Pro.
"""

from __future__ import annotations
import math
from typing import Any


class StampTerrainEngine:
    """Implementa o algoritmo de carimbo (Stamp) sobre malhas de terreno TIN."""

    @staticmethod
    def point_in_polygon_2d(px: float, py: float, poly: list[list[float]]) -> bool:
        """Verifica se (px, py) esta estritamente contido no poligono 2D via ray casting."""
        inside = False
        n = len(poly)
        if n < 3:
            return False
        j = n - 1
        for i in range(n):
            xi, yi = poly[i][0], poly[i][1]
            xj, yj = poly[j][0], poly[j][1]
            if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi):
                inside = not inside
            j = i
        return inside

    @staticmethod
    def min_distance_to_polygon_2d(px: float, py: float, poly: list[list[float]]) -> float:
        """Calcula a distancia euclidiana 2D minima de um ponto ao perimetro do poligono."""
        min_dist_sq = float("inf")
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i][0], poly[i][1]
            x2, y2 = poly[(i + 1) % n][0], poly[(i + 1) % n][1]
            dx, dy = x2 - x1, y2 - y1
            l2 = dx * dx + dy * dy
            if l2 < 1e-12:
                d_sq = (px - x1) ** 2 + (py - y1) ** 2
            else:
                t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
                proj_x = x1 + t * dx
                proj_y = y1 + t * dy
                d_sq = (px - proj_x) ** 2 + (py - proj_y) ** 2
            if d_sq < min_dist_sq:
                min_dist_sq = d_sq
        return math.sqrt(min_dist_sq)

    @classmethod
    def apply_stamp(
        cls,
        tin_vertices: list[list[float]],
        tin_triangles: list[list[int]],
        footprint_polygon: list[list[float]],
        target_elevation: float,
        transition_width: float = 1.5,
    ) -> dict[str, Any]:
        """Aplica o carimbo do poligono na malha TIN com talude perimetral suave."""
        if not tin_vertices or len(footprint_polygon) < 3:
            return {
                "success": False,
                "modified_vertices": tin_vertices,
                "triangles": tin_triangles,
                "vertices_plateau_count": 0,
                "vertices_slope_count": 0,
                "cut_volume_m3": 0.0,
                "fill_volume_m3": 0.0,
            }

        transition_width = max(0.01, float(transition_width))
        modified = []
        plateau_count = 0
        slope_count = 0
        net_elevation_delta = 0.0
        cut_vol = 0.0
        fill_vol = 0.0

        for v in tin_vertices:
            x, y, z_orig = float(v[0]), float(v[1]), float(v[2])
            is_inside = cls.point_in_polygon_2d(x, y, footprint_polygon)

            if is_inside:
                z_new = float(target_elevation)
                plateau_count += 1
            else:
                dist = cls.min_distance_to_polygon_2d(x, y, footprint_polygon)
                if dist <= transition_width:
                    # Fator de amortecimento Hermite / Smoothstep: 3t^2 - 2t^3
                    t = dist / transition_width
                    factor = t * t * (3.0 - 2.0 * t)
                    z_new = (1.0 - factor) * float(target_elevation) + factor * z_orig
                    slope_count += 1
                else:
                    z_new = z_orig

            diff = z_new - z_orig
            net_elevation_delta += diff
            if diff < 0:
                cut_vol += abs(diff) * 1.0  # estimativa por celula normalizada
            elif diff > 0:
                fill_vol += diff * 1.0

            modified.append([round(x, 4), round(y, 4), round(z_new, 4)])

        return {
            "success": True,
            "modified_vertices": modified,
            "triangles": tin_triangles,
            "total_vertices": len(modified),
            "vertices_plateau_count": plateau_count,
            "vertices_slope_count": slope_count,
            "target_elevation": float(target_elevation),
            "transition_width": transition_width,
            "estimated_cut_m3": round(cut_vol * 0.25, 3),
            "estimated_fill_m3": round(fill_vol * 0.25, 3),
        }
