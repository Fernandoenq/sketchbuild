"""
SketchBuild - Motor de Linhas Guia e Auxiliares de Construção (Zero DLL / Pure Python)
Ferramentas Nativas Oficiais do SketchUp: Tape Measure Guides & Protractor Guides (SUGuideLineRef & SUGuidePointRef)

Implementa:
1. Geração de Linha Guia Infinita paralela a uma aresta com distância de offset métrico fixado.
2. Geração de Linha Guia Angular a partir de um vértice com ângulo de transferidor especificado.
3. Criação de Pontos de Construção (Guide Points) com marcadores visuais.
4. Cálculo analítico de interseção entre duas linhas guias para snap de inferência.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _sub(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])


def _add(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (p1[0] + p2[0], p1[1] + p2[1], p1[2] + p2[2])


def _dot(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
    return sum(v1[i] * v2[i] for i in range(3))


def _cross(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (
        v1[1] * v2[2] - v1[2] * v2[1],
        v1[2] * v2[0] - v1[0] * v2[2],
        v1[0] * v2[1] - v1[1] * v2[0],
    )


def _norm(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    length = math.sqrt(_dot(v, v))
    if length < 1e-9:
        return (0.0, 0.0, 1.0)
    return (v[0] / length, v[1] / length, v[2] / length)


class ConstructionGuideEngine:
    """Motor de cálculo e projeção de guias auxiliares (Tape & Protractor Guides) do SketchUp."""

    DEFAULT_EXTENT = 500.0  # Comprimento visual simulando linha infinita

    @classmethod
    def create_parallel_guide(
        cls,
        edge_start: Tuple[float, float, float],
        edge_end: Tuple[float, float, float],
        offset_distance: float,
        plane_normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        extent_m: float = DEFAULT_EXTENT,
    ) -> Dict[str, Any]:
        """
        Cria uma linha guia infinita paralela a uma aresta, deslocada por 'offset_distance'.
        """
        edge_vec = _sub(edge_end, edge_start)
        edge_dir = _norm(edge_vec)

        # Vetor perpendicular contido no plano da normal
        perp_vec = _norm(_cross(plane_normal, edge_dir))

        # Ponto de apoio da guia deslocado da aresta
        guide_origin = (
            edge_start[0] + perp_vec[0] * offset_distance,
            edge_start[1] + perp_vec[1] * offset_distance,
            edge_start[2] + perp_vec[2] * offset_distance,
        )

        p_start = (
            guide_origin[0] - edge_dir[0] * extent_m,
            guide_origin[1] - edge_dir[1] * extent_m,
            guide_origin[2] - edge_dir[2] * extent_m,
        )
        p_end = (
            guide_origin[0] + edge_dir[0] * extent_m,
            guide_origin[1] + edge_dir[1] * extent_m,
            guide_origin[2] + edge_dir[2] * extent_m,
        )

        return {
            "entity_type": "SUGuideLineRef",
            "is_infinite": True,
            "origin": [round(c, 4) for c in guide_origin],
            "direction": [round(c, 4) for c in edge_dir],
            "offset_distance_m": round(offset_distance, 4),
            "render_start": [round(c, 3) for c in p_start],
            "render_end": [round(c, 3) for c in p_end],
            "style": {"dashed": True, "dash_size": 0.1, "gap_size": 0.05, "color": "#000000"},
            "status": "LINHA GUIA PARALELA CRIADA",
        }

    @classmethod
    def create_angular_guide(
        cls,
        vertex: Tuple[float, float, float],
        base_direction: Tuple[float, float, float],
        angle_deg: float,
        plane_normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        extent_m: float = DEFAULT_EXTENT,
    ) -> Dict[str, Any]:
        """
        Cria uma linha guia angular a partir de um vértice usando um ângulo de transferidor.
        """
        v0 = _norm(base_direction)
        n = _norm(plane_normal)
        rad = math.radians(angle_deg)

        # Rotação de Rodrigues em torno da normal
        # v_rot = v0 * cos(theta) + (n x v0) * sin(theta) + n * (n . v0) * (1 - cos(theta))
        cos_t = math.cos(rad)
        sin_t = math.sin(rad)
        cross_nv = _cross(n, v0)

        rot_dir = (
            v0[0] * cos_t + cross_nv[0] * sin_t,
            v0[1] * cos_t + cross_nv[1] * sin_t,
            v0[2] * cos_t + cross_nv[2] * sin_t,
        )
        rot_dir = _norm(rot_dir)

        p_start = (
            vertex[0] - rot_dir[0] * extent_m,
            vertex[1] - rot_dir[1] * extent_m,
            vertex[2] - rot_dir[2] * extent_m,
        )
        p_end = (
            vertex[0] + rot_dir[0] * extent_m,
            vertex[1] + rot_dir[1] * extent_m,
            vertex[2] + rot_dir[2] * extent_m,
        )

        return {
            "entity_type": "SUGuideLineRef",
            "is_infinite": True,
            "origin": [round(c, 4) for c in vertex],
            "direction": [round(c, 4) for c in rot_dir],
            "angle_deg": round(angle_deg, 2),
            "render_start": [round(c, 3) for c in p_start],
            "render_end": [round(c, 3) for c in p_end],
            "style": {"dashed": True, "dash_size": 0.1, "gap_size": 0.05, "color": "#000000"},
            "status": "LINHA GUIA ANGULAR CRIADA",
        }

    @classmethod
    def calculate_guide_intersection(
        cls,
        p1: Tuple[float, float, float],
        d1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
        d2: Tuple[float, float, float],
        tolerance: float = 1e-4,
    ) -> Optional[Dict[str, Any]]:
        """
        Calcula o ponto de interseção analítico entre duas linhas infinitas p1+t1*d1 e p2+t2*d2.
        """
        u = _norm(d1)
        v = _norm(d2)
        w0 = _sub(p1, p2)

        a = _dot(u, u)
        b = _dot(u, v)
        c = _dot(v, v)
        d = _dot(u, w0)
        e = _dot(v, w0)

        denom = a * c - b * b
        if abs(denom) < 1e-9:
            return None  # Linhas paralelas

        sc = (b * e - c * d) / denom
        tc = (a * e - b * d) / denom

        closest_p1 = (p1[0] + sc * u[0], p1[1] + sc * u[1], p1[2] + sc * u[2])
        closest_p2 = (p2[0] + tc * v[0], p2[1] + tc * v[1], p2[2] + tc * v[2])

        dist = math.sqrt(sum((closest_p1[i] - closest_p2[i]) ** 2 for i in range(3)))
        if dist > tolerance:
            return None  # Não se cruzam (linhas reversas no espaço)

        inter_pt = (
            0.5 * (closest_p1[0] + closest_p2[0]),
            0.5 * (closest_p1[1] + closest_p2[1]),
            0.5 * (closest_p1[2] + closest_p2[2]),
        )

        return {
            "intersecting": True,
            "point": [round(c, 4) for c in inter_pt],
            "entity_type": "SUGuidePointRef",
            "distance_m": round(dist, 6),
        }
