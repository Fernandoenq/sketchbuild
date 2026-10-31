"""Engine de Engenharia Reversa da Ferramenta Projetar (Drape Tool) da Caixa de Areia (Sandbox).

Molda e projeta linhas, curvas e contornos 2D verticalmente sobre a malha 3D
irregular de um terreno (TIN), interpolando cotas baricentricas em cada triangulo.
"""

from __future__ import annotations
import math
from typing import Any


class DrapeContourEngine:
    """Projeta caminhos 2D sobre malhas de terreno 3D (Drape)."""

    @staticmethod
    def _barycentric_elevation(
        px: float,
        py: float,
        v0: list[float],
        v1: list[float],
        v2: list[float]
    ) -> float | None:
        """Calcula a cota Z em (px, py) projetada no triangulo (v0, v1, v2) via coordenadas baricentricas."""
        x0, y0, z0 = v0[0], v0[1], v0[2]
        x1, y1, z1 = v1[0], v1[1], v1[2]
        x2, y2, z2 = v2[0], v2[1], v2[2]

        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(det) < 1e-12:
            return None

        w0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / det
        w1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / det
        w2 = 1.0 - w0 - w1

        # Tolerancia pequena para pontos na borda
        eps = -1e-5
        if w0 >= eps and w1 >= eps and w2 >= eps:
            return w0 * z0 + w1 * z1 + w2 * z2
        return None

    @classmethod
    def drape_path(
        cls,
        tin_vertices: list[list[float]],
        tin_triangles: list[list[int]],
        path_points_2d: list[list[float]],
        subdivision_steps: int = 4
    ) -> dict[str, Any]:
        """Projeta a polilinha 2D sobre os triangulos da TIN."""
        if len(path_points_2d) < 2 or not tin_vertices or not tin_triangles:
            return {
                "success": False,
                "draped_points_3d": [],
                "length_2d_m": 0.0,
                "length_3d_m": 0.0,
                "slope_pct": 0.0,
            }

        # Subdivide os segmentos 2D para acompanhar fielmente o relevo
        dense_2d_points = []
        for i in range(len(path_points_2d) - 1):
            p_curr = path_points_2d[i]
            p_next = path_points_2d[i + 1]
            dense_2d_points.append(p_curr)
            for step in range(1, subdivision_steps):
                t = step / subdivision_steps
                dense_2d_points.append([
                    p_curr[0] + t * (p_next[0] - p_curr[0]),
                    p_curr[1] + t * (p_next[1] - p_curr[1])
                ])
        dense_2d_points.append(path_points_2d[-1])

        draped_3d = []
        default_z = float(tin_vertices[0][2])

        for pt in dense_2d_points:
            px, py = float(pt[0]), float(pt[1])
            found_z = None
            for tri in tin_triangles:
                v0 = tin_vertices[tri[0]]
                v1 = tin_vertices[tri[1]]
                v2 = tin_vertices[tri[2]]
                elev = cls._barycentric_elevation(px, py, v0, v1, v2)
                if elev is not None:
                    found_z = elev
                    break

            z_final = found_z if found_z is not None else default_z
            draped_3d.append([round(px, 4), round(py, 4), round(z_final, 4)])

        # Calcula comprimentos e declividade media
        len_2d = 0.0
        len_3d = 0.0
        for i in range(len(draped_3d) - 1):
            p0, p1 = draped_3d[i], draped_3d[i + 1]
            d2 = math.sqrt((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2)
            d3 = math.sqrt((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2 + (p1[2] - p0[2]) ** 2)
            len_2d += d2
            len_3d += d3

        slope = ((len_3d - len_2d) / (len_2d + 1e-12)) * 100.0

        return {
            "success": True,
            "draped_points_3d": draped_3d,
            "total_points": len(draped_3d),
            "length_2d_m": round(len_2d, 3),
            "length_3d_m": round(len_3d, 3),
            "elongation_pct": round(slope, 2),
            "average_elevation_m": round(sum(p[2] for p in draped_3d) / max(1, len(draped_3d)), 3)
        }
