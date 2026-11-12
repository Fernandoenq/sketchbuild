"""Caixa limite (mín, máx) de uma instância no espaço do contêiner que a contém (FORMATO-SKP.md seção 7).

Regras conferidas contra `SUDrawingElementGetBoundingBox` da SketchUpAPI e contra o `0x13a0` de um arquivo salvo pelo
SketchUp:
- instância comum: caixa dos oito cantos da caixa da definição, transformados;
- instância de componente que sempre olha para a câmera (face-me): centrada na origem da instância, com meia largura
  `R * (|cos t| + |sen t|)` em x e y, onde `R` é o maior raio horizontal (`hypot(x, y)`) dos cantos da caixa da definição e
  `t` o giro da instância em torno de z (a caixa do quadrado de lado `2R` girado); o z é o da definição transformado.
"""
import itertools
import math
from typing import Sequence, Tuple

Ponto = Tuple[float, float, float]


def _aplica(m: Sequence[float], p: Ponto) -> Ponto:
    """Matriz 4x4 em ordem de colunas (a do SketchUp): ponto -> ponto."""
    return (m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12],
            m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13],
            m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14])


def caixa_instancia(pontos: Sequence[Ponto], matriz: Sequence[float], face_me: bool = False) -> Tuple[Ponto, Ponto]:
    """Caixa limite da instância de uma definição com os vértices `pontos`, com transformação 4x4 `matriz`."""
    if not pontos:
        raise ValueError("definição sem vértices")
    lo = tuple(min(p[k] for p in pontos) for k in range(3))
    hi = tuple(max(p[k] for p in pontos) for k in range(3))
    cantos = [_aplica(matriz, (x, y, z)) for x, y, z in itertools.product(*zip(lo, hi))]
    zmin, zmax = min(c[2] for c in cantos), max(c[2] for c in cantos)
    if not face_me:
        return (tuple(min(c[k] for c in cantos) for k in range(3)), tuple(max(c[k] for c in cantos) for k in range(3)))
    escala = math.hypot(matriz[0], matriz[1], matriz[2])
    if escala < 1e-12:
        raise ValueError("matriz sem escala")
    raio = max(math.hypot(x, y) for x in (lo[0], hi[0]) for y in (lo[1], hi[1])) * escala
    meia = raio * (abs(matriz[0]) + abs(matriz[1])) / escala
    cx, cy = matriz[12], matriz[13]
    return ((cx - meia, cy - meia, zmin), (cx + meia, cy + meia, zmax))
