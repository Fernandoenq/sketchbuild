"""
SketchBuild - Gerenciador de Cenas e Interpolação de Animação de Câmera (Zero DLL / Pure Python)
Frente 69: Engenharia Reversa do SketchUp - SUPageRef / SUSceneRef & Animation Transitions

Implementa o gerenciamento de páginas/cenas do SketchUp, retenção de propriedades
(câmera, sombras, layers, estilos), e interpolação suave (transition_time + delay_time)
para execução de apresentações animadas em 3D.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _lerp(v0: float, v1: float, t: float) -> float:
    return v0 + t * (v1 - v0)


def _lerp_vec(v0: List[float], v1: List[float], t: float) -> List[float]:
    return [_lerp(v0[i], v1[i], t) for i in range(len(v0))]


def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


class ScenesAnimationEngine:
    """Motor de páginas/cenas do SketchUp e gerador de interpolação de animações."""

    @classmethod
    def create_scene(
        cls,
        name: str,
        eye: List[float],
        target: List[float],
        up: List[float] = [0.0, 1.0, 0.0],
        fov: float = 35.0,
        is_orthographic: bool = False,
        transition_time: float = 1.5,
        delay_time: float = 1.0,
        include_in_animation: bool = True,
        use_camera: bool = True,
        use_shadow_info: bool = True,
        use_layer_visibility: bool = True,
        use_section_planes: bool = True,
        use_style: bool = True,
        hidden_tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Cria uma definição de cena SUPageRef canônica do SketchUp."""
        return {
            "type": "SUSceneRef",
            "name": name,
            "camera": {
                "eye": [round(c, 4) for c in eye],
                "target": [round(c, 4) for c in target],
                "up": [round(c, 4) for c in up],
                "fov": round(fov, 2),
                "is_orthographic": is_orthographic,
            },
            "transition_time": round(max(0.0, transition_time), 2),
            "delay_time": round(max(0.0, delay_time), 2),
            "include_in_animation": include_in_animation,
            "flags": {
                "use_camera": use_camera,
                "use_shadow_info": use_shadow_info,
                "use_layer_visibility": use_layer_visibility,
                "use_section_planes": use_section_planes,
                "use_style": use_style,
            },
            "hidden_tags": hidden_tags or [],
        }

    @classmethod
    def generate_animation_timeline(
        cls,
        scenes: List[Dict[str, Any]],
        fps: int = 30,
        loop: bool = True,
    ) -> Dict[str, Any]:
        """
        Gera uma timeline contínua interpolando suavemente câmera e tempos entre cenas ativas.
        """
        active_scenes = [s for s in scenes if s.get("include_in_animation", True)]
        if len(active_scenes) < 2:
            return {
                "total_duration_sec": 0.0,
                "total_frames": 0,
                "fps": fps,
                "frames": [],
                "keyframes": [],
            }

        pairs = []
        for i in range(len(active_scenes) - 1):
            pairs.append((active_scenes[i], active_scenes[i + 1]))
        if loop and len(active_scenes) > 2:
            pairs.append((active_scenes[-1], active_scenes[0]))

        frames: List[Dict[str, Any]] = []
        keyframes: List[Dict[str, Any]] = []
        current_time = 0.0

        for idx, (scene_a, scene_b) in enumerate(pairs):
            cam_a = scene_a["camera"]
            cam_b = scene_b["camera"]

            transition_sec = scene_b.get("transition_time", 1.5)
            delay_sec = scene_b.get("delay_time", 1.0)

            # Marca o keyframe de início
            keyframes.append({
                "scene_name": scene_a["name"],
                "timestamp_sec": round(current_time, 2),
                "frame_index": len(frames),
            })

            # 1. Frames de Transição interpolada (Smoothstep)
            n_trans_frames = max(1, int(transition_sec * fps))
            for f in range(n_trans_frames):
                raw_t = f / float(n_trans_frames)
                t = _smoothstep(raw_t)

                eye = _lerp_vec(cam_a["eye"], cam_b["eye"], t)
                target = _lerp_vec(cam_a["target"], cam_b["target"], t)
                up = _lerp_vec(cam_a["up"], cam_b["up"], t)
                fov = _lerp(cam_a["fov"], cam_b["fov"], t)

                frames.append({
                    "time_sec": round(current_time + (f / fps), 3),
                    "eye": [round(c, 4) for c in eye],
                    "target": [round(c, 4) for c in target],
                    "up": [round(c, 4) for c in up],
                    "fov": round(fov, 2),
                    "is_static": False,
                })

            current_time += transition_sec

            # 2. Frames de Espera estática na cena B (Delay)
            n_delay_frames = int(delay_sec * fps)
            for f in range(n_delay_frames):
                frames.append({
                    "time_sec": round(current_time + (f / fps), 3),
                    "eye": cam_b["eye"],
                    "target": cam_b["target"],
                    "up": cam_b["up"],
                    "fov": cam_b["fov"],
                    "is_static": True,
                })

            current_time += delay_sec

        return {
            "total_duration_sec": round(current_time, 2),
            "total_frames": len(frames),
            "fps": fps,
            "scenes_count": len(active_scenes),
            "keyframes": keyframes,
            "frames": frames,
        }
