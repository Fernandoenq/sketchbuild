"""F3: Empurrar/Puxar (Push/Pull) sobre o núcleo de topologia.

Dois modos, escolhidos como o SketchUp faz:
- mover: a face faz parte de um sólido e todas as faces vizinhas são perpendiculares a ela
  (parede a parede). Ela só desliza ao longo da normal e as paredes esticam ou encolhem.
  Empurrar até zerar a altura colapsa o sólido (r05); passar para o outro lado não é suportado.
- extrusar: face solta ou coplanar com as vizinhas (r04, r11). Nascem paredes ao redor de cada
  laço e a face sobe ou desce. Face solta mantém a base (vira o fundo do sólido). Se a face
  desce e pousa dentro de outra face coplanar (furo vazado, r11), a face de destino ganha um
  furo e a face movida some.
`criar_nova=True` (Ctrl) força a extrusão e mantém a face original no lugar.
"""
from typing import Dict, List, Optional, Sequence

from core.topology.draw import _delta, _estado
from core.topology.model import Face, Point, Topology, _cross, _dot, _norm, _sub, _unit


def _vizinhas(t: Topology, fid: int) -> List[int]:
    """Faces que dividem alguma aresta com `fid`, uma entrada por aresta."""
    f = t.faces[fid]
    out: List[int] = []
    for lp in f.loops():
        for i, a in enumerate(lp):
            b = lp[(i + 1) % len(lp)]
            eid = t.edge_between(a, b)
            if eid is not None:
                out.extend(o for o in t.faces_of_edge(eid) if o != fid)
    return out


def _centro(t: Topology, lp: Sequence[int]) -> Point:
    return tuple(sum(t.verts[v][i] for v in lp) / len(lp) for i in range(3))


def _aresta(t: Topology, a: int, b: int) -> int:
    eid = t.edge_between(a, b)
    if eid is None:
        eid = next(t._eid)
        t.edges[eid] = (a, b)
    return eid


def _parede(t: Topology, a: int, b: int, a2: int, b2: int, dirv: Point, ref: Point, fora: bool,
            material: Optional[str] = None) -> Face:
    """Parede [a, b, b2, a2] com a normal para fora do laço externo (ou para dentro do furo)."""
    m = tuple((t.verts[a][i] + t.verts[b][i]) / 2 for i in range(3))
    c = _unit(_cross(_sub(t.verts[b], t.verts[a]), dirv))
    if (_dot(c, _sub(m, ref)) < 0) == fora:
        c = tuple(-x for x in c)
    return Face([a, b, b2, a2], [], c, material, material)  # assunção: a parede herda a cor da face puxada


def _mover(t: Topology, fid: int, v: Point, d: float) -> None:
    f = t.faces[fid]
    n = f.normal
    movem = {x for lp in f.loops() for x in lp}
    colapsa = set()
    parceiros = set()
    for p in movem:
        for a, b in t.edges.values():
            if p not in (a, b):
                continue
            q = b if a == p else a
            if q in movem:
                continue
            seg = _sub(t.verts[q], t.verts[p])
            if _norm(_cross(seg, n)) > t.tol * max(1.0, _norm(seg)):
                continue  # aresta que não é paralela à normal
            atual = _dot(seg, n)
            resto = atual - d
            if abs(resto) <= t.tol:
                colapsa.add(p)
                parceiros.add(q)
            elif resto * atual < 0:
                raise ValueError("o Push/Pull passa do outro lado do sólido (não suportado)")
    if colapsa and colapsa != movem:
        raise ValueError("colapso parcial do sólido (não suportado)")
    for p in movem:
        t.verts[p] = tuple(t.verts[p][i] + v[i] for i in range(3))
    if colapsa:
        _fundir_coincidentes(t, movem | parceiros)


