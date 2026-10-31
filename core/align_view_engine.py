"""
SketchBuild - Motor de Alinhamento de Câmera à Face (Zero DLL / Pure Python)
Frente 82: Engenharia Reversa do SketchUp - Align View to Face (Context Menu)

Calcula a rotação, enquadramento e orientação exata da câmera do visualizador para encarar
qualquer face plana selecionada perpendicularmente à sua normal (Align View).
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


class AlignViewEngine:
    """Motor de cálculo de enquadramento da câmera perpendicular a faces selecionadas."""

    @classmethod
    def calculate_align_view(
        cls,
        face_vertices: List[Tuple[float, float, float]],
        fov_deg: float = 35.0,
        margin_factor: float = 1.25,
    ) -> Dict[str, Any]:
        """
        Calcula nova posição de câmera (eye, target, up) perfeitamente alinhada à face.
        """
        n_pts = len(face_vertices)
        if n_pts < 3:
            raise ValueError("Uma face necessita de pelo menos 3 vértices para alinhar exibição.")

        # 1. Centróide da face
        cx = sum(p[0] for p in face_vertices) / n_pts
        cy = sum(p[1] for p in face_vertices) / n_pts
        cz = sum(p[2] for p in face_vertices) / n_pts
        centroid = (cx, cy, cz)

        # 2. Normal da face
        v0 = face_vertices[0]
        v1 = face_vertices[1]
        v2 = face_vertices[2]
        normal = _norm(_cross(_sub(v1, v0), _sub(v2, v0)))

        # 3. Raio delimitador
        max_dist_sq = max(
            (p[0] - cx) ** 2 + (p[1] - cy) ** 2 + (p[2] - cz) ** 2
            for p in face_vertices
        )
        radius = math.sqrt(max_dist_sq)
        radius = max(0.1, radius)

        # 4. Distância focal
        half_fov_rad = math.radians(fov_deg * 0.5)
        dist = (radius / math.tan(half_fov_rad)) * margin_factor

        eye = (
            centroid[0] + normal[0] * dist,
            centroid[1] + normal[1] * dist,
            centroid[2] + normal[2] * dist,
        )

        # 5. Vetor Up perpendicular
        # Se normal não for paralela a Z
        z_dot = _dot(normal, (0.0, 0.0, 1.0))
        if abs(z_dot) < 0.98:
            # Projeção de Z no plano da face: Z - (Z . N) * N
            up_cand = (
                0.0 - z_dot * normal[0],
                0.0 - z_dot * normal[1],
                1.0 - z_dot * normal[2],
            )
            up_vec = _norm(up_cand)
        else:
            # Face horizontal (chão ou teto): alinhar com o eixo Y do mundo
            up_vec = (0.0, 1.0, 0.0) if normal[2] > 0 else (0.0, -1.0, 0.0)

        return {
            "entity_type": "AlignViewCamera",
            "eye": [round(c, 4) for c in eye],
            "target": [round(c, 4) for c in centroid],
            "up": [round(c, 4) for c in up_vec],
            "normal": [round(c, 4) for c in normal],
            "distance_m": round(dist, 4),
            "face_radius_m": round(radius, 4),
            "status": "CÂMERA ALINHADA PERPENDICULARMENTE À FACE",
        }
