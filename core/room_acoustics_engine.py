"""
Motor de Acústica Arquitetônica e Tempo de Reverberação NBR 10152 (Room Acoustics - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 112).
Cálculo analítico do Tempo de Reverberação (RT60) pela fórmula clássica de Wallace Sabine,
em 6 bandas de frequência (125Hz a 4000Hz), e diagnóstico de inteligibilidade da fala.
"""

from __future__ import annotations

import math
from typing import Any


class RoomAcousticsEngine:
    """Motor analítico de acústica de salas e tempos de reverberação em Python puro."""

    # Coeficientes de absorção sonora alfa (alpha) padrão da literatura (125Hz a 4000Hz)
    ABSORPTION_DATABASE = {
        "concreto_aparente": [0.01, 0.01, 0.02, 0.02, 0.02, 0.03],
        "alvenaria_rebocada": [0.02, 0.02, 0.03, 0.04, 0.05, 0.05],
        "vidro_comum": [0.35, 0.25, 0.18, 0.12, 0.07, 0.04],
        "piso_madeira": [0.15, 0.11, 0.10, 0.07, 0.06, 0.07],
        "piso_porcelanato": [0.01, 0.01, 0.01, 0.02, 0.02, 0.02],
        "gesso_acartonado": [0.29, 0.10, 0.05, 0.04, 0.07, 0.09],
        "painel_acustico_la_vidro": [0.20, 0.50, 0.85, 0.95, 0.95, 0.90],
        "cortina_pesada": [0.07, 0.31, 0.49, 0.75, 0.70, 0.60],
        "publico_poltronas_estofadas": [0.44, 0.60, 0.77, 0.89, 0.82, 0.70],
    }

    FREQUENCIES_HZ = [125, 250, 500, 1000, 2000, 4000]

    @staticmethod
    def calculate_room_reverberation(
        room_width_m: float = 6.0,
        room_length_m: float = 8.0,
        room_height_m: float = 3.0,
        surfaces: list[dict[str, Any]] | None = None,
        room_type: str = "CLASSROOM",  # "CLASSROOM", "AUDITORIUM", "OFFICE", "RECORDING_STUDIO"
    ) -> dict[str, Any]:
        """
        Calcula o volume, área total e tempo de reverberação RT60 para cada frequência.
        Cada surface: {'name': str, 'area_m2': float, 'material_id': str}
        """
        volume_m3 = room_width_m * room_length_m * room_height_m

        if not surfaces:
            # Superfícies padrão: Piso porcelanato, Teto gesso, Paredes reboco, Janelas vidro
            area_floor = room_width_m * room_length_m
            area_ceiling = area_floor
            area_walls = 2.0 * (room_width_m + room_length_m) * room_height_m
            area_windows = 8.0
            area_net_walls = max(1.0, area_walls - area_windows)

            surfaces = [
                {"name": "Piso", "area_m2": area_floor, "material_id": "piso_porcelanato"},
                {"name": "Forro", "area_m2": area_ceiling, "material_id": "gesso_acartonado"},
                {"name": "Paredes Rebocadas", "area_m2": area_net_walls, "material_id": "alvenaria_rebocada"},
                {"name": "Esquadrias Vidro", "area_m2": area_windows, "material_id": "vidro_comum"},
            ]

        total_surface_area_m2 = sum(float(s.get("area_m2", 1.0)) for s in surfaces)

        # Cálculo da absorção equivalente A (em m2 Sabin) por frequência
        rt60_by_frequency = {}
        total_absorption_by_freq = []

        for f_idx, freq in enumerate(RoomAcousticsEngine.FREQUENCIES_HZ):
            total_a = 0.0
            for s in surfaces:
                area = float(s.get("area_m2", 1.0))
                mat_id = s.get("material_id", "alvenaria_rebocada").lower()
                alphas = RoomAcousticsEngine.ABSORPTION_DATABASE.get(
                    mat_id, RoomAcousticsEngine.ABSORPTION_DATABASE["alvenaria_rebocada"]
                )
                alpha_f = alphas[f_idx]
                total_a += area * alpha_f

            total_a = max(0.01, total_a)
            total_absorption_by_freq.append(round(total_a, 2))

            # Fórmula de Sabine: RT60 = 0.161 * V / A_total
            rt60 = (0.161 * volume_m3) / total_a
            rt60_by_frequency[f"{freq}Hz"] = round(rt60, 2)

        # Média nas frequências médias (500Hz e 1000Hz) - padrão de avaliação NBR 10152
        rt60_mid = (rt60_by_frequency["500Hz"] + rt60_by_frequency["1000Hz"]) / 2.0

        # Metas ideais segundo a NBR 10152:
        targets_map = {
            "CLASSROOM": (0.6, 0.8),
            "AUDITORIUM": (1.0, 1.4),
            "OFFICE": (0.5, 0.7),
            "RECORDING_STUDIO": (0.3, 0.45),
        }
        min_target, max_target = targets_map.get(room_type.upper(), (0.6, 0.9))

        is_ideal = (min_target <= rt60_mid <= max_target)

        return {
            "entity_type": "RoomAcousticsReport",
            "parameters": {
                "room_type": room_type.upper(),
                "volume_m3": round(volume_m3, 2),
                "total_surface_area_m2": round(total_surface_area_m2, 2),
            },
            "acoustic_metrics": {
                "rt60_mid_seconds": round(rt60_mid, 2),
                "target_range_seconds": [min_target, max_target],
                "is_compliant_nbr10152": is_ideal,
                "status_label": "ACÚSTICA OTIMIZADA (CONFORME NBR 10152)" if is_ideal else ("EXCESSO DE REVERBERAÇÃO (ECO)" if rt60_mid > max_target else "SALA MUITO AMORTECIDA"),
            },
            "rt60_frequency_spectrum": rt60_by_frequency,
            "total_absorption_sabins": total_absorption_by_freq,
            "status": "COMPUTED",
        }
