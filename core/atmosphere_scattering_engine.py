"""
SketchBuild - Céu Físico Rayleigh & Mie e Espalhamento Atmosférico (Zero DLL / Pure Python)
Frente 104: Engenharia Reversa do SketchUp - Atmospheric Scattering & Physical Sky (Preetham Model)

Configura parâmetros analíticos de espalhamento de Rayleigh (céu azul) e Mie (névoa e halo solar)
com posição solar 3D astronômica integrada para Three.js Sky Shader.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class AtmosphericScatteringEngine:
    """Motor analítico de modelo de céu físico e espalhamento atmosférico."""

    @staticmethod
    def configure_physical_sky(
        solar_elevation_deg: float = 35.0,
        solar_azimuth_deg: float = 135.0,
        turbidity: float = 3.0,
        rayleigh: float = 1.2,
        mie_coefficient: float = 0.005,
        mie_directional_g: float = 0.82
    ) -> Dict[str, Any]:
        """
        Calcula os vetores e uniformes físicos do céu baseado no modelo Preetham para Three.js.
        """
        # Conversão de ângulos esféricos para vetor unitário de posição solar
        elev_rad = math.radians(solar_elevation_deg)
        azim_rad = math.radians(solar_azimuth_deg)

        # Vetor solar
        # No Three.js Sky: X = cos(elev) * sin(azim), Y = sin(elev), Z = cos(elev) * cos(azim)
        sun_x = math.cos(elev_rad) * math.sin(azim_rad)
        sun_y = math.sin(elev_rad)
        sun_z = math.cos(elev_rad) * math.cos(azim_rad)

        # Estimativa de temperatura de cor da luz direta em função da elevação solar
        # Céu zenital ~ 5800K, pôr do sol ~ 2200K
        sin_e = max(0.0, math.sin(elev_rad))
        approx_kelvin = 2000.0 + (sin_e ** 0.5) * 4000.0

        # Coeficientes espectrais de Rayleigh para comprimentos de onda RGB [680nm, 550nm, 440nm]
        # beta_rayleigh = 8 * pi³ * (n² - 1)² / (3 * N * lambda⁴)
        lambda_r = 680e-9
        lambda_g = 550e-9
        lambda_b = 440e-9
        base_const = 1e-31
        beta_r = [
            round(base_const / (lambda_r ** 4) * rayleigh, 6),
            round(base_const / (lambda_g ** 4) * rayleigh, 6),
            round(base_const / (lambda_b ** 4) * rayleigh, 6),
        ]

        return {
            "entity_type": "AtmosphericSkyConfig",
            "solar_angles": {
                "elevation_deg": solar_elevation_deg,
                "azimuth_deg": solar_azimuth_deg,
                "solar_zenith_rad": round((math.pi / 2.0) - elev_rad, 4),
            },
            "sun_position_vector": [round(sun_x, 5), round(sun_y, 5), round(sun_z, 5)],
            "atmospheric_parameters": {
                "turbidity": turbidity,
                "rayleigh": rayleigh,
                "mie_coefficient": mie_coefficient,
                "mie_directional_g": mie_directional_g,
                "estimated_sun_kelvin": round(approx_kelvin, 1),
                "rayleigh_spectral_betas": beta_r,
            },
            "three_sky_uniforms": {
                "turbidity": turbidity,
                "rayleigh": rayleigh,
                "mieCoefficient": mie_coefficient,
                "mieDirectionalG": mie_directional_g,
                "sunPosition": [round(sun_x, 5), round(sun_y, 5), round(sun_z, 5)],
            },
            "status": "CÉU FÍSICO ATMOSFÉRICO CONFIGURADO COM SUCESSO"
        }
