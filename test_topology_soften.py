"""M11: suavizar arestas (bits 0x08/0x10), por ângulo e normais lisas por vértice."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.soften import LISA, SUAVE, definir, limpar, normais_suaves, por_angulo  # noqa: E402


def telhado(graus):
    """Duas faces que se encontram na aresta x=0 com `graus` de dobra."""
    t = Topology()
    a = math.radians(graus)
    t.add_face([(0, 0, 0), (-10, 0, 0), (-10, 10, 0), (0, 10, 0)])
    t.add_face([(0, 0, 0), (10 * math.cos(a), 0, 10 * math.sin(a)),
                (10 * math.cos(a), 10, 10 * math.sin(a)), (0, 10, 0)])
    return t


def aresta_do_meio(t):
    return next(e for e, (a, b) in t.edges.items() if t.verts[a][0] == 0 and t.verts[b][0] == 0 and
                abs(t.verts[a][1] - t.verts[b][1]) == 10)


def dobra(t):
    """Ângulo real (graus) entre as normais das duas faces, como o núcleo as orientou."""
    n1, n2 = (f.normal for f in t.faces.values())
    return math.degrees(math.acos(max(-1.0, min(1.0, sum(a * b for a, b in zip(n1, n2))))))


class TestSoften(unittest.TestCase):
    def test_definir_e_limpar(self):
        t = telhado(30)
        e = aresta_do_meio(t)
        self.assertEqual(definir(t, [e]), 1)
        self.assertEqual(t.eflags[e] & (SUAVE | LISA), SUAVE | LISA)
        self.assertEqual(definir(t, [e]), 0)  # já estava
        self.assertEqual(limpar(t, [e]), 1)
        self.assertNotIn(e, t.eflags)
        with self.assertRaises(ValueError):
            definir(t, [999])

    def test_por_angulo(self):
        t = telhado(30)
        d = dobra(t)
        self.assertEqual(por_angulo(t, d - 1), [])
        self.assertEqual(por_angulo(t, d + 1), [aresta_do_meio(t)])
        with self.assertRaises(ValueError):
            por_angulo(t, 181)

    def test_normais_lisas_so_com_aresta_lisa(self):
        t = telhado(60)
        self.assertEqual(normais_suaves(t), {})
        definir(t, [aresta_do_meio(t)])
        ns = normais_suaves(t)
        self.assertEqual(len(ns), 2)
        for d in ns.values():
            self.assertEqual(len(d), 2)  # só os 2 vértices da aresta compartilhada
        n1, n2 = (next(iter(d.values())) for d in ns.values())
        self.assertEqual(n1, n2)
        # a média das duas normais fica na metade do ângulo entre elas
        f1, f2 = (f.normal for f in t.faces.values())
        for fn in (f1, f2):
            ang = math.degrees(math.acos(max(-1.0, min(1.0, sum(a * b for a, b in zip(n1, fn))))))
            self.assertAlmostEqual(ang, dobra(t) / 2, places=4)

    def test_aresta_dura_nao_suaviza(self):
        t = telhado(60)
        e = aresta_do_meio(t)
        t.eflags[e] = SUAVE  # só "suave" (oculta/sem linha), sem normal lisa
        self.assertEqual(normais_suaves(t), {})


if __name__ == "__main__":
    unittest.main()
