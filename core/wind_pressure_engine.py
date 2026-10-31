"""
SketchBuild - Simulação de Vento e Pressão Dinâmica NBR 6123 (Zero DLL / Pure Python)
Frente 103: Engenharia Reversa do SketchUp - Wind Pressure & Structural Aerodynamics (NBR 6123)

Calcula a velocidade característica de rajada (Vk), pressão dinâmica (q) e forças
resultantes de sucção e sobrepressão de vento em fachadas e coberturas.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class WindPressureEngine:
    """Motor analítico de cálculo de vento normativo NBR 6123."""

    @staticmethod
    def calculate_wind_pressure(
        basic_speed_v0_m_s: float = 45.0,  # Isopletas do Brasil (ex: SP = 40~45 m/s)
        terrain_category: str = "IV",      # Categoria IV (cidades, subúrbios)
        building_height_m: float = 12.0,
        facade_width_m: float = 20.0,
        facade_length_m: float = 15.0,
        topographic_s1: float = 1.0,       # Terreno plano
        statistical_s3: float = 1.0        # Ocupação normal (fator 1.0)
    ) -> Dict[str, Any]:
        """
        Calcula as forças estáticas equivalentes de vento pela NBR 6123.
        """
        # Parâmetros de rugosidade da Categoria IV (Tabela 2 NBR 6123 - Classe B)
        # S2 = b * Fr * (z / 10)^p
        cat = terrain_category.upper()
        if cat == "I":
            b, p = 1.10, 0.06
        elif cat == "II":
            b, p = 1.00, 0.09
        elif cat == "III":
            b, p = 0.94, 0.12
        elif cat == "V":
            b, p = 0.75, 0.23
        else:  # IV (default)
            b, p = 0.86, 0.15

        z_clamped = max(5.0, min(building_height_m, 200.0))
        s2 = b * ((z_clamped / 10.0) ** p)

        # Velocidade característica: Vk = V0 * S1 * S2 * S3
        vk = basic_speed_v0_m_s * topographic_s1 * s2 * statistical_s3

        # Pressão dinâmica básica: q = 0.613 * Vk² (em N/m² ou Pa)
        q_pa = 0.613 * (vk ** 2)

        # Coeficientes de pressão externa médios (Cpe) - NBR 6123
        # Vento a 0°: Fachada frontal (Barlavento: +0.8), Fachada posterior (Sotavento: -0.5), Laterais (-0.7)
        cpe_windward = 0.8
        cpe_leeward = -0.5
        cpe_side = -0.7

        # Áreas das fachadas
        area_frontal = facade_width_m * building_height_m
        area_lateral = facade_length_m * building_height_m

        # Forças resultantes: F = q * Cpe * Area (em kN)
        f_windward_kn = (q_pa * cpe_windward * area_frontal) / 1000.0
        f_leeward_kn = (q_pa * abs(cpe_leeward) * area_frontal) / 1000.0
        total_drag_force_kn = f_windward_kn + f_leeward_kn

        return {
            "entity_type": "WindPressureReport",
            "parameters": {
                "basic_speed_v0_m_s": basic_speed_v0_m_s,
                "terrain_category": cat,
                "building_height_m": building_height_m,
                "factors": {
                    "s1_topographic": topographic_s1,
                    "s2_roughness_height": round(s2, 4),
                    "s3_statistical": statistical_s3,
                }
            },
            "aerodynamics": {
                "characteristic_velocity_vk_m_s": round(vk, 2),
                "dynamic_pressure_q_pa": round(q_pa, 2),
                "dynamic_pressure_kgf_m2": round(q_pa / 9.81, 2),
            },
            "facade_loads": {
                "windward_pressure_pa": round(q_pa * cpe_windward, 2),
                "leeward_suction_pa": round(q_pa * cpe_leeward, 2),
                "side_walls_suction_pa": round(q_pa * cpe_side, 2),
                "windward_force_kn": round(f_windward_kn, 2),
                "leeward_force_kn": round(f_leeward_kn, 2),
                "total_horizontal_drag_kn": round(total_drag_force_kn, 2),
            },
            "status": "ANÁLISE DE PRESSÃO DE VENTO NBR 6123 CONCLUÍDA COM SUCESSO"
        }
