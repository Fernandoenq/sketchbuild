"""
Motor de Projeção de Texturas e Coordenadas UV do SketchUp (Zero DLL).

Implementa os modos analíticos de mapeamento de textura do SketchUp:
1. Projeção Planar (Texture Projected): Projeção ortogonal contínua sobre faces adjacentes.
2. Projeção Cilíndrica: Mapeamento contínuo de veios de madeira em colunas e postes redondos.
3. Transformação UV afim (escala em centímetros, rotação e offset de textura).
4. Geração de buffers UV (Float32Array) para renderização no Three.js e injeção no .SKP.
"""

import math
from typing import List, Dict, Any, Tuple


class TextureProjectionEngine:
    """Motor analítico de cálculo e projeção de coordenadas UV."""

    @classmethod
    def project_planar_uv(
        cls,
        vertices: List[Tuple[float, float, float]],
        plane_normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        scale_u_m: float = 1.0,
        scale_v_m: float = 1.0,
        rotation_deg: float = 0.0,
        offset_uv: Tuple[float, float] = (0.0, 0.0)
    ) -> List[Tuple[float, float]]:
        """
        Calcula coordenadas (u, v) projetando ortogonalmente os vértices no plano do material.
        """
        nx, ny, nz = plane_normal
        mag = math.sqrt(nx**2 + ny**2 + nz**2) or 1.0
        nx, ny, nz = nx/mag, ny/mag, nz/mag

        # Constrói eixos ortonormais U e V coplanares ao plano de projeção
        if abs(nz) > 0.9:
            # Plano quase horizontal: U ao longo de X, V ao longo de Y
            ux, uy, uz = 1.0, 0.0, 0.0
        else:
            # U perpendicular ao eixo Z global: U = n x Z
            ux, uy, uz = ny, -nx, 0.0
            u_len = math.sqrt(ux**2 + uy**2) or 1.0
            ux, uy, uz = ux/u_len, uy/u_len, 0.0

        # V = n x U
        vx = ny * uz - nz * uy
        vy = nz * ux - nx * uz
        vz = nx * uy - ny * ux

        # Aplica rotação nos eixos U e V se houver
        if abs(rotation_deg) > 1e-4:
            rot_rad = math.radians(rotation_deg)
            cos_r = math.cos(rot_rad)
            sin_r = math.sin(rot_rad)
            u_rot_x = cos_r * ux - sin_r * vx
            u_rot_y = cos_r * uy - sin_r * vy
            u_rot_z = cos_r * uz - sin_r * vz
            v_rot_x = sin_r * ux + cos_r * vx
            v_rot_y = sin_r * uy + cos_r * vy
            v_rot_z = sin_r * uz + cos_r * vz
            ux, uy, uz = u_rot_x, u_rot_y, u_rot_z
            vx, vy, vz = v_rot_x, v_rot_y, v_rot_z

        uvs = []
        off_u, off_v = offset_uv
        for px, py, pz in vertices:
            # Projeção escalar: u = (P . U) / scale_u
            u = (px * ux + py * uy + pz * uz) / max(1e-4, scale_u_m) + off_u
            v = (px * vx + py * vy + pz * vz) / max(1e-4, scale_v_m) + off_v
            uvs.append((round(u, 4), round(v, 4)))

        return uvs

    @classmethod
    def project_cylindrical_uv(
        cls,
        vertices: List[Tuple[float, float, float]],
        cylinder_center: Tuple[float, float] = (0.0, 0.0),
        cylinder_height_m: float = 2.0,
        scale_u_repeats: float = 1.0,
        scale_v_repeats: float = 1.0
    ) -> List[Tuple[float, float]]:
        """
        Mapeia texturas cilindricamente ao redor do eixo Z (ideal para toras de madeira).
        """
        cx, cy = cylinder_center
        uvs = []

        for px, py, pz in vertices:
            dx = px - cx
            dy = py - cy
            # Ângulo azimutal de 0 a 2*pi mapeado para [0, 1]
            angle = math.atan2(dy, dx)
            if angle < 0:
                angle += 2.0 * math.pi
            u = (angle / (2.0 * math.pi)) * scale_u_repeats

            # V proporcional à cota vertical Z
            v = (pz / max(1e-4, cylinder_height_m)) * scale_v_repeats
            uvs.append((round(u, 4), round(v, 4)))

        return uvs
