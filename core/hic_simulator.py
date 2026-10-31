"""
Simulador de Impacto e Altura Crítica de Queda HIC (NBR 16071-3 / EN 1177 - Zero DLL).

Modela a desaceleração de impacto na cabeça segundo o Head Injury Criterion:
1. Cálculo do HIC <= 1000 e pico de desaceleração <= 200g.
2. Determinação da Altura Crítica de Queda (Critical Fall Height - CFH).
3. Dimensionamento da espessura de piso absorvedor (Areia, Casca de Madeira, EPDM, Grama).
4. Curva de desaceleração simulada a(t) durante os 30-50 milissegundos de contato.
"""

import math
from typing import List, Dict, Any, Tuple


class HicSimulator:
    """Motor de simulação de absorção de impacto e pisos atenuantes."""

    G: float = 9.80665  # m/s²

    # Tabela de coeficientes e propriedades de materiais atenuantes (NBR 16071-3)
    SURFACE_PROPERTIES = {
        "areia_lavada": {
            "name": "Areia Lavada Descompactada",
            "grain_size_mm": "0.2 a 2.0 mm",
            "min_thickness_layer_mm": 300,
            "max_cfh_m": 3.00,
            "rebound_coeff": 0.15,
        },
        "casca_madeira": {
            "name": "Cavaco de Eucalipto / Casca de Árvore",
            "grain_size_mm": "20 a 80 mm",
            "min_thickness_layer_mm": 300,
            "max_cfh_m": 3.00,
            "rebound_coeff": 0.12,
        },
        "borracha_epdm": {
            "name": "Piso Emborrachado EPDM Moldado In Loco",
            "grain_size_mm": "Resina PU + Grânulos EPDM",
            "min_thickness_layer_mm": 50,  # varia com a altura
            "max_cfh_m": 2.20,
            "rebound_coeff": 0.35,
        },
        "grama_natural": {
            "name": "Grama Natural sobre Terra Fofa",
            "grain_size_mm": "Vegetação Natural",
            "min_thickness_layer_mm": 0,
            "max_cfh_m": 1.00,
            "rebound_coeff": 0.18,
        }
    }

    @classmethod
    def simulate_impact(
        cls,
        fall_height_m: float = 1.80,
        surface_type: str = "areia_lavada",
        installed_thickness_mm: float = 300.0,
        head_mass_kg: float = 4.60  # Massa da cabeça de ensaio padrão ISO (4.6 kg)
    ) -> Dict[str, Any]:
        """
        Simula a colisão e calcula o índice HIC e desaceleração máxima.
        """
        surface = cls.SURFACE_PROPERTIES.get(surface_type, cls.SURFACE_PROPERTIES["areia_lavada"])
        cfh_limit = surface["max_cfh_m"]

        # Velocidade no início do impacto: v = sqrt(2 * g * h)
        impact_velocity_m_s = math.sqrt(2.0 * cls.G * fall_height_m)

        # Tempo de desaceleração (compressão da camada)
        # delta_t ~ 2 * s_deform / v_impact
        # Deformação plástica/elástica estimada proporcional à espessura da camada:
        max_deform_m = (installed_thickness_mm / 1000.0) * (0.25 if "borracha" in surface_type else 0.40)
        max_deform_m = max(0.015, min(max_deform_m, 0.15))

        impact_duration_s = max(0.012, (2.0 * max_deform_m) / max(0.5, impact_velocity_m_s))

        # Pico de desaceleração médio em 'g' (onda semi-senoidal)
        # a_peak = (pi/2) * (v / delta_t)
        a_peak_m_s2 = (math.pi * 0.5) * (impact_velocity_m_s / impact_duration_s)
        a_peak_g = a_peak_m_s2 / cls.G

        # Integração do HIC: HIC ~ (delta_t) * (a_avg / g)^2.5
        a_avg_g = (2.0 / math.pi) * a_peak_g
        hic_value = impact_duration_s * (a_avg_g ** 2.5)

        is_hic_compliant = (hic_value <= 1000.0) and (a_peak_g <= 200.0) and (fall_height_m <= cfh_limit)

        # Cálculo da espessura recomendada mínima para a altura dada
        if "borracha" in surface_type:
            # Emborrachado requer aprox 25mm para cada metro de queda
            recommended_thickness_mm = max(30.0, math.ceil(fall_height_m * 28.0 / 5.0) * 5.0)
        else:
            recommended_thickness_mm = 200.0 if fall_height_m <= 2.0 else 300.0

        # Discretização da curva de desaceleração a(t) em 20 pontos de amostragem
        curve_points = []
        samples = 20
        for i in range(samples + 1):
            t = (i / samples) * impact_duration_s
            # Perfil semi-senoidal a(t) = a_peak * sin(pi * t / duration)
            current_a_g = a_peak_g * math.sin(math.pi * t / impact_duration_s)
            curve_points.append({
                "time_ms": round(t * 1000.0, 2),
                "deceleration_g": round(max(0.0, current_a_g), 1)
            })

        return {
            "entity_type": "HicImpactAnalysis",
            "surface_name": surface["name"],
            "surface_type": surface_type,
            "fall_height_m": fall_height_m,
            "installed_thickness_mm": installed_thickness_mm,
            "recommended_thickness_mm": recommended_thickness_mm,
            "impact_velocity_m_s": round(impact_velocity_m_s, 2),
            "impact_duration_ms": round(impact_duration_s * 1000.0, 1),
            "peak_deceleration_g": round(a_peak_g, 1),
            "hic_score": round(hic_value, 1),
            "critical_fall_height_m": cfh_limit,
            "hic_limit": 1000.0,
            "peak_g_limit": 200.0,
            "is_compliant": is_hic_compliant,
            "curve_points_count": len(curve_points),
            "curve_points": curve_points,
            "safety_verdict": "PISO EM CONFORMIDADE TOTAL NBR 16071-3" if is_hic_compliant else "NÃO CONFORME - RISCO DE TRAUMA CRANIANO (Aumentar espessura do piso)"
        }
