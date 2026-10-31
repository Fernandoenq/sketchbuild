"""
Motor de Avaliação do Ciclo de Vida (ACV / LCA) e Energia Embutida ISO 14040 (Life Cycle Assessment - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 145).
Quantificação analítica de pegada de carbono incorporada (Cradle-to-Gate), energia primária não-renovável (MJ),
potencial de aquecimento global (GWP em kg CO2e/m2 de área construída) e conformidade com certificações ambientais LEED/AQUA.
"""

from __future__ import annotations

from typing import Any


class LifeCycleAssessmentEngine:
    """Motor analítico de cálculo de ciclo de vida e emissões de carbono em Python puro."""

    @staticmethod
    def calculate_lca(
        gross_floor_area_m2: float = 850.0,
        building_lifespan_years: int = 50,
        materials_inventory: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Calcula as emissões de carbono de berço ao portão (Módulos A1-A3 da EN 15978):
        GWP_total = sum(massa_i * fator_emissao_i)
        """
        if not materials_inventory:
            materials_inventory = [
                {"material": "Concreto Usinado C30", "category": "ESTRUTURA", "quantity_m3": 280.0, "density_kg_m3": 2400.0, "emission_factor_kgco2_kg": 0.130, "embodied_energy_mj_kg": 1.10},
                {"material": "Aço Armadura CA-50", "category": "ESTRUTURA", "quantity_kg": 24000.0, "density_kg_m3": 7850.0, "emission_factor_kgco2_kg": 1.450, "embodied_energy_mj_kg": 25.0},
                {"material": "Alvenaria Bloco Cerâmico", "category": "VEDAÇÃO", "quantity_m2": 1100.0, "weight_kg_m2": 85.0, "emission_factor_kgco2_kg": 0.220, "embodied_energy_mj_kg": 2.50},
                {"material": "Vidro Laminado 8mm", "category": "ESQUADRIAS", "quantity_m2": 140.0, "weight_kg_m2": 20.0, "emission_factor_kgco2_kg": 1.150, "embodied_energy_mj_kg": 15.0},
                {"material": "Piso Porcelanato", "category": "ACABAMENTO", "quantity_m2": 650.0, "weight_kg_m2": 22.0, "emission_factor_kgco2_kg": 0.580, "embodied_energy_mj_kg": 8.0},
            ]

        total_embodied_carbon_kgco2e = 0.0
        total_embodied_energy_mj = 0.0
        breakdown = []

        for item in materials_inventory:
            # Determina a massa total em kg
            if "quantity_kg" in item:
                mass_kg = item["quantity_kg"]
            elif "quantity_m3" in item:
                mass_kg = item["quantity_m3"] * item.get("density_kg_m3", 2000.0)
            elif "quantity_m2" in item and "weight_kg_m2" in item:
                mass_kg = item["quantity_m2"] * item["weight_kg_m2"]
            else:
                mass_kg = 1000.0

            ef_carbon = item.get("emission_factor_kgco2_kg", 0.20)
            ef_energy = item.get("embodied_energy_mj_kg", 2.0)

            carbon_kg = mass_kg * ef_carbon
            energy_mj = mass_kg * ef_energy

            total_embodied_carbon_kgco2e += carbon_kg
            total_embodied_energy_mj += energy_mj

            breakdown.append({
                "material": item["material"],
                "category": item["category"],
                "total_mass_tons": round(mass_kg / 1000.0, 2),
                "embodied_carbon_tons_co2e": round(carbon_kg / 1000.0, 2),
                "embodied_energy_gigajoules": round(energy_mj / 1000.0, 2),
            })

        # Emissões específicas normalizadas por m2 de área construída:
        carbon_intensity_kgco2e_m2 = round(total_embodied_carbon_kgco2e / max(1.0, gross_floor_area_m2), 1)
        energy_intensity_mj_m2 = round(total_embodied_energy_mj / max(1.0, gross_floor_area_m2), 1)

        # Benchmark de sustentabilidade (Green Building Council / LEED v4):
        # Excelente: < 350 kg CO2e/m2, Bom: 350 - 550 kg CO2e/m2, Típico: > 550 kg CO2e/m2
        if carbon_intensity_kgco2e_m2 < 350.0:
            leed_score = "EXCELENTE (LEED PLATINUM CANDIDATE)"
        elif carbon_intensity_kgco2e_m2 <= 550.0:
            leed_score = "BOM (LEED GOLD / SILVER)"
        else:
            leed_score = "PADRÃO DE MERCADO"

        return {
            "entity_type": "LifeCycleAssessmentReport",
            "parameters": {
                "gross_floor_area_m2": gross_floor_area_m2,
                "building_lifespan_years": building_lifespan_years,
                "materials_count": len(materials_inventory),
            },
            "lca_metrics": {
                "total_embodied_carbon_tons_co2e": round(total_embodied_carbon_kgco2e / 1000.0, 2),
                "carbon_intensity_kgco2e_m2": carbon_intensity_kgco2e_m2,
                "total_embodied_energy_gj": round(total_embodied_energy_mj / 1000.0, 1),
                "energy_intensity_mj_m2": energy_intensity_mj_m2,
                "environmental_performance_rating": leed_score,
                "status_label": f"ACV CONCLUÍDA: {carbon_intensity_kgco2e_m2} kg CO2e/m2 ({round(total_embodied_carbon_kgco2e/1000, 1)} t CO2e total - {leed_score})",
            },
            "materials_breakdown": breakdown,
            "status": "COMPUTED",
        }
