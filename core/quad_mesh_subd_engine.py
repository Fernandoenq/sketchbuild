"""
SketchBuild - Decodificador e Subdivisão de Superfície SubD / QuadMesh (Zero DLL / Pure Python)
Frente 86: Engenharia Reversa do SketchUp - QuadFace Tools e Algoritmo Catmull-Clark

Implementa topologia quadrilátera estruturada (QuadMesh) e algoritmo analítico
de subdivisão de superfície Catmull-Clark para gerar malhas suaves orgânicas
a partir de malhas de controle poligonais.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple


class QuadMeshSubDEngine:
    """Motor analítico de subdivisão Catmull-Clark e topologia QuadFace."""

    @staticmethod
    def _vec_add(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    @staticmethod
    def _vec_sub(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> Tuple[float, float, float]:
        return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

    @staticmethod
    def _vec_scale(v: Tuple[float, float, float], s: float) -> Tuple[float, float, float]:
        return (v[0] * s, v[1] * s, v[2] * s)

    @staticmethod
    def subdivide_catmull_clark(
        vertices: List[Tuple[float, float, float]],
        faces: List[List[int]],
        iterations: int = 1
    ) -> Dict[str, Any]:
        """
        Aplica o algoritmo analítico de Catmull-Clark sobre a malha de controle.
        Transforma triângulos e quadriláteros em uma malha suave composta exclusivamente
        de quadriláteros subdivididos.
        """
        curr_verts = [tuple(v) for v in vertices]
        curr_faces = [list(f) for f in faces]

        for _ in range(max(1, min(iterations, 3))):
            curr_verts, curr_faces = QuadMeshSubDEngine._step_catmull_clark(curr_verts, curr_faces)

        # Triangulação opcional para visualizadores que exigem triângulos
        triangles: List[List[int]] = []
        for q in curr_faces:
            if len(q) == 4:
                triangles.append([q[0], q[1], q[2]])
                triangles.append([q[0], q[2], q[3]])
            elif len(q) == 3:
                triangles.append(q)

        return {
            "entity_type": "SubDMeshResult",
            "iterations": iterations,
            "original_vertices_count": len(vertices),
            "original_faces_count": len(faces),
            "subdivided_vertices_count": len(curr_verts),
            "subdivided_quad_faces_count": len(curr_faces),
            "triangles_count": len(triangles),
            "vertices": [list(v) for v in curr_verts],
            "quad_faces": curr_faces,
            "triangles": triangles,
            "status": "SUBDIVISÃO CATMULL-CLARK GERADA COM SUCESSO"
        }

    @staticmethod
    def _step_catmull_clark(
        vertices: List[Tuple[float, float, float]],
        faces: List[List[int]]
    ) -> Tuple[List[Tuple[float, float, float]], List[List[int]]]:
        # 1. Pontos de Face (Centróide de cada face)
        face_points: List[Tuple[float, float, float]] = []
        for face in faces:
            n = len(face)
            cx = sum(vertices[i][0] for i in face) / n
            cy = sum(vertices[i][1] for i in face) / n
            cz = sum(vertices[i][2] for i in face) / n
            face_points.append((cx, cy, cz))

        # 2. Mapeamento de arestas e incidentes
        # Cada aresta (min_idx, max_idx) mapeia para faces incidentes
        edges: Dict[Tuple[int, int], List[int]] = {}
        for f_idx, face in enumerate(faces):
            k = len(face)
            for i in range(k):
                v1 = face[i]
                v2 = face[(i + 1) % k]
                edge_key = (min(v1, v2), max(v1, v2))
                if edge_key not in edges:
                    edges[edge_key] = []
                edges[edge_key].append(f_idx)

        # 3. Pontos de Aresta
        edge_points: Dict[Tuple[int, int], Tuple[float, float, float]] = {}
        for edge_key, inc_faces in edges.items():
            v1, v2 = edge_key
            p1 = vertices[v1]
            p2 = vertices[v2]
            if len(inc_faces) == 2:
                # Interna: média de p1, p2 e os face points das 2 faces
                f1 = face_points[inc_faces[0]]
                f2 = face_points[inc_faces[1]]
                ep = (
                    (p1[0] + p2[0] + f1[0] + f2[0]) / 4.0,
                    (p1[1] + p2[1] + f1[1] + f2[1]) / 4.0,
                    (p1[2] + p2[2] + f1[2] + f2[2]) / 4.0,
                )
            else:
                # Borda: ponto médio simples
                ep = (
                    (p1[0] + p2[0]) / 2.0,
                    (p1[1] + p2[1]) / 2.0,
                    (p1[2] + p2[2]) / 2.0,
                )
            edge_points[edge_key] = ep

        # 4. Atualização dos vértices originais (Vertex Points)
        # Para cada vértice original, coletar faces adjacentes e arestas incidentes
        vert_adj_faces: Dict[int, List[int]] = {i: [] for i in range(len(vertices))}
        vert_inc_edges: Dict[int, List[Tuple[int, int]]] = {i: [] for i in range(len(vertices))}

        for f_idx, face in enumerate(faces):
            for v_idx in face:
                vert_adj_faces[v_idx].append(f_idx)

        for edge_key in edges.keys():
            v1, v2 = edge_key
            vert_inc_edges[v1].append(edge_key)
            vert_inc_edges[v2].append(edge_key)

        new_vertices: List[Tuple[float, float, float]] = []
        for i, old_v in enumerate(vertices):
            n = len(vert_adj_faces[i])
            if n < 3:
                # Vértice de canto ou borda: manter posição ou média simples
                new_vertices.append(old_v)
                continue

            # Média dos face points das faces incidentes
            f_avg = (
                sum(face_points[f][0] for f in vert_adj_faces[i]) / n,
                sum(face_points[f][1] for f in vert_adj_faces[i]) / n,
                sum(face_points[f][2] for f in vert_adj_faces[i]) / n,
            )

            # Média dos pontos médios das arestas incidentes
            m_edges = len(vert_inc_edges[i])
            r_avg = (
                sum((vertices[e[0]][0] + vertices[e[1]][0]) / 2.0 for e in vert_inc_edges[i]) / m_edges,
                sum((vertices[e[0]][1] + vertices[e[1]][1]) / 2.0 for e in vert_inc_edges[i]) / m_edges,
                sum((vertices[e[0]][2] + vertices[e[1]][2]) / 2.0 for e in vert_inc_edges[i]) / m_edges,
            )

            # Fórmula padrão Catmull-Clark: V' = (F + 2R + (n-3)V) / n
            vx = (f_avg[0] + 2.0 * r_avg[0] + (n - 3) * old_v[0]) / n
            vy = (f_avg[1] + 2.0 * r_avg[1] + (n - 3) * old_v[1]) / n
            vz = (f_avg[2] + 2.0 * r_avg[2] + (n - 3) * old_v[2]) / n
            new_vertices.append((round(vx, 6), round(vy, 6), round(vz, 6)))

        # Vértices de saída combinam:
        # [0 .. len(vertices)-1]: novos vertex points
        # [len(vertices) .. +len(face_points)-1]: face points
        # [...]: edge points
        out_verts: List[Tuple[float, float, float]] = list(new_vertices)
        face_pt_indices: List[int] = []
        for fp in face_points:
            face_pt_indices.append(len(out_verts))
            out_verts.append((round(fp[0], 6), round(fp[1], 6), round(fp[2], 6)))

        edge_pt_indices: Dict[Tuple[int, int], int] = {}
        for edge_key, ep in edge_points.items():
            edge_pt_indices[edge_key] = len(out_verts)
            out_verts.append((round(ep[0], 6), round(ep[1], 6), round(ep[2], 6)))

        # 5. Criar novos quadriláteros para cada face original
        new_quads: List[List[int]] = []
        for f_idx, face in enumerate(faces):
            k = len(face)
            fp_idx = face_pt_indices[f_idx]
            for i in range(k):
                v_curr = face[i]
                v_prev = face[(i - 1 + k) % k]
                v_next = face[(i + 1) % k]

                e_prev = (min(v_prev, v_curr), max(v_prev, v_curr))
                e_next = (min(v_curr, v_next), max(v_curr, v_next))

                ep_prev_idx = edge_pt_indices[e_prev]
                ep_next_idx = edge_pt_indices[e_next]

                # Quadrilátero: [V' (atual), EdgePointNext, FacePoint, EdgePointPrev]
                new_quads.append([v_curr, ep_next_idx, fp_idx, ep_prev_idx])

        return out_verts, new_quads
