"""F6: desfazer e refazer com log de operações."""
import unittest

from core.topology.cena import Cena
from core.topology.draw import desenhar
from core.topology.edit import escalar, mover, offset, vertices_da_selecao
from core.topology.historico import Historico
from core.topology.pushpull import empurrar


def foto(c: Cena):
    return {
        "ativa": c.ativa,
        "defs": {d: (dict(t.verts), dict(t.edges),
                     {i: (list(f.outer), [list(h) for h in f.holes], f.normal) for i, f in t.faces.items()})
                 for d, t in c.defs.items()},
        "inst": {i: (x.definicao, x.pai, x.nome, x.tipo, tuple(x.transformacao)) for i, x in c.instancias.items()},
    }


def sequencia(h: Historico):
    c = h.cena
    h.executar("retangulo", {}, lambda: desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0)))
    h.executar("pushpull", {}, lambda: empurrar(c.topo, max(c.topo.faces), -50))
    h.executar("mover", {}, lambda: mover(c.topo, set(c.topo.verts), (10, 0, 0)))
    h.executar("escalar", {}, lambda: escalar(c.topo, set(c.topo.verts), 2, centro=(0, 0, 0)))
    h.executar("circulo", {}, lambda: desenhar(c.topo, "circulo", centro=(500, 500, 0), raio=30))
    h.executar("offset", {}, lambda: offset(c.topo, max(c.topo.faces), -5))
    h.executar("grupo", {}, lambda: c.criar_grupo(faces=[min(c.topo.faces)]))


class TestHistorico(unittest.TestCase):
    def test_desfazer_tudo_e_refazer_tudo(self):
        c = Cena()
        h = Historico(c)
        inicial = foto(c)
        sequencia(h)
        final = foto(c)
        self.assertNotEqual(inicial, final)
        n = 0
        while h.pode_desfazer():
            h.desfazer()
            n += 1
        self.assertEqual(n, 7)
        self.assertEqual(foto(c), inicial)
        while h.pode_refazer():
            h.refazer()
        self.assertEqual(foto(c), final)

    def test_cada_passo_volta_ao_estado_anterior(self):
        c = Cena()
        h = Historico(c)
        fotos = [foto(c)]
        passos = [
            lambda: desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(10, 10, 0)),
            lambda: desenhar(c.topo, "linha", pontos=[(20, 0, 0), (30, 0, 0)]),
            lambda: desenhar(c.topo, "circulo", centro=(50, 50, 0), raio=5),
        ]
        for k, p in enumerate(passos):
            h.executar("p%d" % k, {}, p)
            fotos.append(foto(c))
        for esperado in reversed(fotos[:-1]):
            h.desfazer()
            self.assertEqual(foto(c), esperado)

    def test_nova_operacao_limpa_o_refazer(self):
        c = Cena()
        h = Historico(c)
        h.executar("a", {}, lambda: desenhar(c.topo, "linha", pontos=[(0, 0, 0), (1, 0, 0)]))
        h.desfazer()
        self.assertTrue(h.pode_refazer())
        h.executar("b", {}, lambda: desenhar(c.topo, "linha", pontos=[(0, 0, 0), (0, 1, 0)]))
        self.assertFalse(h.pode_refazer())

    def test_erro_na_operacao_desfaz_sozinho_e_nao_entra_no_historico(self):
        c = Cena()
        h = Historico(c)
        h.executar("a", {}, lambda: desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0)))
        antes = foto(c)

        def ruim():
            c.topo.verts[1] = (999.0, 0.0, 0.0)  # mexe e depois falha
            raise ValueError("falhou")

        with self.assertRaises(ValueError):
            h.executar("ruim", {}, ruim)
        self.assertEqual(foto(c), antes)
        self.assertEqual(h.resumo()["passos_desfazer"], ["a"])

    def test_vazio_e_limite(self):
        h = Historico(Cena(), limite=3)
        with self.assertRaises(ValueError):
            h.desfazer()
        with self.assertRaises(ValueError):
            h.refazer()
        for k in range(5):
            h.executar("p%d" % k, {}, lambda k=k: desenhar(h.cena.topo, "linha", pontos=[(k, 0, 0), (k, 5, 0)]))
        self.assertEqual(h.resumo()["passos_desfazer"], ["p2", "p3", "p4"])

    def test_log(self):
        h = Historico(Cena())
        h.executar("a", {"x": 1}, lambda: None)
        h.desfazer()
        ops = [x["operacao"] for x in h.resumo()["log"]]
        self.assertEqual(ops, ["a", "desfazer:a"])


if __name__ == "__main__":
    unittest.main()
