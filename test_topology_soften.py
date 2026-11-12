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
        # cada face recebe a normal do grupo virada para o seu lado; as duas são a mesma reta
        (f1, d1), (f2, d2) = ns.items()
        v = next(iter(d1))
        a, b = d1[v], d2[v]
        self.assertAlmostEqual(abs(sum(x * y for x, y in zip(a, b))), 1.0, places=9)
        for fid, d in ns.items():
            self.assertGreaterEqual(sum(x * y for x, y in zip(d[v], t.faces[fid].normal)), 0.0)  # lado da própria face

    def test_enrolamento_consistente_e_cantos_iguais_da_a_bissetriz(self):
        t = Topology()
        a = math.radians(60)
        t.add_face([(0, 0, 0), (-10, 0, 0), (-10, 10, 0), (0, 10, 0)])  # percorre a aresta do meio de (0,10,0) para (0,0,0)
        t.add_face([(0, 0, 0), (0, 10, 0), (10 * math.cos(a), 10, 10 * math.sin(a)), (10 * math.cos(a), 0, 10 * math.sin(a))])  # no sentido oposto
        definir(t, [aresta_do_meio(t)])
        ns = normais_suaves(t)
        f1, f2 = (f.normal for f in t.faces.values())
        for fid, d in ns.items():
            ang = math.degrees(math.acos(max(-1.0, min(1.0, sum(x * y for x, y in zip(next(iter(d.values())), t.faces[fid].normal))))))
            self.assertAlmostEqual(ang, dobra(t) / 2, places=4)  # regra da SDK: peso = ângulo do canto (90 e 90)

    def test_aresta_dura_nao_suaviza(self):
        t = telhado(60)
        e = aresta_do_meio(t)
        t.eflags[e] = SUAVE  # só "suave" (oculta/sem linha), sem normal lisa
        self.assertEqual(normais_suaves(t), {})


if __name__ == "__main__":
    unittest.main()
