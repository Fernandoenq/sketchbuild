"""
SketchBuild - Planificação e Desdobramento de Chapa Metálica (Zero DLL / Pure Python)
Frente 97: Engenharia Reversa do SketchUp - Sheet Metal Unfolding & Flat Pattern (DIN 6935)

Calcula o desenvolvimento plano de peças em chapa dobrada (Blank Flat Pattern),
aplicando fórmulas normativas de tolerância de dobra (Bend Allowance / K-Factor)
para corte a laser e conformação em prensa dobradeira.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class SheetMetalUnfoldEngine:
    """Motor analítico de cálculo de desdobramento de chapas metálicas."""

    @staticmethod
    def calculate_bend_allowance(
        bend_angle_deg: float,
        thickness_mm: float,
        inner_radius_mm: float,
        k_factor: float = 0.44
    ) -> Dict[str, float]:
        """
        Fórmula normativa DIN 6935:
        BA = (pi / 180) * angle * (R + K * T)
        Setback = (R + T) * tan(angle / 2)
        BD = 2 * Setback - BA
        """
        angle_rad = math.radians(bend_angle_deg)
        ba = angle_rad * (inner_radius_mm + k_factor * thickness_mm)
        setback = (inner_radius_mm + thickness_mm) * math.tan(angle_rad / 2.0)
        bd = (2.0 * setback) - ba

        return {
            "bend_angle_deg": bend_angle_deg,
            "bend_allowance_mm": round(ba, 4),
            "setback_mm": round(setback, 4),
            "bend_deduction_mm": round(bd, 4)
        }

    @staticmethod
    def unfold_flanges(
        base_length_mm: float,
        base_width_mm: float,
        thickness_mm: float = 2.0,
        inner_radius_mm: float = 2.0,
        k_factor: float = 0.44,
        flanges: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calcula o Blank total planificado de uma peça com base e abas (flanges) dobradas.
        flanges: [{'name': str, 'edge': 'LEFT'/'RIGHT'/'TOP'/'BOTTOM', 'length_mm': float, 'angle_deg': float}]
        """
        flanges = flanges or []
        flange_results: List[Dict[str, Any]] = []

        total_length_mm = base_length_mm
        total_width_mm = base_width_mm

        bend_lines: List[Dict[str, Any]] = []

        for f in flanges:
            edge = f.get("edge", "RIGHT").upper()
            f_len = float(f.get("length_mm", 50.0))
            f_angle = float(f.get("angle_deg", 90.0))

            b_calc = SheetMetalUnfoldEngine.calculate_bend_allowance(
                f_angle, thickness_mm, inner_radius_mm, k_factor
            )
            # Comprimento desenvolvido da aba: L_desenv = F_len - Setback + (BA / 2)
            developed_flange = f_len - b_calc["setback_mm"] + b_calc["bend_allowance_mm"]

            flange_results.append({
                "name": f.get("name", f"Aba_{edge}"),
                "edge": edge,
                "nominal_length_mm": f_len,
                "bend_angle_deg": f_angle,
                "developed_flange_length_mm": round(developed_flange, 3),
                "bend_allowance_mm": b_calc["bend_allowance_mm"],
                "bend_deduction_mm": b_calc["bend_deduction_mm"]
            })

            # Atualizar dimensões totais do Blank
            if edge in ("LEFT", "RIGHT"):
                total_length_mm += developed_flange
                bend_lines.append({
                    "flange_edge": edge,
                    "position_mm": round(total_length_mm - developed_flange, 2),
                    "angle_deg": f_angle,
                    "direction": "UP" if f_angle > 0 else "DOWN"
                })
            elif edge in ("TOP", "BOTTOM"):
                total_width_mm += developed_flange
                bend_lines.append({
                    "flange_edge": edge,
                    "position_mm": round(total_width_mm - developed_flange, 2),
                    "angle_deg": f_angle,
                    "direction": "UP" if f_angle > 0 else "DOWN"
                })

        blank_area_mm2 = total_length_mm * total_width_mm

        return {
            "entity_type": "SheetMetalUnfoldResult",
            "material_thickness_mm": thickness_mm,
            "inner_bend_radius_mm": inner_radius_mm,
            "k_factor": k_factor,
            "base_dimensions_mm": [base_length_mm, base_width_mm],
            "blank_dimensions_mm": [round(total_length_mm, 2), round(total_width_mm, 2)],
            "blank_area_m2": round(blank_area_mm2 / 1e6, 4),
            "flanges_count": len(flanges),
            "flanges": flange_results,
            "bend_lines": bend_lines,
            "status": "PLANIFICAÇÃO DE CHAPA (BLANK) CALCULADA COM SUCESSO"
        }
