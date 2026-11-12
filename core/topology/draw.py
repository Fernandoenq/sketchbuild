"""F2: ferramentas de desenho (Linha, Retângulo, Círculo, Polígono, Arco, Mão livre)
sobre o núcleo de topologia. Cada ferramenta gera os pontos como o SketchUp e chama
`add_edge`/`add_face`; `desenhar` devolve o delta (o que nasceu, mudou e sumiu)."""
import math
from typing import Dict, List, Optional, Sequence, Tuple

from core.topology.model import Point, Topology, _cross, _dot, _norm, _unit

CIRCULO_LADOS = 24  # padrão do SketchUp (r09)
ARCO_LADOS = 12
POLIGONO_LADOS = 6


def eixos(normal: Point) -> Tuple[Point, Point]:
    """Eixos X e Y do plano de desenho (mesma regra do SketchUp: X = Z x normal)."""
    n = _unit(normal)
    if abs(n[0]) < 1e-9 and abs(n[1]) < 1e-9:
        x = (1.0, 0.0, 0.0)
    else:
        x = _unit(_cross((0.0, 0.0, 1.0), n))
    return x, _cross(n, x)


def _pt(c: Point, x: Point, y: Point, a: float, b: float) -> Point:
    return tuple(c[i] + a * x[i] + b * y[i] for i in range(3))


def pontos_retangulo(p0: Point, p1: Point, normal: Point = (0, 0, 1)) -> List[Point]:
    x, y = eixos(normal)
    d = tuple(p1[i] - p0[i] for i in range(3))
    a, b = _dot(d, x), _dot(d, y)
    return [p0, _pt(p0, x, y, a, 0), _pt(p0, x, y, a, b), _pt(p0, x, y, 0, b)]


def pontos_circulo(centro: Point, raio: float, normal: Point = (0, 0, 1),
                   lados: int = CIRCULO_LADOS) -> List[Point]:
    x, y = eixos(normal)
    return [_pt(centro, x, y, raio * math.cos(2 * math.pi * i / lados),
                raio * math.sin(2 * math.pi * i / lados)) for i in range(lados)]


def pontos_poligono(centro: Point, raio: float, normal: Point = (0, 0, 1),
                    lados: int = POLIGONO_LADOS, circunscrito: bool = False) -> List[Point]:
    """Inscrito: o raio vai ao vértice. Circunscrito: o raio vai ao meio do lado."""
    if circunscrito:
        raio = raio / math.cos(math.pi / lados)
    return pontos_circulo(centro, raio, normal, lados)


def pontos_arco(centro: Point, raio: float, ang_ini: float, ang_fim: float,
                normal: Point = (0, 0, 1), lados: int = ARCO_LADOS) -> List[Point]:
    """Arco do ângulo inicial ao final (graus, anti-horário), com `lados` segmentos."""
    x, y = eixos(normal)
    return [_pt(centro, x, y,
                raio * math.cos(math.radians(ang_ini + (ang_fim - ang_ini) * i / lados)),
                raio * math.sin(math.radians(ang_ini + (ang_fim - ang_ini) * i / lados)))
            for i in range(lados + 1)]


def arco_por_3_pontos(p0: Point, p1: Point, p2: Point) -> Tuple[Point, float, Point, float, float]:
    """Arco que parte de p0, passa por p1 e termina em p2: (centro, raio, normal, ang_ini, ang_fim) em graus.

    A normal é a do triângulo (p0, p1, p2), então o arco sempre corre no sentido anti-horário em torno dela."""
    u = tuple(p1[i] - p0[i] for i in range(3))
    v = tuple(p2[i] - p0[i] for i in range(3))
    n = _cross(u, v)
    d = 2.0 * _dot(n, n)
    if d <= 1e-18 or _norm(n) <= 1e-9 * max(_norm(u), _norm(v), 1.0):
        raise ValueError("arco: os três pontos são colineares")
    uu, vv = _dot(u, u), _dot(v, v)
    c = tuple((vv * _cross(n, u)[i] + uu * _cross(v, n)[i]) / d for i in range(3))
    centro = tuple(p0[i] + c[i] for i in range(3))
    raio = _norm(c)
    normal = _unit(n)
    x, y = eixos(normal)

    def ang(p: Point) -> float:
        r = tuple(p[i] - centro[i] for i in range(3))
        return math.degrees(math.atan2(_dot(r, y), _dot(r, x)))

    ini = ang(p0)
    varredura = (ang(p2) - ini) % 360.0
    return centro, raio, normal, ini, ini + varredura


