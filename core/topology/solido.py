"""M12: ferramentas de sólido sobre o núcleo: verificação de sólido válido, volume e união, subtração e interseção.

Sólido válido: toda aresta do contorno está em exatamente duas faces do conjunto, as faces se orientam de forma
consistente e o volume é maior que zero. As operações booleanas cortam um sólido pelo outro (Intersect Faces), classificam
cada pedaço de face como dentro ou fora do outro sólido por lançamento de raio e guardam os pedaços certos.
Limite desta versão: faces coplanares sobrepostas entre os dois sólidos dão erro (sem oráculo no SketchUp real)."""
from typing import Dict, Iterable, List, Optional, Tuple

from .intersect import intersectar
from .model import Face, Point, Topology, _dot, _newell, _sub, _unit

_RAIO = _unit((0.48273, 0.71935, 0.50291))  # direção sem alinhamento com eixos nem diagonais, para não bater em quinas
_OP = ("uniao", "subtracao", "intersecao")
_MARCA_A, _MARCA_B = "\x00A|", "\x00B|"  # tags temporárias (+ a tag de antes): de qual sólido veio cada pedaço dos cortes


def _arestas_da_face(f: Face) -> List[Tuple[int, int]]:
    """Pares (a, b) de cada laço, na ordem do laço."""
    return [(lp[i], lp[(i + 1) % len(lp)]) for lp in f.loops() for i in range(len(lp))]


def _orientacao(t: Topology, faces: List[int]) -> Optional[Tuple[Dict[int, int], List[List[int]]]]:
    """(sinal, cascas): +1/-1 por face para os laços ficarem consistentes (cada aresta percorrida em sentidos opostos
    pelas 2 faces) e as faces agrupadas em cascas conexas (um sólido com cavidade tem 2 ou mais).
    None se não der (aresta com número de faces diferente de 2, ou superfície não orientável)."""
    uso: Dict[frozenset, List[Tuple[int, Tuple[int, int]]]] = {}
    for fid in faces:
        for a, b in _arestas_da_face(t.faces[fid]):
            uso.setdefault(frozenset((a, b)), []).append((fid, (a, b)))
    if not uso or any(len(v) != 2 for v in uso.values()):
        return None
    vizinhos: Dict[int, List[Tuple[int, int]]] = {f: [] for f in faces}
    for (f1, d1), (f2, d2) in uso.values():
        if f1 == f2:
            return None
        rel = -1 if d1 == d2 else 1  # mesmo sentido nas duas faces => uma delas precisa inverter
        vizinhos[f1].append((f2, rel))
        vizinhos[f2].append((f1, rel))
    sinal: Dict[int, int] = {}
    cascas: List[List[int]] = []
    for ini in faces:
        if ini in sinal:
            continue
        sinal[ini] = 1
        casca, pilha = [ini], [ini]
        while pilha:
            f = pilha.pop()
            for g, rel in vizinhos[f]:
                esperado = sinal[f] * rel
                if g not in sinal:
                    sinal[g] = esperado
                    casca.append(g)
                    pilha.append(g)
                elif sinal[g] != esperado:
                    return None
        cascas.append(casca)
    return sinal, cascas


def _volume_da_casca(t: Topology, casca: List[int], sinal: Dict[int, int]) -> float:
    total = 0.0
    for fid in casca:
        f = t.faces[fid]
        vet = _newell([t.verts[v] for v in f.outer])
        for h in f.holes:
            hv = _newell([t.verts[v] for v in h])
            if _dot(hv, vet) > 0:
                vet = _sub(vet, hv)
            else:
                vet = tuple(vet[i] + hv[i] for i in range(3))
        total += sinal[fid] * _dot(vet, t.verts[f.outer[0]]) / 6.0  # a soma de Newell é o dobro da área; o volume divide por 3
    return abs(total)


def volume(t: Topology, faces: Iterable[int]) -> float:
    """Volume (positivo) do sólido formado pelas faces; ValueError se não for um sólido válido.

    Cascas dentro de outra casca são cavidades e entram subtraindo (uma casca dentro de uma cavidade volta a somar)."""
    faces = sorted(set(faces))
    for f in faces:
        if f not in t.faces:
            raise ValueError(f"face {f} não existe")
    orient = _orientacao(t, faces)
    if orient is None:
        raise ValueError("não é um sólido: toda aresta precisa estar em exatamente duas faces, com orientação consistente")
    sinal, cascas = orient
    total = 0.0
    for c in cascas:
        profundidade = 0
        if len(cascas) > 1:
            ponto = _ponto_interior(t, t.faces[c[0]])
            profundidade = sum(1 for o in cascas if o is not c and _classificar(t, ponto, o)[0] == "dentro")
        total += (-1) ** profundidade * _volume_da_casca(t, c, sinal)
    if total <= t.tol ** 3:
        raise ValueError("não é um sólido: volume zero")
    return total


def eh_solido(t: Topology, faces: Iterable[int]) -> bool:
    try:
        volume(t, faces)
        return True
    except ValueError:
        return False


