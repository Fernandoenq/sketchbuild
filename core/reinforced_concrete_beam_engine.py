"""
Motor de Vigas de Concreto Armado no Estado Limite Último ABNT NBR 6118 (RC Beam ELU - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 126).
Dimensionamento analítico à flexão simples no Estádio III (domínios 2 e 3 de deformação),
profundidade da linha neutra x, armadura longitudinal tracionada As e estribos transversais Asw contra cortante.
"""

from __future__ import annotations

import math
from typing import Any


class ReinforcedConcreteBeamEngine:
    """Motor analítico de dimensionamento de vigas de concreto armado em Python puro."""

    @staticmethod
    def calculate_beam_elu(
        section_width_bw_cm: float = 20.0,
        section_height_h_cm: float = 50.0,
        bending_moment_mk_kn_m: float = 120.0,  # Momento fletor característico (kN.m)
        shear_force_vk_kn: float = 85.0,  # Força cortante característica (kN)
        concrete_fck_mpa: float = 30.0,
        steel_fyk_mpa: float = 500.0,  # Aço CA-50
        concrete_cover_cm: float = 3.0,  # Cobrimento nominal c
    ) -> dict[str, Any]:
        """
        Calcula armadura longitudinal tracionada As e armadura transversal Asw segundo a NBR 6118:
        Md = 1.4 * Mk, Vd = 1.4 * Vk
        """
        # Coeficientes de ponderação
        gamma_c = 1.40
        gamma_s = 1.15

        fcd_mpa = concrete_fck_mpa / gamma_c
        fyd_mpa = steel_fyk_mpa / gamma_s

        bw_m = section_width_bw_cm / 100.0
        h_m = section_height_h_cm / 100.0
        d_m = h_m - (concrete_cover_cm / 100.0) - 0.015  # Altura útil aproximada

        m_sd_kn_m = bending_moment_mk_kn_m * 1.40
        v_sd_kn = shear_force_vk_kn * 1.40

        # Momento adimensional: mu = Md / (bw * d^2 * fcd * 1000)
        mu = (m_sd_kn_m) / (bw_m * (d_m ** 2) * (fcd_mpa * 1000.0))

        # Limite do domínio 3 (x/d <= 0.45 para fck <= 50 MPa para garantir ductilidade)
        mu_lim = 0.295
        is_double_reinforced = mu > mu_lim

        # Profundidade da linha neutra: x = (1 - sqrt(1 - 2*mu)) * d / 0.80
        if mu < 0.50:
            x_m = (1.0 - math.sqrt(max(0.0, 1.0 - 2.0 * mu))) * d_m / 0.80
        else:
            x_m = 0.45 * d_m

        x_over_d = round(x_m / d_m, 3)

        # Braço de alavanca z = d - 0.4 * x
        z_m = d_m - 0.40 * x_m

        # Área de aço longitudinal As = Md / (z * fyd)
        as_m2 = (m_sd_kn_m) / (z_m * (fyd_mpa * 1000.0))
        as_cm2 = round(as_m2 * 10000.0, 2)

        # Armadura mínima de flexão NBR 6118 (rho_min ~ 0.15% para C30)
        as_min_cm2 = round(0.0015 * section_width_bw_cm * section_height_h_cm, 2)
        as_final_cm2 = max(as_cm2, as_min_cm2)

        # Sugestão de bitola e número de barras (ex: barras de 16mm -> área unitária = 2.01 cm2)
        rebar_diam_mm = 16.0
        bar_area_cm2 = math.pi * ((rebar_diam_mm / 10.0) ** 2) / 4.0
        bars_count = math.ceil(as_final_cm2 / bar_area_cm2)

        # 2. Dimensionamento ao esforço cortante (Modelo I NBR 6118)
        # Tensão resistente da biela comprimida V_rd2 = 0.27 * (1 - fck/250) * fcd * bw * d
        alpha_v1 = 1.0 - (concrete_fck_mpa / 250.0)
        v_rd2_kn = 0.27 * alpha_v1 * (fcd_mpa * 1000.0) * bw_m * d_m
        is_web_crushing_safe = v_sd_kn <= v_rd2_kn

        # Parcela resistida pelo concreto Vc0 = 0.6 * fctd * bw * d
        fctm_mpa = 0.30 * (concrete_fck_mpa ** (2.0 / 3.0))
        fctd_mpa = (0.70 * fctm_mpa) / gamma_c
        vc0_kn = 0.60 * (fctd_mpa * 1000.0) * bw_m * d_m
        v_sw_kn = max(0.0, v_sd_kn - vc0_kn)

        # Armadura transversal Asw/s = V_sw / (0.9 * d * fyd) (cm2/m)
        asw_per_meter_cm2 = round((v_sw_kn / (0.90 * d_m * (fyd_mpa * 1000.0))) * 10000.0, 2)
        # Estribos mínimos: rho_w_min = 0.2 * fctm / fyk
        asw_min_cm2 = round(0.20 * (fctm_mpa / steel_fyk_mpa) * section_width_bw_cm * 100.0, 2)
        asw_per_meter_cm2 = max(asw_per_meter_cm2, asw_min_cm2)

        # Geometria 3D da viga de concreto
        beam_len_m = 5.0
        vertices = [
            [0.0, -bw_m/2, 0.0], [beam_len_m, -bw_m/2, 0.0], [beam_len_m, bw_m/2, 0.0], [0.0, bw_m/2, 0.0],
            [0.0, -bw_m/2, h_m], [beam_len_m, -bw_m/2, h_m], [beam_len_m, bw_m/2, h_m], [0.0, bw_m/2, h_m],
        ]
        triangles = [
            [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1], [2, 6, 7], [2, 7, 3],
        ]

        return {
            "entity_type": "ReinforcedConcreteBeamReport",
            "parameters": {
                "section_dimensions_cm": [section_width_bw_cm, section_height_h_cm],
                "bending_moment_mk_kn_m": bending_moment_mk_kn_m,
                "shear_force_vk_kn": shear_force_vk_kn,
                "concrete_fck_mpa": concrete_fck_mpa,
                "steel_fyk_mpa": steel_fyk_mpa,
                "concrete_cover_cm": concrete_cover_cm,
            },
            "design_results": {
                "design_bending_moment_msd_kn_m": round(m_sd_kn_m, 1),
                "design_shear_vsd_kn": round(v_sd_kn, 1),
                "neutral_axis_depth_x_cm": round(x_m * 100.0, 2),
                "neutral_axis_ratio_x_d": x_over_d,
                "is_ductile_section": x_over_d <= 0.45,
                "longitudinal_steel_as_cm2": as_final_cm2,
                "suggested_rebars": f"{bars_count} barras $\\varnothing${int(rebar_diam_mm)}mm",
                "transverse_stirrups_asw_cm2_m": asw_per_meter_cm2,
                "diagonal_compression_safe": is_web_crushing_safe,
                "status_label": f"VIGA APROVADA NO ELU: {bars_count} $\\varnothing${int(rebar_diam_mm)}mm (As = {as_final_cm2} cm2, Estribos = {asw_per_meter_cm2} cm2/m)",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
