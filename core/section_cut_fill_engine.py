"""Engine de Engenharia Reversa para Inversao de Plano de Corte e Preenchimento de Secao (Section Cut Fill).

Implementa a inversao da direcao de visao da secao (Flip Section Direction) e
a geracao analitica de poligonos de tampa (Section Fill Caps) nos solidos interceptados.
"""

from __future__ import annotations
import math
from typing import Any


class SectionCutFillEngine:
    """Calcula tampas poligonais de preenchimento (Section Fill) e inversao de planos de corte."""

    @staticmethod
    def flip_plane(plane_coeffs: list[float]) -> list[float]:
        """Inverte a normal e a constante do plano: [a, b, c, d] -> [-a, -b, -c, -d]."""
        if len(plane_coeffs) != 4:
            return [0.0, -1.0, 0.0, 0.0]
        return [-float(c) for c in plane_coeffs]

    @staticmethod
    def _intersect_edge_with_plane(
        p0: list[float],
        p1: list[float],
        plane: list[float]
    ) -> list[float] | None:
        """Calcula o ponto 3D de intersecao entre um segmento de reta e um plano ax+by+cz+d=0."""
        a, b, c, d = plane
        d0 = a * p0[0] + b * p0[1] + c * p0[2] + d
        d1 = a * p1[0] + b * p1[1] + c * p1[2] + d
        if abs(d1 - d0) < 1e-12:
            return None
        t = -d0 / (d1 - d0)
        if 0.0 <= t <= 1.0:
            return [
                p0[0] + t * (p1[0] - p0[0]),
                p0[1] + t * (p1[1] - p0[1]),
                p0[2] + t * (p1[2] - p0[2])
            ]
        return None

    @classmethod
    def compute_section_fill(
        cls,
        solid_vertices: list[list[float]],
        solid_triangles: list[list[int]],
        plane_coeffs: list[float],
        flip_direction: bool = False,
        fill_color_hex: str = "#333333"
    ) -> dict[str, Any]:
        """Calcula a geometria da tampa de preenchimento da secao no plano."""
        active_plane = cls.flip_plane(plane_coeffs) if flip_direction else [float(c) for c in plane_coeffs]
        norm = math.sqrt(active_plane[0] ** 2 + active_plane[1] ** 2 + active_plane[2] ** 2)
        if norm > 1e-12:
            active_plane = [c / norm for c in active_plane]

        segments = []
        for tri in solid_triangles:
            v0 = solid_vertices[tri[0]]
            v1 = solid_vertices[tri[1]]
            v2 = solid_vertices[tri[2]]

            pts_on_plane = []
            for edge_start, edge_end in [(v0, v1), (v1, v2), (v2, v0)]:
                inter = cls._intersect_edge_with_plane(edge_start, edge_end, active_plane)
                if inter:
                    pts_on_plane.append(inter)

            if len(pts_on_plane) == 2:
                # Segmento de corte valido
                pA, pB = pts_on_plane[0], pts_on_plane[1]
                dist = math.sqrt((pB[0] - pA[0]) ** 2 + (pB[1] - pA[1]) ** 2 + (pB[2] - pA[2]) ** 2)
                if dist > 1e-5:
                    segments.append((pA, pB))

        # Encadeia os segmentos para obter contornos e ponto central
        fill_vertices = []
        fill_triangles = []
        if segments:
            all_pts = []
            for s1, s2 in segments:
                all_pts.extend([s1, s2])

            cx = sum(p[0] for p in all_pts) / len(all_pts)
            cy = sum(p[1] for p in all_pts) / len(all_pts)
            cz = sum(p[2] for p in all_pts) / len(all_pts)
            center = [round(cx, 4), round(cy, 4), round(cz, 4)]
            fill_vertices.append(center)

            for s1, s2 in segments:
                idx1 = len(fill_vertices)
                fill_vertices.append([round(s1[0], 4), round(s1[1], 4), round(s1[2], 4)])
                idx2 = len(fill_vertices)
                fill_vertices.append([round(s2[0], 4), round(s2[1], 4), round(s2[2], 4)])
                fill_triangles.append([0, idx1, idx2])

        return {
            "success": True,
            "active_plane": [round(c, 4) for c in active_plane],
            "flip_direction": flip_direction,
            "fill_color_hex": fill_color_hex,
            "cut_segments_count": len(segments),
            "fill_geometry": {
                "vertices": fill_vertices,
                "triangles": fill_triangles,
            },
            "has_fill_cap": len(fill_triangles) > 0,
        }
