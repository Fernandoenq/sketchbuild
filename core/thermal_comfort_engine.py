"""
Motor de Conforto Térmico e Transmitância Térmica NBR 15220 (Thermal Transmittance - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 111).
Cálculo analítico de resistência térmica total, transmitância térmica (U em W/(m2.K)),
capacidade térmica (Ct) e classificação bioclimática PBE Edifica.
"""

from __future__ import annotations

import math
from typing import Any


class ThermalComfortEngine:
    """Motor analítico de desempenho térmico de envoltória predial em Python puro."""

    @staticmethod
    def calculate_envelope_thermal_performance(
        layers: list[dict[str, Any]] | None = None,
        rsi_m2_k_w: float = 0.13,  # Resistência superficial interna horizontal
        rse_m2_k_w: float = 0.04,  # Resistência superficial externa
        target_bioclimatic_zone: int = 3,  # ZB3 (São Paulo, Campinas, etc.)
    ) -> dict[str, Any]:
        """
        Calcula o coeficiente U e capacidade térmica Ct de parede ou cobertura multicamadas.
        Cada camada: {
            'material': str,
            'thickness_m': float,
            'conductivity_w_m_k': float (lambda),
            'density_kg_m3': float,
            'specific_heat_j_kg_k': float
        }
        """
        if not layers:
            # Parede padrão de alvenaria cerâmica com reboco em ambas as faces
            layers = [
                {"material": "Argamassa Reboco Externo", "thickness_m": 0.025, "conductivity_w_m_k": 1.15, "density_kg_m3": 1800.0, "specific_heat_j_kg_k": 1000.0},
                {"material": "Tijolo Cerâmico Furado 8 furos", "thickness_m": 0.090, "conductivity_w_m_k": 0.40, "density_kg_m3": 950.0, "specific_heat_j_kg_k": 920.0},
                {"material": "Argamassa Reboco Interno", "thickness_m": 0.025, "conductivity_w_m_k": 1.15, "density_kg_m3": 1800.0, "specific_heat_j_kg_k": 1000.0},
            ]

        # 1. Resistência térmica total (R_T = Rse + sum(e / lambda) + Rsi)
        total_layers_resistance = 0.0
        total_heat_capacity_kj_m2_k = 0.0
        total_thickness_m = 0.0
        total_weight_kg_m2 = 0.0

        layer_breakdown = []
        for lay in layers:
            e = max(0.001, float(lay.get("thickness_m", 0.02)))
            lam = max(0.01, float(lay.get("conductivity_w_m_k", 0.80)))
            rho = max(10.0, float(lay.get("density_kg_m3", 1500.0)))
            c = max(100.0, float(lay.get("specific_heat_j_kg_k", 1000.0)))

            r_layer = e / lam
            total_layers_resistance += r_layer
            total_thickness_m += e

            weight_layer = e * rho
            total_weight_kg_m2 += weight_layer

            # Capacidade térmica da camada em kJ/(m2.K): Ct = e * rho * c / 1000
            ct_layer = (e * rho * c) / 1000.0
            total_heat_capacity_kj_m2_k += ct_layer

            layer_breakdown.append({
                "material": lay.get("material", "Camada"),
                "thickness_cm": round(e * 100.0, 1),
                "resistance_m2_k_w": round(r_layer, 3),
                "heat_capacity_kj_m2_k": round(ct_layer, 1),
            })

        total_r = rse_m2_k_w + total_layers_resistance + rsi_m2_k_w
        # Transmitância Térmica U = 1 / R_T (W/(m2.K))
        u_value_w_m2_k = 1.0 / total_r

        # Critérios da NBR 15220-3 para ZB3:
        # Parede: U <= 2.50 W/(m2.K) e Ct >= 130 kJ/(m2.K)
        max_u_allowed = 2.50
        min_ct_allowed = 130.0

        is_u_compliant = u_value_w_m2_k <= max_u_allowed
        is_ct_compliant = total_heat_capacity_kj_m2_k >= min_ct_allowed
        is_nbr15220_compliant = is_u_compliant and is_ct_compliant

        # Atraso térmico aproximado (Phi em horas): Phi ~ 1.38 * R * sqrt(Ct)
        thermal_lag_hours = min(14.0, 1.38 * total_r * math.sqrt(max(1.0, total_heat_capacity_kj_m2_k)))

        return {
            "entity_type": "ThermalComfortReport",
            "parameters": {
                "bioclimatic_zone": target_bioclimatic_zone,
                "rsi_m2_k_w": rsi_m2_k_w,
                "rse_m2_k_w": rse_m2_k_w,
            },
            "thermal_metrics": {
                "total_thickness_cm": round(total_thickness_m * 100.0, 1),
                "total_surface_weight_kg_m2": round(total_weight_kg_m2, 1),
                "total_thermal_resistance_m2_k_w": round(total_r, 3),
                "transmittance_u_w_m2_k": round(u_value_w_m2_k, 2),
                "max_allowed_u_w_m2_k": max_u_allowed,
                "heat_capacity_ct_kj_m2_k": round(total_heat_capacity_kj_m2_k, 1),
                "min_allowed_ct_kj_m2_k": min_ct_allowed,
                "thermal_lag_hours": round(thermal_lag_hours, 1),
                "is_compliant_nbr15220": is_nbr15220_compliant,
                "efficiency_label": "NÍVEL A (PBE EDIFICA)" if is_nbr15220_compliant and u_value_w_m2_k < 2.0 else "NÍVEL B / CONFORME",
            },
            "layers": layer_breakdown,
            "status": "COMPUTED",
        }
