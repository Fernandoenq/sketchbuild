"""Engine de Engenharia Reversa da Ferramenta Posicionar Camera (Position Camera Tool).

Coloca o observador exatamente sobre o ponto clicado no chao ou piso (na altura ergonomica dos olhos)
com suporte a direcionamento do olhar por clique-e-arraste (click-and-drag).
"""

from __future__ import annotations
import math
from typing import Any


class PositionCameraEngine:
    """Implementa o posicionamento exato da camera do SketchUp (Position Camera Tool)."""

    @classmethod
    def position_camera(
        cls,
        click_point_xyz: list[float],
        drag_target_xyz: list[float] | None = None,
        eye_height_m: float = 1.68,
        default_view_direction: list[float] | None = None
    ) -> dict[str, Any]:
        """Posiciona a camera na cota do clique + altura dos olhos e calcula o foco."""
        cx, cy, cz = float(click_point_xyz[0]), float(click_point_xyz[1]), float(click_point_xyz[2])
        eye_z = cz + float(eye_height_m)
        eye_pos = [round(cx, 4), round(cy, 4), round(eye_z, 4)]

        if drag_target_xyz is not None:
            tx = float(drag_target_xyz[0])
            ty = float(drag_target_xyz[1])
            tz = float(drag_target_xyz[2])

            dx = tx - cx
            dy = ty - cy
            dz = tz - eye_z
            dist = math.sqrt(dx * dx + dy * dy + dz * dz)
            if dist > 1e-6:
                dir_vec = [dx / dist, dy / dist, dz / dist]
                target_pos = [round(tx, 4), round(ty, 4), round(tz, 4)]
            else:
                dir_vec = [0.0, 1.0, 0.0]
                target_pos = [round(cx, 4), round(cy + 10.0, 4), round(eye_z, 4)]
        else:
            if default_view_direction is not None and len(default_view_direction) == 3:
                dx, dy, dz = default_view_direction
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                if dist > 1e-6:
                    dir_vec = [dx / dist, dy / dist, dz / dist]
                else:
                    dir_vec = [0.0, 1.0, 0.0]
            else:
                dir_vec = [0.0, 1.0, 0.0]  # Direcao Norte (Eixo Verde) padrao

            target_pos = [
                round(cx + 10.0 * dir_vec[0], 4),
                round(cy + 10.0 * dir_vec[1], 4),
                round(eye_z + 10.0 * dir_vec[2], 4),
            ]

        # Calcula angulos Yaw e Pitch resultantes
        horiz_dist = math.sqrt(dir_vec[0] ** 2 + dir_vec[1] ** 2)
        yaw_deg = math.degrees(math.atan2(dir_vec[0], dir_vec[1])) % 360.0
        pitch_deg = math.degrees(math.atan2(dir_vec[2], max(1e-6, horiz_dist)))

        return {
            "success": True,
            "camera_eye": eye_pos,
            "camera_target": target_pos,
            "view_direction": [round(c, 4) for c in dir_vec],
            "eye_height_m": float(eye_height_m),
            "ground_point_xyz": [round(cx, 4), round(cy, 4), round(cz, 4)],
            "yaw_deg": round(yaw_deg, 2),
            "pitch_deg": round(pitch_deg, 2),
            "active_mode": "LOOK_AROUND_READY",
        }
