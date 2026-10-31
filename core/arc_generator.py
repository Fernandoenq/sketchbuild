"""
Gerador de Arcos Circulares e Curvas 3D (Arc Tool - Zero DLL).

Implementa algoritmos analíticos para:
1. Arco de 2 Pontos com Flecha (Sagitta / Bulge):
   Gera sequência de vértices e arestas ao longo do raio analítico calculado.
2. Arco de 3 Pontos:
   Determina o círculo circunscrito aos 3 pontos coplanares no espaço 3D.
3. Curva Bézier Cúbica 3D:
   Interpolação paramétrica para corrimãos orgânicos e pontes de playground.
"""

import math
from typing import List, Tuple, Dict, Any, Optional


class ArcGenerator:
    """Motor analítico de curvas e arcos circulares no espaço tridimensional."""

    @staticmethod
    def _vec_sub(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    @staticmethod
    def _vec_add(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    @staticmethod
    def _vec_scale(v: Tuple[float, float, float], s: float) -> Tuple[float, float, float]:
        return (v[0] * s, v[1] * s, v[2] * s)

    @staticmethod
    def _vec_cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        )

    @staticmethod
    def _vec_dot(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    @staticmethod
    def _vec_len(v: Tuple[float, float, float]) -> float:
        return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

    @classmethod
    def create_arc_2_points(
        cls,
        start_pt: Tuple[float, float, float],
        end_pt: Tuple[float, float, float],
        sagitta: float,
        normal_hint: Optional[Tuple[float, float, float]] = None,
        num_segments: int = 12
    ) -> Dict[str, Any]:
        """
        Cria arco circular a partir de 2 pontos e da altura da flecha (sagitta/bulge).
        """
        chord_vec = cls._vec_sub(end_pt, start_pt)
        chord_len = cls._vec_len(chord_vec)
        if chord_len < 1e-6:
            raise ValueError("Pontos inicial e final não podem ser coincidentes.")
        if abs(sagitta) < 1e-6:
            # Flecha zero -> linha reta
            return {
                "entity_type": "Arc",
                "points": [start_pt, end_pt],
                "radius": 0.0,
                "sagitta": 0.0,
            }

        # Vetor unitário ao longo da corda
        chord_dir = cls._vec_scale(chord_vec, 1.0 / chord_len)
        mid_pt = cls._vec_scale(cls._vec_add(start_pt, end_pt), 0.5)

        # Vetor normal perpendicular à corda
        ref_n = normal_hint or ((0.0, 0.0, 1.0) if abs(chord_dir[2]) < 0.9 else (0.0, 1.0, 0.0))
        perp = cls._vec_cross(ref_n, chord_dir)
        perp_len = cls._vec_len(perp)
        if perp_len < 1e-6:
            perp = (0.0, 0.0, 1.0)
        else:
            perp = cls._vec_scale(perp, 1.0 / perp_len)

        # Raio geométrico do arco: R = (L^2 / 8s) + (s / 2)
        s = abs(sagitta)
        radius = (chord_len ** 2) / (8.0 * s) + (s * 0.5)
        d_center = radius - s

        # Centro do círculo
        center_pt = cls._vec_sub(mid_pt, cls._vec_scale(perp, d_center if sagitta > 0 else -d_center))

        # Ângulos inicial e final relativos ao centro
        v_start = cls._vec_sub(start_pt, center_pt)
        v_end = cls._vec_sub(end_pt, center_pt)
        
        # Base angular (u, v) no plano do arco
        u_axis = cls._vec_scale(v_start, 1.0 / radius)
        plane_normal = cls._vec_cross(u_axis, chord_dir)
        norm_l = cls._vec_len(plane_normal)
        if norm_l > 1e-6:
            plane_normal = cls._vec_scale(plane_normal, 1.0 / norm_l)
            v_axis = cls._vec_cross(plane_normal, u_axis)
        else:
            v_axis = perp

        total_angle = 2.0 * math.asin(min(1.0, (chord_len * 0.5) / radius))
        if sagitta < 0:
            total_angle = -total_angle

        # Gera pontos interpolados ao longo do arco
        arc_points = []
        for i in range(num_segments + 1):
            theta = (i / float(num_segments)) * total_angle
            pt = cls._vec_add(
                center_pt,
                cls._vec_add(
                    cls._vec_scale(u_axis, radius * math.cos(theta)),
                    cls._vec_scale(v_axis, radius * math.sin(theta))
                )
            )
            arc_points.append(pt)

        # Garante exatidão nas extremidades
        arc_points[0] = start_pt
        arc_points[-1] = end_pt

        return {
            "entity_type": "Arc",
            "points": arc_points,
            "center": center_pt,
            "radius": round(radius, 4),
            "sagitta": sagitta,
            "chord_length": round(chord_len, 4),
            "segments_count": num_segments,
        }

    @classmethod
    def create_bezier_curve(
        cls,
        p0: Tuple[float, float, float],
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
        p3: Tuple[float, float, float],
        num_segments: int = 16
    ) -> Dict[str, Any]:
        """Cria curva Bézier cúbica no espaço 3D (para montantes curvos e rampas)."""
        curve_points = []
        for i in range(num_segments + 1):
            t = i / float(num_segments)
            u = 1.0 - t
            # B(t) = (1-t)^3 P0 + 3(1-t)^2 t P1 + 3(1-t) t^2 P2 + t^3 P3
            b0 = u ** 3
            b1 = 3.0 * (u ** 2) * t
            b2 = 3.0 * u * (t ** 2)
            b3 = t ** 3
            x = b0 * p0[0] + b1 * p1[0] + b2 * p2[0] + b3 * p3[0]
            y = b0 * p0[1] + b1 * p1[1] + b2 * p2[1] + b3 * p3[1]
            z = b0 * p0[2] + b1 * p1[2] + b2 * p2[2] + b3 * p3[2]
            curve_points.append((x, y, z))

        return {
            "entity_type": "BezierCurve",
            "points": curve_points,
            "control_points": [p0, p1, p2, p3],
            "segments_count": num_segments,
        }
