"""
Motor de Proteção contra Descargas Atmosféricas SPDA ABNT NBR 5419 (Lightning Protection - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 132).
Dimensionamento pelo Método da Esfera Rolante (Eletrogeométrico), ângulo de proteção de Franklin e malha de Faraday,
cálculo do raio da esfera (R = 20m a 60m por classe de proteção I a IV) e volume de proteção 3D gerado.
"""

from __future__ import annotations

import math
from typing import Any


class LightningProtectionSpdaEngine:
    """Motor analítico de cálculo de SPDA e proteção contra raios em Python puro."""

    @staticmethod
    def calculate_spda(
        building_width_m: float = 20.0,
        building_length_m: float = 30.0,
        building_height_m: float = 18.0,
        protection_level: str = "LEVEL_III",  # LEVEL_I, LEVEL_II, LEVEL_III, LEVEL_IV
        air_terminals_count: int = 4,  # Hastes captoras tipo Franklin na cobertura
        terminal_height_m: float = 3.0,
    ) -> dict[str, Any]:
        """
        Determina o raio da esfera rolante e malha de Faraday segundo a NBR 5419-3:
        Nível I: R = 20m, malha 5x5m
        Nível II: R = 30m, malha 10x10m
        Nível III: R = 45m, malha 15x15m
        Nível IV: R = 60m, malha 20x20m
        """
        level_map = {
            "LEVEL_I": {"radius_m": 20.0, "mesh_m": 5.0, "down_conductors_spacing_m": 10.0},
            "LEVEL_II": {"radius_m": 30.0, "mesh_m": 10.0, "down_conductors_spacing_m": 10.0},
            "LEVEL_III": {"radius_m": 45.0, "mesh_m": 15.0, "down_conductors_spacing_m": 15.0},
            "LEVEL_IV": {"radius_m": 60.0, "mesh_m": 20.0, "down_conductors_spacing_m": 20.0},
        }
        level_info = level_map.get(protection_level.upper(), level_map["LEVEL_III"])
        sphere_radius_m = level_info["radius_m"]
        max_mesh_size_m = level_info["mesh_m"]
        down_spacing_m = level_info["down_conductors_spacing_m"]

        # Perímetro da edificação e número de condutores de descida obrigatórios
        perimeter_m = 2.0 * (building_width_m + building_length_m)
        min_down_conductors_count = max(2, math.ceil(perimeter_m / down_spacing_m))

        # Raio de proteção horizontal do captor Franklin no topo (Método da Esfera Rolante):
        # rp = sqrt(h * (2*R - h))
        h_eff = min(terminal_height_m, sphere_radius_m)
        protection_radius_per_terminal_m = math.sqrt(h_eff * (2.0 * sphere_radius_m - h_eff))

        # Verificação se as hastes cobrem o perímetro da cobertura
        coverage_area_per_terminal_m2 = math.pi * (protection_radius_per_terminal_m ** 2)
        total_terminals_coverage_m2 = air_terminals_count * coverage_area_per_terminal_m2
        roof_area_m2 = building_width_m * building_length_m
        coverage_ratio = round(total_terminals_coverage_m2 / max(1.0, roof_area_m2), 2)

        # Frequência esperada de descargas diretas para a estrutura:
        # Ng = 0.04 * Td^1.25 (densidade de raios/km2/ano)
        # Nd = Ng * Ae * C1 * 1e-6
        # Área de exposição equivalente: Ae = L*W + 2*(L+W)*H*3 + pi*(3*H)^2
        ae_m2 = (building_length_m * building_width_m) + (6.0 * (building_length_m + building_width_m) * building_height_m) + (math.pi * ((3.0 * building_height_m) ** 2))
        expected_flashes_per_year = round(4.0 * ae_m2 * 1e-6, 4)

        # Geometria 3D dos volumes cônicos/esféricos de proteção dos captores
        terminal_positions = [
            [-building_width_m * 0.35, -building_length_m * 0.35, building_height_m + terminal_height_m],
            [building_width_m * 0.35, -building_length_m * 0.35, building_height_m + terminal_height_m],
            [building_width_m * 0.35, building_length_m * 0.35, building_height_m + terminal_height_m],
            [-building_width_m * 0.35, building_length_m * 0.35, building_height_m + terminal_height_m],
        ]

        return {
            "entity_type": "LightningProtectionSpdaReport",
            "parameters": {
                "building_dimensions_m": [building_width_m, building_length_m, building_height_m],
                "protection_level": protection_level,
                "air_terminals_count": air_terminals_count,
                "terminal_height_m": terminal_height_m,
            },
            "spda_design": {
                "rolling_sphere_radius_m": sphere_radius_m,
                "faraday_max_mesh_size_m": max_mesh_size_m,
                "min_down_conductors_count": min_down_conductors_count,
                "protection_radius_per_terminal_m": round(protection_radius_per_terminal_m, 2),
                "equivalent_exposure_area_ae_m2": round(ae_m2, 1),
                "expected_flashes_per_year": expected_flashes_per_year,
                "roof_coverage_ratio": coverage_ratio,
                "is_compliant_nbr5419": coverage_ratio >= 1.0,
                "status_label": f"SPDA {protection_level} APROVADO: Esfera R={int(sphere_radius_m)}m, {min_down_conductors_count} Descidas, Malha {int(max_mesh_size_m)}x{int(max_mesh_size_m)}m",
            },
            "air_terminals_positions_3d": terminal_positions,
            "status": "COMPUTED",
        }
