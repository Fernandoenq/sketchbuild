"""Guias (pontos e linhas de construção) e planos de seção: só dados; o gravador os escreve (FORMATO-SKP.md 7h)."""
import math
from typing import Optional, Sequence

from .model import Point, Topology


def guia_ponto(t: Topology, p: Point) -> int:
    gid = next(t._gid)
    t.guias[gid] = {"tipo": "ponto", "p": tuple(float(c) for c in p)}
    return gid


def guia_linha(t: Topology, p: Point, alvo: Optional[Point] = None, direcao: Optional[Sequence[float]] = None) -> int:
    """Linha de guia. Com `alvo` é finita (de `p` até `alvo`); com `direcao` é infinita pelos dois lados."""
    if (alvo is None) == (direcao is None):
        raise ValueError("guia: informe só `alvo` (finita) ou só `direcao` (infinita)")
    if alvo is not None:
        v = [alvo[i] - p[i] for i in range(3)]
        n = math.sqrt(sum(c * c for c in v))
        if n < 1e-12:
            raise ValueError("guia: início e fim iguais")
        d, t0, t1 = tuple(c / n for c in v), 0.0, n
    else:
        n = math.sqrt(sum(c * c for c in direcao))
        if n < 1e-12:
            raise ValueError("guia: direção nula")
        d, t0, t1 = tuple(c / n for c in direcao), -1e30, 1e30
    gid = next(t._gid)
    t.guias[gid] = {"tipo": "linha", "p": tuple(float(c) for c in p), "d": d, "t0": t0, "t1": t1}
    return gid


def plano_secao(t: Topology, normal: Point, ponto: Point) -> int:
    """Plano de seção que passa por `ponto` com a `normal` dada."""
    n = math.sqrt(sum(c * c for c in normal))
    if n < 1e-12:
        raise ValueError("plano de seção: normal nula")
    a, b, c = (x / n for x in normal)
    gid = next(t._gid)
    t.secoes[gid] = (a, b, c, -(a * ponto[0] + b * ponto[1] + c * ponto[2]))
    return gid


def apagar(t: Topology, ident: int) -> None:
    if ident in t.guias:
        del t.guias[ident]
    elif ident in t.secoes:
        del t.secoes[ident]
    else:
        raise ValueError(f"guia ou plano {ident} não existe")
