"""
Calculador de Offset / Equidistância Analítica 2D e 3D em Pure Python (Zero DLL).

Implementa o algoritmo de deslocamento paralelo de arestas coplanares (Ferramenta Offset 'F' do SketchUp):
1. Projeção de loop 3D para base 2D local ortonormal.
2. Deslocamento paralelo de cada segmento por distância linear d.
3. Interseção exata entre segmentos adjacentes via determinantes analíticos.
4. Reprojeção para o espaço 3D global.
5. Geração de molduras (anéis com furo) e malhas trianguladas coplanares.
"""

import math
from typing import List, Tuple, Dict, Any, Optional


class OffsetCalculator:
    """Motor analítico de equidistância / offset de contornos poligonais."""

    @staticmethod
    def _vec_sub(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    @staticmethod
    def _vec_add(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    @staticmethod
    def _vec_scale(v: Tuple[float, float, float], s: float) -> Tuple[float, float, float]:
        return (v[0] * s, v[1] * s, v[2] * s)

    @staticmethod
    def _vec_dot(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    @staticmethod
    def _vec_cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        )

    @staticmethod
    def _vec_len(v: Tuple[float, float, float]) -> float:
        return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

    @classmethod
    def calculate_polygon_normal(cls, vertices: List[Tuple[float, float, float]]) -> Tuple[float, float, float]:
        """Calcula normal unitária via método de Newell."""
        nx = ny = nz = 0.0
        n = len(vertices)
        for i in range(n):
            c = vertices[i]
            nxt = vertices[(i + 1) % n]
            nx += (c[1] - nxt[1]) * (c[2] + nxt[2])
            ny += (c[2] - nxt[2]) * (c[0] + nxt[0])
            nz += (c[0] - nxt[0]) * (c[1] + nxt[1])
        mag = math.sqrt(nx * nx + ny * ny + nz * nz)
        if mag < 1e-9:
            return (0.0, 0.0, 1.0)
        return (nx / mag, ny / mag, nz / mag)

    @classmethod
    def offset_polygon_3d(
        cls,
        vertices: List[Tuple[float, float, float]],
        distance: float,
        inside: bool = True
    ) -> List[Tuple[float, float, float]]:
        """
        Calcula o polígono deslocado por uma distância métrica d.
        distance: valor em metros ou unidades consistentes.
        inside: True para offset para o interior do polígono, False para exterior.
        """
        n = len(vertices)
        if n < 3:
            raise ValueError("Polígono precisa ter no mínimo 3 vértices.")

        normal = cls.calculate_polygon_normal(vertices)
        p0 = vertices[0]

        # Constrói base ortonormal 2D (u, v) no plano da face
        edge0 = cls._vec_sub(vertices[1], p0)
        u_len = cls._vec_len(edge0)
        if u_len < 1e-9:
            u_axis = (1.0, 0.0, 0.0) if abs(normal[0]) < 0.9 else (0.0, 1.0, 0.0)
            u_axis = cls._vec_cross(u_axis, normal)
            u_mag = cls._vec_len(u_axis)
            u_axis = cls._vec_scale(u_axis, 1.0 / u_mag)
        else:
            u_axis = cls._vec_scale(edge0, 1.0 / u_len)

        v_axis = cls._vec_cross(normal, u_axis)

        # Projeta vértices 3D para 2D (u, v)
        pts_2d = []
        for p in vertices:
            rel = cls._vec_sub(p, p0)
            u = cls._vec_dot(rel, u_axis)
            v = cls._vec_dot(rel, v_axis)
            pts_2d.append((u, v))

        # Calcula orientação (área com sinal) para saber sentido horário / anti-horário
        signed_area = 0.0
        for i in range(n):
            x1, y1 = pts_2d[i]
            x2, y2 = pts_2d[(i + 1) % n]
            signed_area += (x1 * y2 - x2 * y1)
        is_ccw = signed_area > 0

        # Direção do offset (para o interior)
        offset_dist = distance if inside else -distance
        sign = 1.0 if is_ccw else -1.0

        # Para cada aresta 2D, calcula os coeficientes da reta deslocada A*u + B*v + C = 0
        lines = []
        for i in range(n):
            p_cur = pts_2d[i]
            p_nxt = pts_2d[(i + 1) % n]
            dx = p_nxt[0] - p_cur[0]
            dy = p_nxt[1] - p_cur[1]
            seg_len = math.sqrt(dx * dx + dy * dy)
            if seg_len < 1e-9:
                continue

            # Normal unitária perpendicular apontando para o interior
            # Normal perpendicular a (dx, dy) rotacionada 90 graus
            nx = -dy / seg_len * sign
            ny = dx / seg_len * sign

            # Ponto deslocado
            shift_x = nx * offset_dist
            shift_y = ny * offset_dist
            px = p_cur[0] + shift_x
            py = p_cur[1] + shift_y

            # Equação da reta: ny*u - nx*v + C = 0 => dx*v - dy*u + ...
            # Mais simples: A = -dy, B = dx, C = -(A*px + B*py)
            A = -dy
            B = dx
            C = -(A * px + B * py)
            lines.append((A, B, C))

        # Interseção entre retas consecutivas (Regra de Cramer)
        m = len(lines)
        offset_2d = []
        for i in range(m):
            A1, B1, C1 = lines[(i - 1 + m) % m]
            A2, B2, C2 = lines[i]

            det = A1 * B2 - A2 * B1
            if abs(det) < 1e-9:
                # Linhas paralelas, média simples
                offset_2d.append(pts_2d[i])
            else:
                ix = (B1 * C2 - B2 * C1) / det
                iy = (A2 * C1 - A1 * C2) / det
                offset_2d.append((ix, iy))

        # Reprojeção para o espaço 3D
        offset_3d = []
        for u, v in offset_2d:
            p_3d = cls._vec_add(
                p0,
                cls._vec_add(cls._vec_scale(u_axis, u), cls._vec_scale(v_axis, v))
            )
            offset_3d.append(p_3d)

        return offset_3d

    @classmethod
    def generate_frame_faces(
        cls,
        outer_loop: List[Tuple[float, float, float]],
        inner_loop: List[Tuple[float, float, float]]
    ) -> List[List[Tuple[float, float, float]]]:
        """Gera faces quadriláteras da moldura (anel) conectando o loop externo ao interno."""
        n = len(outer_loop)
        faces = []
        for i in range(n):
            i_next = (i + 1) % n
            faces.append([
                outer_loop[i],
                outer_loop[i_next],
                inner_loop[i_next],
                inner_loop[i]
            ])
        return faces
