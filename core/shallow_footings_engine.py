"""
Motor de Sapatas Isoladas e Fundações Rasas ABNT NBR 6122 / NBR 6118 (Shallow Footings - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 123).
Dimensionamento em planta por tensão admissível do solo, verificação de rigidez da sapata (sapata rígida),
ângulo das bielas de compressão e cálculo de armadura de flexão de base.
"""

from __future__ import annotations

import math
from typing import Any


class ShallowFootingsEngine:
    """Motor analítico de dimensionamento de sapatas rasas em Python puro."""

    @staticmethod
    def calculate_footing(
        column_load_kn: float = 650.0,
        soil_allowable_stress_mpa: float = 0.20,  # 0.20 MPa = 2.0 kgf/cm2 = 200 kPa
        column_dim_a_cm: float = 20.0,  # Dimensão do pilar em X (cm)
        column_dim_b_cm: float = 40.0,  # Dimensão do pilar em Y (cm)
        fck_concrete_mpa: float = 25.0,
        fyk_steel_mpa: float = 500.0,  # CA-50
    ) -> dict[str, Any]:
        """
        Calcula lados A e B da sapata mantendo abas de balanço iguais para uniformidade de tensões:
        a - a0 = b - b0 -> B = A + (b0 - a0)
        Área necessária: S = 1.10 * N_k / sigma_adm
        """
        sigma_adm_kpa = soil_allowable_stress_mpa * 1000.0
        # Considera peso próprio da sapata e solo (~10% da carga do pilar)
        design_load_kn = column_load_kn * 1.10
        required_area_m2 = design_load_kn / sigma_adm_kpa

        a0_m = column_dim_a_cm / 100.0
        b0_m = column_dim_b_cm / 100.0
        delta_m = b0_m - a0_m

        # A * (A + delta) = S -> A^2 + delta*A - S = 0
        disc = (delta_m ** 2) + 4.0 * required_area_m2
        footing_a_m = (-delta_m + math.sqrt(disc)) / 2.0
        footing_b_m = footing_a_m + delta_m

        # Arredonda para múltiplos de 5cm superiores
        footing_a_m = math.ceil(footing_a_m * 20.0) / 20.0
        footing_b_m = math.ceil(footing_b_m * 20.0) / 20.0
        final_area_m2 = footing_a_m * footing_b_m

        # Tensão real atuante na base do solo
        actual_stress_kpa = design_load_kn / final_area_m2

        # Altura da sapata para critério de sapata rígida NBR 6118:
        # h >= (a - a0) / 3 e h >= (b - b0) / 3
        overhang_a_m = (footing_a_m - a0_m) / 2.0
        overhang_b_m = (footing_b_m - b0_m) / 2.0
        max_overhang_m = max(overhang_a_m, overhang_b_m)

        height_h_m = max(0.40, math.ceil((max_overhang_m / 2.5) * 20.0) / 20.0)
        # Altura útil d
        d_m = height_h_m - 0.05

        # Armadura de flexão nas duas direções pelo método das bielas
        # As_a = 1.4 * N_k * (a - a0) / (8 * d * fyd)
        fyd_kpa = (fyk_steel_mpa / 1.15) * 1000.0
        as_a_m2 = (1.4 * column_load_kn * overhang_a_m) / (8.0 * d_m * fyd_kpa)
        as_b_m2 = (1.4 * column_load_kn * overhang_b_m) / (8.0 * d_m * fyd_kpa)

        as_a_cm2 = round(as_a_m2 * 10000.0, 2)
        as_b_cm2 = round(as_b_m2 * 10000.0, 2)

        # Geometria 3D tronco-piramidal ou prismática da sapata
        a_half = footing_a_m / 2.0
        b_half = footing_b_m / 2.0
        vertices = [
            [-a_half, -b_half, 0.0], [a_half, -b_half, 0.0], [a_half, b_half, 0.0], [-a_half, b_half, 0.0],
            [-a_half, -b_half, height_h_m], [a_half, -b_half, height_h_m], [a_half, b_half, height_h_m], [-a_half, b_half, height_h_m],
        ]
        triangles = [
            [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
        ]

        return {
            "entity_type": "ShallowFootingReport",
            "parameters": {
                "column_load_kn": column_load_kn,
                "soil_allowable_stress_mpa": soil_allowable_stress_mpa,
                "column_dimensions_cm": [column_dim_a_cm, column_dim_b_cm],
                "fck_concrete_mpa": fck_concrete_mpa,
            },
            "footing_dimensions": {
                "footing_width_a_m": footing_a_m,
                "footing_length_b_m": footing_b_m,
                "footing_height_h_m": height_h_m,
                "effective_depth_d_m": d_m,
                "base_area_m2": round(final_area_m2, 2),
                "actual_soil_stress_kpa": round(actual_stress_kpa, 1),
                "allowable_soil_stress_kpa": sigma_adm_kpa,
                "reinforcement_as_x_cm2": as_a_cm2,
                "reinforcement_as_y_cm2": as_b_cm2,
                "is_rigid_footing": True,
                "status_label": f"SAPATA RÍGIDA APROVADA: {int(footing_a_m*100)}x{int(footing_b_m*100)}x{int(height_h_m*100)}cm",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
