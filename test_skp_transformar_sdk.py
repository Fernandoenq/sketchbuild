"""Mover/Rotacionar/Escalar: o núcleo (`edit`) tem de dar o mesmo que `SUEntitiesTransform` da SketchUpAPI
(posição dos vértices, normal da face e, no espelho, a ordem dos vértices que a SDK reescreve para manter a normal)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.edit import escalar, mover, rotacionar  # noqa: E402

try:
    import tools.conferir_transformar_sdk as oraculo
    from core.su_api import SketchUpAPI
    SketchUpAPI().initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False

_Q = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
_CUBO_V = [(x, y, z) for z in (0, 10) for (x, y) in ((0, 0), (10, 0), (10, 10), (0, 10))]
_CUBO_F = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]


def _r(p):
    return tuple(round(c, 6) + 0.0 for c in p)


def _nucleo(verts, faces):
    t = Topology()
    for f in faces:
        t.add_face([verts[i] for i in f])
    return t


def _foto(t):
    """Por face: (normal, conjunto de posições, ciclo de posições normalizado pelo menor ponto)."""
    out = []
    for f in t.faces.values():
        ciclo = [_r(t.verts[v]) for v in f.outer]
        i = ciclo.index(min(ciclo))
        out.append((_r(f.normal), frozenset(ciclo), tuple(ciclo[i:] + ciclo[:i])))
    return sorted(out, key=lambda x: sorted(x[1]))


def _foto_sdk(r):
    out = []
    for f in r["faces"]:
        ciclo = [_r(p) for p in f["ordem"]]
        i = ciclo.index(min(ciclo))
        out.append((_r(f["normal"]), frozenset(ciclo), tuple(ciclo[i:] + ciclo[:i])))
    return sorted(out, key=lambda x: sorted(x[1]))


# nome: (matriz da SDK, operação no núcleo)
def _ids(t):
    return set(t.verts)


CASOS = {
    "mover": (oraculo.translacao(5, -3, 2) if DISPONIVEL else None, lambda t: mover(t, _ids(t), (5, -3, 2))),
    "rotar_90_em_z_na_origem": (oraculo.rot_z(90) if DISPONIVEL else None, lambda t: rotacionar(t, _ids(t), 90, (0, 0, 1), (0, 0, 0))),
    "escala_uniforme_2": (oraculo.escala(2, 2, 2) if DISPONIVEL else None, lambda t: escalar(t, _ids(t), 2, (0, 0, 0))),
    "escala_nao_uniforme": (oraculo.escala(2, 1, 3) if DISPONIVEL else None, lambda t: escalar(t, _ids(t), (2, 1, 3), (0, 0, 0))),
    "espelho_x": (oraculo.escala(-1, 1, 1) if DISPONIVEL else None, lambda t: escalar(t, _ids(t), (-1, 1, 1), (0, 0, 0))),
    "espelho_z": (oraculo.escala(1, 1, -1) if DISPONIVEL else None, lambda t: escalar(t, _ids(t), (1, 1, -1), (0, 0, 0))),
}


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestTransformarContraASdk(unittest.TestCase):
    def test_quadrado_e_cubo(self):
        # só o cubo: a normal de uma face solta no chão tem convenção própria no núcleo (primeira face olha para baixo)
        for forma, verts, faces in (("cubo", _CUBO_V, _CUBO_F),):
            for nome, (m, op) in CASOS.items():
                with self.subTest(f"{forma}/{nome}"):
                    sdk = oraculo.transformar([{"verts": verts, "faces": faces}], m)
                    self.assertEqual(sdk["codigo"], 0)
                    t = _nucleo(verts, faces)
                    op(t)
                    self.assertEqual(_foto(t), _foto_sdk(sdk))


class TestEspelhoNoNucleo(unittest.TestCase):
    def test_fator_zero_recusado(self):
        t = _nucleo(_Q, [[0, 1, 2, 3]])
        with self.assertRaises(ValueError):
            escalar(t, set(t.verts), (1, 0, 1), (0, 0, 0))

    def test_espelho_inverte_a_ordem_e_reflete_a_normal(self):
        t = _nucleo(_Q, [[0, 1, 2, 3]])
        f = next(iter(t.faces.values()))
        antes, n0 = list(f.outer), f.normal
        escalar(t, set(t.verts), (-1, 1, 1), (0, 0, 0))
        self.assertEqual(f.outer, antes[::-1])
        self.assertEqual(_r(f.normal), _r(n0))  # espelho em x não muda a normal em z

    def test_espelho_desfeito_quando_a_operacao_falha(self):
        t = _nucleo(_CUBO_V, _CUBO_F)
        antes = {fid: list(f.outer) for fid, f in t.faces.items()}
        with self.assertRaises(ValueError):
            escalar(t, {min(t.verts)}, (-1, 1, 1), (5, 5, 0))  # mexer num vértice só deixa as faces não planas
        self.assertEqual({fid: list(f.outer) for fid, f in t.faces.items()}, antes)


if __name__ == "__main__":
    unittest.main()
