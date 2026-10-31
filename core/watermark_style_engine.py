"""
Motor de Estilos de Marca d'Água do SketchUp (Watermark Style Engine - Zero DLL).

Implementa a engenharia reversa do painel Estilos -> Marca d'Água (Watermark) do SketchUp:
1. Modos de Camada:
   - Primeiro Plano (Overlay): Imagem renderizada sobre o modelo 3D (ex: carimbos de homologação, rascunhos, logos).
   - Segundo Plano (Background): Imagem renderizada atrás do modelo 3D (ex: céu estilizado, foto de entorno urbano).
2. Modos de Disposição no Viewport:
   - Posicionamento em Grade de 9 Pontos (Screen Positioned):
     'top-left', 'top-center', 'top-right', 'center-left', 'center', 'center-right', 'bottom-left', 'bottom-center', 'bottom-right'.
   - Mosaico (Tiled): Repetição contínua em padrão quadriculado com escala configurável.
   - Ajustar à Tela (Stretched): Estica para cobrir o viewport mantendo ou distorcendo a proporção.
3. Transparência e Mesclagem:
   - Opacidade regulável de 0% a 100%.
   - Modos de mesclagem CSS: 'normal', 'multiply', 'screen', 'overlay'.
"""

from typing import List, Dict, Any, Tuple, Optional


class WatermarkStyleEngine:
    """Motor analítico de marcas d'água e fundos gráficos do SketchUp."""

    VALID_LAYERS = ["overlay", "background"]
    VALID_PLACEMENTS = ["screen_position", "tiled", "stretched"]
    VALID_ANCHORS = [
        "top-left", "top-center", "top-right",
        "center-left", "center", "center-right",
        "bottom-left", "bottom-center", "bottom-right"
    ]

    @classmethod
    def configure_watermark(
        cls,
        name: str,
        image_url: str,
        layer: str = "overlay",
        placement: str = "screen_position",
        anchor: str = "bottom-right",
        opacity_pct: float = 80.0,
        scale_pct: float = 100.0,
        lock_aspect_ratio: bool = True,
        blend_mode: str = "normal",
        offset_px: Tuple[int, int] = (20, 20)
    ) -> Dict[str, Any]:
        """
        Configura uma marca d'água no padrão do gerenciador de estilos do SketchUp.
        """
        layer_clean = layer.lower().strip()
        if layer_clean not in cls.VALID_LAYERS:
            layer_clean = "overlay"

        placement_clean = placement.lower().strip()
        if placement_clean not in cls.VALID_PLACEMENTS:
            placement_clean = "screen_position"

        anchor_clean = anchor.lower().strip()
        if anchor_clean not in cls.VALID_ANCHORS:
            anchor_clean = "bottom-right"

        opacity_clamped = max(0.0, min(100.0, opacity_pct))
        scale_clamped = max(10.0, min(500.0, scale_pct))

        # Gera estilo CSS analítico pronto para injeção no viewport Three.js
        css_styles: Dict[str, str] = {
            "position": "absolute",
            "pointer-events": "none",
            "opacity": f"{opacity_clamped / 100.0:.2f}",
            "mix-blend-mode": blend_mode,
            "z-index": "15" if layer_clean == "overlay" else "0"
        }

        if placement_clean == "stretched":
            css_styles.update({
                "top": "0", "left": "0", "width": "100%", "height": "100%",
                "object-fit": "contain" if lock_aspect_ratio else "fill"
            })
        elif placement_clean == "tiled":
            css_styles.update({
                "top": "0", "left": "0", "width": "100%", "height": "100%",
                "background-image": f"url('{image_url}')",
                "background-repeat": "repeat",
                "background-size": f"{scale_clamped}%"
            })
        else:  # screen_position
            # Resolve posicionamento nas 9 âncoras
            if "top" in anchor_clean:
                css_styles["top"] = f"{offset_px[1]}px"
            elif "bottom" in anchor_clean:
                css_styles["bottom"] = f"{offset_px[1]}px"
            else:
                css_styles["top"] = "50%"
                css_styles["transform"] = "translateY(-50%)"

            if "left" in anchor_clean:
                css_styles["left"] = f"{offset_px[0]}px"
            elif "right" in anchor_clean:
                css_styles["right"] = f"{offset_px[0]}px"
            else:
                css_styles["left"] = "50%"
                if "transform" in css_styles:
                    css_styles["transform"] = "translate(-50%, -50%)"
                else:
                    css_styles["transform"] = "translateX(-50%)"

            css_styles["max-width"] = f"{scale_clamped}%"
            css_styles["max-height"] = f"{scale_clamped}%"

        return {
            "name": name,
            "image_url": image_url,
            "layer": layer_clean,
            "placement": placement_clean,
            "anchor": anchor_clean,
            "opacity_pct": round(opacity_clamped, 1),
            "scale_pct": round(scale_clamped, 1),
            "lock_aspect_ratio": lock_aspect_ratio,
            "blend_mode": blend_mode,
            "offset_px": offset_px,
            "css_styles": css_styles
        }
