"""
Motor de Estruturas Espaciais e Treliças Tubulares 3D (Space Truss - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 130).
Geração paramétrica de malhas espaciais tridimensionais (sistema de nós esféricos tipo Mero e barras tubulares),
topologia de módulos piramidais em duas camadas (corda superior e inferior) e dimensionamento à tração e compressão axial.
"""

from __future__ import annotations

import math
from typing import Any


class SpaceTrussEngine:
    """Motor analítico de cálculo de treliças espaciais tridimensionais em Python puro."""

    @staticmethod
    def generate_space_truss(
        span_x_m: float = 12.0,
        span_y_m: float = 12.0,
        module_size_m: float = 2.0,  # Passo da malha em X e Y
        truss_depth_m: float = 1.20,  # Altura estrutural entre planos de cordas
        uniform_load_kn_m2: float = 1.20,  # Carga de cobertura + vento
        tube_outer_diam_mm: float = 76.2,  # Tubo de aço 3"
        tube_wall_thickness_mm: float = 3.6,
        steel_fy_mpa: float = 250.0,
    ) -> dict[str, Any]:
        """
        Gera os nós superiores, inferiores e barras (corda superior, corda inferior e diagonais),
        calculando o esforço axial máximo e taxa de trabalho.
        """
        nx = int(span_x_m / module_size_m)
        ny = int(span_y_m / module_size_m)

        # 1. Geração de nós (Nodes)
        top_nodes = []
        node_id = 0
        node_map = {}

        for ix in range(nx + 1):
            for iy in range(ny + 1):
                x = ix * module_size_m
                y = iy * module_size_m
                z = truss_depth_m
                top_nodes.append({"id": node_id, "pos": [round(x, 2), round(y, 2), round(z, 2)], "layer": "TOP"})
                node_map[(ix, iy, "T")] = node_id
                node_id += 1

        # Corda inferior deslocada em meio módulo (pirâmides invertidas padrão Mero)
        bottom_nodes = []
        for ix in range(nx):
            for iy in range(ny):
                x = (ix + 0.5) * module_size_m
                y = (iy + 0.5) * module_size_m
                z = 0.0
                bottom_nodes.append({"id": node_id, "pos": [round(x, 2), round(y, 2), round(z, 2)], "layer": "BOTTOM"})
                node_map[(ix, iy, "B")] = node_id
                node_id += 1

        all_nodes = top_nodes + bottom_nodes

        # 2. Geração de barras (Members)
        members = []
        member_id = 0

        # Barras da corda superior
        for ix in range(nx):
            for iy in range(ny + 1):
                members.append({"id": member_id, "from": node_map[(ix, iy, "T")], "to": node_map[(ix + 1, iy, "T")], "type": "TOP_CHORD"})
                member_id += 1
        for ix in range(nx + 1):
            for iy in range(ny):
                members.append({"id": member_id, "from": node_map[(ix, iy, "T")], "to": node_map[(ix, iy + 1, "T")], "type": "TOP_CHORD"})
                member_id += 1

        # Barras da corda inferior
        for ix in range(nx - 1):
            for iy in range(ny):
                members.append({"id": member_id, "from": node_map[(ix, iy, "B")], "to": node_map[(ix + 1, iy, "B")], "type": "BOTTOM_CHORD"})
                member_id += 1
        for ix in range(nx):
            for iy in range(ny - 1):
                members.append({"id": member_id, "from": node_map[(ix, iy, "B")], "to": node_map[(ix, iy + 1, "B")], "type": "BOTTOM_CHORD"})
                member_id += 1

        # Diagonais espaciais ligando nós inferiores aos 4 nós superiores adjacentes
        for ix in range(nx):
            for iy in range(ny):
                b_idx = node_map[(ix, iy, "B")]
                t_corners = [
                    node_map[(ix, iy, "T")],
                    node_map[(ix + 1, iy, "T")],
                    node_map[(ix + 1, iy + 1, "T")],
                    node_map[(ix, iy + 1, "T")],
                ]
                for tc in t_corners:
                    members.append({"id": member_id, "from": b_idx, "to": tc, "type": "DIAGONAL"})
                    member_id += 1

        # Propriedades do tubo de aço:
        d_ext = tube_outer_diam_mm
        t = tube_wall_thickness_mm
        d_int = d_ext - 2.0 * t
        area_tube_mm2 = (math.pi / 4.0) * ((d_ext ** 2) - (d_int ** 2))
        radius_gyration_r_mm = math.sqrt(((d_ext ** 2) + (d_int ** 2)) / 16.0)

        # Esforço axial estimado por placa ortotrópica equivalente:
        total_roof_load_kn = span_x_m * span_y_m * uniform_load_kn_m2
        max_moment_kn_m = (uniform_load_kn_m2 * (span_x_m ** 2)) / 8.0
        # Força axial de corda no meio do vão ~ M / d
        max_chord_force_kn = round(max_moment_kn_m / truss_depth_m, 1)

        # Flambagem da barra comprimida (comprimento L = module_size):
        slenderness_lambda = (module_size_m * 1000.0) / radius_gyration_r_mm
        # Capacidade resistente de cálculo à compressão:
        chi = min(1.0, 150000.0 / (slenderness_lambda ** 2))
        nc_rd_kn = (chi * area_tube_mm2 * (steel_fy_mpa / 1.10)) / 1000.0

        is_structurally_safe = max_chord_force_kn <= nc_rd_kn

        return {
            "entity_type": "SpaceTrussReport",
            "parameters": {
                "span_dimensions_m": [span_x_m, span_y_m],
                "module_size_m": module_size_m,
                "truss_depth_m": truss_depth_m,
                "uniform_load_kn_m2": uniform_load_kn_m2,
                "tube_outer_diam_mm": tube_outer_diam_mm,
            },
            "truss_statistics": {
                "nodes_count": len(all_nodes),
                "members_count": len(members),
                "tube_cross_section_area_cm2": round(area_tube_mm2 / 100.0, 2),
                "max_chord_axial_force_kn": max_chord_force_kn,
                "allowable_buckling_load_kn": round(nc_rd_kn, 1),
                "slenderness_lambda": round(slenderness_lambda, 1),
                "is_structurally_safe": is_structurally_safe,
                "status_label": f"TRELIÇA ESPACIAL GERADA: {len(all_nodes)} nós, {len(members)} barras (Segurança à Flambagem: {round((nc_rd_kn/max(0.1, max_chord_force_kn)), 2)})",
            },
            "truss_nodes": all_nodes[:20],  # Amostra para resposta compacta
            "status": "COMPUTED",
        }
