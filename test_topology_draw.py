"""F2: as ferramentas de desenho contra os dados golden do SketchUp real (docs/f0)."""
import math
import unittest

from core.topology import Topology
from core.topology.draw import desenhar, eixos, pontos_poligono
from test_topology_golden import GoldenCase, etapa


class TestDesenho(GoldenCase):
    def test_retangulo_r03(self):
        t = Topology()
        d = desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        self.confere(t, etapa("r03", "depois"))
        self.assertEqual((len(d["vertices"]["added"]), len(d["edges"]["added"]), len(d["faces"]["added"])), (4, 4, 1))

    def test_linhas_fecham_laco_r02(self):
        t = Topology()
        desenhar(t, "linha", pontos=[(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0), (0, 0, 0)])
        self.confere(t, etapa("r02", "apos_find_faces"))

    def test_linha_solta_r01(self):
        t = Topology()
        desenhar(t, "linha", pontos=[(0, 0, 0), (100, 0, 0)])
        self.confere(t, etapa("r01", "depois"))

    def test_circulo_r09(self):
        t = Topology()
        desenhar(t, "circulo", centro=(0, 0, 0), raio=50)
        self.confere(t, etapa("r09", "com_face"))

    def test_arco_e_raios_r13(self):
        t = Topology()
        desenhar(t, "arco", centro=(0, 0, 0), raio=50, ang_ini=0, ang_fim=90, normal=(0, -1, 0), lados=12)
        desenhar(t, "linha", pontos=[(0, 0, 0), (50, 0, 0)])
        d = desenhar(t, "linha", pontos=[(0, 0, 0), (0, 0, 50)])
        self.confere(t, etapa("r13", "apos_find_faces"))
        self.assertEqual(len(d["faces"]["added"]), 1)

    def test_linha_dividindo_face_r06(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        d = desenhar(t, "linha", pontos=[(50, 0, 0), (50, 100, 0)])
        self.assertEqual(len(t.faces), 2)
        self.assertTrue(d["faces"]["removed"] or d["faces"]["changed"])

    def test_face_dentro_de_face_r10(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(200, 200, 0))
        desenhar(t, "retangulo", p0=(50, 50, 0), p1=(150, 150, 0))
        self.confere(t, etapa("r10", "depois"))

    def test_poligono_hexagono(self):
        t = Topology()
        desenhar(t, "poligono", centro=(0, 0, 0), raio=10, lados=6)
        self.assertEqual(t.counts(), {"vertices": 6, "edges": 6, "faces": 1})
        # circunscrito: a distância do centro ao meio do lado é o raio dado
        pts = pontos_poligono((0, 0, 0), 10, lados=6, circunscrito=True)
        meio = [(pts[0][i] + pts[1][i]) / 2 for i in range(3)]
        self.assertAlmostEqual(math.hypot(*meio), 10, places=6)

    def test_mao_livre_fechada_vira_face(self):
        t = Topology()
        desenhar(t, "mao_livre", pontos=[(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0), (0, 0, 0)])
        self.assertEqual(t.counts(), {"vertices": 4, "edges": 4, "faces": 1})

    def test_retangulo_em_parede(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 0, 50), normal=(0, -1, 0))
        self.assertEqual(t.counts(), {"vertices": 4, "edges": 4, "faces": 1})
        self.assertAlmostEqual(t.face_area(next(iter(t.faces))), 5000, places=3)

    def test_eixos_ortogonais(self):
        for n in [(0, 0, 1), (0, -1, 0), (1, 1, 1), (0, 0, -1)]:
            x, y = eixos(n)
            self.assertAlmostEqual(sum(a * b for a, b in zip(x, y)), 0, places=9)

    def test_ferramenta_desconhecida(self):
        with self.assertRaises(ValueError):
            desenhar(Topology(), "pincel")


if __name__ == "__main__":
    unittest.main()


class TestRetanguloRotacionado(unittest.TestCase):
    def test_lado_inclinado_e_largura_pelo_terceiro_ponto(self):
        t = Topology()
        desenhar(t, "retangulo_rotacionado", p0=(0, 0, 0), p1=(10, 10, 0), p2=(0, 10, 0))
        (f,) = t.faces.values()
        pts = [t.verts[v] for v in f.outer]
        self.assertEqual(len(pts), 4)
        lados = sorted(round(math.dist(pts[i], pts[(i + 1) % 4]), 6) for i in range(4))
        self.assertAlmostEqual(lados[0], 7.071068, places=5)  # largura = distância de p2 à reta p0-p1
        self.assertAlmostEqual(lados[3], 14.142136, places=5)
        for i in range(4):  # cantos retos
            a, b, c = pts[i - 1], pts[i], pts[(i + 1) % 4]
            self.assertAlmostEqual(sum((a[k] - b[k]) * (c[k] - b[k]) for k in range(3)), 0.0, places=6)

    def test_largura_zero_e_lado_zero_recusam(self):
        t = Topology()
        with self.assertRaises(ValueError):
            desenhar(t, "retangulo_rotacionado", p0=(0, 0, 0), p1=(10, 0, 0), p2=(5, 0, 0))
        with self.assertRaises(ValueError):
            desenhar(t, "retangulo_rotacionado", p0=(0, 0, 0), p1=(0, 0, 0), p2=(5, 5, 0))
