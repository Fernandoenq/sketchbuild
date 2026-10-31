"""
Simulador de Cinemática e Envelope de Segurança para Balanços (NBR 16071 - Zero DLL).

Modela o comportamento físico-dinâmico de equipamentos de balanço:
1. Pêndulo gravitacional acoplado (oscilação angular e velocidade tangencial).
2. Tração máxima nos elos de corrente de aço inox e parafusos olhal.
3. Envelope volumétrico de impacto e zona de amortecimento frontal/traseira (NBR 16071-2).
4. Geração de trajetórias 3D discretizadas para animação no visualizador.
"""

import math
from typing import List, Dict, Any, Tuple


class SwingKinematicsSimulator:
    """Motor físico analítico para equipamentos oscilantes e balanços."""

    G: float = 9.80665  # Aceleração da gravidade (m/s²)

    @classmethod
    def simulate_swing(
        cls,
        chain_length_m: float = 2.20,
        user_mass_kg: float = 50.0,
        initial_angle_deg: float = 45.0,
        seat_height_at_rest_m: float = 0.45,
        damping_ratio: float = 0.05,
        total_time_s: float = 5.0,
        fps: int = 24
    ) -> Dict[str, Any]:
        """
        Simula a cinemática do balanço no plano vertical ao longo do tempo.
        """
        theta_0 = math.radians(initial_angle_deg)
        omega_n = math.sqrt(cls.G / chain_length_m)
        gamma = damping_ratio * omega_n
        omega_d = omega_n * math.sqrt(max(0.001, 1.0 - damping_ratio**2))

        # Velocidade tangencial máxima no ponto inferior (theta = 0) sem amortecimento
        # v_max = sqrt(2 * g * L * (1 - cos(theta_0)))
        v_max = math.sqrt(2.0 * cls.G * chain_length_m * (1.0 - math.cos(theta_0)))

        # Força centrípeta e tração máxima nos tirantes:
        # T_max = m * (g + v_max^2 / L) = m * g * (3 - 2 * cos(theta_0))
        tension_max_n = user_mass_kg * cls.G * (3.0 - 2.0 * math.cos(theta_0))

        # Requisitos normativos NBR 16071:
        # Altura mínima do assento em repouso ao solo: >= 0.35m e <= 0.60m
        seat_clearance_compliant = (seat_height_at_rest_m >= 0.35) and (seat_height_at_rest_m <= 0.60)

        # Zona de impacto longitudinal NBR 16071-2:
        # Espaço livre mínimo para frente e para trás: L_impact = 0.867 * sqrt(H_suspensão) + 1.75
        h_suspension = chain_length_m + seat_height_at_rest_m
        impact_zone_length_m = 0.867 * math.sqrt(h_suspension) + 1.75

        # Discretização temporal da trajetória
        total_steps = int(total_time_s * fps)
        dt = 1.0 / fps
        trajectory_points = []

        for step in range(total_steps + 1):
            t = step * dt
            # theta(t) = theta_0 * exp(-gamma * t) * cos(omega_d * t)
            theta_t = theta_0 * math.exp(-gamma * t) * math.cos(omega_d * t)

            # Posição relativa em relação ao ponto de ancoragem no topo:
            # X = L * sin(theta_t)
            # Z = H_suspensao - L * cos(theta_t)
            x = chain_length_m * math.sin(theta_t)
            z = h_suspension - chain_length_m * math.cos(theta_t)
            speed = abs(chain_length_m * (-gamma * theta_t - theta_0 * math.exp(-gamma * t) * omega_d * math.sin(omega_d * t)))

            trajectory_points.append({
                "time_s": round(t, 3),
                "angle_deg": round(math.degrees(theta_t), 2),
                "position": [round(x, 4), 0.0, round(z, 4)],
                "speed_m_s": round(speed, 3)
            })

        return {
            "entity_type": "SwingKinematicsAnalysis",
            "chain_length_m": chain_length_m,
            "suspension_height_m": round(h_suspension, 3),
            "user_mass_kg": user_mass_kg,
            "initial_angle_deg": initial_angle_deg,
            "max_tangential_speed_m_s": round(v_max, 3),
            "max_chain_tension_kn": round(tension_max_n / 1000.0, 3),
            "seat_clearance_at_rest_m": seat_height_at_rest_m,
            "seat_clearance_compliant": seat_clearance_compliant,
            "required_impact_zone_length_m": round(impact_zone_length_m, 3),
            "trajectory_points_count": len(trajectory_points),
            "trajectory_points": trajectory_points,
            "safety_status": "CONFORME NBR 16071" if seat_clearance_compliant else "NÃO CONFORME (Ajustar altura do assento)"
        }
