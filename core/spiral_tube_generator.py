"""
Gerador de Tubos e Tobogãs Espirais Paramétricos 3D (Zero DLL).

Modela escorregadores e calhas helicoidais para playgrounds infantis:
1. Curva analítica espacial helicoidal com raio, passo, altura e voltas.
2. Orientação por sistema de coordenadas locais móveis (Frenet-Serret Frame).
3. Geração de anéis seccionais circulares e costura de faces poligonais B-Rep.
4. Cálculo de comprimento de descida, inclinação média e velocidade teórica.
"""

import math
from typing import List, Dict, Any, Tuple


class SpiralTubeGenerator:
    """Motor analítico de modelagem de tubos e escorregadores helicoidais."""

    @classmethod
    def generate_spiral(
        cls,
        radius_m: float = 1.20,
        height_m: float = 2.40,
        turns: float = 1.25,
        tube_radius_m: float = 0.38,
        segments_per_turn: int = 16,
        tube_segments: int = 8,
        is_open_gutter: bool = False
    ) -> Dict[str, Any]:
        """
        Gera a malha 3D de um tobogã espiral (tubo fechado ou calha aberta).
        """
        total_angle = turns * 2.0 * math.pi
        total_steps = int(turns * segments_per_turn)
        dt = total_angle / max(1, total_steps)

        # 1. Gera a espinha dorsal helicoidal e vetores tangentes
        spine_points = []
        for i in range(total_steps + 1):
            theta = i * dt
            # Decai linearmente de z = height_m até z = 0
            z = height_m * (1.0 - (theta / total_angle))
            x = radius_m * math.cos(theta)
            y = radius_m * math.sin(theta)
            spine_points.append((x, y, z))

        # 2. Gera anéis de vértices ao longo da espinha
        rings = []
        # Se for calha aberta, usa meio círculo (de -pi/2 a +pi/2 ou 0 a pi)
        phi_start = -math.pi * 0.75 if is_open_gutter else 0.0
        phi_end = math.pi * 0.75 if is_open_gutter else 2.0 * math.pi
        num_tube_pts = tube_segments + (1 if is_open_gutter else 0)

        for i in range(len(spine_points)):
            p = spine_points[i]
            theta = i * dt

            # Vetor tangente aproximado:
            # dx/dtheta = -R sin(theta), dy/dtheta = R cos(theta), dz/dtheta = -H / total_angle
            tx = -radius_m * math.sin(theta)
            ty = radius_m * math.cos(theta)
            tz = -height_m / total_angle
            t_len = math.sqrt(tx**2 + ty**2 + tz**2)
            tx, ty, tz = tx / t_len, ty / t_len, tz / t_len

            # Vetor normal principal (aponta para o eixo central):
            nx, ny, nz = -math.cos(theta), -math.sin(theta), 0.0

            # Vetor binormal b = t x n:
            bx = ty * nz - tz * ny
            by = tz * nx - tx * nz
            bz = tx * ny - ty * nx
            b_len = math.sqrt(bx**2 + by**2 + bz**2)
            bx, by, bz = bx / b_len, by / b_len, bz / b_len

            ring_pts = []
            for j in range(num_tube_pts):
                fraction = j / max(1, tube_segments)
                phi = phi_start + fraction * (phi_end - phi_start)

                # Deslocamento no plano perpendicular à tangente
                cos_p = math.cos(phi)
                sin_p = math.sin(phi)

                vx = p[0] + tube_radius_m * (cos_p * nx + sin_p * bx)
                vy = p[1] + tube_radius_m * (cos_p * ny + sin_p * by)
                vz = p[2] + tube_radius_m * (cos_p * nz + sin_p * bz)
                ring_pts.append((round(vx, 4), round(vy, 4), round(vz, 4)))

            rings.append(ring_pts)

        # 3. Malha de vértices e faces conectando os anéis
        vertices = []
        faces = []
        vert_map = {}

        def get_vert_idx(pt):
            if pt not in vert_map:
                vert_map[pt] = len(vertices)
                vertices.append([pt[0], pt[1], pt[2]])
            return vert_map[pt]

        for i in range(len(rings) - 1):
            r1 = rings[i]
            r2 = rings[i + 1]
            n_pts = len(r1)
            limit = n_pts - 1 if is_open_gutter else n_pts

            for j in range(limit):
                j_next = (j + 1) % n_pts
                idx1 = get_vert_idx(r1[j])
                idx2 = get_vert_idx(r1[j_next])
                idx3 = get_vert_idx(r2[j_next])
                idx4 = get_vert_idx(r2[j])

                # Cria face quadrilátera
                faces.append([idx1, idx2, idx3, idx4])

        # Métricas analíticas do tobogã
        path_length_m = 0.0
        for i in range(len(spine_points) - 1):
            p1, p2 = spine_points[i], spine_points[i + 1]
            dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)
            path_length_m += dist

        avg_slope_deg = math.degrees(math.atan2(height_m, turns * 2.0 * math.pi * radius_m))
        # Velocidade teórica com atrito cinético de PEAD (mu ~ 0.20)
        # v ~ sqrt(2 * g * H * (1 - mu / tan(alpha)))
        g = 9.80665
        mu = 0.20
        rad_slope = math.radians(avg_slope_deg)
        eff = max(0.2, 1.0 - mu / math.tan(rad_slope))
        estimated_exit_speed_m_s = math.sqrt(2.0 * g * height_m * eff)

        return {
            "entity_type": "SpiralTubeGeometry",
            "radius_m": radius_m,
            "height_m": height_m,
            "turns": turns,
            "tube_radius_m": tube_radius_m,
            "is_open_gutter": is_open_gutter,
            "path_length_m": round(path_length_m, 2),
            "average_slope_deg": round(avg_slope_deg, 1),
            "estimated_exit_speed_m_s": round(estimated_exit_speed_m_s, 2),
            "vertices_count": len(vertices),
            "faces_count": len(faces),
            "vertices": vertices,
            "faces": faces,
            "status": "GEOMETRIA HELICOIDAL GERADA COM SUCESSO"
        }
