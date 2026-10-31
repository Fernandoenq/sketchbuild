"""
Motor de Drenagem Pluvial, Calhas e Condutores ABNT NBR 10844 (Stormwater Drainage - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 116).
Dimensionamento hidráulico de calhas de beiral/platibanda e condutores verticais/horizontais
segundo a equação de Manning-Strickler e vazões de projeto pluviais.
"""

from __future__ import annotations

import math
from typing import Any


class StormwaterDrainageEngine:
    """Motor analítico de dimensionamento de calhas e condutores pluviais em Python puro."""

    @staticmethod
    def calculate_drainage(
        roof_area_m2: float = 120.0,
        rainfall_intensity_mm_h: float = 150.0,  # Chuva de projeto (mm/h) para período de retorno T=5 anos
        gutter_width_m: float = 0.20,
        gutter_depth_m: float = 0.15,
        gutter_slope_m_m: float = 0.005,  # Declividade mínima 0.5%
        manning_roughness: float = 0.011,  # n de Manning (PVC = 0.011, Aço Galvanizado = 0.013)
        downspout_diameter_mm: float = 100.0,
        gutters_count: int = 2,
    ) -> dict[str, Any]:
        """
        Calcula vazão de projeto (Q = I * A / 60) em L/min e capacidade de calhas e condutores.
        """
        # 1. Vazão de projeto NBR 10844: Q = (I * A) / 60 em Litros/min
        total_design_flow_l_min = (rainfall_intensity_mm_h * roof_area_m2) / 60.0
        design_flow_per_gutter_l_min = total_design_flow_l_min / max(1, gutters_count)
        design_flow_m3_s = (design_flow_per_gutter_l_min / 60.0) / 1000.0

        # 2. Capacidade da Calha Trapezoidal/Retangular por Manning:
        # Q = (1 / n) * A_molhada * R_h^(2/3) * S^(1/2)
        # Assumindo lâmina d'água máxima de 80% da profundidade da calha (borda livre de segurança)
        water_depth_m = gutter_depth_m * 0.80
        wet_area_m2 = gutter_width_m * water_depth_m
        wetted_perimeter_m = gutter_width_m + 2.0 * water_depth_m
        hydraulic_radius_m = wet_area_m2 / max(0.001, wetted_perimeter_m)

        gutter_capacity_m3_s = (1.0 / manning_roughness) * wet_area_m2 * (hydraulic_radius_m ** (2.0 / 3.0)) * math.sqrt(gutter_slope_m_m)
        gutter_capacity_l_min = gutter_capacity_m3_s * 60.0 * 1000.0

        is_gutter_ok = gutter_capacity_l_min >= design_flow_per_gutter_l_min

        # 3. Capacidade do Condutor Vertical NBR 10844:
        # Para condutores verticais de altura padrão com funil de entrada:
        # Capacidade tabelada Q = 0.00366 * D^(8/3) aproximadamente
        d_m = downspout_diameter_mm / 1000.0
        downspout_capacity_l_min = (0.00366 * (downspout_diameter_mm ** (8.0 / 3.0))) * 60.0
        is_downspout_ok = downspout_capacity_l_min >= design_flow_per_gutter_l_min

        # 4. Geração geométrica 3D da calha (extrusão prismática no eixo X)
        length_m = 6.0
        w = gutter_width_m
        h = gutter_depth_m
        vertices = [
            [-length_m / 2, -w / 2, 0.0],
            [length_m / 2, -w / 2, 0.0],
            [length_m / 2, w / 2, 0.0],
            [-length_m / 2, w / 2, 0.0],
            [-length_m / 2, -w / 2, h],
            [length_m / 2, -w / 2, h],
            [length_m / 2, w / 2, h],
            [-length_m / 2, w / 2, h],
        ]
        triangles = [
            [0, 1, 2], [0, 2, 3],  # Fundo
            [0, 4, 5], [0, 5, 1],  # Lateral A
            [2, 6, 7], [2, 7, 3],  # Lateral B
        ]

        return {
            "entity_type": "StormwaterDrainageReport",
            "parameters": {
                "roof_area_m2": roof_area_m2,
                "rainfall_intensity_mm_h": rainfall_intensity_mm_h,
                "gutter_width_m": gutter_width_m,
                "gutter_depth_m": gutter_depth_m,
                "gutter_slope_m_m": gutter_slope_m_m,
                "downspout_diameter_mm": downspout_diameter_mm,
                "gutters_count": gutters_count,
            },
            "hydraulic_results": {
                "total_design_flow_l_min": round(total_design_flow_l_min, 1),
                "design_flow_per_gutter_l_min": round(design_flow_per_gutter_l_min, 1),
                "gutter_capacity_l_min": round(gutter_capacity_l_min, 1),
                "downspout_capacity_l_min": round(downspout_capacity_l_min, 1),
                "is_gutter_adequate": is_gutter_ok,
                "is_downspout_adequate": is_downspout_ok,
                "is_compliant_nbr10844": is_gutter_ok and is_downspout_ok,
                "status_label": "CALHAS E CONDUTORES APROVADOS (NBR 10844)" if (is_gutter_ok and is_downspout_ok) else "ATENÇÃO: VAZÃO EXCEDE CAPACIDADE",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
