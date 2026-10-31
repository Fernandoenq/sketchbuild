"""
Motor de Estabilidade de Taludes e Encostas Método de Bishop Simplificado (Slope Stability - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 121).
Análise geotécnica de equilíbrio limite para superfícies de ruptura circulares em solos coesivos-friccionais,
discretização em fatias verticais e convergência iterativa do Fator de Segurança (FS).
"""

from __future__ import annotations

import math
from typing import Any


class SlopeStabilityBishopEngine:
    """Motor analítico de estabilidade de taludes por Bishop Simplificado em Python puro."""

    @staticmethod
    def calculate_stability(
        slope_height_m: float = 8.0,  # Altura vertical do talude (m)
        slope_angle_deg: float = 35.0,  # Ângulo de inclinação com a horizontal
        soil_cohesion_kpa: float = 12.0,  # Coesão efetiva c' (kPa)
        soil_friction_angle_deg: float = 28.0,  # Ângulo de atrito interno phi' (graus)
        soil_unit_weight_kn_m3: float = 19.0,  # Peso específico gamma (kN/m3)
        piezometric_ru: float = 0.15,  # Razão de poro-pressão ru (presença de lençol freático)
        slices_count: int = 15,
    ) -> dict[str, Any]:
        """
        Discretiza a massa escorregante em fatias e itera a equação não-linear de Bishop:
        FS = sum [ (c'*b + (W - u*b)*tan(phi')) / m_alpha ] / sum [ W * sin(alpha) ]
        onde m_alpha = cos(alpha) * (1 + tan(alpha)*tan(phi') / FS)
        """
        # Geometria do talude
        slope_rad = math.radians(slope_angle_deg)
        phi_rad = math.radians(soil_friction_angle_deg)
        c_kpa = soil_cohesion_kpa
        gamma = soil_unit_weight_kn_m3

        # Centro e raio estimado do círculo crítico de ruptura
        radius_m = slope_height_m * 1.6
        xc_m = slope_height_m * 0.4
        yc_m = slope_height_m * 1.5

        # Discretização em fatias
        x_min = -slope_height_m / math.tan(slope_rad)
        x_max = radius_m * 0.8
        total_width_m = x_max - x_min
        slice_width_m = total_width_m / max(5, slices_count)

        slices_data = []
        driving_moment_sum = 0.0

        for i in range(slices_count):
            xi = x_min + (i + 0.5) * slice_width_m
            # Posição Y da base do círculo: yc - sqrt(R^2 - (xi - xc)^2)
            dx = xi - xc_m
            if abs(dx) < radius_m:
                y_circle = yc_m - math.sqrt(radius_m**2 - dx**2)
            else:
                y_circle = 0.0

            # Posição Y do terreno
            if xi <= 0.0:
                y_ground = max(0.0, slope_height_m + xi * math.tan(slope_rad))
            else:
                y_ground = slope_height_m

            slice_height_m = max(0.2, y_ground - y_circle)
            weight_kn = slice_height_m * slice_width_m * gamma

            # Ângulo alpha da base da fatia com a horizontal: sin(alpha) = dx / R
            sin_alpha = dx / radius_m
            sin_alpha = max(-0.95, min(0.95, sin_alpha))
            alpha_rad = math.asin(sin_alpha)
            cos_alpha = math.cos(alpha_rad)

            u_kpa = piezometric_ru * gamma * slice_height_m

            driving_moment_sum += weight_kn * sin_alpha

            slices_data.append({
                "weight_kn": weight_kn,
                "alpha_rad": alpha_rad,
                "cos_alpha": cos_alpha,
                "sin_alpha": sin_alpha,
                "u_kpa": u_kpa,
                "width_m": slice_width_m,
            })

        driving_moment_sum = max(1.0, driving_moment_sum)

        # Iteração de convergência do Fator de Segurança (Bishop)
        fs_curr = 1.30
        for _ in range(25):
            resisting_sum = 0.0
            for sl in slices_data:
                tan_alpha = math.tan(sl["alpha_rad"])
                m_alpha = sl["cos_alpha"] * (1.0 + (tan_alpha * math.tan(phi_rad)) / fs_curr)
                if abs(m_alpha) < 0.1:
                    m_alpha = 0.1

                numerator = (c_kpa * sl["width_m"]) + ((sl["weight_kn"] - sl["u_kpa"] * sl["width_m"]) * math.tan(phi_rad))
                resisting_sum += numerator / m_alpha

            fs_next = resisting_sum / driving_moment_sum
            if abs(fs_next - fs_curr) < 0.002:
                fs_curr = fs_next
                break
            fs_curr = fs_next

        fs_final = round(max(0.5, min(5.0, fs_curr)), 2)
        is_safe = fs_final >= 1.50

        # Arco 3D do círculo de ruptura para renderização
        arc_points = []
        for sl_idx in range(len(slices_data)):
            xi = x_min + sl_idx * slice_width_m
            dx = xi - xc_m
            if abs(dx) < radius_m:
                yi = yc_m - math.sqrt(radius_m**2 - dx**2)
            else:
                yi = 0.0
            arc_points.append([round(xi, 2), round(yi, 2), 0.0])

        return {
            "entity_type": "SlopeStabilityReport",
            "parameters": {
                "slope_height_m": slope_height_m,
                "slope_angle_deg": slope_angle_deg,
                "soil_cohesion_kpa": soil_cohesion_kpa,
                "soil_friction_angle_deg": soil_friction_angle_deg,
                "soil_unit_weight_kn_m3": soil_unit_weight_kn_m3,
                "piezometric_ru": piezometric_ru,
                "slices_count": slices_count,
            },
            "stability_analysis": {
                "factor_of_safety_bishop": fs_final,
                "critical_circle_radius_m": round(radius_m, 2),
                "critical_circle_center_xy_m": [round(xc_m, 2), round(yc_m, 2)],
                "is_stable_nbr11682": is_safe,
                "status_label": f"TALUDE ESTÁVEL (FS = {fs_final} >= 1.50)" if is_safe else f"ALERTA: RISCO DE ESCORREGAMENTO (FS = {fs_final} < 1.50)",
            },
            "failure_arc_points": arc_points,
            "status": "COMPUTED",
        }
