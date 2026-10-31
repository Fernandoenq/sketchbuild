"""
SketchBuild - Motor de Curvas e Polilinhas Soldadas (Zero DLL / Pure Python)
Frente 66: Engenharia Reversa do SketchUp - SUCurveRef e SUArcCurveRef

Gerencia cadeias de arestas conectadas (welded polylines / splines discretizadas),
detecção analítica de arcos e circunferências 3D, geração paramétrica de arcos
e compatibilidade canônica com SUCurveRef e SUArcCurveRef do SketchUp C API.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _dist_sq(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2


def _dist(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
    return math.sqrt(_dist_sq(p1, p2))


def _dot(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]


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


class CurveEngine:
    """Motor de curvas soldadas e arcos geométricos analíticos do SketchUp."""

    @classmethod
    def weld_edges(
        cls,
        edges: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]],
        tolerance: float = 1e-4,
    ) -> List[List[Tuple[float, float, float]]]:
        """
        Recebe uma lista de arestas desconexas ou fora de ordem e une as que compartilham vértices
        em cadeias contínuas de vértices ordenados (polilinhas soldadas).
        """
        if not edges:
            return []

        remaining = [((e[0][0], e[0][1], e[0][2]), (e[1][0], e[1][1], e[1][2])) for e in edges]
        chains: List[List[Tuple[float, float, float]]] = []

        while remaining:
            first_edge = remaining.pop(0)
            chain = [first_edge[0], first_edge[1]]
            extended = True

            while extended:
                extended = False
                head = chain[0]
                tail = chain[-1]

                for i, edge in enumerate(remaining):
                    p0, p1 = edge
                    # Checa cauda com p0
                    if _dist(tail, p0) <= tolerance:
                        chain.append(p1)
                        remaining.pop(i)
                        extended = True
                        break
                    # Checa cauda com p1
                    elif _dist(tail, p1) <= tolerance:
                        chain.append(p0)
                        remaining.pop(i)
                        extended = True
                        break
                    # Checa cabeça com p1
                    elif _dist(head, p1) <= tolerance:
                        chain.insert(0, p0)
                        remaining.pop(i)
                        extended = True
                        break
                    # Checa cabeça com p0
                    elif _dist(head, p0) <= tolerance:
                        chain.insert(0, p1)
                        remaining.pop(i)
                        extended = True
                        break

            chains.append(chain)

        return chains

    @classmethod
    def detect_arc(
        cls,
        vertices: List[Tuple[float, float, float]],
        tolerance: float = 0.005,
    ) -> Optional[Dict[str, Any]]:
        """
        Analisa uma cadeia de vértices 3D ordenada e detecta se representam um arco ou círculo analítico.
        Retorna dicionário no padrão SUArcCurveRef ou None se não for um arco.
        """
        n_pts = len(vertices)
        if n_pts < 3:
            return None

        # 1. Estimar plano médio através dos 3 primeiros pontos ou pontos extremos
        p0 = vertices[0]
        p_mid = vertices[n_pts // 2]
        p_end = vertices[-1]

        v1 = (p_mid[0] - p0[0], p_mid[1] - p0[1], p_mid[2] - p0[2])
        v2 = (p_end[0] - p0[0], p_end[1] - p0[1], p_end[2] - p0[2])
        normal = _norm(_cross(v1, v2))

        # Se os pontos forem colineares, não é arco
        if _dist_sq(normal, (0.0, 0.0, 0.0)) < 1e-8:
            return None

        # 2. Encontrar centro da circunferência circunscrita através de 3 pontos (p0, p_mid, p_end)
        # Vetor perpendicular a v1 no plano da curva
        d1 = _cross(normal, v1)
        d2 = _cross(normal, (p_end[0] - p_mid[0], p_end[1] - p_mid[1], p_end[2] - p_mid[2]))

        m1 = ((p0[0] + p_mid[0]) * 0.5, (p0[1] + p_mid[1]) * 0.5, (p0[2] + p_mid[2]) * 0.5)
        m2 = ((p_mid[0] + p_end[0]) * 0.5, (p_mid[1] + p_end[1]) * 0.5, (p_mid[2] + p_end[2]) * 0.5)

        # Resolver interseção 2D das retas m1 + t*d1 e m2 + s*d2
        # Projetado no eixo principal
        delta_m = (m2[0] - m1[0], m2[1] - m1[1], m2[2] - m1[2])
        cross_d = _cross(d1, d2)
        denom = _dot(cross_d, normal)

        if abs(denom) < 1e-7:
            return None

        t = _dot(_cross(delta_m, d2), normal) / denom
        center = (m1[0] + t * d1[0], m1[1] + t * d1[1], m1[2] + t * d1[2])

        radius = _dist(center, p0)
        if radius < 1e-4:
            return None

        # 3. Testar se todos os vértices da cadeia estão a uma distância `radius` do centro
        max_error = 0.0
        for pt in vertices:
            d = abs(_dist(center, pt) - radius)
            if d > max_error:
                max_error = d

        if max_error > (radius * tolerance + tolerance):
            return None

        # 4. Calcular ângulos e vetor de referência
        ref_vec = _norm((p0[0] - center[0], p0[1] - center[1], p0[2] - center[2]))
        y_axis = _norm(_cross(normal, ref_vec))

        angles: List[float] = []
        for pt in vertices:
            v = (pt[0] - center[0], pt[1] - center[1], pt[2] - center[2])
            x_proj = _dot(v, ref_vec)
            y_proj = _dot(v, y_axis)
            ang = math.atan2(y_proj, x_proj)
            if ang < 0:
                ang += 2 * math.pi
            angles.append(ang)

        is_full_circle = _dist(vertices[0], vertices[-1]) <= tolerance

        start_angle = 0.0
        end_angle = (2 * math.pi) if is_full_circle else angles[-1]

        return {
            "type": "SUArcCurveRef",
            "is_circle": is_full_circle,
            "center": [round(c, 4) for c in center],
            "radius": round(radius, 4),
            "normal": [round(n, 4) for n in normal],
            "ref_vector": [round(r, 4) for r in ref_vec],
            "start_angle_rad": round(start_angle, 4),
            "end_angle_rad": round(end_angle, 4),
            "num_segments": n_pts - (1 if is_full_circle else 0),
            "max_fitting_error": round(max_error, 6),
        }

    @classmethod
    def create_arc(
        cls,
        center: Tuple[float, float, float],
        radius: float,
        normal: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        ref_vector: Optional[Tuple[float, float, float]] = None,
        start_angle_rad: float = 0.0,
        end_angle_rad: float = 2 * math.pi,
        num_segments: int = 24,
    ) -> Dict[str, Any]:
        """
        Gera uma curva de arco canônica SUArcCurveRef discretizada com vértices e arestas contíguas.
        """
        n = _norm(normal)
        if ref_vector is None:
            # Encontra um vetor perpendicular à normal
            if abs(n[2]) < 0.9:
                ref = _norm(_cross(n, (0.0, 0.0, 1.0)))
            else:
                ref = _norm(_cross(n, (1.0, 0.0, 0.0)))
        else:
            ref = _norm(ref_vector)

        y_axis = _norm(_cross(n, ref))
        num_segments = max(3, num_segments)
        is_circle = abs(abs(end_angle_rad - start_angle_rad) - 2 * math.pi) < 1e-5

        total_pts = num_segments if is_circle else num_segments + 1
        delta_ang = (end_angle_rad - start_angle_rad) / num_segments

        vertices: List[List[float]] = []
        for i in range(total_pts):
            theta = start_angle_rad + i * delta_ang
            cos_t = math.cos(theta)
            sin_t = math.sin(theta)
            px = center[0] + radius * (cos_t * ref[0] + sin_t * y_axis[0])
            py = center[1] + radius * (cos_t * ref[1] + sin_t * y_axis[1])
            pz = center[2] + radius * (cos_t * ref[2] + sin_t * y_axis[2])
            vertices.append([round(px, 4), round(py, 4), round(pz, 4)])

        edges: List[List[int]] = []
        for i in range(num_segments):
            next_idx = (i + 1) % len(vertices) if is_circle else (i + 1)
            edges.append([i, next_idx])

        return {
            "type": "SUArcCurveRef",
            "is_circle": is_circle,
            "center": [round(c, 4) for c in center],
            "radius": round(radius, 4),
            "normal": [round(c, 4) for c in n],
            "ref_vector": [round(c, 4) for c in ref],
            "start_angle_rad": round(start_angle_rad, 4),
            "end_angle_rad": round(end_angle_rad, 4),
            "num_segments": num_segments,
            "vertices": vertices,
            "edges": edges,
        }
