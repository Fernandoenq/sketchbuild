"""Pintar faces com material de cor sólida (Fase C). O material vive em `Topology.materiais` e a face aponta por nome."""
from __future__ import annotations

import math
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
            f.uv = None
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


def matriz_uv(tamanho: float, u0: float = 0.0, v0: float = 0.0, graus: float = 0.0) -> Tuple[float, float, float, float, float, float]:
    """Matriz UV -> plano da face (FORMATO-SKP 7j) de uma textura que repete a cada `tamanho` polegadas.

    `(u0, v0)` é a coordenada de textura na origem do plano e `graus` gira a textura no sentido anti-horário.
    Conferida contra a SketchUpAPI em quatro casos (escala, escala 4, deslocamento e giro de 90 graus).
    """
    if tamanho <= 0:
        raise ValueError("o tamanho do ladrilho precisa ser positivo")
    c, s = math.cos(math.radians(graus)), math.sin(math.radians(graus))
    a, b, c2, d = tamanho * c, -tamanho * s, tamanho * s, tamanho * c  # S * R, linhas [a b] [c d]
    return (a, b, c2, d, -(u0 * a + v0 * c2), -(u0 * b + v0 * d))


def posicionar_textura(t: Topology, faces: Sequence[int], matriz: Optional[Sequence[float]]) -> None:
    """Grava (ou, com `matriz=None`, tira) o posicionamento da textura na frente das faces; exige textura na frente."""
    faltam = [f for f in faces if f not in t.faces]
    if faltam:
        raise ValueError(f"faces inexistentes: {faltam}")
    if matriz is not None and len(matriz) != 6:
        raise ValueError("a matriz de textura tem 6 números (a, b, c, d, tx, ty)")
    for fid in faces:
        f = t.faces[fid]
        if matriz is not None and not (f.frente and "textura" in t.materiais.get(f.frente, {})):
            raise ValueError(f"face {fid}: a frente não tem material com textura")
        f.uv = tuple(float(x) for x in matriz) if matriz is not None else None
