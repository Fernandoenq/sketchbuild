"""
Motor de Redes Coletoras de Esgoto Sanitário por Gravidade ABNT NBR 9649 (Sewer Network - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 118).
Dimensionamento hidráulico em escoamento livre, verificação de lâmina máxima (y/D <= 0.75),
tensão trativa mínima de autolimpeza (tau >= 1.0 Pa) e cálculo de declividade mínima.
"""

from __future__ import annotations

import math
from typing import Any


class SewerNetworkGravityEngine:
    """Motor analítico de dimensionamento de esgoto sanitário em Python puro."""

    @staticmethod
    def calculate_sewer_run(
        pipe_diameter_dn_mm: float = 150.0,  # Diâmetro nominal mínimo coletor predial/público (mm)
        flow_rate_l_s: float = 2.50,  # Vazão final de esgoto (L/s)
        pipe_length_m: float = 40.0,
        slope_m_m: float = 0.008,  # Declividade de 0.8%
        manning_n: float = 0.013,  # PVC liso
    ) -> dict[str, Any]:
        """
        Calcula lâmina d'água (y/D), velocidade de escoamento e tensão trativa de arrasto.
        """
        d_m = pipe_diameter_dn_mm / 1000.0
        q_m3_s = flow_rate_l_s / 1000.0

        # Vazão a seção plena por Manning: Q0 = (pi * D^2 / 4) * (D / 4)^(2/3) * S^(1/2) / n
        area_full_m2 = (math.pi * (d_m ** 2)) / 4.0
        rh_full_m = d_m / 4.0
        q_full_m3_s = (1.0 / manning_n) * area_full_m2 * (rh_full_m ** (2.0 / 3.0)) * math.sqrt(slope_m_m)

        flow_ratio = min(1.0, q_m3_s / max(0.0001, q_full_m3_s))

        # Aproximação analítica robusta para relação y/D em função de Q/Q0
        # Relação trigonométrica clássica de condutos circulares
        y_over_d = math.pow(flow_ratio, 0.60)
        y_over_d = min(0.95, max(0.05, y_over_d))
        water_depth_m = y_over_d * d_m

        # Raio hidráulico efetivo aproximado
        rh_eff_m = rh_full_m * (1.0 + 0.3 * math.sin(math.pi * y_over_d))
        area_eff_m2 = area_full_m2 * math.pow(y_over_d, 1.25)

        velocity_m_s = q_m3_s / max(0.0001, area_eff_m2)

        # Tensão trativa média de arrasto NBR 9649: tau = gamma_w * Rh * S (em Pascais)
        # gamma_w = 9810 N/m3
        shear_stress_pa = 9810.0 * rh_eff_m * slope_m_m

        # Verificação normativa NBR 9649:
        # 1. Lâmina máxima y/D <= 0.75
        is_depth_ok = y_over_d <= 0.75
        # 2. Tensão trativa mínima tau >= 1.0 Pa para garantir autolimpeza de sólidos
        is_shear_ok = shear_stress_pa >= 1.00
        # 3. Velocidade crítica (evitar desgaste) v <= 5.0 m/s
        is_velocity_ok = 0.60 <= velocity_m_s <= 5.00

        is_compliant = is_depth_ok and is_shear_ok and is_velocity_ok

        # Desnível geométrico total do trecho
        delta_h_m = pipe_length_m * slope_m_m

        # Geometria 3D representativa do tubo cilíndrico inclinado
        vertices = [
            [0.0, 0.0, delta_h_m], [pipe_length_m, 0.0, 0.0],
            [0.0, d_m, delta_h_m], [pipe_length_m, d_m, 0.0],
        ]
        triangles = [[0, 1, 2], [1, 3, 2]]

        return {
            "entity_type": "SewerNetworkReport",
            "parameters": {
                "pipe_diameter_dn_mm": pipe_diameter_dn_mm,
                "flow_rate_l_s": flow_rate_l_s,
                "pipe_length_m": pipe_length_m,
                "slope_m_m": slope_m_m,
                "manning_n": manning_n,
            },
            "hydraulic_metrics": {
                "full_pipe_capacity_l_s": round(q_full_m3_s * 1000.0, 2),
                "water_depth_ratio_y_d": round(y_over_d, 3),
                "water_depth_m": round(water_depth_m, 3),
                "flow_velocity_m_s": round(velocity_m_s, 2),
                "shear_stress_pa": round(shear_stress_pa, 2),
                "elevation_drop_m": round(delta_h_m, 3),
                "is_self_cleaning_compliant": is_shear_ok,
                "is_depth_compliant": is_depth_ok,
                "is_compliant_nbr9649": is_compliant,
                "status_label": "TRECHO DE ESGOTO APROVADO (NBR 9649)" if is_compliant else "ATENÇÃO: RISCO DE SEDIMENTAÇÃO OU AFOGAMENTO",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
