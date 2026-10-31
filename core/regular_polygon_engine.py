"""
Motor da Ferramenta Polígono Regular Paramétrico do SketchUp (Polygon Tool - Zero DLL).

Implementa a engenharia reversa da ferramenta 'Polígono' do SketchUp Desktop:
(Desenho -> Formas -> Polígono / VCB: '6s', '8s', '12s')
1. Parâmetros Nativos:
   - Número de lados (sides_count): 3 (triângulo), 5 (pentágono), 6 (hexágono), 8 (octógono), etc.
   - Raio (radius_m): Distância do centro aos vértices (circunscrito) ou ao ponto médio dos lados (inscrito).
   - Modo de raio: 'CIRCUMSCRIBED' ou 'INSCRIBED'.
   - Plano e normal de desenho: Padrão horizontal Z=(0,0,1) ou qualquer plano arbitrário.
   - Ponto central da forma (center_xyz).
2. Geração da Geometria B-Rep:
   - Arestas perimetrais e face poligonal plana preenchida, subdividida em triângulos tipo leque (fan) a partir do centro.
"""

import math
from typing import List, Dict, Any, Tuple


class RegularPolygonEngine:
    """Motor analítico de polígonos regulares oficiais do SketchUp."""

    @classmethod
    def generate_regular_polygon(
        cls,
        sides_count: int = 6,
        radius_m: float = 1.0,
        radius_mode: str = "CIRCUMSCRIBED",
        center_xyz: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        normal_xyz: Tuple[float, float, float] = (0.0, 0.0, 1.0)
    ) -> Dict[str, Any]:
        """
        Gera um polígono regular paramétrico no espaço 3D.
        """
        n = max(3, sides_count)
        r = max(0.001, radius_m)

        # Se inscrito, calcula raio aos vértices: r_vertex = r / cos(pi / n)
        mode_clean = radius_mode.upper().strip()
        if mode_clean == "INSCRIBED":
            r_vertex = r / math.cos(math.pi / n)
        else:
            r_vertex = r

        # Normaliza vetor normal
        nl = math.sqrt(normal_xyz[0] ** 2 + normal_xyz[1] ** 2 + normal_xyz[2] ** 2)
        if nl < 1e-9:
            norm = (0.0, 0.0, 1.0)
        else:
            norm = (normal_xyz[0] / nl, normal_xyz[1] / nl, normal_xyz[2] / nl)

        # Base ortogonal do plano
        if abs(norm[0]) < 0.9 and abs(norm[1]) < 0.9:
            arb = (1.0, 0.0, 0.0)
        else:
            arb = (0.0, 1.0, 0.0)

        # Eixo U perpendicular à normal
        ux = arb[1] * norm[2] - arb[2] * norm[1]
        uy = arb[2] * norm[0] - arb[0] * norm[2]
        uz = arb[0] * norm[1] - arb[1] * norm[0]
        ul = math.sqrt(ux * ux + uy * uy + uz * uz)
        axis_u = (ux / ul, uy / ul, uz / ul)

        # Eixo V = norm x axis_u
        axis_v = (
            norm[1] * axis_u[2] - norm[2] * axis_u[1],
            norm[2] * axis_u[0] - norm[0] * axis_u[2],
            norm[0] * axis_u[1] - norm[1] * axis_u[0]
        )

        cx, cy, cz = center_xyz
        perimeter_vertices = []
        angle_step = 2.0 * math.pi / n

        for i in range(n):
            theta = i * angle_step
            cos_t = math.cos(theta) * r_vertex
            sin_t = math.sin(theta) * r_vertex

            vx = cx + cos_t * axis_u[0] + sin_t * axis_v[0]
            vy = cy + cos_t * axis_u[1] + sin_t * axis_v[1]
            vz = cz + cos_t * axis_u[2] + sin_t * axis_v[2]
            perimeter_vertices.append((round(vx, 4), round(vy, 4), round(vz, 4)))

        # Triangulação em leque a partir do centro
        triangles = []
        for i in range(n):
            v_curr = perimeter_vertices[i]
            v_next = perimeter_vertices[(i + 1) % n]
            triangles.append([center_xyz, v_curr, v_next])

        # Arestas perimetrais
        edges = []
        for i in range(n):
            edges.append([perimeter_vertices[i], perimeter_vertices[(i + 1) % n]])

        # Área analítica do polígono regular: 0.5 * n * r_vertex^2 * sin(2*pi / n)
        area_m2 = 0.5 * n * (r_vertex ** 2) * math.sin(2.0 * math.pi / n)
        side_length_m = 2.0 * r_vertex * math.sin(math.pi / n)

        return {
            "sides_count": n,
            "radius_m": round(r, 4),
            "radius_vertex_m": round(r_vertex, 4),
            "radius_mode": mode_clean,
            "side_length_m": round(side_length_m, 4),
            "area_m2": round(area_m2, 4),
            "perimeter_m": round(side_length_m * n, 4),
            "center": center_xyz,
            "perimeter_vertices": perimeter_vertices,
            "vertices": perimeter_vertices,
            "edges_count": len(edges),
            "triangles_count": len(triangles),
            "triangles": triangles,
            "edges": edges
        }
