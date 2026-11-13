"""F4: edição sobre o núcleo de topologia: Mover, Rotacionar, Escalar e Offset.

Mover/Rotacionar/Escalar transformam os vértices da seleção (faces e arestas viram os seus
vértices). A operação é atômica: se alguma face afetada deixar de ser plana, ou dois vértices
colidirem, tudo volta ao estado anterior e a chamada dá erro. Offset cria um laço paralelo
dentro (negativo) ou fora (positivo) da face, como o SketchUp.
"""
import math
from typing import Dict, Iterable, List, Sequence, Set

from core.topology.draw import _delta, _estado
from core.topology.model import Face, Point, Topology, _cross, _dot, _newell, _norm, _sub, _unit


def vertices_da_selecao(t: Topology, vertices: Iterable[int] = (), arestas: Iterable[int] = (),
                        faces: Iterable[int] = ()) -> Set[int]:
    out: Set[int] = set()
    for v in vertices:
        if v not in t.verts:
            raise ValueError(f"vértice {v} não existe")
        out.add(v)
    for e in arestas:
        if e not in t.edges:
            raise ValueError(f"aresta {e} não existe")
        out.update(t.edges[e])
    for f in faces:
        if f not in t.faces:
            raise ValueError(f"face {f} não existe")
        for lp in t.faces[f].loops():
            out.update(lp)
    if not out:
        raise ValueError("seleção vazia")
    return out


def _centroide(t: Topology, ids: Iterable[int]) -> Point:
    pts = [t.verts[i] for i in ids]
    return tuple(sum(p[k] for p in pts) / len(pts) for k in range(3))


def _plana(t: Topology, f: Face) -> bool:
    pts = [t.verts[v] for v in f.outer]
    n = _unit(_newell(pts))
    if _norm(n) == 0:
        return False
    return all(abs(_dot(_sub(t.verts[v], pts[0]), n)) <= t.tol * 10 for lp in f.loops() for v in lp)


def _aplicar(t: Topology, ids: Set[int], mapa) -> None:
    """Move os vértices por `mapa(ponto) -> ponto`; desfaz tudo se o grafo ficar inválido."""
    velhos = {i: t.verts[i] for i in ids}
    normais = {fid: f.normal for fid, f in t.faces.items()}
    for i in ids:
        t.verts[i] = tuple(float(x) for x in mapa(t.verts[i]))
    try:
        novos = list(t.verts.items())
        for k, (a, pa) in enumerate(novos):
            if a not in ids:
                continue
            for b, pb in novos:
                if b != a and _norm(_sub(pa, pb)) <= t.tol:
                    raise ValueError("a operação junta dois vértices (não suportado)")
        for fid, f in t.faces.items():
            if not any(v in ids for lp in f.loops() for v in lp):
                continue
            if not _plana(t, f):
                raise ValueError(f"a face {fid} deixaria de ser plana (não suportado)")
            n = _unit(_newell([t.verts[v] for v in f.outer]))
            f.normal = n if _dot(n, normais[fid]) >= 0 else tuple(-x for x in n)
    except ValueError:
        for i, p in velhos.items():
            t.verts[i] = p
        for fid, n in normais.items():
            t.faces[fid].normal = n
        raise


def mover(t: Topology, ids: Set[int], vetor: Point) -> Dict[str, dict]:
    if _norm(vetor) <= t.tol:
        raise ValueError("deslocamento nulo")
    antes = _estado(t)
    _aplicar(t, ids, lambda p: tuple(p[k] + vetor[k] for k in range(3)))
    return _delta(antes, _estado(t))


def _rodrigues(p: Point, c: Point, eixo: Point, ang: float) -> Point:
    k = _unit(eixo)
    v = _sub(p, c)
    cs, sn = math.cos(ang), math.sin(ang)
    kv = _cross(k, v)
    kd = _dot(k, v)
    return tuple(c[i] + v[i] * cs + kv[i] * sn + k[i] * kd * (1 - cs) for i in range(3))


def rotacionar(t: Topology, ids: Set[int], angulo_graus: float, eixo: Point = (0, 0, 1),
               centro: Point = None) -> Dict[str, dict]:
    if _norm(eixo) == 0:
        raise ValueError("eixo nulo")
    if abs(angulo_graus) < 1e-9:
        raise ValueError("ângulo nulo")
    antes = _estado(t)
    c = centro if centro is not None else _centroide(t, ids)
    ang = math.radians(angulo_graus)
    _aplicar(t, ids, lambda p: _rodrigues(p, c, eixo, ang))
    return _delta(antes, _estado(t))


def escalar(t: Topology, ids: Set[int], fator, centro: Point = None) -> Dict[str, dict]:
    """`fator` é um número (uniforme) ou (fx, fy, fz). Fator zero ou negativo é recusado."""
    f = (fator, fator, fator) if isinstance(fator, (int, float)) else tuple(fator)
    if len(f) != 3 or any(x <= 0 for x in f):
        raise ValueError("o fator de escala precisa ser positivo")
    if all(abs(x - 1) < 1e-12 for x in f):
        raise ValueError("fator 1 não muda nada")
    antes = _estado(t)
    c = centro if centro is not None else _centroide(t, ids)
    _aplicar(t, ids, lambda p: tuple(c[k] + (p[k] - c[k]) * f[k] for k in range(3)))
    return _delta(antes, _estado(t))


