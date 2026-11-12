"""M10: arco por 3 pontos, por corda e flecha, setor, fatia, Bézier e RDP na mão livre."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.draw import (arco_por_3_pontos, arco_por_corda, desenhar, pontos_bezier,  # noqa: E402
                                simplificar_rdp)


class TestArcos(unittest.TestCase):
    def test_tres_pontos_semicirculo(self):
        c, r, n, a0, a1 = arco_por_3_pontos((10, 0, 0), (0, 10, 0), (-10, 0, 0))
        self.assertTrue(all(abs(x - y) < 1e-9 for x, y in zip(c, (0, 0, 0))))
        self.assertAlmostEqual(r, 10.0)
        self.assertEqual(n, (0.0, 0.0, 1.0))
        self.assertAlmostEqual(a1 - a0, 180.0)

    def test_tres_pontos_passa_pelo_ponto_do_meio_em_3d(self):
        t = Topology()
        d = desenhar(t, "arco_3pontos", p0=(0, 0, 0), p1=(5, 0, 5), p2=(10, 0, 0), lados=12)
        pts = [tuple(round(x, 6) for x in v) for v in d["vertices"]["added"].values()]
        self.assertIn((5.0, 0.0, 5.0), pts)  # 12 lados: o ponto médio cai no vértice 6
        self.assertEqual(len(pts), 13)
        self.assertEqual(len(t.curvas), 1)

    def test_colinear_e_corda_invalida(self):
        with self.assertRaises(ValueError):
            arco_por_3_pontos((0, 0, 0), (1, 0, 0), (2, 0, 0))
        with self.assertRaises(ValueError):
            arco_por_corda((0, 0, 0), (0, 0, 0), 1)
        with self.assertRaises(ValueError):
            arco_por_corda((0, 0, 0), (1, 0, 0), 0)

    def test_corda_e_flecha(self):
        c, r, n, a0, a1 = arco_por_corda((0, 0, 0), (10, 0, 0), 2.5)
        self.assertAlmostEqual(r, 6.25)
        self.assertAlmostEqual(c[0], 5.0)
        self.assertAlmostEqual(c[1], -3.75)
        # a flecha vira a altura: do ponto médio da corda ao topo do arco
        self.assertAlmostEqual(r - abs(c[1]), 2.5)

    def test_setor_e_fatia_fecham_face(self):
        for nome, arestas in (("setor", 12 + 2), ("fatia", 12 + 1)):
            t = Topology()
            desenhar(t, nome, centro=(0, 0, 0), raio=10, ang_ini=0, ang_fim=90, lados=12)
            self.assertEqual(len(t.faces), 1, nome)
            self.assertEqual(len(t.edges), arestas, nome)

    def test_bezier(self):
        pts = pontos_bezier([(0, 0, 0), (5, 10, 0), (10, 0, 0)], 4)
        self.assertEqual(pts[0], (0, 0, 0))
        self.assertEqual(pts[-1], (10, 0, 0))
        self.assertAlmostEqual(pts[2][1], 5.0)  # t=0.5 da quadrática: y = 2*0.25*10
        with self.assertRaises(ValueError):
            pontos_bezier([(0, 0, 0), (1, 1, 0)])
        t = Topology()
        desenhar(t, "bezier", pontos=[(0, 0, 0), (5, 10, 0), (10, 0, 0)], lados=8)
        self.assertEqual(len(t.edges), 8)

    def test_rdp(self):
        reta = [(i, 0.001 * (i % 2), 0) for i in range(11)]
        self.assertEqual(len(simplificar_rdp(reta, 0.01)), 2)
        self.assertEqual(len(simplificar_rdp(reta, 0)), 11)
        quina = [(0, 0, 0), (5, 0, 0), (10, 0, 0), (10, 5, 0), (10, 10, 0)]
        self.assertEqual(simplificar_rdp(quina, 0.1), [(0, 0, 0), (10, 0, 0), (10, 10, 0)])
        t = Topology()
        desenhar(t, "mao_livre", pontos=reta, tolerancia=0.01)
        self.assertEqual(len(t.edges), 1)


if __name__ == "__main__":
    unittest.main()
