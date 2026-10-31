"""
Motor Completo da Caixa de Areia Nativa do SketchUp (Sandbox Tools - Zero DLL).

Implementa a engenharia reversa das 4 ferramentas fundamentais de Sandbox do SketchUp:
1. Modelar (Smoove):
   - Deformação orgânica de relevo com raio de influência e decaimento cossenoidal suave:
     f(d) = 0.5 * (1 + cos(pi * d / R)) para d <= R.
2. Estampar (Stamp):
   - Rebaixa ou eleva um platô no terreno a partir da pegada de uma edificação (footprint),
     gerando uma saia de transição de talude (skirt offset).
3. Projetar (Drape):
   - Projeta caminhos 2D, ruas e divisas ortogonalmente sobre a malha de relevo 3D (TIN),
     interpolando a altitude Z exata nas faces triangulares.
4. Virar Aresta (Flip Edge):
   - Inverte a aresta diagonal compartilhada entre dois triângulos coplanares/adjacentes
     para retificar o escoamento ou cumes de terreno.
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class SandboxToolsEngine:
    """Motor analítico das ferramentas de Caixa de Areia (Sandbox) do SketchUp."""

    @classmethod
    def smoove(
        cls,
        vertices: List[Tuple[float, float, float]],
        center_x: float,
        center_y: float,
        radius_m: float,
        offset_z_m: float
    ) -> Dict[str, Any]:
        """
        Executa a ferramenta 'Modelar' (Smoove) do SketchUp.
        Aplica decaimento suave cossenoidal nos vértices dentro do raio de influência.
        """
        if radius_m <= 0.0:
            raise ValueError("O raio de influência deve ser maior que zero.")

        modified_vertices = []
        affected_count = 0

        for vx, vy, vz in vertices:
            dist = math.sqrt((vx - center_x) ** 2 + (vy - center_y) ** 2)
            if dist <= radius_m:
                # Função de peso cossenoidal suave (0 no limite, 1 no centro)
                weight = 0.5 * (1.0 + math.cos(math.pi * (dist / radius_m)))
                new_z = vz + (offset_z_m * weight)
                affected_count += 1
                modified_vertices.append((round(vx, 4), round(vy, 4), round(new_z, 4)))
            else:
                modified_vertices.append((round(vx, 4), round(vy, 4), round(vz, 4)))

        return {
            "center": (round(center_x, 4), round(center_y, 4)),
            "radius_m": round(radius_m, 3),
            "offset_z_m": round(offset_z_m, 3),
            "total_vertices": len(vertices),
            "affected_vertices_count": affected_count,
            "vertices": modified_vertices
        }

    @classmethod
    def stamp(
        cls,
        vertices: List[Tuple[float, float, float]],
        footprint_poly: List[Tuple[float, float]],
        plateau_elevation_z: float,
        skirt_offset_m: float = 1.0
    ) -> Dict[str, Any]:
        """
        Executa a ferramenta 'Estampar' (Stamp) do SketchUp.
        Cria um platô nivelado e um talude suave de transição (saia).
        """
        if skirt_offset_m < 0.0:
            raise ValueError("A distância de saia/offset deve ser não-negativa.")

        def point_in_poly(px: float, py: float, poly: List[Tuple[float, float]]) -> bool:
            inside = False
            n = len(poly)
            for i in range(n):
                x1, y1 = poly[i]
                x2, y2 = poly[(i + 1) % n]
                if ((y1 > py) != (y2 > py)) and (px < (x2 - x1) * (py - y1) / (y2 - y1 + 1e-12) + x1):
                    inside = not inside
            return inside

        def dist_to_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> float:
            dx = x2 - x1
            dy = y2 - y1
            l2 = dx * dx + dy * dy
            if l2 < 1e-12:
                return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)
            t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / l2))
            proj_x = x1 + t * dx
            proj_y = y1 + t * dy
            return math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)

        def min_dist_to_poly_boundary(px: float, py: float, poly: List[Tuple[float, float]]) -> float:
            min_d = float('inf')
            n = len(poly)
            for i in range(n):
                d = dist_to_segment(px, py, poly[i][0], poly[i][1], poly[(i + 1) % n][0], poly[(i + 1) % n][1])
                if d < min_d:
                    min_d = d
            return min_d

        modified_vertices = []
        plateau_count = 0
        skirt_count = 0

        for vx, vy, vz in vertices:
            if point_in_poly(vx, vy, footprint_poly):
                # Vértice interno ao platô
                modified_vertices.append((round(vx, 4), round(vy, 4), round(plateau_elevation_z, 4)))
                plateau_count += 1
            else:
                dist_boundary = min_dist_to_poly_boundary(vx, vy, footprint_poly)
                if dist_boundary <= skirt_offset_m and skirt_offset_m > 0:
                    # Vértice na saia de talude: interpolação linear
                    t = dist_boundary / skirt_offset_m
                    new_z = (1.0 - t) * plateau_elevation_z + t * vz
                    modified_vertices.append((round(vx, 4), round(vy, 4), round(new_z, 4)))
                    skirt_count += 1
                else:
                    modified_vertices.append((round(vx, 4), round(vy, 4), round(vz, 4)))

        return {
            "plateau_elevation_z": round(plateau_elevation_z, 3),
            "skirt_offset_m": round(skirt_offset_m, 3),
            "plateau_vertices_count": plateau_count,
            "skirt_vertices_count": skirt_count,
            "vertices": modified_vertices
        }

    @classmethod
    def drape(
        cls,
        path_points_2d: List[Tuple[float, float]],
        triangles: List[List[Tuple[float, float, float]]]
    ) -> Dict[str, Any]:
        """
        Executa a ferramenta 'Projetar' (Drape) do SketchUp.
        Projeta uma curva ou caminho 2D verticalmente sobre as faces do terreno 3D.
        """
        if not path_points_2d:
            raise ValueError("O caminho 2D para projeção não pode estar vazio.")

        def point_in_triangle_2d(px: float, py: float, p0: Tuple[float, float, float], p1: Tuple[float, float, float], p2: Tuple[float, float, float]):
            # Coordenadas baricêntricas
            area = 0.5 * (-p1[1] * p2[0] + p0[1] * (-p1[0] + p2[0]) + p0[0] * (p1[1] - p2[1]) + p1[0] * p2[1])
            if abs(area) < 1e-9:
                return False, 0, 0, 0
            s = 1.0 / (2.0 * area) * (p0[1] * p2[0] - p0[0] * p2[1] + (p2[1] - p0[1]) * px + (p0[0] - p2[0]) * py)
            t = 1.0 / (2.0 * area) * (p0[0] * p1[1] - p0[1] * p1[0] + (p0[1] - p1[1]) * px + (p1[0] - p0[0]) * py)
            u = 1.0 - s - t
            return (s >= -1e-4 and t >= -1e-4 and u >= -1e-4), u, s, t

        draped_path_3d = []
        for px, py in path_points_2d:
            projected_z = 0.0
            found = False
            for tri in triangles:
                inside, w0, w1, w2 = point_in_triangle_2d(px, py, tri[0], tri[1], tri[2])
                if inside:
                    projected_z = w0 * tri[0][2] + w1 * tri[1][2] + w2 * tri[2][2]
                    found = True
                    break
            if not found and triangles:
                # Fallback para o primeiro triângulo mais próximo
                projected_z = triangles[0][0][2]
            draped_path_3d.append((round(px, 4), round(py, 4), round(projected_z, 4)))

        # Calcula comprimento 3D total do caminho sobre o terreno
        total_length_m = 0.0
        for i in range(len(draped_path_3d) - 1):
            p1 = draped_path_3d[i]
            p2 = draped_path_3d[i + 1]
            total_length_m += math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)

        return {
            "path_points_count": len(path_points_2d),
            "draped_points_count": len(draped_path_3d),
            "total_3d_length_m": round(total_length_m, 3),
            "draped_path_3d": draped_path_3d
        }

    @classmethod
    def flip_edge(
        cls,
        tri_a: List[Tuple[float, float, float]],
        tri_b: List[Tuple[float, float, float]]
    ) -> Dict[str, Any]:
        """
        Executa a ferramenta 'Virar Aresta' (Flip Edge) do SketchUp.
        Troca a diagonal compartilhada entre dois triângulos coplanares/adjacentes.
        """
        # Identifica os vértices compartilhados
        shared = []
        unique_a = None
        unique_b = None

        for pt in tri_a:
            if pt in tri_b:
                shared.append(pt)
            else:
                unique_a = pt

        for pt in tri_b:
            if pt not in shared:
                unique_b = pt

        if len(shared) != 2 or unique_a is None or unique_b is None:
            raise ValueError("Os triângulos fornecidos não compartilham exatamente uma aresta (2 vértices).")

        # Inverte a diagonal: em vez de conectar shared[0]-shared[1], conecta unique_a-unique_b
        new_tri_1 = [unique_a, shared[0], unique_b]
        new_tri_2 = [unique_a, unique_b, shared[1]]

        return {
            "success": True,
            "old_shared_edge": [shared[0], shared[1]],
            "new_shared_edge": [unique_a, unique_b],
            "flipped_triangles": [new_tri_1, new_tri_2]
        }
