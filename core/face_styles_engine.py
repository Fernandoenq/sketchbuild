"""
SketchBuild - Motor de Estilos de Faces e Transparência Estilo Vidro (Zero DLL / Pure Python)
Frente 68: Engenharia Reversa do SketchUp - Face Styles & Glass Shader PBR

Gerencia os modos de renderização de faces nativos do SketchUp:
- Wireframe (Apenas Arestas)
- Hidden Line (Linha Oculta monocromática sem sombras/texturas)
- Shaded (Sombreado por cores difusas sem texturas)
- Shaded with Textures (Sombreado com mapeamento UV de texturas)
- Monochrome (Inspeção de orientação de normais: front_color vs back_color)
- X-Ray (Transparência global uniforme 50%)
E controle de materiais físicos translúcidos estilo vidro.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional


class FaceRenderMode(str, Enum):
    WIRE_FRAME = "WIRE_FRAME"
    HIDDEN_LINE = "HIDDEN_LINE"
    SHADED = "SHADED"
    SHADED_WITH_TEXTURES = "SHADED_WITH_TEXTURES"
    MONOCHROME = "MONOCHROME"
    XRAY = "XRAY"


class FaceStylesEngine:
    """Motor de controle de estilos de renderização de superfícies e transparência física."""

    DEFAULT_FRONT_COLOR = "#f5f6fa"  # Branco quente / off-white padrão SketchUp
    DEFAULT_BACK_COLOR = "#7f8fa6"   # Azul acinzentado padrão para verso de face
    DEFAULT_HIDDEN_LINE_COLOR = "#ffffff"

    @classmethod
    def resolve_material_render_properties(
        cls,
        mode: FaceRenderMode = FaceRenderMode.SHADED_WITH_TEXTURES,
        material_color: Optional[str] = None,
        texture_path: Optional[str] = None,
        opacity: float = 1.0,
        is_back_face: bool = False,
    ) -> Dict[str, Any]:
        """
        Calcula as propriedades de exibição gráfica no Three.js para uma face com base no modo ativo.
        """
        is_transparent = opacity < 0.99
        eff_opacity = max(0.0, min(1.0, opacity))

        if mode == FaceRenderMode.WIRE_FRAME:
            return {
                "visible": False,
                "wireframe": True,
                "color": "#000000",
                "use_texture": False,
                "opacity": 0.0,
                "transparent": True,
            }

        elif mode == FaceRenderMode.HIDDEN_LINE:
            return {
                "visible": True,
                "wireframe": False,
                "color": cls.DEFAULT_HIDDEN_LINE_COLOR,
                "use_texture": False,
                "opacity": 1.0,
                "transparent": False,
                "roughness": 1.0,
                "metalness": 0.0,
            }

        elif mode == FaceRenderMode.MONOCHROME:
            chosen_color = cls.DEFAULT_BACK_COLOR if is_back_face else cls.DEFAULT_FRONT_COLOR
            return {
                "visible": True,
                "wireframe": False,
                "color": chosen_color,
                "use_texture": False,
                "opacity": 1.0,
                "transparent": False,
                "roughness": 0.8,
                "metalness": 0.0,
            }

        elif mode == FaceRenderMode.SHADED:
            return {
                "visible": True,
                "wireframe": False,
                "color": material_color or cls.DEFAULT_FRONT_COLOR,
                "use_texture": False,
                "opacity": eff_opacity,
                "transparent": is_transparent,
                "roughness": 0.5,
                "metalness": 0.0,
            }

        elif mode == FaceRenderMode.XRAY:
            return {
                "visible": True,
                "wireframe": False,
                "color": material_color or cls.DEFAULT_FRONT_COLOR,
                "use_texture": bool(texture_path),
                "texture_path": texture_path if texture_path else None,
                "opacity": 0.5,
                "transparent": True,
                "depthWrite": False,
                "roughness": 0.4,
                "metalness": 0.0,
            }

        else:  # SHADED_WITH_TEXTURES (Default nativo do SketchUp)
            return {
                "visible": True,
                "wireframe": False,
                "color": material_color or cls.DEFAULT_FRONT_COLOR,
                "use_texture": bool(texture_path),
                "texture_path": texture_path if texture_path else None,
                "opacity": eff_opacity,
                "transparent": is_transparent,
                "roughness": 0.5,
                "metalness": 0.0,
            }

    @classmethod
    def create_glass_material(
        cls,
        name: str = "Vidro Arquitetônico Transparente",
        color: str = "#dff9fb",
        opacity: float = 0.3,
        refraction_index: float = 1.52,
    ) -> Dict[str, Any]:
        """
        Cria a definição de um material PBR estilo vidro compatível com o Three.js e exportação .skp.
        """
        return {
            "name": name,
            "type": "SUMaterialRef",
            "is_glass": True,
            "color": color,
            "opacity": round(max(0.05, min(0.95, opacity)), 2),
            "refraction_index": round(refraction_index, 3),
            "three_pbr": {
                "transparent": True,
                "opacity": round(opacity, 2),
                "transmission": 0.92,
                "ior": round(refraction_index, 3),
                "roughness": 0.05,
                "metalness": 0.05,
                "depthWrite": False,
            },
        }
