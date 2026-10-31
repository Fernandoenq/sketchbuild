"""
SketchBuild - Sequenciador de Montagem Passo a Passo e Manual Técnico 3D
(Frente 26 - Zero DLL / Pure Python)

Gera a sequência ordenada de montagem fabril para o Desmontador Parkelô,
agrupando componentes por cota de nível vertical (Z), tipologia estrutural
e vinculando os kits de fixação necessários para cada etapa.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional


class AssemblySequencer:
    """Calculador analítico de etapas sequenciais de montagem de playgrounds e marcenaria."""

    CATEGORIA_ORDEM = {
        "fundacao": 1,
        "estruturas": 2,
        "colunas": 2,
        "assoalhos": 3,
        "decks": 3,
        "paineis": 3,
        "travessas": 3,
        "escadas": 4,
        "rampas": 4,
        "passarelas": 4,
        "tubos": 5,
        "escorregadores": 5,
        "telhados": 5,
        "brinquedos": 5,
        "acabamentos": 6,
        "outros": 4,
    }

    @classmethod
    def _categorizar_peca(cls, nome: str) -> str:
        n = nome.upper()
        if any(k in n for k in ["SAPATA", "CHUMBADOR", "BASE", "PE"]):
            return "fundacao"
        if any(k in n for k in ["COLUNA", "POSTE", "PILAR", "VIGA"]):
            return "estruturas"
        if any(k in n for k in ["ASSOALHO", "DECK", "PAINEL", "TRAVESSA", "PISO"]):
            return "assoalhos"
        if any(k in n for k in ["ESCADA", "RAMPA", "PASSARELA", "CORDA", "ESCALADA"]):
            return "escadas"
        if any(k in n for k in ["TUBO", "ESCORREGADOR", "TELHADO", "CURVA", "PONTEIRA"]):
            return "tubos"
        return "outros"

    @classmethod
    def generate_steps(cls, scene_dto: Dict[str, Any]) -> Dict[str, Any]:
        """Gera a linha do tempo de montagem passo a passo."""
        instances = scene_dto.get("instances", [])
        definitions = {d.get("definition_id"): d for d in scene_dto.get("definitions", [])}

        if not instances:
            return {"steps": [], "total_steps": 0, "total_instances": 0}

        # 1. Enriquecer cada instância com altura Z e categoria
        parsed_items = []
        for inst in instances:
            iid = inst.get("instance_id")
            name = inst.get("name") or "Componente"
            did = inst.get("definition_id")
            d_info = definitions.get(did, {})
            def_name = d_info.get("name", name)

            # Matriz 4x4: translacao em Z
            mat = inst.get("transform", [])
            tz_m = 0.0
            if len(mat) >= 16:
                # Na convenção interna da API, mat[14] é Z em polegadas, convertemos para metros
                tz_m = (mat[14] * 0.0254) if abs(mat[14]) > 1e-4 else 0.0

            cat = cls._categorizar_peca(def_name)
            ordem_cat = cls.CATEGORIA_ORDEM.get(cat, 4)

            parsed_items.append({
                "instance_id": iid,
                "name": def_name,
                "category": cat,
                "category_order": ordem_cat,
                "z_m": round(tz_m, 3),
            })

        # 2. Agrupa por etapa lógica
        # Ordena por: ordem da categoria e depois por altura Z crescente
        parsed_items.sort(key=lambda x: (x["category_order"], x["z_m"]))

        stages_map: Dict[str, List[Dict[str, Any]]] = {}
        for it in parsed_items:
            cat = it["category"]
            if cat not in stages_map:
                stages_map[cat] = []
            stages_map[cat].append(it)

        # Monta os passos finais estruturados
        steps = []
        step_idx = 1

        stage_titles = {
            "fundacao": ("Bases e Sapatas de Fixação", "Posicionar e nivelar sapatas e chumbadores no solo/piso."),
            "estruturas": ("Estrutura Principal e Colunas", "Erigir as colunas principais e travar as vigas de sustentação."),
            "assoalhos": ("Assoalhos, Decks e Travessas", "Fixar os módulos de assoalho e travessas de fechamento estrutural."),
            "escadas": ("Módulos de Acesso (Escadas e Passarelas)", "Instalar escadas, pontes e módulos de circulação com parafusos passantes."),
            "tubos": ("Brinquedos, Tubos e Escorregadores", "Encaixar e prender os tubos rotomoldados, curvas e escorregadores."),
            "outros": ("Complementos e Acabamentos", "Finalizar com tampões de segurança, ponteiras e verificação de torque."),
        }

        # Segue a ordem natural de montagem
        for cat_key in ["fundacao", "estruturas", "assoalhos", "escadas", "tubos", "outros"]:
            items_in_stage = stages_map.get(cat_key, [])
            if not items_in_stage:
                continue

            title, desc = stage_titles.get(cat_key, (cat_key.capitalize(), "Instalação dos componentes."))

            # Contagem de peças nesta etapa
            parts_summary = {}
            for item in items_in_stage:
                pname = item["name"]
                parts_summary[pname] = parts_summary.get(pname, 0) + 1

            parts_list = [{"name": k, "count": v} for k, v in parts_summary.items()]
            total_stage_parts = sum(parts_summary.values())
            hardware_needed = total_stage_parts * 4  # 4 fixadores padrão por peça

            steps.append({
                "step_number": step_idx,
                "title": f"Etapa {step_idx}: {title}",
                "category": cat_key,
                "instruction": desc,
                "instance_ids": [it["instance_id"] for it in items_in_stage],
                "parts_count": total_stage_parts,
                "parts": parts_list,
                "hardware_estimate": f"{hardware_needed} Parafusos Inox c/ Porca Travante",
            })
            step_idx += 1

        return {
            "steps": steps,
            "total_steps": len(steps),
            "total_instances": len(parsed_items),
        }

    @classmethod
    def generate_html_manual(cls, scene_dto: Dict[str, Any], project_name: str = "Playground Parkelô") -> str:
        """Gera um manual visual em HTML autônomo e imprimível para a equipe de montagem."""
        data = cls.generate_steps(scene_dto)
        steps = data["steps"]

        html = [
            '<!DOCTYPE html>',
            '<html lang="pt-br">',
            '<head>',
            '  <meta charset="UTF-8">',
            f'  <title>Manual de Montagem - {project_name}</title>',
            '  <style>',
            '    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #F4F6F9; color: #2D3748; margin: 0; padding: 24px; }',
            '    .container { max-width: 900px; margin: 0 auto; background: #FFFFFF; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); overflow: hidden; }',
            '    .header { background: #1B365D; color: #FFFFFF; padding: 24px; text-align: center; }',
            '    .header h1 { margin: 0 0 8px 0; font-size: 24px; }',
            '    .header p { margin: 0; opacity: 0.85; font-size: 13px; }',
            '    .step-card { border-bottom: 1px solid #E2E8F0; padding: 20px 24px; }',
            '    .step-card:last-child { border-bottom: none; }',
            '    .step-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }',
            '    .step-title { font-size: 16px; font-weight: 700; color: #1B365D; }',
            '    .badge { background: #EBF8FF; color: #2B6CB0; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }',
            '    .instruction { font-size: 13px; color: #4A5568; margin-bottom: 12px; line-height: 1.5; }',
            '    .parts-table { width: 100%; border-collapse: collapse; font-size: 12px; margin-bottom: 10px; }',
            '    .parts-table th, .parts-table td { border: 1px solid #E2E8F0; padding: 8px 12px; text-align: left; }',
            '    .parts-table th { background: #F7FAFC; color: #4A5568; font-weight: 600; }',
            '    .hardware-info { background: #FEFCBF; border-left: 4px solid #D69E2E; padding: 8px 12px; font-size: 12px; color: #744210; border-radius: 2px; }',
            '    .footer { text-align: center; padding: 16px; font-size: 11px; color: #A0AEC0; background: #F7FAFC; }',
            '  </style>',
            '</head>',
            '<body>',
            '  <div class="container">',
            '    <div class="header">',
            f'      <h1>Manual Técnico de Montagem 3D</h1>',
            f'      <p>{project_name} &bull; Total de Etapas: {data["total_steps"]} &bull; Engenharia Parkelô</p>',
            '    </div>',
        ]

        for s in steps:
            html.append('    <div class="step-card">')
            html.append('      <div class="step-header">')
            html.append(f'        <span class="step-title">{s["title"]}</span>')
            html.append(f'        <span class="badge">{s["parts_count"]} peças</span>')
            html.append('      </div>')
            html.append(f'      <p class="instruction"><strong>Instrução:</strong> {s["instruction"]}</p>')
            html.append('      <table class="parts-table">')
            html.append('        <thead><tr><th>Componente / Peça</th><th style="width: 80px; text-align: center;">Quantidade</th></tr></thead>')
            html.append('        <tbody>')
            for p in s["parts"]:
                html.append(f'          <tr><td>{p["name"]}</td><td style="text-align: center;">{p["count"]}</td></tr>')
            html.append('        </tbody>')
            html.append('      </table>')
            html.append(f'      <div class="hardware-info"><strong>Fixadores Necessários:</strong> {s["hardware_estimate"]}</div>')
            html.append('    </div>')

        html.append('    <div class="footer">Gerado automaticamente por SketchBuild &bull; Desenvolvido por Fernando Filho</div>')
        html.append('  </div>')
        html.append('</body>')
        html.append('</html>')

        return '\n'.join(html)
