"""
Ferramenta de Escala e Redimensionamento Paramétrico (Scale Tool - Zero DLL).

Implementa operações analíticas da ferramenta 'Escala' (Atalho S) do SketchUp:
1. Escala não-uniforme (sx, sy, sz) em torno de pivô arbitrário (centro ou canto oposto).
2. Construção de matriz afim de escala 4x4 column-major.
3. Transformação de vértices e cálculo de novos volumes e áreas superficiais.
"""

from typing import List, Tuple, Dict, Any


class ScaleTool:
    """Motor de redimensionamento e escala analítica."""

    @staticmethod
    def create_scale_matrix(
        scale_factors: Tuple[float, float, float],
        pivot: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    ) -> List[float]:
        """
        Cria matriz 4x4 column-major de escala em relação a um ponto pivô.
        scale_factors: (sx, sy, sz)
        pivot: (px, py, pz)
        """
        sx, sy, sz = scale_factors
        px, py, pz = pivot

        # Translação resultante: T(pivot) * S * T(-pivot)
        tx = px * (1.0 - sx)
        ty = py * (1.0 - sy)
        tz = pz * (1.0 - sz)

        return [
            sx,  0.0, 0.0, 0.0,  # Coluna 0
            0.0, sy,  0.0, 0.0,  # Coluna 1
            0.0, 0.0, sz,  0.0,  # Coluna 2
            tx,  ty,  tz,  1.0   # Coluna 3
        ]

    @classmethod
    def scale_vertices(
        cls,
        vertices: List[Tuple[float, float, float]],
        scale_factors: Tuple[float, float, float],
        pivot: Tuple[float, float, float]
    ) -> List[Tuple[float, float, float]]:
        """Aplica escala métrica diretamente a uma lista de vértices 3D."""
        sx, sy, sz = scale_factors
        px, py, pz = pivot
        scaled = []
        for x, y, z in vertices:
            nx = px + (x - px) * sx
            ny = py + (y - py) * sy
            nz = pz + (z - pz) * sz
            scaled.append((round(nx, 6), round(ny, 6), round(nz, 6)))
        return scaled
