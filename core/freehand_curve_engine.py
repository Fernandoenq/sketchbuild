"""
Motor da Ferramenta Mão Livre do SketchUp (Freehand Tool - Zero DLL).

Implementa a engenharia reversa da ferramenta 'Mão Livre' do SketchUp Desktop:
(Desenho -> Linhas -> Mão Livre / Draw -> Lines -> Freehand)
1. Entrada de Traço Livre Contínuo:
   - Amostragem de sequência de pontos 3D desenhados pelo usuário.
2. Simplificação Analítica de Ramer-Douglas-Peucker (RDP):
   - Reduz ruído de amostragem de alta frequência mantendo a curvatura original.
   - Epsilon de tolerância métrica configurável (padrão: 0.02m).
3. Detecção de Fechamento de Laço e Geração de Face:
   - Se a distância entre o ponto inicial e o ponto final for menor que o limiar de fechamento,
     solda as pontas formando um laço fechado (Closed Loop) e sintetiza uma face plana automaticamente.
4. Soldagem de Arestas em Entidade Curva (Curve):
   - Converte os segmentos em uma polilinha contínua única.
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class FreehandCurveEngine:
    """Motor analítico da ferramenta de desenho à mão livre oficial do SketchUp."""

    @staticmethod
    def _point_line_distance(
        pt: Tuple[float, float, float],
        line_start: Tuple[float, float, float],
        line_end: Tuple[float, float, float]
    ) -> float:
        """Calcula a menor distância euclidiana entre um ponto e um segmento de reta 3D."""
        dx = line_end[0] - line_start[0]
        dy = line_end[1] - line_start[1]
        dz = line_end[2] - line_start[2]
        l2 = dx * dx + dy * dy + dz * dz
        if l2 < 1e-9:
            return math.sqrt((pt[0] - line_start[0]) ** 2 + (pt[1] - line_start[1]) ** 2 + (pt[2] - line_start[2]) ** 2)

        t = max(0.0, min(1.0, (
            (pt[0] - line_start[0]) * dx +
            (pt[1] - line_start[1]) * dy +
            (pt[2] - line_start[2]) * dz
        ) / l2))

        proj_x = line_start[0] + t * dx
        proj_y = line_start[1] + t * dy
        proj_z = line_start[2] + t * dz

        return math.sqrt((pt[0] - proj_x) ** 2 + (pt[1] - proj_y) ** 2 + (pt[2] - proj_z) ** 2)

    @classmethod
    def ramer_douglas_peucker(
        cls,
        points: List[Tuple[float, float, float]],
        epsilon: float = 0.02
    ) -> List[Tuple[float, float, float]]:
        """Aplica o algoritmo Ramer-Douglas-Peucker recursivamente."""
        if len(points) < 3:
            return points

        dmax = 0.0
        index = 0
        start = points[0]
        end = points[-1]

        for i in range(1, len(points) - 1):
            d = cls._point_line_distance(points[i], start, end)
            if d > dmax:
                index = i
                dmax = d

        if dmax > epsilon:
            rec_results1 = cls.ramer_douglas_peucker(points[:index + 1], epsilon)
            rec_results2 = cls.ramer_douglas_peucker(points[index:], epsilon)
            return rec_results1[:-1] + rec_results2
        else:
            return [start, end]

    @classmethod
    def process_freehand_curve(
        cls,
        raw_points_xyz: List[Tuple[float, float, float]],
        tolerance_m: float = 0.02,
        auto_close: bool = False,
        close_threshold_m: float = 0.10
    ) -> Dict[str, Any]:
        """Alias para process_freehand_stroke com suporte a auto_close."""
        thresh = close_threshold_m if auto_close else 0.0
        res = cls.process_freehand_stroke(
            raw_points=raw_points_xyz,
            simplification_tolerance_m=tolerance_m,
            close_loop_threshold_m=thresh
        )
        # Campos de conveniência
        res["simplified_points"] = res.get("curve_points", [])
        res["is_closed"] = res.get("is_closed_loop", False)
        res["reduction_percent"] = res.get("reduction_percentage", 0.0)
        res["edges_count"] = max(0, len(res.get("curve_points", [])) - 1)
        if res.get("has_face_generated"):
            pts = res.get("curve_points", [])
            # Área aproximada da face plana no plano XY
            area = 0.0
            for i in range(len(pts) - 1):
                area += pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1]
            res["face"] = {
                "area_m2": round(abs(area) * 0.5, 4),
                "triangles_count": len(res.get("triangles", []))
            }
        else:
            res["face"] = None
        return res

    @classmethod
    def process_freehand_stroke(
        cls,
        raw_points: List[Tuple[float, float, float]],
        simplification_tolerance_m: float = 0.02,
        close_loop_threshold_m: float = 0.10
    ) -> Dict[str, Any]:
        """
        Processa o traço à mão livre, simplifica e detecta se gerou contorno fechado com face.
        """
        if len(raw_points) < 2:
            raise ValueError("O traço à mão livre requer no mínimo 2 pontos.")

        # 1. Simplificação RDP
        simplified = cls.ramer_douglas_peucker(raw_points, simplification_tolerance_m)

        # 2. Comprimento da curva
        total_length = 0.0
        for i in range(len(simplified) - 1):
            p1 = simplified[i]
            p2 = simplified[i + 1]
            total_length += math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2 + (p2[2] - p1[2]) ** 2)

        # 3. Teste de laço fechado
        p_start = simplified[0]
        p_end = simplified[-1]
        dist_closure = math.sqrt((p_end[0] - p_start[0]) ** 2 + (p_end[1] - p_start[1]) ** 2 + (p_end[2] - p_start[2]) ** 2)

        is_closed = dist_closure <= close_loop_threshold_m and len(simplified) >= 4
        triangles = []

        if is_closed:
            # Solda o último vértice exatamente no primeiro
            simplified[-1] = p_start

            # Triangulação fan do polígono fechado para gerar face
            # Centroide dos pontos
            n = len(simplified) - 1
            cx = sum(p[0] for p in simplified[:-1]) / n
            cy = sum(p[1] for p in simplified[:-1]) / n
            cz = sum(p[2] for p in simplified[:-1]) / n
            centroid = (round(cx, 4), round(cy, 4), round(cz, 4))

            for i in range(n):
                v_curr = simplified[i]
                v_next = simplified[i + 1]
                triangles.append([centroid, v_curr, v_next])

        return {
            "raw_points_count": len(raw_points),
            "simplified_points_count": len(simplified),
            "reduction_percentage": round((1.0 - len(simplified) / len(raw_points)) * 100.0, 1),
            "total_length_m": round(total_length, 4),
            "is_closed_loop": is_closed,
            "has_face_generated": is_closed,
            "curve_points": [(round(p[0], 4), round(p[1], 4), round(p[2], 4)) for p in simplified],
            "triangles": triangles
        }