def _laco_paralelo(t: Topology, lp: Sequence[int], normal: Point, d: float) -> List[Point]:
    """Laço deslocado `d` para o lado esquerdo das arestas (em relação à normal), com quinas em esquadro."""
    pts = [t.verts[v] for v in lp]
    n = len(pts)
    linhas = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dire = _unit(_sub(b, a))
        esq = _cross(normal, dire)
        linhas.append((tuple(a[k] + esq[k] * d for k in range(3)), dire))
    out = []
    for i in range(n):
        p1, d1 = linhas[i - 1]
        p2, d2 = linhas[i]
        c = _cross(d1, d2)
        den = _dot(c, c)
        if den < 1e-12:  # arestas consecutivas paralelas
            out.append(p2)
            continue
        s = _dot(_cross(_sub(p2, p1), d2), c) / den
        out.append(tuple(p1[k] + d1[k] * s for k in range(3)))
    for i in range(n):  # aresta que encolheu até sumir ou virou do avesso: o contorno colapsou
        novo = _sub(out[(i + 1) % n], out[i])
        if _dot(novo, linhas[i][1]) <= 1e-9:
            raise ValueError("o offset colapsa o contorno: a distância é maior que a espessura da face")
    return out


def offset(t: Topology, fid: int, distancia: float) -> Dict[str, dict]:
    """Offset da face: negativo vai para dentro, positivo para fora. Todos os laços acompanham."""
    if fid not in t.faces:
        raise ValueError(f"face {fid} não existe")
    if abs(distancia) <= t.tol:
        raise ValueError("distância nula")
    antes = _estado(t)
    f = t.faces[fid]
    n = f.normal
    # laço externo anti-horário em relação à normal => esquerda das arestas é o interior
    def ccw(lp):
        return _dot(_newell([t.verts[v] for v in lp]), n) > 0
    interior = -distancia  # esquerda positiva = para dentro; distancia<0 (para dentro) => esquerda +
    novos: List[List[Point]] = []
    for k, lp in enumerate(f.loops()):
        lado = (1 if ccw(lp) else -1) * interior
        if k > 0:  # furo: "para dentro da face" é para fora do furo
            lado = -lado
        novos.append(_laco_paralelo(t, lp, n, lado))
    ref = novos[0]
    if distancia < 0:  # para dentro: o laço novo vira face e furo da original (add_face faz isso)
        for lp in novos[1:]:
            t.add_face(lp)
        nova = t.add_face(ref)
        if nova is None:
            raise ValueError("o offset não gerou face")
    else:  # para fora: a nova face é maior e a original vira o furo dela
        for lp in novos[1:]:
            t.add_face(lp)
        for i, p in enumerate(ref):
            t.add_edge(p, ref[(i + 1) % len(ref)])
        ids = [t._vertex(p) for p in ref]
        nova_id = next(t._fid)
        t.faces[nova_id] = Face(ids, [list(f.outer)], n)
    return _delta(antes, _estado(t))


def apagar(t: Topology, arestas: Iterable[int] = (), faces: Iterable[int] = ()) -> Dict[str, dict]:
    """Ferramenta Apagar / tecla Delete, como no SketchUp.

    Apagar uma aresta leva junto as faces que a usam (no contorno ou em furo) e, se ela faz parte de uma curva
    (círculo, arco, Bézier, polígono, mão livre), a curva inteira. Apagar uma face deixa as arestas dela. Vértice que
    não é mais usado por aresta nem face some. Sem nada a apagar dá erro."""
    arestas, faces = list(dict.fromkeys(arestas)), list(dict.fromkeys(faces))
    faltam = [e for e in arestas if e not in t.edges] + [f for f in faces if f not in t.faces]
    if faltam:
        raise ValueError(f"não existem: {faltam}")
    if not arestas and not faces:
        raise ValueError("apagar: nada selecionado")
    antes = _estado(t)
    alvo = set(arestas)
    for cid in [c for c, cv in t.curvas.items() if alvo & set(cv["arestas"])]:
        alvo |= set(t.curvas[cid]["arestas"])
        del t.curvas[cid]
    por_apagar = set(faces)
    for e in alvo:
        a, b = t.edges[e]
        for fid, f in t.faces.items():
            if any({lp[i], lp[(i + 1) % len(lp)]} == {a, b} for lp in f.loops() for i in range(len(lp))):
                por_apagar.add(fid)
    for fid in por_apagar:
        del t.faces[fid]
    tocados = set()
    for e in alvo:
        tocados |= set(t.edges.pop(e))
        t.etags.pop(e, None)
        t.eflags.pop(e, None)
    for v in tocados:
        if v in t.verts and not any(v in e for e in t.edges.values()) \
                and not any(v in lp for f in t.faces.values() for lp in f.loops()):
            del t.verts[v]
    return _delta(antes, _estado(t))
