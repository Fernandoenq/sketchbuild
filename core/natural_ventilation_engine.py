"""
Motor de Ventilação Natural e Efeito Chaminé ABNT NBR 15220 / ASHRAE (Natural Ventilation - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 137).
Modelagem analítica de ventilação cruzada por ação do vento (pressão dinâmica delta_Cp) e tiragem térmica
(Stack Effect / Efeito Chaminé em átrios/lanternins), cálculo da vazão volumétrica (m3/s) e taxa de trocas de ar (ACH).
"""

from __future__ import annotations

import math
from typing import Any


class NaturalVentilationEngine:
    """Motor analítico de cálculo de ventilação natural em Python puro."""

    @staticmethod
    def calculate_ventilation(
        room_volume_m3: float = 180.0,
        inlet_opening_area_m2: float = 2.50,
        outlet_opening_area_m2: float = 2.50,
        vertical_height_difference_m: float = 4.0,  # Desnível entre abertura inferior e superior
        wind_speed_m_s: float = 3.5,  # Velocidade média do vento externo
        wind_incidence_angle_deg: float = 45.0,  # Ângulo de incidência na fachada
        outdoor_temp_c: float = 22.0,
        indoor_temp_c: float = 27.0,  # Ambiente interno mais quente (força motriz do efeito chaminé)
    ) -> dict[str, Any]:
        """
        Calcula as vazões combinadas de vento e tiragem térmica:
        Q_vento = Cd * A_equiv * v * cos(theta)
        Q_termico = Cd * A_equiv * sqrt(2 * g * H * delta_T / T_m)
        Q_combinado = sqrt(Q_vento^2 + Q_termico^2)
        """
        # Área equivalente de abertura em série: A_eq = (A1 * A2) / sqrt(A1^2 + A2^2)
        a1, a2 = inlet_opening_area_m2, outlet_opening_area_m2
        a_equiv_m2 = (a1 * a2) / math.sqrt((a1 ** 2) + (a2 ** 2))
        cd = 0.60  # Coeficiente de descarga de aberturas de janelas

        # 1. Ventilação por Vento (Pressão eólica):
        wind_rad = math.radians(wind_incidence_angle_deg)
        effective_wind_speed = wind_speed_m_s * max(0.2, math.cos(wind_rad))
        # Coeficiente de pressão delta Cp entre barlavento e sotavento ~ 0.50
        delta_cp = 0.50
        q_wind_m3_s = cd * a_equiv_m2 * effective_wind_speed * math.sqrt(delta_cp)

        # 2. Ventilação por Efeito Chaminé (Térmica / Flutuabilidade):
        delta_t = abs(indoor_temp_c - outdoor_temp_c)
        t_mean_kelvin = 273.15 + ((indoor_temp_c + outdoor_temp_c) / 2.0)

        # Q_stack = Cd * A_eq * sqrt(2 * g * H * (delta_T / T_m))
        stack_factor = (2.0 * 9.81 * vertical_height_difference_m * (delta_t / t_mean_kelvin))
        q_stack_m3_s = cd * a_equiv_m2 * math.sqrt(max(0.0, stack_factor))

        # 3. Vazão combinada quadrática (método recomendado ASHRAE):
        q_total_m3_s = math.sqrt((q_wind_m3_s ** 2) + (q_stack_m3_s ** 2))
        q_total_m3_h = q_total_m3_s * 3600.0

        # Taxa de trocas de ar por hora (Air Changes per Hour - ACH):
        ach = round(q_total_m3_h / max(1.0, room_volume_m3), 1)

        # Avaliação de conforto bioclimático NBR 15220:
        # ACH >= 6.0 trocas/h garante excelente resfriamento passivo
        is_excellent_ventilation = ach >= 6.0

        return {
            "entity_type": "NaturalVentilationReport",
            "parameters": {
                "room_volume_m3": room_volume_m3,
                "inlet_area_m2": inlet_opening_area_m2,
                "outlet_area_m2": outlet_opening_area_m2,
                "height_difference_m": vertical_height_difference_m,
                "wind_speed_m_s": wind_speed_m_s,
                "outdoor_temp_c": outdoor_temp_c,
                "indoor_temp_c": indoor_temp_c,
            },
            "ventilation_results": {
                "equivalent_opening_area_m2": round(a_equiv_m2, 2),
                "wind_driven_flow_m3_s": round(q_wind_m3_s, 2),
                "stack_effect_flow_m3_s": round(q_stack_m3_s, 2),
                "total_combined_airflow_m3_s": round(q_total_m3_s, 2),
                "total_combined_airflow_m3_h": round(q_total_m3_h, 1),
                "air_changes_per_hour_ach": ach,
                "is_effective_cooling": is_excellent_ventilation,
                "status_label": f"VENTILAÇÃO NATURAL: {ach} trocas/hora ({round(q_total_m3_h, 0)} m3/h - {'CONFORTE PASSIVO EFICAZ' if is_excellent_ventilation else 'MODERADA'})",
            },
            "status": "COMPUTED",
        }
