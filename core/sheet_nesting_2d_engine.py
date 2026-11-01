"""
SketchBuild - Motor de Plano de Corte e Nesting 2D Guilhotinado para Marcenaria (Zero DLL / Pure Python)
Frente Marcenaria Avançada: Otimização de Corte em Chapas MDF/MDP (Guillotine 2D Bin Packing)

Implementa:
1. Padrão industrial brasileiro de chapas MDF: 2750mm x 1830mm (personalizável).
2. Refilo perimetral de esquadrejamento (aparamento das bordas da chapa bruta, tipicamente 10mm a 15mm).
3. Espessura da lâmina de serra (Saw Kerf, padrão 3.2mm a 4.0mm).
4. Restrição de sentido do veio da madeira (Grain Direction): impede rotação em painéis amadeirados.
5. Algoritmo de empacotamento guilhotinado (Guillotine Cut Partitioning):
   - Simula cortes contínuos de ponta a ponta de esquadrejadeiras e seccionadoras horizontais.
6. Cálculo analítico de aproveitamento percentual (Yield Rate), sobras, retalhos e diagrama vetorial.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class SheetNesting2DEngine:
    """Motor analítico de otimização de plano de corte guilhotinado em chapas de madeira."""

    DEFAULT_SHEET_WIDTH_MM: float = 2750.0
    DEFAULT_SHEET_HEIGHT_MM: float = 1830.0
    DEFAULT_TRIM_MARGIN_MM: float = 10.0   # Refilo de borda
    DEFAULT_SAW_KERF_MM: float = 3.2       # Espessura do disco de serra

    @classmethod
    def optimize_cut_list(
        cls,
        parts: List[Dict[str, Any]],
        sheet_width_mm: float = DEFAULT_SHEET_WIDTH_MM,
        sheet_height_mm: float = DEFAULT_SHEET_HEIGHT_MM,
        trim_margin_mm: float = DEFAULT_TRIM_MARGIN_MM,
        saw_kerf_mm: float = DEFAULT_SAW_KERF_MM,
    ) -> Dict[str, Any]:
        """
        Executa o plano de corte 2D guilhotinado para uma lista de peças retangulares.

        Args:
            parts: Lista de peças contendo:
                   - "id": str
                   - "name": str
                   - "width_mm": float
                   - "height_mm": float
                   - "quantity": int
                   - "can_rotate": bool (False se tiver veio de madeira definido)
            sheet_width_mm: Largura da chapa MDF em mm (padrão 2750mm).
            sheet_height_mm: Altura da chapa MDF em mm (padrão 1830mm).
            trim_margin_mm: Refilo de segurança em torno da chapa (mm).
            saw_kerf_mm: Perda milimétrica da espessura do corte da serra.

        Returns:
            Dicionário com chapas utilizadas, peças posicionadas, taxa de aproveitamento e sobras.
        """
        # Área útil da chapa após refilo
        usable_w = sheet_width_mm - 2 * trim_margin_mm
        usable_h = sheet_height_mm - 2 * trim_margin_mm

        if usable_w <= 0 or usable_h <= 0:
            raise ValueError("Dimensões úteis da chapa após refilo são inválidas")

        # Expande lista com base na quantidade e ordena por área decrescente (Heurística FFDH)
        expanded_parts: List[Dict[str, Any]] = []
        for p in parts:
            qty = max(1, int(p.get("quantity", 1)))
            pw = float(p.get("width_mm", 0.0))
            ph = float(p.get("height_mm", 0.0))
            p_id = str(p.get("id", "P"))
            p_name = str(p.get("name", "Peça"))
            rotatable = bool(p.get("can_rotate", True))

            for q_idx in range(qty):
                expanded_parts.append({
                    "id": f"{p_id}_{q_idx+1}" if qty > 1 else p_id,
                    "name": p_name,
                    "w": pw,
                    "h": ph,
                    "area": pw * ph,
                    "can_rotate": rotatable,
                })

        # Ordena as peças pela maior dimensão e área
        expanded_parts.sort(key=lambda item: (max(item["w"], item["h"]), item["area"]), reverse=True)

        # Estrutura de chapas e espaços livres (Guillotine Best Fit)
        sheets: List[Dict[str, Any]] = []

        def create_new_sheet(idx: int) -> Dict[str, Any]:
            return {
                "sheet_index": idx,
                "dimensions_mm": {"width": sheet_width_mm, "height": sheet_height_mm},
                "usable_origin_mm": {"x": trim_margin_mm, "y": trim_margin_mm},
                "usable_size_mm": {"width": usable_w, "height": usable_h},
                "free_rects": [(trim_margin_mm, trim_margin_mm, usable_w, usable_h)],
                "placed_parts": [],
                "used_area_mm2": 0.0,
            }

        if expanded_parts:
            sheets.append(create_new_sheet(1))

        total_part_area_mm2 = sum(p["area"] for p in expanded_parts)
        unplaced_parts: List[Dict[str, Any]] = []

        for part in expanded_parts:
            placed = False
            best_sheet_idx = -1
            best_rect_idx = -1
            best_rotated = False
            min_waste = float("inf")

            pw, ph = part["w"], part["h"]

            # Tenta encaixar nos retângulos livres das chapas abertas
            for s_idx, sheet in enumerate(sheets):
                for r_idx, (rx, ry, rw, rh) in enumerate(sheet["free_rects"]):
                    # Orientação original
                    if pw <= rw and ph <= rh:
                        waste = (rw * rh) - (pw * ph)
                        if waste < min_waste:
                            min_waste = waste
                            best_sheet_idx = s_idx
                            best_rect_idx = r_idx
                            best_rotated = False

                    # Orientação rotacionada (se permitido)
                    if part["can_rotate"] and ph <= rw and pw <= rh:
                        waste = (rw * rh) - (pw * ph)
                        if waste < min_waste:
                            min_waste = waste
                            best_sheet_idx = s_idx
                            best_rect_idx = r_idx
                            best_rotated = True

            if best_sheet_idx != -1:
                # Encaixa a peça no retângulo escolhido
                sheet = sheets[best_sheet_idx]
                rx, ry, rw, rh = sheet["free_rects"].pop(best_rect_idx)
                actual_w = ph if best_rotated else pw
                actual_h = pw if best_rotated else ph

                sheet["placed_parts"].append({
                    "id": part["id"],
                    "name": part["name"],
                    "x_mm": round(rx, 2),
                    "y_mm": round(ry, 2),
                    "width_mm": round(actual_w, 2),
                    "height_mm": round(actual_h, 2),
                    "is_rotated": best_rotated,
                })
                sheet["used_area_mm2"] += actual_w * actual_h

                # Particionamento guilhotinado do espaço residual (Right split + Top split com saw kerf)
                remain_w = rw - actual_w - saw_kerf_mm
                remain_h = rh - actual_h - saw_kerf_mm

                if remain_w > 50.0:  # Retângulo à direita da peça
                    sheet["free_rects"].append((
                        rx + actual_w + saw_kerf_mm,
                        ry,
                        remain_w,
                        actual_h,
                    ))

                if remain_h > 50.0:  # Retângulo acima da peça
                    sheet["free_rects"].append((
                        rx,
                        ry + actual_h + saw_kerf_mm,
                        rw,
                        remain_h,
                    ))
                placed = True
            else:
                # Abre nova chapa se couber
                if (pw <= usable_w and ph <= usable_h) or (part["can_rotate"] and ph <= usable_w and pw <= usable_h):
                    new_s = create_new_sheet(len(sheets) + 1)
                    rx, ry, rw, rh = new_s["free_rects"].pop(0)

                    rotate = False
                    if not (pw <= usable_w and ph <= usable_h):
                        rotate = True

                    actual_w = ph if rotate else pw
                    actual_h = pw if rotate else ph

                    new_s["placed_parts"].append({
                        "id": part["id"],
                        "name": part["name"],
                        "x_mm": round(rx, 2),
                        "y_mm": round(ry, 2),
                        "width_mm": round(actual_w, 2),
                        "height_mm": round(actual_h, 2),
                        "is_rotated": rotate,
                    })
                    new_s["used_area_mm2"] += actual_w * actual_h

                    remain_w = rw - actual_w - saw_kerf_mm
                    remain_h = rh - actual_h - saw_kerf_mm
                    if remain_w > 50.0:
                        new_s["free_rects"].append((rx + actual_w + saw_kerf_mm, ry, remain_w, actual_h))
                    if remain_h > 50.0:
                        new_s["free_rects"].append((rx, ry + actual_h + saw_kerf_mm, rw, remain_h))

                    sheets.append(new_s)
                    placed = True
                else:
                    unplaced_parts.append(part)

        # Remove free_rects internos do retorno final para simplificar payload
        clean_sheets = []
        total_sheet_area_mm2 = len(sheets) * (sheet_width_mm * sheet_height_mm)

        for s in sheets:
            sheet_usable_area = usable_w * usable_h
            efficiency = (s["used_area_mm2"] / sheet_usable_area * 100.0) if sheet_usable_area > 0 else 0.0
            clean_sheets.append({
                "sheet_index": s["sheet_index"],
                "width_mm": sheet_width_mm,
                "height_mm": sheet_height_mm,
                "parts_count": len(s["placed_parts"]),
                "efficiency_percent": round(efficiency, 2),
                "waste_percent": round(100.0 - efficiency, 2),
                "placed_parts": s["placed_parts"],
            })

        global_yield = (total_part_area_mm2 / total_sheet_area_mm2 * 100.0) if total_sheet_area_mm2 > 0 else 0.0

        return {
            "status": "success",
            "sheet_count": len(clean_sheets),
            "parts_requested": len(expanded_parts),
            "parts_placed": len(expanded_parts) - len(unplaced_parts),
            "unplaced_count": len(unplaced_parts),
            "global_yield_percent": round(global_yield, 2),
            "global_waste_percent": round(100.0 - global_yield, 2),
            "sheets": clean_sheets,
            "saw_kerf_mm": saw_kerf_mm,
            "trim_margin_mm": trim_margin_mm,
        }
