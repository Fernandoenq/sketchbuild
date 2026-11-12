"""F5: grupos e componentes sobre o núcleo de topologia.

Uma Cena tem definições (cada uma com a sua Topology; a 0 é a raiz do modelo) e instâncias
(definição + transformação 4x4 + nome). Grupo = definição usada por uma instância só. Componente
= definição que várias instâncias podem usar. As operações de desenho e edição rodam sempre na
definição ativa (`cena.topo`); `entrar` e `sair` mudam qual é.
"""
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set

from core.topology.model import Contador, Face, Point, Topology

IDENTIDADE = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]


@dataclass
class Instancia:
    id: int
    definicao: int
    pai: int  # definição que contém a instância
    nome: str
    tipo: str  # "grupo" | "componente"
    transformacao: List[float] = field(default_factory=lambda: list(IDENTIDADE))
    tag: Optional[str] = None  # nome da tag (Topology.tags); None = Layer0


def _aplica(m: Sequence[float], p: Point) -> Point:
    """Matriz 4x4 em ordem de colunas (a do SketchUp): ponto -> ponto."""
    return (
        m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
        m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
        m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14],
    )


class Cena:
    def __init__(self) -> None:
        self.defs: Dict[int, Topology] = {0: Topology()}
        self.nomes: Dict[int, str] = {0: "Modelo"}
        self.instancias: Dict[int, Instancia] = {}
        self.caminho: List[int] = []  # instâncias por onde se entrou (vazio = raiz)
        # cenas (abas): {"nome", "descricao", "animar", "camera": {"olho", "alvo", "cima"} | None}
        self.cenas: List[dict] = []
        # comportamento do componente por definição (FORMATO-SKP 7m): {def: {"face_me", "corta_abertura", "sombra_sol"}}
        self.comportamento: Dict[int, dict] = {}
        self._def, self._inst = Contador(), Contador()

    def adicionar_cena(self, nome: str, descricao: str = "", animar: bool = True, camera: Optional[dict] = None) -> int:
        """Acrescenta uma cena (aba). `camera` = {"olho": (x,y,z), "alvo": (x,y,z), "cima": (x,y,z)} ou None."""
        if not nome.strip():
            raise ValueError("a cena precisa de nome")
        if any(c["nome"] == nome for c in self.cenas):
            raise ValueError(f"já existe a cena {nome!r}")
        if camera is not None:
            olho, alvo = camera["olho"], camera["alvo"]
            if sum((a - b) ** 2 for a, b in zip(olho, alvo)) < 1e-12:
                raise ValueError("câmera com olho igual ao alvo")
        self.cenas.append({"nome": nome, "descricao": descricao, "animar": bool(animar), "camera": camera})
        return len(self.cenas) - 1

    def definir_comportamento(self, definicao: int, face_me: bool = False, corta_abertura: bool = False,
                              sombra_sol: bool = False, snap: int = 0) -> None:
        """Comportamento do componente: sempre olha para a câmera, corta abertura, sombra segue o sol; snap 0-4 (nenhum, qualquer, horizontal, vertical, inclinado)."""
        if not 0 <= snap <= 4:
            raise ValueError("snap vai de 0 a 4")
        if definicao not in self.defs or definicao == 0:
            raise ValueError(f"definição {definicao} não existe ou é a raiz")
        usos = [i for i in self.instancias.values() if i.definicao == definicao]
        if not usos or any(i.tipo != "componente" for i in usos):
            raise ValueError("só componentes têm comportamento (grupo não)")
        self.comportamento[definicao] = {"face_me": bool(face_me), "corta_abertura": bool(corta_abertura),
                                         "sombra_sol": bool(sombra_sol), "snap": int(snap)}

    # -- definição ativa -------------------------------------------------------------

    @property
    def ativa(self) -> int:
        return self.instancias[self.caminho[-1]].definicao if self.caminho else 0

    @property
    def topo(self) -> Topology:
        return self.defs[self.ativa]

    def entrar(self, instancia: int) -> None:
        i = self.instancias.get(instancia)
        if i is None or i.pai != self.ativa:
            raise ValueError("só dá para entrar numa instância da definição ativa")
        self.caminho.append(instancia)

    def sair(self) -> None:
        if not self.caminho:
            raise ValueError("já está na raiz do modelo")
        self.caminho.pop()

    # -- criar -----------------------------------------------------------------------

    def _criar(self, tipo: str, faces: Iterable[int], arestas: Iterable[int], nome: Optional[str]) -> int:
        t = self.topo
        faces, arestas = list(faces), list(arestas)
        if not faces and not arestas:
            raise ValueError("seleção vazia")
        for f in faces:
            if f not in t.faces:
                raise ValueError(f"face {f} não existe")
        for e in arestas:
            if e not in t.edges:
                raise ValueError(f"aresta {e} não existe")
        mover_f: Set[int] = set(faces)
        mover_e: Set[int] = set(arestas)
        for f in mover_f:
            for lp in t.faces[f].loops():
                for i, a in enumerate(lp):
                    eid = t.edge_between(a, lp[(i + 1) % len(lp)])
                    if eid is not None:
                        mover_e.add(eid)
        verts: Set[int] = {v for e in mover_e for v in t.edges[e]}
        did = next(self._def)
        d = Topology(t.tol)
        mapa: Dict[int, int] = {}
        for v in sorted(verts):
            mapa[v] = d._vertex(t.verts[v])
        for e in sorted(mover_e):
            a, b = t.edges[e]
            ne = next(d._eid)
            d.edges[ne] = (mapa[a], mapa[b])
            if e in t.etags:
                d.etags[ne] = t.etags[e]
            if e in t.eflags:
                d.eflags[ne] = t.eflags[e]
        for f in sorted(mover_f):
            F = t.faces[f]
            d.faces[next(d._fid)] = Face([mapa[v] for v in F.outer], [[mapa[v] for v in h] for h in F.holes], F.normal,
                                         F.frente, F.verso, F.tag, F.uv)
        d.materiais = dict(t.materiais)
        d.tags = dict(t.tags)
        # sai da definição de origem: faces; arestas que nenhuma face que ficou usa; vértices soltos
        for f in mover_f:
            del t.faces[f]
        usadas = {frozenset((lp[i], lp[(i + 1) % len(lp)]))
                  for F in t.faces.values() for lp in F.loops() for i in range(len(lp))}
        for e in mover_e:
            if e in t.edges and frozenset(t.edges[e]) not in usadas:
                del t.edges[e]
        for v in verts:
            if v in t.verts and not any(v in e for e in t.edges.values()) \
                    and not any(v in lp for F in t.faces.values() for lp in F.loops()):
                del t.verts[v]
        self.defs[did] = d
        self.nomes[did] = nome or f"{'Grupo' if tipo == 'grupo' else 'Componente'}#{did}"
        iid = next(self._inst)
        self.instancias[iid] = Instancia(iid, did, self.ativa, self.nomes[did], tipo)
        return iid

    def criar_grupo(self, faces: Iterable[int] = (), arestas: Iterable[int] = (), nome: Optional[str] = None) -> int:
        return self._criar("grupo", faces, arestas, nome)

    def criar_componente(self, faces: Iterable[int] = (), arestas: Iterable[int] = (), nome: Optional[str] = None) -> int:
        return self._criar("componente", faces, arestas, nome)

    def instanciar(self, instancia: int, transformacao: Optional[Sequence[float]] = None) -> int:
        """Nova instância do mesmo componente (compartilha a definição)."""
        i = self.instancias.get(instancia)
        if i is None:
            raise ValueError(f"instância {instancia} não existe")
        if i.tipo != "componente":
            raise ValueError("só componentes podem ter várias instâncias (grupo é único)")
        iid = next(self._inst)
        self.instancias[iid] = Instancia(iid, i.definicao, i.pai, i.nome, "componente",
                                         list(transformacao) if transformacao else list(i.transformacao))
        return iid

    def explodir(self, instancia: int) -> None:
        """Devolve a geometria da instância à definição que a continha, já transformada."""
        i = self.instancias.get(instancia)
        if i is None or i.pai != self.ativa:
            raise ValueError("só dá para explodir uma instância da definição ativa")
        if any(x.pai == i.definicao for x in self.instancias.values()):
            raise ValueError("explodir instâncias aninhadas ainda não é suportado")
        t, d = self.topo, self.defs[i.definicao]
        mapa = {v: t._vertex(_aplica(i.transformacao, p)) for v, p in d.verts.items()}
        t.materiais.update({n: m for n, m in d.materiais.items() if n not in t.materiais})
        t.tags.update({n: m for n, m in d.tags.items() if n not in t.tags})
        for ed, (a, b) in d.edges.items():
            tag_aresta = d.etags.get(ed)
            flags_aresta = d.eflags.get(ed)
            if t.edge_between(mapa[a], mapa[b]) is None and mapa[a] != mapa[b]:
                ne = next(t._eid)
                t.edges[ne] = (mapa[a], mapa[b])
                if tag_aresta is not None:
                    t.etags[ne] = tag_aresta
                if flags_aresta is not None:
                    t.eflags[ne] = flags_aresta
        for F in d.faces.values():
            t.faces[next(t._fid)] = Face([mapa[v] for v in F.outer], [[mapa[v] for v in h] for h in F.holes], F.normal, F.frente, F.verso, F.tag)
        del self.instancias[instancia]
        if not any(x.definicao == i.definicao for x in self.instancias.values()):
            del self.defs[i.definicao]
            self.comportamento.pop(i.definicao, None)
            del self.nomes[i.definicao]

    # -- consulta --------------------------------------------------------------------

    def resumo(self) -> Dict[str, object]:
        return {
            "ativa": self.ativa,
            "caminho": list(self.caminho),
            "definicoes": {d: {"nome": self.nomes[d], **self.defs[d].counts(), "comportamento": self.comportamento.get(d)}
                           for d in self.defs},
            "instancias": {
                i: {"definicao": x.definicao, "pai": x.pai, "nome": x.nome, "tipo": x.tipo, "transformacao": x.transformacao}
                for i, x in self.instancias.items()
            },
        }
