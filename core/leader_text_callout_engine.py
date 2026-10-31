"""
SketchBuild - Motor de Chamadas de Texto 3D e Rótulo de Área de Face (Zero DLL / Pure Python)
Ferramenta Nativa Oficial do SketchUp: Leader Text & Face Area Callout (SUTextRef)

Implementa:
1. Cálculo analítico exato de área 3D de faces poligonais planares (Shoelace 3D / Produto Vetorial).
2. Geração de rótulos de chamada com linha líder (leader line) ancorada no baricentro ou vértice da face.
3. Posicionamento de tela Face-Me / Billboard para renderização em Three.js / WebGL.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _cross(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )


def _dot(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
    return sum(v1[i] * v2[i] for i in range(3))


def _norm(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    length = math.sqrt(_dot(v, v))
    if length < 1e-9:
        return (0.0, 0.0, 1.0)
    return (v[0] / length, v[1] / length, v[2] / length)


class LeaderTextCalloutEngine:
    """Motor de geração de anotações com linha de chamada líder e cálculo automático de área de face."""

    @classmethod
    def calculate_polygon_area_3d(cls, vertices: List[Tuple[float, float, float]]) -> float:
        """
        Calcula a área tridimensional de um polígono planar 3D arbitrário
        usando a fórmula de Stokes / Shoelace 3D via produto vetorial cumulativo.
        """
        n = len(vertices)
        if n < 3:
            return 0.0

        total_cross = [0.0, 0.0, 0.0]
        for i in range(n):
            v0 = vertices[i]
            v1 = vertices[(i + 1) % n]
            cp = _cross(v0, v1)
            total_cross[0] += cp[0]
            total_cross[1] += cp[1]
            total_cross[2] += cp[2]

        area = 0.5 * math.sqrt(sum(c**2 for c in total_cross))
        return round(area, 4)

    @classmethod
    def calculate_face_centroid(cls, vertices: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
        """Calcula o baricentro (centro geométrico) de um conjunto de vértices 3D."""
        n = len(vertices)
        if n == 0:
            return (0.0, 0.0, 0.0)
        cx = sum(v[0] for v in vertices) / n
        cy = sum(v[1] for v in vertices) / n
        cz = sum(v[2] for v in vertices) / n
        return (round(cx, 4), round(cy, 4), round(cz, 4))

    @classmethod
    def create_leader_callout(
        cls,
        anchor_point: Tuple[float, float, float],
        text: str,
        offset_vector: Tuple[float, float, float] = (0.4, 0.4, 0.3),
        leader_type: str = "BENT",  # BENT (dois segmentos com cotovelo), STRAIGHT (linha reta)
        arrow_type: str = "ARROW",  # ARROW, DOT, NONE, CLOSED_ARROW
        elbow_dx: float = 0.2,
    ) -> Dict[str, Any]:
        """
        Gera uma anotação de texto com linha de chamada 3D compatível com SUTextRef.
        """
        p0 = (float(anchor_point[0]), float(anchor_point[1]), float(anchor_point[2]))
        p_target = (
            p0[0] + float(offset_vector[0]),
            p0[1] + float(offset_vector[1]),
            p0[2] + float(offset_vector[2]),
        )

        segments = []
        if leader_type == "BENT":
            # Ponto de cotovelo com extensão horizontal no plano de visão
            elbow_pt = (p_target[0] - elbow_dx, p_target[1], p_target[2])
            segments.append([list(p0), list(elbow_pt)])
            segments.append([list(elbow_pt), list(p_target)])
        else:
            segments.append([list(p0), list(p_target)])

        line_length = math.sqrt(sum((p_target[i] - p0[i]) ** 2 for i in range(3)))

        return {
            "entity_type": "SUTextRef",
            "is_leader": True,
            "text": text,
            "anchor_point": list(p0),
            "text_position": [round(c, 4) for c in p_target],
            "leader_segments": segments,
            "leader_type": leader_type,
            "arrow_type": arrow_type.upper(),
            "leader_length_m": round(line_length, 4),
            "render_props": {
                "billboard": True,
                "color": "#111827",
                "arrow_size": 0.04,
                "line_width": 1.5,
            },
            "status": "CHAMADA DE TEXTO LÍDER CRIADA",
        }

    @classmethod
    def create_face_area_callout(
        cls,
        face_vertices: List[Tuple[float, float, float]],
        prefix: str = "Área: ",
        unit: str = "m²",
        offset_vector: Tuple[float, float, float] = (0.3, 0.3, 0.4),
    ) -> Dict[str, Any]:
        """
        Calcula a área da face e gera automaticamente o rótulo de chamada Leader Text oficial do SketchUp.
        """
        area_val = cls.calculate_polygon_area_3d(face_vertices)
        centroid = cls.calculate_face_centroid(face_vertices)
        formatted_text = f"{prefix}{area_val:.2f} {unit}"

        callout = cls.create_leader_callout(
            anchor_point=centroid,
            text=formatted_text,
            offset_vector=offset_vector,
            leader_type="BENT",
            arrow_type="DOT",
        )
        callout["face_area_m2"] = area_val
        callout["vertex_count"] = len(face_vertices)
        return callout
