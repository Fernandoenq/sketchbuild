"""F5: Siga-me (Follow Me): varre uma face (perfil) ao longo de um caminho de arestas.

Cada vértice do caminho tem um plano de esquadro (bissetriz das duas direções) onde o anel do perfil
se apoia. Entre dois anéis nascem paredes planas. A face do perfil vira a tampa do começo, nasce
uma tampa no fim, e paredes vizinhas no mesmo plano se fundem (r14: V15 E20 F8, caminho fica solto).
O caminho fechado ainda não é suportado.
"""
from typing import Dict, List, Sequence

from core.topology.draw import _delta, _estado
from core.topology.model import Face, Point, Topology, _cross, _dot, _norm, _sub, _unit
from core.topology.pushpull import _aresta


def _cadeia(t: Topology, arestas: Sequence[int]) -> List[int]:
    """Ordena as arestas num caminho simples e aberto; devolve os vértices em ordem."""
    if not arestas:
        raise ValueError("caminho vazio")
    pares = []
    for e in arestas:
        if e not in t.edges:
            raise ValueError(f"aresta {e} não existe")
        pares.append(t.edges[e])
    grau: Dict[int, int] = {}
    for a, b in pares:
        grau[a] = grau.get(a, 0) + 1
        grau[b] = grau.get(b, 0) + 1
    if any(g > 2 for g in grau.values()):
        raise ValueError("o caminho se ramifica")
    pontas = [v for v, g in grau.items() if g == 1]
    if len(pontas) != 2:
        raise ValueError("o caminho precisa ser aberto (caminho fechado não é suportado)")
    cadeia = [min(pontas)]
    restantes = list(pares)
    while restantes:
        atual = cadeia[-1]
        achou = next(((a, b) for a, b in restantes if atual in (a, b)), None)
        if achou is None:
            raise ValueError("as arestas do caminho não são contínuas")
        restantes.remove(achou)
        cadeia.append(achou[1] if achou[0] == atual else achou[0])
    return cadeia


def siga_me(t: Topology, fid: int, arestas: Sequence[int]) -> Dict[str, dict]:
    if fid not in t.faces:
        raise ValueError(f"face {fid} não existe")
    cadeia = _cadeia(t, arestas)
    P = [t.verts[v] for v in cadeia]
    dirs = [_unit(_sub(P[k + 1], P[k])) for k in range(len(P) - 1)]
    if any(_norm(d) == 0 for d in dirs):
        raise ValueError("aresta de comprimento zero no caminho")
    f = t.faces[fid]
    antes = _estado(t)

    # esquadros: um por vértice do caminho (nas pontas, a direção do segmento)
    planos = [dirs[0]] + [_unit(tuple(dirs[k - 1][i] + dirs[k][i] for i in range(3))) for k in range(1, len(dirs))] + [dirs[-1]]
    for m, d in zip(planos[1:-1], dirs[1:]):
        if _norm(m) == 0:
            raise ValueError("o caminho volta sobre si mesmo")

    laços = f.loops()
    pts0 = [[t.verts[v] for v in lp] for lp in laços]
    # anel inicial: o perfil projetado no plano do primeiro vértice
    d0 = dirs[0]
    aneis: List[List[List[Point]]] = [[
        [tuple(q[i] - d0[i] * _dot(_sub(q, P[0]), d0) for i in range(3)) for q in lp] for lp in pts0
    ]]
    for k in range(len(dirs)):
        seg = _sub(P[k + 1], P[k])
        m, d = planos[k + 1], dirs[k]
        proximo = []
        for lp in aneis[-1]:
            novo = []
            for r in lp:
                rt = tuple(r[i] + seg[i] for i in range(3))
                s = _dot(_sub(P[k + 1], rt), m) / _dot(d, m)
                novo.append(tuple(rt[i] + d[i] * s for i in range(3)))
            proximo.append(novo)
        aneis.append(proximo)

    ids = [[[t._vertex(q) for q in lp] for lp in anel] for anel in aneis]
    paredes: List[int] = []
    for k in range(len(dirs)):
        for j, lp in enumerate(ids[k]):
            ref = tuple(sum(t.verts[v][i] for v in lp) / len(lp) for i in range(3))
            for i, a in enumerate(lp):
                b = lp[(i + 1) % len(lp)]
                a2, b2 = ids[k + 1][j][i], ids[k + 1][j][(i + 1) % len(lp)]
                _aresta(t, a, b)
                _aresta(t, a, a2)
                _aresta(t, a2, b2)
                m = tuple((t.verts[a][c] + t.verts[b][c]) / 2 for c in range(3))
                n = _unit(_cross(_sub(t.verts[b], t.verts[a]), dirs[k]))
                if (_dot(n, _sub(m, ref)) < 0) == (j == 0):
                    n = tuple(-x for x in n)
                fid_p = next(t._fid)
                t.faces[fid_p] = Face([a, b, b2, a2], [], n)
                paredes.append(fid_p)
    # tampas: o perfil fecha o começo e nasce uma tampa no fim
    f.normal = tuple(-x for x in dirs[0])
    f.outer[:] = ids[0][0]
    f.holes[:] = [list(h) for h in ids[0][1:]]
    fim = ids[-1]
    t.faces[next(t._fid)] = Face(list(fim[0]), [list(h) for h in fim[1:]], dirs[-1])
    _fundir_paredes_coplanares(t, paredes)
    return _delta(antes, _estado(t))


def _fundir_paredes_coplanares(t: Topology, paredes: Sequence[int]) -> None:
    """Apaga a aresta entre duas paredes no mesmo plano (o SketchUp as junta numa face só)."""
    alvo = set(paredes)
    mudou = True
    while mudou:
        mudou = False
        for eid in list(t.edges):
            if eid not in t.edges:
                continue
            fs = t.faces_of_edge(eid)
            if len(fs) != 2 or not all(x in alvo for x in fs):
                continue
            a, b = (t.faces[x] for x in fs)
            if abs(_dot(a.normal, b.normal)) < 1 - 1e-9:
                continue
            p = t.verts[a.outer[0]]
            if any(abs(_dot(_sub(t.verts[v], p), a.normal)) > t.tol for v in b.outer):
                continue
            antes = set(t.faces)
            t.erase_edge(eid)
            novas = set(t.faces) - antes
            alvo -= set(fs)
            alvo |= novas
            mudou = True
            break
