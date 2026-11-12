"""Suavizar arestas (Soften/Smooth Edges): bits 0x08 (suave) e 0x10 (lisa) do 0x07d3 da aresta."""
import math
from typing import Dict, Iterable, List, Sequence

from .model import Topology, _dot, _norm, _unit, _has_edge, _newell

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


def normais_suaves(t: Topology) -> Dict[int, Dict[int, tuple]]:
    """Normais por vértice para o sombreamento liso: {face: {vértice: normal}}.

    Em cada vértice, as faces ligadas por uma aresta lisa (bit 0x10, compartilhada por exatamente 2 faces) formam um
    grupo; a normal do grupo é a média das normais das faces ponderada pela área. Só entram vértices cujo grupo tem mais
    de uma face (os demais usam a normal da própria face)."""
    por_aresta: Dict[tuple, List[int]] = {}
    for fid, f in t.faces.items():
        for lp in f.loops():
            for i, a in enumerate(lp):
                b = lp[(i + 1) % len(lp)]
                por_aresta.setdefault((min(a, b), max(a, b)), []).append(fid)
    lisa_ids = {(min(a, b), max(a, b)) for e, (a, b) in t.edges.items() if t.eflags.get(e, 0) & LISA}
    lisas = {k for k, fs in por_aresta.items() if len(fs) == 2 and k in lisa_ids}
    peso = {fid: tuple(c for c in _newell([t.verts[v] for v in f.outer])) for fid, f in t.faces.items()}
    em_vertice: Dict[int, List[int]] = {}
    for fid, f in t.faces.items():
        for v in {v for lp in f.loops() for v in lp}:
            em_vertice.setdefault(v, []).append(fid)
    saida: Dict[int, Dict[int, tuple]] = {}
    for v, fs in em_vertice.items():
        pai = {f: f for f in fs}

        def raiz(x):
            while pai[x] != x:
                pai[x] = pai[pai[x]]
                x = pai[x]
            return x
        for k in lisas:
            if v in k:
                a, b = por_aresta[k]
                if a in pai and b in pai:
                    pai[raiz(a)] = raiz(b)
        grupos: Dict[int, List[int]] = {}
        for f in fs:
            grupos.setdefault(raiz(f), []).append(f)
        for g in grupos.values():
            if len(g) < 2:
                continue
            soma = tuple(sum(peso[f][i] for f in g) for i in range(3))
            if _norm(soma) <= 1e-12:
                continue
            n = _unit(soma)
            for f in g:
                saida.setdefault(f, {})[v] = n
    return saida
