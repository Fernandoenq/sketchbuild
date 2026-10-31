"""
SketchBuild - Tabela de Cutlist Otimizada para Fabricação CNC (Zero DLL / Pure Python)
Frente 95: Engenharia Reversa do SketchUp - CNC Cutlist, Saw Nesting & Part Table Export

Gera tabelas industriais de corte (CSV/JSON) para serras seccionadoras e centros CNC,
incluindo margens de refilo (trimming), sentido do veio da madeira e códigos de barras.
"""

from __future__ import annotations

import csv
import io
from typing import Any, Dict, List


class CamCutlistFabricationEngine:
    """Motor de geração de listas de corte industriais e metadados CNC."""

    @staticmethod
    def generate_cnc_cutlist(
        parts: List[Dict[str, Any]],
        saw_kerf_mm: float = 4.0,
        trim_margin_mm: float = 15.0,
        export_csv: bool = True
    ) -> Dict[str, Any]:
        """
        Processa peças de marcenaria ou estrutura metálica e produz tabela de corte executiva.
        """
        processed_parts: List[Dict[str, Any]] = []
        total_finished_area_m2 = 0.0
        total_raw_area_m2 = 0.0
        total_parts_count = 0

        for idx, p in enumerate(parts):
            name = p.get("name", f"Peça_{idx + 1}")
            part_id = p.get("id", f"P_{idx + 1:03d}")
            material = p.get("material", "Madeira Maciça")
            qty = int(p.get("quantity", 1))

            fin_len = float(p.get("length_mm", 1000.0))
            fin_wid = float(p.get("width_mm", 100.0))
            thick = float(p.get("thickness_mm", 20.0))
            grain = p.get("grain_direction", "LENGTHWISE")  # Sentido do veio

            # Dimensões brutas com margem de refilo (saw kerf + trim)
            raw_len = fin_len + (trim_margin_mm * 2.0)
            raw_wid = fin_wid + (trim_margin_mm * 2.0)

            fin_area = (fin_len * fin_wid / 1e6) * qty
            raw_area = (raw_len * raw_wid / 1e6) * qty

            total_finished_area_m2 += fin_area
            total_raw_area_m2 += raw_area
            total_parts_count += qty

            barcode = f"{part_id}-{int(fin_len)}x{int(fin_wid)}"

            processed_parts.append({
                "part_id": part_id,
                "name": name,
                "material": material,
                "quantity": qty,
                "finished_length_mm": round(fin_len, 1),
                "finished_width_mm": round(fin_wid, 1),
                "thickness_mm": round(thick, 1),
                "raw_length_mm": round(raw_len, 1),
                "raw_width_mm": round(raw_wid, 1),
                "grain_direction": grain,
                "barcode": barcode,
                "area_m2": round(fin_area, 4)
            })

        # Geração de CSV industrial compatível com seccionadoras CNC
        csv_content = ""
        if export_csv:
            output = io.StringIO()
            writer = csv.writer(output, delimiter=";")
            writer.writerow([
                "PartID", "Name", "Material", "Qty",
                "FinLength_mm", "FinWidth_mm", "Thickness_mm",
                "RawLength_mm", "RawWidth_mm", "Grain", "Barcode"
            ])
            for item in processed_parts:
                writer.writerow([
                    item["part_id"],
                    item["name"],
                    item["material"],
                    item["quantity"],
                    item["finished_length_mm"],
                    item["finished_width_mm"],
                    item["thickness_mm"],
                    item["raw_length_mm"],
                    item["raw_width_mm"],
                    item["grain_direction"],
                    item["barcode"]
                ])
            csv_content = output.getvalue()

        yield_pct = (total_finished_area_m2 / total_raw_area_m2 * 100.0) if total_raw_area_m2 > 0 else 100.0

        return {
            "entity_type": "CamCutlistReport",
            "saw_kerf_mm": saw_kerf_mm,
            "trim_margin_mm": trim_margin_mm,
            "unique_parts_count": len(parts),
            "total_items_count": total_parts_count,
            "total_finished_area_m2": round(total_finished_area_m2, 4),
            "total_raw_area_m2": round(total_raw_area_m2, 4),
            "cutting_yield_percent": round(yield_pct, 2),
            "parts": processed_parts,
            "csv_data": csv_content,
            "status": "LISTA DE CORTE CNC GERADA COM SUCESSO"
        }
