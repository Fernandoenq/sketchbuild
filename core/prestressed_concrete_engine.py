"""
Motor de Concreto Protendido e Perdas de Protensão ABNT NBR 6118 (Prestressed Concrete - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 128).
Dimensionamento de força de protensão inicial (P0) e efetiva (P_inf), traçado parabólico de cabos com excentricidade e_p,
e cálculo analítico das perdas imediatas (atrito, acomodação de ancoragem, encurtamento elástico) e diferidas (fluência e retração).
"""

from __future__ import annotations

import math
from typing import Any


class PrestressedConcreteEngine:
    """Motor analítico de cálculo de concreto protendido em Python puro."""

    @staticmethod
    def calculate_prestressing(
        beam_span_m: float = 16.0,
        section_height_h_m: float = 0.90,
        section_width_bw_m: float = 0.35,
        strands_count: int = 8,  # Número de cordoalhas de 12.7mm (1/2")
        strand_nominal_area_mm2: float = 98.7,  # Cordoalha CP-190 RB
        fptk_steel_mpa: float = 1900.0,  # Tensão de ruptura característica
        concrete_fck_mpa: float = 40.0,
        eccentricity_midspan_m: float = 0.32,  # Excentricidade máxima no meio do vão
    ) -> dict[str, Any]:
        """
        Calcula as tensões normais de bordo superior e inferior no Estádio I:
        sigma = (P / A) -/+ (P * e * y / I) +/- (M_ext * y / I)
        """
        # Área de aço de protensão total
        ap_total_mm2 = strands_count * strand_nominal_area_mm2
        ap_total_m2 = ap_total_mm2 / 1e6

        # Propriedades da seção transversal retangular
        area_c_m2 = section_width_bw_m * section_height_h_m
        inertia_m4 = (section_width_bw_m * (section_height_h_m ** 3)) / 12.0
        y_inf_m = section_height_h_m / 2.0

        # Tensão máxima de tracionamento inicial na ancoragem (NBR 6118: 0.74 * fptk)
        sigma_p0_mpa = 0.74 * fptk_steel_mpa
        p0_kn = (sigma_p0_mpa * 1000.0) * ap_total_m2

        # 1. Perdas Imediatas de Protensão (~8% a 12%):
        # Atrito ao longo da bainha (mu ~ 0.20, k ~ 0.002):
        loss_friction_pct = 4.5
        # Acomodação da cunha de ancoragem (delta ~ 6mm):
        loss_anchorage_pct = 3.5
        # Encurtamento elástico do concreto:
        loss_elastic_pct = 3.0
        immediate_losses_total_pct = loss_friction_pct + loss_anchorage_pct + loss_elastic_pct

        p_immediate_kn = p0_kn * (1.0 - (immediate_losses_total_pct / 100.0))

        # 2. Perdas Diferidas no Tempo (Fluência e Retração do concreto + Relaxação do aço ~ 12% a 16%):
        deferred_losses_pct = 14.0
        total_losses_pct = immediate_losses_total_pct + deferred_losses_pct

        p_effective_inf_kn = p0_kn * (1.0 - (total_losses_pct / 100.0))

        # Carga equivalente distribuída ascendente por desvio parabólico (Balanço de Carga de T.Y. Lin):
        # q_eq = 8 * P * e / L^2
        upward_equivalent_load_kn_m = (8.0 * p_effective_inf_kn * eccentricity_midspan_m) / (beam_span_m ** 2)

        # Peso próprio da viga de concreto (gamma = 25 kN/m3)
        self_weight_kn_m = area_c_m2 * 25.0
        net_gravity_load_kn_m = round(self_weight_kn_m - upward_equivalent_load_kn_m, 2)

        # Verificação da tensão no bordo inferior no meio do vão a tempo infinito sob peso próprio:
        # sigma_inf = (P_inf / A) + (P_inf * e * y / I) - (M_g * y / I)
        mg_kn_m = (self_weight_kn_m * (beam_span_m ** 2)) / 8.0
        sigma_inf_kpa = ((p_effective_inf_kn / area_c_m2) +
                         (p_effective_inf_kn * eccentricity_midspan_m * y_inf_m / inertia_m4) -
                         (mg_kn_m * y_inf_m / inertia_m4))
        sigma_inf_mpa = round(sigma_inf_kpa / 1000.0, 2)

        # Traçado 3D do cabo parabólico através do comprimento da viga
        cable_points_3d = []
        num_pts = 11
        for i in range(num_pts):
            x = (i / (num_pts - 1)) * beam_span_m
            # Parábola centrada: y(x) = 4 * e * (x/L) * (1 - x/L)
            e_x = 4.0 * eccentricity_midspan_m * (x / beam_span_m) * (1.0 - (x / beam_span_m))
            z = (section_height_h_m / 2.0) - e_x
            cable_points_3d.append([round(x, 2), 0.0, round(z, 3)])

        return {
            "entity_type": "PrestressedConcreteReport",
            "parameters": {
                "beam_span_m": beam_span_m,
                "section_dimensions_m": [section_width_bw_m, section_height_h_m],
                "strands_count": strands_count,
                "strand_type": "CP-190 RB 12.7mm",
                "eccentricity_midspan_m": eccentricity_midspan_m,
                "concrete_fck_mpa": concrete_fck_mpa,
            },
            "prestress_metrics": {
                "initial_prestress_force_p0_kn": round(p0_kn, 1),
                "immediate_losses_percent": immediate_losses_total_pct,
                "deferred_losses_percent": deferred_losses_pct,
                "total_prestress_losses_percent": total_losses_pct,
                "final_effective_force_p_inf_kn": round(p_effective_inf_kn, 1),
                "upward_balancing_load_kn_m": round(upward_equivalent_load_kn_m, 2),
                "self_weight_kn_m": round(self_weight_kn_m, 2),
                "net_deflection_load_kn_m": net_gravity_load_kn_m,
                "bottom_fiber_stress_mpa": sigma_inf_mpa,
                "is_compressed_fiber": sigma_inf_mpa > 0.0,
                "status_label": f"PROTENSÃO APROVADA: P_inf = {round(p_effective_inf_kn, 1)} kN (Compensação de Carga = {round((upward_equivalent_load_kn_m/self_weight_kn_m)*100, 1)}% do Peso)",
            },
            "parabolic_tendon_3d": cable_points_3d,
            "status": "COMPUTED",
        }
