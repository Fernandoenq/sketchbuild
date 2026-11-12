"""Textos livres: só dados; o gravador os escreve (FORMATO-SKP.md 7l)."""
import math
from typing import Optional, Sequence

from .model import Point, Topology

MATERIAL_AUTO = "<auto>"  # material automático que o SketchUp cria ao pôr cor num texto
FONTE_PADRAO = 2  # id da primeira fonte do modelo em branco (a segunda é 3)


def texto_livre(t: Topology, texto: str, ponto: Point, tipo: int = 0, vetor: Optional[Sequence[float]] = None,
                seta: int = 0, fonte: int = FONTE_PADRAO,
                cor: Optional[Sequence[int]] = None, fonte_nova: Optional[Sequence] = None) -> int:
    """Texto no `ponto`. `tipo` = tipo da linha de chamada (0, 1 ou 2, como na SketchUpAPI); `vetor` = vetor da chamada.

    `cor` = (r, g, b[, a]): o SketchUp cria o material automático "<auto>" (FORMATO-SKP 7l). Só uma cor de texto por
    modelo: com várias, o nome dos materiais seguintes não foi observado.

    `fonte_nova` = (nome, negrito, itálico, pontos): o SketchUp acrescenta a fonte (`SUModelAddFont`) à lista de fontes
    do modelo (FORMATO-SKP 7l); sem ela o texto usa `fonte` (id de uma das fontes que já existem)."""
    if not texto.strip():
        raise ValueError("texto: o texto não pode ser vazio")
    if tipo not in (0, 1, 2):
        raise ValueError("texto: tipo de linha de chamada deve ser 0, 1 ou 2")
    if seta < 0:
        raise ValueError("texto: tipo de seta não pode ser negativo")
    v = tuple(float(c) for c in (vetor or (0.0, 0.0, 0.0)))
    if any(not math.isfinite(c) for c in v) or any(not math.isfinite(c) for c in ponto):
        raise ValueError("texto: coordenada inválida")
    nova = None
    if fonte_nova is not None:
        nome, negrito, italico, pontos = fonte_nova
        if not str(nome).strip() or not 1 <= int(pontos) <= 1000:
            raise ValueError("texto: fonte nova precisa de nome e de 1 a 1000 pontos")
        nova = (str(nome), bool(negrito), bool(italico), int(pontos))
    material = None
    if cor is not None:
        c = [int(x) for x in cor]
        if len(c) not in (3, 4) or any(not 0 <= x <= 255 for x in c):
            raise ValueError("texto: cor deve ser (r, g, b[, a]) de 0 a 255")
        novo = {"rgb": tuple(c[:3]), "alpha": c[3] if len(c) == 4 else 255}
        if t.materiais.setdefault(MATERIAL_AUTO, novo) != novo:
            raise ValueError("texto: só uma cor de texto por modelo (a segunda ainda não foi observada na SDK)")
        material = MATERIAL_AUTO
    tid = next(t._gid)
    t.textos[tid] = {"texto": texto, "ponto": tuple(float(c) for c in ponto), "tipo": int(tipo), "vetor": v,
                     "seta": int(seta), "fonte": int(fonte), "material": material, "fonte_nova": nova}
    return tid


def apagar_texto(t: Topology, ident: int) -> None:
    if ident not in t.textos:
        raise ValueError(f"texto {ident} não existe")
    del t.textos[ident]
