"""
SketchBuild - Decodificador de Projeção Esférica e Panorama 360° (Zero DLL / Pure Python)
Frente 88: Engenharia Reversa do SketchUp - Spherical 360° Panorama & Cubemap Viewport

Gera parâmetros canônicos de projeção equirretangular 360x180 graus e matrizes
de câmera para as 6 faces do cubemap (Right, Left, Top, Bottom, Front, Back)
a partir de um ponto de vista da cena.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class EquirectangularPanoramaEngine:
    """Motor analítico de projeção esférica 360° e cubemap para VR / Three.js."""

    @staticmethod
    def calculate_cubemap_cameras(
        eye_position: Tuple[float, float, float]
    ) -> Dict[str, Any]:
        """
        Gera as 6 câmeras ortogonais (FOV 90°) para renderizar um cubemap a partir de eye_position.
        Tratamento padrão OpenGL/Three.js (+X, -X, +Y, -Y, +Z, -Z).
        """
        ex, ey, ez = eye_position

        faces = [
            {"face": "PX_RIGHT",  "target": [ex + 1.0, ey, ez],       "up": [0.0, 0.0, 1.0], "name": "+X (Direita)"},
            {"face": "NX_LEFT",   "target": [ex - 1.0, ey, ez],       "up": [0.0, 0.0, 1.0], "name": "-X (Esquerda)"},
            {"face": "PY_FRONT",  "target": [ex, ey + 1.0, ez],       "up": [0.0, 0.0, 1.0], "name": "+Y (Frente)"},
            {"face": "NY_BACK",   "target": [ex, ey - 1.0, ez],       "up": [0.0, 0.0, 1.0], "name": "-Y (Trás)"},
            {"face": "PZ_TOP",    "target": [ex, ey, ez + 1.0],       "up": [0.0, 1.0, 0.0], "name": "+Z (Topo/Céu)"},
            {"face": "NZ_BOTTOM", "target": [ex, ey, ez - 1.0],       "up": [0.0, -1.0, 0.0], "name": "-Z (Base/Solo)"},
        ]

        return {
            "entity_type": "CubemapCameraSet",
            "eye_position": [round(ex, 4), round(ey, 4), round(ez, 4)],
            "fov_deg": 90.0,
            "aspect_ratio": 1.0,
            "faces_count": 6,
            "faces": faces,
            "status": "CUBEMAP 6-FACES CONFIGURADO COM SUCESSO"
        }

    @staticmethod
    def calculate_equirectangular_grid(
        eye_position: Tuple[float, float, float],
        horizontal_samples: int = 16,
        vertical_samples: int = 8,
        sphere_radius_m: float = 10.0
    ) -> Dict[str, Any]:
        """
        Gera a malha de raios e vértices de uma esfera de projeção equirretangular 360° x 180°.
        Permite mapeamento direto de texturas equirretangulares no Three.js SphereGeometry.
        """
        ex, ey, ez = eye_position
        rays: List[Dict[str, Any]] = []

        for j in range(vertical_samples + 1):
            # Pitch de -90 a +90 graus (latitude)
            phi = -math.pi / 2.0 + (math.pi * j / vertical_samples)
            v_uv = j / vertical_samples
            for i in range(horizontal_samples + 1):
                # Yaw de 0 a 360 graus (longitude)
                theta = 2.0 * math.pi * i / horizontal_samples
                u_uv = i / horizontal_samples

                dir_x = math.cos(phi) * math.sin(theta)
                dir_y = math.cos(phi) * math.cos(theta)
                dir_z = math.sin(phi)

                world_pt = [
                    round(ex + dir_x * sphere_radius_m, 4),
                    round(ey + dir_y * sphere_radius_m, 4),
                    round(ez + dir_z * sphere_radius_m, 4),
                ]

                rays.append({
                    "yaw_deg": round(math.degrees(theta), 2),
                    "pitch_deg": round(math.degrees(phi), 2),
                    "direction": [round(dir_x, 4), round(dir_y, 4), round(dir_z, 4)],
                    "world_point": world_pt,
                    "uv": [round(u_uv, 4), round(v_uv, 4)]
                })

        return {
            "entity_type": "EquirectangularProjectionGrid",
            "eye_position": [round(ex, 4), round(ey, 4), round(ez, 4)],
            "sphere_radius_m": sphere_radius_m,
            "horizontal_fov_deg": 360.0,
            "vertical_fov_deg": 180.0,
            "total_sample_rays": len(rays),
            "rays": rays,
            "three_mapping_mode": "THREE.EquirectangularReflectionMapping",
            "status": "GRID DE PROJEÇÃO EQUIRRETANGULAR 360° CALCULADO COM SUCESSO"
        }
