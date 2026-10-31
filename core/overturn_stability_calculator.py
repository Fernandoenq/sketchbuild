"""
Calculador de Centro de Gravidade e Estabilidade ao Tombamento (NBR 16071 / NBR 6123 - Zero DLL).

Avalia o risco de tombamento de estruturas de recreio sob ação combinada:
1. Centro de Gravidade (CG) volumétrico e polígono de sustentação da base.
2. Momento Restaurador gravitacional (estabilizante).
3. Ação do vento segundo ABNT NBR 6123 e empuxo dinâmico de usuários.
4. Fator de Segurança ao tombamento (FS >= 1.50) e lastro/sapata mínima de concreto.
"""

import math
from typing import List, Dict, Any, Tuple


class OverturnStabilityCalculator:
    """Motor analítico de cálculo de estabilidade estática e tombamento."""

    G: float = 9.80665  # m/s²
    DENSITY_CONCRETE_KG_M3: float = 2400.0  # Concreto armado/simples

    @classmethod
    def calculate_stability(
        cls,
        total_mass_kg: float = 850.0,
        cg_position: Tuple[float, float, float] = (1.50, 1.20, 1.45),
        base_support_points: List[Tuple[float, float]] = None,
        wind_speed_km_h: float = 100.0,
        exposed_frontal_area_m2: float = 6.50,
        lateral_live_load_n: float = 500.0,
        live_load_height_m: float = 1.80
    ) -> Dict[str, Any]:
        """
        Calcula os momentos estabilizantes e de tombamento da estrutura.
        """
        if not base_support_points:
            # Apoios retangulares padrão nos cantos de um deck 3.0 x 2.4 m
            base_support_points = [(0.0, 0.0), (3.0, 0.0), (3.0, 2.4), (0.0, 2.4)]

        # Determina a menor distância do CG projetado no solo (x, y) até as bordas da base
        cg_x, cg_y, cg_z = cg_position

        # Menor braço de alavanca para os 4 quadrantes da base
        min_x = min(p[0] for p in base_support_points)
        max_x = max(p[0] for p in base_support_points)
        min_y = min(p[1] for p in base_support_points)
        max_y = max(p[1] for p in base_support_points)

        dist_left = abs(cg_x - min_x)
        dist_right = abs(max_x - cg_x)
        dist_front = abs(cg_y - min_y)
        dist_back = abs(max_y - cg_y)

        restoring_arm_m = min(dist_left, dist_right, dist_front, dist_back)

        # 1. Momento Restaurador (Estabilizante)
        # M_rest = Peso * braco_minimo
        weight_n = total_mass_kg * cls.G
        restoring_moment_n_m = weight_n * restoring_arm_m

        # 2. Ação do Vento (NBR 6123)
        # Velocidade em m/s:
        v_m_s = wind_speed_km_h / 3.6
        # Pressão dinâmica de vento: q = 0.613 * v^2 (N/m²)
        wind_pressure_pa = 0.613 * (v_m_s ** 2)
        # Coeficiente de arrasto/forma Cf ~ 1.2 para treliças/estruturas lúdicas
        drag_coeff = 1.2
        wind_force_n = wind_pressure_pa * exposed_frontal_area_m2 * drag_coeff
        wind_application_height_m = cg_z  # Aplica na altura média do centroide

        overturning_wind_moment = wind_force_n * wind_application_height_m
        overturning_live_moment = lateral_live_load_n * live_load_height_m

        total_overturning_moment = overturning_wind_moment + overturning_live_moment

        # 3. Fator de Segurança (FS = M_rest / M_tomb)
        if total_overturning_moment > 1e-6:
            safety_factor = restoring_moment_n_m / total_overturning_moment
        else:
            safety_factor = 99.0

        is_stable = safety_factor >= 1.50

        # 4. Cálculo de Lastro ou Sapata de Concreto Adicional se instável
        extra_ballast_kg = 0.0
        concrete_volume_m3 = 0.0
        if safety_factor < 1.50:
            # Requer: (weight_n + ballast_n) * restoring_arm_m >= 1.50 * total_overturning_moment
            required_weight_n = (1.50 * total_overturning_moment) / max(0.1, restoring_arm_m)
            extra_weight_needed = max(0.0, required_weight_n - weight_n)
            extra_ballast_kg = extra_weight_needed / cls.G
            concrete_volume_m3 = extra_ballast_kg / cls.DENSITY_CONCRETE_KG_M3

        return {
            "entity_type": "OverturnStabilityAnalysis",
            "total_mass_kg": round(total_mass_kg, 1),
            "center_of_gravity": [round(cg_x, 3), round(cg_y, 3), round(cg_z, 3)],
            "restoring_arm_m": round(restoring_arm_m, 3),
            "restoring_moment_kn_m": round(restoring_moment_n_m / 1000.0, 3),
            "wind_speed_km_h": wind_speed_km_h,
            "wind_pressure_pa": round(wind_pressure_pa, 1),
            "wind_force_kn": round(wind_force_n / 1000.0, 3),
            "overturning_moment_kn_m": round(total_overturning_moment / 1000.0, 3),
            "safety_factor": round(safety_factor, 2),
            "required_safety_factor": 1.50,
            "is_stable": is_stable,
            "extra_ballast_kg": round(extra_ballast_kg, 1),
            "extra_concrete_volume_m3": round(concrete_volume_m3, 3),
            "status": "ESTÁVEL (FS >= 1.50)" if is_stable else f"INSTÁVEL - REQUER SAPATAS DE CONCRETO ({extra_ballast_kg:.0f} kg)"
        }
