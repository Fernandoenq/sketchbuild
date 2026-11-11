"""F5: Intersect Faces."""
import unittest

from core.topology import Topology
from core.topology.draw import desenhar
from core.topology.intersect import intersectar
from core.topology.pushpull import empurrar


def cubo(t, x0=0, y0=0, lado=100, altura=50):
    desenhar(t, "retangulo", p0=(x0, y0, 0), p1=(x0 + lado, y0 + lado, 0))
    fid = max(t.faces)
    empurrar(t, fid, -altura)


class TestIntersect(unittest.TestCase):
    def test_plano_atravessa_o_cubo(self):
        t = Topology()
        cubo(t)
        desenhar(t, "retangulo", p0=(50, -20, -10), p1=(50, 120, 60), normal=(1, 0, 0))
        self.assertEqual(len(t.faces), 7)
        d = intersectar(t)
        self.assertEqual(t.counts(), {"vertices": 16, "edges": 24, "faces": 12})
        self.assertTrue(d["faces"]["added"])
        areas = sorted(round(t.face_area(f), 3) for f in t.faces)
        self.assertIn(5000.0, areas)  # a seção do cubo (100 x 50)

    def test_sem_cruzamento_nao_muda(self):
        t = Topology()
        cubo(t)
        desenhar(t, "retangulo", p0=(300, 0, 0), p1=(400, 100, 0))
        antes = t.counts()
        intersectar(t)
        self.assertEqual(t.counts(), antes)

    def test_coplanares_sao_ignoradas(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        antes = t.counts()
        intersectar(t)
        self.assertEqual(t.counts(), antes)

    def test_so_as_faces_dadas(self):
        t = Topology()
        cubo(t)
        desenhar(t, "retangulo", p0=(50, -20, -10), p1=(50, 120, 60), normal=(1, 0, 0))
        plano = max(t.faces)
        topo = next(i for i, f in t.faces.items() if f.normal[2] > 0.9 and t.verts[f.outer[0]][2] > 40)
        intersectar(t, [plano, topo])
        self.assertEqual(len(t.faces), 8)  # só o topo foi dividido

    def test_face_inexistente(self):
        with self.assertRaises(ValueError):
            intersectar(Topology(), [1])


if __name__ == "__main__":
    unittest.main()
