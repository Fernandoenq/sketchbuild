"""F6: histórico (desfazer e refazer) da Cena, com log de operações.

Cada operação que muda a cena roda por `executar`: o estado anterior é guardado (cópia profunda),
a operação roda e, se der erro, a cena volta sozinha ao que era. `desfazer` e `refazer` trocam o
estado atual pelo guardado, então qualquer sequência de N operações desfeita e refeita volta
exatamente ao mesmo estado. O log guarda nome e parâmetros de cada operação (para depurar e,
no futuro, repetir a sequência).
"""
import copy
import time
from typing import Any, Callable, Dict, List, Optional

from core.topology.cena import Cena

LIMITE = 100


class Historico:
    def __init__(self, cena: Cena, limite: int = LIMITE) -> None:
        self.cena = cena
        self.limite = limite
        self._desfazer: List[Dict[str, Any]] = []  # {"nome", "params", "antes"}
        self._refazer: List[Dict[str, Any]] = []
        self.log: List[Dict[str, Any]] = []

    @staticmethod
    def _foto(cena: Cena) -> Cena:
        return copy.deepcopy(cena)

    def _restaurar(self, foto: Cena) -> None:
        self.cena.__dict__.clear()
        self.cena.__dict__.update(copy.deepcopy(foto).__dict__)

    def executar(self, nome: str, params: Optional[dict], operacao: Callable[[], Any]) -> Any:
        antes = self._foto(self.cena)
        try:
            resultado = operacao()
        except Exception:
            self._restaurar(antes)
            raise
        self._desfazer.append({"nome": nome, "params": params or {}, "antes": antes})
        del self._desfazer[: -self.limite]
        self._refazer.clear()
        self.log.append({"operacao": nome, "params": params or {}, "quando": time.time()})
        return resultado

    def pode_desfazer(self) -> bool:
        return bool(self._desfazer)

    def pode_refazer(self) -> bool:
        return bool(self._refazer)

    def desfazer(self) -> str:
        if not self._desfazer:
            raise ValueError("nada para desfazer")
        passo = self._desfazer.pop()
        self._refazer.append({"nome": passo["nome"], "params": passo["params"], "antes": self._foto(self.cena)})
        self._restaurar(passo["antes"])
        self.log.append({"operacao": "desfazer:" + passo["nome"], "params": {}, "quando": time.time()})
        return passo["nome"]

    def refazer(self) -> str:
        if not self._refazer:
            raise ValueError("nada para refazer")
        passo = self._refazer.pop()
        self._desfazer.append({"nome": passo["nome"], "params": passo["params"], "antes": self._foto(self.cena)})
        self._restaurar(passo["antes"])
        self.log.append({"operacao": "refazer:" + passo["nome"], "params": {}, "quando": time.time()})
        return passo["nome"]

    def resumo(self) -> Dict[str, Any]:
        return {
            "pode_desfazer": self.pode_desfazer(),
            "pode_refazer": self.pode_refazer(),
            "passos_desfazer": [p["nome"] for p in self._desfazer],
            "passos_refazer": [p["nome"] for p in self._refazer],
            "log": [{"operacao": x["operacao"], "params": x["params"]} for x in self.log[-50:]],
        }
