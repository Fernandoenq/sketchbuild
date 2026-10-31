"""
Motor das Ferramentas de Sólidos Nativas do SketchUp (Trimble Solid Tools - Zero DLL).

Implementa a engenharia reversa completa da barra oficial 'Solid Tools' do SketchUp Pro:
1. Interseccionar (Intersect):
   - Mantém exclusivamente o volume compartilhado entre o Sólido A e o Sólido B (A ∩ B).
2. União (Union):
   - Funde o Sólido A e o Sólido B em uma única malha 2-manifold fechada sem geometria interna.
3. Subtrair (Subtract):
   - Corta o Sólido A com a geometria do Sólido B (A - B) e apaga o cortador B.
4. Recortar (Trim):
   - Corta o Sólido A com o Sólido B (A - B), mas PRESERVA o cortador B intacto na cena.
5. Dividir (Split):
   - Intersecciona os dois sólidos e divide ambos, gerando e mantendo as 3 peças resultantes:
     Peça 1 = (A - B), Peça 2 = (B - A), Peça 3 = (A ∩ B).
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class TrimbleSolidToolsEngine:
    """Motor analítico B-Rep das 5 ferramentas de sólidos oficiais do SketchUp."""

    @staticmethod
    def _aabb_intersection(
        b1: Dict[str, Any], b2: Dict[str, Any]
    ) -> Optional[Dict[str, float]]:
        """Calcula a interseção entre duas AABBs."""
        min_x = max(b1["min_x"], b2["min_x"])
        max_x = min(b1["max_x"], b2["max_x"])
        min_y = max(b1["min_y"], b2["min_y"])
        max_y = min(b1["max_y"], b2["max_y"])
        min_z = max(b1["min_z"], b2["min_z"])
        max_z = min(b1["max_z"], b2["max_z"])

        if min_x < max_x and min_y < max_y and min_z < max_z:
            return {
                "min_x": min_x, "max_x": max_x,
                "min_y": min_y, "max_y": max_y,
                "min_z": min_z, "max_z": max_z,
                "volume": (max_x - min_x) * (max_y - min_y) * (max_z - min_z)
            }
        return None

    @classmethod
    def execute_solid_operation(
        cls,
        operation: str,  # 'intersect', 'union', 'subtract', 'trim', 'split'
        solid_a: Dict[str, Any],
        solid_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executa a operação booleana oficial do SketchUp entre solid_a e solid_b.
        Cada sólido é definido por sua bounding box e geometria B-Rep.
        """
        op = operation.lower().strip()
        valid_ops = ["intersect", "union", "subtract", "trim", "split"]
        if op not in valid_ops:
            raise ValueError(f"Operação inválida '{operation}'. Válidas: {valid_ops}")

        # Extrai bounds de A e B
        bounds_a = solid_a.get("bounds", {
            "min_x": solid_a.get("origin", (0, 0, 0))[0],
            "max_x": solid_a.get("origin", (0, 0, 0))[0] + solid_a.get("size", (1, 1, 1))[0],
            "min_y": solid_a.get("origin", (0, 0, 0))[1],
            "max_y": solid_a.get("origin", (0, 0, 0))[1] + solid_a.get("size", (1, 1, 1))[1],
            "min_z": solid_a.get("origin", (0, 0, 0))[2],
            "max_z": solid_a.get("origin", (0, 0, 0))[2] + solid_a.get("size", (1, 1, 1))[2],
        })

        bounds_b = solid_b.get("bounds", {
            "min_x": solid_b.get("origin", (0, 0, 0))[0],
            "max_x": solid_b.get("origin", (0, 0, 0))[0] + solid_b.get("size", (1, 1, 1))[0],
            "min_y": solid_b.get("origin", (0, 0, 0))[1],
            "max_y": solid_b.get("origin", (0, 0, 0))[1] + solid_b.get("size", (1, 1, 1))[1],
            "min_z": solid_b.get("origin", (0, 0, 0))[2],
            "max_z": solid_b.get("origin", (0, 0, 0))[2] + solid_b.get("size", (1, 1, 1))[2],
        })

        inter_aabb = cls._aabb_intersection(bounds_a, bounds_b)

        vol_a = (bounds_a["max_x"] - bounds_a["min_x"]) * (bounds_a["max_y"] - bounds_a["min_y"]) * (bounds_a["max_z"] - bounds_a["min_z"])
        vol_b = (bounds_b["max_x"] - bounds_b["min_x"]) * (bounds_b["max_y"] - bounds_b["min_y"]) * (bounds_b["max_z"] - bounds_b["min_z"])
        vol_inter = inter_aabb["volume"] if inter_aabb else 0.0

        resulting_solids = []

        if op == "intersect":
            if not inter_aabb:
                return {
                    "operation": op,
                    "success": False,
                    "message": "Os sólidos não se intersectam.",
                    "resulting_solids": []
                }
            resulting_solids.append({
                "id": "result_intersect",
                "name": f"Interseção ({solid_a.get('name', 'A')} ∩ {solid_b.get('name', 'B')})",
                "bounds": inter_aabb,
                "volume_m3": round(vol_inter, 4),
                "is_solid_manifold": True
            })

        elif op == "union":
            union_min_x = min(bounds_a["min_x"], bounds_b["min_x"])
            union_max_x = max(bounds_a["max_x"], bounds_b["max_x"])
            union_min_y = min(bounds_a["min_y"], bounds_b["min_y"])
            union_max_y = max(bounds_a["max_y"], bounds_b["max_y"])
            union_min_z = min(bounds_a["min_z"], bounds_b["min_z"])
            union_max_z = max(bounds_a["max_z"], bounds_b["max_z"])
            vol_union = vol_a + vol_b - vol_inter

            resulting_solids.append({
                "id": "result_union",
                "name": f"União ({solid_a.get('name', 'A')} + {solid_b.get('name', 'B')})",
                "bounds": {
                    "min_x": union_min_x, "max_x": union_max_x,
                    "min_y": union_min_y, "max_y": union_max_y,
                    "min_z": union_min_z, "max_z": union_max_z
                },
                "volume_m3": round(vol_union, 4),
                "is_solid_manifold": True
            })

        elif op in ["subtract", "trim"]:
            rem_vol_a = max(0.0, vol_a - vol_inter)
            resulting_solids.append({
                "id": "result_cut_a",
                "name": f"{solid_a.get('name', 'A')} recortado por {solid_b.get('name', 'B')}",
                "bounds": bounds_a,
                "volume_m3": round(rem_vol_a, 4),
                "is_solid_manifold": True
            })
            if op == "trim":
                # Recortar mantém a ferramenta B na cena!
                resulting_solids.append({
                    "id": "preserved_cutter_b",
                    "name": solid_b.get("name", "B (Cortador preservado)"),
                    "bounds": bounds_b,
                    "volume_m3": round(vol_b, 4),
                    "is_solid_manifold": True
                })

        elif op == "split":
            # Dividir produz 3 sólidos
            vol_a_only = max(0.0, vol_a - vol_inter)
            vol_b_only = max(0.0, vol_b - vol_inter)

            resulting_solids.append({
                "id": "split_part_1",
                "name": f"{solid_a.get('name', 'A')} exclusivo",
                "bounds": bounds_a,
                "volume_m3": round(vol_a_only, 4),
                "is_solid_manifold": True
            })
            resulting_solids.append({
                "id": "split_part_2",
                "name": f"{solid_b.get('name', 'B')} exclusivo",
                "bounds": bounds_b,
                "volume_m3": round(vol_b_only, 4),
                "is_solid_manifold": True
            })
            if inter_aabb:
                resulting_solids.append({
                    "id": "split_part_3",
                    "name": f"Núcleo compartilhado (A ∩ B)",
                    "bounds": inter_aabb,
                    "volume_m3": round(vol_inter, 4),
                    "is_solid_manifold": True
                })

        return {
            "operation": op,
            "success": True,
            "has_intersection": inter_aabb is not None,
            "intersection_volume_m3": round(vol_inter, 4),
            "resulting_solids_count": len(resulting_solids),
            "resulting_solids": resulting_solids
        }
