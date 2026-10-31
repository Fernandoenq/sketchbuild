"""
SketchBuild - Gerenciador de Georreferenciamento e Coordenadas Globais (Zero DLL / Pure Python)
Frente 80: Engenharia Reversa do SketchUp - SUGeoReferenceRef

Gerencia localização geográfica (Latitude, Longitude, Altitude, Norte Verdadeiro),
conversão métrica para UTM e mapeamento bidirecional entre coordenadas locais (x,y,z) e WGS84.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class GeoReferenceEngine:
    """Motor de cálculo e projeção geográfica do SketchUp (SUGeoReferenceRef)."""

    # Elipsoide WGS84
    WGS84_A = 6378137.0         # Semi-eixo maior (metros)
    WGS84_E_SQ = 0.00669437999  # Primeira excentricidade ao quadrado

    @classmethod
    def set_geo_location(
        cls,
        latitude: float,
        longitude: float,
        altitude_m: float = 0.0,
        north_angle_deg: float = 0.0,
        city: str = "São Paulo",
        country: str = "Brasil",
    ) -> Dict[str, Any]:
        """
        Define a localização geográfica do modelo no padrão SUGeoReferenceRef.
        """
        lat = max(-90.0, min(90.0, float(latitude)))
        lon = max(-180.0, min(180.0, float(longitude)))
        utm = cls.lat_lon_to_utm(lat, lon)

        return {
            "type": "SUGeoReferenceRef",
            "latitude": round(lat, 6),
            "longitude": round(lon, 6),
            "altitude_m": round(altitude_m, 2),
            "north_angle_deg": round(north_angle_deg % 360.0, 2),
            "city": city,
            "country": country,
            "utm": utm,
            "status": f"GEORREFERENCIAMENTO CONFIGURADO ({city}, {country})",
        }

    @classmethod
    def lat_lon_to_utm(cls, lat: float, lon: float) -> Dict[str, Any]:
        """Converte coordenadas geodésicas (Lat, Lon) em coordenadas planas UTM (WGS84)."""
        zone = int((lon + 180.0) / 6.0) + 1
        hemisphere = "N" if lat >= 0 else "S"
        lon_origin = (zone - 1) * 6 - 180 + 3
        lon_origin_rad = math.radians(lon_origin)

        lat_rad = math.radians(lat)
        lon_rad = math.radians(lon)

        a = cls.WGS84_A
        e2 = cls.WGS84_E_SQ
        e_prime2 = e2 / (1.0 - e2)

        n = a / math.sqrt(1.0 - e2 * math.sin(lat_rad) ** 2)
        t = math.tan(lat_rad) ** 2
        c = e_prime2 * math.cos(lat_rad) ** 2
        al = math.cos(lat_rad) * (lon_rad - lon_origin_rad)

        # Distância meridional M
        m = a * (
            (1.0 - e2 / 4.0 - 3.0 * e2**2 / 64.0 - 5.0 * e2**3 / 256.0) * lat_rad
            - (3.0 * e2 / 8.0 + 3.0 * e2**2 / 32.0 + 45.0 * e2**3 / 1024.0) * math.sin(2.0 * lat_rad)
            + (15.0 * e2**2 / 256.0 + 45.0 * e2**3 / 1024.0) * math.sin(4.0 * lat_rad)
            - (35.0 * e2**3 / 3072.0) * math.sin(6.0 * lat_rad)
        )

        k0 = 0.9996
        easting = k0 * n * (al + (1.0 - t + c) * al**3 / 6.0 + (5.0 - 18.0 * t + t**2 + 72.0 * c - 58.0 * e_prime2) * al**5 / 120.0) + 500000.0
        northing = k0 * (m + n * math.tan(lat_rad) * (al**2 / 2.0 + (5.0 - t + 9.0 * c + 4.0 * c**2) * al**4 / 24.0 + (61.0 - 58.0 * t + t**2 + 600.0 * c - 330.0 * e_prime2) * al**6 / 720.0))
        if lat < 0:
            northing += 10000000.0

        return {
            "zone": zone,
            "hemisphere": hemisphere,
            "easting_m": round(easting, 2),
            "northing_m": round(northing, 2),
        }

    @classmethod
    def local_point_to_wgs84(
        cls,
        local_xyz_m: Tuple[float, float, float],
        origin_lat: float,
        origin_lon: float,
        origin_alt_m: float = 0.0,
        north_angle_deg: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Converte um ponto 3D local do modelo (x, y, z em metros) para coordenadas geográficas reais WGS84.
        """
        x, y, z = local_xyz_m
        theta = math.radians(north_angle_deg)

        # Rotação pelo ângulo do Norte verdadeiro
        delta_north = y * math.cos(theta) - x * math.sin(theta)
        delta_east = y * math.sin(theta) + x * math.cos(theta)

        lat_rad = math.radians(origin_lat)
        m_per_deg_lat = 111132.954 - 559.822 * math.cos(2 * lat_rad) + 1.175 * math.cos(4 * lat_rad)
        m_per_deg_lon = (math.pi / 180.0) * cls.WGS84_A * math.cos(lat_rad) / math.sqrt(1.0 - cls.WGS84_E_SQ * math.sin(lat_rad) ** 2)

        calc_lat = origin_lat + (delta_north / m_per_deg_lat)
        calc_lon = origin_lon + (delta_east / max(1.0, m_per_deg_lon))
        calc_alt = origin_alt_m + z

        return {
            "local_xyz_m": [round(c, 4) for c in local_xyz_m],
            "latitude": round(calc_lat, 8),
            "longitude": round(calc_lon, 8),
            "altitude_m": round(calc_alt, 3),
            "delta_north_m": round(delta_north, 3),
            "delta_east_m": round(delta_east, 3),
            "status": "COORDENADA GEOGRÁFICA CALCULADA",
        }
