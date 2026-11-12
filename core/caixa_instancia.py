"""Caixa limite (mín, máx) de uma instância no espaço do contêiner que a contém (FORMATO-SKP.md seção 7).

Regras conferidas contra `SUDrawingElementGetBoundingBox` da SketchUpAPI e contra o `0x13a0` de um arquivo salvo pelo
SketchUp:
- instância comum: caixa dos oito cantos da caixa da definição, transformados;
- instância de componente que sempre olha para a câmera (face-me): a caixa local vira `[-R, R]² x [zmin, zmax]`, onde
  `R` é o maior raio horizontal (`hypot(x, y)`) dos cantos da caixa da definição, e entra a mesma regra dos oito cantos
  transformados. Vale para qualquer giro e escala (conferido contra a SDK também com giros em x e y).
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
    if face_me:
        # a definição gira em torno do próprio z para olhar a câmera: varre o disco de raio R no plano local xy
        raio = max(math.hypot(x, y) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]))
        lo, hi = (-raio, -raio, lo[2]), (raio, raio, hi[2])
    cantos = [_aplica(matriz, (x, y, z)) for x, y, z in itertools.product(*zip(lo, hi))]
    return (tuple(min(c[k] for c in cantos) for k in range(3)), tuple(max(c[k] for c in cantos) for k in range(3)))
