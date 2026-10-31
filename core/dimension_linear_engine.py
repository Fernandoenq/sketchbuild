"""
SketchBuild - Motor de Cotas Lineares e Alinhadas (Zero DLL / Pure Python)
Frente 72: Engenharia Reversa do SketchUp - SUDimensionLinearRef

Calcula cotas lineares com linhas de extensão (witness lines), tiques arquitetônicos / setas,
afastamento analítico em plano de apoio e formatação de distâncias em unidades métricas ou imperiais.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _dist(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    return math.sqrt(sum((p1[i] - p2[i]) ** 2 for i in range(3)))


def _sub(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])


def _add(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (p1[0] + p2[0], p1[1] + p2[1], p1[2] + p2[2])


def _scale(v: Tuple[float, float, float], s: float) -> Tuple[float, float, float]:
    return (v[0] * s, v[1] * s, v[2] * s)


def _cross(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )


def _dot(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
    return sum(v1[i] * v2[i] for i in range(3))


def _norm(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    length = math.sqrt(_dot(v, v))
    if length < 1e-9:
        return (0.0, 0.0, 1.0)
    return (v[0] / length, v[1] / length, v[2] / length)


class DimensionLinearEngine:
    """Motor de cálculo e representação gráfica de cotas lineares SUDimensionLinearRef."""

    @classmethod
    def create_dimension(
        cls,
        start_pt: Tuple[float, float, float],
        end_pt: Tuple[float, float, float],
        offset_distance: float = 0.2,
        plane_normal: Optional[Tuple[float, float, float]] = None,
        arrow_type: str = "SLASH",  # SLASH (45° tick), ARROW, DOT
        unit: str = "m",            # m, cm, mm, in
        precision: int = 2,
        custom_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calcula a geometria 3D analítica da cota linear.
        """
        raw_dist = _dist(start_pt, end_pt)
        if raw_dist < 1e-6:
            raise ValueError("Os pontos de início e fim da cota não podem ser coincidentes.")

        dir_vec = _norm(_sub(end_pt, start_pt))

        # Determinar a direção de afastamento (perpendicular à linha de cota e contida no plano)
        if plane_normal is not None:
            n = _norm(plane_normal)
            offset_dir = _norm(_cross(dir_vec, n))
        else:
            # Selecionar perpendicular padrão com base nos eixos principais
            if abs(dir_vec[2]) > 0.9:  # Linha quase vertical Z
                offset_dir = (1.0, 0.0, 0.0)
            else:
                # Perpendicular no plano horizontal XY
                offset_dir = (-dir_vec[1], dir_vec[0], 0.0)
                if _dot(offset_dir, offset_dir) < 1e-4:
                    offset_dir = (0.0, 0.0, 1.0)
                else:
                    offset_dir = _norm(offset_dir)

        offset_vec = _scale(offset_dir, offset_distance)

        # Pontos da linha de cota principal
        dim_start = _add(start_pt, offset_vec)
        dim_end = _add(end_pt, offset_vec)
        dim_mid = _scale(_add(dim_start, dim_end), 0.5)

        # Linhas de extensão (witness lines)
        # Recuo da peça (gap = 0.02m) e overshoot além da linha de cota (0.05m)
        gap = 0.02 * (1.0 if offset_distance >= 0 else -1.0)
        overshoot = 0.05 * (1.0 if offset_distance >= 0 else -1.0)

        ext1_start = _add(start_pt, _scale(offset_dir, gap))
        ext1_end = _add(dim_start, _scale(offset_dir, overshoot))

        ext2_start = _add(end_pt, _scale(offset_dir, gap))
        ext2_end = _add(dim_end, _scale(offset_dir, overshoot))

        # Formatação do texto da cota
        if custom_text:
            formatted_text = custom_text
        else:
            if unit == "mm":
                val = raw_dist * 1000.0
                formatted_text = f"{val:.{precision}f} mm"
            elif unit == "cm":
                val = raw_dist * 100.0
                formatted_text = f"{val:.{precision}f} cm"
            elif unit == "in":
                val = raw_dist * 39.3701
                formatted_text = f'{val:.{precision}f}"'
            else:  # m
                formatted_text = f"{raw_dist:.{precision}f} m"

        # Tiques arquitetônicos a 45° nos extremos da linha de cota
        tick_size = 0.03
        tick_dir = _norm(_add(dir_vec, offset_dir))
        tick1 = [
            _add(dim_start, _scale(tick_dir, -tick_size)),
            _add(dim_start, _scale(tick_dir, tick_size)),
        ]
        tick2 = [
            _add(dim_end, _scale(tick_dir, -tick_size)),
            _add(dim_end, _scale(tick_dir, tick_size)),
        ]

        return {
            "type": "SUDimensionLinearRef",
            "distance_m": round(raw_dist, 4),
            "text": formatted_text,
            "unit": unit,
            "text_position": [round(c, 4) for c in dim_mid],
            "dimension_line": [
                [round(c, 4) for c in dim_start],
                [round(c, 4) for c in dim_end],
            ],
            "witness_lines": [
                [[round(c, 4) for c in ext1_start], [round(c, 4) for c in ext1_end]],
                [[round(c, 4) for c in ext2_start], [round(c, 4) for c in ext2_end]],
            ],
            "ticks": [
                [[round(c, 4) for c in tick1[0]], [round(c, 4) for c in tick1[1]]],
                [[round(c, 4) for c in tick2[0]], [round(c, 4) for c in tick2[1]]],
            ],
            "arrow_type": arrow_type.upper(),
            "status": f"COTA LINEAR CALCULADA ({formatted_text})",
        }
