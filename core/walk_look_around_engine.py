"""
Motor das Ferramentas Nativas Caminhar, Olhar em Volta e Posicionar Câmera do SketchUp (Zero DLL).

Implementa a engenharia reversa das 3 ferramentas clássicas da barra Câmera do SketchUp:
1. Posicionar Câmera (Position Camera):
   - Fixa o olho do observador no ponto (x, y, z + eye_height) e direciona para um alvo de visada.
   - Padrão de altura dos olhos (eye_height): 1.68m (ajustável no VCB).
2. Olhar em Volta (Look Around):
   - Mantém a posição do observador fixa e rotaciona o vetor de visão em Yaw (azimute) e Pitch (elevação).
   - Bloqueio de gimbal (clamp de pitch entre -89° e +89°) para evitar inversão do horizonte.
3. Caminhar (Walk):
   - Navegação cinemática em 1ª pessoa com translação em x/y (frente/trás/estrado).
   - Detecção analítica de colisão contra caixas delimitadoras (AABB) de obstáculos/paredes.
   - Transposição de degraus (step-up) para escadas até a altura limite de 0.22m.
   - Aderência ao solo / gravidade simples mantendo eye_height sobre o terreno.
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class WalkLookAroundEngine:
    """Motor analítico de navegação em primeira pessoa nativo do SketchUp."""

    DEFAULT_EYE_HEIGHT_M = 1.68
    MAX_STEP_UP_M = 0.22
    COLLISION_RADIUS_M = 0.30

    @classmethod
    def position_camera(
        cls,
        eye_x: float,
        eye_y: float,
        eye_z: float,
        target_x: float,
        target_y: float,
        target_z: float,
        eye_height_m: float = DEFAULT_EYE_HEIGHT_M,
        use_eye_height_offset: bool = True
    ) -> Dict[str, Any]:
        """
        Posiciona a câmera na coordenada clicada.
        Se use_eye_height_offset for True, eleva a coordenada Z pela altura do observador.
        """
        final_eye_z = eye_z + (eye_height_m if use_eye_height_offset else 0.0)

        # Vetor de direção
        dx = target_x - eye_x
        dy = target_y - eye_y
        dz = target_z - final_eye_z
        dist = math.sqrt(dx * dx + dy * dy + dz * dz)

        if dist < 1e-6:
            # Alvo padrão olhando para o norte (+Y horizontal)
            dx, dy, dz = 0.0, 1.0, 0.0
            dist = 1.0

        dir_norm = (dx / dist, dy / dist, dz / dist)

        # Ângulos de Euler
        yaw_rad = math.atan2(dx, dy)  # 0 = Norte (+Y), pi/2 = Leste (+X)
        pitch_rad = math.asin(max(-1.0, min(1.0, dz / dist)))

        return {
            "eye": (round(eye_x, 4), round(eye_y, 4), round(final_eye_z, 4)),
            "target": (round(target_x, 4), round(target_y, 4), round(target_z, 4)),
            "direction": (round(dir_norm[0], 4), round(dir_norm[1], 4), round(dir_norm[2], 4)),
            "eye_height_m": round(eye_height_m, 3),
            "yaw_deg": round(math.degrees(yaw_rad), 2),
            "pitch_deg": round(math.degrees(pitch_rad), 2),
            "up": (0.0, 0.0, 1.0),
            "fov_deg": 35.0  # FOV padrão arquitetônico do SketchUp ao posicionar câmera
        }

    @classmethod
    def look_around(
        cls,
        eye: Tuple[float, float, float],
        current_yaw_deg: float,
        current_pitch_deg: float,
        delta_yaw_deg: float,
        delta_pitch_deg: float,
        target_distance_m: float = 10.0
    ) -> Dict[str, Any]:
        """
        Gira a visão mantendo a posição dos olhos fixa (Look Around).
        Aplica clamp estrito no pitch para evitar flip do horizonte.
        """
        new_yaw_deg = (current_yaw_deg + delta_yaw_deg) % 360.0
        new_pitch_deg = max(-89.0, min(89.0, current_pitch_deg + delta_pitch_deg))

        yaw_rad = math.radians(new_yaw_deg)
        pitch_rad = math.radians(new_pitch_deg)

        # Conversão de ângulos esféricos para vetor cartesiano no padrão Z-Up
        dir_x = math.sin(yaw_rad) * math.cos(pitch_rad)
        dir_y = math.cos(yaw_rad) * math.cos(pitch_rad)
        dir_z = math.sin(pitch_rad)

        target = (
            eye[0] + dir_x * target_distance_m,
            eye[1] + dir_y * target_distance_m,
            eye[2] + dir_z * target_distance_m
        )

        return {
            "eye": (round(eye[0], 4), round(eye[1], 4), round(eye[2], 4)),
            "target": (round(target[0], 4), round(target[1], 4), round(target[2], 4)),
            "direction": (round(dir_x, 4), round(dir_y, 4), round(dir_z, 4)),
            "yaw_deg": round(new_yaw_deg, 2),
            "pitch_deg": round(new_pitch_deg, 2),
            "up": (0.0, 0.0, 1.0)
        }

    @classmethod
    def walk_step(
        cls,
        current_eye: Tuple[float, float, float],
        yaw_deg: float,
        move_forward: float,   # Metros para frente (+) ou trás (-)
        move_strafe: float,    # Metros para direita (+) ou esquerda (-)
        obstacles_aabb: Optional[List[Dict[str, Any]]] = None,
        terrain_elevation_z: Optional[float] = None,
        eye_height_m: float = DEFAULT_EYE_HEIGHT_M,
        enable_collision: bool = True
    ) -> Dict[str, Any]:
        """
        Executa um passo de caminhada em primeira pessoa (Walk).
        Calcula translação horizontal baseada no Yaw, colisão com AABBs e subida de degraus.
        """
        yaw_rad = math.radians(yaw_deg)
        fwd_x = math.sin(yaw_rad)
        fwd_y = math.cos(yaw_rad)

        right_x = math.cos(yaw_rad)
        right_y = -math.sin(yaw_rad)

        delta_x = (fwd_x * move_forward) + (right_x * move_strafe)
        delta_y = (fwd_y * move_forward) + (right_y * move_strafe)

        candidate_x = current_eye[0] + delta_x
        candidate_y = current_eye[1] + delta_y
        candidate_foot_z = current_eye[2] - eye_height_m

        collision_detected = False
        step_up_applied = False
        collided_obstacle = None

        if enable_collision and obstacles_aabb:
            for obs in obstacles_aabb:
                # Cada AABB: {'min_x', 'max_x', 'min_y', 'max_y', 'min_z', 'max_z'}
                min_x = obs.get("min_x", 0.0) - cls.COLLISION_RADIUS_M
                max_x = obs.get("max_x", 0.0) + cls.COLLISION_RADIUS_M
                min_y = obs.get("min_y", 0.0) - cls.COLLISION_RADIUS_M
                max_y = obs.get("max_y", 0.0) + cls.COLLISION_RADIUS_M
                top_z = obs.get("max_z", 0.0)

                # Verifica se a nova posição horizontal penetra a AABB
                if min_x <= candidate_x <= max_x and min_y <= candidate_y <= max_y:
                    # Verifica altura do obstáculo
                    step_diff = top_z - candidate_foot_z
                    if 0.0 < step_diff <= cls.MAX_STEP_UP_M:
                        # Degrau transponível (ex: escada)
                        candidate_foot_z = top_z
                        step_up_applied = True
                    elif step_diff > cls.MAX_STEP_UP_M:
                        # Parede / obstáculo intransponível
                        collision_detected = True
                        collided_obstacle = obs
                        break

        if collision_detected:
            # Não move no eixo colidido
            final_x = current_eye[0]
            final_y = current_eye[1]
            final_z = current_eye[2]
        else:
            final_x = candidate_x
            final_y = candidate_y
            # Ajuste de gravidade / terreno se fornecido
            if terrain_elevation_z is not None:
                final_z = max(terrain_elevation_z, candidate_foot_z) + eye_height_m
            else:
                final_z = candidate_foot_z + eye_height_m

        # Direção de visada para reconstruir target
        target = (
            final_x + fwd_x * 5.0,
            final_y + fwd_y * 5.0,
            final_z
        )

        return {
            "eye": (round(final_x, 4), round(final_y, 4), round(final_z, 4)),
            "target": (round(target[0], 4), round(target[1], 4), round(target[2], 4)),
            "moved": not collision_detected and (abs(delta_x) > 1e-4 or abs(delta_y) > 1e-4),
            "collision_detected": collision_detected,
            "step_up_applied": step_up_applied,
            "collided_obstacle": collided_obstacle,
            "eye_height_m": round(eye_height_m, 3),
            "up": (0.0, 0.0, 1.0)
        }
