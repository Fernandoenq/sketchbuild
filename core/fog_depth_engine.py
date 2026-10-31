"""
SketchBuild - Motor de Estilos de Névoa e Profundidade Atmosférica (Zero DLL / Pure Python)
Frente 77: Engenharia Reversa do SketchUp - SUStyleRef (Fog & Depth Cue)

Gerencia as configurações de névoa atmosférica do SketchUp, cálculo automático de profundidade
baseado na Bounding Box do modelo e mapeamento direto para THREE.Fog.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class FogDepthEngine:
    """Motor de cálculo e configuração de névoa de cena e atenuação de profundidade."""

    DEFAULT_FOG_COLOR = "#dcdde1"

    @classmethod
    def configure_fog(
        cls,
        enabled: bool = True,
        start_dist_m: float = 10.0,
        end_dist_m: float = 100.0,
        color_hex: str = DEFAULT_FOG_COLOR,
    ) -> Dict[str, Any]:
        """
        Configura os parâmetros de névoa canônicos SUStyleRef do SketchUp.
        """
        start_val = max(0.0, start_dist_m)
        end_val = max(start_val + 0.1, end_dist_m)

        return {
            "entity_type": "SUStyleFog",
            "enabled": enabled,
            "start_distance_m": round(start_val, 2),
            "end_distance_m": round(end_val, 2),
            "color": color_hex,
            "three_fog": {
                "type": "Fog",
                "color": color_hex,
                "near": round(start_val, 2),
                "far": round(end_val, 2),
            },
            "status": "NÉVOA ATIVADA" if enabled else "NÉVOA DESATIVADA",
        }

    @classmethod
    def calculate_auto_fog_from_bbox(
        cls,
        min_point: Tuple[float, float, float],
        max_point: Tuple[float, float, float],
        color_hex: str = DEFAULT_FOG_COLOR,
    ) -> Dict[str, Any]:
        """
        Calcula as distâncias ideais de névoa linear com base nas dimensões da cena.
        """
        dx = max_point[0] - min_point[0]
        dy = max_point[1] - min_point[1]
        dz = max_point[2] - min_point[2]
        diag = math.sqrt(dx**2 + dy**2 + dz**2)
        diag = max(5.0, diag)

        # Início em 0.6x da diagonal e fim em 2.5x da diagonal
        start_dist = diag * 0.6
        end_dist = diag * 2.5

        return cls.configure_fog(
            enabled=True,
            start_dist_m=start_dist,
            end_dist_m=end_dist,
            color_hex=color_hex,
        )
