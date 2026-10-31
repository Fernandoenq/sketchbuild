"""
Motor do Inspetor de Informações da Entidade do SketchUp (Entity Info Inspector - Zero DLL).

Implementa a engenharia reversa do painel 'Informações da Entidade' (Entity Info) do SketchUp:
1. Análise Polimórfica por Tipo de Entidade:
   - Aresta / Linha (Edge): Comprimento exato em metros/cm/mm, estado Suave (Smooth), Suave Oculta (Soft) e Oculta (Hidden).
   - Arco / Curva (Arc / Curve): Raio de curvatura, comprimento do arco e quantidade de segmentos poligonais.
   - Face: Área de superfície tridimensional exata (m²), materiais aplicados na face frontal e traseira, vetor normal do plano.
   - Grupo / Componente (Solid Inspector): Detecção analítica de sólido 2-manifold estanque (Solid Group/Component),
     cálculo exato de volume líquido (m³) pelo Teorema da Divergência e área total de casca.
2. Formatação com unidades do modelo e detecção de erros de estanqueidade (*Not a Solid*).
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class EntityMetricsInspectorEngine:
    """Motor analítico de inspeção de propriedades geométricas oficiais do SketchUp."""

    @classmethod
    def inspect_edge(
        cls,
        v1: Tuple[float, float, float],
        v2: Tuple[float, float, float],
        is_smooth: bool = False,
        is_soft: bool = False,
        is_hidden: bool = False,
        tag: str = "Layer0"
    ) -> Dict[str, Any]:
        """Inspeciona propriedades de uma aresta/linha."""
        length_m = math.sqrt((v2[0] - v1[0]) ** 2 + (v2[1] - v1[1]) ** 2 + (v2[2] - v1[2]) ** 2)

        return {
            "entity_type": "Edge",
            "length_m": round(length_m, 4),
            "length_cm": round(length_m * 100.0, 2),
            "length_mm": round(length_m * 1000.0, 1),
            "is_smooth": is_smooth,
            "is_soft": is_soft,
            "is_hidden": is_hidden,
            "tag": tag,
            "vertices": [v1, v2]
        }

    @classmethod
    def inspect_arc(
        cls,
        radius_m: float,
        num_segments: int,
        arc_angle_deg: float = 360.0,
        tag: str = "Layer0"
    ) -> Dict[str, Any]:
        """Inspeciona propriedades de um arco ou circunferência."""
        arc_rad = math.radians(min(360.0, max(0.1, arc_angle_deg)))
        arc_length_m = radius_m * arc_rad

        return {
            "entity_type": "ArcCurve",
            "radius_m": round(radius_m, 4),
            "segments_count": num_segments,
            "arc_angle_deg": round(arc_angle_deg, 2),
            "arc_length_m": round(arc_length_m, 4),
            "is_closed_circle": abs(arc_angle_deg - 360.0) < 1e-3,
            "tag": tag
        }

    @classmethod
    def inspect_face(
        cls,
        vertices: List[Tuple[float, float, float]],
        front_material: Optional[str] = None,
        back_material: Optional[str] = None,
        tag: str = "Layer0"
    ) -> Dict[str, Any]:
        """Inspeciona propriedades de uma face tridimensional."""
        if len(vertices) < 3:
            raise ValueError("Uma face requer pelo menos 3 vértices.")

        # Cálculo de área via fórmula de Newell / soma baricêntrica
        area = 0.0
        v0 = vertices[0]
        normal = [0.0, 0.0, 0.0]

        for i in range(1, len(vertices) - 1):
            v1 = vertices[i]
            v2 = vertices[i + 1]
            ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
            bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]

            cx = ay * bz - az * by
            cy = az * bx - ax * bz
            cz = ax * by - ay * bx

            normal[0] += cx
            normal[1] += cy
            normal[2] += cz

        norm_len = math.sqrt(normal[0] ** 2 + normal[1] ** 2 + normal[2] ** 2)
        area_m2 = norm_len / 2.0
        unit_normal = (
            round(normal[0] / norm_len, 4) if norm_len > 1e-9 else 0.0,
            round(normal[1] / norm_len, 4) if norm_len > 1e-9 else 0.0,
            round(normal[2] / norm_len, 4) if norm_len > 1e-9 else 1.0,
        )

        return {
            "entity_type": "Face",
            "area_m2": round(area_m2, 4),
            "area_cm2": round(area_m2 * 10000.0, 2),
            "vertices_count": len(vertices),
            "normal": unit_normal,
            "front_material": front_material or "Padrão",
            "back_material": back_material or "Padrão",
            "tag": tag
        }

    @classmethod
    def inspect_solid_component(
        cls,
        definition_name: str,
        instance_name: str,
        triangles: List[List[Tuple[float, float, float]]],
        tag: str = "Layer0",
        dynamic_attributes: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Inspeciona um grupo ou componente, verificando se é um Sólido 2-Manifold estanque
        e calculando volume líquido exato e área de superfície total.
        """
        if not triangles:
            return {
                "entity_type": "ComponentInstance",
                "definition_name": definition_name,
                "instance_name": instance_name,
                "is_solid": False,
                "solid_status": "Não é um sólido (Vazio)",
                "volume_m3": None,
                "total_area_m2": 0.0,
                "tag": tag
            }

        # 1. Verificação de 2-manifold estanque (cada aresta compartilhada por exatamente 2 faces)
        edge_count: Dict[Tuple[Tuple[float, float, float], Tuple[float, float, float]], int] = {}
        total_area = 0.0
        volume_m3 = 0.0

        for tri in triangles:
            p0, p1, p2 = tri[0], tri[1], tri[2]

            # Área do triângulo
            ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
            bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]
            cx = ay * bz - az * by
            cy = az * bx - ax * bz
            cz = ax * by - ay * bx
            total_area += math.sqrt(cx * cx + cy * cy + cz * cz) / 2.0

            # Teorema da Divergência para volume de poliedro fechado: det(p0, p1, p2) / 6.0
            det = (
                p0[0] * (p1[1] * p2[2] - p1[2] * p2[1]) -
                p0[1] * (p1[0] * p2[2] - p1[2] * p2[0]) +
                p0[2] * (p1[0] * p2[1] - p1[1] * p2[0])
            )
            volume_m3 += det / 6.0

            # Contagem de arestas ordenadas (convertendo cada vértice para tupla imutável)
            for edge in [(p0, p1), (p1, p2), (p2, p0)]:
                sorted_edge = tuple(tuple(p) for p in sorted(edge, key=lambda p: (p[0], p[1], p[2])))
                edge_count[sorted_edge] = edge_count.get(sorted_edge, 0) + 1

        is_watertight = all(count == 2 for count in edge_count.values())
        final_volume = abs(volume_m3) if is_watertight else None

        return {
            "entity_type": "ComponentInstance",
            "definition_name": definition_name,
            "instance_name": instance_name or "(Sem nome de instância)",
            "is_solid": is_watertight,
            "solid_status": "Sólido (Solid Component)" if is_watertight else "Não é um sólido",
            "volume_m3": round(final_volume, 4) if final_volume is not None else None,
            "total_area_m2": round(total_area, 4),
            "faces_count": len(triangles),
            "unique_edges_count": len(edge_count),
            "tag": tag,
            "dynamic_attributes_count": len(dynamic_attributes or {})
        }
