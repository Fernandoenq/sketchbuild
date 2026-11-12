"""F5: Intersect Faces. Cada par de faces em planos diferentes que se cruzam ganha a aresta da
interseção; as arestas dividem as faces como qualquer aresta desenhada (r06) e laços fechados
viram face (furo na face de fora, r10). Opera na topologia inteira ou só nas faces dadas."""
from typing import Dict, Iterable, List, Optional, Tuple

from core.topology.draw import _delta, _estado
from core.topology.model import Face, Point, Topology, _cross, _dot, _norm, _sub, _unit, _seg_param


def _linha_dos_planos(p1: Point, n1: Point, p2: Point, n2: Point) -> Optional[Tuple[Point, Point]]:
    d = _cross(n1, n2)
    den = _dot(d, d)
    if den < 1e-12:
        return None  # planos paralelos
    d1, d2 = _dot(n1, p1), _dot(n2, p2)
    ponto = tuple(
        (d1 * _cross(n2, d)[i] + d2 * _cross(d, n1)[i]) / den for i in range(3)
    )
    return ponto, _unit(d)


def _intervalos(t: Topology, f: Face, p0: Point, d: Point) -> List[Tuple[float, float]]:
    """Trechos da reta (p0 + s*d) que estão dentro da face (com furos)."""
    cortes: List[float] = []
    for lp in f.loops():
        for i, a in enumerate(lp):
            b = lp[(i + 1) % len(lp)]
            pa, pb = t.verts[a], t.verts[b]
            e = _sub(pb, pa)
            c = _cross(d, e)
            den = _dot(c, c)
            if den < 1e-14:
                continue  # aresta paralela à reta
            w = _sub(pa, p0)
            s = _dot(_cross(w, e), c) / den
            u = _dot(_cross(w, d), c) / den
            if -t.tol <= u * _norm(e) and u <= 1 + t.tol / max(_norm(e), 1e-9):
                ponto_a = tuple(p0[k] + d[k] * s for k in range(3))
                ponto_b = tuple(pa[k] + e[k] * u for k in range(3))
                if _norm(_sub(ponto_a, ponto_b)) <= t.tol * 10:
                    cortes.append(s)
    cortes.sort()
    limpos: List[float] = []
    for s in cortes:
        if not limpos or s - limpos[-1] > t.tol:
            limpos.append(s)
    out = []
    for s0, s1 in zip(limpos, limpos[1:]):
        meio = tuple(p0[k] + d[k] * (s0 + s1) / 2 for k in range(3))
        if t._inside_face(f, meio):
            out.append((s0, s1))
    return out


def _sobrepoe(a: List[Tuple[float, float]], b: List[Tuple[float, float]], tol: float):
    for a0, a1 in a:
        for b0, b1 in b:
            lo, hi = max(a0, b0), min(a1, b1)
            if hi - lo > tol:
                yield lo, hi


def intersectar(t: Topology, faces: Iterable[int] = None) -> Dict[str, dict]:
    """Cria as arestas de interseção entre as faces (todas, ou só entre as dadas)."""
    antes = _estado(t)
    ids = list(faces) if faces is not None else list(t.faces)
    for f in ids:
        if f not in t.faces:
            raise ValueError(f"face {f} não existe")
    segmentos: List[Tuple[Point, Point]] = []
    for i, fa in enumerate(ids):
        for fb in ids[i + 1:]:
            A, B = t.faces[fa], t.faces[fb]
            if abs(abs(_dot(A.normal, B.normal)) - 1) < 1e-9:
                continue  # paralelas ou coplanares
            linha = _linha_dos_planos(t.verts[A.outer[0]], A.normal, t.verts[B.outer[0]], B.normal)
            if linha is None:
                continue
            p0, d = linha
            for lo, hi in _sobrepoe(_intervalos(t, A, p0, d), _intervalos(t, B, p0, d), t.tol):
                segmentos.append((
                    tuple(p0[k] + d[k] * lo for k in range(3)),
                    tuple(p0[k] + d[k] * hi for k in range(3)),
                ))
    antes_arestas = set(t.edges)
    for a, b in segmentos:
        t.add_edge(a, b)
    novas = {e for e in t.edges if e not in antes_arestas}
    for a, b in segmentos:  # aresta que já existia sobre o corte também divide as faces que ela atravessa
        for eid, (u, v) in t.edges.items():
            if eid not in novas and all(_seg_param(t.verts[w], a, b, t.tol) is not None for w in (u, v)):
                novas.add(eid)
    for eid in sorted(novas):
        if eid in t.edges:
            t.find_faces(eid)
    return _delta(antes, _estado(t))
