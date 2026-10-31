"""
Motor de Muros de Gabião e Contenções Gravíticas Drenantes ABNT NBR 10328 (Gabion Wall - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 124).
Dimensionamento de muros em caixas de malha metálica preenchidas com pedra britada,
cálculo de estabilidade por gravidade, peso próprio, empuxo de terra Rankine e verificação de tombamento/deslizamento.
"""

from __future__ import annotations

import math
from typing import Any


class GabionRetainingWallEngine:
    """Motor analítico de cálculo de muros de gabião em Python puro."""

    @staticmethod
    def calculate_gabion(
        wall_height_m: float = 4.0,  # Altura total (m)
        tiers_count: int = 4,  # Número de fiadas de caixas (1.0m de altura cada)
        base_width_m: float = 2.5,  # Largura da base (m)
        top_width_m: float = 1.0,  # Largura do coroamento (m)
        soil_friction_angle_deg: float = 30.0,
        soil_unit_weight_kn_m3: float = 18.0,
        rock_fill_unit_weight_kn_m3: float = 19.0,  # Pedra rachão com ~30% de vazios
        batter_angle_deg: float = 6.0,  # Inclinação da face frontal para trás (deg)
        surcharge_kpa: float = 5.0,
    ) -> dict[str, Any]:
        """
        Calcula o peso próprio escalonado dos gabiões, empuxo ativo de terra Rankine,
        e os fatores de segurança contra tombamento e deslizamento de base.
        """
        phi_rad = math.radians(soil_friction_angle_deg)
        ka = math.tan(math.radians(45.0 - (soil_friction_angle_deg / 2.0))) ** 2

        # Altura de cada fiada
        tier_h = wall_height_m / max(1, tiers_count)

        # Geometria escalonada dos gabiões (da base para o topo)
        tiers_widths = []
        total_gabion_weight_kn = 0.0
        stabilizing_moment_kn_m = 0.0

        for t in range(tiers_count):
            # Interpolação linear da largura
            frac = t / max(1, tiers_count - 1)
            tw = base_width_m - frac * (base_width_m - top_width_m)
            tiers_widths.append(round(tw, 2))

            # Peso por metro linear: W = width * height * 1.0 * gamma
            tier_weight = tw * tier_h * rock_fill_unit_weight_kn_m3
            total_gabion_weight_kn += tier_weight

            # Braço de alavanca em relação à ponta frontal da base (toe)
            lever_arm = tw / 2.0
            stabilizing_moment_kn_m += tier_weight * lever_arm

        # Empuxo de terra ativo Rankine por metro linear:
        # Ea_solo = 0.5 * ka * gamma * H^2
        ea_soil_kn = 0.5 * ka * soil_unit_weight_kn_m3 * (wall_height_m ** 2)
        # Ea_sobrecarga = ka * q * H
        ea_surcharge_kn = ka * surcharge_kpa * wall_height_m
        total_thrust_kn = ea_soil_kn + ea_surcharge_kn

        # Momento de tombamento em relação à ponta da base
        overturning_moment_kn_m = (ea_soil_kn * (wall_height_m / 3.0)) + (ea_surcharge_kn * (wall_height_m / 2.0))

        # Fatores de segurança
        fs_overturning = stabilizing_moment_kn_m / max(0.01, overturning_moment_kn_m)

        # Deslizamento na base: atrito solo-gabião com delta ~ 25 graus
        delta_base_rad = math.radians(25.0)
        resisting_friction_kn = total_gabion_weight_kn * math.tan(delta_base_rad)
        fs_sliding = resisting_friction_kn / max(0.01, total_thrust_kn)

        is_stable = (fs_overturning >= 1.50) and (fs_sliding >= 1.20)

        # Geometria 3D dos blocos de gabião escalonados
        vertices = []
        triangles = []
        length_run_m = 6.0
        v_offset = 0

        for t_idx, tw in enumerate(tiers_widths):
            z_bottom = t_idx * tier_h
            z_top = z_bottom + tier_h
            base_v = [
                [0.0, 0.0, z_bottom], [tw, 0.0, z_bottom], [tw, length_run_m, z_bottom], [0.0, length_run_m, z_bottom],
                [0.0, 0.0, z_top], [tw, 0.0, z_top], [tw, length_run_m, z_top], [0.0, length_run_m, z_top],
            ]
            vertices.extend(base_v)
            tri_indices = [
                [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
                [0, 5, 1], [0, 4, 5], [1, 6, 2], [1, 5, 6],
            ]
            for tri in tri_indices:
                triangles.append([tri[0] + v_offset, tri[1] + v_offset, tri[2] + v_offset])
            v_offset += 8

        return {
            "entity_type": "GabionRetainingWallReport",
            "parameters": {
                "wall_height_m": wall_height_m,
                "tiers_count": tiers_count,
                "base_width_m": base_width_m,
                "top_width_m": top_width_m,
                "rock_fill_unit_weight_kn_m3": rock_fill_unit_weight_kn_m3,
            },
            "stability_analysis": {
                "tiers_widths_m": tiers_widths,
                "total_wall_weight_kn_m": round(total_gabion_weight_kn, 1),
                "total_horizontal_thrust_kn_m": round(total_thrust_kn, 1),
                "safety_factor_overturning": round(fs_overturning, 2),
                "safety_factor_sliding": round(fs_sliding, 2),
                "is_stable_nbr10328": is_stable,
                "free_draining": True,
                "status_label": f"MURO DE GABIÃO ESTÁVEL (FS_tomb={round(fs_overturning, 2)}, FS_desl={round(fs_sliding, 2)})" if is_stable else "REQUER ALARGAMENTO DA BASE",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
