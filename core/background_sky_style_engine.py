"""
SketchBuild - Motor de Estilos de Céu, Solo e Horizonte Gradiente (Zero DLL / Pure Python)
Frente 83: Engenharia Reversa do SketchUp - SUStyleRef (Sky, Ground & Horizon Settings)

Gerencia as opções nativas de plano de fundo do SketchUp: gradiente de céu azul,
plano de chão translúcido, cor de horizonte e integração direta com o Three.js.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class BackgroundSkyStyleEngine:
    """Motor de controle de cores de plano de fundo, céu e solo do modelo."""

    DEFAULT_SKY_COLOR = "#b4d5fe"       # Azul suave clássico SketchUp
    DEFAULT_GROUND_COLOR = "#c2b8a3"    # Bege terra
    DEFAULT_HORIZON_COLOR = "#95afc0"   # Cinza horizonte
    DEFAULT_BACKGROUND_COLOR = "#ffffff"

    @classmethod
    def configure_background_sky(
        cls,
        sky_enabled: bool = True,
        ground_enabled: bool = True,
        sky_color: str = DEFAULT_SKY_COLOR,
        ground_color: str = DEFAULT_GROUND_COLOR,
        horizon_color: str = DEFAULT_HORIZON_COLOR,
        background_color: str = DEFAULT_BACKGROUND_COLOR,
        ground_transparency_percent: int = 50,
        show_horizon: bool = True,
    ) -> Dict[str, Any]:
        """
        Gera as definições canônicas de background, céu e solo SUStyleRef.
        """
        transp = max(0, min(100, ground_transparency_percent))
        ground_opacity = round(transp / 100.0, 2)

        # Gradiente CSS para o container do Three.js
        if sky_enabled and ground_enabled:
            css_gradient = f"linear-gradient(to bottom, {sky_color} 0%, {horizon_color} 50%, {ground_color} 100%)"
        elif sky_enabled:
            css_gradient = f"linear-gradient(to bottom, {sky_color} 0%, {horizon_color} 100%)"
        else:
            css_gradient = background_color

        return {
            "entity_type": "SUStyleBackgroundSky",
            "sky_enabled": sky_enabled,
            "ground_enabled": ground_enabled,
            "sky_color": sky_color,
            "ground_color": ground_color,
            "horizon_color": horizon_color,
            "background_color": background_color,
            "ground_transparency_percent": transp,
            "ground_opacity": ground_opacity,
            "show_horizon": show_horizon,
            "three_config": {
                "css_background": css_gradient,
                "clear_color": background_color if not sky_enabled else sky_color,
                "use_shadow_plane": ground_enabled,
                "shadow_plane_opacity": ground_opacity,
            },
            "status": "ESTILO DE CÉU E SOLO ATUALIZADO",
        }
