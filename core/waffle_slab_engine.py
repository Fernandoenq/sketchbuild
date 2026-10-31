"""
Motor de Lajes Nervuradas Bidirecionais com Cubetas Plásticas (Waffle Slab - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 127).
Modulação paramétrica de nervuras em eixos X/Y, cubetas plásticas recuperáveis,
espessura da capa colaborante superior e dimensionamento de capitéis maciços de punção em pilares.
"""

from __future__ import annotations

import math
from typing import Any


class WaffleSlabEngine:
    """Motor analítico de dimensionamento de lajes nervuradas bidirecionais em Python puro."""

    @staticmethod
    def calculate_waffle_slab(
        span_x_m: float = 8.0,
        span_y_m: float = 8.0,
        rib_spacing_cm: float = 80.0,  # Eixo a eixo das nervuras (módulo da cubeta)
        rib_width_bw_cm: float = 12.0,  # Largura da nervura
        slab_total_height_h_cm: float = 30.0,  # Altura total da laje nervurada
        topping_thickness_hf_cm: float = 5.0,  # Capa de concreto superior (mínimo 5cm NBR 6118)
        column_dim_cm: float = 40.0,
        live_load_kpa: float = 3.0,  # Sobrecarga acidental de uso
    ) -> dict[str, Any]:
        """
        Calcula consumo equivalente de concreto, peso próprio reduzido vs laje maciça,
        dimensão do capitel maciço de punção e rigidez à flexão equivalente.
        """
        # Dimensões da cubeta plástica
        mold_width_cm = rib_spacing_cm - rib_width_bw_cm
        mold_height_cm = slab_total_height_h_cm - topping_thickness_hf_cm

        # Volume de concreto por metro quadrado:
        # 1 m2 de laje maciça de 30cm = 0.30 m3
        solid_volume_per_m2 = slab_total_height_h_cm / 100.0

        # Na nervurada: capa cheia de 5cm + nervuras em X e Y
        topping_vol_m2 = topping_thickness_hf_cm / 100.0
        # Fração de nervuras em 1 célula (80x80cm):
        cell_area_m2 = (rib_spacing_cm / 100.0) ** 2
        void_area_m2 = (mold_width_cm / 100.0) ** 2
        rib_area_m2 = cell_area_m2 - void_area_m2
        ribs_vol_per_cell = rib_area_m2 * (mold_height_cm / 100.0)
        ribs_vol_m2 = ribs_vol_per_cell / cell_area_m2

        waffle_concrete_vol_m2 = topping_vol_m2 + ribs_vol_m2
        equivalent_thickness_cm = round(waffle_concrete_vol_m2 * 100.0, 1)

        # Economia de concreto em relação à laje maciça equivalente de mesma altura
        concrete_savings_percent = round((1.0 - (waffle_concrete_vol_m2 / solid_volume_per_m2)) * 100.0, 1)

        # Peso próprio:
        gamma_c = 25.0
        self_weight_kpa = waffle_concrete_vol_m2 * gamma_c
        solid_self_weight_kpa = solid_volume_per_m2 * gamma_c

        # Dimensão mínima recomendada do capitel maciço em torno do pilar (NBR 6118 contra punção):
        # L_capitel >= c + 2 * (1.5 * d) onde d ~ h - 3cm
        d_cm = slab_total_height_h_cm - 3.0
        capitel_dim_cm = math.ceil((column_dim_cm + 2.0 * (1.5 * d_cm)) / 10.0) * 10.0

        # Número de cubetas no pano de laje
        molds_x = math.floor(span_x_m / (rib_spacing_cm / 100.0))
        molds_y = math.floor(span_y_m / (rib_spacing_cm / 100.0))
        total_molds_count = molds_x * molds_y

        # Geometria 3D representativa da laje com nervuras
        vertices = [
            [0.0, 0.0, 0.0], [span_x_m, 0.0, 0.0], [span_x_m, span_y_m, 0.0], [0.0, span_y_m, 0.0],
            [0.0, 0.0, slab_total_height_h_cm/100.0], [span_x_m, 0.0, slab_total_height_h_cm/100.0],
            [span_x_m, span_y_m, slab_total_height_h_cm/100.0], [0.0, span_y_m, slab_total_height_h_cm/100.0],
        ]
        triangles = [
            [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1], [2, 6, 7], [2, 7, 3],
        ]

        return {
            "entity_type": "WaffleSlabReport",
            "parameters": {
                "slab_dimensions_m": [span_x_m, span_y_m],
                "rib_spacing_cm": rib_spacing_cm,
                "rib_width_bw_cm": rib_width_bw_cm,
                "slab_total_height_h_cm": slab_total_height_h_cm,
                "topping_thickness_hf_cm": topping_thickness_hf_cm,
                "column_dim_cm": column_dim_cm,
            },
            "waffle_metrics": {
                "mold_dimensions_cm": [mold_width_cm, mold_width_cm, mold_height_cm],
                "total_molds_count": total_molds_count,
                "equivalent_solid_thickness_cm": equivalent_thickness_cm,
                "concrete_consumption_m3_m2": round(waffle_concrete_vol_m2, 3),
                "self_weight_kpa": round(self_weight_kpa, 2),
                "solid_slab_weight_kpa": round(solid_self_weight_kpa, 2),
                "concrete_savings_percent": concrete_savings_percent,
                "solid_shear_head_capitel_dim_cm": capitel_dim_cm,
                "status_label": f"LAJE NERVURADA: ECONOMIA DE {concrete_savings_percent}% DE CONCRETO (Capitel {int(capitel_dim_cm)}x{int(capitel_dim_cm)}cm)",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
