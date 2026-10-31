"""
Motor Oficial de Geração de Relatórios do SketchUp (Generate Report - Zero DLL).

Implementa a engenharia reversa do recurso 'Gerar Relatório' do SketchUp Pro:
(Arquivo -> Gerar Relatório)
1. Escopo de Relatório:
   - Todo o Modelo ('entire_model')
   - Apenas Seleção Atual ('selection_only')
2. Agregação e Quantificação:
   - Agrupamento por Definição de Componente ou detalhamento linha a linha por Instância.
   - Cálculo de Quantidade, Volume Total (m³), Área de Superfície (m²).
   - Dimensões do envelope métrico (Largura X, Comprimento Y, Altura Z).
   - Extração de Materiais, Etiquetas/Tags, Classificações IFC e Atributos Dinâmicos.
3. Formatos de Saída:
   - Tabela estruturada (JSON) para visualização e impressão em tela.
   - Formato CSV padrão da indústria (RFC 4180) para exportação para Excel e LibreOffice.
"""

import io
import csv
from typing import List, Dict, Any, Optional


class GenerateReportEngine:
    """Motor de geração de relatórios de quantitativos e metadados do SketchUp Pro."""

    DEFAULT_COLUMNS = [
        "Entity Name", "Definition Name", "Quantity", "Tag",
        "Width (m)", "Depth (m)", "Height (m)", "Area (m2)", "Volume (m3)",
        "Material", "IFC Class"
    ]

    @classmethod
    def generate_report(
        cls,
        instances: List[Dict[str, Any]],
        scope: str = "entire_model",
        group_by_definition: bool = True,
        selected_instance_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Gera relatório estruturado e CSV a partir da lista de instâncias da cena.
        """
        scope_clean = scope.lower().strip()
        filtered_instances = []

        # 1. Filtro por escopo
        if scope_clean == "selection_only" and selected_instance_ids:
            selected_set = set(selected_instance_ids)
            filtered_instances = [inst for inst in instances if inst.get("instance_id", inst.get("id")) in selected_set]
        else:
            filtered_instances = list(instances)

        # 2. Agregação por definição ou listagem individual
        report_rows = []
        total_quantity = 0
        total_volume_m3 = 0.0
        total_area_m2 = 0.0

        if group_by_definition:
            grouped: Dict[str, Dict[str, Any]] = {}
            for inst in filtered_instances:
                def_name = inst.get("definition_name", inst.get("name", "Componente Sem Nome"))
                vol = float(inst.get("volume_m3", inst.get("volume", 0.0)))
                area = float(inst.get("area_m2", inst.get("area", 0.0)))
                tag = inst.get("tag", inst.get("layer", "Layer0"))
                mat = inst.get("material", "Padrão")
                ifc = inst.get("ifc_class", inst.get("classification", {}).get("ifc_class", "Não classificado"))
                bounds = inst.get("bounds", inst.get("size", (1.0, 1.0, 1.0)))
                w = bounds[0] if isinstance(bounds, (list, tuple)) else bounds.get("width", 1.0)
                d = bounds[1] if isinstance(bounds, (list, tuple)) else bounds.get("depth", 1.0)
                h = bounds[2] if isinstance(bounds, (list, tuple)) else bounds.get("height", 1.0)

                if def_name not in grouped:
                    grouped[def_name] = {
                        "Entity Name": def_name,
                        "Definition Name": def_name,
                        "Quantity": 0,
                        "Tag": tag,
                        "Width (m)": round(w, 3),
                        "Depth (m)": round(d, 3),
                        "Height (m)": round(h, 3),
                        "Area (m2)": 0.0,
                        "Volume (m3)": 0.0,
                        "Material": mat,
                        "IFC Class": ifc,
                        "Instances": []
                    }

                grouped[def_name]["Quantity"] += 1
                grouped[def_name]["Area (m2)"] = round(grouped[def_name]["Area (m2)"] + area, 4)
                grouped[def_name]["Volume (m3)"] = round(grouped[def_name]["Volume (m3)"] + vol, 4)
                grouped[def_name]["Instances"].append(inst.get("instance_id", inst.get("id", "")))

                total_quantity += 1
                total_volume_m3 += vol
                total_area_m2 += area

            report_rows = list(grouped.values())
        else:
            for inst in filtered_instances:
                inst_id = inst.get("instance_id", inst.get("id", "inst_0"))
                def_name = inst.get("definition_name", inst.get("name", "Componente"))
                vol = float(inst.get("volume_m3", 0.0))
                area = float(inst.get("area_m2", 0.0))
                tag = inst.get("tag", "Layer0")
                mat = inst.get("material", "Padrão")
                ifc = inst.get("ifc_class", "Não classificado")
                bounds = inst.get("bounds", (1.0, 1.0, 1.0))
                w = bounds[0] if isinstance(bounds, (list, tuple)) else 1.0
                d = bounds[1] if isinstance(bounds, (list, tuple)) else 1.0
                h = bounds[2] if isinstance(bounds, (list, tuple)) else 1.0

                report_rows.append({
                    "Entity Name": inst_id,
                    "Definition Name": def_name,
                    "Quantity": 1,
                    "Tag": tag,
                    "Width (m)": round(w, 3),
                    "Depth (m)": round(d, 3),
                    "Height (m)": round(h, 3),
                    "Area (m2)": round(area, 4),
                    "Volume (m3)": round(vol, 4),
                    "Material": mat,
                    "IFC Class": ifc
                })
                total_quantity += 1
                total_volume_m3 += vol
                total_area_m2 += area

        # 3. Compilação em CSV
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=cls.DEFAULT_COLUMNS, extrasaction='ignore')
        writer.writeheader()
        for row in report_rows:
            writer.writerow(row)
        csv_string = csv_buffer.getvalue()

        return {
            "scope": scope_clean,
            "group_by_definition": group_by_definition,
            "total_items_count": len(report_rows),
            "total_instances_count": total_quantity,
            "total_volume_m3": round(total_volume_m3, 4),
            "total_area_m2": round(total_area_m2, 4),
            "columns": cls.DEFAULT_COLUMNS,
            "rows": report_rows,
            "csv_content": csv_string
        }
