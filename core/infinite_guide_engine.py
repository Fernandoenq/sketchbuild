"""
SketchBuild - Motor de Linhas e Pontos de Construção Infinitos (Zero DLL / Pure Python)
Frente 73: Engenharia Reversa do SketchUp - SUGuideLineRef & SUGuidePointRef

Gerencia guias auxiliares tracejadas infinitas (Tape Measure Tool), pontos de construção
e cálculo analítico de interseção entre guias para snap de inferência.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _dot(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
    return sum(v1[i] * v2[i] for i in range(3))


def _norm(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    length = math.sqrt(_dot(v, v))
    if length < 1e-9:
        return (0.0, 0.0, 1.0)
    return (v[0] / length, v[1] / length, v[2] / length)


class InfiniteGuideEngine:
    """Motor de cálculo e projeção de linhas de guia e pontos auxiliares de construção."""

    DEFAULT_EXTENT = 500.0  # Alcance métrico padrão para simular linha infinita

    @classmethod
    def create_guide_line(
        cls,
        point: Tuple[float, float, float],
        direction: Optional[Tuple[float, float, float]] = None,
        end_point: Optional[Tuple[float, float, float]] = None,
        is_infinite: bool = True,
        extent_m: float = DEFAULT_EXTENT,
    ) -> Dict[str, Any]:
        """
        Cria uma linha de guia finita ou infinita no padrão SUGuideLineRef.
        """
        p0 = (float(point[0]), float(point[1]), float(point[2]))

        if not is_infinite and end_point is not None:
            p1 = (float(end_point[0]), float(end_point[1]), float(end_point[2]))
            disp = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
            dir_u = _norm(disp)
            render_start = p0
            render_end = p1
            length = math.sqrt(_dot(disp, disp))
        else:
            if direction is not None:
                dir_u = _norm(direction)
            elif end_point is not None:
                disp = (end_point[0] - p0[0], end_point[1] - p0[1], end_point[2] - p0[2])
                dir_u = _norm(disp)
            else:
                dir_u = (1.0, 0.0, 0.0)

            render_start = (
                p0[0] - dir_u[0] * extent_m,
                p0[1] - dir_u[1] * extent_m,
                p0[2] - dir_u[2] * extent_m,
            )
            render_end = (
                p0[0] + dir_u[0] * extent_m,
                p0[1] + dir_u[1] * extent_m,
                p0[2] + dir_u[2] * extent_m,
            )
            length = extent_m * 2.0

        return {
            "type": "SUGuideLineRef",
            "is_infinite": is_infinite,
            "origin_point": [round(c, 4) for c in p0],
            "direction": [round(c, 4) for c in dir_u],
            "display_segment": [
                [round(c, 4) for c in render_start],
                [round(c, 4) for c in render_end],
            ],
            "length_m": round(length, 4),
            "three_style": {
                "dashed": True,
                "dash_size": 0.08,
                "gap_size": 0.05,
                "color": "#2c3e50",
            },
            "status": "GUIA INFINITA CRIADA" if is_infinite else "GUIA FINITA CRIADA",
        }

    @classmethod
    def create_guide_point(
        cls,
        point: Tuple[float, float, float],
    ) -> Dict[str, Any]:
        """Cria um ponto de construção SUGuidePointRef com geometria de cruz de visualização."""
        p = (float(point[0]), float(point[1]), float(point[2]))
        size = 0.05  # Tamanho da cruz

        cross_lines = [
            [[p[0] - size, p[1], p[2]], [p[0] + size, p[1], p[2]]],
            [[p[0], p[1] - size, p[2]], [p[0], p[1] + size, p[2]]],
            [[p[0], p[1], p[2] - size], [p[0], p[1], p[2] + size]],
        ]

        return {
            "type": "SUGuidePointRef",
            "point": [round(c, 4) for c in p],
            "marker_cross_lines": cross_lines,
            "status": "PONTO DE CONSTRUÇÃO CRIADO",
        }

    @classmethod
    def intersect_guide_lines(
        cls,
        line1: Dict[str, Any],
        line2: Dict[str, Any],
        tolerance: float = 1e-3,
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula o ponto 3D de interseção analítica entre duas linhas de guia.
        Retorna as coordenadas do ponto de interseção se forem concorrentes ou None se reversas/paralelas.
        """
        p1 = tuple(line1["origin_point"])
        d1 = tuple(line1["direction"])
        p2 = tuple(line2["origin_point"])
        d2 = tuple(line2["direction"])

        # Resolver o sistema dos mínimos quadrados para retas p1 + s*d1 e p2 + t*d2
        # d1 . (p1 + s*d1 - p2 - t*d2) = 0
        # d2 . (p1 + s*d1 - p2 - t*d2) = 0
        w0 = (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])
        a = _dot(d1, d1)
        b = _dot(d1, d2)
        c = _dot(d2, d2)
        d = _dot(d1, w0)
        e = _dot(d2, w0)

        denom = a * c - b * b
        if abs(denom) < 1e-8:
            return None  # Paralelas

        s = (b * e - c * d) / denom
        t = (a * e - b * d) / denom

        closest_pt1 = (p1[0] + s * d1[0], p1[1] + s * d1[1], p1[2] + s * d1[2])
        closest_pt2 = (p2[0] + t * d2[0], p2[1] + t * d2[1], p2[2] + t * d2[2])

        dist_between = math.sqrt(sum((closest_pt1[i] - closest_pt2[i]) ** 2 for i in range(3)))
        if dist_between > tolerance:
            return None  # Reversas (não se cruzam dentro da tolerância)

        intersection = (
            (closest_pt1[0] + closest_pt2[0]) * 0.5,
            (closest_pt1[1] + closest_pt2[1]) * 0.5,
            (closest_pt1[2] + closest_pt2[2]) * 0.5,
        )

        return {
            "intersection_point": [round(c, 4) for c in intersection],
            "distance_between_rays": round(dist_between, 6),
            "status": "INTERSEÇÃO DE GUIAS ENCONTRADA",
        }
