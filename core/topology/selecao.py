"""M13: seleção sobre o núcleo (selecionar tudo, inverter, conectados, por tag/material, janela e cruzamento).

Cada função devolve {"faces": [...], "edges": [...], "vertices": [...]} com ids ordenados. Não altera o modelo."""
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from .model import Topology


def _saida(faces: Iterable[int], edges: Iterable[int], verts: Iterable[int] = ()) -> Dict[str, List[int]]:
    return {"faces": sorted(set(faces)), "edges": sorted(set(edges)), "vertices": sorted(set(verts))}


def _arestas_da_face(t: Topology, fid: int) -> Set[int]:
    out = set()
    for lp in t.faces[fid].loops():
        for i, a in enumerate(lp):
            e = t.edge_between(a, lp[(i + 1) % len(lp)])
            if e is not None:
                out.add(e)
    return out


def tudo(t: Topology) -> Dict[str, List[int]]:
    return _saida(t.faces, t.edges)


def inverter(t: Topology, faces: Iterable[int] = (), edges: Iterable[int] = ()) -> Dict[str, List[int]]:
    """Troca o que está selecionado pelo que não está (faces e arestas separadamente)."""
    return _saida(set(t.faces) - set(faces), set(t.edges) - set(edges))


def arestas_das_faces(t: Topology, faces: Iterable[int]) -> Dict[str, List[int]]:
    """Duplo clique na face: a face e todas as arestas do seu contorno (e furos)."""
    faces = [f for f in faces if f in t.faces]
    return _saida(faces, set().union(*(_arestas_da_face(t, f) for f in faces)) if faces else ())


def faces_das_arestas(t: Topology, edges: Iterable[int]) -> Dict[str, List[int]]:
    """Faces cujo contorno inteiro (com furos) está nas arestas dadas."""
    es = {e for e in edges if e in t.edges}
    return _saida([f for f in t.faces if _arestas_da_face(t, f) and _arestas_da_face(t, f) <= es], es)


def conectados(t: Topology, faces: Iterable[int] = (), edges: Iterable[int] = ()) -> Dict[str, List[int]]:
    """Triplo clique: tudo o que se liga à seleção por vértices compartilhados."""
    sementes: Set[int] = set()
    for f in faces:
        if f not in t.faces:
            raise ValueError(f"face {f} não existe")
        sementes.update(v for lp in t.faces[f].loops() for v in lp)
    for e in edges:
        if e not in t.edges:
            raise ValueError(f"aresta {e} não existe")
        sementes.update(t.edges[e])
    vizinhos: Dict[int, Set[int]] = {}
    for a, b in t.edges.values():
        vizinhos.setdefault(a, set()).add(b)
        vizinhos.setdefault(b, set()).add(a)
    for f in t.faces.values():  # face sem aresta registrada ainda liga seus vértices
        for lp in f.loops():
            for i, a in enumerate(lp):
                b = lp[(i + 1) % len(lp)]
                vizinhos.setdefault(a, set()).add(b)
                vizinhos.setdefault(b, set()).add(a)
    vistos, pilha = set(sementes), list(sementes)
    while pilha:
        for w in vizinhos.get(pilha.pop(), ()):
            if w not in vistos:
                vistos.add(w)
                pilha.append(w)
    return _saida([f for f, x in t.faces.items() if x.outer and x.outer[0] in vistos],
                  [e for e, (a, b) in t.edges.items() if a in vistos], vistos)


def por_tag(t: Topology, nome: str) -> Dict[str, List[int]]:
    if nome not in t.tags:
        raise ValueError(f"tag {nome!r} não existe")
    return _saida([f for f, x in t.faces.items() if x.tag == nome], [e for e, n in t.etags.items() if n == nome])


def por_material(t: Topology, nome: str) -> Dict[str, List[int]]:
    """Faces pintadas com o material (frente ou verso)."""
    if nome not in t.materiais:
        raise ValueError(f"material {nome!r} não existe")
    return _saida([f for f, x in t.faces.items() if nome in (x.frente, x.verso)], ())


def _projetar(matriz: Sequence[float], p) -> Tuple[float, float] | None:
    """Ponto 3D -> (x, y) de tela com a matriz 4x4 (16 números, linha a linha). None se estiver atrás da câmera."""
    m = matriz
    x, y, z = p
    w = m[12] * x + m[13] * y + m[14] * z + m[15]
    if w <= 1e-12:
        return None
    return ((m[0] * x + m[1] * y + m[2] * z + m[3]) / w, (m[4] * x + m[5] * y + m[6] * z + m[7]) / w)


def _segmento_toca(a, b, r) -> bool:
    """Liang-Barsky: o segmento a-b toca o retângulo r = (x0, y0, x1, y1)?"""
    x0, y0, x1, y1 = r
    dx, dy = b[0] - a[0], b[1] - a[1]
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, a[0] - x0), (dx, x1 - a[0]), (-dy, a[1] - y0), (dy, y1 - a[1])):
        if abs(p) < 1e-15:
            if q < 0:
                return False
            continue
        s = q / p
        if p < 0:
            t0 = max(t0, s)
        else:
            t1 = min(t1, s)
        if t0 > t1:
            return False
    return True


def _ponto_no_poligono(pt, poly) -> bool:
    dentro = False
    for i in range(len(poly)):
        (xa, ya), (xb, yb) = poly[i], poly[(i + 1) % len(poly)]
        if (ya > pt[1]) != (yb > pt[1]) and pt[0] < (xb - xa) * (pt[1] - ya) / (yb - ya) + xa:
            dentro = not dentro
    return dentro


def por_retangulo(t: Topology, matriz: Sequence[float], retangulo: Sequence[float],
                  cruzamento: bool = False) -> Dict[str, List[int]]:
    """Seleção por janela (esquerda para a direita: só o que cabe inteiro) ou cruzamento (o que toca o retângulo).

    `matriz` projeta [x, y, z, 1] em coordenadas de tela (16 números, linha a linha, divisão por w); `retangulo` está
    nas mesmas coordenadas. Vértice atrás da câmera (w <= 0) deixa de fora a aresta e a face que o usam."""
    if len(matriz) != 16:
        raise ValueError("matriz precisa de 16 números")
    x0, x1 = sorted((retangulo[0], retangulo[2]))
    y0, y1 = sorted((retangulo[1], retangulo[3]))
    r = (x0, y0, x1, y1)
    tela = {v: _projetar(matriz, p) for v, p in t.verts.items()}

    def dentro(q):
        return q is not None and x0 <= q[0] <= x1 and y0 <= q[1] <= y1

    arestas = set()
    for e, (a, b) in t.edges.items():
        pa, pb = tela[a], tela[b]
        if pa is None or pb is None:
            continue
        if (_segmento_toca(pa, pb, r) if cruzamento else dentro(pa) and dentro(pb)):
            arestas.add(e)
    faces = set()
    centro = ((x0 + x1) / 2, (y0 + y1) / 2)
    for fid, f in t.faces.items():
        pts = [tela[v] for v in f.outer]
        if any(p is None for p in pts):
            continue
        if not cruzamento:
            if all(dentro(p) for p in pts):
                faces.add(fid)
        elif _arestas_da_face(t, fid) & arestas or _ponto_no_poligono(centro, pts):
            faces.add(fid)
    return _saida(faces, arestas)
