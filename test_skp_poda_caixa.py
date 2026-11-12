"""Poda "total" recalcula a caixa 0x13a0 também com instâncias vivas (FORMATO-SKP 7); o oráculo é o mesmo desenho gravado
sem a geometria oculta (o gravador usa a regra conferida contra a SDK)."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.skp_hidden_pruner import podar_skp  # noqa: E402
from core.skp_topology_writer import gravar_cena  # noqa: E402
from core.topology.cena import Cena  # noqa: E402
from core.topology.draw import desenhar  # noqa: E402
from test_caixa_instancia import _giro_z, caixa_da_raiz  # noqa: E402


def _cena(oculta, tipo="componente", face_me=False):
    c = Cena()
    desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
    desenhar(c.topo, "retangulo", p0=(500, 0, 0), p1=(540, 40, 0))
    criar = c.criar_componente if tipo == "componente" else c.criar_grupo
    i = criar(faces=[max(c.topo.faces)], nome="G")
    c.instancias[i].transformacao = _giro_z(33, (1000, 2000, 50))
    if face_me:
        c.definir_comportamento(c.instancias[i].definicao, face_me=True)
    if oculta:
        c.entrar(i)
        desenhar(c.topo, "linha", pontos=[(5000, 5000, 0), (6000, 6000, 0)])
        e = max(c.topo.edges)
        c.topo.eflags[e] = c.topo.eflags.get(e, 0) | 1  # bit 0x01 do 0x07d3 = oculta
        c.sair()
    return c


def _cena_aninhada(oculta):
    """Raiz -> grupo G (girado) -> grupo N (girado) com a linha oculta longe dentro de N."""
    c = Cena()
    desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
    desenhar(c.topo, "retangulo", p0=(500, 0, 0), p1=(540, 40, 0))
    g = c.criar_grupo(faces=[max(c.topo.faces)], nome="G")
    c.instancias[g].transformacao = _giro_z(33, (1000, 2000, 50))
    c.entrar(g)
    desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(30, 30, 0))
    desenhar(c.topo, "retangulo", p0=(200, 0, 0), p1=(230, 30, 0))
    n = c.criar_grupo(faces=[max(c.topo.faces)], nome="N")
    c.instancias[n].transformacao = _giro_z(-20, (300, 100, 0))
    if oculta:
        c.entrar(n)
        desenhar(c.topo, "linha", pontos=[(5000, 5000, 0), (6000, 6000, 0)])
        e = max(c.topo.edges)
        c.topo.eflags[e] = c.topo.eflags.get(e, 0) | 1
        c.sair()
    c.sair()
    return c


class TestPodaRecalculaCaixaComInstancia(unittest.TestCase):
    def _confere(self, **kw):
        with tempfile.TemporaryDirectory() as d:
            a, b, p = (os.path.join(d, n) for n in ("a.skp", "b.skp", "p.skp"))
            gravar_cena(_cena(True, **kw), a)
            gravar_cena(_cena(False, **kw), b)
            antes = caixa_da_raiz(a)
            rel = podar_skp(a, p, "total")
            self.assertGreaterEqual(rel["geometria_arestas"], 1)
            depois, esperada = caixa_da_raiz(p), caixa_da_raiz(b)
            self.assertNotEqual(antes, esperada)  # a geometria oculta alargava a caixa
            for got, want in zip(depois, esperada):
                self.assertAlmostEqual(got, want, places=6)

    def test_componente(self):
        self._confere(tipo="componente")

    def test_grupo(self):
        self._confere(tipo="grupo")

    def test_componente_face_me(self):
        self._confere(tipo="componente", face_me=True)

    def test_definicoes_aninhadas(self):
        with tempfile.TemporaryDirectory() as d:
            a, b, p = (os.path.join(d, n) for n in ("a.skp", "b.skp", "p.skp"))
            gravar_cena(_cena_aninhada(True), a)
            gravar_cena(_cena_aninhada(False), b)
            podar_skp(a, p, "total")
            self.assertNotEqual(caixa_da_raiz(a), caixa_da_raiz(b))
            for got, want in zip(caixa_da_raiz(p), caixa_da_raiz(b)):
                self.assertAlmostEqual(got, want, places=6)

    def test_sem_nada_oculto_o_arquivo_fica_igual(self):
        with tempfile.TemporaryDirectory() as d:
            b, p = os.path.join(d, "b.skp"), os.path.join(d, "p.skp")
            gravar_cena(_cena(False), b)
            podar_skp(b, p, "total")
            self.assertEqual(caixa_da_raiz(p), caixa_da_raiz(b))


if __name__ == "__main__":
    unittest.main()
