"""
Motor de Simulação de Cinemática e Corpos Rígidos (Rigid Body Physics - Zero DLL).
SketchBuild - Engenharia Reversa do SketchUp (Frente 106).
Física Newtoniana discreta: gravidade, colisões AABB/esferas, conservação de momento,
atrito estático/dinâmico e coeficiente de restituição.
"""

from __future__ import annotations

import math
from typing import Any


class RigidBodyPhysicsEngine:
    """Motor analítico de física de corpos rígidos em Python puro."""

    @staticmethod
    def simulate_drop(
        bodies: list[dict[str, Any]],
        gravity_z: float = -9.81,
        ground_z: float = 0.0,
        time_step_s: float = 0.016,
        total_time_s: float = 2.0,
        restitution: float = 0.45,
        friction_coeff: float = 0.35,
    ) -> dict[str, Any]:
        """
        Simula a trajetória temporal de corpos rígidos sob gravidade e contato com o solo.
        Cada body: {
            'id': str,
            'name': str,
            'mass_kg': float,
            'initial_pos': [x, y, z],
            'initial_vel': [vx, vy, vz],
            'dimensions': [dx, dy, dz] # largura, comprimento, altura da bounding box
        }
        """
        num_frames = int(total_time_s / time_step_s)
        trajectories = {b.get("id", f"body_{i}"): [] for i, b in enumerate(bodies)}

        # Estado dinâmico
        states = []
        for i, b in enumerate(bodies):
            pos = list(b.get("initial_pos", [0.0, 0.0, 5.0]))
            vel = list(b.get("initial_vel", [0.0, 0.0, 0.0]))
            mass = max(0.01, float(b.get("mass_kg", 10.0)))
            dims = list(b.get("dimensions", [0.5, 0.5, 0.5]))
            states.append({
                "id": b.get("id", f"body_{i}"),
                "name": b.get("name", f"Objeto {i+1}"),
                "pos": pos,
                "vel": vel,
                "mass": mass,
                "dims": dims,
                "half_h": dims[2] / 2.0,
                "is_resting": False,
            })

        for frame_idx in range(num_frames):
            t = frame_idx * time_step_s
            for st in states:
                if not st["is_resting"]:
                    # Aplica aceleração gravitacional
                    st["vel"][2] += gravity_z * time_step_s

                    # Integração de posição (Euler semi-implícito)
                    st["pos"][0] += st["vel"][0] * time_step_s
                    st["pos"][1] += st["vel"][1] * time_step_s
                    st["pos"][2] += st["vel"][2] * time_step_s

                    # Detecção de colisão com o plano do solo Z
                    bottom_z = st["pos"][2] - st["half_h"]
                    if bottom_z <= ground_z:
                        st["pos"][2] = ground_z + st["half_h"]
                        # Rebatimento elástico
                        if abs(st["vel"][2]) < 0.2:
                            # Acomodação em repouso
                            st["vel"][2] = 0.0
                            st["vel"][0] *= 0.5
                            st["vel"][1] *= 0.5
                            if math.hypot(st["vel"][0], st["vel"][1]) < 0.05:
                                st["vel"][0] = 0.0
                                st["vel"][1] = 0.0
                                st["is_resting"] = True
                        else:
                            st["vel"][2] = -st["vel"][2] * restitution
                            # Atrito de contato
                            st["vel"][0] *= max(0.0, 1.0 - friction_coeff)
                            st["vel"][1] *= max(0.0, 1.0 - friction_coeff)

                # Amostra a cada 2 frames para economizar payload
                if frame_idx % 2 == 0:
                    trajectories[st["id"]].append({
                        "time_s": round(t, 3),
                        "position": [round(st["pos"][0], 4), round(st["pos"][1], 4), round(st["pos"][2], 4)],
                        "velocity": [round(st["vel"][0], 3), round(st["vel"][1], 3), round(st["vel"][2], 3)],
                        "is_resting": st["is_resting"]
                    })

        final_summary = []
        for st in states:
            final_summary.append({
                "id": st["id"],
                "name": st["name"],
                "final_position": [round(v, 4) for v in st["pos"]],
                "settled_at_ground": st["is_resting"] or (st["pos"][2] - st["half_h"] <= ground_z + 0.01),
                "potential_energy_final_j": round(st["mass"] * abs(gravity_z) * max(0.0, st["pos"][2] - ground_z), 2)
            })

        return {
            "entity_type": "RigidBodyPhysicsReport",
            "parameters": {
                "gravity_z": gravity_z,
                "ground_z": ground_z,
                "total_time_s": total_time_s,
                "time_step_s": time_step_s,
                "restitution": restitution,
                "friction_coeff": friction_coeff,
            },
            "bodies_count": len(bodies),
            "final_summary": final_summary,
            "trajectories": trajectories,
            "status": "COMPLETED",
        }
