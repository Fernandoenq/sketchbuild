"""
SketchBuild - Motor de Fita de Borda para Marcenaria Sob Medida (Zero DLL / Pure Python)
Frente Marcenaria Avançada: Gestão de Bordas NBR 14810 e Plano de Coladeira de Borda

Implementa:
1. Aplicação e mapeamento de fitas de borda nas 4 faces de painéis de marcenaria (Top, Bottom, Left, Right).
2. Cálculo de desconto dimensional para fita espessa (fitas de 1.0mm e 2.0mm abatem das dimensões de corte bruto).
3. Cálculo métrico linear de consumo com tolerância de refilo e destopo nas pontas (overhead de 10%).
4. Resumo de custos e metragem agrupados por tipo/cor/espessura de fita PVC/ABS.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class FurnitureEdgeBandingEngine:
    """Motor analítico de cálculo e dimensionamento de fitas de borda para móveis planejados."""

    DEFAULT_OVERHEAD_RATIO: float = 0.10  # 10% de folga para destopo e refilo em coladeira

    @classmethod
    def calculate_panel_edges(
        cls,
        panel_id: str,
        name: str,
        width_mm: float,
        height_mm: float,
        thickness_mm: float,
        edges: Dict[str, Dict[str, Any]],
        overhead_ratio: float = DEFAULT_OVERHEAD_RATIO,
    ) -> Dict[str, Any]:
        """
        Calcula as fitas de borda de um painel individual.

        Args:
            panel_id: Identificador único do painel (ex: "P01").
            name: Descrição (ex: "Lateral Esquerda", "Porta Superior").
            width_mm: Largura final do painel acabado em milímetros.
            height_mm: Altura final do painel acabado em milímetros.
            thickness_mm: Espessura da chapa MDF em mm (ex: 15, 18, 25).
            edges: Dicionário com as 4 bordas: "top", "bottom", "left", "right".
                   Cada borda pode ter:
                   - "enabled": bool (se tem fita)
                   - "thickness_mm": float (espessura da fita, ex: 0.45, 1.0, 2.0)
                   - "material": str (ex: "PVC Branco TX")
                   - "cost_per_meter": float (opcional, custo por metro linear)
            overhead_ratio: Percentual de folga técnica para refilo (padrão 0.10 = 10%).

        Returns:
            Dicionário com dimensões nominais, dimensões brutas de corte, metragem e custos.
        """
        # Dimensões de corte cru começam iguais às nominais acabadas
        cut_width_mm = width_mm
        cut_height_mm = height_mm

        edge_details: Dict[str, Any] = {}
        total_length_m = 0.0
        total_length_with_overhead_m = 0.0
        total_cost = 0.0

        edge_lengths = {
            "top": width_mm,
            "bottom": width_mm,
            "left": height_mm,
            "right": height_mm,
        }

        # Descontos de corte: fita com espessura >= 0.8mm deve ser abatida da chapa crua
        for edge_name, edge_len_mm in edge_lengths.items():
            cfg = edges.get(edge_name, {})
            is_enabled = bool(cfg.get("enabled", False))
            edge_thick = float(cfg.get("thickness_mm", 0.45))
            material = str(cfg.get("material", "PVC Padrão"))
            cost_per_m = float(cfg.get("cost_per_meter", 0.0))

            linear_meters = (edge_len_mm / 1000.0) if is_enabled else 0.0
            linear_with_overhead = linear_meters * (1.0 + overhead_ratio)
            cost = linear_with_overhead * cost_per_m

            if is_enabled:
                total_length_m += linear_meters
                total_length_with_overhead_m += linear_with_overhead
                total_cost += cost

                # Desconto analítico dimensional se a fita for espessa
                if edge_thick >= 0.8:
                    if edge_name in ("top", "bottom"):
                        cut_height_mm -= edge_thick
                    elif edge_name in ("left", "right"):
                        cut_width_mm -= edge_thick

            edge_details[edge_name] = {
                "enabled": is_enabled,
                "thickness_mm": edge_thick if is_enabled else 0.0,
                "material": material if is_enabled else "Nenhum",
                "length_mm": edge_len_mm,
                "linear_meters": round(linear_meters, 4),
                "linear_with_overhead_m": round(linear_with_overhead, 4),
                "cost": round(cost, 2),
            }

        return {
            "panel_id": panel_id,
            "name": name,
            "thickness_mm": thickness_mm,
            "finished_dimensions_mm": {
                "width": round(width_mm, 2),
                "height": round(height_mm, 2),
            },
            "raw_cut_dimensions_mm": {
                "width": round(cut_width_mm, 2),
                "height": round(cut_height_mm, 2),
            },
            "edges": edge_details,
            "summary": {
                "total_linear_meters": round(total_length_m, 4),
                "total_with_overhead_meters": round(total_length_with_overhead_m, 4),
                "total_cost": round(total_cost, 2),
            },
        }

    @classmethod
    def process_furniture_cabinet(
        cls,
        cabinet_name: str,
        panels: List[Dict[str, Any]],
        overhead_ratio: float = DEFAULT_OVERHEAD_RATIO,
    ) -> Dict[str, Any]:
        """
        Processa todos os painéis de um móvel completo (ex: armário de cozinha, roupeiro).
        Gera relatório consolidado de consumo e lista de corte.
        """
        processed_panels: List[Dict[str, Any]] = []
        material_summary: Dict[str, Dict[str, Any]] = {}
        grand_total_linear_m = 0.0
        grand_total_with_overhead_m = 0.0
        grand_total_cost = 0.0

        for p in panels:
            p_id = str(p.get("panel_id", f"P{len(processed_panels) + 1}"))
            p_name = str(p.get("name", "Peça Sem Nome"))
            w = float(p.get("width_mm", 0.0))
            h = float(p.get("height_mm", 0.0))
            th = float(p.get("thickness_mm", 15.0))
            ed = p.get("edges", {})

            result = cls.calculate_panel_edges(
                panel_id=p_id,
                name=p_name,
                width_mm=w,
                height_mm=h,
                thickness_mm=th,
                edges=ed,
                overhead_ratio=overhead_ratio,
            )
            processed_panels.append(result)

            grand_total_linear_m += result["summary"]["total_linear_meters"]
            grand_total_with_overhead_m += result["summary"]["total_with_overhead_meters"]
            grand_total_cost += result["summary"]["total_cost"]

            # Agregação por material de fita
            for edge_info in result["edges"].values():
                if not edge_info["enabled"]:
                    continue
                mat_key = f"{edge_info['material']} ({edge_info['thickness_mm']}mm)"
                if mat_key not in material_summary:
                    material_summary[mat_key] = {
                        "material": edge_info["material"],
                        "thickness_mm": edge_info["thickness_mm"],
                        "total_linear_m": 0.0,
                        "total_with_overhead_m": 0.0,
                        "total_cost": 0.0,
                    }
                material_summary[mat_key]["total_linear_m"] += edge_info["linear_meters"]
                material_summary[mat_key]["total_with_overhead_m"] += edge_info["linear_with_overhead_m"]
                material_summary[mat_key]["total_cost"] += edge_info["cost"]

        # Arredondamentos de sumário
        for k in material_summary:
            material_summary[k]["total_linear_m"] = round(material_summary[k]["total_linear_m"], 3)
            material_summary[k]["total_with_overhead_m"] = round(material_summary[k]["total_with_overhead_m"], 3)
            material_summary[k]["total_cost"] = round(material_summary[k]["total_cost"], 2)

        return {
            "status": "success",
            "cabinet_name": cabinet_name,
            "panel_count": len(processed_panels),
            "panels": processed_panels,
            "materials_breakdown": material_summary,
            "totals": {
                "net_linear_meters": round(grand_total_linear_m, 3),
                "gross_with_overhead_meters": round(grand_total_with_overhead_m, 3),
                "total_edge_banding_cost": round(grand_total_cost, 2),
            },
        }
