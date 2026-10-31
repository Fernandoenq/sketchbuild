"""
SketchBuild - Motor de Planos de Corte Múltiplos, Aninhamento e Inversão (Zero DLL / Pure Python)
Frente 67: Engenharia Reversa do SketchUp - SUSectionPlaneRef

Gerencia planos de corte ativos no modelo ou em componentes aninhados, inversão
de direção de corte, cálculo analítico de segmentos de contorno (cut lines) e geração
de loops poligonais de preenchimento (section fill) para visualização Three.js.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _dot(v1: Tuple[float, float, float], v2: Tuple[float, float, float]) -> float:
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]


def _norm(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
    length = math.sqrt(_dot(v, v))
    if length < 1e-9:
        return (0.0, 0.0, 1.0)
    return (v[0] / length, v[1] / length, v[2] / length)


class SectionPlaneEngine:
    """Motor de planos de corte canônicos SUSectionPlaneRef do SketchUp."""

    @classmethod
    def create_plane(
        cls,
        name: str = "Corte 1",
        symbol: str = "A",
        normal: Tuple[float, float, float] = (0.0, 0.0, -1.0),
        distance: float = 1.0,
        is_active: bool = True,
    ) -> Dict[str, Any]:
        """
        Cria um plano de corte SUSectionPlaneRef com equação Ax + By + Cz + D = 0.
        normal: vetor unitário (A, B, C)
        distance: parâmetro D da equação do plano
        """
        unit_norm = _norm(normal)
        return {
            "type": "SUSectionPlaneRef",
            "name": name,
            "symbol": symbol,
            "equation": [round(unit_norm[0], 6), round(unit_norm[1], 6), round(unit_norm[2], 6), round(distance, 6)],
            "normal": [round(unit_norm[0], 6), round(unit_norm[1], 6), round(unit_norm[2], 6)],
            "distance": round(distance, 6),
            "is_active": is_active,
            # Configuração direta para o Three.js (THREE.Plane onde normal aponta para fora do corte)
            "three_plane": {
                "normal": [round(unit_norm[0], 6), round(unit_norm[1], 6), round(unit_norm[2], 6)],
                "constant": round(-distance, 6),
            },
        }

    @classmethod
    def reverse_plane(cls, plane_data: Dict[str, Any]) -> Dict[str, Any]:
        """Inverte o sentido do corte (inversão da normal e do parâmetro D)."""
        eq = plane_data.get("equation", [0.0, 0.0, -1.0, 0.0])
        rev_eq = [-eq[0], -eq[1], -eq[2], -eq[3]]
        updated = dict(plane_data)
        updated["equation"] = rev_eq
        updated["normal"] = [rev_eq[0], rev_eq[1], rev_eq[2]]
        updated["distance"] = rev_eq[3]
        updated["three_plane"] = {
            "normal": [rev_eq[0], rev_eq[1], rev_eq[2]],
            "constant": round(-rev_eq[3], 6),
        }
        return updated

    @classmethod
    def slice_triangle(
        cls,
        v0: Tuple[float, float, float],
        v1: Tuple[float, float, float],
        v2: Tuple[float, float, float],
        normal: Tuple[float, float, float],
        d: float,
    ) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
        """
        Calcula a interseção entre um triângulo 3D e o plano Ax + By + Cz + D = 0.
        Retorna o segmento de reta 3D da interseção ou None se não houver corte transversal.
        """
        pts = [v0, v1, v2]
        dist = [_dot(pt, normal) + d for pt in pts]

        # Verificar se os vértices estão de lados opostos
        pos = [i for i, dist_val in enumerate(dist) if dist_val >= 1e-6]
        neg = [i for i, dist_val in enumerate(dist) if dist_val < -1e-6]

        if not pos or not neg:
            # Triângulo inteiramente de um lado ou estritamente coplanar
            return None

        # Há corte: 2 arestas interceptam o plano
        cut_points: List[Tuple[float, float, float]] = []

        edges = [(0, 1), (1, 2), (2, 0)]
        for i0, i1 in edges:
            d0 = dist[i0]
            d1 = dist[i1]
            if (d0 * d1) < 0.0:  # Aresta cruza o plano
                t = -d0 / (d1 - d0)
                p_inter = (
                    pts[i0][0] + t * (pts[i1][0] - pts[i0][0]),
                    pts[i0][1] + t * (pts[i1][1] - pts[i0][1]),
                    pts[i0][2] + t * (pts[i1][2] - pts[i0][2]),
                )
                cut_points.append(p_inter)
            elif abs(d0) < 1e-6:
                cut_points.append(pts[i0])

        # Remove pontos duplicados
        unique_pts: List[Tuple[float, float, float]] = []
        for p in cut_points:
            if not any(cls._dist_sq(p, up) < 1e-8 for up in unique_pts):
                unique_pts.append(p)

        if len(unique_pts) == 2:
            return (unique_pts[0], unique_pts[1])
        return None

    @classmethod
    def slice_mesh(
        cls,
        vertices: List[Tuple[float, float, float]],
        faces: List[List[int]],
        plane_equation: Tuple[float, float, float, float],
    ) -> Dict[str, Any]:
        """
        Calcula o fatiamento completo de uma malha por um plano de corte.
        Retorna os segmentos da seção (linhas de corte) e os loops de contorno fechados.
        """
        a, b, c, d = plane_equation
        norm = _norm((a, b, c))

        segments: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = []

        for face in faces:
            if len(face) < 3:
                continue
            # Triangulação em leque se tiver mais de 3 vértices
            v0 = vertices[face[0]]
            for i in range(1, len(face) - 1):
                v1 = vertices[face[i]]
                v2 = vertices[face[i + 1]]
                seg = cls.slice_triangle(v0, v1, v2, norm, d)
                if seg:
                    segments.append(seg)

        # Encadeamento dos segmentos em loops de contorno
        closed_loops = cls._chain_segments(segments)

        return {
            "total_cut_segments": len(segments),
            "cut_lines": [
                [
                    [round(p[0], 4), round(p[1], 4), round(p[2], 4)]
                    for p in seg
                ]
                for seg in segments
            ],
            "closed_loops_count": len(closed_loops),
            "loops": [
                [
                    [round(p[0], 4), round(p[1], 4), round(p[2], 4)]
                    for p in loop
                ]
                for loop in closed_loops
            ],
        }

    @staticmethod
    def _dist_sq(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> float:
        return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2 + (p1[2] - p2[2]) ** 2

    @classmethod
    def _chain_segments(
        cls,
        segments: List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]],
        tol: float = 1e-3,
    ) -> List[List[Tuple[float, float, float]]]:
        if not segments:
            return []

        remaining = list(segments)
        loops: List[List[Tuple[float, float, float]]] = []

        while remaining:
            first = remaining.pop(0)
            chain = [first[0], first[1]]
            extended = True

            while extended:
                extended = False
                head = chain[0]
                tail = chain[-1]

                for i, seg in enumerate(remaining):
                    p0, p1 = seg
                    if cls._dist_sq(tail, p0) <= tol**2:
                        chain.append(p1)
                        remaining.pop(i)
                        extended = True
                        break
                    elif cls._dist_sq(tail, p1) <= tol**2:
                        chain.append(p0)
                        remaining.pop(i)
                        extended = True
                        break
                    elif cls._dist_sq(head, p1) <= tol**2:
                        chain.insert(0, p0)
                        remaining.pop(i)
                        extended = True
                        break
                    elif cls._dist_sq(head, p0) <= tol**2:
                        chain.insert(0, p1)
                        remaining.pop(i)
                        extended = True
                        break

            loops.append(chain)

        return loops
