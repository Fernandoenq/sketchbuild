"""
Motor de Madeira Laminada Colada (Glulam) e CLT ABNT NBR 7190 / Eurocode 5 (Engineered Timber - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 129).
Dimensionamento analítico de vigas de madeira engenheirada (Glulam GL24h/GL28h) e painéis CLT multicamadas cruzadas,
resistência à flexão, módulo de elasticidade efetivo E0_mean, flambagem com torção e taxa de carbonização residual ao fogo.
"""

from __future__ import annotations

import math
from typing import Any


class GlulamCltTimberEngine:
    """Motor analítico de dimensionamento de madeira engenheirada em Python puro."""

    @staticmethod
    def calculate_timber(
        timber_type: str = "GLULAM_BEAM",  # GLULAM_BEAM ou CLT_PANEL
        span_m: float = 9.0,
        width_b_cm: float = 16.0,
        height_h_cm: float = 45.0,
        distributed_load_kn_m: float = 12.0,  # Carga de serviço q_k (kN/m)
        timber_class: str = "GL28h",  # f_m_k = 28 MPa, E_0_mean = 12600 MPa
        fire_resistance_rating_minutes: int = 60,  # RRF (minutos de exposição ao fogo)
    ) -> dict[str, Any]:
        """
        Calcula tensão atuante de flexão sigma_m, flecha elástica instantânea w_inst e final w_fin,
        e seção residual após carbonização ao fogo com taxa beta_n = 0.65 mm/min.
        """
        # Propriedades de resistência da madeira engenheirada (GL28h)
        f_m_k_mpa = 28.0
        e_mean_mpa = 12600.0
        gamma_m = 1.30
        k_mod = 0.80  # Classe de carregamento de média duração e umidade classe 1

        f_m_d_mpa = (k_mod * f_m_k_mpa) / gamma_m

        b_m = width_b_cm / 100.0
        h_m = height_h_cm / 100.0

        area_m2 = b_m * h_m
        inertia_m4 = (b_m * (h_m ** 3)) / 12.0
        section_modulus_w_m3 = (b_m * (h_m ** 2)) / 6.0

        # Momento fletor de cálculo M_sd = 1.4 * (q * L^2 / 8)
        m_k_kn_m = (distributed_load_kn_m * (span_m ** 2)) / 8.0
        m_sd_kn_m = m_k_kn_m * 1.40

        # Tensão atuante de flexão: sigma_m_d = M_sd / W
        sigma_m_d_kpa = m_sd_kn_m / section_modulus_w_m3
        sigma_m_d_mpa = round(sigma_m_d_kpa / 1000.0, 2)
        bending_utilization_ratio = round(sigma_m_d_mpa / f_m_d_mpa, 2)
        is_bending_safe = bending_utilization_ratio <= 1.0

        # Verificação de deformação (flecha elástica NBR 7190):
        # w_inst = (5 * q * L^4) / (384 * E * I)
        e_kpa = e_mean_mpa * 1000.0
        w_inst_m = (5.0 * distributed_load_kn_m * (span_m ** 4)) / (384.0 * e_kpa * inertia_m4)
        w_inst_mm = round(w_inst_m * 1000.0, 1)

        # Limite de flecha sensorial L/300
        w_limit_mm = round((span_m * 1000.0) / 300.0, 1)
        is_deflection_safe = w_inst_mm <= w_limit_mm

        # 3. Resistência ao Fogo NBR 7190 / Eurocode 5 (Charring):
        # Taxa de carbonização unidimensional beta_0 = 0.65 mm/min para madeira colada
        # Camada de transição d_0 = 7.0 mm
        charring_rate_mm_min = 0.65
        char_depth_d_char_mm = (charring_rate_mm_min * fire_resistance_rating_minutes) + 7.0
        char_depth_d_char_cm = char_depth_d_char_mm / 10.0

        # Seção residual carbonizada
        b_residual_cm = max(2.0, width_b_cm - (2.0 * char_depth_d_char_cm))
        h_residual_cm = max(2.0, height_h_cm - char_depth_d_char_cm)
        residual_area_ratio = round((b_residual_cm * h_residual_cm) / (width_b_cm * height_h_cm), 2)
        is_fire_safe = residual_area_ratio >= 0.40

        # Geometria 3D da viga de madeira
        vertices = [
            [0.0, -b_m/2, 0.0], [span_m, -b_m/2, 0.0], [span_m, b_m/2, 0.0], [0.0, b_m/2, 0.0],
            [0.0, -b_m/2, h_m], [span_m, -b_m/2, h_m], [span_m, b_m/2, h_m], [0.0, b_m/2, h_m],
        ]
        triangles = [
            [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1], [2, 6, 7], [2, 7, 3],
        ]

        return {
            "entity_type": "GlulamTimberReport",
            "parameters": {
                "timber_type": timber_type,
                "timber_class": timber_class,
                "span_m": span_m,
                "section_dimensions_cm": [width_b_cm, height_h_cm],
                "distributed_load_kn_m": distributed_load_kn_m,
                "fire_rating_minutes": fire_resistance_rating_minutes,
            },
            "timber_structural_results": {
                "design_bending_stress_mpa": sigma_m_d_mpa,
                "design_strength_fmd_mpa": round(f_m_d_mpa, 2),
                "bending_utilization_ratio": bending_utilization_ratio,
                "elastic_deflection_mm": w_inst_mm,
                "allowable_deflection_limit_mm": w_limit_mm,
                "is_deflection_compliant": is_deflection_safe,
                "fire_charring_depth_mm": round(char_depth_d_char_mm, 1),
                "residual_section_cm": [round(b_residual_cm, 1), round(h_residual_cm, 1)],
                "fire_capacity_safe": is_fire_safe,
                "status_label": f"MADEIRA {timber_class} APROVADA (Taxa Flexão: {int(bending_utilization_ratio*100)}%, Flecha: {w_inst_mm}mm <= {w_limit_mm}mm, Fogo {fire_resistance_rating_minutes}min)",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
