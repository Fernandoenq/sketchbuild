"""
SketchBuild - Decodificador de Malhas com Suavização de Arestas (Zero DLL / Pure Python)
Frente 78: Engenharia Reversa do SketchUp - Soften & Smooth Edges (SUEdgeGetSmooth & SUEdgeGetSoft)

Implementa o algoritmo analítico de suavização de arestas por ângulo diedro do SketchUp,
gerando normais de vértices ponderadas (Phong Shading) para superfícies curvas orgânicas
e identificando arestas ocultas (soft) vs arestas visíveis de silhueta.
"""

from __future__ import annotations

import math
from collections import defaultdict
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


class SmoothSoftEdgesEngine:
    """Motor de cálculo e classificação de arestas Soft & Smooth do SketchUp."""

    @classmethod
    def process_mesh_smoothing(
        cls,
        vertices: List[Tuple[float, float, float]],
        faces: List[List[int]],
        angle_threshold_deg: float = 35.0,
    ) -> Dict[str, Any]:
        """
        Analisa a malha e calcula flags de suavização de arestas e normais de vértices.
        """
        # 1. Calcular normais de cada face
        face_normals: List[Tuple[float, float, float]] = []
        for face in faces:
            if len(face) < 3:
                face_normals.append((0.0, 0.0, 1.0))
                continue
            v0 = vertices[face[0]]
            v1 = vertices[face[1]]
            v2 = vertices[face[2]]
            e1 = _sub(v1, v0)
            e2 = _sub(v2, v0)
            n = _norm(_cross(e1, e2))
            face_normals.append(n)

        # 2. Mapear arestas compartilhadas por faces
        edge_to_faces: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        for f_idx, face in enumerate(faces):
            n_pts = len(face)
            for i in range(n_pts):
                i0 = face[i]
                i1 = face[(i + 1) % n_pts]
                edge_key = (min(i0, i1), max(i0, i1))
                edge_to_faces[edge_key].append(f_idx)

        # 3. Classificar arestas por ângulo diedro
        cos_thresh = math.cos(math.radians(angle_threshold_deg))
        soft_edges: List[Tuple[int, int]] = []
        hard_edges: List[Tuple[int, int]] = []

        # Adjacência de faces suaves para interpolação de normais de vértices
        vertex_face_map: Dict[int, List[int]] = defaultdict(list)
        for f_idx, face in enumerate(faces):
            for v_idx in face:
                vertex_face_map[v_idx].append(f_idx)

        for edge, shared_faces in edge_to_faces.items():
            if len(shared_faces) == 2:
                n1 = face_normals[shared_faces[0]]
                n2 = face_normals[shared_faces[1]]
                dot_val = _dot(n1, n2)
                if dot_val >= cos_thresh:  # Ângulo diedro menor ou igual ao limite
                    soft_edges.append(edge)
                else:
                    hard_edges.append(edge)
            else:
                # Aresta de borda livre
                hard_edges.append(edge)

        # 4. Calcular normais de vértices ponderadas
        vertex_normals: List[List[float]] = []
        for v_idx in range(len(vertices)):
            adj_faces = vertex_face_map[v_idx]
            if not adj_faces:
                vertex_normals.append([0.0, 0.0, 1.0])
                continue
            acc_n = [0.0, 0.0, 0.0]
            for f in adj_faces:
                fn = face_normals[f]
                acc_n[0] += fn[0]
                acc_n[1] += fn[1]
                acc_n[2] += fn[2]
            n_unit = _norm(tuple(acc_n))
            vertex_normals.append([round(c, 4) for c in n_unit])

        return {
            "entity_type": "MeshSmoothingResult",
            "angle_threshold_deg": round(angle_threshold_deg, 1),
            "total_edges": len(edge_to_faces),
            "soft_edges_count": len(soft_edges),
            "hard_edges_count": len(hard_edges),
            "percent_soft": round((len(soft_edges) / max(1, len(edge_to_faces))) * 100.0, 1),
            "soft_edges": [[e[0], e[1]] for e in soft_edges],
            "hard_edges": [[e[0], e[1]] for e in hard_edges],
            "vertex_normals": vertex_normals,
            "status": f"{len(soft_edges)} ARESTAS SUAVIZADAS (THRESHOLD {angle_threshold_deg}°)",
        }
