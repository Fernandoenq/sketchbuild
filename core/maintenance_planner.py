"""
Planejador de Manutenção Preventiva e Vida Útil de Playgrounds (NBR 16071-7 - Zero DLL).

Implementa os ciclos normativos de inspeção da ABNT NBR 16071-7:
1. Inspeção Visual de Rotina (Frequência: Semanal).
2. Inspeção Operacional de Desgaste (Frequência: Trimestral - Reaperto de parafusos inox).
3. Inspeção Principal e Estrutural (Frequência: Anual - Teste de estabilidade e apodrecimento de madeira).
4. Estimativa de vida útil e cálculo de reaplicação de imunizantes e stain protetor.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List


class MaintenancePlanner:
    """Motor analítico de gestão de manutenção preventiva de brinquedos infantis."""

    @classmethod
    def generate_maintenance_plan(
        cls,
        scene_data: Dict[str, Any],
        installation_date_iso: str = "2026-03-01",
        environment_type: str = "urban"  # 'urban', 'coastal' (litoral), 'rural'
    ) -> Dict[str, Any]:
        """Gera o cronograma de manutenção preventiva completo."""
        try:
            start_date = datetime.strptime(installation_date_iso, "%Y-%m-%d")
        except Exception:
            start_date = datetime.now()

        # Fatores de agressividade ambiental
        env_factors = {
            "coastal": {"factor": 1.5, "desc": "Ambiente Litorâneo (Alta Salinidade / Maresia)"},
            "urban": {"factor": 1.0, "desc": "Ambiente Urbano Típico (Praças e Escolas)"},
            "rural": {"factor": 0.8, "desc": "Ambiente Rural / Condomínios Fechados"},
        }
        env_info = env_factors.get(environment_type.lower(), env_factors["urban"])
        agg_factor = env_info["factor"]

        instances = scene_data.get("instances", [])
        total_items = max(1, len(instances))

        # Ciclos de inspeção calculados
        tasks = []

        # 1. Rotina Semanal (a cada 7 dias)
        d_rotina = start_date + timedelta(days=7)
        tasks.append({
            "level": "Rotina",
            "frequency": "Semanal",
            "next_date": d_rotina.strftime("%d/%m/%Y"),
            "items_to_check": "Limpeza do piso amortecedor, detritos, objetos pontiagudos e peças soltas.",
            "responsible": "Equipe de Limpeza / Zeladoria Local",
            "norm_clause": "ABNT NBR 16071-7: Cláusula 5.2.1",
        })

        # 2. Operacional Trimestral (a cada 90 dias / agg_factor)
        days_oper = int(90 / agg_factor)
        d_oper = start_date + timedelta(days=days_oper)
        tasks.append({
            "level": "Operacional",
            "frequency": f"A cada {days_oper} dias",
            "next_date": d_oper.strftime("%d/%m/%Y"),
            "items_to_check": "Reaperto de parafusos e barras roscadas inox, verificação de folgas em corrimãos e trincas superficiais na madeira.",
            "responsible": "Técnico de Manutenção Mecânica",
            "norm_clause": "ABNT NBR 16071-7: Cláusula 5.2.2",
        })

        # 3. Principal Anual
        days_annual = int(365 / agg_factor)
        d_annual = start_date + timedelta(days=days_annual)
        tasks.append({
            "level": "Principal",
            "frequency": "Anual",
            "next_date": d_annual.strftime("%d/%m/%Y"),
            "items_to_check": "Avaliação estrutural completa de colunas enterradas, integridade do tratamento em autoclave (CCA) e reaplicação de stain protetor hidrorrepelente.",
            "responsible": "Engenheiro Responsável Técnico (CREA)",
            "norm_clause": "ABNT NBR 16071-7: Cláusula 5.2.3",
        })

        # Estimativa de vida útil com base no ambiente
        base_life_years = 12.0
        expected_lifespan_years = round(base_life_years / agg_factor, 1)

        return {
            "entity_type": "MaintenancePlan",
            "installation_date": start_date.strftime("%d/%m/%Y"),
            "environment": env_info["desc"],
            "monitored_components_count": total_items,
            "expected_lifespan_years": expected_lifespan_years,
            "tasks": tasks,
            "next_urgent_inspection": tasks[0]["next_date"],
        }
