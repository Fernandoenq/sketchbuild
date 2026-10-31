"""
SketchBuild - Padrões Voronoi e Painéis Vazados Paramétricos 3D (Zero DLL / Pure Python)
Frente 102: Engenharia Reversa do SketchUp - Voronoi Fracture & Parametric Lattice Panels

Gera painéis arquitetônicos vazados e malhas de fratura Voronoi sobre chapas e superfícies,
com controle de sementes, folga/espaçamento entre células (inset) e extrusão 3D.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Tuple


class VoronoiFractureEngine:
    """Motor analítico de células Voronoi e painéis arquitetônicos paramétricos."""

    @staticmethod
    def _dist_sq(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2

    @staticmethod
    def generate_voronoi_panel(
        width_m: float = 2.0,
        height_m: float = 1.0,
        thickness_m: float = 0.03,
        num_seeds: int = 12,
        seed_random_seed: int = 42,
        cell_inset_ratio: float = 0.20
    ) -> Dict[str, Any]:
        """
        Gera uma aproximação analítica de células de Voronoi recortadas sobre placa retangular.
        Gera as células fechadas, centróides e polígonos inset para vazamento 3D.
        """
        random.seed(seed_random_seed)

        # 1. Gerar sementes internas
        seeds: List[Tuple[float, float]] = []
        margin = min(width_m, height_m) * 0.1
        for _ in range(num_seeds):
            sx = margin + random.random() * (width_m - 2.0 * margin)
            sy = margin + random.random() * (height_m - 2.0 * margin)
            seeds.append((round(sx, 4), round(sy, 4)))

        # 2. Aproximar células Voronoi para cada semente via leque angular
        # Para cada semente, varre 16 ângulos e encontra o raio de fronteira até vizinho mais próximo ou borda
        cells: List[Dict[str, Any]] = []
        num_angles = 12

        for s_idx, (sx, sy) in enumerate(seeds):
            cell_pts: List[List[float]] = []
            inset_pts: List[List[float]] = []

            for a in range(num_angles):
                theta = (2.0 * math.pi * a) / num_angles
                dx = math.cos(theta)
                dy = math.sin(theta)

                # Raio limite até a borda retangular do painel
                r_edge = float("inf")
                if dx > 1e-4:
                    r_edge = min(r_edge, (width_m - sx) / dx)
                elif dx < -1e-4:
                    r_edge = min(r_edge, (0.0 - sx) / dx)

                if dy > 1e-4:
                    r_edge = min(r_edge, (height_m - sy) / dy)
                elif dy < -1e-4:
                    r_edge = min(r_edge, (0.0 - sy) / dy)

                # Raio limite até a bissetriz com cada vizinho Voronoi
                r_neighbor = float("inf")
                for o_idx, (ox, oy) in enumerate(seeds):
                    if o_idx == s_idx:
                        continue
                    # Ponto médio e vetor normal da bissetriz
                    mx = (sx + ox) / 2.0
                    my = (sy + oy) / 2.0
                    nx = ox - sx
                    ny = oy - sy
                    denom = nx * dx + ny * dy
                    if denom > 1e-4:
                        # Raio de interseção: (M - S) . N / (D . N)
                        num = (mx - sx) * nx + (my - sy) * ny
                        r_int = num / denom
                        if r_int > 0:
                            r_neighbor = min(r_neighbor, r_int)

                r_final = max(0.02, min(r_edge, r_neighbor))
                r_inset = max(0.01, r_final * (1.0 - cell_inset_ratio))

                # Ponto do perímetro da célula
                px = sx + r_final * dx
                py = sy + r_final * dy
                cell_pts.append([round(px, 4), round(py, 4), 0.0])

                # Ponto vazado interno com folga
                ix = sx + r_inset * dx
                iy = sy + r_inset * dy
                inset_pts.append([round(ix, 4), round(iy, 4), 0.0])

            cells.append({
                "cell_id": s_idx,
                "seed": [sx, sy, 0.0],
                "outer_loop": cell_pts,
                "inner_inset_loop": inset_pts,
            })

        return {
            "entity_type": "VoronoiPanelResult",
            "panel_dimensions_m": [width_m, height_m, thickness_m],
            "seeds_count": len(seeds),
            "seeds": [list(s) for s in seeds],
            "cells": cells,
            "cell_inset_ratio": cell_inset_ratio,
            "status": "PAINEL VORONOI PARAMÉTRICO GERADO COM SUCESSO"
        }
