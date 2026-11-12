"""M11: as normais lisas do núcleo (`soften.normais_suaves`) têm de bater com as da SketchUpAPI (`SUMeshHelperGetNormals`)."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.soften import definir, normais_suaves  # noqa: E402

try:
    import tools.conferir_normais_sdk as oraculo
    from core.su_api import SketchUpAPI
    SketchUpAPI().initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False

_A = math.radians(60)
_COS, _SEN = math.cos(_A), math.sin(_A)


def _tri(ya, yb, fb):
    """Duas faces triangulares com cantos diferentes no vértice 0; `fb` define o sentido da segunda."""
    v = [(0, 0, 0), (0, 10, 0), (-10, ya, 0), (2 * _COS, yb, 2 * _SEN)]
    return v, [[0, 2, 1], fb]


def _tres(fc):
    """Três triangulos em volta do vértice 0, ligados por duas arestas lisas (0-1 e 0-3)."""
    v = [(0, 0, 0), (0, 10, 0), (-10, 0, 0), (2 * _COS, 0, 2 * _SEN), (2 * _COS + 1, -10, 2 * _SEN + 3)]
    return v, [[0, 2, 1], [0, 3, 1], fc]


CASOS = {
    "padrao_inconsistente": oraculo.telhado() if DISPONIVEL else None,
    "cantos_90_90_inconsistente": _tri(0, 0, [0, 3, 1]),
    "cantos_90_90_consistente": _tri(0, 0, [0, 1, 3]),
    "canto_a_45_consistente": _tri(10, 0, [0, 1, 3]),
    "canto_b_45_consistente": _tri(0, 2, [0, 1, 3]),
    "canto_a_135_inconsistente": _tri(-10, 0, [0, 3, 1]),
    "canto_b_45_inconsistente": _tri(0, 2, [0, 3, 1]),
    "tres_faces_consistente": _tres([0, 4, 3]),
    "tres_faces_inconsistente": _tres([0, 3, 4]),
}


def _normais_do_nucleo(v, faces):
    t = Topology()
    ids = [t.add_face([v[i] for i in f]) for f in faces]
    definir(t, [e for e in t.edges if len(t.faces_of_edge(e)) == 2])
    return t, ids, normais_suaves(t)


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestNormaisContraASdk(unittest.TestCase):
    def test_bate_com_a_sdk(self):
        for nome, (v, faces) in CASOS.items():
            with self.subTest(nome):
                original = oraculo.telhado
                oraculo.telhado = lambda **kw: (v, faces)
                try:
                    sdk = oraculo.gerar("lisa")
                finally:
                    oraculo.telhado = original
                t, ids, ns = _normais_do_nucleo(v, faces)
                comparados = 0
                for i, face in sdk.items():
                    for p, q in face["vertices"]:
                        vid = next(x for x, pp in t.verts.items() if all(abs(a - b) < 1e-6 for a, b in zip(pp, p)))
                        meu = ns.get(ids[i], {}).get(vid, t.faces[ids[i]].normal)
                        for a, b in zip(meu, q):
                            self.assertAlmostEqual(a, b, places=6, msg=f"{nome} face {i} vértice {p}")
                        comparados += 1
                self.assertGreaterEqual(comparados, 6)

    def test_so_a_aresta_lisa_muda_a_normal(self):
        v, faces = CASOS["padrao_inconsistente"]
        for variacao in ("nenhuma", "suave"):
            sdk = oraculo.gerar(variacao)
            for face in sdk.values():
                for _, q in face["vertices"]:
                    for a, b in zip(q, face["normal"]):
                        self.assertAlmostEqual(a, b, places=6)  # sem aresta lisa, cada face usa a sua normal
        t = Topology()
        for f in faces:
            t.add_face([v[i] for i in f])
        t.eflags.update({e: 0x08 for e in t.edges})  # só suave
        self.assertEqual(normais_suaves(t), {})


class TestNormaisNoNucleo(unittest.TestCase):
    def test_ponderacao_por_angulo_e_inversao(self):
        v, faces = _tri(0, 0, [0, 1, 3])  # enrolamento consistente, cantos de 90: média simples (bissetriz)
        t, ids, ns = _normais_do_nucleo(v, faces)
        n0 = ns[ids[0]][1]
        n1 = ns[ids[1]][1]
        self.assertAlmostEqual(math.degrees(math.acos(sum(a * b for a, b in zip(n0, t.faces[ids[0]].normal)))),
                               math.degrees(math.acos(sum(a * b for a, b in zip(n1, t.faces[ids[1]].normal)))), places=5)

    def test_sem_aresta_lisa_nao_ha_normais_suaves(self):
        v, faces = CASOS["cantos_90_90_consistente"]
        t = Topology()
        for f in faces:
            t.add_face([v[i] for i in f])
        self.assertEqual(normais_suaves(t), {})


if __name__ == "__main__":
    unittest.main()
