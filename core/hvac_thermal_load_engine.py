"""
Motor de Carga Térmica de Climatização HVAC ASHRAE / ABNT NBR 16401 (HVAC Thermal Load - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 134).
Cálculo analítico de carga térmica de resfriamento (sensível e latente), radiação solar através de vidros,
condução por paredes e coberturas, calor dissipado por ocupantes, iluminação, equipamentos e ar exterior de renovação.
"""

from __future__ import annotations

import math
from typing import Any


class HvacThermalLoadEngine:
    """Motor analítico de cálculo de carga térmica HVAC em Python puro."""

    @staticmethod
    def calculate_cooling_load(
        floor_area_m2: float = 80.0,
        ceiling_height_m: float = 2.80,
        occupants_count: int = 8,
        lighting_power_w_m2: float = 12.0,  # Iluminação LED típica
        equipment_power_w: float = 1500.0,  # Computadores e eletrodomésticos
        window_area_north_m2: float = 12.0,  # Janelas voltadas para o Norte
        outdoor_temp_c: float = 34.0,  # Temperatura de bulbo seco externa de projeto
        indoor_temp_c: float = 24.0,  # Temperatura de conforto de bulbo seco interna
        fresh_air_rate_l_s_person: float = 7.5,  # Vazão mínima de ar exterior NBR 16401
    ) -> dict[str, Any]:
        """
        Calcula os componentes de ganho de calor em Watts e converte para BTU/h e TR:
        Q_total = Q_envoltoria + Q_janelas_solar + Q_ocupantes + Q_iluminacao + Q_equipamentos + Q_ventilacao
        """
        delta_t = outdoor_temp_c - indoor_temp_c

        # 1. Condução por paredes opacas e teto (U médio ~ 1.8 W/m2K):
        # Perímetro estimado
        wall_area_m2 = 4.0 * math.sqrt(floor_area_m2) * ceiling_height_m - window_area_north_m2
        u_wall = 1.80
        q_walls_w = wall_area_m2 * u_wall * delta_t

        # 2. Radiação solar e condução através de vidros (Fator solar FS ~ 0.70, Radiação norte ~ 450 W/m2):
        q_solar_glass_w = window_area_north_m2 * 450.0 * 0.70
        q_conduction_glass_w = window_area_north_m2 * 5.60 * delta_t
        q_windows_total_w = q_solar_glass_w + q_conduction_glass_w

        # 3. Carga interna de ocupantes (Calor sensível ~ 75W + calor latente ~ 55W por pessoa em repouso/escritório):
        q_occupants_sensible_w = occupants_count * 75.0
        q_occupants_latent_w = occupants_count * 55.0
        q_occupants_total_w = q_occupants_sensible_w + q_occupants_latent_w

        # 4. Carga de iluminação e equipamentos:
        q_lighting_w = floor_area_m2 * lighting_power_w_m2
        q_equipment_w = equipment_power_w

        # 5. Carga de ar exterior de renovação (Sensível e latente NBR 16401):
        # Vazão total de ar externo Q_ar (m3/s):
        q_fresh_air_m3_s = (occupants_count * fresh_air_rate_l_s_person) / 1000.0
        # Q_sensivel_ar = 1.2 * 1005 * Q_ar * delta_t (rho * cp)
        q_fresh_air_sensible_w = 1.20 * 1005.0 * q_fresh_air_m3_s * delta_t
        q_fresh_air_latent_w = q_fresh_air_sensible_w * 0.40  # Estimativa de umidade relativa tropical
        q_ventilation_total_w = q_fresh_air_sensible_w + q_fresh_air_latent_w

        # Carga térmica total
        total_cooling_load_w = q_walls_w + q_windows_total_w + q_occupants_total_w + q_lighting_w + q_equipment_w + q_ventilation_total_w
        # Fator de segurança térmico de 10%
        design_cooling_load_w = total_cooling_load_w * 1.10

        # Conversão de unidades: 1 Watt = 3.412142 BTU/h, 1 TR = 12000 BTU/h = 3516.85 W
        total_btu_h = design_cooling_load_w * 3.412142
        total_tr = design_cooling_load_w / 3516.85
        load_density_btu_m2 = total_btu_h / floor_area_m2

        return {
            "entity_type": "HvacThermalLoadReport",
            "parameters": {
                "floor_area_m2": floor_area_m2,
                "ceiling_height_m": ceiling_height_m,
                "occupants_count": occupants_count,
                "outdoor_temp_c": outdoor_temp_c,
                "indoor_temp_c": indoor_temp_c,
                "window_area_m2": window_area_north_m2,
            },
            "thermal_load_breakdown": {
                "walls_conduction_w": round(q_walls_w, 1),
                "windows_solar_conduction_w": round(q_windows_total_w, 1),
                "occupants_heat_w": round(q_occupants_total_w, 1),
                "lighting_heat_w": round(q_lighting_w, 1),
                "equipment_heat_w": round(q_equipment_w, 1),
                "fresh_air_ventilation_w": round(q_ventilation_total_w, 1),
                "total_cooling_load_watts": round(design_cooling_load_w, 1),
                "total_cooling_capacity_btu_h": round(total_btu_h, 0),
                "total_cooling_capacity_tr": round(total_tr, 2),
                "specific_cooling_load_btu_m2": round(load_density_btu_m2, 0),
                "status_label": f"CARGA TÉRMICA: {round(total_tr, 2)} TR ({int(round(total_btu_h, 0))} BTU/h - Densidade {int(round(load_density_btu_m2, 0))} BTU/m2)",
            },
            "status": "COMPUTED",
        }
