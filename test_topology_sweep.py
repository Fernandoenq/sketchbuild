"""F5: Siga-me contra a receita r14 do SketchUp real."""
import unittest

from core.topology import Topology
from core.topology.sweep import siga_me
from test_topology_golden import GoldenCase, etapa


def preparar(caminho):
    t = Topology()
    ids = []
    for a, b in zip(caminho, caminho[1:]):
        ids += t.add_edge(a, b)
    fid = t.add_face([(-5, -5, 0), (5, -5, 0), (5, 5, 0), (-5, 5, 0)])
    return t, fid, ids


class TestSigaMe(GoldenCase):
    def test_r14_caminho_em_L(self):
        t, fid, ids = preparar([(0, 0, 0), (0, 0, 100), (100, 0, 100)])
        siga_me(t, fid, ids)
        self.confere(t, etapa("r14", "depois"))

    def test_caminho_reto_vira_cubo_alongado(self):
        t, fid, ids = preparar([(0, 0, 0), (0, 0, 100)])
        siga_me(t, fid, ids)
        self.assertEqual(t.counts(), {"vertices": 10, "edges": 13, "faces": 6})
        self.assertAlmostEqual(sum(t.face_area(f) for f in t.faces) - 200, 4000, places=3)

    def test_caminho_colinear_funde_paredes(self):
        t, fid, ids = preparar([(0, 0, 0), (0, 0, 50), (0, 0, 100)])
        siga_me(t, fid, ids)
        self.assertEqual(len(t.faces), 6)

    def test_normais_para_fora(self):
        t, fid, ids = preparar([(0, 0, 0), (0, 0, 100), (100, 0, 100)])
        siga_me(t, fid, ids)
        for f in t.faces.values():
            self.assertAlmostEqual(sum(x * x for x in f.normal), 1, places=6)

    def test_erros(self):
        t, fid, ids = preparar([(0, 0, 0), (0, 0, 100)])
        with self.assertRaises(ValueError):
            siga_me(t, 999, ids)
        with self.assertRaises(ValueError):
            siga_me(t, fid, [])


if __name__ == "__main__":
    unittest.main()
