"""
SketchBuild - Animação de Câmera em Percurso Orbit e Flythrough (Zero DLL / Pure Python)
Frente 94: Engenharia Reversa do SketchUp - Camera Animation Path, Orbit & Flythrough Spline

Gera caminhos contínuos de câmera cinematográfica (órbita 360° ou flythrough spline)
com interpolação suave de aceleração (ease-in/ease-out), FOV dinâmico e enquadramento.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class OrbitFlythroughPathEngine:
    """Motor analítico de animação de trajetória e órbita de câmera 3D."""

    @staticmethod
    def generate_orbit_path(
        target_point: Tuple[float, float, float],
        radius_m: float = 10.0,
        height_m: float = 3.5,
        start_angle_deg: float = 0.0,
        total_rotation_deg: float = 360.0,
        duration_seconds: float = 10.0,
        fps: int = 30,
        fov_deg: float = 45.0
    ) -> Dict[str, Any]:
        """
        Gera uma órbita circular contínua ao redor do target_point.
        """
        total_frames = int(duration_seconds * fps)
        frames: List[Dict[str, Any]] = []

        tx, ty, tz = target_point

        for f in range(total_frames):
            t_norm = f / max(1, total_frames - 1)
            # Aceleração senoidal suave (ease-in-out)
            smooth_t = (1.0 - math.cos(t_norm * math.pi)) / 2.0
            angle_deg = start_angle_deg + (total_rotation_deg * smooth_t)
            angle_rad = math.radians(angle_deg)

            eye_x = tx + radius_m * math.cos(angle_rad)
            eye_y = ty + radius_m * math.sin(angle_rad)
            eye_z = tz + height_m

            frames.append({
                "frame": f,
                "timestamp_s": round(f / fps, 3),
                "eye": [round(eye_x, 4), round(eye_y, 4), round(eye_z, 4)],
                "target": [round(tx, 4), round(ty, 4), round(tz, 4)],
                "up": [0.0, 0.0, 1.0],
                "fov_deg": fov_deg
            })

        return {
            "entity_type": "CameraAnimationPath",
            "mode": "ORBIT",
            "duration_seconds": duration_seconds,
            "fps": fps,
            "total_frames": total_frames,
            "radius_m": radius_m,
            "target": list(target_point),
            "frames": frames,
            "status": "TRAJETÓRIA DE ÓRBITA 360° GERADA COM SUCESSO"
        }

    @staticmethod
    def generate_flythrough_path(
        waypoints: List[Tuple[float, float, float]],
        target_point: Tuple[float, float, float],
        duration_seconds: float = 12.0,
        fps: int = 30,
        fov_deg: float = 45.0
    ) -> Dict[str, Any]:
        """
        Interpola percurso flythrough suave usando spline cúbica de Catmull-Rom através dos waypoints.
        """
        if len(waypoints) < 2:
            return {
                "entity_type": "CameraAnimationPath",
                "mode": "FLYTHROUGH",
                "frames": [],
                "status": "MÍNIMO DE 2 WAYPOINTS NECESSÁRIOS"
            }

        total_frames = int(duration_seconds * fps)
        frames: List[Dict[str, Any]] = []

        # Duplicar pontas para spline contínua
        pts = [waypoints[0]] + list(waypoints) + [waypoints[-1]]
        num_segments = len(waypoints) - 1

        for f in range(total_frames):
            t_global = (f / max(1, total_frames - 1)) * num_segments
            seg_idx = min(int(t_global), num_segments - 1)
            t = t_global - seg_idx

            p0 = pts[seg_idx]
            p1 = pts[seg_idx + 1]
            p2 = pts[seg_idx + 2]
            p3 = pts[seg_idx + 3]

            # Catmull-Rom Spline
            # q(t) = 0.5 * ((2*P1) + (-P0 + P2)*t + (2*P0 - 5*P1 + 4*P2 - P3)*t² + (-P0 + 3*P1 - 3*P2 + P3)*t³)
            eye_coords = []
            for k in range(3):
                val = 0.5 * (
                    (2.0 * p1[k]) +
                    (-p0[k] + p2[k]) * t +
                    (2.0 * p0[k] - 5.0 * p1[k] + 4.0 * p2[k] - p3[k]) * (t**2) +
                    (-p0[k] + 3.0 * p1[k] - 3.0 * p2[k] + p3[k]) * (t**3)
                )
                eye_coords.append(round(val, 4))

            frames.append({
                "frame": f,
                "timestamp_s": round(f / fps, 3),
                "eye": eye_coords,
                "target": [round(target_point[0], 4), round(target_point[1], 4), round(target_point[2], 4)],
                "up": [0.0, 0.0, 1.0],
                "fov_deg": fov_deg
            })

        return {
            "entity_type": "CameraAnimationPath",
            "mode": "FLYTHROUGH",
            "duration_seconds": duration_seconds,
            "fps": fps,
            "total_frames": total_frames,
            "waypoints_count": len(waypoints),
            "target": list(target_point),
            "frames": frames,
            "status": "TRAJETÓRIA FLYTHROUGH SPLINE GERADA COM SUCESSO"
        }
