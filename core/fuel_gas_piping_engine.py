"""
Motor de Instalações de Gás Canalizado GLP/GN ABNT NBR 15526 / NBR 15358 (Fuel Gas Piping - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 131).
Dimensionamento hidráulico de redes prediais de gás combustível em baixa e média pressão,
cálculo de perda de carga pela fórmula de Renouard e controle de velocidade máxima admissível.
"""

from __future__ import annotations

import math
from typing import Any


class FuelGasPipingEngine:
    """Motor analítico de cálculo de redes de gás combustível em Python puro."""

    @staticmethod
    def calculate_gas_network(
        gas_type: str = "GLP",  # GLP (Gás Liquefeito de Petróleo) ou GN (Gás Natural)
        total_power_kw: float = 75.0,  # Potência total instalada dos aparelhos (fogões, aquecedores)
        pipe_length_m: float = 25.0,
        inlet_pressure_kpa: float = 2.80,  # Baixa pressão GLP ~ 2.8 kPa (28 mbar) ou GN ~ 2.0 kPa
        pipe_material: str = "COPPER",  # Cobre classe I/A ou Aço Galvanizado
        nominal_diameter_dn_mm: float = 22.0,  # Tubo de cobre 22mm
    ) -> dict[str, Any]:
        """
        Calcula consumo volumétrico Q = Potência / PCI, velocidade e perda de carga por Renouard:
        Delta_P = 22150 * S * L * Q^1.82 / D^4.82 (para baixa pressão)
        onde S = densidade relativa do gás (GLP S ~ 1.55, GN S ~ 0.60)
        """
        # Poder Calorífico Inferior (PCI):
        # GLP ~ 24000 kcal/m3 ~ 27.9 kWh/m3
        # GN ~ 8600 kcal/m3 ~ 10.0 kWh/m3
        if gas_type.upper() == "GLP":
            pci_kwh_m3 = 27.9
            density_relative_s = 1.55  # Mais pesado que o ar
        else:
            pci_kwh_m3 = 10.0
            density_relative_s = 0.60  # Mais leve que o ar

        # Vazão horária de projeto: Q (m3/h)
        flow_rate_m3_h = total_power_kw / pci_kwh_m3
        q_m3_s = flow_rate_m3_h / 3600.0

        # Diâmetro interno do tubo (cobre DN 22mm -> d_int ~ 20.0 mm)
        d_int_mm = nominal_diameter_dn_mm - 2.0
        d_int_m = d_int_mm / 1000.0

        # Área de escoamento e velocidade do gás:
        area_m2 = (math.pi * (d_int_m ** 2)) / 4.0
        velocity_m_s = q_m3_s / area_m2

        # Perda de carga pela fórmula de Renouard simplificada para baixa pressão (P <= 5 kPa):
        # Delta P (mmca) = (22150 * S * L * Q^1.82) / D^4.82
        # Convertendo para kPa (1 mmca = 0.00980665 kPa)
        # Comprimento equivalente total com conexões (+30% NBR 15526)
        total_equivalent_length_m = pipe_length_m * 1.30

        delta_p_mmca = (22150.0 * density_relative_s * total_equivalent_length_m * (flow_rate_m3_h ** 1.82)) / (d_int_mm ** 4.82)
        delta_p_kpa = delta_p_mmca * 0.00980665

        outlet_pressure_kpa = inlet_pressure_kpa - delta_p_kpa

        # Limites da NBR 15526:
        # 1. Perda de carga máxima admissível: 10% da pressão inicial (ou max 0.28 kPa para GLP)
        max_allowed_loss_kpa = inlet_pressure_kpa * 0.10
        is_pressure_drop_ok = delta_p_kpa <= max_allowed_loss_kpa

        # 2. Velocidade máxima permitida: v <= 10.0 m/s para prevenir ruído e arraste
        is_velocity_ok = velocity_m_s <= 10.0

        is_compliant = is_pressure_drop_ok and is_velocity_ok

        # Geometria 3D representativa da tubulação de gás
        vertices = [
            [0.0, 0.0, 0.0], [pipe_length_m, 0.0, 0.0],
            [0.0, d_int_m, 0.0], [pipe_length_m, d_int_m, 0.0],
        ]
        triangles = [[0, 1, 2], [1, 3, 2]]

        return {
            "entity_type": "FuelGasPipingReport",
            "parameters": {
                "gas_type": gas_type,
                "total_power_kw": total_power_kw,
                "pipe_length_m": pipe_length_m,
                "inlet_pressure_kpa": inlet_pressure_kpa,
                "nominal_diameter_dn_mm": nominal_diameter_dn_mm,
            },
            "gas_network_results": {
                "gas_flow_rate_m3_h": round(flow_rate_m3_h, 3),
                "gas_velocity_m_s": round(velocity_m_s, 2),
                "total_pressure_drop_kpa": round(delta_p_kpa, 3),
                "total_pressure_drop_mmca": round(delta_p_mmca, 1),
                "outlet_pressure_kpa": round(outlet_pressure_kpa, 3),
                "max_allowed_loss_kpa": round(max_allowed_loss_kpa, 3),
                "is_pressure_loss_compliant": is_pressure_drop_ok,
                "is_velocity_compliant": is_velocity_ok,
                "is_compliant_nbr15526": is_compliant,
                "status_label": "REDE DE GÁS APROVADA (NBR 15526)" if is_compliant else "ALERTA: PERDA DE CARGA OU VELOCIDADE EXCESSIVA",
            },
            "geometry_3d": {
                "vertices": vertices,
                "triangles": triangles,
            },
            "status": "COMPUTED",
        }
