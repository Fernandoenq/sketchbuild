"""
Motor de Movimentação de Terra e Diagrama de Massas de Brückner (Earthwork - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 120).
Cálculo de corte e aterro por seções transversais consecutivas (método das médias das áreas),
fator de empolamento/contração e curva acumulada de Brückner com distância média de transporte (DMT).
"""

from __future__ import annotations

from typing import Any


class EarthworkBrucknerEngine:
    """Motor analítico de cálculo de terraplenagem e transporte em Python puro."""

    @staticmethod
    def calculate_earthwork(
        cross_sections: list[dict[str, Any]] | None = None,
        bulking_factor: float = 1.25,  # Fator de empolamento do solo escavado (25%)
        compaction_factor: float = 0.85,  # Fator de contração no aterro compactado
    ) -> dict[str, Any]:
        """
        Processa as estacas/seções transversais ao longo de um alinhamento.
        Cada seção contém: {'station_m', 'cut_area_m2', 'fill_area_m2'}.
        """
        if not cross_sections:
            cross_sections = [
                {"station_m": 0.0, "cut_area_m2": 15.0, "fill_area_m2": 0.0},
                {"station_m": 20.0, "cut_area_m2": 22.0, "fill_area_m2": 2.0},
                {"station_m": 40.0, "cut_area_m2": 18.0, "fill_area_m2": 8.0},
                {"station_m": 60.0, "cut_area_m2": 4.0, "fill_area_m2": 25.0},
                {"station_m": 80.0, "cut_area_m2": 0.0, "fill_area_m2": 32.0},
                {"station_m": 100.0, "cut_area_m2": 0.0, "fill_area_m2": 18.0},
            ]

        total_cut_volume_m3 = 0.0
        total_fill_volume_m3 = 0.0
        bruckner_mass_curve: list[dict[str, float]] = []

        cumulative_volume = 0.0
        bruckner_mass_curve.append({
            "station_m": cross_sections[0]["station_m"],
            "cumulative_volume_m3": 0.0
        })

        for i in range(len(cross_sections) - 1):
            s1, s2 = cross_sections[i], cross_sections[i+1]
            dist_m = s2["station_m"] - s1["station_m"]

            # Método das médias das áreas: V = ((A1 + A2) / 2) * dist
            cut_vol = ((s1["cut_area_m2"] + s2["cut_area_m2"]) / 2.0) * dist_m
            fill_vol = ((s1["fill_area_m2"] + s2["fill_area_m2"]) / 2.0) * dist_m

            total_cut_volume_m3 += cut_vol
            total_fill_volume_m3 += fill_vol

            # Volume corrigido para a curva de Brückner (Corte positivo, Aterro negativo com contração)
            net_vol = cut_vol - (fill_vol / compaction_factor)
            cumulative_volume += net_vol

            bruckner_mass_curve.append({
                "station_m": s2["station_m"],
                "cumulative_volume_m3": round(cumulative_volume, 2)
            })

        # Balanço global
        net_balance_m3 = total_cut_volume_m3 - total_fill_volume_m3
        is_borrow_required = net_balance_m3 < 0.0  # Necessidade de bota-fora ou jazida de empréstimo

        # Estimativa de Distância Média de Transporte (DMT)
        total_length_m = cross_sections[-1]["station_m"] - cross_sections[0]["station_m"]
        dmt_m = round(total_length_m * 0.40, 1)

        return {
            "entity_type": "EarthworkBrucknerReport",
            "parameters": {
                "sections_count": len(cross_sections),
                "bulking_factor": bulking_factor,
                "compaction_factor": compaction_factor,
            },
            "earthwork_summary": {
                "total_cut_geometric_m3": round(total_cut_volume_m3, 2),
                "total_cut_bulked_m3": round(total_cut_volume_m3 * bulking_factor, 2),
                "total_fill_geometric_m3": round(total_fill_volume_m3, 2),
                "net_balance_m3": round(net_balance_m3, 2),
                "estimated_dmt_m": dmt_m,
                "borrow_or_spoil": "JAZIDA DE EMPRÉSTIMO (FALTA TERRA)" if is_borrow_required else "BOTA-FORA (SOBRA DE TERRA)",
                "status_label": f"BALANÇO: {abs(round(net_balance_m3, 1))} m3 ({'FALTA' if is_borrow_required else 'SOBRA'})",
            },
            "bruckner_curve": bruckner_mass_curve,
            "status": "COMPUTED",
        }
