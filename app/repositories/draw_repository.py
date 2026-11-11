"""Sessão de desenho em memória (F2): um núcleo de topologia por execução do backend."""
from __future__ import annotations

from core.topology import Topology
from core.topology.cena import Cena
from core.topology.historico import Historico
from core.topology.intersect import intersectar
from core.topology.sweep import siga_me
from core.topology.draw import desenhar
from core.topology.edit import escalar, mover, offset, rotacionar, vertices_da_selecao
from core.topology.pushpull import empurrar

_CENA = Cena()
_HIST = Historico(_CENA)


def _topo() -> Topology:
    return _CENA.topo

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
        res = _chave(_HIST.executar("desenhar:" + ferramenta, params, lambda: desenhar(_topo(), ferramenta, **params)))
        res["counts"] = _topo().counts()
        return res

    def empurrar(self, face_id: int, distancia: float, criar_nova: bool = False) -> dict:
        res = _chave(_HIST.executar("pushpull", {"face": face_id, "distancia": distancia}, lambda: empurrar(_topo(), face_id, distancia, criar_nova)))
        res["counts"] = _topo().counts()
        return res

    def editar(self, operacao: str, vertices, arestas, faces, vetor=None, angulo=None,
               eixo=(0.0, 0.0, 1.0), centro=None, fator=None, fatores=None) -> dict:
        ids = vertices_da_selecao(_topo(), vertices, arestas, faces)
        if operacao == "mover":
            if vetor is None:
                raise ValueError("mover: falta o vetor")
            delta = _HIST.executar("mover", {"vetor": vetor}, lambda: mover(_topo(), ids, vetor))
        elif operacao == "rotacionar":
            if angulo is None:
                raise ValueError("rotacionar: falta o angulo")
            delta = _HIST.executar("rotacionar", {"angulo": angulo}, lambda: rotacionar(_topo(), ids, angulo, eixo, centro))
        else:
            if fator is None and fatores is None:
                raise ValueError("escalar: falta o fator")
            delta = _HIST.executar("escalar", {"fator": fator}, lambda: escalar(_topo(), ids, fatores if fatores is not None else fator, centro))
        res = _chave(delta)
        res["counts"] = _topo().counts()
        return res

    def offset(self, face_id: int, distancia: float) -> dict:
        res = _chave(_HIST.executar("offset", {"face": face_id, "distancia": distancia}, lambda: offset(_topo(), face_id, distancia)))
        res["counts"] = _topo().counts()
        return res

    def siga_me(self, face_id: int, arestas: list[int]) -> dict:
        res = _chave(_HIST.executar("followme", {"face": face_id}, lambda: siga_me(_topo(), face_id, arestas)))
        res["counts"] = _topo().counts()
        return res

    def intersectar(self, faces) -> dict:
        res = _chave(_HIST.executar("intersect", {}, lambda: intersectar(_topo(), faces)))
        res["counts"] = _topo().counts()
        return res

    def agrupar(self, tipo: str, faces, arestas, nome) -> dict:
        criar = _CENA.criar_grupo if tipo == "grupo" else _CENA.criar_componente
        iid = _HIST.executar(tipo, {"nome": nome}, lambda: criar(faces, arestas, nome))
        return {"instancia": iid, **self.cena()}

    def instanciar(self, instancia: int, transformacao) -> dict:
        iid = _HIST.executar("instanciar", {"instancia": instancia}, lambda: _CENA.instanciar(instancia, transformacao))
        return {"instancia": iid, **self.cena()}

    def explodir(self, instancia: int) -> dict:
        _HIST.executar("explodir", {"instancia": instancia}, lambda: _CENA.explodir(instancia))
        return self.cena()

    def entrar(self, instancia: int) -> dict:
        _CENA.entrar(instancia)
        return self.cena()

    def sair(self) -> dict:
        _CENA.sair()
        return self.cena()

    def cena(self) -> dict:
        r = _CENA.resumo()
        return {
            "ativa": r["ativa"],
            "caminho": r["caminho"],
            "definicoes": {str(k): v for k, v in r["definicoes"].items()},
            "instancias": {str(k): v for k, v in r["instancias"].items()},
        }

    def desfazer(self) -> dict:
        _HIST.desfazer()
        return self.estado()

    def refazer(self) -> dict:
        _HIST.refazer()
        return self.estado()

    def historico(self) -> dict:
        return _HIST.resumo()

    def estado(self) -> dict:
        return {
            "vertices": {str(i): list(p) for i, p in _topo().verts.items()},
            "edges": {str(i): list(e) for i, e in _topo().edges.items()},
            "faces": {str(i): {"outer": f.outer, "holes": f.holes, "normal": list(f.normal)}
                      for i, f in _topo().faces.items()},
            "counts": _topo().counts(),
            "historico": {k: v for k, v in _HIST.resumo().items() if k.startswith("pode")},
        }

    def limpar(self) -> None:
        global _CENA, _HIST
        _CENA = Cena()
        _HIST = Historico(_CENA)
