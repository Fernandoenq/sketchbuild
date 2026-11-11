"""F4: Mover, Rotacionar, Escalar e Offset sobre o núcleo de topologia."""
import unittest

from core.topology import Topology
from core.topology.draw import desenhar
from core.topology.edit import escalar, mover, offset, rotacionar, vertices_da_selecao
from core.topology.pushpull import empurrar


def cubo():
    t = Topology()
    desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
    empurrar(t, next(iter(t.faces)), -50)
    return t


def caixa(t):
    xs = [p[0] for p in t.verts.values()]
    ys = [p[1] for p in t.verts.values()]
    zs = [p[2] for p in t.verts.values()]
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


class TestEdicao(unittest.TestCase):
    def test_mover_tudo(self):
        t = cubo()
        ids = set(t.verts)
        d = mover(t, ids, (10, 20, 30))
        self.assertEqual(caixa(t)[0], (10, 20, 30))
        self.assertEqual(len(d["vertices"]["changed"]), 8)
        self.assertEqual(t.counts(), {"vertices": 8, "edges": 12, "faces": 6})

    def test_mover_a_face_do_topo_estica(self):
        t = cubo()
        topo = max(t.faces, key=lambda i: t.verts[t.faces[i].outer[0]][2] + t.faces[i].normal[2])
        mover(t, vertices_da_selecao(t, faces=[topo]), (0, 0, 20))
        self.assertAlmostEqual(caixa(t)[1][2], 70)

    def test_mover_um_vertice_quebra_planaridade_e_desfaz(self):
        t = cubo()
        antes = dict(t.verts)
        v = max(t.verts, key=lambda i: t.verts[i][0] + t.verts[i][1] + t.verts[i][2])
        with self.assertRaises(ValueError):
            mover(t, {v}, (0, 0, 10))
        self.assertEqual(t.verts, antes)

    def test_rotacionar_90_no_z(self):
        t = cubo()
        rotacionar(t, set(t.verts), 90, centro=(50, 50, 0))
        (x0, y0, z0), (x1, y1, z1) = caixa(t)
        for a, b in zip((x0, y0, z0, x1, y1, z1), (0, 0, 0, 100, 100, 50)):
            self.assertAlmostEqual(a, b, places=6)
        for f in t.faces.values():  # normais continuam para fora
            pts = [t.verts[v] for v in f.outer]
            c = [sum(p[i] for p in pts) / len(pts) for i in range(3)]
            self.assertGreater(sum(f.normal[i] * (c[i] - (50, 50, 25)[i]) for i in range(3)), 0)

    def test_escalar_dobra(self):
        t = cubo()
        escalar(t, set(t.verts), 2, centro=(0, 0, 0))
        self.assertEqual(caixa(t)[1], (200, 200, 100))

    def test_escalar_nao_uniforme_mantem_planaridade(self):
        t = cubo()
        escalar(t, set(t.verts), (1, 2, 3), centro=(0, 0, 0))
        self.assertEqual(caixa(t)[1], (100, 200, 150))

    def test_escalar_negativo_recusado(self):
        with self.assertRaises(ValueError):
            escalar(cubo(), {1}, -1)

    def test_offset_para_dentro(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        fid = next(iter(t.faces))
        offset(t, fid, -10)
        self.assertEqual(t.counts(), {"vertices": 8, "edges": 8, "faces": 2})
        areas = sorted(round(t.face_area(f), 3) for f in t.faces)
        self.assertEqual(areas, [3600.0, 6400.0])

    def test_offset_para_fora(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        offset(t, next(iter(t.faces)), 10)
        self.assertEqual(t.counts(), {"vertices": 8, "edges": 8, "faces": 2})
        self.assertEqual(sorted(round(t.face_area(f), 3) for f in t.faces), [4400.0, 10000.0])

    def test_offset_em_circulo(self):
        t = Topology()
        desenhar(t, "circulo", centro=(0, 0, 0), raio=50)
        offset(t, next(iter(t.faces)), -5)
        self.assertEqual(t.counts()["faces"], 2)
        self.assertEqual(t.counts()["vertices"], 48)

    def test_erros(self):
        t = cubo()
        with self.assertRaises(ValueError):
            vertices_da_selecao(t)
        with self.assertRaises(ValueError):
            mover(t, {1}, (0, 0, 0))
        with self.assertRaises(ValueError):
            offset(t, 999, 5)


if __name__ == "__main__":
    unittest.main()
