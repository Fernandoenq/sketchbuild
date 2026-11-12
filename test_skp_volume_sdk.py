"""M12: o volume do núcleo (`solido.volume`) tem de bater com `SUComponentInstanceComputeVolume` da SketchUpAPI."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.solido import _orientacao, booleana, eh_solido, volume  # noqa: E402

try:
    import tools.conferir_volume_sdk as oraculo
    from core.su_api import SketchUpAPI
    SketchUpAPI().initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False


def _misto(x, y, z, s):
    """Cubo com enrolamentos arbitrários (como nos testes do núcleo): a SDK e o núcleo têm de unificar do mesmo jeito."""
    def P(i, j, k):
        return (x + i * s, y + j * s, z + k * s)
    lados = [[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
             [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
             [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]]
    verts, faces = [], []
    for f in lados:
        idx = []
        for p in f:
            q = P(*p)
            if q not in verts:
                verts.append(q)
            idx.append(verts.index(q))
        faces.append(idx)
    return verts, faces


def _no_nucleo(cubos):
    t = Topology()
    ids = []
    for v, faces in cubos:
        ids += [t.add_face([v[i] for i in f]) for f in faces]
    return t, ids


def _casos():
    c = oraculo._cubo
    return {
        "cubo": [c(0, 0, 0, 10)],
        "cavidade_invertida": [c(0, 0, 0, 10), c(3, 3, 3, 4, invertido=True)],
        "casca_interna_mesmo_sentido": [c(0, 0, 0, 10), c(3, 3, 3, 4)],
        "cubo_todo_invertido": [c(0, 0, 0, 10, invertido=True)],
        "cubo_misto": [_misto(0, 0, 0, 10)],
        "misto_com_misto_dentro": [_misto(0, 0, 0, 10), _misto(3, 3, 3, 4)],
        "misto_com_interno_invertido": [_misto(0, 0, 0, 10), c(3, 3, 3, 4, invertido=True)],
    }


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestVolumeContraASdk(unittest.TestCase):
    def test_bate_com_a_sdk(self):
        for nome, cubos in _casos().items():
            with self.subTest(nome):
                t, ids = _no_nucleo(cubos)
                self.assertAlmostEqual(volume(t, ids), oraculo.volume(cubos), places=6)

    def test_aberto_nao_e_solido_nos_dois(self):
        cubos = [oraculo._cubo(0, 0, 0, 10, sem=1)]
        with self.assertRaises(AssertionError):
            oraculo.volume(cubos)  # a SDK devolve erro 9
        t, ids = _no_nucleo(cubos)
        self.assertFalse(eh_solido(t, ids))


class TestSubtracaoInverteACavidade(unittest.TestCase):
    def test_parede_da_cavidade_fica_consistente(self):
        t = Topology()
        v, faces = oraculo_cubo(0, 0, 0, 10)
        a = [t.add_face([v[i] for i in f]) for f in faces]
        v, faces = oraculo_cubo(3, 3, 3, 4)
        b = [t.add_face([v[i] for i in f]) for f in faces]
        r = booleana(t, a, b, "subtracao")
        sinal, cascas = _orientacao(t, r["faces"])
        self.assertEqual(len(cascas), 2)  # casca externa e casca da cavidade
        # o sentido real das duas cascas é oposto: as somas com sinal têm sinais contrários
        from core.topology.solido import _volume_da_casca
        v1, v2 = (_volume_da_casca(t, c, sinal) for c in cascas)
        self.assertLess(v1 * v2, 0)
        self.assertAlmostEqual(volume(t, r["faces"]), 936.0)


def oraculo_cubo(x, y, z, s):
    """Cubo com normais para fora, sem depender da SDK (mesma tabela de tools/conferir_volume_sdk.py)."""
    lados = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
    v = [(x + i * s, y + j * s, z + k * s) for k in (0, 1) for j, i in ((0, 0), (0, 1), (1, 1), (1, 0))]
    return v, lados


if __name__ == "__main__":
    unittest.main()
