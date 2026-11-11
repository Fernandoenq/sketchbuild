"""F3: Push/Pull contra os dados golden do SketchUp real (docs/f0)."""
import unittest

from core.topology import Topology
from core.topology.draw import desenhar
from core.topology.pushpull import empurrar
from test_topology_golden import GoldenCase, etapa


def cubo():
    t = Topology()
    desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
    fid = next(iter(t.faces))
    empurrar(t, fid, -50)  # a normal da face no chão é -Z: -50 sobe
    return t


def topo(t):
    return max(t.faces, key=lambda i: t.faces[i].normal[2] * 1000 + t.verts[t.faces[i].outer[0]][2])


class TestPushPull(GoldenCase):
    def test_r04_retangulo_vira_cubo(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        d = empurrar(t, next(iter(t.faces)), -50)
        self.confere(t, etapa("r04", "depois"))
        self.assertEqual(len(d["faces"]["added"]), 5)

    def test_normais_para_fora(self):
        t = cubo()
        centro = (50, 50, 25)
        for f in t.faces.values():
            pts = [t.verts[v] for v in f.outer]
            c = tuple(sum(p[i] for p in pts) / len(pts) for i in range(3))
            self.assertGreater(sum(f.normal[i] * (c[i] - centro[i]) for i in range(3)), 0)

    def test_mover_o_topo_estica_as_paredes(self):
        t = cubo()
        empurrar(t, topo(t), 30)
        self.assertEqual(t.counts(), {"vertices": 8, "edges": 12, "faces": 6})
        self.assertAlmostEqual(max(p[2] for p in t.verts.values()), 80)

    def test_r05_empurrar_tudo_colapsa(self):
        t = cubo()
        empurrar(t, topo(t), -50)
        self.confere(t, etapa("r05", "apos_pushpull_negativo_total"))

    def test_passar_do_outro_lado_da_erro(self):
        t = cubo()
        with self.assertRaises(ValueError):
            empurrar(t, topo(t), -60)

    def test_r11_furo_vazado(self):
        t = cubo()
        desenhar(t, "retangulo", p0=(30, 30, 50), p1=(70, 70, 50))
        self.confere(t, etapa("r11", "cubo_com_face_no_topo"))
        interna = min(t.faces, key=lambda i: t.face_area(i))
        empurrar(t, interna, -50)
        self.confere(t, etapa("r11", "apos_pushpull_vazado"))

    def test_face_inexistente(self):
        with self.assertRaises(ValueError):
            empurrar(Topology(), 1, 10)


if __name__ == "__main__":
    unittest.main()
