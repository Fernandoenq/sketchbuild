"""
SketchBuild - Lâmpadas Fotométricas e Holofotes Spot (Zero DLL / Pure Python)
Frente 92: Engenharia Reversa do SketchUp - Photometric Spotlights & IES Luminaire Profiles

Parametriza fontes de luz artificial (spots pontuais, holofotes cônicos e perfis IES),
calculando temperatura de cor em Kelvin, atenuação física inversa ao quadrado e
configuração analítica para Three.js SpotLight.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class PhotometricSpotLightEngine:
    """Motor analítico de iluminação spot artificial e conversão fotométrica."""

    @staticmethod
    def kelvin_to_rgb(temperature_k: float) -> Tuple[int, int, int]:
        """
        Algoritmo clássico de Tanner Helland para aproximação de corpo negro (Kelvin para RGB).
        Faixa recomendada: 1000K a 40000K.
        """
        temp = max(1000.0, min(temperature_k, 40000.0)) / 100.0

        # Vermelho (Red)
        if temp <= 66.0:
            red = 255
        else:
            red = int(329.698727446 * ((temp - 60.0) ** -0.1332047592))
            red = max(0, min(255, red))

        # Verde (Green)
        if temp <= 66.0:
            green = int(99.4708025861 * math.log(temp) - 161.1195681661)
            green = max(0, min(255, green))
        else:
            green = int(288.1221695283 * ((temp - 60.0) ** -0.0755148492))
            green = max(0, min(255, green))

        # Azul (Blue)
        if temp >= 66.0:
            blue = 255
        elif temp <= 19.0:
            blue = 0
        else:
            blue = int(138.5177312231 * math.log(temp - 10.0) - 305.0447927307)
            blue = max(0, min(255, blue))

        return (red, green, blue)

    @staticmethod
    def configure_spot_light(
        position: Tuple[float, float, float],
        target: Tuple[float, float, float],
        lumens: float = 1200.0,
        color_temperature_k: float = 3000.0,
        beam_angle_deg: float = 45.0,
        penumbra_percent: float = 25.0,
        max_distance_m: float = 20.0,
        cast_shadows: bool = True
    ) -> Dict[str, Any]:
        """
        Calcula os parâmetros canônicos de holofote cônico para renderizadores e Three.js.
        """
        dx = target[0] - position[0]
        dy = target[1] - position[1]
        dz = target[2] - position[2]
        dist = math.sqrt(dx**2 + dy**2 + dz**2)

        dir_vec = [
            round(dx / dist, 4) if dist > 1e-6 else 0.0,
            round(dy / dist, 4) if dist > 1e-6 else 0.0,
            round(dz / dist, 4) if dist > 1e-6 else -1.0,
        ]

        rgb = PhotometricSpotLightEngine.kelvin_to_rgb(color_temperature_k)
        hex_color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        # Ângulo do cone em radianos para Three.js (half-angle)
        cone_angle_rad = math.radians(beam_angle_deg / 2.0)
        penumbra_ratio = max(0.0, min(1.0, penumbra_percent / 100.0))

        # Três intensidades: lúmens brutos, candela axial estimada e intensidade Three.js
        # Candela axial aprox = Lumens / (2 * pi * (1 - cos(theta_half)))
        solid_angle = 2.0 * math.pi * (1.0 - math.cos(cone_angle_rad))
        axial_candela = lumens / solid_angle if solid_angle > 1e-4 else lumens

        return {
            "entity_type": "PhotometricSpotLight",
            "position": [round(position[0], 4), round(position[1], 4), round(position[2], 4)],
            "target": [round(target[0], 4), round(target[1], 4), round(target[2], 4)],
            "direction": dir_vec,
            "photometrics": {
                "lumens": lumens,
                "axial_candela": round(axial_candela, 2),
                "color_temperature_k": color_temperature_k,
                "color_rgb": list(rgb),
                "color_hex": hex_color,
            },
            "beam_geometry": {
                "beam_angle_deg": beam_angle_deg,
                "cone_angle_rad": round(cone_angle_rad, 4),
                "penumbra_percent": penumbra_percent,
                "max_distance_m": max_distance_m,
                "decay_exponent": 2.0,  # Físico 1/d²
            },
            "three_config": {
                "color": hex_color,
                "intensity": round(lumens / 100.0, 2),
                "distance": max_distance_m,
                "angle": round(cone_angle_rad, 4),
                "penumbra": round(penumbra_ratio, 3),
                "decay": 2,
                "castShadow": cast_shadows,
            },
            "status": "LÂMPADA FOTOMÉTRICA SPOT CONFIGURADA COM SUCESSO"
        }
