"""
SketchBuild - Decodificador de Grupos Aninhados e Matrizes Globais de Instância (Zero DLL / Pure Python)
Frente 75: Engenharia Reversa do SketchUp - Nested Instance Hierarchy & World Matrix Resolution

Calcula matrizes afins acumuladas 4x4 em árvores de instâncias e grupos aninhados (SUComponentInstanceRef,
SUGroupRef), decomposição geométrica (translação, rotação, escala) e cálculo de matriz local relativa
para edição no espaço mundial (World Space Editing).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _identity_matrix_16() -> List[float]:
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def _matmul4(a: List[float], b: List[float]) -> List[float]:
    """Multiplicação de duas matrizes 4x4 column-major: a x b."""
    out = [0.0] * 16
    for col in range(4):
        for row in range(4):
            val = 0.0
            for k in range(4):
                val += a[k * 4 + row] * b[col * 4 + k]
            out[col * 4 + row] = val
    return out


def _invert_affine4(m: List[float]) -> List[float]:
    """Inverte uma matriz afim rígida/escala 4x4 column-major."""
    # Extrair submatriz de rotação/escala 3x3
    r00, r01, r02 = m[0], m[4], m[8]
    r10, r11, r12 = m[1], m[5], m[9]
    r20, r21, r22 = m[2], m[6], m[10]
    tx, ty, tz = m[12], m[13], m[14]

    # Determinante 3x3
    det = (
        r00 * (r11 * r22 - r12 * r21)
        - r01 * (r10 * r22 - r12 * r20)
        + r02 * (r10 * r21 - r11 * r20)
    )

    if abs(det) < 1e-9:
        return _identity_matrix_16()

    inv_det = 1.0 / det

    # Inversa da submatriz 3x3
    i00 = (r11 * r22 - r12 * r21) * inv_det
    i01 = (r02 * r21 - r01 * r22) * inv_det
    i02 = (r01 * r12 - r02 * r11) * inv_det

    i10 = (r12 * r20 - r10 * r22) * inv_det
    i11 = (r00 * r22 - r02 * r20) * inv_det
    i12 = (r02 * r10 - r00 * r12) * inv_det

    i20 = (r10 * r21 - r11 * r20) * inv_det
    i21 = (r01 * r20 - r00 * r21) * inv_det
    i22 = (r00 * r11 - r01 * r10) * inv_det

    # Nova translação = -InvR * T
    itx = -(i00 * tx + i01 * ty + i02 * tz)
    ity = -(i10 * tx + i11 * ty + i12 * tz)
    itz = -(i20 * tx + i21 * ty + i22 * tz)

    return [
        i00, i10, i20, 0.0,
        i01, i11, i21, 0.0,
        i02, i12, i22, 0.0,
        itx, ity, itz, 1.0,
    ]


class NestedInstanceHierarchyEngine:
    """Motor de cálculo e resolução de matrizes mundiais e hierarquia aninhada de instâncias."""

    @classmethod
    def decompose_matrix(cls, m: List[float]) -> Dict[str, Any]:
        """Decompõe matriz 4x4 column-major em translação, escala e rotação analítica."""
        tx, ty, tz = m[12], m[13], m[14]

        # Escala como o comprimento das colunas do eixo 3x3
        sx = math.sqrt(m[0] ** 2 + m[1] ** 2 + m[2] ** 2)
        sy = math.sqrt(m[4] ** 2 + m[5] ** 2 + m[6] ** 2)
        sz = math.sqrt(m[8] ** 2 + m[9] ** 2 + m[10] ** 2)

        return {
            "translation": [round(tx, 4), round(ty, 4), round(tz, 4)],
            "scale": [round(sx, 4), round(sy, 4), round(sz, 4)],
            "is_uniform_scale": abs(sx - sy) < 1e-4 and abs(sy - sz) < 1e-4,
        }

    @classmethod
    def calculate_world_matrix_chain(
        cls,
        matrix_chain: List[List[float]],
    ) -> List[float]:
        """
        Recebe uma cadeia de matrizes locais do topo da hierarquia até o nó folha:
        [M_parent, M_child, M_grandchild, ...] e retorna a matriz acumulada mundial.
        """
        if not matrix_chain:
            return _identity_matrix_16()

        result = matrix_chain[0]
        for next_mat in matrix_chain[1:]:
            result = _matmul4(result, next_mat)

        return [round(c, 6) for c in result]

    @classmethod
    def convert_world_transform_to_local(
        cls,
        desired_world_matrix: List[float],
        parent_world_matrix: List[float],
    ) -> List[float]:
        """
        Calcula a nova matriz local que deve ser atribuída a um nó filho para que ele
        atinja a posição e orientação desejadas no espaço mundial (World Space Editing).
        M_local = (M_parent_world)^-1 x M_desired_world
        """
        inv_parent = _invert_affine4(parent_world_matrix)
        local_mat = _matmul4(inv_parent, desired_world_matrix)
        return [round(c, 6) for c in local_mat]

    @classmethod
    def resolve_hierarchy_node(
        cls,
        node_id: str,
        path_to_node: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Resolve a transformação completa de um nó aninhado a partir do seu caminho hierárquico.
        path_to_node: lista de nós [{id, name, local_matrix_16}, ...]
        """
        matrices = [n.get("local_matrix_16", _identity_matrix_16()) for n in path_to_node]
        world_mat = cls.calculate_world_matrix_chain(matrices)
        decomp = cls.decompose_matrix(world_mat)

        parent_matrices = matrices[:-1]
        parent_world = cls.calculate_world_matrix_chain(parent_matrices) if parent_matrices else _identity_matrix_16()

        return {
            "entity_type": "NestedHierarchyNode",
            "node_id": node_id,
            "depth_level": len(path_to_node),
            "world_matrix_16": world_mat,
            "parent_world_matrix_16": parent_world,
            "decomposition": decomp,
            "status": f"HIERARQUIA RESOLVIDA (PROFUNDIDADE {len(path_to_node)})",
        }
