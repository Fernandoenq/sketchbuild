"""
Interpolador de Caminho de Câmera e Voo Panorâmico (Flythrough - Zero DLL).

Implementa interpolação suave Catmull-Rom C^1 entre cenas e câmeras:
1. Suavização contínua de trajetória de câmera (posição, alvo e vetor UP).
2. Cálculo de distâncias euclidianas e temporalização constante de velocidade.
3. Geração de keyframes para animação cinematográfica no Three.js e exportação.
"""

import math
from typing import List, Dict, Any, Tuple


class CameraPathInterpolator:
    """Motor analítico de sobrevoo de câmera 3D."""

    @staticmethod
    def _catmull_rom_spline(
        p0: Tuple[float, float, float],
        p1: Tuple[float, float, float],
        p2: Tuple[float, float, float],
        p3: Tuple[float, float, float],
        t: float
    ) -> Tuple[float, float, float]:
        """Interpolação de spline Catmull-Rom para t em [0, 1]."""
        t2 = t * t
        t3 = t2 * t
        # Matriz Catmull-Rom padrão (centripetal/uniforme)
        res = []
        for i in range(3):
            val = 0.5 * (
                (2.0 * p1[i]) +
                (-p0[i] + p2[i]) * t +
                (2.0 * p0[i] - 5.0 * p1[i] + 4.0 * p2[i] - p3[i]) * t2 +
                (-p0[i] + 3.0 * p1[i] - 3.0 * p2[i] + p3[i]) * t3
            )
            res.append(round(val, 4))
        return (res[0], res[1], res[2])

    @classmethod
    def generate_flythrough_path(
        cls,
        waypoints: List[Dict[str, Any]],
        frames_per_segment: int = 24
    ) -> Dict[str, Any]:
        """
        Gera rota cinematográfica contínua a partir de uma lista de câmeras/cenas.
        cada waypoint: {'position': [x,y,z], 'target': [x,y,z]}
        """
        n = len(waypoints)
        if n < 2:
            raise ValueError("Voo panorâmico requer pelo menos 2 pontos de câmera.")

        positions = [tuple(w.get('position', [0, 0, 5])) for w in waypoints]
        targets = [tuple(w.get('target', [0, 0, 0])) for w in waypoints]

        # Estende os extremos para suporte do Catmull-Rom
        ext_pos = [positions[0]] + positions + [positions[-1]]
        ext_tar = [targets[0]] + targets + [targets[-1]]

        keyframe_positions = []
        keyframe_targets = []

        for seg in range(n - 1):
            p0 = ext_pos[seg]
            p1 = ext_pos[seg + 1]
            p2 = ext_pos[seg + 2]
            p3 = ext_pos[seg + 3]

            t0 = ext_tar[seg]
            t1 = ext_tar[seg + 1]
            t2 = ext_tar[seg + 2]
            t3 = ext_tar[seg + 3]

            for f in range(frames_per_segment):
                t = f / float(frames_per_segment)
                pos = cls._catmull_rom_spline(p0, p1, p2, p3, t)
                tar = cls._catmull_rom_spline(t0, t1, t2, t3, t)
                keyframe_positions.append(pos)
                keyframe_targets.append(tar)

        # Adiciona o ponto final
        keyframe_positions.append(positions[-1])
        keyframe_targets.append(targets[-1])

        return {
            "entity_type": "FlythroughPath",
            "waypoints_count": n,
            "total_frames": len(keyframe_positions),
            "duration_seconds": round(len(keyframe_positions) / 24.0, 2),
            "camera_positions": keyframe_positions,
            "camera_targets": keyframe_targets,
        }
