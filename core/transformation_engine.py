"""
Motor de Transformações Geométricas 3D e Ferramenta Rotacionar (Rotate Tool - Zero DLL).

Implementa rotação tridimensional em torno de eixos arbitrários (Transferidor/Protractor):
- Formulação analítica de Rodrigues para rotação em torno de qualquer normal e ponto de pivô.
- Composição de matrizes afins 4x4 column-major prontas para Three.js e Tag 0x1966 do .SKP.
- Rotação de pontos individuais, vértices de malha e matrizes de instâncias de componentes.
"""

import math
from typing import List, Tuple, Dict, Any


class TransformationEngine:
    """Motor analítico de transformações afins 4x4 e rotações com transferidor."""

    @staticmethod
    def create_rotation_matrix_around_axis(
        pivot: Tuple[float, float, float],
        axis: Tuple[float, float, float],
        angle_degrees: float
    ) -> List[float]:
        """
        Gera matriz 4x4 column-major de rotação em torno de um eixo e pivô arbitrários.
        pivot: (cx, cy, cz)
        axis: (kx, ky, kz)
        angle_degrees: ângulo em graus (positivo = anti-horário pela regra da mão direita)
        """
        # Normaliza o vetor eixo
        kx, ky, kz = axis
        mag = math.sqrt(kx * kx + ky * ky + kz * kz)
        if mag < 1e-9:
            kx, ky, kz = (0.0, 0.0, 1.0)
        else:
            kx, ky, kz = kx / mag, ky / mag, kz / mag

        rad = math.radians(angle_degrees)
        c = math.cos(rad)
        s = math.sin(rad)
        t = 1.0 - c

        # Matriz de rotação 3x3 de Rodrigues
        r00 = t * kx * kx + c
        r01 = t * kx * ky - s * kz
        r02 = t * kx * kz + s * ky

        r10 = t * kx * ky + s * kz
        r11 = t * ky * ky + c
        r12 = t * ky * kz - s * kx

        r20 = t * kx * kz - s * ky
        r21 = t * ky * kz + s * kx
        r22 = t * kz * kz + c

        # Translação para aplicar o pivô: T(pivot) * R * T(-pivot)
        px, py, pz = pivot
        tx = px - (r00 * px + r01 * py + r02 * pz)
        ty = py - (r10 * px + r11 * py + r12 * pz)
        tz = pz - (r20 * px + r21 * py + r22 * pz)

        # Matriz 4x4 column-major (Three.js e SketchUp format)
        # [ m0, m1, m2, m3,  m4, m5, m6, m7,  m8, m9, m10, m11,  m12, m13, m14, m15 ]
        return [
            r00, r10, r20, 0.0,  # Coluna 0
            r01, r11, r21, 0.0,  # Coluna 1
            r02, r12, r22, 0.0,  # Coluna 2
            tx,  ty,  tz,  1.0   # Coluna 3 (Translação)
        ]

    @classmethod
    def rotate_point(
        cls,
        point: Tuple[float, float, float],
        pivot: Tuple[float, float, float],
        axis: Tuple[float, float, float],
        angle_degrees: float
    ) -> Tuple[float, float, float]:
        """Aplica rotação analítica a um ponto 3D individual."""
        mat = cls.create_rotation_matrix_around_axis(pivot, axis, angle_degrees)
        x, y, z = point
        # Multiplicação coluna: P' = Mat * [x, y, z, 1]^T
        rx = mat[0] * x + mat[4] * y + mat[8] * z + mat[12]
        ry = mat[1] * x + mat[5] * y + mat[9] * z + mat[13]
        rz = mat[2] * x + mat[6] * y + mat[10] * z + mat[14]
        return (round(rx, 6), round(ry, 6), round(rz, 6))

    @classmethod
    def multiply_matrices_4x4(cls, a: List[float], b: List[float]) -> List[float]:
        """Multiplica duas matrizes 4x4 em formato column-major: C = A * B."""
        result = [0.0] * 16
        for col in range(4):
            for row in range(4):
                val = 0.0
                for k in range(4):
                    val += a[k * 4 + row] * b[col * 4 + k]
                result[col * 4 + row] = val
        return result
