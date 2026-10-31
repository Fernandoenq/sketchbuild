"""
SketchBuild - Decodificador de Malhas com Furos e Hierarquia de Loops (Zero DLL / Pure Python)
Frente 81: Engenharia Reversa do SketchUp - SULoopRef & SUPolyMeshRef (Outer & Inner Loops)

Implementa a separação de loops externos e internos (furos e aberturas) e algoritmo de triangulação
Ear-Clipping com cortes de ponte (seam bridge), permitindo renderizar faces poligonais complexas
com furos no Three.js sem dependência de bibliotecas externas.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _sub(p1: Tuple[float, float, float], p2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    return (p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2])


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


def _signed_area_2d(pts: List[Tuple[float, float]]) -> float:
    n = len(pts)
    return sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n)) * 0.5


def _pt_eq_2d(p1: Tuple[float, float], p2: Tuple[float, float], tol: float = 1e-6) -> bool:
    return abs(p1[0] - p2[0]) < tol and abs(p1[1] - p2[1]) < tol


class PolyMeshLoopEngine:
    """Motor de cálculo de hierarquia de loops e triangulação de faces com furos."""

    @classmethod
    def triangulate_face_with_holes(
        cls,
        outer_loop_3d: List[Tuple[float, float, float]],
        inner_loops_3d: Optional[List[List[Tuple[float, float, float]]]] = None,
    ) -> Dict[str, Any]:
        """
        Recebe o loop externo e lista de loops internos (furos) e triangula a face plana.
        """
        if len(outer_loop_3d) < 3:
            return {"vertices": [], "triangles": [], "face_count": 0}

        # 1. Determinar o plano médio do loop externo
        v0 = outer_loop_3d[0]
        v1 = outer_loop_3d[1]
        v2 = outer_loop_3d[2]
        normal = _norm(_cross(_sub(v1, v0), _sub(v2, v0)))

        # Base ortonormal (u, v) no plano da face
        if abs(normal[2]) < 0.9:
            u_axis = _norm(_cross(normal, (0.0, 0.0, 1.0)))
        else:
            u_axis = _norm(_cross(normal, (1.0, 0.0, 0.0)))
        v_axis = _norm(_cross(normal, u_axis))

        # 2. Projetar para 2D
        def to_2d(pts_3d: List[Tuple[float, float, float]]) -> List[Tuple[float, float]]:
            res = []
            for p in pts_3d:
                rel = _sub(p, v0)
                res.append((_dot(rel, u_axis), _dot(rel, v_axis)))
            return res

        outer_2d = to_2d(outer_loop_3d)
        outer_3d_oriented = list(outer_loop_3d)
        # Garantir que outer é CCW (área positiva)
        if _signed_area_2d(outer_2d) < 0:
            outer_2d.reverse()
            outer_3d_oriented.reverse()

        # Se não houver furos, ear-clipping direto no outer_2d
        if not inner_loops_3d:
            triangles = cls._ear_clipping_2d(outer_2d)
            return {
                "entity_type": "SUPolyMeshRef",
                "normal": [round(c, 4) for c in normal],
                "vertices": [[round(c, 4) for c in pt] for pt in outer_3d_oriented],
                "triangles": triangles,
                "face_count": len(triangles),
                "holes_count": 0,
                "status": f"FACE TRIANGULADA ({len(triangles)} TRIÂNGULOS)",
            }

        # 3. Incorporar furos no polígono através de pontes (Bridge / Seam cuts)
        all_verts_3d: List[Tuple[float, float, float]] = list(outer_3d_oriented)

        combined_polygon_2d: List[Tuple[float, float]] = list(outer_2d)
        combined_indices: List[int] = list(range(len(outer_2d)))

        for raw_hole_3d in inner_loops_3d:
            if len(raw_hole_3d) < 3:
                continue
            hole_3d = list(raw_hole_3d)
            hole_2d = to_2d(hole_3d)
            # Furos devem ter orientação horária (área negativa)
            if _signed_area_2d(hole_2d) > 0:
                hole_2d.reverse()
                hole_3d.reverse()

            hole_base_idx = len(all_verts_3d)
            all_verts_3d.extend(hole_3d)

            # Encontrar ponto do furo com maior coordenada U
            best_hole_pt_idx = max(range(len(hole_2d)), key=lambda i: hole_2d[i][0])
            h_pt = hole_2d[best_hole_pt_idx]

            # Encontrar ponto mais próximo no polígono externo atual
            best_outer_idx = min(
                range(len(combined_polygon_2d)),
                key=lambda i: (combined_polygon_2d[i][0] - h_pt[0]) ** 2 + (combined_polygon_2d[i][1] - h_pt[1]) ** 2
            )

            # Reordenar furo a partir do ponto de conexão
            reordered_hole_2d = hole_2d[best_hole_pt_idx:] + hole_2d[:best_hole_pt_idx]
            reordered_hole_idx = [hole_base_idx + ((best_hole_pt_idx + k) % len(hole_2d)) for k in range(len(hole_2d))]

            seam_insert = (
                reordered_hole_2d
                + [reordered_hole_2d[0]]
                + [combined_polygon_2d[best_outer_idx]]
            )
            seam_insert_idx = (
                reordered_hole_idx
                + [reordered_hole_idx[0]]
                + [combined_indices[best_outer_idx]]
            )

            insert_pos = best_outer_idx + 1
            combined_polygon_2d = combined_polygon_2d[:insert_pos] + seam_insert + combined_polygon_2d[insert_pos:]
            combined_indices = combined_indices[:insert_pos] + seam_insert_idx + combined_indices[insert_pos:]

        # 4. Triangular polígono unificado
        local_tris = cls._ear_clipping_2d(combined_polygon_2d)
        mapped_triangles = [
            [combined_indices[t[0]], combined_indices[t[1]], combined_indices[t[2]]]
            for t in local_tris
        ]

        return {
            "entity_type": "SUPolyMeshRef",
            "normal": [round(c, 4) for c in normal],
            "vertices": [[round(c, 4) for c in pt] for pt in all_verts_3d],
            "triangles": mapped_triangles,
            "face_count": len(mapped_triangles),
            "holes_count": len(inner_loops_3d),
            "status": f"FACE COM {len(inner_loops_3d)} FURO(S) TRIANGULADA ({len(mapped_triangles)} TRIÂNGULOS)",
        }

    @classmethod
    def _ear_clipping_2d(cls, polygon: List[Tuple[float, float]]) -> List[List[int]]:
        """Algoritmo Ear-Clipping padrão com suporte a pontes de costura e vértices duplicados."""
        n = len(polygon)
        if n < 3:
            return []
        if n == 3:
            return [[0, 1, 2]]

        indices = list(range(n))
        triangles: List[List[int]] = []

        def is_ear(u: int, v: int, w: int, poly_indices: List[int]) -> bool:
            a = polygon[u]
            b = polygon[v]
            c = polygon[w]
            ab_x, ab_y = b[0] - a[0], b[1] - a[1]
            bc_x, bc_y = c[0] - b[0], c[1] - b[1]
            cross_val = ab_x * bc_y - ab_y * bc_x
            if cross_val <= 1e-9:
                return False

            # Testar se nenhum outro ponto está estritamente dentro do triângulo ABC
            for idx in poly_indices:
                if idx in (u, v, w):
                    continue
                p = polygon[idx]
                if _pt_eq_2d(p, a) or _pt_eq_2d(p, b) or _pt_eq_2d(p, c):
                    continue
                c1 = (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])
                c2 = (c[0] - b[0]) * (p[1] - b[1]) - (c[1] - b[1]) * (p[0] - b[0])
                c3 = (a[0] - c[0]) * (p[1] - c[1]) - (a[1] - c[1]) * (p[0] - c[0])
                if c1 >= 1e-7 and c2 >= 1e-7 and c3 >= 1e-7:
                    return False
            return True

        poly = list(indices)
        count = 3 * len(poly)
        i = 0
        while len(poly) > 2 and count > 0:
            count -= 1
            n_cur = len(poly)
            prev_idx = poly[(i - 1 + n_cur) % n_cur]
            curr_idx = poly[i % n_cur]
            next_idx = poly[(i + 1) % n_cur]

            if is_ear(prev_idx, curr_idx, next_idx, poly):
                triangles.append([prev_idx, curr_idx, next_idx])
                poly.pop(i % n_cur)
                count = 3 * len(poly)
            else:
                i = (i + 1) % n_cur

        return triangles
