"""
Motor de Perfis Estruturais Metálicos Paramétricos NBR 8800 (Structural Steel Profiles - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 114).
Biblioteca paramétrica procedural de perfis laminados/soldados (Viga I/W, Perfil U, Cantoneira L,
Tubo Retangular/Circular), cálculo de propriedades de seção (A, Ix, Iy, Wx, Wy, Zx) e malha 3D B-Rep.
"""

from __future__ import annotations

import math
from typing import Any


class SteelProfileEngine:
    """Motor analítico de seções metálicas estruturais em Python puro."""

    @staticmethod
    def generate_i_beam(
        depth_d_mm: float = 200.0,       # Altura total d
        flange_width_bf_mm: float = 100.0, # Largura da mesa bf
        web_thickness_tw_mm: float = 6.0,  # Espessura da alma tw
        flange_thickness_tf_mm: float = 9.0,# Espessura da mesa tf
        length_m: float = 3.0,            # Comprimento da barra
        steel_density_kg_m3: float = 7850.0, # Densidade do aço estrutural ASTM A36 / A572
    ) -> dict[str, Any]:
        """
        Gera uma Viga I / W, calcula propriedades de seção NBR 8800 e emite malha 3D.
        """
        d = depth_d_mm / 1000.0
        bf = flange_width_bf_mm / 1000.0
        tw = web_thickness_tw_mm / 1000.0
        tf = flange_thickness_tf_mm / 1000.0

        hw = d - 2.0 * tf  # Altura líquida da alma

        # 1. Área da Seção Transversal (A)
        area_flanges = 2.0 * (bf * tf)
        area_web = hw * tw
        total_area_m2 = area_flanges + area_web
        total_area_cm2 = total_area_m2 * 10000.0

        # Massa linear (kg/m)
        linear_mass_kg_m = total_area_m2 * steel_density_kg_m3
        total_mass_kg = linear_mass_kg_m * length_m

        # 2. Momento de Inércia Eixo Maior (Ix - horizontal)
        # Teorema dos Eixos Paralelos (Steiner):
        ix_web = (tw * (hw ** 3)) / 12.0
        d_flange = (hw / 2.0) + (tf / 2.0)
        ix_flanges = 2.0 * (((bf * (tf ** 3)) / 12.0) + (bf * tf * (d_flange ** 2)))
        ix_m4 = ix_web + ix_flanges
        ix_cm4 = ix_m4 * 1.0e8

        # 3. Momento de Inércia Eixo Menor (Iy - vertical)
        iy_web = (hw * (tw ** 3)) / 12.0
        iy_flanges = 2.0 * ((tf * (bf ** 3)) / 12.0)
        iy_m4 = iy_web + iy_flanges
        iy_cm4 = iy_m4 * 1.0e8

        # 4. Módulo de Resistência Elástico (Wx, Wy)
        wx_cm3 = (ix_cm4 / (d * 100.0 / 2.0))
        wy_cm3 = (iy_cm4 / (bf * 100.0 / 2.0))

        # 5. Módulo Plástico Aproximado (Zx)
        zx_cm3 = (bf * tf * (d - tf) + (tw * (hw ** 2)) / 4.0) * 1.0e6

        # 6. Raio de Giração (rx, ry)
        rx_cm = math.sqrt(ix_cm4 / total_area_cm2)
        ry_cm = math.sqrt(iy_cm4 / total_area_cm2)

        # Geração da geometria 3D (Polígono em I com 12 vértices extrudado ao longo do eixo Y)
        # Metades para simetria:
        half_bf = bf / 2.0
        half_tw = tw / 2.0
        half_d = d / 2.0
        y_inner = half_d - tf

        # 12 vértices do perfil I no plano XZ:
        profile_xz = [
            [-half_bf, -half_d],
            [half_bf, -half_d],
            [half_bf, -y_inner],
            [half_tw, -y_inner],
            [half_tw, y_inner],
            [half_bf, y_inner],
            [half_bf, half_d],
            [-half_bf, half_d],
            [-half_bf, y_inner],
            [-half_tw, y_inner],
            [-half_tw, -y_inner],
            [-half_bf, -y_inner],
        ]

        vertices_3d = []
        # Extremidade Y = 0
        for pt in profile_xz:
            vertices_3d.append([round(pt[0], 5), 0.0, round(pt[1], 5)])
        # Extremidade Y = length_m
        for pt in profile_xz:
            vertices_3d.append([round(pt[0], 5), round(length_m, 4), round(pt[1], 5)])

        # Faces laterais fechadas
        triangles_3d = []
        for i in range(12):
            next_i = (i + 1) % 12
            p1 = i
            p2 = next_i
            p3 = next_i + 12
            p4 = i + 12
            triangles_3d.append([p1, p2, p3])
            triangles_3d.append([p1, p3, p4])

        return {
            "entity_type": "SteelProfileReport",
            "profile_type": "I_BEAM_W",
            "nominal_designation": f"W {depth_d_mm:.0f}x{linear_mass_kg_m:.1f}",
            "dimensions_mm": {
                "depth_d": depth_d_mm,
                "flange_width_bf": flange_width_bf_mm,
                "web_thickness_tw": web_thickness_tw_mm,
                "flange_thickness_tf": flange_thickness_tf_mm,
                "length_m": length_m,
            },
            "section_properties": {
                "area_cm2": round(total_area_cm2, 2),
                "linear_mass_kg_m": round(linear_mass_kg_m, 2),
                "total_mass_kg": round(total_mass_kg, 2),
                "ix_cm4": round(ix_cm4, 1),
                "iy_cm4": round(iy_cm4, 1),
                "wx_cm3": round(wx_cm3, 1),
                "wy_cm3": round(wy_cm3, 1),
                "zx_cm3": round(zx_cm3, 1),
                "rx_cm": round(rx_cm, 2),
                "ry_cm": round(ry_cm, 2),
            },
            "geometry_3d": {
                "vertices": vertices_3d,
                "triangles": triangles_3d,
                "vertices_count": len(vertices_3d),
                "triangles_count": len(triangles_3d),
            },
            "status": "GENERATED",
        }
