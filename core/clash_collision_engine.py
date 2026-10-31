"""
SketchBuild - Detecção de Colisão e Interferência entre Componentes (Zero DLL / Pure Python)
Frente 89: Engenharia Reversa do SketchUp - Clash Detection & Interference Analysis (BIM)

Identifica interferências geométricas e sobreposições físicas entre componentes,
grupos e sólidos (Hard Clash, Soft/Clearance Clash), calculando penetração e volume.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class CollisionClashDetectionEngine:
    """Motor de detecção de colisões e interferências geométricas entre componentes."""

    @staticmethod
    def _aabb_overlap(
        box_a: Tuple[List[float], List[float]],
        box_b: Tuple[List[float], List[float]],
        clearance_margin: float = 0.0
    ) -> Tuple[bool, float, List[float], List[float]]:
        """
        Verifica sobreposição entre dois AABBs considerando margem de tolerância.
        Retorna (tem_sobreposicao, penetracao_maxima, inter_min, inter_max).
        """
        min_a, max_a = box_a
        min_b, max_b = box_b

        inter_min = [
            max(min_a[0], min_b[0]),
            max(min_a[1], min_b[1]),
            max(min_a[2], min_b[2]),
        ]
        inter_max = [
            min(max_a[0], max_b[0]),
            min(max_a[1], max_b[1]),
            min(max_a[2], max_b[2]),
        ]

        overlap_x = (inter_max[0] - inter_min[0]) + clearance_margin
        overlap_y = (inter_max[1] - inter_min[1]) + clearance_margin
        overlap_z = (inter_max[2] - inter_min[2]) + clearance_margin

        if overlap_x > 0 and overlap_y > 0 and overlap_z > 0:
            penetration = min(overlap_x, overlap_y, overlap_z)
            return True, penetration, inter_min, inter_max
        return False, 0.0, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]

    @staticmethod
    def detect_clashes(
        components: List[Dict[str, Any]],
        clearance_tolerance_m: float = 0.01
    ) -> Dict[str, Any]:
        """
        Analisa lista de componentes [{'id': str, 'name': str, 'bbox_min': [x,y,z], 'bbox_max': [x,y,z]}].
        Retorna pares em colisão física (HARD_CLASH) ou dentro do raio de folga (SOFT_CLASH).
        """
        clashes: List[Dict[str, Any]] = []
        n = len(components)

        for i in range(n):
            for j in range(i + 1, n):
                c1 = components[i]
                c2 = components[j]

                box_1 = (c1["bbox_min"], c1["bbox_max"])
                box_2 = (c2["bbox_min"], c2["bbox_max"])

                # Checagem de Hard Clash (interseção estrita sem margem)
                is_hard, pen_hard, i_min, i_max = CollisionClashDetectionEngine._aabb_overlap(box_1, box_2, 0.0)

                if is_hard:
                    inter_vol = (i_max[0] - i_min[0]) * (i_max[1] - i_min[1]) * (i_max[2] - i_min[2])
                    clashes.append({
                        "clash_type": "HARD_CLASH",
                        "severity": "CRITICAL",
                        "component_a_id": c1["id"],
                        "component_a_name": c1.get("name", c1["id"]),
                        "component_b_id": c2["id"],
                        "component_b_name": c2.get("name", c2["id"]),
                        "penetration_depth_m": round(pen_hard, 4),
                        "intersection_volume_m3": round(abs(inter_vol), 6),
                        "clash_center": [
                            round((i_min[0] + i_max[0]) / 2.0, 4),
                            round((i_min[1] + i_max[1]) / 2.0, 4),
                            round((i_min[2] + i_max[2]) / 2.0, 4),
                        ]
                    })
                elif clearance_tolerance_m > 0:
                    # Checagem de Clearance Clash (proximidade excessiva)
                    is_soft, pen_soft, s_min, s_max = CollisionClashDetectionEngine._aabb_overlap(
                        box_1, box_2, clearance_tolerance_m
                    )
                    if is_soft:
                        clashes.append({
                            "clash_type": "CLEARANCE_CLASH",
                            "severity": "WARNING",
                            "component_a_id": c1["id"],
                            "component_a_name": c1.get("name", c1["id"]),
                            "component_b_id": c2["id"],
                            "component_b_name": c2.get("name", c2["id"]),
                            "penetration_depth_m": round(pen_soft, 4),
                            "intersection_volume_m3": 0.0,
                            "clash_center": [
                                round((s_min[0] + s_max[0]) / 2.0, 4),
                                round((s_min[1] + s_max[1]) / 2.0, 4),
                                round((s_min[2] + s_max[2]) / 2.0, 4),
                            ]
                        })

        has_hard = any(c["clash_type"] == "HARD_CLASH" for c in clashes)
        status_msg = "INTERFERÊNCIAS CRÍTICAS DETECTADAS" if has_hard else (
            "AVISOS DE FOLGA DETECTADOS" if clashes else "NENHUMA INTERFERÊNCIA ENCONTRADA (CONFORME)"
        )

        return {
            "entity_type": "ClashDetectionReport",
            "components_analyzed_count": n,
            "total_clashes_count": len(clashes),
            "hard_clashes_count": sum(1 for c in clashes if c["clash_type"] == "HARD_CLASH"),
            "clearance_clashes_count": sum(1 for c in clashes if c["clash_type"] == "CLEARANCE_CLASH"),
            "clashes": clashes,
            "status": status_msg
        }