def arco_por_corda(p0: Point, p1: Point, flecha: float, normal: Point = (0, 0, 1)) -> Tuple[Point, float, Point, float, float]:
    """Arco por corda (p0 a p1) e flecha (altura do arco, positiva à esquerda de p0→p1 visto da normal)."""
    corda = tuple(p1[i] - p0[i] for i in range(3))
    if _norm(corda) <= 1e-9:
        raise ValueError("arco: corda de comprimento zero")
    if abs(flecha) <= 1e-9:
        raise ValueError("arco: flecha zero")
    lado = _unit(_cross(_unit(normal), corda))
    topo = tuple((p0[i] + p1[i]) / 2.0 + flecha * lado[i] for i in range(3))
    return arco_por_3_pontos(p0, topo, p1)


def pontos_bezier(controles: Sequence[Point], lados: int = ARCO_LADOS) -> List[Point]:
    """Curva de Bézier (de Casteljau) de grau len(controles)-1, com `lados` segmentos."""
    if len(controles) < 3:
        raise ValueError("bezier: precisa de ao menos 3 pontos de controle")
    out = []
    for i in range(lados + 1):
        u = i / lados
        q = [tuple(c) for c in controles]
        while len(q) > 1:
            q = [tuple((1 - u) * q[k][j] + u * q[k + 1][j] for j in range(3)) for k in range(len(q) - 1)]
        out.append(q[0])
    out[0], out[-1] = tuple(controles[0]), tuple(controles[-1])
    return out


def simplificar_rdp(pontos: Sequence[Point], tolerancia: float) -> List[Point]:
    """Ramer-Douglas-Peucker: tira pontos a menos de `tolerancia` da reta entre os extremos do trecho."""
    pts = [tuple(p) for p in pontos]
    if tolerancia <= 0 or len(pts) < 3:
        return pts
    manter = [False] * len(pts)
    manter[0] = manter[-1] = True
    pilha = [(0, len(pts) - 1)]
    while pilha:
        i, j = pilha.pop()
        a, b = pts[i], pts[j]
        ab = tuple(b[k] - a[k] for k in range(3))
        nab = _norm(ab)
        melhor, idx = -1.0, -1
        for m in range(i + 1, j):
            ap = tuple(pts[m][k] - a[k] for k in range(3))
            dist = _norm(ap) if nab <= 1e-12 else _norm(_cross(ab, ap)) / nab
            if dist > melhor:
                melhor, idx = dist, m
        if idx >= 0 and melhor > tolerancia:
            manter[idx] = True
            pilha += [(i, idx), (idx, j)]
    return [p for p, m in zip(pts, manter) if m]


def _estado(t: Topology) -> Dict[str, dict]:
    return {
        "vertices": dict(t.verts),
        "edges": dict(t.edges),
        "faces": {i: (tuple(f.outer), tuple(tuple(h) for h in f.holes)) for i, f in t.faces.items()},
    }


def _delta(antes: Dict[str, dict], depois: Dict[str, dict]) -> Dict[str, dict]:
    out = {}
    for k in antes:
        a, d = antes[k], depois[k]
        out[k] = {
            "added": {i: d[i] for i in d if i not in a},
            "changed": {i: d[i] for i in d if i in a and a[i] != d[i]},
            "removed": [i for i in a if i not in d],
        }
    return out


def _polilinha(t: Topology, pts: Sequence[Point], fechar: bool) -> None:
    n = len(pts)
    for i in range(n if fechar else n - 1):
        t.add_edge(pts[i], pts[(i + 1) % n])


def _registrar_curva(t: Topology, pts: Sequence[Point], fechar: bool, centro: Optional[Point] = None,
                     raio: float = 0.0, ang_ini: float = 0.0, ang_fim: float = 0.0,
                     normal: Point = (0, 0, 1)) -> None:
    """Guarda a curva com as arestas na ordem em que foram desenhadas.

    Com `centro`, é curva de arco (círculo/arco, registro 0x1397); sem, é curva simples (polígono, mão livre: 0x1396)."""
    n = len(pts)
    arestas = []
    for i in range(n if fechar else n - 1):
        a, b = t._vertex(pts[i]), t._vertex(pts[(i + 1) % n])
        e = t.edge_between(a, b)
        if e is None:
            return
        arestas.append(e)
    if centro is None:
        t.curvas[next(t._cid)] = {"tipo": "simples", "arestas": arestas}
        return
    t.curvas[next(t._cid)] = {"tipo": "arco", "centro": tuple(centro), "normal": tuple(normal), "raio": raio,
                              "ang_ini": ang_ini, "ang_fim": ang_fim, "inicio": tuple(pts[0]), "arestas": arestas}


