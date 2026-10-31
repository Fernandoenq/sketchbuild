"""
Ferramenta de Linhas de Trajetória para Vista Explodida (Zero DLL).

Gera linhas-guia e trilhas tracejadas de montagem mecânica (Exploded Trails):
1. Conexão analítica entre posição montada (original) e posição explodida no espaço.
2. Traçado ortogonal ou linear direto com subdivisões para padrão tracejado.
3. Compatibilidade com Three.js LineDashedMaterial e pranchas 2D SVG de manual.
4. Pontos de ancoragem para fixadores, porcas e conectores estruturais.
"""

import math
from typing import List, Dict, Any, Tuple


class ExplodedViewTrailTool:
    """Motor analítico de trilhas e linhas de chamada de vista explodida."""

    @classmethod
    def calculate_trails(
        cls,
        parts: List[Dict[str, Any]],
        dash_size_m: float = 0.05,
        gap_size_m: float = 0.03
    ) -> Dict[str, Any]:
        """
        Calcula as trilhas de explosão entre as posições montadas e explodidas.
        parts: [{'id': str, 'name': str, 'original_pos': [x,y,z], 'exploded_pos': [x,y,z]}]
        """
        trails = []
        total_trail_length_m = 0.0

        for p in parts:
            p_id = p.get("id", "part")
            name = p.get("name", "Peça")
            orig = p.get("original_pos", [0.0, 0.0, 0.0])
            expl = p.get("exploded_pos", [0.0, 0.0, 0.0])

            dx = expl[0] - orig[0]
            dy = expl[1] - orig[1]
            dz = expl[2] - orig[2]
            dist = math.sqrt(dx**2 + dy**2 + dz**2)

            if dist < 0.01:
                # Peça não foi movida (peça raiz de base)
                continue

            total_trail_length_m += dist

            # Gera segmentos tracejados discretizados
            # Segmentos: ponto inicial, ponto final e direção unitária
            ux, uy, uz = dx / dist, dy / dist, dz / dist

            # Segmentação tracejada
            cycle = dash_size_m + gap_size_m
            num_dashes = max(1, int(dist / cycle))
            dashed_segments = []

            for i in range(num_dashes):
                t_start = i * cycle
                t_end = min(dist, t_start + dash_size_m)

                seg_start = [
                    round(orig[0] + t_start * ux, 4),
                    round(orig[1] + t_start * uy, 4),
                    round(orig[2] + t_start * uz, 4)
                ]
                seg_end = [
                    round(orig[0] + t_end * ux, 4),
                    round(orig[1] + t_end * uy, 4),
                    round(orig[2] + t_end * uz, 4)
                ]
                dashed_segments.append([seg_start, seg_end])

            trails.append({
                "part_id": p_id,
                "part_name": name,
                "start_point": [round(orig[0], 4), round(orig[1], 4), round(orig[2], 4)],
                "end_point": [round(expl[0], 4), round(expl[1], 4), round(expl[2], 4)],
                "length_m": round(dist, 3),
                "direction": [round(ux, 3), round(uy, 3), round(uz, 3)],
                "dashed_segments": dashed_segments,
                "segments_count": len(dashed_segments)
            })

        return {
            "entity_type": "ExplodedViewTrails",
            "parts_with_trails_count": len(trails),
            "total_trail_length_m": round(total_trail_length_m, 2),
            "dash_size_m": dash_size_m,
            "gap_size_m": gap_size_m,
            "trails": trails
        }
