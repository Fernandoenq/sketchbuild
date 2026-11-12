"""Grafo de vértices, arestas e faces com as regras de modelagem do SketchUp.

Unidade: polegadas (a mesma dos dados golden de docs/f0). Regras cobertas, conforme
docs/F0-RESULTADOS.md: aresta nova divide aresta existente em T (não em X), aresta
entre dois vértices do mesmo laço divide a face, laço fechado vira face por
find_faces, face dentro de face vira furo, apagar aresta funde faces e remove
vértices colineares.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

Point = Tuple[float, float, float]


class Contador:
    """Contador de ids que se copia com copy.deepcopy (itertools.count perde isso no Python 3.14)."""

    def __init__(self, inicio: int = 1) -> None:
        self.proximo = inicio

    def __iter__(self):
        return self

    def __next__(self) -> int:
        v = self.proximo
        self.proximo += 1
        return v
TOL = 1e-3


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    return math.sqrt(_dot(a, a))


def _unit(a):
    n = _norm(a)
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 0.0, 0.0)


def _newell(pts: Sequence[Point]):
    nx = ny = nz = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    return (nx, ny, nz)


def _seg_param(p: Point, a: Point, b: Point, tol: float) -> Optional[float]:
    """Parâmetro t (0..1) de p sobre o segmento a-b, ou None se p não estiver nele."""
    ab = _sub(b, a)
    L2 = _dot(ab, ab)
    if L2 < 1e-12:
        return None
    t = _dot(_sub(p, a), ab) / L2
    q = (a[0] + ab[0] * t, a[1] + ab[1] * t, a[2] + ab[2] * t)
    if _norm(_sub(p, q)) > tol:
        return None
    return t


def _has_edge(lp: Sequence[int], a: int, b: int) -> bool:
    n = len(lp)
    return any({lp[i], lp[(i + 1) % n]} == {a, b} for i in range(n))


@dataclass
class Face:
    outer: List[int]
    holes: List[List[int]] = field(default_factory=list)
    normal: Point = (0.0, 0.0, 1.0)
    frente: Optional[str] = None  # nome do material (chave de Topology.materiais)
    verso: Optional[str] = None
    tag: Optional[str] = None  # nome da tag (chave de Topology.tags); None = Layer0 (sem tag)

    def loops(self) -> List[List[int]]:
        return [self.outer] + self.holes


class Topology:
    def __init__(self, tol: float = TOL):
        self.tol = tol
        self.verts: Dict[int, Point] = {}
        self.edges: Dict[int, Tuple[int, int]] = {}
        self.faces: Dict[int, Face] = {}
        self._vid, self._eid, self._fid = Contador(), Contador(), Contador()
        # curvas de arco (círculo/arco): id -> {centro, normal, raio, ang_ini, ang_fim (graus), arestas (em ordem)}.
        # Só metadado para gravar o registro 0x1397; se uma aresta membro sumir ou for dividida, a curva é ignorada.
        self.curvas: Dict[int, dict] = {}
        self._cid = Contador()
        # materiais: nome -> {"rgb": (r, g, b), "alpha": 0-255}. Faces apontam por nome (Face.frente / Face.verso).
        self.materiais: Dict[str, dict] = {}
        # tags (camadas): nome -> {"visivel": bool}. Faces apontam por nome (Face.tag).
        self.tags: Dict[str, dict] = {}
        self.etags: Dict[int, str] = {}  # tag de arestas soltas ou de borda: id da aresta -> nome da tag

    # -- consulta ---------------------------------------------------------------

    def counts(self) -> Dict[str, int]:
        return {"vertices": len(self.verts), "edges": len(self.edges), "faces": len(self.faces)}

    def face_area(self, fid: int) -> float:
        f = self.faces[fid]
        return abs(self._loop_area(f.outer)) - sum(abs(self._loop_area(h)) for h in f.holes)

    def faces_of_edge(self, eid: int) -> List[int]:
        a, b = self.edges[eid]
        return [fid for fid, f in self.faces.items() if any(_has_edge(lp, a, b) for lp in f.loops())]

    def edges_by_face_count(self) -> Dict[int, int]:
        out: Dict[int, int] = {}
        for eid in self.edges:
            n = len(self.faces_of_edge(eid))
            out[n] = out.get(n, 0) + 1
        return out

    def edge_between(self, a: int, b: int) -> Optional[int]:
        for eid, e in self.edges.items():
            if set(e) == {a, b}:
                return eid
        return None

    # -- vértices ---------------------------------------------------------------

    def _vertex(self, p: Point) -> int:
        for vid, q in self.verts.items():
            if _norm(_sub(p, q)) <= self.tol:
                return vid
        vid = next(self._vid)
        self.verts[vid] = (float(p[0]), float(p[1]), float(p[2]))
        return vid

    def _interior_param(self, p: Point, u: int, v: int) -> Optional[float]:
        a, b = self.verts[u], self.verts[v]
        t = _seg_param(p, a, b, self.tol)
        if t is None:
            return None
        L = _norm(_sub(b, a))
        return t if t * L > self.tol and (1 - t) * L > self.tol else None

    def _split_edges_at(self, vid: int) -> None:
        """Divide em T toda aresta que tem o vértice no seu interior."""
        p = self.verts[vid]
        for eid, (u, v) in list(self.edges.items()):
            if vid in (u, v) or self._interior_param(p, u, v) is None:
                continue
            del self.edges[eid]
            e1, e2 = next(self._eid), next(self._eid)
            if eid in self.etags:
                self.etags[e1] = self.etags[e2] = self.etags.pop(eid)
            self.edges[e1] = (u, vid)
            self.edges[e2] = (vid, v)
            self._dividir_na_curva(eid, e1, e2, (u, v))
            for f in self.faces.values():
                for lp in f.loops():
                    n = len(lp)
                    for i in range(n):
                        if {lp[i], lp[(i + 1) % n]} == {u, v}:
                            lp.insert(i + 1, vid)
                            break

    def _dividir_na_curva(self, eid: int, e1: int, e2: int, uv: Tuple[int, int]) -> None:
        """A aresta `eid` (u→v) virou e1 (u→vid) e e2 (vid→v): a curva que a continha passa a ter as duas, em ordem."""
        for c in self.curvas.values():
            ar = c["arestas"]
            if eid not in ar:
                continue
            i = ar.index(eid)
            vizinho = ar[i - 1] if i > 0 else (ar[i + 1] if len(ar) > 1 else None)
            u, v = uv
            # sentido do percurso: a ponta que a aresta compartilha com a anterior (ou a de trás da seguinte) é o início
            comeca_em_u = True
            if vizinho is not None and vizinho in self.edges:
                a, b = self.edges[vizinho]
                if i > 0:
                    comeca_em_u = u in (a, b)
                else:
                    comeca_em_u = v in (a, b)
            ar[i:i + 1] = [e1, e2] if comeca_em_u else [e2, e1]

    # -- arestas ----------------------------------------------------------------

    def add_edge(self, p: Point, q: Point) -> List[int]:
        """Cria a aresta, dividida pelos vértices que ela atravessa. Devolve os ids novos."""
        a, b = self._vertex(p), self._vertex(q)
        if a == b:
            return []
        self._split_edges_at(a)
        self._split_edges_at(b)
        pa, pb = self.verts[a], self.verts[b]
        mids = []
        for vid, pv in self.verts.items():
            if vid in (a, b):
                continue
            t = self._interior_param(pv, a, b)
            if t is not None:
                mids.append((t, vid))
        chain = [a] + [v for _, v in sorted(mids)] + [b]
        created = []
        for u, v in zip(chain, chain[1:]):
            if self.edge_between(u, v) is None:
                eid = next(self._eid)
                self.edges[eid] = (u, v)
                created.append(eid)
        for eid in created:
            self._split_faces_by_edge(eid)
        return created

    def _split_faces_by_edge(self, eid: int) -> None:
        a, b = self.edges[eid]
        for fid, f in list(self.faces.items()):
            lp = f.outer
            if a not in lp or b not in lp or _has_edge(lp, a, b):
                continue
            pm = tuple((x + y) / 2 for x, y in zip(self.verts[a], self.verts[b]))
            if not self._inside_face(f, pm):
                continue
            i, j = sorted((lp.index(a), lp.index(b)))
            l1, l2 = lp[i:j + 1], lp[j:] + lp[:i + 1]
            del self.faces[fid]
            n1, n2 = Face(l1, [], f.normal, f.frente, f.verso, f.tag), Face(l2, [], f.normal, f.frente, f.verso, f.tag)
            for h in f.holes:
                (n1 if self._point_in_loop(self.verts[h[0]], l1, f.normal) else n2).holes.append(h)
            self.faces[next(self._fid)] = n1
            self.faces[next(self._fid)] = n2
            return

    def erase_edge(self, eid: int) -> None:
        a, b = self.edges.pop(eid)
        self.etags.pop(eid, None)
        adjacent = [fid for fid, f in self.faces.items() if any(_has_edge(lp, a, b) for lp in f.loops())]
        if len(adjacent) == 2 and all(_has_edge(self.faces[f].outer, a, b) for f in adjacent):
            self._merge_faces(adjacent[0], adjacent[1], a, b)
        else:
            for fid in adjacent:
                del self.faces[fid]
        for vid in (a, b):
            self._heal_vertex(vid)

    def _merge_faces(self, f1: int, f2: int, a: int, b: int) -> None:
        A, B = self.faces.pop(f1), self.faces.pop(f2)

        def direction(lp):
            n = len(lp)
            for i in range(n):
                if (lp[i], lp[(i + 1) % n]) == (a, b):
                    return (a, b), i
                if (lp[i], lp[(i + 1) % n]) == (b, a):
                    return (b, a), i
            raise ValueError("aresta fora do laço")

        (x, y), i = direction(A.outer)
        la = A.outer[i + 1:] + A.outer[:i + 1]  # começa em y, termina em x
        lb = list(B.outer)
        if direction(lb)[0] == (x, y):
            lb.reverse()
        _, j = direction(lb)
        lb = lb[j + 1:] + lb[:j + 1]  # começa em x, termina em y
        self.faces[next(self._fid)] = Face(la + lb[1:-1], A.holes + B.holes, A.normal, A.frente, A.verso, A.tag)

    def _heal_vertex(self, vid: int) -> None:
        """Remove vértice de grau 2 colinear, juntando as duas arestas e ajustando os laços."""
        if vid not in self.verts:
            return
        inc = [(eid, e) for eid, e in self.edges.items() if vid in e]
        if not inc:
            if not any(vid in lp for f in self.faces.values() for lp in f.loops()):
                del self.verts[vid]
            return
        if len(inc) != 2:
            return
        (e1, (a1, b1)), (e2, (a2, b2)) = inc
        u = b1 if a1 == vid else a1
        w = b2 if a2 == vid else a2
        pu, pv, pw = self.verts[u], self.verts[vid], self.verts[w]
        if _norm(_cross(_sub(pv, pu), _sub(pw, pv))) > self.tol * max(_norm(_sub(pw, pu)), 1.0):
            return
        for f in self.faces.values():
            for lp in f.loops():
                if vid in lp:
                    lp.remove(vid)
        del self.edges[e1], self.edges[e2]
        novo = next(self._eid)
        self.edges[novo] = (u, w)
        if self.etags.get(e1) is not None and self.etags.get(e1) == self.etags.get(e2):
            self.etags[novo] = self.etags[e1]
        self.etags.pop(e1, None)
        self.etags.pop(e2, None)
        del self.verts[vid]

    # -- faces ------------------------------------------------------------------

    def _loop_area(self, lp: Sequence[int]) -> float:
        nw = _newell([self.verts[v] for v in lp])
        return 0.5 * _norm(nw)

    def add_face(self, points: Sequence[Point]) -> Optional[int]:
        """Cria as arestas do polígono e a face (furo se cair dentro de outra face)."""
        pts = [tuple(map(float, p)) for p in points]
        if len(pts) < 3:
            return None
        for i, p in enumerate(pts):
            self.add_edge(p, pts[(i + 1) % len(pts)])
        return self._register_face([self._vertex(p) for p in pts])

    def find_faces(self, eid: int) -> List[int]:
        """Cria faces para os laços planares fechados que contêm a aresta."""
        a, b = self.edges[eid]
        planes: List[Point] = []
        for e2, (u, v) in self.edges.items():
            if e2 == eid or not ({u, v} & {a, b}):
                continue
            c = _cross(_sub(self.verts[b], self.verts[a]), _sub(self.verts[v], self.verts[u]))
            if _norm(c) > 1e-9:
                n = _unit(c)
                if not any(abs(_dot(n, m)) > 1 - 1e-9 for m in planes):
                    planes.append(n)
        created = []
        for n in planes:
            for loop in self._planar_cycles_through(eid, n):
                fid = self._register_face(loop)
                if fid:
                    created.append(fid)
        return created

    def _planar_cycles_through(self, eid: int, n: Point) -> List[List[int]]:
        a0, b0 = self.edges[eid]
        origin = self.verts[a0]
        sel = [e for e in self.edges.values()
               if all(abs(_dot(_sub(self.verts[v], origin), n)) <= self.tol for v in e)]
        ux = _unit(_sub(self.verts[b0], origin))
        uy = _cross(n, ux)
        xy = {v: (_dot(_sub(p, origin), ux), _dot(_sub(p, origin), uy)) for v, p in self.verts.items()}
        adj: Dict[int, List[int]] = {}
        for u, v in sel:
            adj.setdefault(u, []).append(v)
            adj.setdefault(v, []).append(u)

        def ang(frm, to):
            return math.atan2(xy[to][1] - xy[frm][1], xy[to][0] - xy[frm][0])

        out = []
        for start in ((a0, b0), (b0, a0)):
            ring, (u, v) = [start[0]], start
            closed = False
            for _ in range(len(sel) * 2 + 2):
                ring.append(v)
                back = ang(v, u)
                cands = [w for w in adj[v] if w != u] or [u]
                # primeiro vizinho no sentido horário a partir da direção de volta
                w = min(cands, key=lambda c: (back - ang(v, c)) % (2 * math.pi) or 2 * math.pi)
                u, v = v, w
                if (u, v) == start:
                    closed = True
                    break
            if not closed:
                continue
            ring = ring[:-1]
            if len(set(ring)) != len(ring) or len(ring) < 3:
                continue
            k = len(ring)
            area = 0.5 * sum(xy[ring[i]][0] * xy[ring[(i + 1) % k]][1]
                             - xy[ring[(i + 1) % k]][0] * xy[ring[i]][1] for i in range(k))
            if area > self.tol:  # só o laço interno (anti-horário), nunca o contorno externo
                out.append(ring)
        return out

    def _register_face(self, loop: List[int]) -> Optional[int]:
        if len(loop) < 3:
            return None
        key = frozenset(loop)
        if any(frozenset(f.outer) == key for f in self.faces.values()):
            return None
        pts = [self.verts[v] for v in loop]
        n = _unit(_newell(pts))
        if _norm(n) == 0:
            return None
        # No SketchUp, face horizontal em z=0 nasce virada para baixo (golden r02/r03)
        if abs(abs(n[2]) - 1) < 1e-6 and all(abs(p[2]) <= self.tol for p in pts):
            n = (0.0, 0.0, -1.0)
        host = None
        for fid, f in self.faces.items():
            if set(f.outer) & set(loop) or abs(_dot(n, f.normal)) < 1 - 1e-9:
                continue
            if abs(_dot(_sub(pts[0], self.verts[f.outer[0]]), f.normal)) > self.tol:
                continue
            if all(self._point_in_loop(p, f.outer, f.normal) for p in pts) and \
                    not any(self._point_in_loop(p, h, f.normal) for h in f.holes for p in pts):
                if host is None or self._loop_area(f.outer) < self._loop_area(self.faces[host].outer):
                    host = fid
        if host is not None:
            self.faces[host].holes.append(list(loop))
        fid = next(self._fid)
        self.faces[fid] = Face(list(loop), [], n)
        return fid

    def _point_in_loop(self, p: Point, lp: Sequence[int], normal: Point) -> bool:
        pts = [self.verts[v] for v in lp]
        ux = _unit(_sub(pts[1], pts[0]))
        uy = _cross(normal, ux)
        o = pts[0]
        poly = [(_dot(_sub(q, o), ux), _dot(_sub(q, o), uy)) for q in pts]
        x, y = _dot(_sub(p, o), ux), _dot(_sub(p, o), uy)
        inside = False
        for i in range(len(poly)):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                inside = not inside
        return inside

    def _inside_face(self, f: Face, p: Point) -> bool:
        return self._point_in_loop(p, f.outer, f.normal) and \
            not any(self._point_in_loop(p, h, f.normal) for h in f.holes)
