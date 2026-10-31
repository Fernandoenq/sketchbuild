"""
SketchBuild - Motor de Reexibição de Entidades Ocultas (Zero DLL / Pure Python)
Frente 184: Engenharia Reversa do SketchUp - SUDrawingElementSetHidden & Unhide (All / Selection / Last)

Implementa a funcionalidade oficial de reexibição do SketchUp Desktop Classic:
- Menu: Editar -> Reexibir -> Tudo (All)
- Menu: Editar -> Reexibir -> Último (Last)
- Menu: Editar -> Reexibir -> Selecionado (Selected)
Rastreia a pilha histórica de entidades ocultadas (stack de IDs) e altera
a propriedade de visibilidade (hidden=False) retornando contagens e entidades restauradas.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple


class UnhideEntitiesEngine:
    """Motor analítico de controle de visibilidade e reexibição de entidades do modelo."""

    @classmethod
    def hide_entities(
        cls,
        entities: List[Dict[str, Any]],
        target_ids: List[str],
        history_stack: Optional[List[List[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Oculta uma lista de entidades por ID e registra no topo da pilha de histórico.
        """
        if history_stack is None:
            history_stack = []

        target_set = set(target_ids)
        newly_hidden: List[str] = []

        for ent in entities:
            ent_id = str(ent.get("id", ent.get("instance_id", "")))
            if ent_id in target_set and not ent.get("hidden", False):
                ent["hidden"] = True
                newly_hidden.append(ent_id)

        if newly_hidden:
            history_stack.append(newly_hidden)

        return {
            "hidden_count": len(newly_hidden),
            "hidden_ids": newly_hidden,
            "history_depth": len(history_stack),
            "history_stack": history_stack,
        }

    @classmethod
    def unhide(
        cls,
        entities: List[Dict[str, Any]],
        scope: str = "all",  # "all", "last", "selection"
        target_ids: Optional[List[str]] = None,
        history_stack: Optional[List[List[str]]] = None,
    ) -> Dict[str, Any]:
        """
        Reexibe entidades de acordo com o escopo solicitado:
        - "all": Reexibe todas as entidades que estejam com hidden=True no modelo.
        - "last": Reexibe o último conjunto de entidades registrado no histórico.
        - "selection": Reexibe apenas os IDs especificados em target_ids.
        """
        if history_stack is None:
            history_stack = []

        unhidden_ids: List[str] = []
        scope_normalized = scope.lower().strip()

        if scope_normalized == "all":
            for ent in entities:
                if ent.get("hidden", False):
                    ent["hidden"] = False
                    ent_id = str(ent.get("id", ent.get("instance_id", "")))
                    unhidden_ids.append(ent_id)
            history_stack.clear()

        elif scope_normalized == "last":
            if history_stack:
                last_group = history_stack.pop()
                last_set = set(last_group)
                for ent in entities:
                    ent_id = str(ent.get("id", ent.get("instance_id", "")))
                    if ent_id in last_set and ent.get("hidden", False):
                        ent["hidden"] = False
                        unhidden_ids.append(ent_id)

        elif scope_normalized == "selection":
            req_set = set(target_ids or [])
            for ent in entities:
                ent_id = str(ent.get("id", ent.get("instance_id", "")))
                if ent_id in req_set and ent.get("hidden", False):
                    ent["hidden"] = False
                    unhidden_ids.append(ent_id)

            # Remove os restaurados das pilhas anteriores do histórico
            unhidden_set = set(unhidden_ids)
            for group in history_stack:
                group[:] = [gid for gid in group if gid not in unhidden_set]
            history_stack[:] = [g for g in history_stack if g]
        else:
            raise ValueError(f"Escopo de reexibição inválido: {scope}. Use 'all', 'last' ou 'selection'.")

        return {
            "unhidden_count": len(unhidden_ids),
            "unhidden_ids": unhidden_ids,
            "scope": scope_normalized,
            "remaining_hidden_count": sum(1 for e in entities if e.get("hidden", False)),
            "history_depth": len(history_stack),
            "history_stack": history_stack,
        }
