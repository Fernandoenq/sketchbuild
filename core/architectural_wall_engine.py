"""
SketchBuild - Paredes Arquitetônicas com Aberturas Automáticas de Vãos (Zero DLL / Pure Python)
Frente 96: Engenharia Reversa do SketchUp - Architectural Walls & Window/Door Openings

Gera paredes paramétricas 3D (altura, espessura) ao longo de eixos e recorta automaticamente
vãos de portas e janelas (peitoril, verga/lintel e ombreiras) gerando sólidos B-Rep estanques.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class ArchitecturalWallWindowEngine:
    """Motor de modelagem paramétrica de paredes arquitetônicas e vãos automáticos."""

    @staticmethod
    def _vec_sub(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    @staticmethod
    def _normalize_2d(vx: float, vy: float) -> Tuple[float, float]:
        mag = math.sqrt(vx**2 + vy**2)
        if mag < 1e-9:
            return (1.0, 0.0)
        return (vx / mag, vy / mag)

    @staticmethod
    def generate_wall_with_openings(
        start_pt: Tuple[float, float, float],
        end_pt: Tuple[float, float, float],
        height_m: float = 2.80,
        thickness_m: float = 0.15,
        openings: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gera parede retilínea entre start_pt e end_pt com recortes de portas e janelas.
        openings: [{'name': str, 'dist_from_start_m': float, 'width_m': float, 'sill_height_m': float, 'height_m': float}]
        """
        openings = openings or []
        dx = end_pt[0] - start_pt[0]
        dy = end_pt[1] - start_pt[1]
        wall_length = math.sqrt(dx**2 + dy**2)

        if wall_length < 0.1:
            return {
                "entity_type": "ArchitecturalWallResult",
                "wall_length_m": wall_length,
                "status": "COMPRIMENTO DE PAREDE INSUFICIENTE"
            }

        ux, uy = ArchitecturalWallWindowEngine._normalize_2d(dx, dy)
        # Normal ortogonal no plano XY (para dar espessura à parede)
        nx, ny = -uy, ux
        half_t = thickness_m / 2.0

        z_base = start_pt[2]
        z_top = z_base + height_m

        # Se não há aberturas, gera paralelepípedo sólido simples de 6 faces
        if not openings:
            # 8 vértices
            # Base inferior (-half_t e +half_t)
            v0 = [start_pt[0] - nx * half_t, start_pt[1] - ny * half_t, z_base]
            v1 = [end_pt[0] - nx * half_t, end_pt[1] - ny * half_t, z_base]
            v2 = [end_pt[0] + nx * half_t, end_pt[1] + ny * half_t, z_base]
            v3 = [start_pt[0] + nx * half_t, start_pt[1] + ny * half_t, z_base]
            # Topo superior
            v4 = [v0[0], v0[1], z_top]
            v5 = [v1[0], v1[1], z_top]
            v6 = [v2[0], v2[1], z_top]
            v7 = [v3[0], v3[1], z_top]

            verts = [v0, v1, v2, v3, v4, v5, v6, v7]
            faces = [
                [0, 3, 2, 1],  # fundo
                [4, 5, 6, 7],  # topo
                [0, 1, 5, 4],  # lado esquerdo
                [1, 2, 6, 5],  # topo final
                [2, 3, 7, 6],  # lado direito
                [3, 0, 4, 7],  # inicio inicial
            ]
            triangles = []
            for q in faces:
                triangles.append([q[0], q[1], q[2]])
                triangles.append([q[0], q[2], q[3]])

            return {
                "entity_type": "ArchitecturalWallResult",
                "wall_length_m": round(wall_length, 3),
                "height_m": height_m,
                "thickness_m": thickness_m,
                "openings_count": 0,
                "vertices_count": len(verts),
                "faces_count": len(faces),
                "triangles_count": len(triangles),
                "vertices": verts,
                "faces": faces,
                "triangles": triangles,
                "net_volume_m3": round(wall_length * height_m * thickness_m, 4),
                "status": "PAREDE MACIÇA GERADA COM SUCESSO"
            }

        # Com aberturas: dividir a parede em sub-blocos horizontais e vergas
        # Ordenar aberturas ao longo do comprimento
        sorted_ops = sorted(openings, key=lambda o: float(o.get("dist_from_start_m", 0.0)))
        blocks: List[Dict[str, Any]] = []

        curr_x = 0.0
        total_void_volume = 0.0

        for op in sorted_ops:
            op_dist = float(op.get("dist_from_start_m", 0.0))
            op_width = float(op.get("width_m", 0.9))
            op_sill = float(op.get("sill_height_m", 0.0))  # 0.0 para porta, 1.0 para janela
            op_h = float(op.get("height_m", 2.1))

            # 1. Bloco sólido antes da abertura
            if op_dist > curr_x:
                blocks.append({
                    "start_x": curr_x,
                    "end_x": op_dist,
                    "z_min": z_base,
                    "z_max": z_top
                })

            # 2. Peitoril sob a janela (se houver sill > 0)
            if op_sill > 0.01:
                blocks.append({
                    "start_x": op_dist,
                    "end_x": op_dist + op_width,
                    "z_min": z_base,
                    "z_max": z_base + op_sill
                })

            # 3. Verga (lintel) acima da abertura até o topo da parede
            top_open = z_base + op_sill + op_h
            if top_open < z_top - 0.01:
                blocks.append({
                    "start_x": op_dist,
                    "end_x": op_dist + op_width,
                    "z_min": top_open,
                    "z_max": z_top
                })

            total_void_volume += op_width * op_h * thickness_m
            curr_x = op_dist + op_width

        # Bloco sólido final restante
        if curr_x < wall_length:
            blocks.append({
                "start_x": curr_x,
                "end_x": wall_length,
                "z_min": z_base,
                "z_max": z_top
            })

        # Construir geometria combinada para todos os blocos
        all_verts: List[List[float]] = []
        all_faces: List[List[int]] = []
        all_triangles: List[List[int]] = []

        def get_pt(dist_along: float, side_factor: float, z: float) -> List[float]:
            px = start_pt[0] + ux * dist_along + nx * (half_t * side_factor)
            py = start_pt[1] + uy * dist_along + ny * (half_t * side_factor)
            return [round(px, 5), round(py, 5), round(z, 5)]

        for b in blocks:
            b_start = b["start_x"]
            b_end = b["end_x"]
            bz0 = b["z_min"]
            bz1 = b["z_max"]

            base_idx = len(all_verts)
            v0 = get_pt(b_start, -1.0, bz0)
            v1 = get_pt(b_end, -1.0, bz0)
            v2 = get_pt(b_end, 1.0, bz0)
            v3 = get_pt(b_start, 1.0, bz0)
            v4 = get_pt(b_start, -1.0, bz1)
            v5 = get_pt(b_end, -1.0, bz1)
            v6 = get_pt(b_end, 1.0, bz1)
            v7 = get_pt(b_start, 1.0, bz1)

            all_verts.extend([v0, v1, v2, v3, v4, v5, v6, v7])

            # 6 faces do bloco
            b_faces = [
                [base_idx + 0, base_idx + 3, base_idx + 2, base_idx + 1],
                [base_idx + 4, base_idx + 5, base_idx + 6, base_idx + 7],
                [base_idx + 0, base_idx + 1, base_idx + 5, base_idx + 4],
                [base_idx + 1, base_idx + 2, base_idx + 6, base_idx + 5],
                [base_idx + 2, base_idx + 3, base_idx + 7, base_idx + 6],
                [base_idx + 3, base_idx + 0, base_idx + 4, base_idx + 7],
            ]
            all_faces.extend(b_faces)
            for q in b_faces:
                all_triangles.append([q[0], q[1], q[2]])
                all_triangles.append([q[0], q[2], q[3]])

        gross_vol = wall_length * height_m * thickness_m
        net_vol = max(0.0, gross_vol - total_void_volume)

        return {
            "entity_type": "ArchitecturalWallResult",
            "wall_length_m": round(wall_length, 3),
            "height_m": height_m,
            "thickness_m": thickness_m,
            "openings_count": len(openings),
            "blocks_count": len(blocks),
            "vertices_count": len(all_verts),
            "faces_count": len(all_faces),
            "triangles_count": len(all_triangles),
            "vertices": all_verts,
            "faces": all_faces,
            "triangles": all_triangles,
            "gross_volume_m3": round(gross_vol, 4),
            "void_volume_m3": round(total_void_volume, 4),
            "net_volume_m3": round(net_vol, 4),
            "status": "PAREDE COM VÃOS PARAMÉTRICOS GERADA COM SUCESSO"
        }
