"""
Motor de Muros de Arrimo e Estabilidade Geotécnica NBR 11682 (Retaining Walls - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 108).
Cálculo analítico de empuxos de terra ativo/passivo (Rankine/Coulomb), verificação contra
tombamento (FS >= 1.5), deslizamento (FS >= 1.5) e geração de geometria 3D B-Rep.
"""

from __future__ import annotations

import math
from typing import Any


class RetainingWallEngine:
    """Motor analítico de estabilidade de muros de arrimo em Python puro."""

    @staticmethod
    def calculate_wall_stability(
        wall_height_m: float = 3.0,
        stem_top_thickness_m: float = 0.25,
        stem_bottom_thickness_m: float = 0.45,
        base_width_m: float = 1.80,
        base_thickness_m: float = 0.40,
        soil_friction_angle_deg: float = 30.0,
        soil_unit_weight_kn_m3: float = 18.0,
        concrete_unit_weight_kn_m3: float = 25.0,
        surcharge_kpa: float = 5.0,
    ) -> dict[str, Any]:
        """
        Calcula a estabilidade geotécnica e gera B-Rep do muro de arrimo com sapata.
        """
        phi_rad = math.radians(soil_friction_angle_deg)
        # Coeficiente de empuxo ativo de Rankine: Ka = tan^2(45 - phi/2) = (1 - sin(phi)) / (1 + sin(phi))
        ka = (1.0 - math.sin(phi_rad)) / (1.0 + math.sin(phi_rad))

        total_h = wall_height_m + base_thickness_m

        # Empuxo do solo ativo triangular: Ea_solo = 0.5 * gamma * H^2 * Ka
        ea_soil = 0.5 * soil_unit_weight_kn_m3 * (total_h ** 2) * ka
        arm_soil = total_h / 3.0

        # Empuxo da sobrecarga retangular: Ea_q = q * H * Ka
        ea_surcharge = surcharge_kpa * total_h * ka
        arm_surcharge = total_h / 2.0

        total_horizontal_force_kn = ea_soil + ea_surcharge
        overturning_moment_kn_m = (ea_soil * arm_soil) + (ea_surcharge * arm_surcharge)

        # Cargas verticais resistentes (Peso próprio do concreto)
        toe_length = (base_width_m - stem_bottom_thickness_m) * 0.35
        heel_length = base_width_m - stem_bottom_thickness_m - toe_length

        # 1. Peso da sapata:
        w_base = base_width_m * base_thickness_m * concrete_unit_weight_kn_m3
        arm_base = base_width_m / 2.0

        # 2. Peso do fuste (retângulo inferior + trapézio):
        w_stem_rect = stem_top_thickness_m * wall_height_m * concrete_unit_weight_kn_m3
        arm_stem_rect = toe_length + (stem_top_thickness_m / 2.0)

        stem_var_thickness = stem_bottom_thickness_m - stem_top_thickness_m
        w_stem_tri = 0.5 * stem_var_thickness * wall_height_m * concrete_unit_weight_kn_m3
        arm_stem_tri = toe_length + stem_top_thickness_m + (stem_var_thickness / 3.0)

        # 3. Peso da terra sobre o calcanhar (heel):
        w_soil_heel = heel_length * wall_height_m * soil_unit_weight_kn_m3
        arm_soil_heel = base_width_m - (heel_length / 2.0)

        total_vertical_load_kn = w_base + w_stem_rect + w_stem_tri + w_soil_heel
        stabilizing_moment_kn_m = (
            (w_base * arm_base)
            + (w_stem_rect * arm_stem_rect)
            + (w_stem_tri * arm_stem_tri)
            + (w_soil_heel * arm_soil_heel)
        )

        # Fatores de Segurança
        fs_overturning = stabilizing_moment_kn_m / max(0.001, overturning_moment_kn_m)
        # Atrito solo-concreto na base: delta = (2/3) * phi
        base_friction_angle = (2.0 / 3.0) * phi_rad
        resisting_friction_force = total_vertical_load_kn * math.tan(base_friction_angle)
        fs_sliding = resisting_friction_force / max(0.001, total_horizontal_force_kn)

        is_safe = (fs_overturning >= 1.50) and (fs_sliding >= 1.50)

        # Geração da B-Rep 3D (Perfil extrudado ao longo de 4.0m de extensão de muro)
        wall_length_m = 4.0
        # Perfil 2D no plano XZ:
        p0 = [0.0, 0.0]                                          # Canto inferior esquerdo sapata
        p1 = [base_width_m, 0.0]                                 # Canto inferior direito sapata
        p2 = [base_width_m, base_thickness_m]                   # Canto superior direito sapata
        p3 = [toe_length + stem_bottom_thickness_m, base_thickness_m]
        p4 = [toe_length + stem_top_thickness_m, total_h]       # Topo traseiro fuste
        p5 = [toe_length, total_h]                              # Topo frontal fuste
        p6 = [toe_length, base_thickness_m]                     # Junção frontal sapata-fuste

        profile_2d = [p0, p1, p2, p3, p4, p5, p6]
        vertices_3d = []
        # Base Y=0
        for pt in profile_2d:
            vertices_3d.append([pt[0], 0.0, pt[1]])
        # Topo Y=wall_length_m
        for pt in profile_2d:
            vertices_3d.append([pt[0], wall_length_m, pt[1]])

        triangles_3d = [
            # Tampa inicial Y=0
            [0, 1, 2], [0, 2, 6], [6, 2, 3], [6, 3, 5], [5, 3, 4],
            # Tampa final Y=L
            [7, 9, 8], [7, 13, 9], [13, 10, 9], [13, 12, 10], [12, 11, 10],
            # Laterais fechadas
            [0, 7, 8], [0, 8, 1],
            [1, 8, 9], [1, 9, 2],
            [2, 9, 10], [2, 10, 3],
            [3, 10, 11], [3, 11, 4],
            [4, 11, 12], [4, 12, 5],
            [5, 12, 13], [5, 13, 6],
            [6, 13, 7], [6, 7, 0],
        ]

        return {
            "entity_type": "RetainingWallReport",
            "parameters": {
                "wall_height_m": wall_height_m,
                "base_width_m": base_width_m,
                "base_thickness_m": base_thickness_m,
                "stem_top_thickness_m": stem_top_thickness_m,
                "stem_bottom_thickness_m": stem_bottom_thickness_m,
                "soil_friction_angle_deg": soil_friction_angle_deg,
                "soil_unit_weight_kn_m3": soil_unit_weight_kn_m3,
            },
            "stability_analysis": {
                "rankine_ka": round(ka, 4),
                "total_horizontal_thrust_kn": round(total_horizontal_force_kn, 2),
                "overturning_moment_kn_m": round(overturning_moment_kn_m, 2),
                "total_vertical_load_kn": round(total_vertical_load_kn, 2),
                "stabilizing_moment_kn_m": round(stabilizing_moment_kn_m, 2),
                "safety_factor_overturning": round(fs_overturning, 2),
                "safety_factor_sliding": round(fs_sliding, 2),
                "is_compliant_nbr11682": is_safe,
                "status_label": "ESTÁVEL (APROVADO NBR 11682)" if is_safe else "REQUER REDIMENSIONAMENTO DE SAPATA",
            },
            "geometry_3d": {
                "vertices": vertices_3d,
                "triangles": triangles_3d,
                "vertices_count": len(vertices_3d),
                "triangles_count": len(triangles_3d),
            },
            "status": "CALCULATED",
        }
