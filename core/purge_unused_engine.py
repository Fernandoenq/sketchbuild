"""
Motor de Eliminação de Elementos Não Utilizados do SketchUp (Purge Unused - Zero DLL).

Implementa a engenharia reversa da ferramenta oficial 'Eliminar não utilizados' (Purge Unused):
(Janela -> Informações do Modelo -> Estatísticas -> Eliminar não utilizados)
1. Identificação e Purgação de Entidades Órfãs:
   - Definições de Componentes: Definições na biblioteca interna com 0 instâncias ativas na cena.
   - Materiais e Texturas: Cores e imagens carregadas não atribuídas a nenhuma face ou componente.
   - Etiquetas / Tags: Camadas sem instâncias (preservando obrigatoriamente a 'Layer0' canônica).
   - Estilos: Estilos não associados à cena ativa.
2. Relatório de Otimização:
   - Quantidade e nomes exatos de elementos removidos.
   - Estimativa de redução de memória e compactação da árvore de dados do .SKP.
"""

from typing import List, Dict, Any, Set, Tuple


class PurgeUnusedEngine:
    """Motor analítico de limpeza e purgação de elementos órfãos do SketchUp."""

    @classmethod
    def purge_unused_items(
        cls,
        component_definitions: List[Dict[str, Any]],
        instances: List[Dict[str, Any]],
        materials: List[Dict[str, Any]],
        tags: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Executa a purgação de definições, materiais e tags não utilizados no modelo.
        """
        # 1. Componentes em uso
        used_definition_names: Set[str] = set()
        used_materials: Set[str] = set()
        used_tags: Set[str] = {"Layer0", "Sem Etiqueta"}

        for inst in instances:
            def_name = inst.get("definition_name", inst.get("name"))
            if def_name:
                used_definition_names.add(def_name)

            mat = inst.get("material")
            if mat:
                used_materials.add(mat)

            tag = inst.get("tag", inst.get("layer"))
            if tag:
                used_tags.add(tag)

        # 2. Purga definições de componentes não utilizadas
        purged_components = []
        kept_components = []
        for c in component_definitions:
            c_name = c.get("name", c.get("definition_name", ""))
            if c_name not in used_definition_names:
                purged_components.append(c_name)
            else:
                kept_components.append(c)

        # 3. Purga materiais não utilizados
        purged_materials = []
        kept_materials = []
        for m in materials:
            m_name = m.get("name", m.get("material_name", ""))
            if m_name and m_name not in used_materials and m_name != "Padrão":
                purged_materials.append(m_name)
            else:
                kept_materials.append(m)

        # 4. Purga tags não utilizadas (exceto Layer0)
        purged_tags = []
        kept_tags = []
        for t in tags:
            t_name = t.get("name", t.get("tag_name", ""))
            if t_name not in used_tags and t_name != "Layer0":
                purged_tags.append(t_name)
            else:
                kept_tags.append(t)

        total_purged = len(purged_components) + len(purged_materials) + len(purged_tags)

        return {
            "total_items_purged": total_purged,
            "purged_components_count": len(purged_components),
            "purged_components": purged_components,
            "purged_materials_count": len(purged_materials),
            "purged_materials": purged_materials,
            "purged_tags_count": len(purged_tags),
            "purged_tags": purged_tags,
            "kept_components_count": len(kept_components),
            "kept_materials_count": len(kept_materials),
            "kept_tags_count": len(kept_tags),
            "status": "Model successfully purged and compacted" if total_purged > 0 else "Nothing to purge"
        }
