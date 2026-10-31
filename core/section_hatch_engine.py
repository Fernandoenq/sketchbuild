"""
SketchBuild - Motor de Hachuras Gráficas para Cortes de Seção (Zero DLL / Pure Python)
Frente 79: Engenharia Reversa do SketchUp - Section Fill Hatching (NBR 6492 & ISO 128)

Gera hachuras analíticas padronizadas (Madeira, Concreto, Aço, Sólido) sobre os loops
fechados de corte transversal de planos de seção (SUSectionPlaneRef).
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


def _cross(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )


class SectionHatchPatternEngine:
    """Motor de cálculo e geração de hachuras gráficas para cortes de seção técnica."""

    @classmethod
    def generate_hatch_lines(
        cls,
        closed_loop_3d: List[Tuple[float, float, float]],
        pattern: str = "WOOD",  # WOOD, CONCRETE, STEEL, SOLID
        spacing_m: float = 0.05,
        angle_deg: float = 45.0,
    ) -> Dict[str, Any]:
        """
        Gera segmentos 3D de hachura recortados no interior do loop poligonal fechado.
        """
        n_pts = len(closed_loop_3d)
        if n_pts < 3:
            return {"pattern": pattern, "hatch_lines_count": 0, "hatch_segments": []}

        # 1. Determinar o plano médio do loop
        p0 = closed_loop_3d[0]
        p1 = closed_loop_3d[1]
        p2 = closed_loop_3d[2]
        v1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v2 = (p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2])
        normal = _norm(_cross(v1, v2))

        # Base ortonormal local (u, v)
        if abs(normal[2]) < 0.9:
            u_axis = _norm(_cross(normal, (0.0, 0.0, 1.0)))
        else:
            u_axis = _norm(_cross(normal, (1.0, 0.0, 0.0)))
        v_axis = _norm(_cross(normal, u_axis))

        # 2. Projetar vértices 3D em 2D local (u, v)
        loop_2d: List[Tuple[float, float]] = []
        for pt in closed_loop_3d:
            rel = (pt[0] - p0[0], pt[1] - p0[1], pt[2] - p0[2])
            u = _dot(rel, u_axis)
            v = _dot(rel, v_axis)
            loop_2d.append((u, v))

        # Bounding box 2D
        min_u = min(p[0] for p in loop_2d)
        max_u = max(p[0] for p in loop_2d)
        min_v = min(p[1] for p in loop_2d)
        max_v = max(p[1] for p in loop_2d)

        spacing = max(0.005, spacing_m)
        rad = math.radians(angle_deg)
        cos_ang = math.cos(rad)
        sin_ang = math.sin(rad)

        # Direção normal da linha de hachura (nx, ny)
        h_norm = (-sin_ang, cos_ang)
        # Direção ao longo da linha de hachura (dx, dy)
        h_dir = (cos_ang, sin_ang)

        # Projetar bbox na normal das linhas de hachura para saber a faixa de deslocamentos D
        d_vals = [p[0] * h_norm[0] + p[1] * h_norm[1] for p in loop_2d]
        min_d = min(d_vals)
        max_d = max(d_vals)

        hatch_segments_2d: List[Tuple[Tuple[float, float], Tuple[float, float]]] = []

        cur_d = min_d + spacing * 0.5
        while cur_d <= max_d:
            # Encontrar interseções da reta p . h_norm = cur_d com as arestas do polígono
            intersections: List[float] = []

            for i in range(len(loop_2d)):
                p_a = loop_2d[i]
                p_b = loop_2d[(i + 1) % len(loop_2d)]

                da = p_a[0] * h_norm[0] + p_a[1] * h_norm[1] - cur_d
                db = p_b[0] * h_norm[0] + p_b[1] * h_norm[1] - cur_d

                if (da * db) < 0.0:  # Aresta cruza a reta
                    t = -da / (db - da)
                    inter_u = p_a[0] + t * (p_b[0] - p_a[0])
                    inter_v = p_a[1] + t * (p_b[1] - p_a[1])
                    # Projeção ao longo de h_dir
                    s = inter_u * h_dir[0] + inter_v * h_dir[1]
                    intersections.append(s)

            intersections.sort()
            # Agrupar pares de dentro para fora (even-odd rule)
            for k in range(0, len(intersections) - 1, 2):
                s1 = intersections[k]
                s2 = intersections[k + 1]
                # Ponto de referência na reta: cur_d * h_norm
                ref_u = cur_d * h_norm[0]
                ref_v = cur_d * h_norm[1]

                pt1 = (ref_u + s1 * h_dir[0], ref_v + s1 * h_dir[1])
                pt2 = (ref_u + s2 * h_dir[0], ref_v + s2 * h_dir[1])
                hatch_segments_2d.append((pt1, pt2))

            cur_d += spacing

        # 3. Converter segmentos 2D de volta para 3D
        hatch_segments_3d: List[List[List[float]]] = []
        for seg in hatch_segments_2d:
            p1_3d = [
                round(p0[0] + seg[0][0] * u_axis[0] + seg[0][1] * v_axis[0], 4),
                round(p0[1] + seg[0][0] * u_axis[1] + seg[0][1] * v_axis[1], 4),
                round(p0[2] + seg[0][0] * u_axis[2] + seg[0][1] * v_axis[2], 4),
            ]
            p2_3d = [
                round(p0[0] + seg[1][0] * u_axis[0] + seg[1][1] * v_axis[0], 4),
                round(p0[1] + seg[1][0] * u_axis[1] + seg[1][1] * v_axis[1], 4),
                round(p0[2] + seg[1][0] * u_axis[2] + seg[1][1] * v_axis[2], 4),
            ]
            hatch_segments_3d.append([p1_3d, p2_3d])

        return {
            "entity_type": "SectionHatchResult",
            "pattern": pattern.upper(),
            "spacing_m": round(spacing, 4),
            "angle_deg": round(angle_deg, 1),
            "hatch_lines_count": len(hatch_segments_3d),
            "hatch_segments": hatch_segments_3d,
            "status": f"{len(hatch_segments_3d)} LINHAS DE HACHURA ({pattern.upper()}) GERADAS",
        }
