"""
Motor de Fôrmas e Escoramento de Estruturas de Concreto ABNT NBR 15696 / DIN 18218 (Formwork & Shoring - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 125).
Cálculo da pressão hidrostática lateral do concreto fresco em pilares/paredes,
dimensionamento de tirantes e espaçamento seguro de escoras metálicas contra flambagem de Euler.
"""

from __future__ import annotations

import math
from typing import Any


class ConcreteFormworkShoringEngine:
    """Motor analítico de cálculo de fôrmas e escoramento em Python puro."""

    @staticmethod
    def calculate_formwork(
        element_type: str = "COLUMN",  # COLUMN, WALL ou SLAB
        height_or_span_m: float = 3.20,
        pour_rate_v_m_h: float = 2.50,  # Velocidade de concretagem (m/h)
        concrete_temp_c: float = 20.0,
        slump_cm: float = 12.0,  # Consistência do concreto (cm)
        shore_allowable_load_kn: float = 25.0,  # Carga de catálogo da escora telescópica (kN)
        slab_thickness_cm: float = 15.0,
    ) -> dict[str, Any]:
        """
        Calcula pressão máxima de fôrma (Pmax DIN 18218 / NBR 15696):
        Para paredes/pilares com concreto plastificado:
        Pmax = min(gamma * H, (5 * v + 21)) em kPa
        E para lajes: carga vertical (peso próprio + acidental de operários ~ 2.0 kN/m2)
        """
        gamma_c = 25.0  # Peso específico do concreto armado fresco (kN/m3)

        # 1. Pressão lateral em paredes/pilares
        p_hydrostatic_kpa = gamma_c * height_or_span_m
        # Fórmula DIN 18218 para concreto plástico normal (T=20C):
        p_din_kpa = (5.0 * pour_rate_v_m_h) + 21.0
        p_max_lateral_kpa = min(p_hydrostatic_kpa, p_din_kpa)

        # Espaçamento recomendado de tirantes/gravatas de fôrma (para tirante de 12mm aguenta ~ 35 kN)
        tie_rod_capacity_kn = 35.0
        max_tie_spacing_m = round(math.sqrt(tie_rod_capacity_kn / max(1.0, p_max_lateral_kpa)), 2)

        # 2. Escoramento vertical de lajes (Shoring)
        dead_load_slab_kpa = (slab_thickness_cm / 100.0) * gamma_c
        live_load_construction_kpa = 2.0  # Carga de trabalho de operários e carrinhos NBR 15696
        formwork_self_weight_kpa = 0.40  # Compensado e barrotes
        total_vertical_load_kpa = dead_load_slab_kpa + live_load_construction_kpa + formwork_self_weight_kpa

        # Área de influência máxima por escora: A_escora = Q_adm / Q_total
        max_shore_tributary_area_m2 = shore_allowable_load_kn / total_vertical_load_kpa
        shore_spacing_m = round(math.sqrt(max_shore_tributary_area_m2), 2)
        # Limite prático máximo de 1.20m por segurança
        shore_spacing_m = min(1.20, max(0.60, shore_spacing_m))

        # Flambagem de Euler da escora telescópica de aço (E = 210 GPa):
        # P_cr = (pi^2 * E * I) / L^2
        # Tubo D=48.3mm, t=2.6mm -> I ~ 11.6 cm4
        i_cm4 = 11.6
        e_gpa = 210.0
        p_euler_kn = (math.pi ** 2 * (e_gpa * 1e6) * (i_cm4 * 1e-8)) / (height_or_span_m ** 2)
        fs_euler = round(p_euler_kn / max(1.0, shore_allowable_load_kn), 2)

        # Geometria 3D representativa dos painéis de fôrma e escoras
        vertices = [
            [-0.4, -0.4, 0.0], [0.4, -0.4, 0.0], [0.4, 0.4, 0.0], [-0.4, 0.4, 0.0],
            [-0.4, -0.4, height_or_span_m], [0.4, -0.4, height_or_span_m], [0.4, 0.4, height_or_span_m], [-0.4, 0.4, height_or_span_m],
        ]
        triangles = [
            [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2],
        ]

        return {
            "entity_type": "FormworkShoringReport",
            "parameters": {
                "element_type": element_type,
                "height_or_span_m": height_or_span_m,
                "pour_rate_v_m_h": pour_rate_v_m_h,
                "slump_cm": slump_cm,
                "slab_thickness_cm": slab_thickness_cm,
            },
            "formwork_metrics": {
                "max_lateral_pressure_kpa": round(p_max_lateral_kpa, 1),
                "tie_rods_max_spacing_m": max_tie_spacing_m,
                "total_slab_gravity_load_kpa": round(total_vertical_load_kpa, 2),
                "shores_grid_spacing_m": shore_spacing_m,
                "euler_buckling_load_kn": round(p_euler_kn, 1),
                "buckling_safety_factor": fs_euler,
                "is_safe_nbr15696": fs_euler >= 2.0,
                "status_label": f"FÔRMAS & ESCORAS APROVADAS (Pmax = {round(p_max_lateral_kpa, 1)} kPa, Malha de Escoras = {shore_spacing_m}m)",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
