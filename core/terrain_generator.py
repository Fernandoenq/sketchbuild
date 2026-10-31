"""
Gerador de Terrenos Paramétricos e Malha Topográfica Sandbox (Zero DLL).

Implementa ferramentas clássicas de Sandbox / Topografia do SketchUp:
1. Geração de grid topográfico 3D (TIN - Triangulated Irregular Network).
2. Cálculo de desníveis, relevos e declividades do terreno.
3. Estimativa analítica de terraplenagem (volume de corte e aterro em m3).
4. Injeção direta de faces de terreno na sessão binária .SKP e Three.js.
"""

import math
from typing import List, Tuple, Dict, Any


class TerrainGenerator:
    """Motor paramétrico de geração de terrenos e topografia 3D."""

    @classmethod
    def generate_grid_terrain(
        cls,
        width_m: float = 10.0,
        length_m: float = 10.0,
        grid_resolution_m: float = 1.0,
        slope_x_pct: float = 0.0,   # Declividade em X (%)
        slope_y_pct: float = 5.0,   # Declividade em Y (%)
        base_elevation_m: float = 0.0
    ) -> Dict[str, Any]:
        """Gera malha topográfica 3D em grid retangular triangulado."""
        nx = max(2, int(width_m / grid_resolution_m) + 1)
        ny = max(2, int(length_m / grid_resolution_m) + 1)

        dx = width_m / (nx - 1)
        dy = length_m / (ny - 1)

        # 1. Gera vértices 3D
        vertices_grid = []
        for j in range(ny):
            row = []
            y = j * dy
            for i in range(nx):
                x = i * dx
                # Elevação baseada na declividade percentual
                z = base_elevation_m + (x * (slope_x_pct / 100.0)) + (y * (slope_y_pct / 100.0))
                row.append((round(x, 4), round(y, 4), round(z, 4)))
            vertices_grid.append(row)

        # 2. Gera faces triangulares da malha TIN
        faces = []
        triangles_indices = []
        for j in range(ny - 1):
            for i in range(nx - 1):
                p00 = vertices_grid[j][i]
                p10 = vertices_grid[j][i + 1]
                p11 = vertices_grid[j + 1][i + 1]
                p01 = vertices_grid[j + 1][i]

                # Triângulo 1 (inferior)
                faces.append([p00, p10, p11])
                # Triângulo 2 (superior)
                faces.append([p00, p11, p01])

        # 3. Cálculo de terraplenagem em relação à cota média
        all_z = [p[2] for row in vertices_grid for p in row]
        mean_z = sum(all_z) / len(all_z)
        cell_area = dx * dy

        vol_cut = sum(max(0.0, z - mean_z) * (cell_area / (nx * ny)) for z in all_z)
        vol_fill = sum(max(0.0, mean_z - z) * (cell_area / (nx * ny)) for z in all_z)

        return {
            "entity_type": "TerrainMesh",
            "dimensions_m": [width_m, length_m],
            "grid_size": [nx, ny],
            "vertex_count": nx * ny,
            "triangle_count": len(faces),
            "faces": faces,
            "mean_elevation_m": round(mean_z, 3),
            "max_elevation_m": round(max(all_z), 3),
            "min_elevation_m": round(min(all_z), 3),
            "earthwork_cut_m3": round(vol_cut, 3),
            "earthwork_fill_m3": round(vol_fill, 3),
        }
