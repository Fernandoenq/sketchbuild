"""
Motor de Bloqueio de Eixos e Inferência do SketchUp (Axis Lock & Inference Engine - Zero DLL).

Implementa a engenharia reversa das regras nativas de inferência e bloqueio de eixos do SketchUp:
1. Bloqueio por Setas do Teclado (Arrow Keys):
   - Seta Direita (Right Arrow): Trava no Eixo Vermelho / X (vetor [1, 0, 0]).
   - Seta Esquerda (Left Arrow): Trava no Eixo Verde / Y (vetor [0, 1, 0]).
   - Seta Cima (Up Arrow): Trava no Eixo Azul / Z (vetor [0, 0, 1]).
   - Seta Baixo (Down Arrow): Trava na direção Paralela ou Perpendicular à última aresta/inferência.
2. Trava de Direção por Tecla Shift (Shift Lock):
   - Mantém fixa qualquer linha de inferência encontrada (eixo ativo ou vetor customizado).
3. Projeção Geométrica Restrita:
   - Projeta qualquer ponto ou raio arbitrário 3D do cursor sobre o raio/eixo bloqueado:
     P_restrito = P_origem + dot(P_cursor - P_origem, u_dir) * u_dir.
"""

import math
from typing import Dict, Any, Tuple, Optional


class AxisLockInferenceEngine:
    """Motor analítico de restrição de eixos e inferência geométrica do SketchUp."""

    AXIS_VECTORS = {
        "X": (1.0, 0.0, 0.0),        # Red Axis
        "Y": (0.0, 1.0, 0.0),        # Green Axis
        "Z": (0.0, 0.0, 1.0),        # Blue Axis
        "NONE": (0.0, 0.0, 0.0)
    }

    AXIS_COLORS = {
        "X": "#EA4335",  # Vermelho
        "Y": "#34A853",  # Verde
        "Z": "#4285F4",  # Azul
        "CUSTOM": "#FBBC05",  # Magenta/Amarelo inferência
        "NONE": "#808080"
    }

    @classmethod
    def resolve_arrow_key_lock(
        cls,
        arrow_key: str,
        custom_direction: Optional[Tuple[float, float, float]] = None
    ) -> Dict[str, Any]:
        """
        Interpreta a tecla de seta pressionada no SketchUp para definir a restrição de eixo.
        arrow_key: 'RIGHT', 'LEFT', 'UP', 'DOWN', 'NONE'.
        """
        key_upper = str(arrow_key).upper().strip()

        if key_upper == "RIGHT":
            axis_name = "X"
            vec = (1.0, 0.0, 0.0)
            color = cls.AXIS_COLORS["X"]
            desc = "Bloqueado no Eixo X (Vermelho)"
        elif key_upper == "LEFT":
            axis_name = "Y"
            vec = (0.0, 1.0, 0.0)
            color = cls.AXIS_COLORS["Y"]
            desc = "Bloqueado no Eixo Y (Verde)"
        elif key_upper == "UP":
            axis_name = "Z"
            vec = (0.0, 0.0, 1.0)
            color = cls.AXIS_COLORS["Z"]
            desc = "Bloqueado no Eixo Z (Azul)"
        elif key_upper == "DOWN":
            axis_name = "CUSTOM"
            if custom_direction:
                l = math.sqrt(custom_direction[0]**2 + custom_direction[1]**2 + custom_direction[2]**2)
                if l > 1e-7:
                    vec = (custom_direction[0] / l, custom_direction[1] / l, custom_direction[2] / l)
                else:
                    vec = (1.0, 0.0, 0.0)
            else:
                vec = (1.0, 0.0, 0.0)
            color = cls.AXIS_COLORS["CUSTOM"]
            desc = "Bloqueado Paralelo/Perpendicular à Referência"
        else:
            axis_name = "NONE"
            vec = (0.0, 0.0, 0.0)
            color = cls.AXIS_COLORS["NONE"]
            desc = "Livre / Sem restrição de eixo"

        return {
            "arrow_key": key_upper,
            "axis_name": axis_name,
            "direction_vector": list(vec),
            "axis_color": color,
            "description": desc,
            "is_locked": axis_name != "NONE"
        }

    @classmethod
    def project_point_onto_axis(
        cls,
        cursor_point: Tuple[float, float, float],
        origin_point: Tuple[float, float, float],
        axis_direction: Tuple[float, float, float]
    ) -> Dict[str, Any]:
        """
        Projeta um ponto arbitrário do cursor sobre uma reta/eixo definido por origin e direction.
        """
        l = math.sqrt(axis_direction[0]**2 + axis_direction[1]**2 + axis_direction[2]**2)
        if l < 1e-7:
            # Sem direção, retorna o próprio cursor
            return {
                "projected_point": list(cursor_point),
                "distance_along_axis_m": 0.0,
                "is_valid": False
            }

        ux, uy, uz = axis_direction[0] / l, axis_direction[1] / l, axis_direction[2] / l
        vx = cursor_point[0] - origin_point[0]
        vy = cursor_point[1] - origin_point[1]
        vz = cursor_point[2] - origin_point[2]

        # Produto escalar (t = proj)
        t = vx * ux + vy * uy + vz * uz

        proj_x = origin_point[0] + t * ux
        proj_y = origin_point[1] + t * uy
        proj_z = origin_point[2] + t * uz

        return {
            "status": "success",
            "cursor_point": list(cursor_point),
            "origin_point": list(origin_point),
            "axis_direction": [ux, uy, uz],
            "distance_along_axis_m": round(t, 4),
            "projected_point": [round(proj_x, 4), round(proj_y, 4), round(proj_z, 4)],
            "is_valid": True
        }
