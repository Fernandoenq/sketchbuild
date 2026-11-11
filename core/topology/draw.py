"""F2: ferramentas de desenho (Linha, Retângulo, Círculo, Polígono, Arco, Mão livre)
sobre o núcleo de topologia. Cada ferramenta gera os pontos como o SketchUp e chama
`add_edge`/`add_face`; `desenhar` devolve o delta (o que nasceu, mudou e sumiu)."""
import math
from typing import Dict, List, Sequence, Tuple

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


def _registrar_curva(t: Topology, pts: Sequence[Point], fechar: bool, centro: Point, raio: float,
                     ang_ini: float, ang_fim: float, normal: Point) -> None:
    """Guarda a curva (círculo/arco) com as arestas na ordem em que foram desenhadas."""
    n = len(pts)
    arestas = []
    for i in range(n if fechar else n - 1):
        a, b = t._vertex(pts[i]), t._vertex(pts[(i + 1) % n])
        e = t.edge_between(a, b)
        if e is None:
            return
        arestas.append(e)
    t.curvas[next(t._cid)] = {"centro": tuple(centro), "normal": tuple(normal), "raio": raio,
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
    mao_livre(pontos, fechar)
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
        t.add_face(pontos_poligono(p["centro"], p["raio"], p.get("normal", (0, 0, 1)),
                                   p.get("lados", POLIGONO_LADOS), p.get("circunscrito", False)))
    elif ferramenta == "arco":
        pts = pontos_arco(p["centro"], p["raio"], p["ang_ini"], p["ang_fim"],
                          p.get("normal", (0, 0, 1)), p.get("lados", ARCO_LADOS))
        _polilinha(t, pts, False)
        _registrar_curva(t, pts, False, p["centro"], p["raio"], p["ang_ini"], p["ang_fim"], p.get("normal", (0, 0, 1)))
        _fechar_lacos(t, eids)
    elif ferramenta == "mao_livre":
        pts = list(p["pontos"])
        fechar = p.get("fechar", _norm(tuple(pts[0][i] - pts[-1][i] for i in range(3))) <= t.tol)
        if fechar and len(pts) > 1 and _norm(tuple(pts[0][i] - pts[-1][i] for i in range(3))) <= t.tol:
            pts = pts[:-1]
        _polilinha(t, pts, fechar)
        _fechar_lacos(t, eids)
    else:
        raise ValueError(f"ferramenta desconhecida: {ferramenta!r}")
    return _delta(antes, _estado(t))
