"""Suavizar arestas (Soften/Smooth Edges): bits 0x08 (suave) e 0x10 (lisa) do 0x07d3 da aresta."""
import math
from typing import Dict, Iterable, List, Sequence

from .model import Face, Topology, _cross, _dot, _norm, _sub, _unit, _has_edge, _newell

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


def _canto(t: Topology, f: Face, v: int) -> float:
    """Ângulo do canto da face no vértice v, em graus (0 a 360), medido do lado de dentro do contorno externo."""
    lp = f.outer
    i = lp.index(v)
    p, q = t.verts[lp[i - 1]], t.verts[lp[(i + 1) % len(lp)]]
    c = t.verts[v]
    nw = _unit(_newell([t.verts[x] for x in lp]))
    a, b = _sub(q, c), _sub(p, c)
    ang = math.atan2(_dot(_cross(a, b), nw), _dot(a, b))
    return math.degrees(ang % (2 * math.pi))


def normais_suaves(t: Topology) -> Dict[int, Dict[int, tuple]]:
    """Normais por vértice para o sombreamento liso: {face: {vértice: normal}}.

    Regra lida na SketchUpAPI.dll (REA, `SUMeshHelperGetNormals` e a tabela de normais por vértice) e conferida contra
    ela em `tools/conferir_normais_sdk.py`:
      * só o bit lisa (0x10) liga as faces; o bit suave (0x08) sozinho não muda a normal;
      * as faces ligadas por aresta lisa, em cada vértice, formam um grupo; a normal do grupo é a soma das normais das
        faces ponderadas pelo ângulo do canto da face no vértice, normalizada;
      * a orientação de cada face é comparada com a da primeira do grupo (a de menor id) pelo sentido em que ela percorre
        a aresta lisa: se as duas percorrem no mesmo sentido, a face entra com a normal invertida e peso de 360 graus
        menos o ângulo do canto (um comportamento estranho, mas é o que a DLL faz);
      * cada face recebe a normal do grupo virada para o seu próprio lado (produto escalar negativo com a normal da face
        inverte).
    Só entram vértices do contorno externo; grupo de uma face só usa a normal da própria face."""
    por_aresta: Dict[tuple, List[tuple]] = {}
    for fid, f in t.faces.items():
        lp = f.outer
        for i, a in enumerate(lp):
            b = lp[(i + 1) % len(lp)]
            por_aresta.setdefault((min(a, b), max(a, b)), []).append((fid, a, b))
    lisa_ids = {(min(a, b), max(a, b)) for e, (a, b) in t.edges.items() if t.eflags.get(e, 0) & LISA}
    lisas = {k: u for k, u in por_aresta.items() if len(u) == 2 and k in lisa_ids}
    em_vertice: Dict[int, List[int]] = {}
    for fid, f in t.faces.items():
        for v in f.outer:
            em_vertice.setdefault(v, []).append(fid)
    saida: Dict[int, Dict[int, tuple]] = {}
    for v, fs in em_vertice.items():
        vizinhos: Dict[int, List[tuple]] = {f: [] for f in fs}
        for k, ((f1, a1, b1), (f2, a2, b2)) in lisas.items():
            if v in k and f1 in vizinhos and f2 in vizinhos:
                rel = -1 if (a1, b1) == (a2, b2) else 1  # mesmo sentido na aresta: orientações opostas
                vizinhos[f1].append((f2, rel))
                vizinhos[f2].append((f1, rel))
        visto: set = set()
        for seed in sorted(fs):
            if seed in visto:
                continue
            sinal = {seed: 1}
            pilha = [seed]
            while pilha:
                f = pilha.pop()
                for g, rel in vizinhos[f]:
                    if g not in sinal:
                        sinal[g] = sinal[f] * rel
                        pilha.append(g)
            visto |= set(sinal)
            if len(sinal) < 2:
                continue
            soma = [0.0, 0.0, 0.0]
            for f, s in sinal.items():
                face = t.faces[f]
                nw = _unit(_newell([t.verts[x] for x in face.outer]))
                ang = _canto(t, face, v)
                peso = ang if s > 0 else 360.0 - ang
                for i in range(3):
                    soma[i] += s * peso * nw[i]
            if _norm(tuple(soma)) <= 1e-12:
                continue
            r = _unit(tuple(soma))
            for f in sinal:
                n = t.faces[f].normal
                saida.setdefault(f, {})[v] = r if _dot(r, n) >= 0 else tuple(-c for c in r)
    return saida
