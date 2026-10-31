"""
SketchBuild - Motor de Materiais com Canal Alfa e Componentes Face-Me (Zero DLL / Pure Python)
Frente 74: Engenharia Reversa do SketchUp - Alpha Masking & Face-Me Billboard Rotation

Gerencia materiais com transparência por canal alfa (PNG cutouts para vegetação e pessoas),
recorte de profundidade (alphaTest) e cálculo analítico de matrizes de rotação Face-Me
compatíveis com SUComponentDefinitionRef.behavior.camera_facing.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class AlphaTextureEngine:
    """Motor de controle de transparência por canal alfa e rotação de componentes Face-Me."""

    @classmethod
    def configure_alpha_material(
        cls,
        name: str,
        texture_path: str,
        alpha_mode: str = "MASK",  # MASK (AlphaTest) ou BLEND (Transparência suave)
        alpha_threshold: float = 0.5,
        double_sided: bool = True,
    ) -> Dict[str, Any]:
        """
        Gera os parâmetros de shader e renderização para texturas com recorte alfa.
        """
        is_mask = alpha_mode.upper() == "MASK"
        thresh = max(0.01, min(0.99, alpha_threshold))

        return {
            "type": "SUMaterialRef",
            "name": name,
            "texture_path": texture_path,
            "has_alpha": True,
            "alpha_mode": "MASK" if is_mask else "BLEND",
            "alpha_threshold": thresh,
            "double_sided": double_sided,
            "three_pbr": {
                "transparent": True,
                "alphaTest": thresh if is_mask else 0.0,
                "depthWrite": is_mask,  # MASK escreve no Z-Buffer para evitar sorting bugs
                "depthTest": True,
                "side": 2 if double_sided else 0,  # 2 = DoubleSide, 0 = FrontSide
            },
            "status": f"MATERIAL ALFA {alpha_mode.upper()} CONFIGURADO",
        }

    @classmethod
    def calculate_face_me_matrix(
        cls,
        instance_position: Tuple[float, float, float],
        camera_position: Tuple[float, float, float],
        axial_only: bool = True,  # True = gira apenas em torno do eixo Z (padrão SketchUp)
    ) -> Dict[str, Any]:
        """
        Calcula a matriz de transformação 4x4 (column-major) que rotaciona o componente Face-Me
        para encarar perfeitamente a câmera.
        """
        dx = camera_position[0] - instance_position[0]
        dy = camera_position[1] - instance_position[1]
        dz = camera_position[2] - instance_position[2]

        if axial_only:
            # Rotação apenas em torno do eixo Z (plano XY)
            angle_rad = math.atan2(dx, dy)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)

            # Matriz 4x4 column-major:
            # [ cos, -sin, 0, 0,
            #   sin,  cos, 0, 0,
            #     0,    0, 1, 0,
            #    px,   py, pz, 1 ]
            matrix = [
                round(cos_a, 6), round(sin_a, 6), 0.0, 0.0,
                round(-sin_a, 6), round(cos_a, 6), 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                round(instance_position[0], 4), round(instance_position[1], 4), round(instance_position[2], 4), 1.0,
            ]
            rot_deg = math.degrees(angle_rad)
        else:
            # Billboard esférico completo
            dist = math.sqrt(dx**2 + dy**2 + dz**2)
            if dist < 1e-6:
                matrix = [1,0,0,0, 0,1,0,0, 0,0,1,0, instance_position[0], instance_position[1], instance_position[2], 1]
                rot_deg = 0.0
            else:
                fwd = (dx / dist, dy / dist, dz / dist)
                # up = Z (0, 0, 1)
                right_x = fwd[1]
                right_y = -fwd[0]
                right_norm = math.sqrt(right_x**2 + right_y**2)
                if right_norm > 1e-6:
                    rx = right_x / right_norm
                    ry = right_y / right_norm
                else:
                    rx, ry = 1.0, 0.0
                ux = -fwd[2] * ry
                uy = fwd[2] * rx
                uz = fwd[0] * ry - fwd[1] * rx

                matrix = [
                    round(rx, 6), round(ry, 6), 0.0, 0.0,
                    round(ux, 6), round(uy, 6), round(uz, 6), 0.0,
                    round(fwd[0], 6), round(fwd[1], 6), round(fwd[2], 6), 0.0,
                    round(instance_position[0], 4), round(instance_position[1], 4), round(instance_position[2], 4), 1.0,
                ]
                rot_deg = 0.0

        return {
            "entity_type": "FaceMeTransform",
            "instance_position": list(instance_position),
            "camera_position": list(camera_position),
            "axial_only": axial_only,
            "yaw_rotation_deg": round(rot_deg, 2),
            "matrix_4x4_column_major": matrix,
            "status": "MATRIZ BILLBOARD FACE-ME CALCULADA",
        }
