"""Sessão de desenho em memória (F2): um núcleo de topologia por execução do backend."""
from __future__ import annotations

from core.topology import Topology
from core.topology.draw import desenhar

_TOPO = Topology()

_OBRIGATORIOS = {
    "linha": ("pontos",),
    "retangulo": ("p0", "p1"),
    "circulo": ("centro", "raio"),
    "poligono": ("centro", "raio"),
    "arco": ("centro", "raio", "ang_ini", "ang_fim"),
    "mao_livre": ("pontos",),
}


def _chave(delta: dict) -> dict:
    """JSON só aceita chave de texto; ids do núcleo são inteiros."""
    out = {}
    for k, v in delta.items():
        out[k] = {
            "added": {str(i): _lista(x) for i, x in v["added"].items()},
            "changed": {str(i): _lista(x) for i, x in v["changed"].items()},
            "removed": list(v["removed"]),
        }
    return out


def _lista(x):
    if isinstance(x, tuple):
        return [_lista(i) for i in x]
    return x


class DrawRepository:
    def desenhar(self, ferramenta: str, **params) -> dict:
        faltam = [c for c in _OBRIGATORIOS[ferramenta] if params.get(c) is None]
        if faltam:
            raise ValueError(f"{ferramenta}: faltam {', '.join(faltam)}")
        params = {k: v for k, v in params.items() if v is not None}
        res = _chave(desenhar(_TOPO, ferramenta, **params))
        res["counts"] = _TOPO.counts()
        return res

    def estado(self) -> dict:
        return {
            "vertices": {str(i): list(p) for i, p in _TOPO.verts.items()},
            "edges": {str(i): list(e) for i, e in _TOPO.edges.items()},
            "faces": {str(i): {"outer": f.outer, "holes": f.holes, "normal": list(f.normal)}
                      for i, f in _TOPO.faces.items()},
            "counts": _TOPO.counts(),
        }

    def limpar(self) -> None:
        global _TOPO
        _TOPO = Topology()
