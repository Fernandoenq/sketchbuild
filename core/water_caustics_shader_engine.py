"""
SketchBuild - Shader PBR de Água, Ondas Gerstner e Cáusticas (Zero DLL / Pure Python)
Frente 99: Engenharia Reversa do SketchUp - PBR Water Surfaces, Gerstner Waves & Caustics

Configura parâmetros físicos para renderização de espelhos d'água, piscinas e lagos:
ondas analíticas de Gerstner, refração física (IOR 1.333), efeito Fresnel e mapa de cáusticas.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class WaterCausticsShaderEngine:
    """Motor analítico de parametrização física de água e cáusticas para Three.js."""

    @staticmethod
    def configure_water_surface(
        shallow_color_hex: str = "#4db5ff",
        deep_color_hex: str = "#004080",
        clarity_percent: float = 85.0,
        wave_amplitude_m: float = 0.05,
        wave_wavelength_m: float = 1.2,
        wave_speed_m_s: float = 1.0,
        ior: float = 1.333,
        caustics_intensity: float = 0.75,
        enable_foam: bool = True
    ) -> Dict[str, Any]:
        """
        Gera os uniformes analíticos de shader PBR para renderização de água realista no Three.js.
        """
        # Frequência espacial k = 2 * pi / lambda
        k_wave = (2.0 * math.pi) / max(0.1, wave_wavelength_m)
        # Frequência temporal omega = sqrt(g * k) (equação de dispersão em águas profundas)
        g_accel = 9.81
        omega = math.sqrt(g_accel * k_wave)

        # Reflectância normal de Fresnel: R0 = ((1.0 - IOR) / (1.0 + IOR))²
        fresnel_r0 = ((1.0 - ior) / (1.0 + ior)) ** 2

        # 3 trens de onda de Gerstner combinados para evitar repetição geométrica
        gerstner_waves = [
            {"direction": [1.0, 0.0],  "amplitude_m": wave_amplitude_m,        "wavelength_m": wave_wavelength_m,       "speed": wave_speed_m_s},
            {"direction": [0.7, 0.7],  "amplitude_m": wave_amplitude_m * 0.5,  "wavelength_m": wave_wavelength_m * 0.6, "speed": wave_speed_m_s * 1.2},
            {"direction": [-0.3, 0.9], "amplitude_m": wave_amplitude_m * 0.25, "wavelength_m": wave_wavelength_m * 0.3, "speed": wave_speed_m_s * 0.8},
        ]

        return {
            "entity_type": "PBRWaterMaterialConfig",
            "optical_properties": {
                "shallow_color": shallow_color_hex,
                "deep_color": deep_color_hex,
                "clarity_percent": clarity_percent,
                "refraction_index_ior": ior,
                "fresnel_r0": round(fresnel_r0, 5),
                "caustics_intensity": caustics_intensity,
                "enable_foam": enable_foam,
            },
            "wave_dynamics": {
                "primary_amplitude_m": wave_amplitude_m,
                "primary_wavelength_m": wave_wavelength_m,
                "wavenumber_k": round(k_wave, 4),
                "angular_frequency_omega": round(omega, 4),
                "gerstner_waves_count": len(gerstner_waves),
                "gerstner_waves": gerstner_waves,
            },
            "three_uniforms": {
                "uShallowColor": shallow_color_hex,
                "uDeepColor": deep_color_hex,
                "uClarity": clarity_percent / 100.0,
                "uWaveHeight": wave_amplitude_m,
                "uWaveSpeed": wave_speed_m_s,
                "uIor": ior,
                "uCausticsFactor": caustics_intensity,
            },
            "status": "SUPERFÍCIE PBR DE ÁGUA CONFIGURADA COM SUCESSO"
        }
