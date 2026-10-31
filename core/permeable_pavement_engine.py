"""
Motor de Pavimentação Permeável e Drenagem Sustentável ABNT NBR 16416 (Permeable Pavement - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 117).
Dimensionamento de camadas de base/sub-base drenante, cálculo do coeficiente de escoamento (Runoff C),
capacidade de infiltração e reservatório de amortecimento hídrico subterrâneo.
"""

from __future__ import annotations

import math
from typing import Any


class PermeablePavementEngine:
    """Motor analítico de dimensionamento de pavimento drenante em Python puro."""

    @staticmethod
    def calculate_pavement(
        pavement_area_m2: float = 250.0,
        design_rainfall_mm: float = 60.0,  # Precipitação de projeto (mm)
        surface_type: str = "INTERLOCKING_CONCRETE_BLOCKS",  # Blocos intertravados permeáveis
        base_thickness_m: float = 0.25,  # Espessura da camada de brita drenante (m)
        base_voids_ratio: float = 0.38,  # Índice de vazios da brita nº 3/4
        soil_infiltration_rate_mm_h: float = 15.0,  # Taxa de infiltração do solo subjacente
        rain_duration_hours: float = 1.0,
    ) -> dict[str, Any]:
        """
        Calcula balanço hídrico de infiltração, volume armazenado temporariamente e redução de pico.
        """
        # Volume total precipitado sobre o pavimento
        total_rain_volume_m3 = (design_rainfall_mm / 1000.0) * pavement_area_m2

        # Infiltração para o subleito durante o evento de chuva
        infiltrated_volume_m3 = ((soil_infiltration_rate_mm_h * rain_duration_hours) / 1000.0) * pavement_area_m2
        infiltrated_volume_m3 = min(total_rain_volume_m3, infiltrated_volume_m3)

        # Volume necessário a ser retido na camada de base drenante
        required_storage_volume_m3 = max(0.0, total_rain_volume_m3 - infiltrated_volume_m3)

        # Capacidade máxima de armazenamento da base de brita
        base_storage_capacity_m3 = pavement_area_m2 * base_thickness_m * base_voids_ratio

        is_storage_adequate = base_storage_capacity_m3 >= required_storage_volume_m3

        # Coeficiente de escoamento superficial resultante (Runoff C):
        # Para pavimento permeável bem dimensionado, C varia de 0.10 a 0.25 (contra 0.90 de asfalto)
        runoff_coefficient_c = 0.15 if is_storage_adequate else 0.45
        runoff_reduction_percent = round((1.0 - (runoff_coefficient_c / 0.90)) * 100.0, 1)

        # Tempo de esvaziamento completo da base por percolação
        drainage_time_hours = round(required_storage_volume_m3 / max(0.01, (soil_infiltration_rate_mm_h / 1000.0) * pavement_area_m2), 1)

        # Malha 3D multicamadas representativa (Placa retangular do pavimento)
        dim = math.sqrt(pavement_area_m2)
        w, l = round(dim, 2), round(dim, 2)
        h = base_thickness_m + 0.08  # Base + Bloco 8cm
        vertices = [
            [0.0, 0.0, 0.0], [w, 0.0, 0.0], [w, l, 0.0], [0.0, l, 0.0],
            [0.0, 0.0, h], [w, 0.0, h], [w, l, h], [0.0, l, h],
        ]
        triangles = [
            [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
        ]

        return {
            "entity_type": "PermeablePavementReport",
            "parameters": {
                "pavement_area_m2": pavement_area_m2,
                "design_rainfall_mm": design_rainfall_mm,
                "surface_type": surface_type,
                "base_thickness_m": base_thickness_m,
                "base_voids_ratio": base_voids_ratio,
                "soil_infiltration_rate_mm_h": soil_infiltration_rate_mm_h,
            },
            "drainage_metrics": {
                "total_rain_volume_m3": round(total_rain_volume_m3, 2),
                "infiltrated_volume_m3": round(infiltrated_volume_m3, 2),
                "required_storage_volume_m3": round(required_storage_volume_m3, 2),
                "base_storage_capacity_m3": round(base_storage_capacity_m3, 2),
                "is_storage_adequate": is_storage_adequate,
                "resulting_runoff_c": runoff_coefficient_c,
                "runoff_reduction_percent": runoff_reduction_percent,
                "reservoir_drainage_time_hours": drainage_time_hours,
                "status_label": "PAVIMENTO PERMEÁVEL APROVADO (NBR 16416)" if is_storage_adequate else "REQUER AUMENTAR ESPESSURA DA BASE DE BRITA",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
