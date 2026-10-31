"""
Motor de Inversão e Orientação de Faces do SketchUp (Reverse Faces & Orient Faces - Zero DLL).

Implementa a engenharia reversa das ferramentas nativas do menu de contexto de faces do SketchUp:
1. Inverter Faces (Reverse Faces):
   - Inverte a ordem cíclica de vértices (winding order) dos loops e triângulos da face.
   - Inverte o vetor normal da face (n -> -n).
2. Orientar Faces (Orient Faces):
   - Seleciona uma face de referência com normal conhecida.
   - Propaga orientação consistente para todas as faces conectadas através de arestas compartilhadas
     (em superfícies 2-manifold orientáveis, duas faces adjacentes devem percorrer a aresta compartilhada em direções opostas).
   - Corrige automaticamente superfícies com faces voltadas para dentro no modelo.
"""

from typing import List, Dict, Any, Tuple, Set


class ReverseOrientFacesEngine:
    """Motor analítico de reversão e orientação de faces do SketchUp."""

    @classmethod
    def reverse_face(cls, face: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inverte a orientação de uma única face (winding order e normal).
        """
        vertices = face.get("vertices", [])
        reversed_vertices = list(reversed(vertices))

        normal = face.get("normal", [0.0, 0.0, 1.0])
        reversed_normal = [-normal[0], -normal[1], -normal[2]]

        # Inverte triângulos se existirem
        triangles = face.get("triangles", [])
        reversed_triangles = []
        for tri in triangles:
            # Triângulo [p0, p1, p2] invertido -> [p0, p2, p1]
            if len(tri) == 3:
                reversed_triangles.append([tri[0], tri[2], tri[1]])
            else:
                reversed_triangles.append(list(reversed(tri)))

        new_face = dict(face)
        new_face["vertices"] = reversed_vertices
        new_face["normal"] = reversed_normal
        if triangles:
            new_face["triangles"] = reversed_triangles
        new_face["is_reversed"] = not face.get("is_reversed", False)
        return new_face

    @classmethod
    def reverse_selected_faces(
        cls,
        faces: List[Dict[str, Any]],
        selected_indices: List[int]
    ) -> Dict[str, Any]:
        """
        Inverte as faces cujos índices foram especificados.
        """
        result_faces = []
        flipped_count = 0
        target_indices = set(selected_indices)

        for idx, f in enumerate(faces):
            if idx in target_indices:
                result_faces.append(cls.reverse_face(f))
                flipped_count += 1
            else:
                result_faces.append(dict(f))

        return {
            "status": "success",
            "flipped_count": flipped_count,
            "total_faces": len(faces),
            "faces": result_faces
        }

    @classmethod
    def orient_connected_faces(
        cls,
        faces: List[Dict[str, Any]],
        reference_face_index: int = 0
    ) -> Dict[str, Any]:
        """
        Propaga a orientação da face de referência para todas as faces conexas (Orient Faces).
        Em uma malha orientada coerente, arestas compartilhadas entre duas faces adjacentes
        devem ser percorridas em sentidos opostos: A -> B em uma, e B -> A na outra.
        """
        if not faces or reference_face_index < 0 or reference_face_index >= len(faces):
            return {
                "status": "error",
                "message": "Índice de face de referência inválido ou lista vazia",
                "flipped_count": 0,
                "faces": faces
            }

        n_faces = len(faces)
        working_faces = [dict(f) for f in faces]

        # Mapeamento de arestas direcionadas para faces
        # edge -> list of (face_idx, p_start, p_end)
        def _get_edges_with_dir(f_idx: int, face_dict: Dict[str, Any]) -> List[Tuple[Tuple[float, float, float], Tuple[float, float, float]]]:
            verts = [tuple(round(coord, 5) for coord in p) for p in face_dict.get("vertices", [])]
            m = len(verts)
            if m < 3:
                return []
            edges = []
            for i in range(m):
                p1 = verts[i]
                p2 = verts[(i + 1) % m]
                edges.append((p1, p2))
            return edges

        # Adjacência de faces através de arestas compartilhadas
        # Monta grafo de conectividade
        visited: Set[int] = {reference_face_index}
        queue = [reference_face_index]
        flipped_indices: Set[int] = set()

        while queue:
            curr_idx = queue.pop(0)
            curr_edges = _get_edges_with_dir(curr_idx, working_faces[curr_idx])

            for other_idx in range(n_faces):
                if other_idx in visited:
                    continue

                other_edges = _get_edges_with_dir(other_idx, working_faces[other_idx])
                
                # Verifica se há aresta compartilhada
                shares_edge = False
                needs_flip = False

                for (p1, p2) in curr_edges:
                    for (q1, q2) in other_edges:
                        # Se arestas coincidem geometricamente
                        if (p1 == q1 and p2 == q2):
                            # Estão no MESMO sentido -> Para orientação coerente de variedade, devem ser OPOSTOS!
                            shares_edge = True
                            needs_flip = True
                            break
                        elif (p1 == q2 and p2 == q1):
                            # Estão no sentido OPOSTO -> Orientação já está coerente!
                            shares_edge = True
                            needs_flip = False
                            break
                    if shares_edge:
                        break

                if shares_edge:
                    visited.add(other_idx)
                    if needs_flip:
                        working_faces[other_idx] = cls.reverse_face(working_faces[other_idx])
                        flipped_indices.add(other_idx)
                    queue.append(other_idx)

        return {
            "status": "success",
            "reference_face_index": reference_face_index,
            "connected_oriented_count": len(visited),
            "flipped_count": len(flipped_indices),
            "flipped_face_indices": sorted(list(flipped_indices)),
            "total_faces": n_faces,
            "faces": working_faces
        }
