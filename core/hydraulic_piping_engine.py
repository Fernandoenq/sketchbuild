"""
Motor de Tubulações Hidráulicas, Conexões e Perda de Carga NBR 5626 (Hydraulic Piping - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 109).
Geração paramétrica de rede predial de água fria/quente (PVC/PPR), cálculo de perda de carga
contínua (Hazen-Williams), perdas localizadas em conexões e pressão residual dinâmica.
"""

from __future__ import annotations

import math
from typing import Any


class HydraulicPipingEngine:
    """Motor analítico de dimensionamento hidráulico e geração 3D em Python puro."""

    @staticmethod
    def calculate_piping_run(
        pipe_diameter_dn_mm: float = 25.0,
        flow_rate_l_s: float = 0.50,
        pipe_roughness_c: float = 140.0,  # C de Hazen-Williams (PVC/PPR = 140 a 150)
        inlet_pressure_mca: float = 15.0,  # Metros de coluna d'água (m.c.a.)
        waypoints: list[list[float]] | None = None,
        fittings: list[str] | None = None,  # Ex: ["ELBOW_90", "TEE_PASSING", "VALVE_BALL"]
    ) -> dict[str, Any]:
        """
        Calcula o traçado 3D e perda de carga hidrostática/hidrodinâmica.
        Waypoints padrão: [0,0,1] -> [0,3,1] -> [0,3,2.5]
        """
        if not waypoints or len(waypoints) < 2:
            waypoints = [[0.0, 0.0, 1.0], [0.0, 3.0, 1.0], [0.0, 3.0, 2.5]]

        if fittings is None:
            fittings = ["ELBOW_90", "ELBOW_90"]

        # Comprimento geométrico real da tubulação
        total_length_m = 0.0
        for i in range(len(waypoints) - 1):
            p1, p2 = waypoints[i], waypoints[i+1]
            dist = math.sqrt((p2[0]-p1[0])**2 + (p2[1]-p1[1])**2 + (p2[2]-p1[2])**2)
            total_length_m += dist

        # Diâmetro interno aproximado (DN 25 -> D_int ~ 21.6 mm = 0.0216 m)
        d_m = (pipe_diameter_dn_mm * 0.86) / 1000.0
        q_m3_s = flow_rate_l_s / 1000.0

        # Área de escoamento e velocidade da água: V = Q / A
        area_m2 = math.pi * (d_m ** 2) / 4.0
        velocity_m_s = q_m3_s / area_m2

        # 1. Perda de carga contínua por Hazen-Williams:
        # J = 10.643 * Q^1.852 * C^-1.852 * D^-4.87
        j_m_per_m = 10.643 * (q_m3_s ** 1.852) * (pipe_roughness_c ** -1.852) * (d_m ** -4.87)
        continuous_head_loss_mca = j_m_per_m * total_length_m

        # 2. Comprimento equivalente de conexões (NBR 5626 para PVC DN 25):
        equiv_lengths_map = {
            "ELBOW_90": 1.2,
            "ELBOW_45": 0.5,
            "TEE_PASSING": 0.7,
            "TEE_BRANCH": 2.3,
            "VALVE_BALL": 0.3,
            "VALVE_GATE": 0.2,
        }
        equivalent_length_fittings_m = sum(equiv_lengths_map.get(f.upper(), 1.0) for f in fittings)
        local_head_loss_mca = j_m_per_m * equivalent_length_fittings_m

        total_head_loss_mca = continuous_head_loss_mca + local_head_loss_mca

        # Diferença de cota geométrica Z (Delta Z)
        delta_z = waypoints[-1][2] - waypoints[0][2]

        # Pressão residual disponível: P_fim = P_ini - Delta_H - Delta_Z
        outlet_pressure_mca = inlet_pressure_mca - total_head_loss_mca - delta_z

        # Verificação NBR 5626 (Velocidade máx 3.0 m/s e Pressão mín 1.0 m.c.a.)
        is_compliant = (velocity_m_s <= 3.0) and (outlet_pressure_mca >= 1.0)

        # Geração da geometria 3D (Cilindro extrudado ao longo do traçado)
        vertices_3d = []
        triangles_3d = []
        radius_ext_m = (pipe_diameter_dn_mm / 2.0) / 1000.0

        # Discretiza anéis em torno de cada waypoint
        num_circle_pts = 8
        for w_idx, pt in enumerate(waypoints):
            for c_i in range(num_circle_pts):
                angle = (2.0 * math.pi * c_i) / num_circle_pts
                # Anel no plano XY
                vx = pt[0] + radius_ext_m * math.cos(angle)
                vy = pt[1] + radius_ext_m * math.sin(angle)
                vz = pt[2]
                vertices_3d.append([round(vx, 4), round(vy, 4), round(vz, 4)])

            if w_idx > 0:
                base_prev = (w_idx - 1) * num_circle_pts
                base_curr = w_idx * num_circle_pts
                for c_i in range(num_circle_pts):
                    next_i = (c_i + 1) % num_circle_pts
                    p1 = base_prev + c_i
                    p2 = base_prev + next_i
                    p3 = base_curr + next_i
                    p4 = base_curr + c_i
                    triangles_3d.append([p1, p2, p3])
                    triangles_3d.append([p1, p3, p4])

        return {
            "entity_type": "HydraulicPipingReport",
            "parameters": {
                "pipe_diameter_dn_mm": pipe_diameter_dn_mm,
                "flow_rate_l_s": flow_rate_l_s,
                "inlet_pressure_mca": inlet_pressure_mca,
                "pipe_roughness_c": pipe_roughness_c,
            },
            "hydraulic_results": {
                "pipe_total_length_m": round(total_length_m, 2),
                "flow_velocity_m_s": round(velocity_m_s, 2),
                "hydraulic_gradient_j_m_m": round(j_m_per_m, 4),
                "continuous_head_loss_mca": round(continuous_head_loss_mca, 2),
                "local_head_loss_mca": round(local_head_loss_mca, 2),
                "total_head_loss_mca": round(total_head_loss_mca, 2),
                "elevation_delta_m": round(delta_z, 2),
                "outlet_pressure_mca": round(outlet_pressure_mca, 2),
                "is_compliant_nbr5626": is_compliant,
                "status_label": "CONFORME NBR 5626 (PRESSÃO E VELOCIDADE ADEQUADAS)" if is_compliant else "ATENÇÃO: VELOCIDADE EXCESSIVA OU BAIXA PRESSÃO",
            },
            "geometry_3d": {
                "vertices": vertices_3d,
                "triangles": triangles_3d,
                "waypoints": waypoints,
            },
            "status": "COMPUTED",
        }