def _dist_segmento(p: Point, a: Point, b: Point) -> float:
    ab = _sub(b, a)
    den = _dot(ab, ab)
    u = 0.0 if den == 0 else max(0.0, min(1.0, _dot(_sub(p, a), ab) / den))
    q = tuple(a[k] + u * ab[k] for k in range(3))
    d = _sub(p, q)
    return _dot(d, d) ** 0.5


def _ponto_interior(t: Topology, f: Face) -> Point:
    """Ponto bem dentro da face (longe do contorno e dos furos), mesmo côncava: centro dos vértices ou de uma orelha."""
    pts = [t.verts[v] for v in f.outer]
    n = len(pts)
    segs = [(t.verts[lp[i]], t.verts[lp[(i + 1) % len(lp)]]) for lp in f.loops() for i in range(len(lp))]
    escala = max(_dot(_sub(a, b), _sub(a, b)) ** 0.5 for a, b in segs)

    def bom(q: Point) -> bool:
        return t._inside_face(f, q) and min(_dist_segmento(q, a, b) for a, b in segs) > 1e-6 * escala

    candidatos = [tuple(sum(p[i] for p in pts) / n for i in range(3))]
    for i in range(n):  # polígono côncavo: o centro de uma orelha costuma cair dentro
        a, b, d = pts[i - 1], pts[i], pts[(i + 1) % n]
        candidatos.append(tuple((a[k] + b[k] + d[k]) / 3 for k in range(3)))
    for q in candidatos:
        if bom(q):
            return q
    raise ValueError("não achei um ponto interior numa face")


def _classificar(t: Topology, p: Point, outro: List[int]) -> Tuple[str, Optional[int]]:
    """('dentro' | 'fora' | 'sobre' | 'oco', face) em relação ao outro sólido.

    'sobre': o ponto está numa face do outro sólido (devolve qual). 'oco': está no plano de uma face dele, dentro do
    contorno externo mas num furo (sobreposição coplanar parcial, não suportada)."""
    cruza = 0
    for fid in outro:
        f = t.faces[fid]
        p0, n = t.verts[f.outer[0]], f.normal
        dist = _dot(n, _sub(p, p0))
        if abs(dist) <= 1e-6:
            if t._inside_face(f, p):
                return "sobre", fid
            if f.holes and t._point_in_loop(p, f.outer, f.normal):
                return "oco", fid
        den = _dot(n, _RAIO)
        if abs(den) < 1e-12:
            continue
        s = -dist / den
        if s <= 1e-9:
            continue
        if t._inside_face(f, tuple(p[k] + s * _RAIO[k] for k in range(3))):
            cruza += 1
    return ("dentro" if cruza % 2 == 1 else "fora"), None


def _sinal_saida(t: Topology, fid: int, solido: List[int]) -> int:
    """+1 se a normal da face aponta para fora do sólido a que ela pertence, -1 se aponta para dentro."""
    f = t.faces[fid]
    p = _ponto_interior(t, f)
    escala = max(_dist_segmento(t.verts[a], t.verts[b], t.verts[b]) for a, b in _arestas_da_face(f))
    q = tuple(p[k] + 1e-4 * escala * f.normal[k] for k in range(3))
    return 1 if _classificar(t, q, solido)[0] == "fora" else -1


def _acao_coplanar(operacao: str, da_a: bool, mesmo_sentido: bool) -> str:
    """O que fazer com uma face que coincide com uma do outro sólido (as duas existem): 'manter' ou 'largar'.

    Mesmo sentido (as duas viradas para o mesmo lado de fora): união e interseção ficam com a de A; a subtração larga as
    duas. Sentidos opostos (os sólidos se encostam): união e interseção largam as duas (a face some por dentro ou não
    entra no resultado); a subtração fica com a de A."""
    if mesmo_sentido:
        return "manter" if da_a and operacao in ("uniao", "intersecao") else "largar"
    return "manter" if da_a and operacao == "subtracao" else "largar"


