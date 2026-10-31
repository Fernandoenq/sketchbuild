"""
Motor de Iluminação Natural e Fator de Luz Diurna FLD NBR 15215 (Daylight Factor - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 113).
Cálculo analítico do Fator de Luz Diurna (FLD %) pelo método BRS simplificado, iluminância
média em lux (Céu encoberto CIE) e conformidade com os requisitos mínimos da ABNT NBR 15215.
"""

from __future__ import annotations

import math
from typing import Any


class DaylightFactorEngine:
    """Motor analítico de iluminação natural e conformidade NBR 15215 em Python puro."""

    @staticmethod
    def calculate_daylight_factor(
        room_width_m: float = 4.0,
        room_depth_m: float = 6.0,
        room_height_m: float = 2.80,
        window_width_m: float = 2.0,
        window_height_m: float = 1.20,
        window_sill_height_m: float = 1.0,
        glass_transmittance: float = 0.85,  # Vidro incolor simples ~0.85; duplo ~0.75
        external_horizontal_lux: float = 10000.0,  # Céu padrão encoberto CIE
        average_internal_reflectance: float = 0.50,  # Paredes claras (0.50 a 0.60)
        obstruction_angle_deg: float = 15.0,  # Ângulo de obstrução de prédios vizinhos
    ) -> dict[str, Any]:
        """
        Calcula o FLD médio e em grid de pontos no plano de trabalho (0.75m de altura).
        """
        floor_area_m2 = room_width_m * room_depth_m
        total_surface_area_m2 = 2.0 * floor_area_m2 + 2.0 * (room_width_m + room_depth_m) * room_height_m
        window_area_m2 = window_width_m * window_height_m

        # Ângulo visível de céu (Theta em graus) descontando obstrução do horizonte:
        sky_angle_deg = max(5.0, 90.0 - obstruction_angle_deg)

        # Fórmula simplificada BRS (Building Research Station) para FLD médio (%):
        # FLD_médio = (Aw * tau * theta) / (At * (1 - R))
        # Ajustado para escala percentual
        theta_factor = sky_angle_deg / 90.0
        r_term = max(0.1, 1.0 - average_internal_reflectance)
        fld_average_percent = (
            (window_area_m2 * glass_transmittance * theta_factor)
            / (total_surface_area_m2 * r_term)
        ) * 100.0 * 2.2  # Coeficiente empírico de calibração geométrica

        fld_average_percent = min(15.0, max(0.5, fld_average_percent))

        # Iluminância interna média estimada em Lux: E = FLD * E_ext / 100
        lux_internal_avg = (fld_average_percent / 100.0) * external_horizontal_lux

        # NBR 15215-4: FLD mínimo recomendado para salas residenciais / escritórios:
        # Geralmente FLD >= 2.0% (ou mínimo 150 a 300 lux sob céu encoberto)
        is_compliant = fld_average_percent >= 2.0

        # Amostragem em grelha 3x3 no plano de trabalho Z = 0.75m
        grid_points = []
        for xi in range(3):
            for yi in range(3):
                # Distância da janela (situada na parede Y = 0)
                px = (xi + 0.5) * (room_width_m / 3.0)
                py = (yi + 0.5) * (room_depth_m / 3.0)
                # O FLD decai exponencialmente com a profundidade do ambiente
                decay = math.exp(-0.45 * py)
                pt_fld = fld_average_percent * decay * 1.6
                grid_points.append({
                    "x_m": round(px, 2),
                    "y_m": round(py, 2),
                    "z_m": 0.75,
                    "fld_percent": round(pt_fld, 2),
                    "lux": round((pt_fld / 100.0) * external_horizontal_lux, 0)
                })

        return {
            "entity_type": "DaylightFactorReport",
            "parameters": {
                "floor_area_m2": round(floor_area_m2, 2),
                "window_area_m2": round(window_area_m2, 2),
                "glass_transmittance": glass_transmittance,
                "sky_condition": "Céu Encoberto Padrão CIE (10.000 lux)",
            },
            "daylight_metrics": {
                "average_fld_percent": round(fld_average_percent, 2),
                "average_lux": round(lux_internal_avg, 0),
                "min_recommended_fld_percent": 2.0,
                "is_compliant_nbr15215": is_compliant,
                "status_label": "ILUMINAÇÃO NATURAL ADEQUADA (NBR 15215)" if is_compliant else "INSUFICIENTE: AMPLIAR VÃO DE JANELA OU REDUZIR OBSTRUÇÃO",
            },
            "workplane_grid_points": grid_points,
            "status": "COMPUTED",
        }
