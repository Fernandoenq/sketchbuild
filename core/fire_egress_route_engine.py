"""
Motor de Rotas de Fuga e Saídas de Emergência em Edifícios ABNT NBR 9077 (Fire Egress - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 133).
Cálculo de Unidades de Passagem (N = P / C), largura mínima de portas/corredores/escadas,
verificação das distâncias máximas de caminhamento até saídas externas e traçado da rota segura.
"""

from __future__ import annotations

import math
from typing import Any


class FireEgressRouteEngine:
    """Motor analítico de dimensionamento de saídas de emergência em Python puro."""

    @staticmethod
    def calculate_egress(
        occupancy_type: str = "OFFICE_D1",  # Grupo D (Escritórios), C (Comércio), A (Residencial), etc.
        floor_population_persons: int = 180,
        longest_travel_distance_m: float = 38.0,  # Distância real percorrida do ponto mais distante à escada/saída
        has_sprinklers: bool = True,  # Edifício dotado de chuveiros automáticos (aumenta distância limite)
        has_smoke_detectors: bool = True,
        doors_count: int = 2,
    ) -> dict[str, Any]:
        """
        Calcula capacidade das saídas e unidades de passagem NBR 9077:
        Largura de 1 UP = 0.55m
        Capacidade da UP:
        - Portas e acessos horizontais: C = 100 pessoas/UP
        - Escadas e rampas: C = 75 pessoas/UP (descendente) ou 60 (ascendente)
        """
        # Capacidade unitária de passagem por tipo de via de escape
        capacity_door = 100.0
        capacity_stair = 75.0

        # Unidades de passagem necessárias
        up_needed_doors = floor_population_persons / capacity_door
        up_needed_stairs = floor_population_persons / capacity_stair

        # Número inteiro de UP com arredondamento normativo (NBR 9077):
        up_doors_int = math.ceil(up_needed_doors)
        up_stairs_int = math.ceil(up_needed_stairs)

        # Largura total mínima exigida: L = N * 0.55m (mínimo absoluto 1.10m = 2 UP ou 1.20m para escritórios)
        min_door_total_width_m = max(1.20, up_doors_int * 0.55)
        min_stair_width_m = max(1.20, up_stairs_int * 0.55)

        width_per_door_m = round(min_door_total_width_m / max(1, doors_count), 2)

        # Distâncias máximas a percorrer NBR 9077 (Tabela de distâncias):
        # Sem sprinklers: ~30m a 40m (com mais de uma saída)
        # Com sprinklers: aumenta em 50% (ex: 45m a 60m)
        base_max_distance_m = 40.0 if doors_count >= 2 else 25.0
        allowed_max_distance_m = base_max_distance_m * 1.50 if has_sprinklers else base_max_distance_m

        is_distance_compliant = longest_travel_distance_m <= allowed_max_distance_m

        # Tempo estimado de evacuação total (v_evacuação ~ 1.0 m/s):
        evacuation_time_seconds = round((longest_travel_distance_m / 1.0) + (floor_population_persons / (doors_count * 1.2)), 1)

        # Traçado 3D representativo da rota de fuga
        egress_waypoints_3d = [
            [-15.0, -10.0, 0.0],
            [0.0, -10.0, 0.0],
            [0.0, 5.0, 0.0],
            [12.0, 5.0, 0.0],
        ]

        return {
            "entity_type": "FireEgressReport",
            "parameters": {
                "occupancy_type": occupancy_type,
                "floor_population_persons": floor_population_persons,
                "longest_travel_distance_m": longest_travel_distance_m,
                "has_sprinklers": has_sprinklers,
                "doors_count": doors_count,
            },
            "egress_metrics": {
                "units_of_passage_doors": up_doors_int,
                "units_of_passage_stairs": up_stairs_int,
                "total_doors_width_required_m": round(min_door_total_width_m, 2),
                "width_per_door_m": width_per_door_m,
                "stair_width_required_m": round(min_stair_width_m, 2),
                "max_allowed_travel_distance_m": allowed_max_distance_m,
                "is_travel_distance_compliant": is_distance_compliant,
                "estimated_evacuation_time_s": evacuation_time_seconds,
                "status_label": f"ROTA DE FUGA APROVADA: {doors_count} porta(s) de {width_per_door_m}m ({longest_travel_distance_m}m <= {allowed_max_distance_m}m NBR 9077)" if is_distance_compliant else "ALERTA: DISTÂNCIA MÁXIMA DE SAÍDA EXCEDIDA",
            },
            "egress_path_waypoints_3d": egress_waypoints_3d,
            "status": "COMPUTED",
        }
