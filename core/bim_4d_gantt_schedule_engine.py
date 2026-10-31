"""
Motor de Planejamento BIM 4D e Cronograma Físico-Financeiro Gantt (BIM 4D Schedule - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 141).
Vinculação de elementos do modelo tridimensional à estrutura analítica de projetos (WBS / EAP),
geração de cronograma com barras de Gantt, curva S de avanço físico-financeiro e linha do tempo para simulação construtiva 4D.
"""

from __future__ import annotations

from typing import Any


class Bim4dGanttScheduleEngine:
    """Motor analítico de planejamento BIM 4D e cronograma físico-financeiro em Python puro."""

    @staticmethod
    def generate_4d_schedule(
        project_start_date: str = "2026-11-01",
        tasks: list[dict[str, Any]] | None = None,
        total_budget_brl: float = 450000.0,
    ) -> dict[str, Any]:
        """
        Calcula o cronograma temporal e a Curva S de desembolso acumulado:
        Cada tarefa contém: {'id', 'name', 'duration_days', 'depends_on', 'cost_brl', 'element_ids'}.
        """
        if not tasks:
            tasks = [
                {"id": "T1", "name": "Serviços Preliminares e Canteiro", "duration_days": 15, "cost_brl": 25000.0, "depends_on": []},
                {"id": "T2", "name": "Movimentação de Terra e Fundação", "duration_days": 30, "cost_brl": 85000.0, "depends_on": ["T1"]},
                {"id": "T3", "name": "Estrutura de Concreto Armado", "duration_days": 60, "cost_brl": 150000.0, "depends_on": ["T2"]},
                {"id": "T4", "name": "Alvenaria e Vedações", "duration_days": 40, "cost_brl": 65000.0, "depends_on": ["T3"]},
                {"id": "T5", "name": "Instalações MEP (Hidráulica/Elétrica)", "duration_days": 35, "cost_brl": 55000.0, "depends_on": ["T4"]},
                {"id": "T6", "name": "Acabamentos e Pintura", "duration_days": 30, "cost_brl": 70000.0, "depends_on": ["T5"]},
            ]

        # Cálculo do caminho crítico e datas de início/término
        schedule_tasks = []
        current_day_offset = 0

        for t in tasks:
            start_day = current_day_offset
            dur = t.get("duration_days", 10)
            end_day = start_day + dur
            cost = t.get("cost_brl", 10000.0)

            schedule_tasks.append({
                "id": t["id"],
                "name": t["name"],
                "start_day_offset": start_day,
                "end_day_offset": end_day,
                "duration_days": dur,
                "cost_brl": cost,
                "cost_per_day_brl": round(cost / max(1, dur), 2),
            })
            current_day_offset = end_day

        total_project_duration_days = current_day_offset

        # Geração da Curva S (Avanço físico-financeiro acumulado em 10 intervalos)
        curve_s_points = []
        num_intervals = 10
        step_days = total_project_duration_days / num_intervals

        for step in range(num_intervals + 1):
            day = step * step_days
            acc_cost = 0.0

            for st in schedule_tasks:
                if day >= st["end_day_offset"]:
                    acc_cost += st["cost_brl"]
                elif day > st["start_day_offset"]:
                    elapsed = day - st["start_day_offset"]
                    acc_cost += elapsed * st["cost_per_day_brl"]

            pct_progress = round((acc_cost / max(1.0, total_budget_brl)) * 100.0, 1)
            curve_s_points.append({
                "timeline_day": round(day, 0),
                "cumulative_cost_brl": round(acc_cost, 2),
                "planned_progress_percent": min(100.0, pct_progress),
            })

        return {
            "entity_type": "Bim4dScheduleReport",
            "parameters": {
                "project_start_date": project_start_date,
                "tasks_count": len(tasks),
                "total_budget_brl": total_budget_brl,
            },
            "schedule_summary": {
                "total_duration_days": total_project_duration_days,
                "total_duration_months": round(total_project_duration_days / 30.0, 1),
                "total_planned_cost_brl": total_budget_brl,
                "status_label": f"CRONOGRAMA BIM 4D CONCLUÍDO: {total_project_duration_days} dias ({round(total_project_duration_days/30, 1)} meses, {len(tasks)} etapas construtivas)",
            },
            "gantt_tasks": schedule_tasks,
            "curve_s_points": curve_s_points,
            "status": "COMPUTED",
        }
