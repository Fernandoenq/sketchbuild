"""Engine de Engenharia Reversa da Ferramenta Dividir Aresta (Edge Divide Tool).

Divide uma aresta ou segmento linear em N partes perfeitamente equidistantes,
gerando novos vertices intermediarios e subarestas, com suporte a parser de VCB.
"""

from __future__ import annotations
import math
import re
from typing import Any


class EdgeDivideEngine:
    """Implementa o particionamento analitico de arestas em N segmentos."""

    @staticmethod
    def parse_vcb_segments(vcb_text: str, default_segments: int = 4) -> int:
        """Extrai o numero de segmentos da digitacao no VCB (ex: '6', '6s', '12 segments')."""
        if not vcb_text:
            return default_segments
        cleaned = vcb_text.strip().lower()
        match = re.search(r"^(\d+)\s*(s|seg|segmentos|segments)?$", cleaned)
        if match:
            val = int(match.group(1))
            return max(2, min(val, 1000))
        return default_segments

    @classmethod
    def divide_edge(
        cls,
        start_point: list[float],
        end_point: list[float],
        num_segments: int | str = 4
    ) -> dict[str, Any]:
        """Divide o segmento linear [start_point, end_point] em N partes iguais."""
        if isinstance(num_segments, str):
            n = cls.parse_vcb_segments(num_segments)
        else:
            n = max(2, int(num_segments))

        p0 = [float(c) for c in start_point]
        p1 = [float(c) for c in end_point]

        dx = p1[0] - p0[0]
        dy = p1[1] - p0[1]
        dz = p1[2] - p0[2]
        total_length = math.sqrt(dx * dx + dy * dy + dz * dz)
        segment_length = total_length / n if n > 0 else 0.0

        divided_points = []
        sub_edges = []

        for k in range(n + 1):
            t = k / n
            pk = [
                round(p0[0] + t * dx, 4),
                round(p0[1] + t * dy, 4),
                round(p0[2] + t * dz, 4),
            ]
            divided_points.append(pk)

        for k in range(n):
            sub_edges.append({
                "segment_index": k + 1,
                "start": divided_points[k],
                "end": divided_points[k + 1],
                "length_m": round(segment_length, 4)
            })

        return {
            "success": True,
            "num_segments": n,
            "total_length_m": round(total_length, 4),
            "segment_length_m": round(segment_length, 4),
            "vertices_count": len(divided_points),
            "points": divided_points,
            "sub_edges": sub_edges,
        }
