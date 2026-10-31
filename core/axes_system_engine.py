"""
Motor do Sistema de Eixos do Modelo do SketchUp (Axes Tool - Zero DLL).

Implementa a engenharia reversa da ferramenta Eixos do SketchUp:
(Ferramentas -> Eixos / Clique com botão direito -> Alinhar Eixos)
1. Ferramenta Eixos (Axes Tool):
   - Posiciona nova Origem do sistema de coordenadas (ponto de inserção).
   - Orienta o Eixo Vermelho (X) em direção a um ponto guia.
   - Orienta o Eixo Verde (Y) determinando o plano de trabalho.
   - Ortonormalização estrita de Gram-Schmidt para garantir Z = X x Y unitário.
2. Alinhar Eixos à Face (Align Axes to Face):
   - Alinha o eixo normal Z perpendicularmente à face selecionada.
   - Origem no centroide da face e eixos X e Y paralelos à sua aresta de base.
   - Facilita desenho e modelagem inclinada (telhados, rampas, fachadas).
3. Redefinir Eixos (Reset Axes):
   - Restaura o sistema para a Origem Global do Modelo (0, 0, 0) com eixos canônicos.
4. Matrizes de Transformação:
   - Gera matriz 4x4 de rotação e translação para o Three.js e inferência de coordenadas locais.
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class AxesSystemEngine:
    """Motor analítico do sistema de eixos e coordenadas locais do SketchUp."""

    @staticmethod
    def _normalize(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
        l = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
        if l < 1e-9:
            return (1.0, 0.0, 0.0)
        return (v[0] / l, v[1] / l, v[2] / l)

    @staticmethod
    def _cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        )

    @classmethod
    def set_custom_axes(
        cls,
        origin: Tuple[float, float, float],
        x_point: Tuple[float, float, float],
        y_point: Tuple[float, float, float]
    ) -> Dict[str, Any]:
        """
        Define um sistema de eixos personalizado a partir da origem e dois pontos direcionais.
        """
        ox, oy, oz = origin

        # Vetor X provisório
        vx = (x_point[0] - ox, x_point[1] - oy, x_point[2] - oz)
        axis_x = cls._normalize(vx)

        # Vetor Y provisório
        vy = (y_point[0] - ox, y_point[1] - oy, y_point[2] - oz)

        # Eixo Z via produto vetorial X x Y
        vz = cls._cross(axis_x, vy)
        axis_z = cls._normalize(vz)

        # Eixo Y corrigido ortogonal Z x X
        axis_y = cls._cross(axis_z, axis_x)

        # Matriz afim 4x4 (column-major)
        matrix4x4 = [
            axis_x[0], axis_y[0], axis_z[0], 0.0,
            axis_x[1], axis_y[1], axis_z[1], 0.0,
            axis_x[2], axis_y[2], axis_z[2], 0.0,
            ox, oy, oz, 1.0
        ]

        return {
            "origin": (round(ox, 4), round(oy, 4), round(oz, 4)),
            "axis_x_red": (round(axis_x[0], 4), round(axis_x[1], 4), round(axis_x[2], 4)),
            "axis_y_green": (round(axis_y[0], 4), round(axis_y[1], 4), round(axis_y[2], 4)),
            "axis_z_blue": (round(axis_z[0], 4), round(axis_z[1], 4), round(axis_z[2], 4)),
            "is_global": False,
            "matrix4x4": [round(m, 6) for m in matrix4x4]
        }

    @classmethod
    def align_axes_to_face(
        cls,
        face_vertices: List[Tuple[float, float, float]]
    ) -> Dict[str, Any]:
        """
        Alinha os eixos do modelo diretamente à face selecionada.
        O eixo Z coincide com a normal externa, e a origem fica no centroide da face.
        """
        if len(face_vertices) < 3:
            raise ValueError("Uma face deve conter no mínimo 3 vértices.")

        # Centroide da face
        n = len(face_vertices)
        cx = sum(v[0] for v in face_vertices) / n
        cy = sum(v[1] for v in face_vertices) / n
        cz = sum(v[2] for v in face_vertices) / n
        origin = (cx, cy, cz)

        # Eixo X paralelo à primeira aresta da face
        v0, v1 = face_vertices[0], face_vertices[1]
        edge_dir = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        axis_x = cls._normalize(edge_dir)

        # Normal da face via produto vetorial das duas primeiras arestas
        v2 = face_vertices[2]
        edge2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
        norm = cls._cross(edge_dir, edge2)
        axis_z = cls._normalize(norm)

        # Eixo Y perpendicular Z x X
        axis_y = cls._cross(axis_z, axis_x)

        matrix4x4 = [
            axis_x[0], axis_y[0], axis_z[0], 0.0,
            axis_x[1], axis_y[1], axis_z[1], 0.0,
            axis_x[2], axis_y[2], axis_z[2], 0.0,
            cx, cy, cz, 1.0
        ]

        return {
            "origin": (round(cx, 4), round(cy, 4), round(cz, 4)),
            "axis_x_red": (round(axis_x[0], 4), round(axis_x[1], 4), round(axis_x[2], 4)),
            "axis_y_green": (round(axis_y[0], 4), round(axis_y[1], 4), round(axis_y[2], 4)),
            "axis_z_blue": (round(axis_z[0], 4), round(axis_z[1], 4), round(axis_z[2], 4)),
            "aligned_to_face": True,
            "matrix4x4": [round(m, 6) for m in matrix4x4]
        }

    @classmethod
    def reset_axes(cls) -> Dict[str, Any]:
        """Restaura o sistema para a Origem Global canônica do SketchUp."""
        return {
            "origin": (0.0, 0.0, 0.0),
            "axis_x_red": (1.0, 0.0, 0.0),
            "axis_y_green": (0.0, 1.0, 0.0),
            "axis_z_blue": (0.0, 0.0, 1.0),
            "is_global": True,
            "matrix4x4": [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0
            ]
        }
