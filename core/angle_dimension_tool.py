"""
Ferramenta de Cota Angular e Medição de Transferidor 3D (Angle Dimension - Zero DLL).

Calcula cotas angulares e arcos gráficos de dimensionamento no espaço:
1. Ângulo diedro e plano entre 3 pontos (vértice central e dois eixos).
2. Determinação analítica do plano da cota via produto vetorial (u x v).
3. Discretização de arcos circulares de cota com setas e raio configurável.
4. Formatação de texto angular (° e rad) e posição ótima do rótulo no espaço.
"""

import math
from typing import List, Dict, Any, Tuple


class AngleDimensionTool:
    """Motor analítico de cotação angular e transferidor 3D."""

    @classmethod
    def calculate_angle_dimension(
        cls,
        vertex_point: Tuple[float, float, float],
        point_a: Tuple[float, float, float],
        point_b: Tuple[float, float, float],
        arc_radius_m: float = 0.60,
        arc_segments: int = 16
    ) -> Dict[str, Any]:
        """
        Calcula o ângulo entre vetores (vertex -> A) e (vertex -> B) e gera o arco de cota.
        """
        vx, vy, vz = vertex_point
        ax, ay, az = point_a
        bx, by, bz = point_b

        # Vetores u e v
        ux, uy, uz = ax - vx, ay - vy, az - vz
        wx, wy, wz = bx - vx, by - vy, bz - vz

        u_len = math.sqrt(ux**2 + uy**2 + uz**2)
        w_len = math.sqrt(wx**2 + wy**2 + wz**2)

        if u_len < 1e-9 or w_len < 1e-9:
            raise ValueError("Os pontos de extremidade devem ser distintos do vértice.")

        # Normaliza u e w
        ux, uy, uz = ux / u_len, uy / u_len, uz / u_len
        wx, wy, wz = wx / w_len, wy / w_len, wz / w_len

        # Produto escalar (cos theta)
        dot = max(-1.0, min(1.0, ux * wx + uy * wy + uz * wz))
        angle_rad = math.acos(dot)
        angle_deg = math.degrees(angle_rad)

        # Vetor normal ao plano do arco: n = u x w
        nx = uy * wz - uz * wy
        ny = uz * wx - ux * wz
        nz = ux * wy - uy * wx
        n_len = math.sqrt(nx**2 + ny**2 + nz**2)

        if n_len < 1e-9:
            # Vetores colineares (0 ou 180 graus), escolhe normal arbitrária
            nx, ny, nz = 0.0, 0.0, 1.0
        else:
            nx, ny, nz = nx / n_len, ny / n_len, nz / n_len

        # Vetor ortogonal a u no mesmo plano (u_perp = n x u)
        px = ny * uz - nz * uy
        py = nz * ux - nx * uz
        pz = nx * uy - ny * ux

        # Geração de pontos discretizados ao longo do arco de cota
        arc_points = []
        for i in range(arc_segments + 1):
            t = (i / max(1, arc_segments)) * angle_rad
            # Posicao = vertex + R * (cos(t) * u + sin(t) * u_perp)
            cos_t = math.cos(t)
            sin_t = math.sin(t)
            pt_x = vx + arc_radius_m * (cos_t * ux + sin_t * px)
            pt_y = vy + arc_radius_m * (cos_t * uy + sin_t * py)
            pt_z = vz + arc_radius_m * (cos_t * uz + sin_t * pz)
            arc_points.append([round(pt_x, 4), round(pt_y, 4), round(pt_z, 4)])

        # Posição central do rótulo de texto (na metade do arco + 10% de folga no raio)
        half_angle = angle_rad * 0.5
        label_r = arc_radius_m * 1.15
        label_x = vx + label_r * (math.cos(half_angle) * ux + math.sin(half_angle) * px)
        label_y = vy + label_r * (math.cos(half_angle) * uy + math.sin(half_angle) * py)
        label_z = vz + label_r * (math.cos(half_angle) * uz + math.sin(half_angle) * pz)

        # Formatação graus, minutos e segundos (GMS)
        d = int(angle_deg)
        m = int((angle_deg - d) * 60)
        s = int(((angle_deg - d) * 60 - m) * 60)
        gms_str = f"{d}° {m:02d}' {s:02d}\""

        return {
            "entity_type": "AngleDimension",
            "vertex_point": list(vertex_point),
            "point_a": list(point_a),
            "point_b": list(point_b),
            "angle_degrees": round(angle_deg, 2),
            "angle_radians": round(angle_rad, 4),
            "angle_gms": gms_str,
            "arc_radius_m": arc_radius_m,
            "plane_normal": [round(nx, 4), round(ny, 4), round(nz, 4)],
            "label_position": [round(label_x, 4), round(label_y, 4), round(label_z, 4)],
            "text_label": f"{angle_deg:.1f}°",
            "arc_points_count": len(arc_points),
            "arc_points": arc_points
        }
