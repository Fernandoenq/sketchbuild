"""Tags (camadas) das faces: definir, atribuir, descartar as não usadas."""
from typing import Dict, Optional, Sequence

from .model import Topology


def definir_tag(t: Topology, nome: str, visivel: bool = True) -> None:
    if not nome.strip() or nome == "Layer0":
        raise ValueError("nome de tag inválido (vazio ou reservado para a tag padrão Layer0)")
    t.tags[nome] = {"visivel": bool(visivel)}


def atribuir(t: Topology, faces: Sequence[int], nome: Optional[str]) -> Dict[int, Optional[str]]:
    """Põe as faces na tag `nome`; None devolve à Layer0. Devolve {face: tag}."""
    if nome is not None and nome not in t.tags:
        raise ValueError(f"tag {nome!r} não definida")
    faltam = [f for f in faces if f not in t.faces]
    if faltam:
        raise ValueError(f"faces inexistentes: {faltam}")
    for f in faces:
        t.faces[f].tag = nome
    return {f: nome for f in faces}


def atribuir_arestas(t: Topology, arestas: Sequence[int], nome: Optional[str]) -> Dict[int, Optional[str]]:
    """Põe arestas na tag `nome` (None devolve à Layer0)."""
    if nome is not None and nome not in t.tags:
        raise ValueError(f"tag {nome!r} não definida")
    faltam = [e for e in arestas if e not in t.edges]
    if faltam:
        raise ValueError(f"arestas inexistentes: {faltam}")
    for e in arestas:
        if nome is None:
            t.etags.pop(e, None)
        else:
            t.etags[e] = nome
    return {e: nome for e in arestas}


def atribuir_instancia(cena, instancia: int, nome: Optional[str]) -> None:
    """Põe a instância (grupo ou componente) na tag `nome`; a tag precisa existir na definição que a contém."""
    i = cena.instancias.get(instancia)
    if i is None:
        raise ValueError(f"instância {instancia} não existe")
    if nome is not None:
        topo = cena.defs[i.pai]
        if nome not in topo.tags:
            raise ValueError(f"tag {nome!r} não definida")
    i.tag = nome


def descartar_nao_usadas(t: Topology) -> int:
    usadas = {f.tag for f in t.faces.values() if f.tag} | set(t.etags.values())
    sobras = [n for n in t.tags if n not in usadas]
    for n in sobras:
        del t.tags[n]
    return len(sobras)
