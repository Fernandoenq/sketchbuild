"""Auditoria (A5), parte E: reexibir entidades e esboço técnico, com valores calculados à mão."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.technical_sketch_shader import TechnicalSketchShader  # noqa: E402
from core.unhide_entities_engine import UnhideEntitiesEngine  # noqa: E402


def _ents(n=4):
    return [{"id": str(i)} for i in range(1, n + 1)]


class TestReexibir(unittest.TestCase):
    def test_ocultar_so_conta_as_visiveis_e_empilha(self):
        e, pilha = _ents(), []
        r = UnhideEntitiesEngine.hide_entities(e, ["1", "2"], pilha)
        self.assertEqual((r["hidden_count"], r["history_depth"]), (2, 1))
        r = UnhideEntitiesEngine.hide_entities(e, ["2", "3"], pilha)  # o 2 já estava oculto
        self.assertEqual((r["hidden_ids"], r["history_depth"]), (["3"], 2))
        self.assertEqual(UnhideEntitiesEngine.hide_entities(e, ["9"], pilha)["history_depth"], 2)  # id inexistente

    def test_instance_id_vale_como_id(self):
        e = [{"instance_id": 7}]
        UnhideEntitiesEngine.hide_entities(e, ["7"])
        self.assertTrue(e[0]["hidden"])

    def test_ultimo_desfaz_so_o_topo_da_pilha(self):
        e, pilha = _ents(), []
        UnhideEntitiesEngine.hide_entities(e, ["1", "2"], pilha)
        UnhideEntitiesEngine.hide_entities(e, ["3"], pilha)
        r = UnhideEntitiesEngine.unhide(e, "last", history_stack=pilha)
        self.assertEqual((r["unhidden_ids"], r["remaining_hidden_count"], r["history_depth"]), (["3"], 2, 1))
        self.assertEqual(UnhideEntitiesEngine.unhide(e, "last", history_stack=[])["unhidden_count"], 0)

    def test_selecao_limpa_o_historico(self):
        e, pilha = _ents(), []
        UnhideEntitiesEngine.hide_entities(e, ["1", "2"], pilha)
        UnhideEntitiesEngine.hide_entities(e, ["3"], pilha)
        r = UnhideEntitiesEngine.unhide(e, "selection", ["3", "2"], pilha)
        self.assertEqual((r["unhidden_count"], r["remaining_hidden_count"]), (2, 1))
        self.assertEqual(pilha, [["1"]])  # o grupo do 3 esvaziou e saiu

    def test_tudo_zera_a_pilha_e_escopo_invalido_falha(self):
        e, pilha = _ents(), []
        UnhideEntitiesEngine.hide_entities(e, ["1", "2", "3"], pilha)
        r = UnhideEntitiesEngine.unhide(e, " ALL ", history_stack=pilha)
        self.assertEqual((r["unhidden_count"], r["remaining_hidden_count"], r["history_depth"]), (3, 0, 0))
        with self.assertRaises(ValueError):
            UnhideEntitiesEngine.unhide(e, "nada")


def _face(z, normal, x0=0.0):
    return {"vertices": [(x0, 0, z), (x0 + 1, 0, z), (x0 + 1, 1, z), (x0, 1, z)], "normal": normal}


class TestEsbocoTecnico(unittest.TestCase):
    def test_aresta_viva_e_borda_livre(self):
        # duas faces compartilhando a aresta x=1: normais a 90° (viva) ou iguais (coplanar, some)
        a = {"vertices": [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], "normal": (0, 0, 1)}
        b = {"vertices": [(1, 1, 0), (1, 0, 0), (1, 0, 1), (1, 1, 1)], "normal": (1, 0, 0)}
        vivas = TechnicalSketchShader.filter_sharp_edges([a, b], 25.0)
        self.assertIn(((1, 0, 0), (1, 1, 0)), vivas)
        c = {"vertices": [(1, 1, 0), (1, 0, 0), (2, 0, 0), (2, 1, 0)], "normal": (0, 0, 1)}
        vivas = TechnicalSketchShader.filter_sharp_edges([a, c], 25.0)
        self.assertNotIn(((1, 0, 0), (1, 1, 0)), vivas)  # coplanar
        self.assertEqual(len(vivas), 6)  # contorno do retângulo 2x1 (6 arestas de borda livre)

    def test_svg_alonga_a_aresta_pelo_overshoot(self):
        # aresta horizontal de 1 m, escala 100 px/m, overshoot 10 mm = 1 px em cada ponta
        svg = TechnicalSketchShader.generate_sketch_svg([((0, 0, 0), (1, 0, 0))], overshoot_mm=10.0, view_scale=100.0)
        self.assertIn('<line x1="399.0" y1="480.0" x2="501.0" y2="480.0" />', svg)

    def test_aresta_nula_e_pulada_e_arquivo_e_gravado(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "e.svg")
            svg = TechnicalSketchShader.generate_sketch_svg([((0, 0, 0), (0, 5, 0))], output_path=p)
            self.assertEqual(svg.count("<line"), 0)  # só varia em y: projeção frontal vira ponto
            with open(p, encoding="utf-8") as fh:
                self.assertEqual(fh.read(), svg)


if __name__ == "__main__":
    unittest.main()
