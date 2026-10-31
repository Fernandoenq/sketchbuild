"""
Calculador de Pegada de Carbono e Sustentabilidade de Madeira (Zero DLL).

Calcula o balanço de sequestro e emissões de carbono de estruturas lúdicas:
1. Carbono sequestrado e biogenicamente armazenado no Eucalipto de reflorestamento.
2. Emissões embutidas de fabricação (ferragens de aço, PEAD rotomoldado e tintas/resinas).
3. Emissões logísticas de transporte rodoviário da fábrica ao local de instalação.
4. Balanço Líquido de Carbono (Carbon Negative Badge) e árvores equivalentes.
"""

from typing import Dict, Any, List


class CarbonFootprintCalculator:
    """Motor de cálculo de pegada de carbono e análise de ciclo de vida (LCA)."""

    # Fatores de emissão / sequestro (kg CO2e por unidade)
    CO2_SEQUESTERED_PER_M3_WOOD: float = 950.0   # 1 m³ de madeira estoca ~950 kg CO2e
    CO2_EMISSION_PER_KG_STEEL: float = 2.10      # 1 kg de aço emite ~2.1 kg CO2e
    CO2_EMISSION_PER_KG_PLASTIC: float = 1.95    # 1 kg de PEAD emite ~1.95 kg CO2e
    CO2_EMISSION_PER_TON_KM: float = 0.12        # Transporte a diesel: 0.12 kg CO2 / ton.km
    CO2_TREE_YEAR_ABSORPTION_KG: float = 22.0    # 1 árvore média absorve ~22 kg CO2/ano

    @classmethod
    def calculate_footprint(
        cls,
        timber_volume_m3: float = 2.80,
        steel_weight_kg: float = 95.0,
        plastic_weight_kg: float = 45.0,
        transport_distance_km: float = 350.0
    ) -> Dict[str, Any]:
        """
        Calcula o balanço completo de carbono do equipamento.
        """
        # 1. Carbono Sequestrado pela Madeira (positivo / absorvido da atmosfera)
        co2_sequestered_kg = timber_volume_m3 * cls.CO2_SEQUESTERED_PER_M3_WOOD

        # 2. Emissões dos materiais e processos
        co2_steel_kg = steel_weight_kg * cls.CO2_EMISSION_PER_KG_STEEL
        co2_plastic_kg = plastic_weight_kg * cls.CO2_EMISSION_PER_KG_PLASTIC

        total_weight_ton = (timber_volume_m3 * 0.75) + (steel_weight_kg / 1000.0) + (plastic_weight_kg / 1000.0)
        co2_transport_kg = total_weight_ton * transport_distance_km * cls.CO2_EMISSION_PER_TON_KM

        # Energia fabril e usinagem (aprox 45 kWh ~ 18 kg CO2)
        co2_manufacturing_kg = 18.0

        total_emissions_kg = co2_steel_kg + co2_plastic_kg + co2_transport_kg + co2_manufacturing_kg

        # 3. Balanço Líquido de Carbono (Sequestrado - Emitido)
        net_carbon_balance_kg = co2_sequestered_kg - total_emissions_kg
        is_carbon_negative = net_carbon_balance_kg > 0.0

        # Equivalência ecológica
        equivalent_trees_years = net_carbon_balance_kg / cls.CO2_TREE_YEAR_ABSORPTION_KG

        return {
            "entity_type": "CarbonFootprintAnalysis",
            "timber_volume_m3": round(timber_volume_m3, 3),
            "co2_sequestered_kg": round(co2_sequestered_kg, 1),
            "steel_weight_kg": round(steel_weight_kg, 1),
            "co2_steel_emissions_kg": round(co2_steel_kg, 1),
            "plastic_weight_kg": round(plastic_weight_kg, 1),
            "co2_plastic_emissions_kg": round(co2_plastic_kg, 1),
            "transport_distance_km": transport_distance_km,
            "co2_transport_emissions_kg": round(co2_transport_kg, 1),
            "total_emissions_kg": round(total_emissions_kg, 1),
            "net_carbon_balance_kg": round(net_carbon_balance_kg, 1),
            "is_carbon_negative": is_carbon_negative,
            "equivalent_trees_planted_years": round(max(0.0, equivalent_trees_years), 1),
            "sustainability_badge": "PRODUTO CLIMA-POSITIVO (CARBONO NEGATIVO)" if is_carbon_negative else "NEUTRO EM CARBONO",
            "status": f"RETÉM {net_carbon_balance_kg:.0f} kg LÍQUIDOS DE CO2 DA ATMOSFERA"
        }
