"""
Motor de Dolly de Câmera, Campo de Visão (FOV) e Lente Fotográfica do SketchUp (Zero DLL).

Implementa a engenharia reversa do comportamento de câmera da Ferramenta Zoom do SketchUp:
1. Equivalência Campo de Visão (FOV) vs Lente Fotográfica (Focal Length mm):
   - No SketchUp Desktop, ao selecionar a ferramenta Zoom, a caixa VCB (Measurements)
     permite digitar graus (ex: '35 deg') ou distância focal equivalente em filme 35mm (ex: '50 mm').
   - Padrão 35mm full-frame tem largura horizontal de sensor w = 36.0 mm.
   - Fórmula ótica:
     f_mm = w / (2 * tan(fov_rad / 2)) = 36.0 / (2 * tan(fov_rad / 2))
     fov_deg = 2 * arctan(36.0 / (2 * f_mm)) * (180 / pi)
2. Dolly de Câmera (Dolly Zoom / Truck):
   - Deslocamento da posição da câmera (eye) ao longo do vetor diretor da linha de visão
     (eye -> target) por uma distância delta (metros).
   - Modo 'KEEP_TARGET': Aproxima o observador mantendo o ponto focal fixo.
   - Modo 'MOVE_TARGET': Desloca tanto o olho quanto o ponto focal em conjunto.
"""

import math
from typing import Dict, Any, Tuple


class DollyFovLensEngine:
    """Motor analítico de controle de lente, FOV e dolly de câmera do SketchUp."""

    SENSOR_WIDTH_MM: float = 36.0  # Padrão fotográfico 35mm full-frame do SketchUp

    @classmethod
    def fov_degrees_to_focal_length_mm(cls, fov_deg: float) -> float:
        """
        Converte ângulo de visão horizontal (graus) para distância focal equivalente (mm).
        """
        clamped_fov = max(1.0, min(170.0, float(fov_deg)))
        half_fov_rad = math.radians(clamped_fov / 2.0)
        f_mm = cls.SENSOR_WIDTH_MM / (2.0 * math.tan(half_fov_rad))
        return round(f_mm, 2)

    @classmethod
    def focal_length_mm_to_fov_degrees(cls, focal_length_mm: float) -> float:
        """
        Converte distância focal de lente 35mm (mm) para ângulo de visão horizontal (graus).
        """
        clamped_f = max(1.0, min(2000.0, float(focal_length_mm)))
        half_fov_rad = math.atan(cls.SENSOR_WIDTH_MM / (2.0 * clamped_f))
        fov_deg = math.degrees(half_fov_rad * 2.0)
        return round(fov_deg, 2)

    @classmethod
    def parse_vcb_camera_input(cls, vcb_text: str) -> Dict[str, Any]:
        """
        Analisa a entrada de texto do VCB do SketchUp para a ferramenta Zoom:
        - '50mm', '35 mm' -> interpreta como lente e calcula FOV.
        - '60 deg', '45deg', '30' -> interpreta como graus de FOV e calcula lente mm.
        """
        clean = str(vcb_text).strip().lower()
        if "mm" in clean:
            val_str = clean.replace("mm", "").strip()
            try:
                f_mm = float(val_str)
                fov_deg = cls.focal_length_mm_to_fov_degrees(f_mm)
                return {
                    "input_type": "FOCAL_LENGTH_MM",
                    "focal_length_mm": f_mm,
                    "fov_degrees": fov_deg,
                    "vcb_formatted": f"{f_mm:.1f} mm"
                }
            except ValueError:
                pass

        if "deg" in clean:
            clean = clean.replace("deg", "").strip()

        try:
            fov_deg = float(clean)
            f_mm = cls.fov_degrees_to_focal_length_mm(fov_deg)
            return {
                "input_type": "FOV_DEGREES",
                "fov_degrees": fov_deg,
                "focal_length_mm": f_mm,
                "vcb_formatted": f"{fov_deg:.1f} deg"
            }
        except ValueError:
            return {
                "input_type": "UNKNOWN",
                "error": f"Entrada VCB inválida: '{vcb_text}'",
                "fov_degrees": 35.0,
                "focal_length_mm": cls.fov_degrees_to_focal_length_mm(35.0)
            }

    @classmethod
    def apply_camera_dolly(
        cls,
        eye_xyz: Tuple[float, float, float],
        target_xyz: Tuple[float, float, float],
        delta_m: float,
        mode: str = "KEEP_TARGET"
    ) -> Dict[str, Any]:
        """
        Desloca a câmera ao longo do eixo de visão.
        delta_m > 0 avança em direção ao target (dolly in).
        delta_m < 0 recua afastando-se do target (dolly out).
        """
        dx = target_xyz[0] - eye_xyz[0]
        dy = target_xyz[1] - eye_xyz[1]
        dz = target_xyz[2] - eye_xyz[2]
        dist = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)

        if dist < 1e-6:
            # Vetor padrão para frente (-Y)
            dir_x, dir_y, dir_z = 0.0, -1.0, 0.0
            dist = 1.0
        else:
            dir_x, dir_y, dir_z = dx / dist, dy / dist, dz / dist

        # Novo ponto de observação
        new_eye_x = eye_xyz[0] + dir_x * delta_m
        new_eye_y = eye_xyz[1] + dir_y * delta_m
        new_eye_z = eye_xyz[2] + dir_z * delta_m

        mode_upper = mode.upper().strip()
        if mode_upper == "MOVE_TARGET":
            new_target_x = target_xyz[0] + dir_x * delta_m
            new_target_y = target_xyz[1] + dir_y * delta_m
            new_target_z = target_xyz[2] + dir_z * delta_m
        else:
            # KEEP_TARGET: target permanece inalterado
            new_target_x, new_target_y, new_target_z = target_xyz

        new_dist = math.sqrt(
            (new_target_x - new_eye_x) ** 2 +
            (new_target_y - new_eye_y) ** 2 +
            (new_target_z - new_eye_z) ** 2
        )

        return {
            "status": "success",
            "mode": mode_upper,
            "delta_m": delta_m,
            "previous_eye": list(eye_xyz),
            "new_eye": [round(new_eye_x, 4), round(new_eye_y, 4), round(new_eye_z, 4)],
            "previous_target": list(target_xyz),
            "new_target": [round(new_target_x, 4), round(new_target_y, 4), round(new_target_z, 4)],
            "new_distance_to_target_m": round(new_dist, 4)
        }
