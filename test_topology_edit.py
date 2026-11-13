"""F4: Mover, Rotacionar, Escalar e Offset sobre o núcleo de topologia."""
import unittest

from core.topology import Topology
from core.topology.draw import desenhar
from core.topology.edit import apagar, escalar, mover, offset, rotacionar, vertices_da_selecao
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


class TestOffsetColapso(unittest.TestCase):
    def _l(self):
        t = Topology()
        return t, t.add_face([(0, 0, 0), (100, 0, 0), (100, 20, 0), (20, 20, 0), (20, 100, 0), (0, 100, 0)])

    def test_para_dentro_alem_da_espessura_recusa_e_nao_altera(self):
        for d in (-11, -30):
            t, f = self._l()
            antes = (dict(t.verts), dict(t.edges), len(t.faces))
            with self.assertRaises(ValueError):
                offset(t, f, d)
            self.assertEqual((dict(t.verts), dict(t.edges), len(t.faces)), antes)

    def test_quadrado_colapsa_no_centro_e_alem(self):
        for d in (-5, -6, -20):
            t = Topology()
            f = t.add_face([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)])
            with self.assertRaises(ValueError):
                offset(t, f, d)

    def test_quina_concava_e_distancia_valida(self):
        t, f = self._l()
        offset(t, f, -9)  # quinas côncavas (L) com folga de 1 até colapsar
        self.assertEqual(len(t.faces), 2)
        t, f = self._l()
        offset(t, f, 50)  # para fora nunca colapsa um L
        self.assertEqual(len(t.faces), 2)


class TestApagar(unittest.TestCase):
    def test_aresta_do_cubo_leva_as_duas_faces(self):
        t = cubo()
        e = next(iter(t.edges))
        apagar(t, arestas=[e])
        self.assertEqual((len(t.faces), len(t.edges)), (4, 11))  # SDK: 6f/12a -> 4f/11a

    def test_face_apagada_deixa_as_arestas(self):
        t = cubo()
        apagar(t, faces=[next(iter(t.faces))])
        self.assertEqual((len(t.faces), len(t.edges), len(t.verts)), (5, 12, 8))  # SDK: 5f/12a

    def test_linha_solta_some_com_os_vertices(self):
        t = Topology()
        desenhar(t, "linha", pontos=[(0, 0, 0), (10, 0, 0)])
        apagar(t, arestas=list(t.edges))
        self.assertEqual((len(t.edges), len(t.verts)), (0, 0))

    def test_aresta_de_curva_leva_a_curva_inteira(self):
        t = Topology()
        desenhar(t, "circulo", centro=(0, 0, 0), raio=10, lados=12)
        self.assertEqual(len(t.curvas), 1)
        apagar(t, arestas=[next(iter(t.edges))])
        self.assertEqual((len(t.edges), len(t.faces), len(t.verts), len(t.curvas)), (0, 0, 0, 0))

    def test_divisoria_apagada_devolve_a_face_inteira(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(30, 10, 0))
        desenhar(t, "linha", pontos=[(10, 0, 0), (10, 10, 0)])
        desenhar(t, "linha", pontos=[(20, 0, 0), (20, 10, 0)])
        self.assertEqual((len(t.faces), len(t.edges)), (3, 10))
        div = next(e for e, (a, b) in t.edges.items() if t.verts[a][0] == t.verts[b][0] == 10)
        apagar(t, arestas=[div])
        self.assertEqual((len(t.faces), len(t.edges)), (2, 7))  # SDK: 3f/10a -> 2f/7a (funde e junta os vértices colineares)
        div = next(e for e, (a, b) in t.edges.items() if t.verts[a][0] == t.verts[b][0] == 20)
        apagar(t, arestas=[div])
        self.assertEqual((len(t.faces), len(t.edges), len(t.verts)), (1, 4, 4))

    def test_faces_coplanares_em_L_fundem_mesmo_sem_vertice_colinear(self):
        t = Topology()
        desenhar(t, "linha", pontos=[(0, 0, 0), (20, 0, 0), (20, 10, 0), (10, 10, 0), (10, 20, 0), (0, 20, 0), (0, 0, 0)])
        desenhar(t, "linha", pontos=[(0, 10, 0), (10, 10, 0)])
        self.assertEqual(len(t.faces), 2)
        meio = next(e for e, (a, b) in t.edges.items() if {t.verts[a], t.verts[b]} == {(0, 10, 0), (10, 10, 0)})
        apagar(t, arestas=[meio])
        self.assertEqual((len(t.faces), len(t.edges)), (1, 6))  # SDK: 2f/8a -> 1f/6a

    def test_aresta_de_furo_apaga_a_face_interna_e_a_externa_perde_o_furo(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        desenhar(t, "retangulo", p0=(20, 20, 0), p1=(40, 40, 0))
        self.assertEqual(len(t.faces), 2)
        furo = next(e for e, (a, b) in t.edges.items() if min(t.verts[a][0], t.verts[b][0]) >= 20 and max(t.verts[a][0], t.verts[b][0]) <= 40)
        apagar(t, arestas=[furo])
        self.assertEqual((len(t.faces), len(t.edges)), (1, 7))  # SDK: 2f/8a -> 1f/7a, a face que sobra tem 4 vértices
        (f,) = t.faces.values()
        self.assertEqual((len(f.outer), len(f.holes)), (4, 0))

    def test_galho_apagado_funde_os_dois_trechos_colineares(self):
        t = Topology()
        desenhar(t, "linha", pontos=[(0, 0, 0), (10, 0, 0), (20, 0, 0)])
        desenhar(t, "linha", pontos=[(10, 0, 0), (10, 10, 0)])
        galho = next(e for e, (a, b) in t.edges.items() if t.verts[a][1] != t.verts[b][1])
        apagar(t, arestas=[galho])
        self.assertEqual(len(t.edges), 1)  # SDK: 3 arestas -> 1

    def test_recusa_vazio_e_inexistente(self):
        t = cubo()
        with self.assertRaises(ValueError):
            apagar(t)
        with self.assertRaises(ValueError):
            apagar(t, arestas=[9999])
        self.assertEqual(len(t.faces), 6)


if __name__ == "__main__":
    unittest.main()
