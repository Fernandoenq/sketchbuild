"""Engine de Engenharia Reversa da Ferramenta Olhar ao Redor (Look Around Tool).

Mantem a posicao do observador fixa sobre um tripe virtual e gira a orientacao
do vetor de visao em Pan (Yaw) e Tilt (Pitch), com controle de altura dos olhos pelo VCB.
"""

from __future__ import annotations
import math
from typing import Any


class LookAroundCameraEngine:
    """Implementa o controle angular da ferramenta Olhar ao Redor (Look Around) do SketchUp."""

    @classmethod
    def rotate_look_around(
        cls,
        camera_eye_xyz: list[float],
        current_yaw_deg: float,
        current_pitch_deg: float,
        delta_yaw_deg: float,
        delta_pitch_deg: float,
        target_distance_m: float = 10.0,
        new_eye_height_m: float | None = None,
        base_ground_z: float = 0.0
    ) -> dict[str, Any]:
        """Calcula a nova orientacao angular e o novo ponto de foco (target) da camera."""
        # 1. Atualiza e limita os angulos
        yaw = (current_yaw_deg + delta_yaw_deg) % 360.0
        pitch = max(-89.0, min(89.0, current_pitch_deg + delta_pitch_deg))

        # 2. Ajusta altura dos olhos caso solicitada pelo VCB
        eye_x = float(camera_eye_xyz[0])
        eye_y = float(camera_eye_xyz[1])
        if new_eye_height_m is not None:
            eye_z = float(base_ground_z) + float(new_eye_height_m)
        else:
            eye_z = float(camera_eye_xyz[2])

        # 3. Converte angulos esfericos para coordenadas cartesianas unitarias
        # Convencao SketchUp: Eixo Z e o Up vertical, X e Vermelho (Leste), Y e Verde (Norte)
        yaw_rad = math.radians(yaw)
        pitch_rad = math.radians(pitch)

        cos_pitch = math.cos(pitch_rad)
        sin_pitch = math.sin(pitch_rad)
        cos_yaw = math.cos(yaw_rad)
        sin_yaw = math.sin(yaw_rad)

        dir_x = cos_pitch * sin_yaw
        dir_y = cos_pitch * cos_yaw
        dir_z = sin_pitch

        # 4. Ponto focal alvo (Target)
        dist = max(0.1, float(target_distance_m))
        tgt_x = eye_x + dist * dir_x
        tgt_y = eye_y + dist * dir_y
        tgt_z = eye_z + dist * dir_z

        return {
            "success": True,
            "yaw_deg": round(yaw, 2),
            "pitch_deg": round(pitch, 2),
            "camera_eye": [round(eye_x, 4), round(eye_y, 4), round(eye_z, 4)],
            "camera_target": [round(tgt_x, 4), round(tgt_y, 4), round(tgt_z, 4)],
            "view_direction": [round(dir_x, 4), round(dir_y, 4), round(dir_z, 4)],
            "eye_height_m": round(eye_z - base_ground_z, 3) if new_eye_height_m is not None else round(eye_z, 3),
        }
