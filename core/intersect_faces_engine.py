"""
Motor de Interseção de Faces do SketchUp (Intersect Faces with Model / Selection - Zero DLL).

Implementa a engenharia reversa da funcionalidade 'Interseccionar Faces' do SketchUp:
1. Intersect Faces with Model (Interseccionar faces com o modelo todo).
2. Intersect Faces with Selection (Interseccionar faces apenas entre as entidades selecionadas).
3. Algoritmo Analítico:
   - Para cada par de faces poligonais (trianguladas), calcula a linha de interseção
     entre os planos que as contêm (vetor n1 x n2).
   - Projeta e intersecta os segmentos de reta dentro do intervalo delimitado por ambos os triângulos.
   - Retorna os segmentos de aresta gerados (edges) para divisão de superfícies e corte de geometria (cutting lines).
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class IntersectFacesEngine:
    """Motor analítico de cálculo de interseção entre faces poligonais 3D."""

    @staticmethod
    def _dot(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    @staticmethod
    def _cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        )

    @staticmethod
    def _sub(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    @staticmethod
    def _add(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    @staticmethod
    def _scale(a: Tuple[float, float, float], s: float) -> Tuple[float, float, float]:
        return (a[0] * s, a[1] * s, a[2] * s)

    @staticmethod
    def _norm(a: Tuple[float, float, float]) -> float:
        return math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2)

    @classmethod
    def _plane_from_points(
        cls, p0: Tuple[float, float, float], p1: Tuple[float, float, float], p2: Tuple[float, float, float]
    ) -> Optional[Tuple[Tuple[float, float, float], float]]:
        v1 = cls._sub(p1, p0)
        v2 = cls._sub(p2, p0)
        n = cls._cross(v1, v2)
        l = cls._norm(n)
        if l < 1e-7:
            return None
        unit_n = (n[0] / l, n[1] / l, n[2] / l)
        d = -cls._dot(unit_n, p0)
        return (unit_n, d)

    @classmethod
    def _intersect_segment_plane(
        cls,
        p0: Tuple[float, float, float],
        p1: Tuple[float, float, float],
        normal: Tuple[float, float, float],
        d: float
    ) -> Optional[Tuple[float, float, float]]:
        """Calcula o ponto de interseção de um segmento com um plano se cruzar."""
        d0 = cls._dot(normal, p0) + d
        d1 = cls._dot(normal, p1) + d

        if abs(d0) < 1e-7 and abs(d1) < 1e-7:
            return None  # Coplanares

        if (d0 > 1e-7 and d1 > 1e-7) or (d0 < -1e-7 and d1 < -1e-7):
            return None  # Sem cruzamento

        t = d0 / (d0 - d1)
        if 0.0 <= t <= 1.0:
            return (
                p0[0] + t * (p1[0] - p0[0]),
                p0[1] + t * (p1[1] - p0[1]),
                p0[2] + t * (p1[2] - p0[2])
            )
        return None

    @classmethod
    def intersect_triangle_pair(
        cls,
        tri_a: List[Tuple[float, float, float]],
        tri_b: List[Tuple[float, float, float]]
    ) -> Optional[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
        """
        Calcula o segmento de reta resultante da interseção de dois triângulos no espaço 3D.
        """
        plane_a = cls._plane_from_points(tri_a[0], tri_a[1], tri_a[2])
        plane_b = cls._plane_from_points(tri_b[0], tri_b[1], tri_b[2])

        if not plane_a or not plane_b:
            return None

        na, da = plane_a
        nb, db = plane_b

        # Vetor diretor da linha de interseção dos dois planos
        line_dir = cls._cross(na, nb)
        if cls._norm(line_dir) < 1e-6:
            # Planos paralelos ou coincidentes
            return None

        # Coleta pontos de cruzamento das arestas de tri_a com o plano de tri_b
        pts_a_on_b = []
        for i in range(3):
            p_int = cls._intersect_segment_plane(tri_a[i], tri_a[(i + 1) % 3], nb, db)
            if p_int:
                pts_a_on_b.append(p_int)

        # Coleta pontos de cruzamento das arestas de tri_b com o plano de tri_a
        pts_b_on_a = []
        for i in range(3):
            p_int = cls._intersect_segment_plane(tri_b[i], tri_b[(i + 1) % 3], na, da)
            if p_int:
                pts_b_on_a.append(p_int)

        all_points = pts_a_on_b + pts_b_on_a
        # Remove duplicatas próximas
        unique_points = []
        for pt in all_points:
            if not any(cls._norm(cls._sub(pt, u)) < 1e-4 for u in unique_points):
                unique_points.append(pt)

        if len(unique_points) >= 2:
            # Seleciona o par com maior distância euclidiana para formar o segmento
            max_dist = -1.0
            best_pair = None
            for i in range(len(unique_points)):
                for j in range(i + 1, len(unique_points)):
                    dist = cls._norm(cls._sub(unique_points[i], unique_points[j]))
                    if dist > max_dist:
                        max_dist = dist
                        best_pair = (unique_points[i], unique_points[j])

            if best_pair and max_dist > 1e-4:
                return best_pair

        return None

    @classmethod
    def intersect_faces_sets(
        cls,
        faces_set_a: List[Dict[str, Any]],
        faces_set_b: Optional[List[Dict[str, Any]]] = None,
        context_mode: str = "WITH_MODEL"
    ) -> Dict[str, Any]:
        """
        Executa interseção entre dois conjuntos de faces ou dentro de um único conjunto.
        context_mode: 'WITH_MODEL' ou 'WITH_SELECTION'.
        """
        set_a = faces_set_a or []
        set_b = faces_set_b if faces_set_b is not None else faces_set_a

        intersection_edges: List[Dict[str, Any]] = []
        tested_pairs = 0

        # Decomposição simples em triângulos para cada face
        def _triangulate(face_dict: Dict[str, Any]) -> List[List[Tuple[float, float, float]]]:
            verts = [tuple(p) for p in face_dict.get("vertices", [])]
            if len(verts) < 3:
                return []
            tris = []
            for i in range(1, len(verts) - 1):
                tris.append([verts[0], verts[i], verts[i + 1]])
            return tris

        is_same_set = (faces_set_b is None)

        for i, fa in enumerate(set_a):
            start_j = (i + 1) if is_same_set else 0
            for j in range(start_j, len(set_b)):
                fb = set_b[j]
                tested_pairs += 1

                tris_a = _triangulate(fa)
                tris_b = _triangulate(fb)

                for ta in tris_a:
                    for tb in tris_b:
                        seg = cls.intersect_triangle_pair(ta, tb)
                        if seg:
                            p0 = [round(c, 5) for c in seg[0]]
                            p1 = [round(c, 5) for c in seg[1]]
                            intersection_edges.append({
                                "start": p0,
                                "end": p1,
                                "face_a_index": i,
                                "face_b_index": j,
                                "length_m": round(cls._norm(cls._sub(seg[0], seg[1])), 4)
                            })

        return {
            "status": "success",
            "context_mode": context_mode.upper().strip(),
            "tested_pairs_count": tested_pairs,
            "intersection_edges_count": len(intersection_edges),
            "intersection_edges": intersection_edges
        }
