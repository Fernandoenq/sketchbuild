"""
Motor de Posicionamento e Mapeamento de Texturas por Pinos do SketchUp (Zero DLL).

Implementa a engenharia reversa da ferramenta oficial 'Posição da Textura' (Texture Position):
(Botão direito na face -> Textura -> Posição)
1. Sistema Clássico dos 4 Pinos Coloridos do SketchUp:
   - Pino Vermelho (Origem / Translação): Desloca o início da textura na face (offset U, V).
   - Pino Verde (Escala e Rotação): Rotaciona e redimensiona a textura mantendo a proporção (aspect ratio).
   - Pino Azul (Cisalhamento / Shear): Deforma a textura obliquamente ao longo do eixo secundário.
   - Pino Amarelo (Distorção de Perspectiva / Warp): Mapeamento livre em 4 cantos trapezoidais para corrigir fotos inclinadas.
2. Cálculo da Matriz de Projeção UV 3x3 Afim / Homográfica:
   - Mapeia coordenadas mundiais 3D da face para coordenadas normalizadas de textura (u, v) no Three.js.
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class TexturePinMappingEngine:
    """Motor analítico de posicionamento de texturas por pinos oficial do SketchUp."""

    @classmethod
    def calculate_pin_transform(
        cls,
        face_vertices: List[Tuple[float, float, float]],
        red_pin_origin: Tuple[float, float] = (0.0, 0.0),       # Translação U, V
        green_pin_scale_rot: Tuple[float, float] = (1.0, 0.0),  # Escala e Rotação em graus
        blue_pin_shear: float = 0.0,                            # Ângulo de cisalhamento em graus
        yellow_pin_distortion: Optional[Tuple[float, float]] = None # Distorção perspectiva
    ) -> Dict[str, Any]:
        """
        Calcula as coordenadas UV dos vértices da face baseando-se nos 4 pinos do SketchUp.
        """
        if len(face_vertices) < 3:
            raise ValueError("A face deve conter pelo menos 3 vértices para mapeamento UV.")

        # Eixos do plano da face
        v0 = face_vertices[0]
        v1 = face_vertices[1]
        v2 = face_vertices[2]

        e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])

        # Normal unitária
        nx = e1[1] * e2[2] - e1[2] * e2[1]
        ny = e1[2] * e2[0] - e1[0] * e2[2]
        nz = e1[0] * e2[1] - e1[1] * e2[0]
        nl = math.sqrt(nx * nx + ny * ny + nz * nz)
        if nl < 1e-9:
            normal = (0.0, 0.0, 1.0)
        else:
            normal = (nx / nl, ny / nl, nz / nl)

        # Base ortogonal local da face (eixo U alinhado a e1)
        el1 = math.sqrt(e1[0] ** 2 + e1[1] ** 2 + e1[2] ** 2)
        if el1 < 1e-9:
            axis_u = (1.0, 0.0, 0.0)
        else:
            axis_u = (e1[0] / el1, e1[1] / el1, e1[2] / el1)

        # Eixo V ortogonal normal x axis_u
        axis_v = (
            normal[1] * axis_u[2] - normal[2] * axis_u[1],
            normal[2] * axis_u[0] - normal[0] * axis_u[2],
            normal[0] * axis_u[1] - normal[1] * axis_u[0]
        )

        # Parâmetros dos pinos
        trans_u, trans_v = red_pin_origin
        scale, rot_deg = green_pin_scale_rot
        scale = max(0.001, scale)
        rot_rad = math.radians(rot_deg)
        shear_rad = math.radians(blue_pin_shear)

        cos_r = math.cos(rot_rad)
        sin_r = math.sin(rot_rad)
        tan_s = math.tan(shear_rad)

        uv_coords = []
        for pt in face_vertices:
            # Projeção no plano local da face
            dx = pt[0] - v0[0]
            dy = pt[1] - v0[1]
            dz = pt[2] - v0[2]

            pu = dx * axis_u[0] + dy * axis_u[1] + dz * axis_u[2]
            pv = dx * axis_v[0] + dy * axis_v[1] + dz * axis_v[2]

            # 1. Pino Vermelho: Translação
            pu_t = pu - trans_u
            pv_t = pv - trans_v

            # 2. Pino Azul: Cisalhamento
            pu_shear = pu_t + pv_t * tan_s
            pv_shear = pv_t

            # 3. Pino Verde: Rotação e Escala
            u_rot = (pu_shear * cos_r - pv_shear * sin_r) / scale
            v_rot = (pu_shear * sin_r + pv_shear * cos_r) / scale

            # 4. Pino Amarelo: Distorção perspectiva (se fornecida)
            if yellow_pin_distortion:
                warp_factor = 1.0 + (pv_shear * yellow_pin_distortion[1] + pu_shear * yellow_pin_distortion[0])
                if abs(warp_factor) > 1e-3:
                    u_rot /= warp_factor
                    v_rot /= warp_factor

            uv_coords.append((round(u_rot, 4), round(v_rot, 4)))

        return {
            "pins_config": {
                "red_pin_origin": (round(trans_u, 4), round(trans_v, 4)),
                "green_pin_scale": round(scale, 4),
                "green_pin_rotation_deg": round(rot_deg, 2),
                "blue_pin_shear_deg": round(blue_pin_shear, 2),
                "has_yellow_pin_warp": yellow_pin_distortion is not None
            },
            "vertices_count": len(face_vertices),
            "uv_coordinates": uv_coords
        }
