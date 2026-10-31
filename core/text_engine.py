"""
SketchBuild - Motor de Textos 2D na Tela e Rótulos Anotativos de Líder (Zero DLL / Pure Python)
Frente 71: Engenharia Reversa do SketchUp - SUTextRef (ScreenText & LeaderText)

Gerencia a criação e projeção de textos de tela fixos (HUD) e textos apontados por flecha/líder
(Leader Text) ancorados em pontos 3D da geometria, compatíveis com a entidade SUTextRef do SketchUp.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class TextEngine:
    """Motor de textos 2D de tela e anotações com linha de chamada (líder) do SketchUp."""

    @classmethod
    def create_screen_text(
        cls,
        text: str,
        screen_x: float = 20.0,
        screen_y: float = 20.0,
        font_name: str = "Arial",
        font_size_pt: int = 12,
        color_hex: str = "#000000",
        bold: bool = False,
        italic: bool = False,
    ) -> Dict[str, Any]:
        """
        Cria uma anotação de texto 2D fixada em coordenadas de tela (HUD).
        """
        return {
            "type": "SUTextRef",
            "is_screen_text": True,
            "text": text,
            "screen_position": [round(screen_x, 1), round(screen_y, 1)],
            "font": {
                "name": font_name,
                "size_pt": font_size_pt,
                "bold": bold,
                "italic": italic,
                "color": color_hex,
            },
            "status": "TEXTO DE TELA CRIADO",
        }

    @classmethod
    def create_leader_text(
        cls,
        text: str,
        anchor_point: Tuple[float, float, float],
        offset_vector: Tuple[float, float, float] = (0.5, 0.5, 0.5),
        arrow_type: str = "ARROW",  # ARROW, DOT, NONE, SLASH
        font_name: str = "Arial",
        font_size_pt: int = 10,
        color_hex: str = "#000000",
    ) -> Dict[str, Any]:
        """
        Cria um rótulo anotativo apontado por linha de chamada (leader) ancorado em um ponto 3D.
        """
        p_anchor = [round(c, 4) for c in anchor_point]
        p_text = [
            round(anchor_point[0] + offset_vector[0], 4),
            round(anchor_point[1] + offset_vector[1], 4),
            round(anchor_point[2] + offset_vector[2], 4),
        ]

        leader_len = math.sqrt(sum(v**2 for v in offset_vector))

        return {
            "type": "SUTextRef",
            "is_screen_text": False,
            "text": text,
            "anchor_point": p_anchor,
            "text_position_3d": p_text,
            "offset_vector": [round(v, 4) for v in offset_vector],
            "leader_length_m": round(leader_len, 4),
            "arrow_type": arrow_type.upper(),
            "leader_line_segments": [
                [p_anchor, p_text]
            ],
            "font": {
                "name": font_name,
                "size_pt": font_size_pt,
                "color": color_hex,
            },
            "three_render": {
                "billboard": True,
                "line_color": color_hex,
                "line_width": 1.5,
            },
            "status": "TEXTO COM LINHA DE CHAMADA (LEADER) CRIADO",
        }
