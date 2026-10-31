"""
Motor de Usinas Solares Fotovoltaicas e Geração Distribuída (Solar PV Array - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 136).
Dimensionamento paramétrico de arranjos de módulos solares em telhados ou solo,
cálculo do ângulo ótimo de inclinação (tilt), espaçamento entre fileiras sem sombreamento mútuo e geração estimada em kWh/ano.
"""

from __future__ import annotations

import math
from typing import Any


class SolarPhotovoltaicArrayEngine:
    """Motor analítico de dimensionamento de arranjos solares fotovoltaicos em Python puro."""

    @staticmethod
    def calculate_pv_system(
        roof_available_area_m2: float = 150.0,
        latitude_deg: float = -23.55,  # Latitude local (ex: São Paulo -23.55°)
        module_peak_power_w: float = 550.0,  # Painel solar moderno de 550W (dimensões ~ 2.28m x 1.13m)
        solar_irradiance_kwh_m2_day: float = 4.80,  # Irradiação solar média diária no plano horizontal (HSP)
        performance_ratio: float = 0.80,  # PR do sistema (perdas térmicas, sujeira, cabeamento e inversor)
        roof_tilt_deg: float | None = None,  # Se None, calcula o tilt ótimo (aproximadamente igual à latitude)
    ) -> dict[str, Any]:
        """
        Calcula a potência de pico (kWp), número máximo de módulos e geração anual estimada de energia.
        """
        module_length_m = 2.28
        module_width_m = 1.13
        module_area_m2 = module_length_m * module_width_m

        # Ângulo ótimo de inclinação do módulo (tilt):
        # Para latitudes tropicais: beta_otimo ~ abs(latitude) * 0.9 + 2 deg (mínimo 10° para autolimpeza da chuva)
        optimal_tilt_deg = max(10.0, abs(latitude_deg) * 0.90 + 2.0)
        tilt_deg = roof_tilt_deg if roof_tilt_deg is not None else optimal_tilt_deg
        tilt_rad = math.radians(tilt_deg)

        # Espaçamento mínimo entre fileiras para evitar sombreamento mútuo no solstício de inverno:
        # Altura do topo do painel: H = L_modulo * sin(tilt)
        module_projected_height_m = module_length_m * math.sin(tilt_rad)
        module_projected_width_m = module_length_m * math.cos(tilt_rad)

        # Ângulo solar mínimo no solstício ao meio-dia: alpha = 90 - abs(lat) - 23.45
        min_solar_elevation_deg = max(15.0, 90.0 - abs(latitude_deg) - 23.45)
        min_elevation_rad = math.radians(min_solar_elevation_deg)
        row_spacing_m = module_projected_width_m + (module_projected_height_m / math.tan(min_elevation_rad))

        # Área necessária por módulo com espaçamento entre fileiras:
        effective_area_per_module_m2 = row_spacing_m * module_width_m

        # Quantidade máxima de módulos fotovoltaicos cabíveis na área disponível:
        modules_count = math.floor(roof_available_area_m2 / effective_area_per_module_m2)

        # Potência total de pico instalada:
        installed_capacity_kwp = (modules_count * module_peak_power_w) / 1000.0

        # Geração de energia estimada:
        # E_dia (kWh/dia) = Potência_kWp * HSP * PR
        daily_generation_kwh = installed_capacity_kwp * solar_irradiance_kwh_m2_day * performance_ratio
        monthly_generation_kwh = daily_generation_kwh * 30.4
        annual_generation_kwh = daily_generation_kwh * 365.25

        # Economia financeira estimada (tarifa média R$ 0.85/kWh):
        annual_savings_brl = annual_generation_kwh * 0.85

        # Coordenadas 3D dos módulos solares
        modules_positions_3d = []
        cols = max(1, math.floor(math.sqrt(modules_count * 1.5)))
        rows = max(1, math.ceil(modules_count / cols))

        for r in range(rows):
            for c in range(cols):
                if len(modules_positions_3d) < modules_count:
                    mx = c * (module_width_m + 0.10)
                    my = r * row_spacing_m
                    mz = 0.5 * module_projected_height_m
                    modules_positions_3d.append([round(mx, 2), round(my, 2), round(mz, 2)])

        return {
            "entity_type": "SolarPhotovoltaicReport",
            "parameters": {
                "roof_available_area_m2": roof_available_area_m2,
                "latitude_deg": latitude_deg,
                "module_peak_power_w": module_peak_power_w,
                "solar_irradiance_kwh_m2_day": solar_irradiance_kwh_m2_day,
                "tilt_angle_deg": round(tilt_deg, 1),
            },
            "solar_system_metrics": {
                "modules_count": modules_count,
                "installed_capacity_kwp": round(installed_capacity_kwp, 2),
                "row_spacing_m": round(row_spacing_m, 2),
                "daily_energy_generation_kwh": round(daily_generation_kwh, 1),
                "monthly_energy_generation_kwh": round(monthly_generation_kwh, 1),
                "annual_energy_generation_kwh": round(annual_generation_kwh, 1),
                "estimated_annual_savings_brl": round(annual_savings_brl, 2),
                "co2_avoided_tons_year": round((annual_generation_kwh * 0.085) / 1000.0, 2),  # Fator emissão matriz BR
                "status_label": f"USINA SOLAR: {modules_count} painéis ({round(installed_capacity_kwp, 2)} kWp, {int(annual_generation_kwh)} kWh/ano, Economia R$ {int(annual_savings_brl)}/ano)",
            },
            "modules_positions_3d": modules_positions_3d[:15],
            "status": "COMPUTED",
        }
