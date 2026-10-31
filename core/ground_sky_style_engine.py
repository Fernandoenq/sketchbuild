"""
Motor de Configurações de Fundo, Solo e Céu dos Estilos do SketchUp (Ground & Sky Style Engine - Zero DLL).

Implementa a engenharia reversa do painel oficial 'Estilos' (Styles -> Edit -> Background Settings) do SketchUp:
1. Parâmetros Nativos:
   - background_color: Cor base do plano de fundo (hex: ex: '#FFFFFF').
   - sky_enabled: Habilita renderização da cúpula/céu.
   - sky_color: Cor do céu (hex: ex: '#C3DDF7').
   - ground_enabled: Habilita plano de horizonte do solo.
   - ground_color: Cor da superfície do solo (hex: ex: '#C7BEB3').
   - ground_transparency_pct: Nível de transparência do plano do solo (0 a 100%).
   - show_ground_from_below: Permite ver o solo quando a câmera está abaixo do plano Z=0.
2. Formatação para Viewport e Three.js / WebGL:
   - Gera as cores RGBA / Hex e parâmetros de renderização de fog/clearColor e grid de chão.
"""

from typing import Dict, Any, Optional


class GroundSkyStyleEngine:
    """Motor analítico de controle de céu, solo e plano de fundo dos Estilos do SketchUp."""

    DEFAULT_STYLE: Dict[str, Any] = {
        "background_color": "#FFFFFF",
        "sky_enabled": True,
        "sky_color": "#C3DDF7",
        "ground_enabled": True,
        "ground_color": "#C7BEB3",
        "ground_transparency_pct": 50,
        "show_ground_from_below": False
    }

    @staticmethod
    def _hex_to_rgb(hex_code: str) -> Dict[str, float]:
        hex_clean = hex_code.strip().lstrip("#")
        if len(hex_clean) == 3:
            hex_clean = "".join(c * 2 for c in hex_clean)
        if len(hex_clean) != 6:
            return {"r": 1.0, "g": 1.0, "b": 1.0}
        try:
            r = int(hex_clean[0:2], 16) / 255.0
            g = int(hex_clean[2:4], 16) / 255.0
            b = int(hex_clean[4:6], 16) / 255.0
            return {"r": round(r, 3), "g": round(g, 3), "b": round(b, 3)}
        except ValueError:
            return {"r": 1.0, "g": 1.0, "b": 1.0}

    @classmethod
    def configure_background_style(
        cls,
        background_color: Optional[str] = None,
        sky_enabled: Optional[bool] = None,
        sky_color: Optional[str] = None,
        ground_enabled: Optional[bool] = None,
        ground_color: Optional[str] = None,
        ground_transparency_pct: Optional[int] = None,
        show_ground_from_below: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Valida, normaliza e compõe as configurações de plano de fundo do Estilo.
        """
        cfg = dict(cls.DEFAULT_STYLE)

        if background_color is not None:
            cfg["background_color"] = str(background_color).strip().upper()
        if sky_enabled is not None:
            cfg["sky_enabled"] = bool(sky_enabled)
        if sky_color is not None:
            cfg["sky_color"] = str(sky_color).strip().upper()
        if ground_enabled is not None:
            cfg["ground_enabled"] = bool(ground_enabled)
        if ground_color is not None:
            cfg["ground_color"] = str(ground_color).strip().upper()
        if ground_transparency_pct is not None:
            cfg["ground_transparency_pct"] = max(0, min(100, int(ground_transparency_pct)))
        if show_ground_from_below is not None:
            cfg["show_ground_from_below"] = bool(show_ground_from_below)

        # Converte cores para RGB numérico (0.0 a 1.0) para uso direto no WebGL/Three.js
        bg_rgb = cls._hex_to_rgb(cfg["background_color"])
        sky_rgb = cls._hex_to_rgb(cfg["sky_color"])
        ground_rgb = cls._hex_to_rgb(cfg["ground_color"])
        ground_opacity = (100 - cfg["ground_transparency_pct"]) / 100.0

        return {
            "status": "success",
            "style_settings": cfg,
            "render_payload": {
                "clear_color_hex": cfg["background_color"] if not cfg["sky_enabled"] else cfg["sky_color"],
                "clear_color_rgb": bg_rgb if not cfg["sky_enabled"] else sky_rgb,
                "sky": {
                    "enabled": cfg["sky_enabled"],
                    "color_hex": cfg["sky_color"],
                    "color_rgb": sky_rgb
                },
                "ground": {
                    "enabled": cfg["ground_enabled"],
                    "color_hex": cfg["ground_color"],
                    "color_rgb": ground_rgb,
                    "opacity": round(ground_opacity, 2),
                    "show_from_below": cfg["show_ground_from_below"]
                }
            }
        }
