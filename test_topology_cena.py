"""F5: grupos e componentes."""
import unittest

from core.topology.cena import Cena
from core.topology.draw import desenhar
from core.topology.pushpull import empurrar


def cena_com_cubo():
    c = Cena()
    desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
    empurrar(c.topo, max(c.topo.faces), -50)
    return c


class TestCena(unittest.TestCase):
    def test_grupo_leva_a_geometria(self):
        c = cena_com_cubo()
        iid = c.criar_grupo(faces=list(c.topo.faces))
        self.assertEqual(c.topo.counts(), {"vertices": 0, "edges": 0, "faces": 0})
        d = c.defs[c.instancias[iid].definicao]
        self.assertEqual(d.counts(), {"vertices": 8, "edges": 12, "faces": 6})
        self.assertEqual(c.instancias[iid].tipo, "grupo")

    def test_grupo_parcial_deixa_o_resto(self):
        c = cena_com_cubo()
        topo = next(i for i, f in c.topo.faces.items() if f.normal[2] > 0.9)
        c.criar_grupo(faces=[topo])
        self.assertEqual(len(c.topo.faces), 5)
        self.assertEqual(len(c.defs[1].faces), 1)
        self.assertEqual(len(c.topo.edges), 12)  # as arestas ainda sustentam outras faces

    def test_entrar_editar_e_sair(self):
        c = cena_com_cubo()
        iid = c.criar_grupo(faces=list(c.topo.faces))
        c.entrar(iid)
        self.assertEqual(c.ativa, c.instancias[iid].definicao)
        desenhar(c.topo, "linha", pontos=[(0, 0, 100), (50, 0, 100)])
        self.assertEqual(len(c.defs[c.ativa].edges), 13)
        c.sair()
        self.assertEqual(c.ativa, 0)
        with self.assertRaises(ValueError):
            c.sair()

    def test_componente_compartilha_definicao(self):
        c = cena_com_cubo()
        a = c.criar_componente(faces=list(c.topo.faces), nome="Caixa")
        t = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 300, 0, 0, 1]
        b = c.instanciar(a, t)
        self.assertEqual(c.instancias[a].definicao, c.instancias[b].definicao)
        self.assertEqual(len(c.defs), 2)
        with self.assertRaises(ValueError):
            c.instanciar(999)

    def test_grupo_nao_tem_varias_instancias(self):
        c = cena_com_cubo()
        g = c.criar_grupo(faces=list(c.topo.faces))
        with self.assertRaises(ValueError):
            c.instanciar(g)

    def test_explodir_devolve_a_geometria_transformada(self):
        c = cena_com_cubo()
        g = c.criar_grupo(faces=list(c.topo.faces))
        c.instancias[g].transformacao = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 10, 20, 30, 1]
        c.explodir(g)
        self.assertEqual(c.topo.counts(), {"vertices": 8, "edges": 12, "faces": 6})
        self.assertEqual(min(p[0] for p in c.topo.verts.values()), 10)
        self.assertEqual(len(c.defs), 1)
        self.assertFalse(c.instancias)

    def test_selecao_vazia(self):
        with self.assertRaises(ValueError):
            Cena().criar_grupo()

    def test_resumo(self):
        c = cena_com_cubo()
        c.criar_grupo(faces=list(c.topo.faces))
        r = c.resumo()
        self.assertEqual(len(r["instancias"]), 1)
        self.assertEqual(r["definicoes"][1]["faces"], 6)


if __name__ == "__main__":
    unittest.main()