def _fundir_coincidentes(t: Topology, afetados: set) -> None:
    """Junta vértices na mesma posição, tira arestas e faces degeneradas e as faces opostas coincidentes."""
    destino: Dict[int, int] = {}
    ids = sorted(t.verts)
    for k, vid in enumerate(ids):
        for outro in ids[:k]:
            if outro not in destino and _norm(_sub(t.verts[vid], t.verts[outro])) <= t.tol:
                destino[vid] = outro
                break
    for vid in destino:
        del t.verts[vid]
    for eid, (a, b) in list(t.edges.items()):
        t.edges[eid] = (destino.get(a, a), destino.get(b, b))
    for f in t.faces.values():
        for lp in f.loops():
            lp[:] = [destino.get(x, x) for x in lp]
    vistas = set()
    for eid, (a, b) in list(t.edges.items()):
        chave = frozenset((a, b))
        if a == b or chave in vistas:
            del t.edges[eid]
        else:
            vistas.add(chave)
    for fid, f in list(t.faces.items()):
        lp = f.outer
        lp[:] = [x for i, x in enumerate(lp) if x != lp[i - 1]]
        if len(set(lp)) < 3:
            del t.faces[fid]
    grupos: Dict[frozenset, List[int]] = {}
    for fid, f in t.faces.items():
        grupos.setdefault(frozenset(f.outer), []).append(fid)
    for fids in grupos.values():
        if len(fids) > 1:  # duas faces coincidentes e opostas se anulam
            for fid in fids:
                del t.faces[fid]
    ocupadas = {
        frozenset((lp[i], lp[(i + 1) % len(lp)]))
        for f in t.faces.values() for lp in f.loops() for i in range(len(lp))
    }
    # o sólido colapsou: arestas do colapso sem nenhuma face saem junto (r05: V0 E0 F0)
    for eid, (a, b) in list(t.edges.items()):
        if frozenset((a, b)) not in ocupadas and a in afetados and b in afetados:
            del t.edges[eid]
    for vid in list(t.verts):
        if vid in afetados and not any(vid in e for e in t.edges.values()):
            del t.verts[vid]


def _extrusar(t: Topology, fid: int, v: Point, manter_base: bool) -> None:
    f = t.faces[fid]
    dirv = _unit(v)
    estava_presa = any(True for _ in _vizinhas(t, fid))
    novos: Dict[int, int] = {}
    for lp in f.loops():
        for x in lp:
            novos[x] = t._vertex(tuple(t.verts[x][i] + v[i] for i in range(3)))
    paredes: List[Face] = []
    for k, lp in enumerate(f.loops()):
        ref = _centro(t, lp)
        for i, a in enumerate(lp):
            b = lp[(i + 1) % len(lp)]
            _aresta(t, a, b)
            _aresta(t, novos[a], novos[b])
            _aresta(t, a, novos[a])
            paredes.append(_parede(t, a, b, novos[a], novos[b], dirv, ref, fora=(k == 0), material=f.frente))
    for w in paredes:
        t.faces[next(t._fid)] = w
    topo = [novos[x] for x in f.outer]
    pousa = None
    if not f.holes and not manter_base:
        for oid, o in t.faces.items():
            if oid == fid or abs(_dot(o.normal, f.normal)) < 1 - 1e-9:
                continue
            if abs(_dot(_sub(t.verts[topo[0]], t.verts[o.outer[0]]), o.normal)) > t.tol:
                continue
            if o.outer != topo and all(t._inside_face(o, t.verts[x]) for x in topo):
                pousa = oid
                break
    if pousa is not None:  # furo vazado: a face de destino ganha o furo, a movida some
        t.faces[pousa].holes.append(list(topo))
        del t.faces[fid]
        return
    novo = Face(topo, [[novos[x] for x in h] for h in f.holes], dirv, f.frente, f.verso, f.tag, f.uv)
    if manter_base or not estava_presa:  # a original vira a base do sólido
        f.normal = tuple(-x for x in dirv)
    else:
        del t.faces[fid]
    t.faces[next(t._fid)] = novo


def empurrar(t: Topology, fid: int, distancia: float, criar_nova: bool = False) -> Dict[str, dict]:
    """Empurra (negativo) ou puxa (positivo) a face `fid` ao longo da normal. Devolve o delta."""
    if fid not in t.faces:
        raise ValueError(f"face {fid} não existe")
    if abs(distancia) <= t.tol:
        raise ValueError("distância nula")
    antes = _estado(t)
    f = t.faces[fid]
    v = tuple(x * distancia for x in f.normal)
    vizinhas = _vizinhas(t, fid)
    perpendiculares = bool(vizinhas) and all(abs(_dot(t.faces[o].normal, f.normal)) < 1e-6 for o in vizinhas)
    if perpendiculares and not criar_nova:
        _mover(t, fid, v, distancia)
    else:
        _extrusar(t, fid, v, criar_nova)
    return _delta(antes, _estado(t))
