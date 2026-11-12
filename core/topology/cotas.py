"""Cotas lineares: só dados; o gravador as escreve (FORMATO-SKP.md 7k)."""
import math
from typing import Sequence, Tuple

from .model import Point, Topology


def _unit(v: Sequence[float], nome: str) -> Tuple[float, float, float]:
    n = math.sqrt(sum(c * c for c in v))
    if n < 1e-12:
        raise ValueError(f"cota: {nome} nulo")
    return tuple(float(c) / n for c in v)


def cota_linear(t: Topology, inicio: Point, fim: Point, normal: Sequence[float] = (0, 0, 1),
                eixo_x: Sequence[float] = (1, 0, 0), texto: str = "", seta: int = 0,
                desloc: Tuple[float, float] = (0.0, 0.0), alinhamento_v: int = 1) -> int:
    """Cota entre dois pontos no plano de `normal`. `texto` vazio = o SketchUp mostra a medida.

    `seta` 0 = padrão (valor de `SUDimensionSetArrowType`); `desloc` = (x, y) do texto no plano da cota, como o SketchUp
    grava (relação exata com o ponto inicial ainda não conferida); `alinhamento_v` = valor do arquivo (padrão 1).
    """
    if math.dist(inicio, fim) < 1e-9:
        raise ValueError("cota: início e fim iguais")
    if seta < 0 or alinhamento_v < 0:
        raise ValueError("cota: seta e alinhamento não podem ser negativos")
    cid = next(t._gid)
    t.cotas[cid] = {
        "inicio": tuple(float(c) for c in inicio), "fim": tuple(float(c) for c in fim),
        "normal": _unit(normal, "normal"), "eixo_x": _unit(eixo_x, "eixo x"),
        "texto": str(texto), "seta": int(seta), "desloc": (float(desloc[0]), float(desloc[1])),
        "alinhamento_v": int(alinhamento_v),
    }
    return cid


def apagar_cota(t: Topology, ident: int) -> None:
    if ident not in t.cotas:
        raise ValueError(f"cota {ident} não existe")
    del t.cotas[ident]
