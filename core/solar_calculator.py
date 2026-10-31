"""
SketchBuild - Motor Astronômico de Estudo Solar e Sombras Analíticas
(Frente 28 - Zero DLL / Pure Python)

Calcula a trajetória solar analítica (Heliodon NOAA / ASHRAE), vetores de iluminação
e sombreamento 3D para o motor Three.js, e emite laudos de conforto térmico e
insolação para playgrounds em conformidade com a ABNT NBR 16071.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class SolarCalculator:
    """Calculador astronômico de posição solar, sombras e conforto térmico de áreas de lazer."""

    # Coordenadas padrão (São Paulo, Brasil: Lat -23.55°, Long -46.63°, Fuso UTC-3)
    DEFAULT_LAT = -23.5505
    DEFAULT_LON = -46.6333
    DEFAULT_UTC_OFFSET = -3.0

    @classmethod
    def calculate_sun_position(
        cls,
        day_of_year: int = 80,  # 80 = Equinócio de Outono (21 de Março)
        solar_hour: float = 14.0,  # 14h00
        latitude_deg: float = DEFAULT_LAT,
        longitude_deg: float = DEFAULT_LON,
        utc_offset: float = DEFAULT_UTC_OFFSET,
    ) -> Dict[str, Any]:
        """Calcula a altitude solar (elevação), azimute e vetor de luz 3D unitário."""
        n = max(1, min(int(day_of_year), 365))
        lat_rad = math.radians(latitude_deg)

        # 1. Declinação Solar (graus)
        # delta = 23.45 * sin(360/365 * (284 + n))
        delta_deg = 23.45 * math.sin(math.radians((360.0 / 365.0) * (284 + n)))
        delta_rad = math.radians(delta_deg)

        # 2. Equação do Tempo (EoT em minutos)
        b_deg = (360.0 / 365.0) * (n - 81)
        b_rad = math.radians(b_deg)
        eot_min = 9.87 * math.sin(2 * b_rad) - 7.53 * math.cos(b_rad) - 1.5 * math.sin(b_rad)

        # 3. Hora Solar Verdadeira (Local Solar Time)
        lstm = 15.0 * utc_offset
        tc_min = 4.0 * (longitude_deg - lstm) + eot_min
        lst_hour = solar_hour + (tc_min / 60.0)

        # 4. Ângulo Horário (Hour Angle)
        # H = 15 graus por hora a partir do meio-dia solar
        h_deg = 15.0 * (lst_hour - 12.0)
        h_rad = math.radians(h_deg)

        # 5. Altitude Solar (Elevação alfa acima do horizonte)
        sin_alpha = math.sin(lat_rad) * math.sin(delta_rad) + math.cos(lat_rad) * math.cos(delta_rad) * math.cos(h_rad)
        sin_alpha = max(-1.0, min(1.0, sin_alpha))
        alpha_rad = math.asin(sin_alpha)
        alpha_deg = math.degrees(alpha_rad)

        is_sun_up = alpha_deg > 0.0

        # 6. Azimute Solar (gama em graus de 0 a 360 a partir do Norte)
        if abs(math.cos(alpha_rad)) > 1e-6:
            cos_gamma = (math.sin(delta_rad) * math.cos(lat_rad) - math.cos(delta_rad) * math.sin(lat_rad) * math.cos(h_rad)) / math.cos(alpha_rad)
            cos_gamma = max(-1.0, min(1.0, cos_gamma))
            gamma_deg = math.degrees(math.acos(cos_gamma))
            if h_deg > 0:
                gamma_deg = 360.0 - gamma_deg
        else:
            gamma_deg = 180.0

        gamma_rad = math.radians(gamma_deg)

        # 7. Vetor de Luz Solar 3D para Three.js (onde Y é vertical, X é Leste, Z é Sul)
        # A luz incide do sol para a origem
        if is_sun_up:
            sun_x = math.sin(gamma_rad) * math.cos(alpha_rad)
            sun_y = math.sin(alpha_rad)
            sun_z = -math.cos(gamma_rad) * math.cos(alpha_rad)
        else:
            sun_x, sun_y, sun_z = 0.0, -1.0, 0.0

        norm = math.sqrt(sun_x**2 + sun_y**2 + sun_z**2)
        if norm > 1e-6:
            light_dir = [round(sun_x / norm, 4), round(sun_y / norm, 4), round(sun_z / norm, 4)]
        else:
            light_dir = [0.0, 1.0, 0.0]

        return {
            "day_of_year": n,
            "hour": round(solar_hour, 2),
            "altitude_deg": round(alpha_deg, 2),
            "azimuth_deg": round(gamma_deg, 2),
            "is_daylight": is_sun_up,
            "light_direction_3d": light_dir,
            "sun_vector": [round(sun_x, 4), round(sun_y, 4), round(sun_z, 4)],
            "shadow_length_multiplier": round(1.0 / math.tan(max(alpha_rad, 0.05)), 2) if is_sun_up else 0.0,
        }

    @classmethod
    def generate_day_curve(
        cls,
        day_of_year: int = 80,
        latitude_deg: float = DEFAULT_LAT,
        longitude_deg: float = DEFAULT_LON,
    ) -> Dict[str, Any]:
        """Gera a curva horária completa de insolação (das 06:00 às 18:00) para o Heliodon."""
        hours_curve = []
        for h in range(6, 19):
            pos = cls.calculate_sun_position(
                day_of_year=day_of_year,
                solar_hour=float(h),
                latitude_deg=latitude_deg,
                longitude_deg=longitude_deg,
            )
            hours_curve.append(pos)

        # Análise de conforto infantil NBR 16071
        # Horas de pico de radiação UV: 10h às 15h
        pico_altitudes = [p["altitude_deg"] for p in hours_curve if 10 <= p["hour"] <= 15 and p["is_daylight"]]
        max_altitude = max(pico_altitudes) if pico_altitudes else 0.0

        conforto_status = "Adequado"
        recomendacao = "Recomenda-se cobertura para sol a pino nos brinquedos rotomoldados."
        if max_altitude > 65.0:
            conforto_status = "Alta Radiação Solar"
            recomendacao = "Instalação obrigatória de toldos ou sombreiros sobre escorregadores (NBR 16071)."

        return {
            "day_of_year": day_of_year,
            "latitude": latitude_deg,
            "longitude": longitude_deg,
            "max_solar_altitude_deg": round(max_altitude, 1),
            "conforto_termico_status": conforto_status,
            "recomendacao_nbr16071": recomendacao,
            "hourly_positions": hours_curve,
        }
