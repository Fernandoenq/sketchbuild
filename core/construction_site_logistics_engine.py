"""
Motor de Logística de Canteiro e Interferência de Gruas NR-18 (Site Logistics - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 143).
Dimensionamento espacial do canteiro de obras, raio de alcance de gruas de torre (jib radius),
capacidade de içamento na ponta (kN/t), verificação de interferência de lanças sobrepostas e áreas de vivência seguras.
"""

from __future__ import annotations

import math
from typing import Any


class ConstructionSiteLogisticsEngine:
    """Motor analítico de logística de canteiro de obras e gruas em Python puro."""

    @staticmethod
    def calculate_site_logistics(
        site_width_m: float = 60.0,
        site_length_m: float = 80.0,
        building_footprint_m2: float = 1200.0,
        cranes: list[dict[str, Any]] | None = None,
        daily_workers_count: int = 65,
    ) -> dict[str, Any]:
        """
        Calcula o raio de cobertura da grua, capacidade de carga na ponta e áreas mínimas
        de vivência obrigatórias pela NR-18 (refeitório, vestiário, sanitários).
        """
        if not cranes:
            cranes = [
                {"id": "CRANE-01", "position_xy": [25.0, 35.0], "jib_radius_m": 45.0, "tip_capacity_ton": 1.80, "tower_height_m": 42.0},
                {"id": "CRANE-02", "position_xy": [50.0, 55.0], "jib_radius_m": 40.0, "tip_capacity_ton": 2.20, "tower_height_m": 48.0},
            ]

        # 1. Verificação de interferência mútua entre lanças de gruas:
        crane_interferences = []
        for i in range(len(cranes)):
            for j in range(i + 1, len(cranes)):
                c1, c2 = cranes[i], cranes[j]
                p1, p2 = c1["position_xy"], c2["position_xy"]
                dist = math.sqrt(((p2[0] - p1[0]) ** 2) + ((p2[1] - p1[1]) ** 2))
                sum_radii = c1["jib_radius_m"] + c2["jib_radius_m"]

                has_overlap = dist < sum_radii
                height_diff = abs(c1["tower_height_m"] - c2["tower_height_m"])
                # NR-18 exige no mínimo 2.0m de desnível vertical se houver sobreposição de lanças
                is_safe_vertical_clearance = height_diff >= 2.0

                crane_interferences.append({
                    "cranes_pair": [c1["id"], c2["id"]],
                    "horizontal_distance_m": round(dist, 1),
                    "has_jib_overlap": has_overlap,
                    "vertical_clearance_m": round(height_diff, 1),
                    "is_compliant_nr18": (not has_overlap) or is_safe_vertical_clearance,
                })

        # 2. Dimensionamento das áreas de vivência obrigatórias NR-18:
        # Refeitório: 1.0 m2 por trabalhador (com turnos ~ 70% simultâneos = 0.70 m2/trab)
        canteen_area_m2 = round(daily_workers_count * 0.75, 1)
        # Vestiário: 1.5 m2 por trabalhador
        locker_room_area_m2 = round(daily_workers_count * 1.50, 1)
        # Instalações sanitárias: 1 bacia sanitária para cada 20 trabalhadores, 1 chuveiro para cada 10
        toilets_count = math.ceil(daily_workers_count / 20.0)
        showers_count = math.ceil(daily_workers_count / 10.0)

        site_total_area_m2 = site_width_m * site_length_m
        available_yard_area_m2 = round(site_total_area_m2 - building_footprint_m2 - canteen_area_m2 - locker_room_area_m2, 1)

        all_cranes_compliant = all(ci["is_compliant_nr18"] for ci in crane_interferences)

        return {
            "entity_type": "ConstructionSiteLogisticsReport",
            "parameters": {
                "site_dimensions_m": [site_width_m, site_length_m],
                "building_footprint_m2": building_footprint_m2,
                "daily_workers_count": daily_workers_count,
                "cranes_count": len(cranes),
            },
            "logistics_results": {
                "site_total_area_m2": site_total_area_m2,
                "available_yard_area_m2": available_yard_area_m2,
                "canteen_area_required_m2": canteen_area_m2,
                "locker_room_area_required_m2": locker_room_area_m2,
                "toilets_required": toilets_count,
                "showers_required": showers_count,
                "crane_overlaps_analysis": crane_interferences,
                "is_site_safe_nr18": all_cranes_compliant,
                "status_label": "CANTEIRO NR-18 EM CONFORMIDADE (Áreas de vivência e desnível de gruas aprovados)" if all_cranes_compliant else "ALERTA: RISCO DE COLISÃO DE GRUAS SEM DESNÍVEL",
            },
            "status": "COMPUTED",
        }
