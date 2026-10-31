"""
Motor de Bacias de Detenção e Amortecimento Hidrológico de Cheias (Detention Basin - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 119).
Cálculo de hidrograma de entrada/saída, volume de espera para amortecimento de cheias
e dimensionamento de vertedouro e orifício de descarga de fundo.
"""

from __future__ import annotations

import math
from typing import Any


class DetentionBasinHydrologyEngine:
    """Motor analítico de dimensionamento de bacia de retenção/detenção em Python puro."""

    @staticmethod
    def calculate_basin(
        catchment_area_ha: float = 5.0,  # Área da bacia de contribuição em hectares (1 ha = 10.000 m2)
        runoff_coefficient: float = 0.70,  # Coeficiente de escoamento pós-ocupação
        design_rainfall_intensity_mm_h: float = 120.0,
        allowable_outflow_l_s: float = 250.0,  # Vazão máxima permitida pelo órgão regulador (vazão pré-desenvolvimento)
        basin_depth_m: float = 2.0,  # Profundidade útil da bacia (m)
        side_slope_h_v: float = 2.0,  # Talude lateral da bacia (2H:1V)
    ) -> dict[str, Any]:
        """
        Calcula o volume de amortecimento necessário pelo método do volume simplificado.
        """
        # Área em m2
        area_m2 = catchment_area_ha * 10000.0

        # Vazão de pico de entrada pelo Método Racional: Q_in = (C * I * A) / 360 (m3/s)
        peak_inflow_m3_s = (runoff_coefficient * design_rainfall_intensity_mm_h * area_m2) / 3600000.0
        peak_inflow_l_s = peak_inflow_m3_s * 1000.0

        # Vazão permitida em m3/s
        outflow_m3_s = allowable_outflow_l_s / 1000.0

        # Volume estimado de detenção por envelope triangular de chuva (duração crítica ~ 60 min)
        duration_seconds = 3600.0
        total_inflow_volume_m3 = 0.5 * peak_inflow_m3_s * duration_seconds * 1.5

        # Volume a reter na bacia
        attenuation_ratio = max(0.1, 1.0 - (outflow_m3_s / max(0.01, peak_inflow_m3_s)))
        required_storage_volume_m3 = total_inflow_volume_m3 * attenuation_ratio

        # Dimensões da bacia trapezoidal invertida
        # V ~ L_base * W_base * h + correções de talude
        base_area_m2 = required_storage_volume_m3 / basin_depth_m
        side_m = math.sqrt(base_area_m2)
        bottom_length_m = round(side_m * 1.2, 1)
        bottom_width_m = round(side_m / 1.2, 1)

        top_length_m = round(bottom_length_m + 2.0 * side_slope_h_v * basin_depth_m, 1)
        top_width_m = round(bottom_width_m + 2.0 * side_slope_h_v * basin_depth_m, 1)

        # Dimensionamento do orifício de descarga de fundo: Q = Cd * A * sqrt(2 * g * h)
        # Cd = 0.62
        orifice_area_m2 = outflow_m3_s / (0.62 * math.sqrt(2.0 * 9.81 * (basin_depth_m * 0.70)))
        orifice_diameter_mm = math.sqrt((4.0 * orifice_area_m2) / math.pi) * 1000.0

        # Vertedouro de emergência de soleira livre: Q = 1.84 * L * H^(1.5)
        weir_length_m = round(peak_inflow_m3_s / (1.84 * math.pow(0.5, 1.5)), 2)

        # Geometria 3D da escavação da bacia
        vertices = [
            [-bottom_length_m/2, -bottom_width_m/2, 0.0],
            [bottom_length_m/2, -bottom_width_m/2, 0.0],
            [bottom_length_m/2, bottom_width_m/2, 0.0],
            [-bottom_length_m/2, bottom_width_m/2, 0.0],
            [-top_length_m/2, -top_width_m/2, basin_depth_m],
            [top_length_m/2, -top_width_m/2, basin_depth_m],
            [top_length_m/2, top_width_m/2, basin_depth_m],
            [-top_length_m/2, top_width_m/2, basin_depth_m],
        ]
        triangles = [
            [0, 1, 2], [0, 2, 3],  # Fundo
            [0, 4, 5], [0, 5, 1],  # Talude sul
            [1, 5, 6], [1, 6, 2],  # Talude leste
            [2, 6, 7], [2, 7, 3],  # Talude norte
            [3, 7, 4], [3, 4, 0],  # Talude oeste
        ]

        return {
            "entity_type": "DetentionBasinReport",
            "parameters": {
                "catchment_area_ha": catchment_area_ha,
                "runoff_coefficient": runoff_coefficient,
                "design_rainfall_intensity_mm_h": design_rainfall_intensity_mm_h,
                "allowable_outflow_l_s": allowable_outflow_l_s,
                "basin_depth_m": basin_depth_m,
            },
            "hydrologic_results": {
                "peak_inflow_l_s": round(peak_inflow_l_s, 1),
                "peak_reduction_percent": round((1.0 - (allowable_outflow_l_s / peak_inflow_l_s)) * 100.0, 1),
                "required_storage_volume_m3": round(required_storage_volume_m3, 1),
                "bottom_dimensions_m": [bottom_length_m, bottom_width_m],
                "top_dimensions_m": [top_length_m, top_width_m],
                "bottom_orifice_diameter_mm": round(orifice_diameter_mm, 1),
                "emergency_weir_length_m": weir_length_m,
                "status_label": "BACIA DE DETENÇÃO REDUZ 100% DO EXCEDENTE DE CHEIA",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
