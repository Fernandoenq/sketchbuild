"""
Ferramenta de Espelhamento e Simetria 3D (Mirror / Flip Tool - Zero DLL).

Implementa operações analíticas de simetria e reflexão espacial:
1. Matriz de Reflexão de Householder (R = I - 2*n*n^T).
2. Espelhamento ao longo dos eixos ortogonais principais (X=Vermelho, Y=Verde, Z=Azul) ou plano arbitrário.
3. Inversão automática do sentido dos loops (winding order) para garantir normais externas consistentes.
4. Suporte a espelhamento com duplicação (geração de módulo simétrico no espaço).
"""

from typing import List, Tuple, Dict, Any


class MirrorTool:
    """Motor analítico de espelhamento e simetria 3D."""

    @staticmethod
    def create_mirror_matrix(
        plane_normal: Tuple[float, float, float] = (1.0, 0.0, 0.0),
        plane_point: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    ) -> List[float]:
        """
        Cria matriz 4x4 column-major de reflexão pelo plano (Householder reflection).
        plane_normal: (nx, ny, nz) unitário
        plane_point: (px, py, pz) ponto que pertence ao plano de espelho
        """
        nx, ny, nz = plane_normal
        mag = (nx**2 + ny**2 + nz**2)**0.5
        if mag < 1e-9:
            nx, ny, nz = (1.0, 0.0, 0.0)
        else:
            nx, ny, nz = nx / mag, ny / mag, nz / mag

        px, py, pz = plane_point
        # Distância d = -(n . p)
        d = -(nx * px + ny * py + nz * pz)

        # Matriz de reflexão: P' = P - 2*(n.P + d)*n
        r00 = 1.0 - 2.0 * nx * nx
        r01 = -2.0 * nx * ny
        r02 = -2.0 * nx * nz

        r10 = -2.0 * ny * nx
        r11 = 1.0 - 2.0 * ny * ny
        r12 = -2.0 * ny * nz

        r20 = -2.0 * nz * nx
        r21 = -2.0 * nz * ny
        r22 = 1.0 - 2.0 * nz * nz

        tx = -2.0 * d * nx
        ty = -2.0 * d * ny
        tz = -2.0 * d * nz

        return [
            r00, r10, r20, 0.0,  # Coluna 0
            r01, r11, r21, 0.0,  # Coluna 1
            r02, r12, r22, 0.0,  # Coluna 2
            tx,  ty,  tz,  1.0   # Coluna 3
        ]

    @classmethod
    def mirror_face_loop(
        cls,
        face_vertices: List[Tuple[float, float, float]],
        plane_normal: Tuple[float, float, float] = (1.0, 0.0, 0.0),
        plane_point: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    ) -> List[Tuple[float, float, float]]:
        """Reflete os vértices de uma face e inverte sua ordem para preservar a normal externa."""
        mat = cls.create_mirror_matrix(plane_normal, plane_point)
        mirrored_pts = []
        for x, y, z in face_vertices:
            rx = mat[0] * x + mat[4] * y + mat[8] * z + mat[12]
            ry = mat[1] * x + mat[5] * y + mat[9] * z + mat[13]
            rz = mat[2] * x + mat[6] * y + mat[10] * z + mat[14]
            mirrored_pts.append((round(rx, 6), round(ry, 6), round(rz, 6)))

        # Inverte o loop porque reflexão inverte a orientação (anti-horário vira horário)
        return list(reversed(mirrored_pts))
