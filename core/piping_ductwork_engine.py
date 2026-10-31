"""
SketchBuild - Tubulações e Dutos Paramétricos 3D com Conexões (Zero DLL / Pure Python)
Frente 93: Engenharia Reversa do SketchUp - Piping, HVAC Ductwork & Fitting Generator

Gera tubulações cilíndricas ou dutos retangulares ao longo de trajetórias 3D,
inserindo automaticamente curvas de raio longo/curto, cotovelos de 90° e flanges.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class PipingDuctworkEngine:
    """Motor analítico de modelagem de tubulações industriais e conexões B-Rep."""

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
    def _normalize(v: Tuple[float, float, float]) -> Tuple[float, float, float]:
        mag = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
        if mag < 1e-9:
            return (0.0, 0.0, 1.0)
        return (v[0] / mag, v[1] / mag, v[2] / mag)

    @staticmethod
    def _cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )

    @staticmethod
    def generate_pipe_route(
        route_points: List[Tuple[float, float, float]],
        outer_diameter_mm: float = 114.3,  # 4 polegadas nominal
        wall_thickness_mm: float = 6.02,
        radial_segments: int = 16,
        bend_radius_factor: float = 1.5   # Raio longo (1.5 x D)
    ) -> Dict[str, Any]:
        """
        Roteia tubulação paramétrica ao longo dos pontos de centro.
        Gera anéis cilíndricos costurados e detecta ângulos de desvio para cotovelos.
        """
        if len(route_points) < 2:
            return {
                "entity_type": "PipingRouteResult",
                "vertices": [],
                "faces": [],
                "fittings": [],
                "total_length_m": 0.0,
                "status": "MÍNIMO DE 2 PONTOS NECESSÁRIOS"
            }

        pipe_radius_m = (outer_diameter_mm / 1000.0) / 2.0
        fittings: List[Dict[str, Any]] = []
        total_length = 0.0

        # Identificar segmentos e cotovelos
        for i in range(len(route_points) - 1):
            p1 = route_points[i]
            p2 = route_points[i + 1]
            seg_len = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2 + (p2[2] - p1[2])**2)
            total_length += seg_len

            if i < len(route_points) - 2:
                p3 = route_points[i + 2]
                v1 = PipingDuctworkEngine._normalize(PipingDuctworkEngine._vec_sub(p2, p1))
                v2 = PipingDuctworkEngine._normalize(PipingDuctworkEngine._vec_sub(p3, p2))
                dot = max(-1.0, min(1.0, v1[0]*v2[0] + v1[1]*v2[1] + v1[2]*v2[2]))
                deflection_angle = math.degrees(math.acos(dot))
                if deflection_angle > 5.0:
                    fittings.append({
                        "fitting_type": "ELBOW",
                        "angle_deg": round(deflection_angle, 1),
                        "position": list(p2),
                        "nominal_diameter_mm": outer_diameter_mm,
                        "bend_radius_m": round(outer_diameter_mm / 1000.0 * bend_radius_factor, 3),
                    })

        # Gerar malha de extrusão B-Rep
        vertices: List[List[float]] = []
        faces: List[List[int]] = []

        rings: List[List[int]] = []
        for pt_idx, pt in enumerate(route_points):
            # Vetor tangente no ponto
            if pt_idx == 0:
                tangent = PipingDuctworkEngine._normalize(PipingDuctworkEngine._vec_sub(route_points[1], pt))
            elif pt_idx == len(route_points) - 1:
                tangent = PipingDuctworkEngine._normalize(PipingDuctworkEngine._vec_sub(pt, route_points[-2]))
            else:
                t1 = PipingDuctworkEngine._normalize(PipingDuctworkEngine._vec_sub(pt, route_points[pt_idx - 1]))
                t2 = PipingDuctworkEngine._normalize(PipingDuctworkEngine._vec_sub(route_points[pt_idx + 1], pt))
                tangent = PipingDuctworkEngine._normalize(PipingDuctworkEngine._vec_add(t1, t2))

            # Triedro de Frenet perpendicular à tangente
            up = (0.0, 0.0, 1.0) if abs(tangent[2]) < 0.9 else (0.0, 1.0, 0.0)
            normal = PipingDuctworkEngine._normalize(PipingDuctworkEngine._cross(tangent, up))
            binormal = PipingDuctworkEngine._normalize(PipingDuctworkEngine._cross(tangent, normal))

            ring_indices: List[int] = []
            for j in range(radial_segments):
                angle = 2.0 * math.pi * j / radial_segments
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                vx = pt[0] + (normal[0] * cos_a + binormal[0] * sin_a) * pipe_radius_m
                vy = pt[1] + (normal[1] * cos_a + binormal[1] * sin_a) * pipe_radius_m
                vz = pt[2] + (normal[2] * cos_a + binormal[2] * sin_a) * pipe_radius_m
                ring_indices.append(len(vertices))
                vertices.append([round(vx, 5), round(vy, 5), round(vz, 5)])
            rings.append(ring_indices)

        # Costurar anéis adjacentes com quads
        for i in range(len(rings) - 1):
            r1 = rings[i]
            r2 = rings[i + 1]
            for j in range(radial_segments):
                j_next = (j + 1) % radial_segments
                faces.append([r1[j], r1[j_next], r2[j_next], r2[j]])

        # Fechamento de pontas (tampas circulares nas extremidades)
        faces.append(list(reversed(rings[0])))
        faces.append(list(rings[-1]))

        # Triangulação
        triangles: List[List[int]] = []
        for poly in faces:
            if len(poly) == 3:
                triangles.append(poly)
            elif len(poly) == 4:
                triangles.append([poly[0], poly[1], poly[2]])
                triangles.append([poly[0], poly[2], poly[3]])
            elif len(poly) > 4:
                for k in range(1, len(poly) - 1):
                    triangles.append([poly[0], poly[k], poly[k + 1]])

        return {
            "entity_type": "PipingRouteResult",
            "outer_diameter_mm": outer_diameter_mm,
            "wall_thickness_mm": wall_thickness_mm,
            "total_length_m": round(total_length, 3),
            "segments_count": len(route_points) - 1,
            "fittings_count": len(fittings),
            "fittings": fittings,
            "vertices_count": len(vertices),
            "faces_count": len(faces),
            "triangles_count": len(triangles),
            "vertices": vertices,
            "faces": faces,
            "triangles": triangles,
            "status": "TUBULAÇÃO PARAMÉTRICA GERADA COM SUCESSO"
        }
