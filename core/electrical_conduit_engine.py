"""
Motor de Dimensionamento de Eletrodutos e Fiação Elétrica NBR 5410 (Electrical Conduits - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 110).
Roteamento 3D de conduítes, verificação da taxa máxima de ocupação (NBR 5410: máx 40% para 3+ cabos)
e cálculo analítico de queda de tensão admissível (<= 4.0%).
"""

from __future__ import annotations

import math
from typing import Any


class ElectricalConduitEngine:
    """Motor analítico de instalações elétricas e eletrodutos em Python puro."""

    @staticmethod
    def calculate_conduit_run(
        conduit_nominal_dn_mm: float = 25.0,  # Conduíte 3/4" (DN 25mm, d_int ~ 19.8mm)
        circuit_current_amperes: float = 16.0,  # Corrente do disjuntor (16A / 20A / 32A)
        cable_gauge_mm2: float = 2.5,  # Seção dos condutores (1.5, 2.5, 4.0, 6.0 mm2)
        cables_count: int = 3,  # Fase, Neutro, Terra (3 cabos)
        circuit_length_m: float = 18.0,  # Extensão do circuito
        voltage_v: float = 127.0,  # Tensão nominal (127V ou 220V)
        power_factor: float = 0.95,  # Fator de potência
        copper_resistivity: float = 0.0178,  # Resistividade do cobre ohm.mm2/m
    ) -> dict[str, Any]:
        """
        Calcula a taxa de ocupação da seção e a queda de tensão percentual.
        """
        # Diâmetro externo comercial do condutor isolado PVC 750V / 1kV (NBR NM 247-3):
        # 1.5mm2 -> ~2.8mm; 2.5mm2 -> ~3.5mm; 4.0mm2 -> ~4.2mm; 6.0mm2 -> ~4.8mm
        cable_ext_diameter_mm = 1.6 + math.sqrt(cable_gauge_mm2) * 1.2
        cable_area_total_mm2 = math.pi * ((cable_ext_diameter_mm / 2.0) ** 2)
        total_cables_area_mm2 = cable_area_total_mm2 * cables_count

        # Diâmetro interno útil do eletroduto corrugado PEAD/PVC:
        # DN 20 -> d_int ~ 15.0mm; DN 25 -> d_int ~ 19.5mm; DN 32 -> d_int ~ 25.0mm
        conduit_internal_d_mm = conduit_nominal_dn_mm * 0.78
        conduit_usable_area_mm2 = math.pi * ((conduit_internal_d_mm / 2.0) ** 2)

        # Taxa de ocupação real:
        occupancy_ratio_percent = (total_cables_area_mm2 / conduit_usable_area_mm2) * 100.0

        # Limite normativo NBR 5410 item 6.2.11.1:
        # 1 condutor -> 53%; 2 condutores -> 31%; 3 ou mais condutores -> 40%
        if cables_count == 1:
            max_allowed_occupancy = 53.0
        elif cables_count == 2:
            max_allowed_occupancy = 31.0
        else:
            max_allowed_occupancy = 40.0

        is_occupancy_compliant = occupancy_ratio_percent <= max_allowed_occupancy

        # Cálculo da Queda de Tensão (Monofásico / Bifásico a dois fios):
        # Delta_V = (2 * rho * L * I * cos(phi)) / S
        voltage_drop_volts = (2.0 * copper_resistivity * circuit_length_m * circuit_current_amperes * power_factor) / cable_gauge_mm2
        voltage_drop_percent = (voltage_drop_volts / voltage_v) * 100.0

        # Limite NBR 5410 item 6.2.7: Máximo 4.0% para circuitos terminais
        is_voltage_drop_compliant = voltage_drop_percent <= 4.0

        is_fully_compliant = is_occupancy_compliant and is_voltage_drop_compliant

        # Rota 3D simples de conduíte e caixa de passagem 4x2
        waypoints = [
            [0.0, 0.0, 0.30],      # Tomada baixa
            [0.0, 0.0, 2.60],      # Subida vertical
            [circuit_length_m * 0.6, 0.0, 2.60], # Trecho forro/laje
            [circuit_length_m * 0.6, 0.0, 1.10], # Descida interruptor
        ]

        return {
            "entity_type": "ElectricalConduitReport",
            "parameters": {
                "conduit_nominal_dn_mm": conduit_nominal_dn_mm,
                "circuit_current_amperes": circuit_current_amperes,
                "cable_gauge_mm2": cable_gauge_mm2,
                "cables_count": cables_count,
                "circuit_length_m": circuit_length_m,
                "voltage_v": voltage_v,
            },
            "conduit_occupancy": {
                "cables_total_area_mm2": round(total_cables_area_mm2, 2),
                "conduit_internal_area_mm2": round(conduit_usable_area_mm2, 2),
                "occupancy_percent": round(occupancy_ratio_percent, 1),
                "max_allowed_percent": max_allowed_occupancy,
                "is_compliant_nbr5410": is_occupancy_compliant,
            },
            "voltage_drop": {
                "voltage_drop_volts": round(voltage_drop_volts, 2),
                "voltage_drop_percent": round(voltage_drop_percent, 2),
                "max_allowed_percent": 4.0,
                "is_compliant_nbr5410": is_voltage_drop_compliant,
            },
            "diagnostic": {
                "is_fully_compliant": is_fully_compliant,
                "status_label": "CONFORME NBR 5410 (OCUPAÇÃO E TENSÃO APROVADAS)" if is_fully_compliant else "ATENÇÃO: AUMENTAR BITOLA OU DIÂMETRO DO ELETRODUTO",
            },
            "waypoints_3d": waypoints,
            "status": "COMPUTED",
        }
