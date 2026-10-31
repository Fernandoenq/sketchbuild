"""
Motor Follow Me / Siga-me - Extrusão 3D ao Longo de Caminho (Zero DLL).

Implementa extrusão de perfil 2D coplanar ao longo de uma curva/polilinha 3D guia:
- Utiliza Parallel Transport Frames (Rotation Minimizing Frames - RMF) para eliminar torções indesejadas (gimbal lock).
- Gera malhas B-Rep 2-manifold fechadas com tampas (caps) inicial e final.
- Suporta perfis circulares (tubos de escorregadores) e perfis retangulares (corrimãos e vigas curvas).
"""

import math
from typing import List, Tuple, Dict, Any, Optional


class FollowMeEngine:
    """Motor analítico de extrusão ao longo de caminho 3D."""

    @staticmethod
    def _vec_sub(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    @staticmethod
    def _vec_add(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    @staticmethod
    def _vec_scale(v: Tuple[float, float, float], s: float) -> Tuple[float, float, float]:
        return (v[0] * s, v[1] * s, v[2] * s)

    @staticmethod
    def _vec_cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        )

    @staticmethod
    def _vec_dot(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    @staticmethod
    def _vec_len(v: Tuple[float, float, float]) -> float:
        return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

    @classmethod
    def _normalize(cls, v: Tuple[float, float, float]) -> Tuple[float, float, float]:
        l = cls._vec_len(v)
        if l < 1e-9:
            return (0.0, 0.0, 1.0)
        return (v[0] / l, v[1] / l, v[2] / l)

    @classmethod
    def extrude_profile_along_path(
        cls,
        profile_2d: List[Tuple[float, float]],
        path_3d: List[Tuple[float, float, float]],
        close_caps: bool = True
    ) -> Dict[str, Any]:
        """
        Extruda um perfil 2D (centrado na origem (0,0)) ao longo de uma polilinha 3D.
        profile_2d: [(u0, v0), (u1, v1), ...]
        path_3d: [(x0, y0, z0), (x1, y1, z1), ...]
        """
        n_prof = len(profile_2d)
        n_path = len(path_3d)
        if n_prof < 3:
            raise ValueError("Perfil requer pelo menos 3 pontos.")
        if n_path < 2:
            raise ValueError("Caminho requer pelo menos 2 pontos.")

        # 1. Calcula os frames locais de referência ortonormal ao longo do caminho (RMF)
        tangents = []
        for i in range(n_path):
            if i == 0:
                t = cls._vec_sub(path_3d[1], path_3d[0])
            elif i == n_path - 1:
                t = cls._vec_sub(path_3d[n_path - 1], path_3d[n_path - 2])
            else:
                t1 = cls._vec_sub(path_3d[i], path_3d[i - 1])
                t2 = cls._vec_sub(path_3d[i + 1], path_3d[i])
                t = cls._vec_add(t1, t2)
            tangents.append(cls._normalize(t))

        # Define vetor normal inicial (u_axis, v_axis) ortogonal a tangents[0]
        t0 = tangents[0]
        ref = (0.0, 0.0, 1.0) if abs(t0[2]) < 0.9 else (0.0, 1.0, 0.0)
        u0 = cls._normalize(cls._vec_cross(t0, ref))
        v0 = cls._normalize(cls._vec_cross(t0, u0))

        frames = [(u0, v0, t0)]

        # Transporta o frame ao longo do caminho usando rotação mínima
        for i in range(1, n_path):
            prev_u, prev_v, prev_t = frames[-1]
            curr_t = tangents[i]

            # Eixo de rotação entre prev_t e curr_t
            axis = cls._vec_cross(prev_t, curr_t)
            axis_len = cls._vec_len(axis)
            if axis_len < 1e-6:
                # Caminho reto contínuo
                frames.append((prev_u, prev_v, curr_t))
            else:
                axis = cls._normalize(axis)
                angle = math.acos(max(-1.0, min(1.0, cls._vec_dot(prev_t, curr_t))))
                
                # Rotação de Rodrigues para prev_u e prev_v
                def rotate_vec(v):
                    cos_a = math.cos(angle)
                    sin_a = math.sin(angle)
                    return cls._vec_add(
                        cls._vec_add(cls._vec_scale(v, cos_a), cls._vec_scale(cls._vec_cross(axis, v), sin_a)),
                        cls._vec_scale(axis, cls._vec_dot(axis, v) * (1.0 - cos_a))
                    )
                curr_u = cls._normalize(rotate_vec(prev_u))
                curr_v = cls._normalize(cls._vec_cross(curr_t, curr_u))
                frames.append((curr_u, curr_v, curr_t))

        # 2. Constrói a malha de anéis de vértices
        rings = []
        for i in range(n_path):
            pos = path_3d[i]
            u_axis, v_axis, _ = frames[i]
            ring_pts = []
            for u, v in profile_2d:
                p = cls._vec_add(pos, cls._vec_add(cls._vec_scale(u_axis, u), cls._vec_scale(v_axis, v)))
                ring_pts.append(p)
            rings.append(ring_pts)

        # 3. Monta as faces laterais quadriláteras
        faces = []
        for i in range(n_path - 1):
            r1 = rings[i]
            r2 = rings[i + 1]
            for j in range(n_prof):
                j_next = (j + 1) % n_prof
                faces.append([r1[j], r1[j_next], r2[j_next], r2[j]])

        # 4. Tampas inicial e final (se solicitado)
        if close_caps:
            # Tampa inicial: ordem reversa para normal apontar para fora (-t0)
            faces.append(list(reversed(rings[0])))
            # Tampa final: ordem direta para normal apontar para fora (+tN)
            faces.append(list(rings[-1]))

        return {
            "entity_type": "FollowMeExtrusion",
            "path_points_count": n_path,
            "profile_points_count": n_prof,
            "faces_count": len(faces),
            "faces": faces,
        }

    @classmethod
    def generate_circular_profile(cls, radius: float, segments: int = 12) -> List[Tuple[float, float]]:
        """Gera perfil 2D circular para tubos."""
        pts = []
        for i in range(segments):
            theta = 2.0 * math.pi * i / segments
            pts.append((radius * math.cos(theta), radius * math.sin(theta)))
        return pts

    @classmethod
    def generate_rectangular_profile(cls, width: float, height: float) -> List[Tuple[float, float]]:
        """Gera perfil 2D retangular para vigas e corrimãos."""
        w2 = width * 0.5
        h2 = height * 0.5
        return [(-w2, -h2), (w2, -h2), (w2, h2), (-w2, h2)]
