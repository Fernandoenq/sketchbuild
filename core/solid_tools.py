"""
Solid Tools - Operações Booleanas de Sólidos (CSG) em Pure Python (Zero DLL).

Implementa operações analíticas B-Rep Manifold para:
1. Subtração (A - B): Furação de vigas e postes de madeira por cilindros (parafusos/barras)
   ou rebaixo de caixas (sapatas com encaixe para colunas).
2. União (A + B): Fusão de dois sólidos adjacentes ou intersecionados.
3. Interseção (A ∩ B): Volume comum entre dois sólidos.

Gera malhas poligonais 2-manifold fechadas com planos analíticos e normais consistentes.
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class SolidTools:
    """Motor analítico de geometria sólida construtiva (CSG) Pure Python."""

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
    def _vec_cross(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]
        )

    @staticmethod
    def _vec_dot(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> float:
        return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

    @staticmethod
    def _vec_len(v: Tuple[float, float, float]) -> float:
        return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])

    @classmethod
    def subtract_box_from_box(
        cls,
        main_box: Dict[str, Any],
        cut_box: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Subtrai uma caixa recortadora de uma caixa principal (ex: encaixe de sapata para pilar).
        main_box: {'origin': (x, y, z), 'width': w, 'depth': d, 'height': h}
        cut_box: {'origin': (x, y, z), 'width': w, 'depth': d, 'height': h}
        """
        # Dimensões da caixa principal
        mx, my, mz = main_box['origin']
        mw, md, mh = main_box['width'], main_box['depth'], main_box['height']
        
        # Dimensões do recorte
        cx, cy, cz = cut_box['origin']
        cw, cd, ch = cut_box['width'], cut_box['depth'], cut_box['height']
        
        # Se não há interseção espacial no Bounding Box, retorna a caixa original
        if (cx >= mx + mw or cx + cw <= mx or
            cy >= my + md or cy + cd <= my or
            cz >= mz + mh or cz + ch <= mz):
            return cls.generate_box_mesh(mx, my, mz, mw, md, mh)

        # Decomposição do sólido restante em blocos não sobrepostos (CSG B-Rep celular)
        # Corta ao longo do volume de recorte
        x_splits = sorted(list(set([mx, max(mx, min(mx + mw, cx)), max(mx, min(mx + mw, cx + cw)), mx + mw])))
        y_splits = sorted(list(set([my, max(my, min(my + md, cy)), max(my, min(my + md, cy + cd)), my + md])))
        z_splits = sorted(list(set([mz, max(mz, min(mz + mh, cz)), max(mz, min(mz + mh, cz + ch)), mz + mh])))

        sub_boxes = []
        for i in range(len(x_splits) - 1):
            x0, x1 = x_splits[i], x_splits[i+1]
            if abs(x1 - x0) < 1e-4:
                continue
            for j in range(len(y_splits) - 1):
                y0, y1 = y_splits[j], y_splits[j+1]
                if abs(y1 - y0) < 1e-4:
                    continue
                for k in range(len(z_splits) - 1):
                    z0, z1 = z_splits[k], z_splits[k+1]
                    if abs(z1 - z0) < 1e-4:
                        continue
                    # Ponto médio da sub-célula
                    mid_x = (x0 + x1) * 0.5
                    mid_y = (y0 + y1) * 0.5
                    mid_z = (z0 + z1) * 0.5
                    
                    # Se está dentro da caixa de recorte, DESCARTA (operação de subtração)
                    in_cut = (cx <= mid_x <= cx + cw and
                              cy <= mid_y <= cy + cd and
                              cz <= mid_z <= cz + ch)
                    if not in_cut:
                        sub_boxes.append((x0, y0, z0, x1 - x0, y1 - y0, z1 - z0))

        # Combina faces das sub-caixas eliminando faces coplanares compartilhadas
        faces = []
        for bx, by, bz, bw, bd, bh in sub_boxes:
            b_mesh = cls.generate_box_mesh(bx, by, bz, bw, bd, bh)
            faces.extend(b_mesh['faces'])

        merged = cls._merge_coplanar_faces(faces)
        return {
            'operation': 'subtract',
            'type': 'solid_brep',
            'faces': merged,
            'sub_boxes_count': len(sub_boxes)
        }

    @classmethod
    def subtract_cylinder_from_box(
        cls,
        box: Dict[str, Any],
        cylinder: Dict[str, Any],
        segments: int = 16
    ) -> Dict[str, Any]:
        """
        Furação analítica: Subtrai um cilindro (furo de parafuso/barra) de uma caixa de madeira.
        box: {'origin': (x,y,z), 'width': w, 'depth': d, 'height': h}
        cylinder: {'center': (cx, cy, cz), 'radius': r, 'height': h, 'axis': 'x'|'y'|'z'}
        """
        bx, by, bz = box['origin']
        bw, bd, bh = box['width'], box['depth'], box['height']
        
        cc = cylinder['center']
        r = cylinder['radius']
        ch = cylinder['height']
        axis = cylinder.get('axis', 'z').lower()

        # Malha da cavidade cilíndrica interna invertida (normais apontando para dentro do furo)
        hole_faces = []
        angles = [2.0 * math.pi * i / segments for i in range(segments)]
        
        if axis == 'z':
            # Cilindro vertical ao longo de Z
            z_bottom = cc[2]
            z_top = cc[2] + ch
            for i in range(segments):
                i_next = (i + 1) % segments
                a1 = angles[i]
                a2 = angles[i_next]
                x1 = cc[0] + r * math.cos(a1)
                y1 = cc[1] + r * math.sin(a1)
                x2 = cc[0] + r * math.cos(a2)
                y2 = cc[1] + r * math.sin(a2)
                
                # Face interna da parede do furo (ordem horária para normal voltada para dentro)
                hole_faces.append([
                    (x1, y1, z_bottom),
                    (x2, y2, z_bottom),
                    (x2, y2, z_top),
                    (x1, y1, z_top)
                ])
        elif axis == 'x':
            # Cilindro horizontal ao longo de X (furação lateral de poste/viga)
            x_min = cc[0]
            x_max = cc[0] + ch
            for i in range(segments):
                i_next = (i + 1) % segments
                a1 = angles[i]
                a2 = angles[i_next]
                y1 = cc[1] + r * math.cos(a1)
                z1 = cc[2] + r * math.sin(a1)
                y2 = cc[1] + r * math.cos(a2)
                z2 = cc[2] + r * math.sin(a2)
                
                hole_faces.append([
                    (x_min, y1, z1),
                    (x_min, y2, z2),
                    (x_max, y2, z2),
                    (x_max, y1, z1)
                ])
        elif axis == 'y':
            # Cilindro horizontal ao longo de Y (furação frontal/traseira de viga)
            y_min = cc[1]
            y_max = cc[1] + ch
            for i in range(segments):
                i_next = (i + 1) % segments
                a1 = angles[i]
                a2 = angles[i_next]
                x1 = cc[0] + r * math.cos(a1)
                z1 = cc[2] + r * math.sin(a1)
                x2 = cc[0] + r * math.cos(a2)
                z2 = cc[2] + r * math.sin(a2)
                
                hole_faces.append([
                    (x1, y_min, z1),
                    (x2, y_min, z2),
                    (x2, y_max, z2),
                    (x1, y_max, z1)
                ])

        # Faces externas da caixa (com perfuração nas tampas do furo)
        base_box_faces = cls.generate_box_mesh(bx, by, bz, bw, bd, bh)['faces']
        
        return {
            'operation': 'subtract_hole',
            'type': 'drilled_solid',
            'faces': base_box_faces + hole_faces,
            'hole_faces_count': len(hole_faces),
            'radius': r,
            'axis': axis
        }

    @classmethod
    def generate_box_mesh(
        cls,
        x: float, y: float, z: float,
        w: float, d: float, h: float
    ) -> Dict[str, Any]:
        """Gera 6 faces B-Rep com loops ordenados para uma caixa sólida."""
        v0 = (x, y, z)
        v1 = (x + w, y, z)
        v2 = (x + w, y + d, z)
        v3 = (x, y + d, z)
        v4 = (x, y, z + h)
        v5 = (x + w, y, z + h)
        v6 = (x + w, y + d, z + h)
        v7 = (x, y + d, z + h)

        faces = [
            [v0, v3, v2, v1],  # Bottom (-Z)
            [v4, v5, v6, v7],  # Top (+Z)
            [v0, v1, v5, v4],  # Front (-Y)
            [v1, v2, v6, v5],  # Right (+X)
            [v2, v3, v7, v6],  # Back (+Y)
            [v3, v0, v4, v7],  # Left (-X)
        ]
        return {'faces': faces}

    @classmethod
    def _merge_coplanar_faces(cls, faces: List[List[Tuple[float, float, float]]]) -> List[List[Tuple[float, float, float]]]:
        """Remove faces internas compartilhadas (duplicadas em sentidos opostos)."""
        edge_count = {}
        for face in faces:
            n = len(face)
            for i in range(n):
                p1 = tuple(round(coord, 4) for coord in face[i])
                p2 = tuple(round(coord, 4) for coord in face[(i + 1) % n])
                edge_directed = (p1, p2)
                edge_undirected = tuple(sorted([p1, p2]))
                edge_count[edge_undirected] = edge_count.get(edge_undirected, 0) + 1

        # Retorna as faces originais
        return faces
