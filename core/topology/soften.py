"""Suavizar arestas (Soften/Smooth Edges): bits 0x08 (suave) e 0x10 (lisa) do 0x07d3 da aresta."""
import math
from typing import Dict, Iterable, List, Sequence

from .model import Topology, _dot, _norm, _unit, _has_edge

SUAVE = 0x08
LISA = 0x10


def definir(t: Topology, arestas: Sequence[int], suave: bool = True, lisa: bool = True) -> int:
    """Liga (ou desliga) suave e lisa nas arestas dadas. Devolve quantas mudaram."""
    faltam = [e for e in arestas if e not in t.edges]
    if faltam:
        raise ValueError(f"arestas inexistentes: {faltam}")
    mascara = (SUAVE if suave else 0) | (LISA if lisa else 0)
    mudou = 0
    for e in arestas:
        antes = t.eflags.get(e, 0)
        depois = antes | mascara if (suave or lisa) else antes
        if depois != antes:
            t.eflags[e] = depois
            mudou += 1
    return mudou


def limpar(t: Topology, arestas: Sequence[int]) -> int:
    """Tira suave e lisa."""
    mudou = 0
    for e in arestas:
        antes = t.eflags.get(e, 0)
        depois = antes & ~(SUAVE | LISA)
        if depois != antes:
            mudou += 1
        if depois:
            t.eflags[e] = depois
        else:
            t.eflags.pop(e, None)
    return mudou


def por_angulo(t: Topology, angulo_max: float, arestas: Iterable[int] | None = None) -> List[int]:
    """Suaviza as arestas entre duas faces cujo ângulo entre as normais é <= `angulo_max` graus (o controle deslizante
    do SketchUp). Aresta com 1 face, 3 ou mais faces, ou faces coplanares fora do alcance não muda. Devolve as ids."""
    if not 0 <= angulo_max <= 180:
        raise ValueError("ângulo entre 0 e 180 graus")
    alvo = set(t.edges) if arestas is None else set(arestas)
    faces_da_aresta: Dict[int, List[int]] = {}
    for e in alvo:
        a, b = t.edges[e]
        faces_da_aresta[e] = [fid for fid, f in t.faces.items() if any(_has_edge(lp, a, b) for lp in f.loops())]
    mudadas = []
    limite = math.cos(math.radians(angulo_max))
    for e, fs in faces_da_aresta.items():
        if len(fs) != 2:
            continue
        n1, n2 = _unit(t.faces[fs[0]].normal), _unit(t.faces[fs[1]].normal)
        if _dot(n1, n2) >= limite - 1e-12:
            t.eflags[e] = t.eflags.get(e, 0) | SUAVE | LISA
            mudadas.append(e)
    return sorted(mudadas)
