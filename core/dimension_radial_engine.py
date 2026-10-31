"""
SketchBuild - Motor de Cotas Radiais e Diamétricas (Zero DLL / Pure Python)
Frente 76: Engenharia Reversa do SketchUp - SUDimensionRadialRef

Calcula cotas radiais (R) e diamétricas (Ø) em arcos e circunferências,
com linhas de líder, tiques/setas de contato na borda e formatação métrica/imperial.
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


class DimensionRadialEngine:
    """Motor de cotas de raio (R) e diâmetro (Ø) em arcos e círculos do SketchUp."""

    @classmethod
    def create_radial_dimension(
        cls,
        center: Tuple[float, float, float],
        radius: float,
        normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        angle_deg: float = 45.0,
        is_diameter: bool = False,
        leader_length: float = 0.3,
        unit: str = "m",
        precision: int = 2,
    ) -> Dict[str, Any]:
        """
        Calcula a geometria 3D de uma cota radial ou diamétrica.
        """
        if radius <= 1e-6:
            raise ValueError("O raio da cota deve ser maior que zero.")

        n = _norm(normal)
        # Construir base ortonormal no plano do círculo
        if abs(n[2]) < 0.9:
            u_axis = _norm(_cross(n, (0.0, 0.0, 1.0)))
        else:
            u_axis = _norm(_cross(n, (1.0, 0.0, 0.0)))
        v_axis = _norm(_cross(n, u_axis))

        ang_rad = math.radians(angle_deg)
        cos_a = math.cos(ang_rad)
        sin_a = math.sin(ang_rad)

        # Vetor radial na direção do ponto de contato
        rad_dir = (
            cos_a * u_axis[0] + sin_a * v_axis[0],
            cos_a * u_axis[1] + sin_a * v_axis[1],
            cos_a * u_axis[2] + sin_a * v_axis[2],
        )

        # Ponto de contato na borda do arco
        rim_point = (
            center[0] + radius * rad_dir[0],
            center[1] + radius * rad_dir[1],
            center[2] + radius * rad_dir[2],
        )

        # Ponto de quebra do líder (elbow) e pouso do texto (landing)
        elbow_point = (
            rim_point[0] + leader_length * rad_dir[0],
            rim_point[1] + leader_length * rad_dir[1],
            rim_point[2] + leader_length * rad_dir[2],
        )

        landing_len = 0.15
        # Prolongamento horizontal no eixo U
        landing_dir = (1.0, 0.0, 0.0) if rad_dir[0] >= 0 else (-1.0, 0.0, 0.0)
        text_pos = (
            elbow_point[0] + landing_len * landing_dir[0],
            elbow_point[1] + landing_len * landing_dir[1],
            elbow_point[2] + landing_len * landing_dir[2],
        )

        # Linhas de desenho
        segments: List[List[List[float]]] = []
        if is_diameter:
            # Passa pelo centro até a borda oposta
            opp_rim_point = (
                center[0] - radius * rad_dir[0],
                center[1] - radius * rad_dir[1],
                center[2] - radius * rad_dir[2],
            )
            segments.append([
                [round(c, 4) for c in opp_rim_point],
                [round(c, 4) for c in rim_point],
            ])
        else:
            # Da origem até a borda ou da borda até o cotovelo
            segments.append([
                [round(c, 4) for c in center],
                [round(c, 4) for c in rim_point],
            ])

        # Segmento do líder
        segments.append([
            [round(c, 4) for c in rim_point],
            [round(c, 4) for c in elbow_point],
        ])
        segments.append([
            [round(c, 4) for c in elbow_point],
            [round(c, 4) for c in text_pos],
        ])

        # Formatação do texto
        measured_val = (radius * 2.0) if is_diameter else radius
        prefix = "Ø " if is_diameter else "R "
        if unit == "mm":
            val_str = f"{measured_val * 1000.0:.{precision}f} mm"
        elif unit == "cm":
            val_str = f"{measured_val * 100.0:.{precision}f} cm"
        elif unit == "in":
            val_str = f'{measured_val * 39.3701:.{precision}f}"'
        else:
            val_str = f"{measured_val:.{precision}f} m"

        display_text = f"{prefix}{val_str}"

        # Seta na borda
        arrow_size = 0.04
        arrow_tick = (
            rim_point[0] - arrow_size * rad_dir[0],
            rim_point[1] - arrow_size * rad_dir[1],
            rim_point[2] - arrow_size * rad_dir[2],
        )

        return {
            "type": "SUDimensionRadialRef",
            "is_diameter": is_diameter,
            "radius_m": round(radius, 4),
            "diameter_m": round(radius * 2.0, 4),
            "text": display_text,
            "unit": unit,
            "center": [round(c, 4) for c in center],
            "rim_point": [round(c, 4) for c in rim_point],
            "text_position": [round(c, 4) for c in text_pos],
            "line_segments": segments,
            "arrow_tip": [round(c, 4) for c in rim_point],
            "status": f"COTA {'DIAMÉTRICA' if is_diameter else 'RADIAL'} CALCULADA ({display_text})",
        }
