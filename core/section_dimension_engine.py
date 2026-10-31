"""
SketchBuild - Motor de Cortes com Cota Automática de Seção (Zero DLL / Pure Python)
Frente 87: Engenharia Reversa do SketchUp - Section Dimensioning & Auto-Annotations (NBR 6492)

Gera automaticamente cotas lineares ortogonais de largura, altura total e cotas
de nível arquitetônico em cortes de planos de seção (SUSectionPlaneRef).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class SectionDimensionEngine:
    """Gera cotas ortogonais automáticas e marcas de nível sobre contornos de seção."""

    @staticmethod
    def generate_auto_section_dimensions(
        cut_loops_3d: List[List[Tuple[float, float, float]]],
        offset_m: float = 0.25,
        unit: str = "m",
        precision: int = 2
    ) -> Dict[str, Any]:
        """
        Analisa os loops resultantes de um corte de seção e sintetiza:
        1. Cota total de largura (Horizontal).
        2. Cota total de altura (Vertical).
        3. Marcas de nível arquitetônico NBR 6492 (topo e base).
        """
        if not cut_loops_3d:
            return {
                "entity_type": "SectionDimensionResult",
                "dimensions": [],
                "level_marks": [],
                "bbox_min": [0.0, 0.0, 0.0],
                "bbox_max": [0.0, 0.0, 0.0],
                "status": "NENHUM LOOP DE CORTE FORNECIDO"
            }

        all_pts: List[Tuple[float, float, float]] = []
        for loop in cut_loops_3d:
            all_pts.extend(loop)

        min_x = min(p[0] for p in all_pts)
        max_x = max(p[0] for p in all_pts)
        min_y = min(p[1] for p in all_pts)
        max_y = max(p[1] for p in all_pts)
        min_z = min(p[2] for p in all_pts)
        max_z = max(p[2] for p in all_pts)

        width_x = max_x - min_x
        length_y = max_y - min_y
        height_z = max_z - min_z

        # Determinar eixo principal horizontal mais expressivo (X ou Y)
        is_x_primary = width_x >= length_y
        span_horiz = width_x if is_x_primary else length_y

        dimensions: List[Dict[str, Any]] = []

        # 1. Cota de Largura Total (Base)
        if is_x_primary:
            start_w = (min_x, (min_y + max_y) / 2.0, min_z - offset_m)
            end_w = (max_x, (min_y + max_y) / 2.0, min_z - offset_m)
        else:
            start_w = ((min_x + max_x) / 2.0, min_y, min_z - offset_m)
            end_w = ((min_x + max_x) / 2.0, max_y, min_z - offset_m)

        dim_width = {
            "type": "HORIZONTAL_WIDTH",
            "start": list(start_w),
            "end": list(end_w),
            "distance_m": round(span_horiz, precision),
            "text": f"{span_horiz:.{precision}f} {unit}",
            "witness_lines": [
                [list(all_pts[0]), list(start_w)],
                [list(all_pts[-1]), list(end_w)]
            ]
        }
        dimensions.append(dim_width)

        # 2. Cota de Altura Total (Lateral)
        if is_x_primary:
            start_h = (max_x + offset_m, (min_y + max_y) / 2.0, min_z)
            end_h = (max_x + offset_m, (min_y + max_y) / 2.0, max_z)
        else:
            start_h = ((min_x + max_x) / 2.0, max_y + offset_m, min_z)
            end_h = ((min_x + max_x) / 2.0, max_y + offset_m, max_z)

        dim_height = {
            "type": "VERTICAL_HEIGHT",
            "start": list(start_h),
            "end": list(end_h),
            "distance_m": round(height_z, precision),
            "text": f"{height_z:.{precision}f} {unit}",
            "witness_lines": [
                [list(all_pts[0]), list(start_h)],
                [list(all_pts[-1]), list(end_h)]
            ]
        }
        dimensions.append(dim_height)

        # 3. Marcas de Nível Arquitetônico NBR 6492
        # Nível da Base
        base_sign = "±" if abs(min_z) < 1e-4 else ("+" if min_z > 0 else "")
        level_base = {
            "name": "NÍVEL BASE",
            "position": [(min_x + max_x) / 2.0, (min_y + max_y) / 2.0, min_z],
            "elevation_m": round(min_z, precision),
            "formatted_text": f"{base_sign}{min_z:.{precision}f}",
            "symbol": "LEVEL_TARGET"
        }

        # Nível do Topo / Cumeeira
        top_sign = "+" if max_z > 0 else ""
        level_top = {
            "name": "NÍVEL TOPO / CUMEEIRA",
            "position": [(min_x + max_x) / 2.0, (min_y + max_y) / 2.0, max_z],
            "elevation_m": round(max_z, precision),
            "formatted_text": f"{top_sign}{max_z:.{precision}f}",
            "symbol": "LEVEL_TARGET"
        }

        return {
            "entity_type": "SectionDimensionResult",
            "dimensions_count": len(dimensions),
            "dimensions": dimensions,
            "level_marks": [level_base, level_top],
            "bbox_min": [round(min_x, 4), round(min_y, 4), round(min_z, 4)],
            "bbox_max": [round(max_x, 4), round(max_y, 4), round(max_z, 4)],
            "span_horizontal_m": round(span_horiz, precision),
            "span_vertical_m": round(height_z, precision),
            "status": "COTAS AUTOMÁTICAS DE SEÇÃO GERADAS COM SUCESSO"
        }
