"""
SketchBuild - Motor de Sombras e Heliodon Integrado (Zero DLL / Pure Python)
Frente 70: Engenharia Reversa do SketchUp - SUShadowInfoRef & Astronomical Sun Vector

Implementa a decodificação dos parâmetros de sombreamento SUShadowInfoRef nativos do .skp,
cálculo astronômico da trajetória solar e conversão direta para os iluminadores
DirectionalLight e AmbientLight do Three.js.
"""

from __future__ import annotations

import datetime
import math
from typing import Any, Dict, Optional, Tuple


class ShadowHeliodonEngine:
    """Motor de cálculo de sombras e heliodon astronômico do SketchUp."""

    DEFAULT_LAT = -23.5505   # São Paulo
    DEFAULT_LON = -46.6333
    DEFAULT_TZ_OFFSET = -3.0

    @classmethod
    def calculate_shadow_info(
        cls,
        year: int = 2026,
        month: int = 3,
        day: int = 21,
        hour: int = 14,
        minute: int = 0,
        latitude: float = DEFAULT_LAT,
        longitude: float = DEFAULT_LON,
        tz_offset: float = DEFAULT_TZ_OFFSET,
        north_angle: float = 0.0,
        light_intensity: int = 80,
        dark_intensity: int = 45,
        display_shadows: bool = True,
        use_sun_for_shading: bool = True,
        edges_cast_shadows: bool = False,
    ) -> Dict[str, Any]:
        """
        Calcula o estado completo de sombreamento e iluminação no formato SUShadowInfoRef.
        """
        dt = datetime.datetime(year, month, day, hour, minute)
        day_of_year = dt.timetuple().tm_yday
        decimal_hour = hour + (minute / 60.0)

        lat_rad = math.radians(latitude)

        # 1. Declinação Solar (Cooper 1969)
        delta_deg = 23.45 * math.sin(math.radians((360.0 / 365.0) * (284 + day_of_year)))
        delta_rad = math.radians(delta_deg)

        # 2. Equação do Tempo (EoT)
        b_deg = (360.0 / 365.0) * (day_of_year - 81)
        b_rad = math.radians(b_deg)
        eot_min = 9.87 * math.sin(2 * b_rad) - 7.53 * math.cos(b_rad) - 1.5 * math.sin(b_rad)

        # 3. Tempo Solar Local (LST)
        lstm = 15.0 * tz_offset
        tc_min = 4.0 * (longitude - lstm) + eot_min
        lst_hour = decimal_hour + (tc_min / 60.0)

        # 4. Ângulo Horário (H)
        h_deg = 15.0 * (lst_hour - 12.0)
        h_rad = math.radians(h_deg)

        # 5. Altitude Solar (Alfa)
        sin_alpha = math.sin(lat_rad) * math.sin(delta_rad) + math.cos(lat_rad) * math.cos(delta_rad) * math.cos(h_rad)
        sin_alpha = max(-1.0, min(1.0, sin_alpha))
        alpha_rad = math.asin(sin_alpha)
        alpha_deg = math.degrees(alpha_rad)

        is_daylight = alpha_deg > 0.0

        # 6. Azimute Solar Natural (Gama a partir do Norte geográfico)
        if abs(math.cos(alpha_rad)) > 1e-6:
            cos_gamma = (math.sin(delta_rad) * math.cos(lat_rad) - math.cos(delta_rad) * math.sin(lat_rad) * math.cos(h_rad)) / math.cos(alpha_rad)
            cos_gamma = max(-1.0, min(1.0, cos_gamma))
            gamma_deg = math.degrees(math.acos(cos_gamma))
            if h_deg > 0:
                gamma_deg = 360.0 - gamma_deg
        else:
            gamma_deg = 180.0

        # Ajuste pelo North Angle (ângulo do norte relativo ao eixo Y positivo do modelo SketchUp)
        model_azimuth_deg = (gamma_deg - north_angle) % 360.0
        model_azimuth_rad = math.radians(model_azimuth_deg)

        # 7. Vetor de Luz Unitário para Three.js (onde Y é vertical, X é Leste, Z é Sul/Norte)
        # SketchUp coordinate system: Z up, Y north, X east.
        # Three.js coordinate system: Y up, X right (east), Z front (south).
        if is_daylight:
            sun_x = math.sin(model_azimuth_rad) * math.cos(alpha_rad)
            sun_y = math.sin(alpha_rad)
            sun_z = -math.cos(model_azimuth_rad) * math.cos(alpha_rad)
            sun_dist = 100.0  # Raio do domo
            light_pos = [round(sun_x * sun_dist, 2), round(sun_y * sun_dist, 2), round(sun_z * sun_dist, 2)]
        else:
            sun_x, sun_y, sun_z = 0.0, -1.0, 0.0
            light_pos = [0.0, -100.0, 0.0]

        # 8. Temperatura de cor e intensidades
        if is_daylight:
            sun_color = "#fffdf0" if alpha_deg > 20.0 else "#ffeaa7"
            dir_intensity = round((light_intensity / 100.0) * 1.5, 2)
        else:
            sun_color = "#2c3e50"
            dir_intensity = 0.0

        amb_intensity = round((dark_intensity / 100.0) * 0.8, 2)

        # 9. Cálculo aproximado de Nascer e Pôr do Sol
        # cos(H_sunrise) = -tan(lat) * tan(delta)
        tan_prod = math.tan(lat_rad) * math.tan(delta_rad)
        if abs(tan_prod) <= 1.0:
            h_sun_deg = math.degrees(math.acos(-tan_prod))
            sunrise_solar = 12.0 - (h_sun_deg / 15.0)
            sunset_solar = 12.0 + (h_sun_deg / 15.0)
            sunrise_clock = sunrise_solar - (tc_min / 60.0)
            sunset_clock = sunset_solar - (tc_min / 60.0)
            sunrise_str = f"{int(sunrise_clock):02d}:{int((sunrise_clock % 1) * 60):02d}"
            sunset_str = f"{int(sunset_clock):02d}:{int((sunset_clock % 1) * 60):02d}"
        else:
            sunrise_str = "00:00"
            sunset_str = "00:00"

        return {
            "type": "SUShadowInfoRef",
            "date_time": dt.isoformat(),
            "display_shadows": display_shadows,
            "use_sun_for_shading": use_sun_for_shading,
            "edges_cast_shadows": edges_cast_shadows,
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "tz_offset": tz_offset,
            "north_angle": round(north_angle, 2),
            "light_intensity_percent": light_intensity,
            "dark_intensity_percent": dark_intensity,
            "astronomy": {
                "day_of_year": day_of_year,
                "solar_altitude_deg": round(alpha_deg, 2),
                "solar_azimuth_deg": round(gamma_deg, 2),
                "is_daylight": is_daylight,
                "sunrise": sunrise_str,
                "sunset": sunset_str,
            },
            "sun_direction": [round(sun_x, 4), round(sun_y, 4), round(sun_z, 4)],
            "three_lighting": {
                "directional_light": {
                    "position": light_pos,
                    "color": sun_color,
                    "intensity": dir_intensity,
                    "cast_shadow": display_shadows and is_daylight,
                },
                "ambient_light": {
                    "color": "#dcdde1",
                    "intensity": amb_intensity,
                },
            },
        }
