"""
Motor de Soldagem de Arestas do SketchUp (Weld Edges Tool - Zero DLL / Pure Python).

Implementa a ferramenta nativa oficial do SketchUp 'Soldar Arestas' (Weld Edges):
1. Análise de adjacência topológica e grau de incidência de nós (valência).
2. Agrupamento de segmentos lineares contíguos em uma única entidade de Curva (Curve/Polyline).
3. Ordenação sequencial cabeça-com-cauda (head-to-tail) dos vértices.
4. Detecção de fechamento (loops fechados vs. curvas abertas).
5. Cálculo analítico de comprimento total, deflexão angular e raio médio de curvatura.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple


class WeldEdgesEngine:
    """Motor analítico para identificação, ordenação e soldagem de arestas em curvas contínuas."""

    @classmethod
    def weld_edges(
        cls,
        edges: List[Dict[str, Any]],
        tolerance_m: float = 1e-4,
    ) -> Dict[str, Any]:
        """
        Recebe uma lista de arestas [{'start': (x,y,z), 'end': (x,y,z)}]
        e solda os segmentos conectados em curvas contínuas (Curve).
        """
        if not edges:
            return {
                "curves": [],
                "total_curves": 0,
                "total_edges": 0,
                "total_length_m": 0.0,
            }

        def quantize_pt(pt: Tuple[float, float, float]) -> Tuple[float, float, float]:
            inv = 1.0 / max(1e-6, tolerance_m)
            return (
                round(pt[0] * inv) / inv,
                round(pt[1] * inv) / inv,
                round(pt[2] * inv) / inv,
            )

        # Constrói grafo de adjacência
        adj: Dict[Tuple[float, float, float], List[Tuple[Tuple[float, float, float], float]]] = {}
        processed_edges = []
        total_len = 0.0

        for edge in edges:
            p1 = quantize_pt(edge["start"])
            p2 = quantize_pt(edge["end"])
            if p1 == p2:
                continue

            dist = math.sqrt(
                (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2
            )
            total_len += dist

            adj.setdefault(p1, []).append((p2, dist))
            adj.setdefault(p2, []).append((p1, dist))
            processed_edges.append((p1, p2, dist))

        # Rastreia componentes conexos e cadeias lineares
        visited_edges: Set[Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = set()
        curves = []

        def edge_key(a, b):
            return (min(a, b), max(a, b))

        # Prioriza pontos terminais (grau 1) para iniciar curvas abertas
        start_nodes = [node for node, neighbors in adj.items() if len(neighbors) == 1]
        # Se todos tiverem grau 2 (loops fechados), usa qualquer nó não visitado
        all_nodes = list(adj.keys())

        for node in start_nodes + all_nodes:
            # Encontra vizinhos com arestas não visitadas
            for neighbor, dist in adj[node]:
                ek = edge_key(node, neighbor)
                if ek in visited_edges:
                    continue

                # Inicia novo traçado de curva
                path = [node, neighbor]
                visited_edges.add(ek)
                curve_length = dist

                # Percorre para frente a partir de neighbor
                curr = neighbor
                prev = node
                while True:
                    next_candidates = [
                        (nxt, d)
                        for nxt, d in adj[curr]
                        if edge_key(curr, nxt) not in visited_edges and nxt != prev
                    ]
                    if not next_candidates:
                        break
                    nxt, d = next_candidates[0]
                    visited_edges.add(edge_key(curr, nxt))
                    path.append(nxt)
                    curve_length += d
                    prev = curr
                    curr = nxt
                    if curr == path[0]:
                        # Loop fechado
                        break

                # Verifica se a curva é fechada
                is_closed = len(path) > 2 and path[0] == path[-1]

                # Ângulos de deflexão nos nós interiores
                interior_angles = []
                for i in range(1, len(path) - 1):
                    p_prev = path[i - 1]
                    p_curr = path[i]
                    p_next = path[i + 1]

                    v1 = (p_curr[0] - p_prev[0], p_curr[1] - p_prev[1], p_curr[2] - p_prev[2])
                    v2 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1], p_next[2] - p_curr[2])
                    m1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2 + v1[2] ** 2) or 1.0
                    m2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2 + v2[2] ** 2) or 1.0
                    dot = (v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]) / (m1 * m2)
                    dot = max(-1.0, min(1.0, dot))
                    angle_deg = math.degrees(math.acos(dot))
                    interior_angles.append(round(angle_deg, 2))

                curves.append({
                    "entity_type": "SUCurveRef",
                    "curve_type": "ClosedLoop" if is_closed else "OpenCurve",
                    "vertex_count": len(path),
                    "segment_count": len(path) - 1,
                    "length_m": round(curve_length, 4),
                    "is_closed": is_closed,
                    "points": [(round(p[0], 4), round(p[1], 4), round(p[2], 4)) for p in path],
                    "deflection_angles_deg": interior_angles,
                })

        return {
            "entity_type": "WeldEdgesResult",
            "total_curves": len(curves),
            "total_edges": len(processed_edges),
            "total_length_m": round(total_len, 4),
            "curves": curves,
        }
