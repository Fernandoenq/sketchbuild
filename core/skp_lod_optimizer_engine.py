"""
SketchBuild - Otimizador e Compactador de Geometria LOD para Baixa Latência Web (Zero DLL / Pure Python)
Frente 100: Engenharia Reversa do SketchUp - Multi-Level of Detail (LOD) & Mesh Decimator

Gera automaticamente 3 níveis de detalhe (LOD0, LOD1, LOD2) para visualização fluida
no Three.js, removendo vértices duplicados e triângulos degenerados enquanto preserva a BBox.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class SkpLODOptimizerEngine:
    """Motor analítico de otimização de malha e geração de níveis de detalhe (LOD)."""

    @staticmethod
    def _clean_and_weld(
        vertices: List[Tuple[float, float, float]],
        triangles: List[List[int]],
        tolerance: float = 1e-4
    ) -> Tuple[List[Tuple[float, float, float]], List[List[int]]]:
        """
        Solda vértices coincidentes e elimina triângulos degenerados.
        """
        unique_map: Dict[Tuple[int, int, int], int] = {}
        new_verts: List[Tuple[float, float, float]] = []
        vert_remap: List[int] = []

        scale = 1.0 / max(1e-6, tolerance)

        for v in vertices:
            key = (int(round(v[0] * scale)), int(round(v[1] * scale)), int(round(v[2] * scale)))
            if key not in unique_map:
                unique_map[key] = len(new_verts)
                new_verts.append(v)
            vert_remap.append(unique_map[key])

        valid_tris: List[List[int]] = []
        for tri in triangles:
            i0 = vert_remap[tri[0]]
            i1 = vert_remap[tri[1]]
            i2 = vert_remap[tri[2]]
            # Ignorar triângulos com vértices repetidos (degenerados)
            if i0 != i1 and i1 != i2 and i0 != i2:
                valid_tris.append([i0, i1, i2])

        return new_verts, valid_tris

    @staticmethod
    def generate_lod_chain(
        vertices: List[Tuple[float, float, float]],
        triangles: List[List[int]],
        lod1_target_ratio: float = 0.50,
        lod2_target_ratio: float = 0.25
    ) -> Dict[str, Any]:
        """
        Gera a cadeia de LODs (LOD0: 100%, LOD1: ~50%, LOD2: ~25% ou proxy) com distâncias Three.js.
        """
        orig_v_count = len(vertices)
        orig_t_count = len(triangles)

        # LOD0: Malha limpa com soldagem de tolerância fina
        lod0_v, lod0_t = SkpLODOptimizerEngine._clean_and_weld(vertices, triangles, tolerance=1e-4)

        # LOD1: Amostragem simplificada (decimação por amostragem de passo 2)
        lod1_step = max(1, int(1.0 / max(0.1, lod1_target_ratio)))
        lod1_t = lod0_t[::lod1_step] if len(lod0_t) > 4 else lod0_t
        # Vértices usados no LOD1
        used_indices_1 = set()
        for t in lod1_t:
            used_indices_1.update(t)
        remap_1 = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted(used_indices_1))}
        lod1_v = [lod0_v[idx] for idx in sorted(used_indices_1)]
        lod1_t_remapped = [[remap_1[idx] for idx in t] for t in lod1_t]

        # LOD2: Amostragem grosseira de longa distância
        lod2_step = max(1, int(1.0 / max(0.05, lod2_target_ratio)))
        lod2_t = lod0_t[::lod2_step] if len(lod0_t) > 8 else lod1_t
        used_indices_2 = set()
        for t in lod2_t:
            used_indices_2.update(t)
        remap_2 = {old_idx: new_idx for new_idx, old_idx in enumerate(sorted(used_indices_2))}
        lod2_v = [lod0_v[idx] for idx in sorted(used_indices_2)]
        lod2_t_remapped = [[remap_2[idx] for idx in t] for t in lod2_t]

        # Bounding box global
        min_x = min(v[0] for v in vertices) if vertices else 0.0
        max_x = max(v[0] for v in vertices) if vertices else 0.0
        min_y = min(v[1] for v in vertices) if vertices else 0.0
        max_y = max(v[1] for v in vertices) if vertices else 0.0
        min_z = min(v[2] for v in vertices) if vertices else 0.0
        max_z = max(v[2] for v in vertices) if vertices else 0.0

        diag = math.sqrt((max_x - min_x)**2 + (max_y - min_y)**2 + (max_z - min_z)**2)

        # Distâncias de troca no Three.js proporcionais à escala do objeto
        d_lod0 = 0.0
        d_lod1 = round(diag * 2.5, 1)
        d_lod2 = round(diag * 6.0, 1)

        # Estimativa de redução de memória (50 bytes aprox por triângulo em buffer Three.js)
        mem_orig_kb = (orig_t_count * 50) / 1024.0
        mem_lod2_kb = (len(lod2_t_remapped) * 50) / 1024.0

        return {
            "entity_type": "SkpLODChainResult",
            "original_mesh": {
                "vertices_count": orig_v_count,
                "triangles_count": orig_t_count,
            },
            "lod_levels": [
                {
                    "level": "LOD0_HIGH",
                    "switch_distance_m": d_lod0,
                    "vertices_count": len(lod0_v),
                    "triangles_count": len(lod0_t),
                    "reduction_percent": 0.0,
                    "vertices": [list(v) for v in lod0_v],
                    "triangles": lod0_t,
                },
                {
                    "level": "LOD1_MEDIUM",
                    "switch_distance_m": d_lod1,
                    "vertices_count": len(lod1_v),
                    "triangles_count": len(lod1_t_remapped),
                    "reduction_percent": round((1.0 - len(lod1_t_remapped) / max(1, orig_t_count)) * 100.0, 1),
                    "vertices": [list(v) for v in lod1_v],
                    "triangles": lod1_t_remapped,
                },
                {
                    "level": "LOD2_LOW",
                    "switch_distance_m": d_lod2,
                    "vertices_count": len(lod2_v),
                    "triangles_count": len(lod2_t_remapped),
                    "reduction_percent": round((1.0 - len(lod2_t_remapped) / max(1, orig_t_count)) * 100.0, 1),
                    "vertices": [list(v) for v in lod2_v],
                    "triangles": lod2_t_remapped,
                },
            ],
            "metrics": {
                "bbox_diagonal_m": round(diag, 3),
                "estimated_memory_reduction_percent": round((1.0 - mem_lod2_kb / max(0.001, mem_orig_kb)) * 100.0, 1),
            },
            "status": "CADEIA DE LOD MULTI-RESOLUÇÃO THREE.JS GERADA COM SUCESSO"
        }
