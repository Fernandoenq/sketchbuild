"""
SketchBuild - Histórico de Operações Atômicas e Undo/Redo (Zero DLL / Pure Python)
Frente 85: Engenharia Reversa do SketchUp - SUModelStartOperation & SUModelCommitOperation

Implementa a pilha transacional reversível do SketchUp para operações atômicas de modelagem
(transformações, exclusões, pinturas, adições), permitindo desfazer (Ctrl+Z) e refazer (Ctrl+Y).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional


class UndoRedoCommandEngine:
    """Motor transacional de pilha de operações reversíveis (Undo/Redo Stack)."""

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self._undo_stack: List[Dict[str, Any]] = []
        self._redo_stack: List[Dict[str, Any]] = []

    def record_operation(
        self,
        name: str,
        action_type: str,
        target_id: str,
        before_state: Dict[str, Any],
        after_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Registra uma nova operação concluída no topo da pilha de Undo, invalidando o Redo.
        """
        op = {
            "op_id": f"op_{int(time.time() * 1000)}",
            "name": name,
            "action_type": action_type.upper(),
            "target_id": target_id,
            "before_state": before_state,
            "after_state": after_state,
            "timestamp": time.time(),
        }

        self._undo_stack.append(op)
        if len(self._undo_stack) > self.max_history:
            self._undo_stack.pop(0)

        # Toda nova operação limpa a pilha de redo
        self._redo_stack.clear()

        return {
            "entity_type": "UndoRedoAction",
            "action": "RECORD",
            "operation": op,
            "restore_state": after_state,
            "can_undo": True,
            "can_redo": False,
            "next_undo_name": op["name"],
            "next_redo_name": None,
            "status": f"OPERAÇÃO '{name}' REGISTRADA NA PILHA DE DESFAZER",
        }

    def undo(self) -> Optional[Dict[str, Any]]:
        """
        Desfaz a última operação registrada, retornando os dados para restauração do before_state.
        """
        if not self._undo_stack:
            return None

        op = self._undo_stack.pop()
        self._redo_stack.append(op)

        return {
            "entity_type": "UndoRedoAction",
            "action": "UNDO",
            "operation": op,
            "restore_state": op["before_state"],
            "can_undo": len(self._undo_stack) > 0,
            "can_redo": True,
            "next_undo_name": self._undo_stack[-1]["name"] if self._undo_stack else None,
            "next_redo_name": op["name"],
            "status": f"OPERAÇÃO '{op['name']}' DESFEITA COM SUCESSO",
        }

    def redo(self) -> Optional[Dict[str, Any]]:
        """
        Refaz a última operação desfeita, retornando os dados do after_state.
        """
        if not self._redo_stack:
            return None

        op = self._redo_stack.pop()
        self._undo_stack.append(op)

        return {
            "entity_type": "UndoRedoAction",
            "action": "REDO",
            "operation": op,
            "restore_state": op["after_state"],
            "can_undo": True,
            "can_redo": len(self._redo_stack) > 0,
            "next_undo_name": op["name"],
            "next_redo_name": self._redo_stack[-1]["name"] if self._redo_stack else None,
            "status": f"OPERAÇÃO '{op['name']}' REFEITA COM SUCESSO",
        }

    def get_history(self) -> Dict[str, Any]:
        """Retorna o estado atual das pilhas de Undo e Redo para a interface."""
        return {
            "entity_type": "UndoRedoStatus",
            "can_undo": len(self._undo_stack) > 0,
            "can_redo": len(self._redo_stack) > 0,
            "undo_name": self._undo_stack[-1]["name"] if self._undo_stack else None,
            "redo_name": self._redo_stack[-1]["name"] if self._redo_stack else None,
            "undo_count": len(self._undo_stack),
            "redo_count": len(self._redo_stack),
            "recent_operations": [op["name"] for op in reversed(self._undo_stack[-5:])],
        }


# Instância singleton padrão do projeto
DEFAULT_UNDO_REDO_ENGINE = UndoRedoCommandEngine()
