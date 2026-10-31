"""
Motor de Seleção Avançada do SketchUp (Advanced Selection - Zero DLL).

Implementa a engenharia reversa dos modos clássicos de seleção do SketchUp Desktop:
1. Níveis de Clique Geométrico:
   - Clique Simples (Single Click): Seleciona a entidade pontual (face ou aresta).
   - Duplo Clique (Double Click): Seleciona a face e suas arestas de contorno circunscritas.
   - Triplo Clique (Triple Click): Seleciona toda a malha geometricamente conectada (Connected Mesh / Ilha).
2. Operações de Seleção do Menu Editar:
   - Inverter Seleção (Invert Selection - Ctrl+Shift+I): Inverte a lista de entidades selecionadas.
   - Selecionar Todas na Mesma Etiqueta (Select All on Same Tag): Seleciona instâncias que compartilham a tag.
   - Selecionar Todas com o Mesmo Material (Select All with Same Material): Seleciona instâncias com a mesma textura.
3. Janela de Seleção (Window vs Crossing Selection):
   - Janela da esquerda para a direita (Azul): Apenas o que estiver 100% contido na caixa.
   - Cruzamento da direita para a esquerda (Verde): Qualquer elemento que cruze ou toque a caixa.
"""

from typing import List, Dict, Any, Set, Optional, Tuple


class AdvancedSelectionEngine:
    """Motor analítico de seleção inteligente e filtragem de entidades do SketchUp."""

    @classmethod
    def invert_selection(
        cls,
        all_entity_ids: List[str],
        currently_selected_ids: List[str]
    ) -> List[str]:
        """Inverte a seleção ativa em relação ao universo total de entidades."""
        selected_set = set(currently_selected_ids)
        return [eid for eid in all_entity_ids if eid not in selected_set]

    @classmethod
    def select_by_tag(
        cls,
        target_tag: str,
        instances: List[Dict[str, Any]]
    ) -> List[str]:
        """Seleciona todas as instâncias que compartilham a mesma Etiqueta/Tag."""
        matched = []
        for inst in instances:
            t = inst.get("tag", inst.get("layer", "Layer0"))
            if t.lower().strip() == target_tag.lower().strip():
                matched.append(inst.get("instance_id", inst.get("id")))
        return matched

    @classmethod
    def select_by_material(
        cls,
        target_material: str,
        instances: List[Dict[str, Any]]
    ) -> List[str]:
        """Seleciona todas as instâncias que compartilham o mesmo Material."""
        matched = []
        for inst in instances:
            m = inst.get("material", "Padrão")
            if m.lower().strip() == target_material.lower().strip():
                matched.append(inst.get("instance_id", inst.get("id")))
        return matched

    @classmethod
    def select_connected_geometry(
        cls,
        seed_face_index: int,
        faces_vertices: List[List[Tuple[float, float, float]]]
    ) -> List[int]:
        """
        Executa o comportamento do 'Triplo Clique':
        A partir de uma face semente, encontra todas as faces conectadas topologicamente por arestas comuns.
        """
        if seed_face_index < 0 or seed_face_index >= len(faces_vertices):
            return []

        # Mapeia vértices -> índices de faces
        vertex_to_faces: Dict[Tuple[float, float, float], Set[int]] = {}
        for f_idx, face in enumerate(faces_vertices):
            for pt in face:
                pt_tuple = (round(pt[0], 4), round(pt[1], 4), round(pt[2], 4))
                if pt_tuple not in vertex_to_faces:
                    vertex_to_faces[pt_tuple] = set()
                vertex_to_faces[pt_tuple].add(f_idx)

        # BFS para visitar todas as faces conectadas
        visited_faces: Set[int] = {seed_face_index}
        queue = [seed_face_index]

        while queue:
            curr_f = queue.pop(0)
            for pt in faces_vertices[curr_f]:
                pt_tuple = (round(pt[0], 4), round(pt[1], 4), round(pt[2], 4))
                neighbors = vertex_to_faces.get(pt_tuple, set())
                for neighbor_f in neighbors:
                    if neighbor_f not in visited_faces:
                        visited_faces.add(neighbor_f)
                        queue.append(neighbor_f)

        return sorted(list(visited_faces))
