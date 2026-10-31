"""
Motor de Inversão ao Longo dos Eixos do SketchUp (Flip Along Tool - Zero DLL / Pure Python).

Implementa a operação nativa do SketchUp Pro 'Inverter ao longo de...' (Flip Along):
1. Inversão ao longo dos eixos do Componente ou do Modelo (Vermelho/X, Verde/Y, Azul/Z).
2. Cálculo de reflexão afim centrada no baricentro/bounding box da entidade.
3. Inversão automática do sentido de enrolamento dos triângulos (winding order)
   para preservar normais de face sólidas (manifold) e evitar faces invertidas.
4. Geração de matriz de transformação 4x4 compatível com Three.js e .SKP.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple, Union


class FlipAlongAxesEngine:
    """Motor analítico de espelhamento e inversão ao longo de eixos ortogonais ou arbitrários."""

    AXIS_VECTORS = {
        "red": (1.0, 0.0, 0.0),
        "green": (0.0, 1.0, 0.0),
        "blue": (0.0, 0.0, 1.0),
        "x": (1.0, 0.0, 0.0),
        "y": (0.0, 1.0, 0.0),
        "z": (0.0, 0.0, 1.0),
    }

    @classmethod
    def flip_along(
        cls,
        vertices: List[Tuple[float, float, float]],
        indices: Optional[List[int]] = None,
        axis: Union[str, Tuple[float, float, float]] = "red",
        center: Optional[Tuple[float, float, float]] = None,
    ) -> Dict[str, Any]:
        """
        Espelha geometricamente vértices e inverte o enrolamento de faces
        ao longo do eixo especificado (red, green, blue ou vetor unitário).
        """
        if not vertices:
            return {
                "vertices": [],
                "indices": indices or [],
                "flipped_axis": str(axis),
                "total_vertices": 0,
                "total_triangles": 0,
            }

        # Resolução do vetor diretor normal do plano de reflexão
        if isinstance(axis, str):
            axis_lower = axis.lower().strip()
            if axis_lower not in cls.AXIS_VECTORS:
                raise ValueError(f"Eixo desconhecido: {axis!r}. Opções válidas: 'red', 'green', 'blue'.")
            nx, ny, nz = cls.AXIS_VECTORS[axis_lower]
        else:
            nx, ny, nz = axis
            mag = math.sqrt(nx * nx + ny * ny + nz * nz)
            if mag < 1e-7:
                raise ValueError("Vetor diretor do eixo de inversão não pode ter comprimento zero.")
            nx, ny, nz = nx / mag, ny / mag, nz / mag

        # Determina o centro de rotação/inversão (padrão: centro da bounding box da geometria)
        if center is None:
            min_x = min(v[0] for v in vertices)
            max_x = max(v[0] for v in vertices)
            min_y = min(v[1] for v in vertices)
            max_y = max(v[1] for v in vertices)
            min_z = min(v[2] for v in vertices)
            max_z = max(v[2] for v in vertices)
            cx = (min_x + max_x) * 0.5
            cy = (min_y + max_y) * 0.5
            cz = (min_z + max_z) * 0.5
        else:
            cx, cy, cz = center

        # Aplica a reflexão de Householder centrada:
        # P' = P - 2 * ((P - C) . n) * n
        flipped_vertices = []
        for x, y, z in vertices:
            dx = x - cx
            dy = y - cy
            dz = z - cz
            dot = dx * nx + dy * ny + dz * nz
            fx = x - 2.0 * dot * nx
            fy = y - 2.0 * dot * ny
            fz = z - 2.0 * dot * nz
            flipped_vertices.append((round(fx, 6), round(fy, 6), round(fz, 6)))

        # Inverte o winding order dos triângulos para que a normal da face continue apontando para fora
        flipped_indices = []
        if indices and len(indices) >= 3:
            for i in range(0, len(indices), 3):
                if i + 2 < len(indices):
                    # Troca o segundo e terceiro vértice: (v0, v1, v2) -> (v0, v2, v1)
                    flipped_indices.extend([indices[i], indices[i + 2], indices[i + 1]])
                else:
                    flipped_indices.extend(indices[i:])
        else:
            flipped_indices = indices or []

        # Matriz 4x4 de transformação afim de reflexão
        # R = I - 2 * n * n^T
        m00 = 1.0 - 2.0 * nx * nx
        m01 = -2.0 * nx * ny
        m02 = -2.0 * nx * nz
        m10 = -2.0 * ny * nx
        m11 = 1.0 - 2.0 * ny * ny
        m12 = -2.0 * ny * nz
        m20 = -2.0 * nz * nx
        m21 = -2.0 * nz * ny
        m22 = 1.0 - 2.0 * nz * nz

        # Translação para preservar o centro C: T = C - R * C
        tx = cx - (m00 * cx + m01 * cy + m02 * cz)
        ty = cy - (m10 * cx + m11 * cy + m12 * cz)
        tz = cz - (m20 * cx + m21 * cy + m22 * cz)

        transform_matrix_16 = [
            round(m00, 6), round(m10, 6), round(m20, 6), 0.0,
            round(m01, 6), round(m11, 6), round(m21, 6), 0.0,
            round(m02, 6), round(m12, 6), round(m22, 6), 0.0,
            round(tx, 6),  round(ty, 6),  round(tz, 6),  1.0,
        ]

        return {
            "entity_type": "FlipAlongResult",
            "axis": str(axis),
            "axis_vector": (round(nx, 4), round(ny, 4), round(nz, 4)),
            "center": (round(cx, 4), round(cy, 4), round(cz, 4)),
            "vertices": flipped_vertices,
            "indices": flipped_indices,
            "total_vertices": len(flipped_vertices),
            "total_triangles": len(flipped_indices) // 3 if flipped_indices else 0,
            "transform_matrix_16": transform_matrix_16,
            "is_winding_inverted": True,
        }
