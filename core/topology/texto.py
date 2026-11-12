"""Textos livres: só dados; o gravador os escreve (FORMATO-SKP.md 7l)."""
import math
from typing import Optional, Sequence

from .model import Point, Topology

FONTE_PADRAO = 2  # id da primeira fonte do modelo em branco (a segunda é 3)


def texto_livre(t: Topology, texto: str, ponto: Point, tipo: int = 0, vetor: Optional[Sequence[float]] = None,
                seta: int = 0, fonte: int = FONTE_PADRAO) -> int:
    """Texto no `ponto`. `tipo` = tipo da linha de chamada (0, 1 ou 2, como na SketchUpAPI); `vetor` = vetor da chamada."""
    if not texto.strip():
        raise ValueError("texto: o texto não pode ser vazio")
    if tipo not in (0, 1, 2):
        raise ValueError("texto: tipo de linha de chamada deve ser 0, 1 ou 2")
    if seta < 0:
        raise ValueError("texto: tipo de seta não pode ser negativo")
    v = tuple(float(c) for c in (vetor or (0.0, 0.0, 0.0)))
    if any(not math.isfinite(c) for c in v) or any(not math.isfinite(c) for c in ponto):
        raise ValueError("texto: coordenada inválida")
    tid = next(t._gid)
    t.textos[tid] = {"texto": texto, "ponto": tuple(float(c) for c in ponto), "tipo": int(tipo), "vetor": v,
                     "seta": int(seta), "fonte": int(fonte)}
    return tid


def apagar_texto(t: Topology, ident: int) -> None:
    if ident not in t.textos:
        raise ValueError(f"texto {ident} não existe")
    del t.textos[ident]