def _executar(t: Topology, fa: List[int], fb: List[int], operacao: str) -> List[int]:
    """Classifica os pedaços já cortados de A e de B e apaga o que não entra no resultado. Devolve as faces do resultado."""
    classe: Dict[int, Tuple[str, Optional[int]]] = {}
    for f in fa:
        classe[f] = _classificar(t, _ponto_interior(t, t.faces[f]), fb)
    for f in fb:
        classe[f] = _classificar(t, _ponto_interior(t, t.faces[f]), fa)
    manter_a = "fora" if operacao in ("uniao", "subtracao") else "dentro"
    manter_b = "fora" if operacao == "uniao" else "dentro"
    manter, virar, largar = [], [], []
    for lista, outra, da_a in ((fa, fb, True), (fb, fa, False)):
        for f in lista:
            tipo, par = classe[f]
            if tipo == "oco":
                raise ValueError("sobreposição coplanar parcial entre as faces dos sólidos ainda não é suportada")
            if tipo == "sobre":
                gemea = t.faces[par]
                if set(t.faces[f].outer) != set(gemea.outer) or len(t.faces[f].holes) != len(gemea.holes):
                    raise ValueError("sobreposição coplanar parcial entre as faces dos sólidos ainda não é suportada")
                mesmo = _dot(t.faces[f].normal, gemea.normal) * _sinal_saida(t, f, lista) * _sinal_saida(t, par, outra) > 0
                (manter if _acao_coplanar(operacao, da_a, mesmo) == "manter" else largar).append(f)
            elif da_a:
                (manter if tipo == manter_a else largar).append(f)
            elif tipo == manter_b:
                manter.append(f)
            elif operacao == "subtracao" and tipo == "dentro":
                virar.append(f)
            else:
                largar.append(f)
    for f in largar:
        del t.faces[f]
    for f in virar:
        face = t.faces[f]
        face.outer.reverse()
        for h in face.holes:
            h.reverse()
        face.normal = tuple(-c for c in face.normal)
    resultado = sorted(set(manter) | set(virar))
    usadas = {frozenset(e) for f in resultado for e in _arestas_da_face(t.faces[f])}
    for e in [e for e, (x, y) in t.edges.items() if frozenset((x, y)) not in usadas]:
        del t.edges[e]
        t.etags.pop(e, None)
        t.eflags.pop(e, None)
    em_uso = {v for e in t.edges.values() for v in e} | {v for f in t.faces.values() for lp in f.loops() for v in lp}
    for v in [v for v in t.verts if v not in em_uso]:
        del t.verts[v]
    return resultado


def _marcar(t: Topology, a: List[int], b: List[int]) -> None:
    for f in a:
        t.faces[f].tag = _MARCA_A + (t.faces[f].tag or "")
    for f in b:
        t.faces[f].tag = _MARCA_B + (t.faces[f].tag or "")


def _desmarcar(t: Topology) -> None:
    for x in t.faces.values():
        if x.tag and x.tag[:3] in (_MARCA_A, _MARCA_B):
            x.tag = x.tag[3:] or None  # os pedaços herdam a tag da face cortada


def _cortar_e_executar(t: Topology, a: List[int], b: List[int], operacao: str) -> List[int]:
    _marcar(t, a, b)
    try:
        intersectar(t, a + b)
        fa = [f for f, x in t.faces.items() if (x.tag or "").startswith(_MARCA_A)]
        fb = [f for f, x in t.faces.items() if (x.tag or "").startswith(_MARCA_B)]
        return _executar(t, fa, fb, operacao)
    finally:
        _desmarcar(t)


def booleana(t: Topology, a: Iterable[int], b: Iterable[int], operacao: str) -> Dict[str, List[int]]:
    """União, subtração (A menos B) ou interseção de dois sólidos do mesmo modelo. Devolve as faces do resultado.

    No mesmo `Topology` faces coplanares se fundem, então só entram sobreposições que o núcleo consegue representar;
    para sólidos que se encostam em faces inteiras use `combinar` (um modelo por sólido)."""
    if operacao not in _OP:
        raise ValueError(f"operação desconhecida: {operacao!r}")
    a, b = sorted(set(a)), sorted(set(b))
    if set(a) & set(b):
        raise ValueError("os dois sólidos não podem compartilhar faces")
    volume(t, a)
    volume(t, b)
    return {"faces": _cortar_e_executar(t, a, b, operacao)}


def _copiar_para(w: Topology, t: Topology, faces: List[int]) -> List[int]:
    """Copia as faces para `w` sem fundir faces coplanares (insere direto, soldando só vértices coincidentes)."""
    novos = []
    for fid in faces:
        f = t.faces[fid]
        mapa = {v: w._vertex(t.verts[v]) for lp in f.loops() for v in lp}
        loops = [[mapa[v] for v in lp] for lp in f.loops()]
        for lp in loops:
            for i, x in enumerate(lp):
                y = lp[(i + 1) % len(lp)]
                if w.edge_between(x, y) is None:
                    w.edges[next(w._eid)] = (x, y)
        nid = next(w._fid)
        w.faces[nid] = Face(loops[0], loops[1:], f.normal, f.frente, f.verso, f.tag, f.uv)
        novos.append(nid)
    return novos


def combinar(ta: Topology, faces_a: Iterable[int], tb: Topology, faces_b: Iterable[int], operacao: str) -> Topology:
    """Operação booleana entre sólidos de dois modelos (por exemplo, dois grupos): devolve um modelo novo com o resultado.

    Aceita sólidos que se encostam ou coincidem em faces inteiras idênticas; sobreposição coplanar parcial dá erro.
    Materiais e tags dos dois modelos vão junto (o de A vence em nome repetido)."""
    if operacao not in _OP:
        raise ValueError(f"operação desconhecida: {operacao!r}")
    fa, fb = sorted(set(faces_a)), sorted(set(faces_b))
    volume(ta, fa)
    volume(tb, fb)
    w = Topology(ta.tol)
    w.materiais = {**tb.materiais, **ta.materiais}
    w.tags = {**tb.tags, **ta.tags}
    a = _copiar_para(w, ta, fa)
    b = _copiar_para(w, tb, fb)
    for v in list(w.verts):  # vértice de um sólido no meio de uma aresta do outro: divide a aresta em T
        w._split_edges_at(v)
    _cortar_e_executar(w, a, b, operacao)
    return w
