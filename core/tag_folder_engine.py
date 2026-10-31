"""
Motor de Pastas de Tags e Árvore de Camadas do SketchUp (Zero DLL).

Implementa a hierarquia nativa de TagFolders introduzida no SketchUp 2021+:
1. Estrutura em árvore de pastas aninhadas contendo Tags (Layers).
2. Resolução de visibilidade em cascata (herança de visibilidade pai -> filho).
3. Atribuição de paleta de cores cromáticas por Tag para o modo 'Color by Tag'.
4. Serialização e sincronização com a árvore de componentes da cena 3D.
"""

from typing import List, Dict, Any, Optional, Set


class TagFolderEngine:
    """Gerenciador de hierarquia de pastas e camadas do SketchUp."""

    def __init__(self):
        # Estrutura: {folder_id: {"name": str, "parent_id": Optional[str], "visible": bool, "expanded": bool, "tags": Set[str]}}
        self._folders: Dict[str, Dict[str, Any]] = {}
        # Tags soltas no nível raiz (sem pasta)
        self._root_tags: Set[str] = {"Sem etiqueta"}
        # Propriedades de tags individuais: {tag_name: {"visible": bool, "color": str}}
        self._tag_props: Dict[str, Dict[str, Any]] = {
            "Sem etiqueta": {"visible": True, "color": "#000000"}
        }

    def add_tag(self, tag_name: str, color_hex: str = "#4A5568", visible: bool = True) -> Dict[str, Any]:
        """Registra uma nova tag no modelo."""
        if tag_name not in self._tag_props:
            self._tag_props[tag_name] = {"visible": visible, "color": color_hex}
            self._root_tags.add(tag_name)
        return {"tag_name": tag_name, **self._tag_props[tag_name]}

    def create_folder(
        self,
        folder_id: str,
        name: str,
        parent_id: Optional[str] = None,
        visible: bool = True
    ) -> Dict[str, Any]:
        """Cria uma nova pasta de tags no modelo."""
        if parent_id and parent_id not in self._folders:
            raise ValueError(f"Pasta pai {parent_id!r} não encontrada.")

        self._folders[folder_id] = {
            "id": folder_id,
            "name": name,
            "parent_id": parent_id,
            "visible": visible,
            "expanded": True,
            "tags": set()
        }
        return self.get_folder_info(folder_id)

    def move_tag_to_folder(self, tag_name: str, target_folder_id: Optional[str]) -> bool:
        """Move uma tag para dentro de uma pasta (ou para a raiz se target_folder_id for None)."""
        if tag_name not in self._tag_props:
            self.add_tag(tag_name)

        # Remove de onde estava antes
        if tag_name in self._root_tags:
            self._root_tags.remove(tag_name)
        for f in self._folders.values():
            if tag_name in f["tags"]:
                f["tags"].remove(tag_name)

        # Insere no destino
        if target_folder_id:
            if target_folder_id not in self._folders:
                raise ValueError(f"Pasta de destino {target_folder_id!r} não existe.")
            self._folders[target_folder_id]["tags"].add(tag_name)
        else:
            self._root_tags.add(tag_name)
        return True

    def set_folder_visibility(self, folder_id: str, visible: bool) -> bool:
        """Altera a visibilidade da pasta."""
        if folder_id in self._folders:
            self._folders[folder_id]["visible"] = visible
            return True
        return False

    def is_tag_effectively_visible(self, tag_name: str) -> bool:
        """
        Calcula a visibilidade efetiva da tag considerando a herança de pastas pai.
        Se qualquer pasta ascendente estiver oculta, a tag estará oculta.
        """
        if tag_name not in self._tag_props:
            return True
        if not self._tag_props[tag_name]["visible"]:
            return False

        # Encontra em qual pasta a tag está
        parent_folder_id = None
        for f_id, f_data in self._folders.items():
            if tag_name in f_data["tags"]:
                parent_folder_id = f_id
                break

        # Percorre a árvore de pastas até a raiz
        curr_id = parent_folder_id
        while curr_id:
            folder = self._folders.get(curr_id)
            if not folder:
                break
            if not folder.get("visible", True):
                return False
            curr_id = folder.get("parent_id")

        return True

    def get_folder_info(self, folder_id: str) -> Dict[str, Any]:
        """Retorna informações estruturadas de uma pasta."""
        if folder_id not in self._folders:
            raise KeyError(f"Pasta {folder_id} não encontrada.")
        f = self._folders[folder_id]
        return {
            "id": f["id"],
            "name": f["name"],
            "parent_id": f["parent_id"],
            "visible": f["visible"],
            "expanded": f["expanded"],
            "tags_count": len(f["tags"]),
            "tags": list(f["tags"])
        }

    def get_full_tree(self) -> Dict[str, Any]:
        """Retorna a árvore completa de pastas e tags para a UI."""
        tree_folders = []
        for f_id in self._folders:
            tree_folders.append(self.get_folder_info(f_id))

        tags_status = {}
        for t_name, props in self._tag_props.items():
            tags_status[t_name] = {
                "own_visible": props["visible"],
                "effectively_visible": self.is_tag_effectively_visible(t_name),
                "color": props["color"]
            }

        return {
            "root_tags": list(self._root_tags),
            "folders": tree_folders,
            "tags_status": tags_status,
            "total_tags": len(self._tag_props),
            "total_folders": len(self._folders)
        }
