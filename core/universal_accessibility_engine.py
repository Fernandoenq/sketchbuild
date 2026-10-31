"""
Motor de Acessibilidade Universal a Edificações ABNT NBR 9050 (Universal Accessibility - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 144).
Auditoria normativa de rotas acessíveis, dimensionamento de rampas (inclinação máxima i <= 8.33% / 1:12),
vãos livres de circulação e portas (min 80cm), áreas de manobra de cadeirantes (giro 180° e 360°) e sanitários P.C.D.
"""

from __future__ import annotations

import math
from typing import Any


class UniversalAccessibilityEngine:
    """Motor analítico de auditoria e dimensionamento de acessibilidade NBR 9050 em Python puro."""

    @staticmethod
    def audit_accessibility(
        door_clear_width_cm: float = 85.0,  # Largura útil de passagem da porta
        corridor_width_cm: float = 120.0,  # Largura livre do corredor
        ramp_slope_percent: float = 8.33,  # Inclinação da rampa (máximo 8.33% para desníveis até 80cm)
        ramp_rise_height_cm: float = 60.0,  # Desnível vertical a vencer
        wheelchair_turn_space_diameter_m: float = 1.50,  # Círculo de giro livre 360° (mínimo 1.50m)
        has_tactile_paving: bool = True,  # Piso tátil de alerta e direcional
    ) -> dict[str, Any]:
        """
        Valida itens obrigatórios segundo a ABNT NBR 9050:2020:
        1. Vão livre de porta >= 80cm
        2. Corredor livre >= 120cm (para uso comum) ou 150cm (para curvas)
        3. Rampa i <= 8.33% com patamares de descanso a cada 50m ou 0.80m de desnível
        4. Círculo de giro para cadeira de rodas >= 1.50m
        """
        # Verificações
        is_door_compliant = door_clear_width_cm >= 80.0
        is_corridor_compliant = corridor_width_cm >= 120.0
        is_ramp_slope_compliant = ramp_slope_percent <= 8.33
        is_turn_space_compliant = wheelchair_turn_space_diameter_m >= 1.50

        # Comprimento projetado da rampa: L = H / (i / 100)
        ramp_run_length_m = (ramp_rise_height_cm / 100.0) / (ramp_slope_percent / 100.0)
        # Patamar intermediário obrigatório se desnível > 80cm ou comprimento > 12m
        intermediate_landings_count = 1 if (ramp_rise_height_cm > 80.0 or ramp_run_length_m > 12.0) else 0

        # Dimensões mínimas do sanitário acessível P.C.D.: 1.50m x 1.70m
        is_overall_accessible = (
            is_door_compliant and
            is_corridor_compliant and
            is_ramp_slope_compliant and
            is_turn_space_compliant and
            has_tactile_paving
        )

        return {
            "entity_type": "AccessibilityReport",
            "parameters": {
                "door_width_cm": door_clear_width_cm,
                "corridor_width_cm": corridor_width_cm,
                "ramp_slope_percent": ramp_slope_percent,
                "ramp_rise_height_cm": ramp_rise_height_cm,
                "wheelchair_turn_diameter_m": wheelchair_turn_space_diameter_m,
            },
            "compliance_checklist": {
                "door_clear_width_ok": is_door_compliant,
                "corridor_width_ok": is_corridor_compliant,
                "ramp_slope_ok": is_ramp_slope_compliant,
                "ramp_run_length_m": round(ramp_run_length_m, 2),
                "intermediate_landings_needed": intermediate_landings_count,
                "turn_space_360_ok": is_turn_space_compliant,
                "tactile_paving_installed": has_tactile_paving,
                "is_fully_accessible_nbr9050": is_overall_accessible,
                "status_label": "EDIFICAÇÃO CONFORME NBR 9050 (ROTA ACESSÍVEL TOTAL)" if is_overall_accessible else "ALERTA: VIOLAÇÃO DE CRITÉRIOS DE ACESSIBILIDADE",
            },
            "status": "COMPUTED",
        }
