"""Engine de Engenharia Reversa da Caixa de Dialogo Exportar Grafico 2D (2D Graphic Export Options).

Controla resolucoes customizadas em pixels, DPI de impressao, proporcao de aspecto,
fator multiplicador de espessura de linhas e fundo transparente para exportacao tecnica.
"""

from __future__ import annotations
import math
from typing import Any


class GraphicExport2DEngine:
    """Implementa a configuracao analitica de exportacao grafica 2D do SketchUp."""

    SUPPORTED_FORMATS = ["PNG", "JPEG", "PDF", "EPS", "BMP", "TIFF"]

    @classmethod
    def configure_2d_export(
        cls,
        image_format: str = "PNG",
        width_px: int = 1920,
        height_px: int | None = None,
        viewport_aspect_ratio: float = 16.0 / 9.0,
        dpi: int = 300,
        line_scale_multiplier: float = 1.0,
        anti_aliasing: bool = True,
        transparent_background: bool = False
    ) -> dict[str, Any]:
        """Calcula as dimensoes fisicas, espessuras de aresta e parametros do renderizador."""
        fmt = image_format.upper().strip()
        if fmt not in cls.SUPPORTED_FORMATS:
            fmt = "PNG"

        w = max(64, min(int(width_px), 16384))
        if height_px is not None:
            h = max(64, min(int(height_px), 16384))
        else:
            aspect = max(0.1, float(viewport_aspect_ratio))
            h = max(64, int(round(w / aspect)))

        res_dpi = max(72, min(int(dpi), 1200))
        scale_mult = max(0.1, min(float(line_scale_multiplier), 10.0))

        # Dimensoes fisicas de impressao
        w_in = w / res_dpi
        h_in = h / res_dpi
        w_cm = w_in * 2.54
        h_cm = h_in * 2.54

        # Espessura nominal de aresta calibrada para a resolucao
        base_edge_px = 1.0
        calibrated_edge_px = round(base_edge_px * scale_mult * (res_dpi / 72.0), 2)

        # Transparencia valida somente para formatos com canal alpha
        has_alpha = transparent_background and (fmt in ["PNG", "TIFF", "PDF"])

        # Parametros para invocacao no WebGL canvas / Three.js
        render_options = {
            "format": fmt,
            "width": w,
            "height": h,
            "dpi": res_dpi,
            "antiAliasing": anti_aliasing,
            "transparent": has_alpha,
            "edgeLineWidth": calibrated_edge_px,
        }

        return {
            "success": True,
            "format": fmt,
            "resolution_px": [w, h],
            "aspect_ratio": round(w / h, 4),
            "dpi": res_dpi,
            "print_size_cm": [round(w_cm, 2), round(h_cm, 2)],
            "print_size_inches": [round(w_in, 2), round(h_in, 2)],
            "line_scale_multiplier": scale_mult,
            "effective_edge_width_px": calibrated_edge_px,
            "transparent_background": has_alpha,
            "anti_aliasing": anti_aliasing,
            "render_options": render_options,
        }
