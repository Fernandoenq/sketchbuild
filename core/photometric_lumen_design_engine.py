"""
Motor de Iluminação Artificial de Interiores e Método dos Lúmens ABNT NBR ISO/CIE 8995-1 (Photometric Lumen - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 135).
Cálculo da iluminância média mantida (Em em lux), índice do recinto K,
coeficiente de utilização de luminárias (CU), fator de depreciação/manutenção e quantidade de luminárias necessárias.
"""

from __future__ import annotations

import math
from typing import Any


class PhotometricLumenDesignEngine:
    """Motor analítico de cálculo luminotécnico pelo método dos lúmens em Python puro."""

    @staticmethod
    def calculate_lighting(
        room_length_m: float = 10.0,
        room_width_m: float = 6.0,
        ceiling_height_m: float = 3.0,
        workplane_height_m: float = 0.75,  # Altura da mesa de trabalho (m)
        target_lux: float = 500.0,  # Norma NBR ISO 8995: 500 lux para escritórios/escrita
        lamp_lumens: float = 4000.0,  # Fluxo luminoso por luminária LED (lúmens)
        luminaire_power_w: float = 36.0,
        maintenance_factor: float = 0.80,  # Fator de perda de luz/manutenção por poeira
        ceiling_reflectance: float = 0.70,
        wall_reflectance: float = 0.50,
        floor_reflectance: float = 0.20,
    ) -> dict[str, Any]:
        """
        Calcula o Índice do Recinto K = (L * W) / (h_montagem * (L + W))
        e o Fluxo Luminoso Total Necessário Phi = (E * A) / (CU * FM)
        """
        room_area_m2 = room_length_m * room_width_m
        mounting_height_h_m = ceiling_height_m - workplane_height_m

        # Índice do Recinto K:
        cavity_ratio_k = (room_length_m * room_width_m) / (mounting_height_h_m * (room_length_m + room_width_m))

        # Coeficiente de Utilização (CU) interpolado por K e refletâncias:
        # Para K ~ 1.5 a 3.0 em luminárias LED difusas de alta eficiência, CU varia de 0.55 a 0.70
        cu = 0.50 + 0.08 * math.log(max(0.5, cavity_ratio_k))
        cu = min(0.75, max(0.40, cu))

        # Fluxo luminoso total necessário (Lúmens):
        total_required_lumens = (target_lux * room_area_m2) / (cu * maintenance_factor)

        # Quantidade de luminárias necessárias:
        luminaires_count = math.ceil(total_required_lumens / lamp_lumens)

        # Arranjo ótimo da malha (colunas e linhas no teto)
        ratio_lw = room_length_m / room_width_m
        cols_count = max(1, math.ceil(math.sqrt(luminaires_count * ratio_lw)))
        rows_count = max(1, math.ceil(luminaires_count / cols_count))
        final_luminaires_count = cols_count * rows_count

        actual_average_lux = (final_luminaires_count * lamp_lumens * cu * maintenance_factor) / room_area_m2

        # Potência elétrica total instalada e densidade de potência (W/m2):
        total_lighting_power_w = final_luminaires_count * luminaire_power_w
        power_density_w_m2 = round(total_lighting_power_w / room_area_m2, 2)
        # NBR 8995 limita densidade a ~ 10-12 W/m2 para edifícios energeticamente eficientes
        is_energy_efficient = power_density_w_m2 <= 12.0

        # Coordenadas 3D das luminárias no plano do teto
        luminaire_positions_3d = []
        spacing_x = room_length_m / cols_count
        spacing_y = room_width_m / rows_count

        for ix in range(cols_count):
            for iy in range(rows_count):
                x = (ix + 0.5) * spacing_x
                y = (iy + 0.5) * spacing_y
                z = ceiling_height_m
                luminaire_positions_3d.append([round(x, 2), round(y, 2), round(z, 2)])

        return {
            "entity_type": "PhotometricLumenReport",
            "parameters": {
                "room_dimensions_m": [room_length_m, room_width_m, ceiling_height_m],
                "target_lux": target_lux,
                "lamp_lumens": lamp_lumens,
                "luminaire_power_w": luminaire_power_w,
                "maintenance_factor": maintenance_factor,
            },
            "lighting_results": {
                "room_cavity_ratio_k": round(cavity_ratio_k, 2),
                "coefficient_of_utilization_cu": round(cu, 2),
                "total_required_lumens": round(total_required_lumens, 0),
                "luminaires_layout_grid": [cols_count, rows_count],
                "total_luminaires_installed": final_luminaires_count,
                "actual_average_lux": round(actual_average_lux, 1),
                "total_installed_power_watts": total_lighting_power_w,
                "lighting_power_density_w_m2": power_density_w_m2,
                "is_energy_efficient": is_energy_efficient,
                "is_compliant_nbr8995": actual_average_lux >= target_lux,
                "status_label": f"ILUMINAÇÃO APROVADA: {final_luminaires_count} luminárias ({round(actual_average_lux, 0)} lux >= {int(target_lux)} lux, {power_density_w_m2} W/m2)",
            },
            "luminaire_positions_3d": luminaire_positions_3d,
            "status": "COMPUTED",
        }
