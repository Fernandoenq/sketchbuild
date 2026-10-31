"""Engine de Engenharia Reversa da Ferramenta Percorrer (Walk Tool) com Gravidade e Colisao.

Simula a caminhada de um pedestre pelo modelo 3D mantendo a altura dos olhos ergonomica,
com deteccao de cota de piso por gravidade e transposicao automatica de degraus.
"""

from __future__ import annotations
import math
from typing import Any


class WalkCameraGravityEngine:
    """Implementa o controlador cinematico da ferramenta Percorrer (Walk Tool) do SketchUp."""

    @staticmethod
    def _ray_cast_ground_elevation(
        px: float,
        py: float,
        tin_vertices: list[list[float]],
        tin_triangles: list[list[int]],
        fallback_elevation: float = 0.0
    ) -> float:
        """Determina a cota Z do chao em (px, py) projetada contra a malha de piso/terreno."""
        for tri in tin_triangles:
            v0, v1, v2 = tin_vertices[tri[0]], tin_vertices[tri[1]], tin_vertices[tri[2]]
            x0, y0, z0 = v0[0], v0[1], v0[2]
            x1, y1, z1 = v1[0], v1[1], v1[2]
            x2, y2, z2 = v2[0], v2[1], v2[2]

            det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(det) < 1e-12:
                continue

            w0 = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / det
            w1 = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / det
            w2 = 1.0 - w0 - w1

            if w0 >= -1e-5 and w1 >= -1e-5 and w2 >= -1e-5:
                return float(w0 * z0 + w1 * z1 + w2 * z2)

        return float(fallback_elevation)

    @classmethod
    def step_walk(
        cls,
        camera_eye_xyz: list[float],
        camera_target_xyz: list[float],
        move_forward_m: float = 0.0,
        strafe_right_m: float = 0.0,
        eye_height_m: float = 1.68,
        ground_vertices: list[list[float]] | None = None,
        ground_triangles: list[list[int]] | None = None,
        max_step_height_m: float = 0.22,
        collision_detection: bool = True
    ) -> dict[str, Any]:
        """Calcula o proximo frame de caminhada com ajuste de piso e gravidade."""
        eye_x, eye_y, eye_z = float(camera_eye_xyz[0]), float(camera_eye_xyz[1]), float(camera_eye_xyz[2])
        tgt_x, tgt_y, tgt_z = float(camera_target_xyz[0]), float(camera_target_xyz[1]), float(camera_target_xyz[2])

        # Direcao de visao horizontal (ignora pitch para andar no plano)
        dx = tgt_x - eye_x
        dy = tgt_y - eye_y
        dist_h = math.sqrt(dx * dx + dy * dy)
        if dist_h < 1e-6:
            fwd_x, fwd_y = 0.0, 1.0
        else:
            fwd_x, fwd_y = dx / dist_h, dy / dist_h

        # Vetor perpendicular para strafe lateral
        right_x = fwd_y
        right_y = -fwd_x

        # Novo ponto horizontal pretendido
        new_x = eye_x + move_forward_m * fwd_x + strafe_right_m * right_x
        new_y = eye_y + move_forward_m * fwd_y + strafe_right_m * right_y

        # Cota de piso anterior e nova cota de piso
        curr_ground_z = eye_z - eye_height_m
        if ground_vertices and ground_triangles:
            new_ground_z = cls._ray_cast_ground_elevation(new_x, new_y, ground_vertices, ground_triangles, curr_ground_z)
        else:
            new_ground_z = 0.0

        delta_elevation = new_ground_z - curr_ground_z
        blocked_by_step = False

        if collision_detection and delta_elevation > max_step_height_m:
            # Degrau alto demais para subir caminhando (ex: parede ou parapeito)
            blocked_by_step = True
            final_x = eye_x
            final_y = eye_y
            final_ground_z = curr_ground_z
        else:
            final_x = new_x
            final_y = new_y
            final_ground_z = new_ground_z

        final_eye_z = final_ground_z + float(eye_height_m)
        pitch_offset = tgt_z - eye_z

        # Novo alvo de camera deslocado paralelamente
        final_tgt_x = final_x + dx
        final_tgt_y = final_y + dy
        final_tgt_z = final_eye_z + pitch_offset

        return {
            "success": True,
            "new_camera_eye": [round(final_x, 4), round(final_y, 4), round(final_eye_z, 4)],
            "new_camera_target": [round(final_tgt_x, 4), round(final_tgt_y, 4), round(final_tgt_z, 4)],
            "ground_elevation_m": round(final_ground_z, 4),
            "eye_height_m": float(eye_height_m),
            "step_climbed": not blocked_by_step and abs(delta_elevation) > 0.01,
            "collision_blocked": blocked_by_step,
            "delta_elevation_m": round(delta_elevation, 4),
        }
