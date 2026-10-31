"""
SketchBuild - Sombras Projetadas em Superfícies e Lotes Vizinhos (Zero DLL / Pure Python)
Frente 98: Engenharia Reversa do SketchUp - Projected Shadow Footprint & Solar Impact

Calcula a projeção analítica de sombras de edifícios e equipamentos sobre terrenos planos
ou fachadas vizinhas a partir do vetor de insolação (Heliodon / SUShadowInfoRef).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class ShadowCastingSurfaceEngine:
    """Motor analítico de cálculo de projeção de sombras em superfícies receptoras."""

    @staticmethod
    def project_shadow_on_plane(
        occluder_vertices: List[Tuple[float, float, float]],
        sun_direction: Tuple[float, float, float],
        ground_elevation_z: float = 0.0
    ) -> Dict[str, Any]:
        """
        Projeta os vértices de um sólido sobre o plano horizontal Z = ground_elevation_z
        ao longo dos raios solares (sun_direction).
        sun_direction aponta do sol para o modelo (vetor descendente, sz < 0).
        """
        sx, sy, sz = sun_direction
        mag = math.sqrt(sx**2 + sy**2 + sz**2)
        if mag > 1e-9:
            sx, sy, sz = sx / mag, sy / mag, sz / mag

        # Se o sol está abaixo do horizonte ou paralelo, não há sombra projetada direta
        if sz >= -1e-4:
            return {
                "entity_type": "ProjectedShadowResult",
                "sun_direction": [round(sx, 4), round(sy, 4), round(sz, 4)],
                "shadow_vertices": [],
                "shadow_area_m2": 0.0,
                "status": "SOL ABAIXO OU NO HORIZONTE (SEM SOMBRA DIRETA)"
            }

        projected_pts: List[List[float]] = []
        for vx, vy, vz in occluder_vertices:
            # P_proj = V + t * S, onde P_proj[2] = ground_elevation_z
            # vz + t * sz = z_ground -> t = (z_ground - vz) / sz
            t = (ground_elevation_z - vz) / sz
            px = vx + t * sx
            py = vy + t * sy
            pz = ground_elevation_z
            projected_pts.append([round(px, 4), round(py, 4), round(pz, 4)])

        # Cálculo da Bounding Box da sombra e estimativa de área convexa 2D
        if projected_pts:
            min_x = min(p[0] for p in projected_pts)
            max_x = max(p[0] for p in projected_pts)
            min_y = min(p[1] for p in projected_pts)
            max_y = max(p[1] for p in projected_pts)

            # Comprimento máximo da sombra em relação à base dos vértices
            base_x = sum(v[0] for v in occluder_vertices) / len(occluder_vertices)
            base_y = sum(v[1] for v in occluder_vertices) / len(occluder_vertices)
            shadow_center_x = (min_x + max_x) / 2.0
            shadow_center_y = (min_y + max_y) / 2.0
            shadow_throw_length = math.sqrt((shadow_center_x - base_x)**2 + (shadow_center_y - base_y)**2)

            # Área do envelope retangular delimitador da mancha de sombra
            shadow_bbox_area = (max_x - min_x) * (max_y - min_y)
        else:
            min_x = max_x = min_y = max_y = 0.0
            shadow_throw_length = 0.0
            shadow_bbox_area = 0.0

        return {
            "entity_type": "ProjectedShadowResult",
            "ground_elevation_z": ground_elevation_z,
            "sun_direction": [round(sx, 4), round(sy, 4), round(sz, 4)],
            "solar_zenith_angle_deg": round(math.degrees(math.acos(abs(sz))), 2),
            "projected_vertices_count": len(projected_pts),
            "projected_points": projected_pts,
            "shadow_throw_length_m": round(shadow_throw_length, 3),
            "shadow_bbox": [min_x, min_y, max_x, max_y],
            "shadow_bbox_area_m2": round(shadow_bbox_area, 3),
            "status": "SOMBRA PROJETADA EM SUPERFÍCIE CALCULADA COM SUCESSO"
        }
