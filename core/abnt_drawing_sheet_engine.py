"""
SketchBuild - Motor de Pranchas Técnicas ABNT e Viewports com Escala (Zero DLL / Pure Python)
Frente LayOut Oficial: Pranchas NBR 6492 / NBR 10068 e Viewports Arquitetônicos

Implementa:
1. Formatos padronizados ABNT NBR 10068: A0, A1, A2, A3 e A4 em milímetros.
2. Margens normativas (esquerda de 25mm para encadernação, outras margens de 10mm ou 7mm).
3. Selo / Carimbo técnico normativo com autor, escala, data, título e revisão.
4. Cálculo analítico de Viewport com escalas arquitetônicas oficiais (1:20, 1:25, 1:50, 1:100, 1:200).
5. Posicionamento de prancha e desenho com conversão métrica exata para vetor SVG/PDF.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


# Dimensões normativas ABNT (largura x altura em milímetros na orientação paisagem, exceto A4 retrato)
SHEET_SIZES_MM: Dict[str, Tuple[float, float]] = {
    "A0": (1189.0, 841.0),
    "A1": (841.0, 594.0),
    "A2": (594.0, 420.0),
    "A3": (420.0, 297.0),
    "A4": (210.0, 297.0),
}

# Margens normativas (esquerda, superior, direita, inferior) em mm
SHEET_MARGINS_MM: Dict[str, Tuple[float, float, float, float]] = {
    "A0": (25.0, 10.0, 10.0, 10.0),
    "A1": (25.0, 10.0, 10.0, 10.0),
    "A2": (25.0, 10.0, 10.0, 10.0),
    "A3": (25.0, 7.0, 7.0, 7.0),
    "A4": (25.0, 7.0, 7.0, 7.0),
}


class AbntDrawingSheetEngine:
    """Motor de cálculo de pranchas técnicas executivas e viewports de escala do SketchUp."""

    @classmethod
    def create_sheet(
        cls,
        format_name: str = "A1",
        project_title: str = "Residência Unifamiliar",
        sheet_title: str = "Plantas Baixas e Cortes",
        author: str = "Fernando Filho",
        client: str = "Cliente Modelo",
        scale: str = "1:50",
        sheet_number: str = "01/03",
        date_str: str = "31/10/2026",
    ) -> Dict[str, Any]:
        """Gera a estrutura paramétrica da prancha técnica e carimbo normativo ABNT (compatibilidade retroativa)."""
        return cls.create_drawing_sheet(
            sheet_format=format_name,
            orientation="landscape" if format_name.upper() != "A4" else "portrait",
            title_block={
                "project_title": project_title,
                "sheet_title": sheet_title,
                "title": sheet_title,
                "author": author,
                "client": client,
                "scale": scale,
                "sheet_number": sheet_number,
                "date": date_str,
            },
        )

    @classmethod
    def create_drawing_sheet(
        cls,
        sheet_format: str = "A3",
        orientation: str = "landscape",
        title_block: Optional[Dict[str, Any]] = None,
        viewports: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Cria a definição completa de prancha normativa ABNT com carimbo e posicionamento de viewports.
        """
        fmt = sheet_format.upper()
        if fmt not in SHEET_SIZES_MM:
            fmt = "A3"

        base_w, base_h = SHEET_SIZES_MM[fmt]
        if orientation == "portrait" and base_w > base_h:
            width_mm, height_mm = base_h, base_w
        elif orientation == "landscape" and base_h > base_w:
            width_mm, height_mm = base_h, base_w
        else:
            width_mm, height_mm = base_w, base_h

        m_left, m_top, m_right, m_bottom = SHEET_MARGINS_MM[fmt]

        usable_w = width_mm - (m_left + m_right)
        usable_h = height_mm - (m_top + m_bottom)

        # Selo / Carimbo normativo posicionado no canto inferior direito
        tb_data = title_block or {}
        stamp_width_mm = 175.0
        stamp_height_mm = 64.0
        stamp_x = width_mm - m_right - stamp_width_mm
        stamp_y = m_bottom

        processed_viewports = []
        if viewports:
            for vp in viewports:
                vp_name = vp.get("name", "Vista 1")
                vp_scale = vp.get("scale", "1:50")
                bounds = vp.get("model_bounds", {})
                min_x = float(bounds.get("min_x", 0.0))
                min_y = float(bounds.get("min_y", 0.0))
                max_x = float(bounds.get("max_x", 1.0))
                max_y = float(bounds.get("max_y", 1.0))

                dx = abs(max_x - min_x)
                dy = abs(max_y - min_y)

                # Extrai proporção numérica da escala (ex: "1:50" -> 50.0)
                try:
                    ratio = float(vp_scale.split(":")[1])
                except Exception:
                    ratio = 50.0

                scale_factor = 1000.0 / ratio  # mm por metro
                paper_w = dx * scale_factor
                paper_h = dy * scale_factor

                processed_viewports.append({
                    "name": vp_name,
                    "scale": vp_scale,
                    "scale_ratio": ratio,
                    "position_mm": {
                        "x": float(vp.get("x_mm", m_left)),
                        "y": float(vp.get("y_mm", m_bottom)),
                    },
                    "paper_size_mm": {
                        "width": round(paper_w, 2),
                        "height": round(paper_h, 2),
                    },
                    "model_bounds_m": bounds,
                })

        return {
            "status": "success",
            "format": fmt,
            "orientation": orientation,
            "dimensions_mm": {
                "width": round(width_mm, 2),
                "height": round(height_mm, 2),
            },
            "margins_mm": {
                "left": m_left,
                "top": m_top,
                "right": m_right,
                "bottom": m_bottom,
            },
            "usable_area_mm": {
                "width": round(usable_w, 2),
                "height": round(usable_h, 2),
            },
            "title_block": {
                "position_mm": {"x": round(stamp_x, 2), "y": round(stamp_y, 2)},
                "dimensions_mm": {"width": stamp_width_mm, "height": stamp_height_mm},
                "title": tb_data.get("title", tb_data.get("sheet_title", "Prancha Técnica")),
                "project_title": tb_data.get("project_title", "Projeto Executivo"),
                "author": tb_data.get("author", "Arquiteto Responsável"),
                "scale": tb_data.get("scale", "Indicada"),
                "sheet_number": tb_data.get("sheet_number", "01/01"),
                "date": tb_data.get("date", "2026-10-31"),
                "standard": "ABNT NBR 10068 / NBR 6492",
            },
            "viewports": processed_viewports,
        }

    @classmethod
    def calculate_viewport_scale(
        cls,
        model_bbox_min: Tuple[float, float, float],
        model_bbox_max: Tuple[float, float, float],
        scale_ratio: float = 50.0,
        view_type: str = "top",
    ) -> Dict[str, Any]:
        """
        Calcula as dimensões em milímetros que um modelo 3D ocupará na prancha na escala especificada.
        1 metro no modelo = (1000 / scale_ratio) mm na prancha.
        """
        dx = abs(model_bbox_max[0] - model_bbox_min[0])
        dy = abs(model_bbox_max[1] - model_bbox_min[1])
        dz = abs(model_bbox_max[2] - model_bbox_min[2])

        if view_type == "top":
            model_w_m = dx
            model_h_m = dy
        elif view_type == "front":
            model_w_m = dx
            model_h_m = dz
        else:
            model_w_m = dy
            model_h_m = dz

        factor_mm_per_m = 1000.0 / scale_ratio
        paper_w_mm = model_w_m * factor_mm_per_m
        paper_h_mm = model_h_m * factor_mm_per_m

        return {
            "status": "success",
            "scale": f"1:{int(scale_ratio)}",
            "scale_ratio": scale_ratio,
            "view_type": view_type,
            "model_size_m": [round(model_w_m, 3), round(model_h_m, 3)],
            "paper_size_mm": [round(paper_w_mm, 1), round(paper_h_mm, 1)],
            "mm_per_meter": round(factor_mm_per_m, 2),
        }
