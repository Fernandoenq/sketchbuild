"""
SketchBuild - Motor de Cotas Radiais, Diamétricas e de Arcos (Zero DLL / Pure Python)
Ferramentas Nativas Oficiais do SketchUp: Radial & Arc Dimension (SUDimensionRadialRef & SUArcCurveRef)

Implementa:
1. Cotagem de Raio (R) com linha líder a partir do centro ou borda.
2. Cotagem de Diâmetro (Ø) cruzando o círculo.
3. Cotagem de Comprimento de Arco (Arc Length) calculando arco real: s = r * theta.
4. Identificação analítica de arcos e posicionamento na bissetriz angular.
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


class RadialArcDimensionEngine:
    """Motor de cálculo de cotas de raio, diâmetro e comprimento de arcos no SketchUp."""

    @classmethod
    def create_radial_dimension(
        cls,
        center: Tuple[float, float, float],
        radius: float,
        angle_deg: float = 45.0,
        is_diameter: bool = False,
        normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        leader_extension: float = 0.25,
        unit: str = "m",
        precision: int = 2,
    ) -> Dict[str, Any]:
        """
        Gera cota radial (R) ou diamétrica (Ø) analítica.
        """
        if radius <= 1e-6:
            raise ValueError("O raio deve ser maior que zero.")

        n = _norm(normal)
        rad = math.radians(angle_deg)

        if abs(n[2]) < 0.9:
            u_axis = _norm(_cross(n, (0.0, 0.0, 1.0)))
        else:
            u_axis = _norm(_cross(n, (1.0, 0.0, 0.0)))
        v_axis = _norm(_cross(n, u_axis))

        # Vetor unitário na direção do ângulo escolhido
        dir_vec = (
            u_axis[0] * math.cos(rad) + v_axis[0] * math.sin(rad),
            u_axis[1] * math.cos(rad) + v_axis[1] * math.sin(rad),
            u_axis[2] * math.cos(rad) + v_axis[2] * math.sin(rad),
        )

        rim_pt = (
            center[0] + dir_vec[0] * radius,
            center[1] + dir_vec[1] * radius,
            center[2] + dir_vec[2] * radius,
        )

        leader_end = (
            rim_pt[0] + dir_vec[0] * leader_extension,
            rim_pt[1] + dir_vec[1] * leader_extension,
            rim_pt[2] + dir_vec[2] * leader_extension,
        )

        if is_diameter:
            measured_val = radius * 2.0
            prefix = "Ø "
            dim_type = "DIAMETER"
            opposite_pt = (
                center[0] - dir_vec[0] * radius,
                center[1] - dir_vec[1] * radius,
                center[2] - dir_vec[2] * radius,
            )
            line_segments = [[list(opposite_pt), list(rim_pt)], [list(rim_pt), list(leader_end)]]
        else:
            measured_val = radius
            prefix = "R "
            dim_type = "RADIUS"
            line_segments = [[list(center), list(rim_pt)], [list(rim_pt), list(leader_end)]]

        formatted_text = f"{prefix}{measured_val:.{precision}f} {unit}"

        return {
            "entity_type": "SUDimensionRadialRef",
            "dimension_type": dim_type,
            "measured_value_m": round(measured_val, 4),
            "formatted_text": formatted_text,
            "center_point": list(center),
            "rim_point": [round(c, 4) for c in rim_pt],
            "text_position": [round(c, 4) for c in leader_end],
            "line_segments": line_segments,
            "arrow_type": "ARROW",
            "status": f"COTA {dim_type} CRIADA COM SUCESSO",
        }

    @classmethod
    def create_arc_length_dimension(
        cls,
        center: Tuple[float, float, float],
        radius: float,
        start_angle_deg: float,
        end_angle_deg: float,
        offset_m: float = 0.2,
        normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        unit: str = "m",
        precision: int = 2,
    ) -> Dict[str, Any]:
        """
        Calcula a cota de comprimento de arco: s = radius * sweep_angle.
        """
        sweep_deg = abs(end_angle_deg - start_angle_deg)
        sweep_rad = math.radians(sweep_deg)
        arc_length = radius * sweep_rad
        mid_angle = math.radians(0.5 * (start_angle_deg + end_angle_deg))

        n = _norm(normal)
        if abs(n[2]) < 0.9:
            u_axis = _norm(_cross(n, (0.0, 0.0, 1.0)))
        else:
            u_axis = _norm(_cross(n, (1.0, 0.0, 0.0)))
        v_axis = _norm(_cross(n, u_axis))

        text_pos = (
            center[0] + (radius + offset_m) * (u_axis[0] * math.cos(mid_angle) + v_axis[0] * math.sin(mid_angle)),
            center[1] + (radius + offset_m) * (u_axis[1] * math.cos(mid_angle) + v_axis[1] * math.sin(mid_angle)),
            center[2] + (radius + offset_m) * (u_axis[2] * math.cos(mid_angle) + v_axis[2] * math.sin(mid_angle)),
        )

        formatted_text = f"Arc: {arc_length:.{precision}f} {unit}"

        return {
            "entity_type": "SUArcCurveRef",
            "dimension_type": "ARC_LENGTH",
            "arc_length_m": round(arc_length, 4),
            "radius_m": round(radius, 4),
            "sweep_angle_deg": round(sweep_deg, 2),
            "formatted_text": formatted_text,
            "text_position": [round(c, 4) for c in text_pos],
            "center": list(center),
            "status": "COTA DE COMPRIMENTO DE ARCO CRIADA COM SUCESSO",
        }
