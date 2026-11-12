"""Pintar faces com material de cor sólida (Fase C). O material vive em `Topology.materiais` e a face aponta por nome."""
from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

from core.topology.model import Topology


def definir_material(t: Topology, nome: str, rgb: Sequence[int], alpha: int = 255, textura: Optional[dict] = None) -> None:
    """`textura` = {"nome": "tijolo.png", "bytes": <arquivo>, "escala": (s, t)}; `rgb` vira a cor média da imagem."""
    if not nome.strip():
        raise ValueError("o material precisa de nome")
    if len(rgb) != 3 or any(not 0 <= int(c) <= 255 for c in rgb) or not 0 <= alpha <= 255:
        raise ValueError("cor fora de 0-255")
    m = {"rgb": tuple(int(c) for c in rgb), "alpha": int(alpha)}
    if textura:
        if not textura.get("nome") or not textura.get("bytes"):
            raise ValueError("a textura precisa de nome e bytes da imagem")
        m["textura"] = {"nome": str(textura["nome"]), "bytes": bytes(textura["bytes"]), "escala": tuple(textura.get("escala", (1.0, 1.0)))}
    t.materiais[nome] = m


def pintar(t: Topology, faces: Sequence[int], frente: Optional[str] = None, verso: Optional[str] = None,
           limpar_frente: bool = False, limpar_verso: bool = False) -> Dict[str, dict]:
    """Aplica material na frente e/ou no verso; `limpar_*` volta a face ao padrão. Devolve {face: (frente, verso)}."""
    for n in (frente, verso):
        if n and n not in t.materiais:
            raise ValueError(f"material {n!r} não definido")
    faltam = [f for f in faces if f not in t.faces]
    if faltam:
        raise ValueError(f"faces inexistentes: {faltam}")
    out = {}
    for fid in faces:
        f = t.faces[fid]
        if frente:
            f.frente = frente
        elif limpar_frente:
            f.frente = None
        if verso:
            f.verso = verso
        elif limpar_verso:
            f.verso = None
        out[fid] = (f.frente, f.verso)
    return out


def descartar_nao_usados(t: Topology) -> None:
    usados = {n for f in t.faces.values() for n in (f.frente, f.verso) if n}
    for n in [n for n in t.materiais if n not in usados]:
        del t.materiais[n]
