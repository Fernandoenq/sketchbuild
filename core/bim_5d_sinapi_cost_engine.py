"""
Motor de Orçamento Paramétrico e Composição de Custos SINAPI (BIM 5D / SINAPI - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 115).
Mapeamento de geometria 3D para o banco oficial de custos SINAPI (Caixa Econômica Federal),
aplicação de BDI, cálculo de custos diretos/indiretos e ordenação em Curva ABC (80/15/5%).
"""

from __future__ import annotations

import math
from typing import Any


class Bim5dSinapiCostEngine:
    """Motor analítico de orçamentação BIM 5D e curva ABC em Python puro."""

    # Banco analítico de composições representativas SINAPI (valores referenciais médios BRL)
    SINAPI_DATABASE = {
        "concreto_armado_fck25": {
            "sinapi_code": "94970",
            "description": "Concreto Fck=25MPa, usinado, bombeado, lançado e adensado",
            "unit": "m3",
            "unit_cost_brl": 485.50,
        },
        "alvenaria_bloco_ceramico": {
            "sinapi_code": "87529",
            "description": "Alvenaria de vedação com bloco cerâmico furado 9x19x19cm, e=9cm",
            "unit": "m2",
            "unit_cost_brl": 68.20,
        },
        "reboco_argamassa": {
            "sinapi_code": "87775",
            "description": "Emboço/reboco de argamassa traço 1:2:8, espessura 20mm",
            "unit": "m2",
            "unit_cost_brl": 34.50,
        },
        "pintura_acrilica": {
            "sinapi_code": "88489",
            "description": "Aplicação de pintura acrílica fosca duas demãos sobre paredes",
            "unit": "m2",
            "unit_cost_brl": 22.80,
        },
        "piso_porcelanato": {
            "sinapi_code": "87251",
            "description": "Revestimento cerâmico/porcelanato 60x60cm assentado com argamassa AC-II",
            "unit": "m2",
            "unit_cost_brl": 89.40,
        },
        "estrutura_metalica_aco": {
            "sinapi_code": "100980",
            "description": "Fornecimento e montagem de estrutura metálica em perfis de aço",
            "unit": "kg",
            "unit_cost_brl": 16.50,
        },
        "madeira_eucalipto_tratado": {
            "sinapi_code": "92760",
            "description": "Armação e montagem de estrutura de madeira roliça tratada em autoclave",
            "unit": "m3",
            "unit_cost_brl": 1450.00,
        },
    }

    @staticmethod
    def calculate_5d_budget(
        elements: list[dict[str, Any]] | None = None,
        bdi_percent: float = 24.50,  # Bonificação e Despesas Indiretas padrão Acórdão TCU
        social_charges_percent: float = 84.0,  # Encargos sociais desonerados/não desonerados
    ) -> dict[str, Any]:
        """
        Calcula o custo direto, BDI, custo total e gera a classificação da Curva ABC.
        Cada element: {'name': str, 'category': str, 'quantity': float, 'unit': str}
        """
        if not elements:
            # Amostra de edifício modelo padrão
            elements = [
                {"name": "Vigas e Pilares Concreto", "category": "concreto_armado_fck25", "quantity": 18.5, "unit": "m3"},
                {"name": "Paredes de Alvenaria", "category": "alvenaria_bloco_ceramico", "quantity": 140.0, "unit": "m2"},
                {"name": "Reboco e Emboço Fachadas", "category": "reboco_argamassa", "quantity": 280.0, "unit": "m2"},
                {"name": "Pintura Externa Acrílica", "category": "pintura_acrilica", "quantity": 280.0, "unit": "m2"},
                {"name": "Piso Interno", "category": "piso_porcelanato", "quantity": 75.0, "unit": "m2"},
                {"name": "Perfis Cobertura Metálica", "category": "estrutura_metalica_aco", "quantity": 650.0, "unit": "kg"},
            ]

        budget_items = []
        total_direct_cost_brl = 0.0

        for el in elements:
            cat = el.get("category", "alvenaria_bloco_ceramico").lower()
            qty = max(0.01, float(el.get("quantity", 1.0)))
            sinapi_info = Bim5dSinapiCostEngine.SINAPI_DATABASE.get(
                cat,
                {
                    "sinapi_code": "GEN-01",
                    "description": el.get("name", "Serviço Genérico"),
                    "unit": el.get("unit", "un"),
                    "unit_cost_brl": 50.0,
                }
            )

            unit_price = sinapi_info["unit_cost_brl"]
            total_item_cost = qty * unit_price
            total_direct_cost_brl += total_item_cost

            budget_items.append({
                "item_name": el.get("name", sinapi_info["description"]),
                "sinapi_code": sinapi_info["sinapi_code"],
                "unit": sinapi_info["unit"],
                "quantity": round(qty, 2),
                "unit_cost_brl": round(unit_price, 2),
                "total_direct_cost_brl": round(total_item_cost, 2),
            })

        # Ordenação decrescente para cálculo da Curva ABC
        budget_items.sort(key=lambda x: x["total_direct_cost_brl"], reverse=True)

        # Cálculo acumulado da Curva ABC (Classe A: até 80%, Classe B: 80% a 95%, Classe C: 95% a 100%)
        accumulated_cost = 0.0
        for item in budget_items:
            accumulated_cost += item["total_direct_cost_brl"]
            accumulated_percent = (accumulated_cost / max(0.01, total_direct_cost_brl)) * 100.0
            item["accumulated_percent"] = round(accumulated_percent, 1)

            if accumulated_percent <= 80.0:
                item["abc_class"] = "A"
            elif accumulated_percent <= 95.0:
                item["abc_class"] = "B"
            else:
                item["abc_class"] = "C"

        # BDI e Custo Global
        bdi_factor = 1.0 + (bdi_percent / 100.0)
        total_indirect_cost_brl = total_direct_cost_brl * (bdi_percent / 100.0)
        total_budget_with_bdi_brl = total_direct_cost_brl * bdi_factor

        return {
            "entity_type": "Bim5dSinapiReport",
            "financial_summary": {
                "total_direct_cost_brl": round(total_direct_cost_brl, 2),
                "bdi_percent": bdi_percent,
                "bdi_amount_brl": round(total_indirect_cost_brl, 2),
                "total_budget_with_bdi_brl": round(total_budget_with_bdi_brl, 2),
                "currency": "BRL",
                "database_reference": "SINAPI / Caixa Econômica Federal",
            },
            "items_count": len(budget_items),
            "abc_classification_summary": {
                "class_a_items_count": sum(1 for i in budget_items if i["abc_class"] == "A"),
                "class_b_items_count": sum(1 for i in budget_items if i["abc_class"] == "B"),
                "class_c_items_count": sum(1 for i in budget_items if i["abc_class"] == "C"),
            },
            "items": budget_items,
            "status": "COMPUTED",
        }