def _fechar_lacos(t: Topology, eids_antes: set) -> None:
    """Como o SketchUp: aresta nova que fecha um laço planar vira face sozinha."""
    for eid in [e for e in t.edges if e not in eids_antes]:
        if eid in t.edges:
            t.find_faces(eid)


def desenhar(t: Topology, ferramenta: str, **p) -> Dict[str, dict]:
    """Aplica uma ferramenta e devolve o delta {vertices|edges|faces: {added, changed, removed}}.

    linha(pontos) | retangulo(p0, p1, normal) | circulo(centro, raio, normal, lados)
    poligono(centro, raio, normal, lados, circunscrito) | arco(centro, raio, ang_ini, ang_fim, normal, lados)
    mao_livre(pontos, fechar, tolerancia) | arco_3pontos(p0, p1, p2, lados) | arco_corda(p0, p1, flecha, normal, lados)
    setor(centro, raio, ang_ini, ang_fim, normal, lados) | fatia(centro, raio, ang_ini, ang_fim, normal, lados)
    bezier(pontos, lados)
    """
    antes, eids = _estado(t), set(t.edges)
    if ferramenta == "linha":
        _polilinha(t, p["pontos"], False)
        _fechar_lacos(t, eids)
    elif ferramenta == "retangulo":
        t.add_face(pontos_retangulo(p["p0"], p["p1"], p.get("normal", (0, 0, 1))))
    elif ferramenta == "circulo":
        pts = pontos_circulo(p["centro"], p["raio"], p.get("normal", (0, 0, 1)), p.get("lados", CIRCULO_LADOS))
        t.add_face(pts)
        _registrar_curva(t, pts, True, p["centro"], p["raio"], 0.0, 360.0, p.get("normal", (0, 0, 1)))
    elif ferramenta == "poligono":
        pts = pontos_poligono(p["centro"], p["raio"], p.get("normal", (0, 0, 1)),
                              p.get("lados", POLIGONO_LADOS), p.get("circunscrito", False))
        t.add_face(pts)
        _registrar_curva(t, pts, True)
    elif ferramenta == "arco":
        pts = pontos_arco(p["centro"], p["raio"], p["ang_ini"], p["ang_fim"],
                          p.get("normal", (0, 0, 1)), p.get("lados", ARCO_LADOS))
        _polilinha(t, pts, False)
        _registrar_curva(t, pts, False, p["centro"], p["raio"], p["ang_ini"], p["ang_fim"], p.get("normal", (0, 0, 1)))
        _fechar_lacos(t, eids)
    elif ferramenta in ("arco_3pontos", "arco_corda"):
        if ferramenta == "arco_3pontos":
            c, r, n, a0, a1 = arco_por_3_pontos(p["p0"], p["p1"], p["p2"])
        else:
            c, r, n, a0, a1 = arco_por_corda(p["p0"], p["p1"], p["flecha"], p.get("normal", (0, 0, 1)))
        pts = pontos_arco(c, r, a0, a1, n, p.get("lados", ARCO_LADOS))
        _polilinha(t, pts, False)
        _registrar_curva(t, pts, False, c, r, a0, a1, n)
        _fechar_lacos(t, eids)
    elif ferramenta in ("setor", "fatia"):
        n = p.get("normal", (0, 0, 1))
        pts = pontos_arco(p["centro"], p["raio"], p["ang_ini"], p["ang_fim"], n, p.get("lados", ARCO_LADOS))
        t.add_face(([tuple(p["centro"])] if ferramenta == "setor" else []) + pts)
        _registrar_curva(t, pts, False, p["centro"], p["raio"], p["ang_ini"], p["ang_fim"], n)
    elif ferramenta == "bezier":
        pts = pontos_bezier(p["pontos"], p.get("lados", ARCO_LADOS))
        _polilinha(t, pts, False)
        _registrar_curva(t, pts, False)
        _fechar_lacos(t, eids)
    elif ferramenta == "mao_livre":
        pts = simplificar_rdp(p["pontos"], p.get("tolerancia", 0.0))
        fechar = p.get("fechar", _norm(tuple(pts[0][i] - pts[-1][i] for i in range(3))) <= t.tol)
        if fechar and len(pts) > 1 and _norm(tuple(pts[0][i] - pts[-1][i] for i in range(3))) <= t.tol:
            pts = pts[:-1]
        _polilinha(t, pts, fechar)
        _fechar_lacos(t, eids)
        if len(pts) > 1:
            _registrar_curva(t, pts, fechar)
    else:
        raise ValueError(f"ferramenta desconhecida: {ferramenta!r}")
    return _delta(antes, _estado(t))
