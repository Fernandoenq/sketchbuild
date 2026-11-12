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


class TestCombinarGrupos(unittest.TestCase):
    def _dois_grupos(self, deslocamento=(50, 50, 0)):
        c = Cena()
        ids = []
        for _ in range(2):
            desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
            empurrar(c.topo, max(c.topo.faces), -50)
            ids.append(c.criar_grupo(faces=list(c.topo.faces)))
        m = list(c.instancias[ids[1]].transformacao)
        m[12], m[13], m[14] = deslocamento
        c.instancias[ids[1]].transformacao = m
        return c, ids

    def _volume(self, c, iid):
        from core.topology.solido import volume
        t = c.defs[c.instancias[iid].definicao]
        return volume(t, list(t.faces))

    def test_uniao_subtracao_e_intersecao_usam_a_matriz_da_instancia(self):
        esperado = {"uniao": 875000.0, "subtracao": 375000.0, "intersecao": 125000.0}
        for op, vol in esperado.items():
            with self.subTest(op):
                c, (a, b) = self._dois_grupos()
                r = c.combinar_grupos(a, b, op, nome="Resultado")
                self.assertEqual(list(c.instancias), [r])  # as duas de origem saíram
                self.assertEqual(c.instancias[r].tipo, "grupo")
                self.assertEqual(c.nomes[c.instancias[r].definicao], "Resultado")
                self.assertEqual(len(c.defs), 2)  # raiz + resultado; as definições de origem foram embora
                self.assertAlmostEqual(self._volume(c, r), vol, places=4)

    def test_sem_encontro_a_interseccao_e_vazia(self):
        c, (a, b) = self._dois_grupos((500, 0, 0))
        with self.assertRaises(ValueError):
            c.combinar_grupos(a, b, "intersecao")

    def test_aparar_mantem_o_segundo_inalterado(self):
        c, (a, b) = self._dois_grupos()
        r = c.aparar_grupos(a, b)
        self.assertEqual(sorted(c.instancias), sorted([r, b]))
        self.assertAlmostEqual(self._volume(c, r), 375000.0, places=4)
        self.assertEqual(c.instancias[b].transformacao[12:14], [50, 50])  # B segue onde estava
        self.assertAlmostEqual(self._volume(c, b), 500000.0, places=4)

    def test_aparar_recusa_quando_b_cobre_a(self):
        c, (a, b) = self._dois_grupos((0, 0, 0))
        with self.assertRaises(ValueError):
            c.aparar_grupos(a, b)

    def test_dividir_gera_tres_pedacos_que_somam_a_uniao(self):
        c, (a, b) = self._dois_grupos()
        novas = c.dividir_grupos(a, b)
        self.assertEqual(sorted(c.instancias), sorted(novas))
        vols = sorted(self._volume(c, i) for i in novas)
        for v, e in zip(vols, [125000.0, 375000.0, 375000.0]):
            self.assertAlmostEqual(v, e, places=4)

    def test_dividir_sem_volume_comum_recusa(self):
        c, (a, b) = self._dois_grupos((500, 0, 0))
        with self.assertRaises(ValueError):
            c.dividir_grupos(a, b)
        self.assertEqual(sorted(c.instancias), sorted([a, b]))  # nada mudou

    def test_recusas(self):
        c, (a, b) = self._dois_grupos()
        with self.assertRaises(ValueError):
            c.combinar_grupos(a, a, "uniao")
        with self.assertRaises(ValueError):
            c.combinar_grupos(a, 99, "uniao")
        c.instancias[b].transformacao[0] = -1.0  # espelha em x
        with self.assertRaises(ValueError):
            c.combinar_grupos(a, b, "uniao")


if __name__ == "__main__":
    unittest.main()
