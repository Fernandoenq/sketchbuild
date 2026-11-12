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


def descartar_nao_usadas(t: Topology) -> int:
    usadas = {f.tag for f in t.faces.values() if f.tag}
    sobras = [n for n in t.tags if n not in usadas]
    for n in sobras:
        del t.tags[n]
    return len(sobras)
