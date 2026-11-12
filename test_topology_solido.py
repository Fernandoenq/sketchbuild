"""M12: sólido válido, volume e booleanas (união, subtração, interseção) entre dois cubos."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.solido import booleana, combinar, eh_solido, volume  # noqa: E402


def cubo(t, x, y, z, s):
    """Seis faces de um cubo de lado `s` com o canto mínimo em (x, y, z); devolve os ids."""
    def P(i, j, k):
        return (x + i * s, y + j * s, z + k * s)
    lados = [[(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
             [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
             [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]]
    return [t.add_face([P(*p) for p in f]) for f in lados]


def dois(deslocamento=(5, 5, 5)):
    t = Topology()
    a = cubo(t, 0, 0, 0, 10)
    b = cubo(t, *deslocamento, 10)
    return t, a, b


class TestSolido(unittest.TestCase):
    def test_cubo_e_valido(self):
        t = Topology()
        a = cubo(t, 0, 0, 0, 10)
        self.assertEqual(len(a), 6)
        self.assertAlmostEqual(volume(t, a), 1000.0)
        self.assertTrue(eh_solido(t, a))

    def test_aberto_nao_e_solido(self):
        t = Topology()
        a = cubo(t, 0, 0, 0, 10)
        self.assertFalse(eh_solido(t, a[:5]))  # sem a tampa
        with self.assertRaises(ValueError):
            volume(t, a[:5])
        with self.assertRaises(ValueError):
            volume(t, [999])
        self.assertFalse(eh_solido(t, []))

    def test_uniao(self):
        t, a, b = dois()
        r = booleana(t, a, b, "uniao")
        self.assertAlmostEqual(volume(t, r["faces"]), 2000 - 125)
        self.assertEqual(sorted(t.faces), r["faces"])

    def test_subtracao(self):
        t, a, b = dois()
        r = booleana(t, a, b, "subtracao")
        self.assertAlmostEqual(volume(t, r["faces"]), 1000 - 125)

    def test_interseccao(self):
        t, a, b = dois()
        r = booleana(t, a, b, "intersecao")
        self.assertAlmostEqual(volume(t, r["faces"]), 125.0)
        self.assertEqual(len(r["faces"]), 6)

    def test_disjuntos(self):
        t, a, b = dois((50, 0, 0))
        self.assertAlmostEqual(volume(t, a), 1000.0)
        r = booleana(t, a, b, "uniao")
        self.assertEqual(len(r["faces"]), 12)  # dois sólidos separados: nenhum corte
        t, a, b = dois((50, 0, 0))
        self.assertEqual(booleana(t, a, b, "intersecao")["faces"], [])

    def test_um_dentro_do_outro(self):
        t = Topology()
        a = cubo(t, 0, 0, 0, 10)
        b = cubo(t, 3, 3, 3, 4)
        r = booleana(t, a, b, "subtracao")  # cavidade interna: casca com 12 faces e volume 1000 - 64
        self.assertEqual(len(r["faces"]), 12)
        self.assertAlmostEqual(volume(t, r["faces"]), 1000 - 64)

    def test_erros_nao_alteram_o_modelo(self):
        t, a, b = dois()
        antes = (dict(t.verts), dict(t.edges), len(t.faces))
        with self.assertRaises(ValueError):
            booleana(t, a, b, "xor")
        with self.assertRaises(ValueError):
            booleana(t, a[:5], b, "uniao")
        with self.assertRaises(ValueError):
            booleana(t, a, a, "uniao")
        self.assertEqual((dict(t.verts), dict(t.edges), len(t.faces)), antes)

    def test_tag_original_volta(self):
        t, a, b = dois()
        t.tags["Caixa"] = {"visivel": True}
        for f in a:
            t.faces[f].tag = "Caixa"
        r = booleana(t, a, b, "uniao")
        self.assertTrue(all(x.tag in (None, "Caixa") for x in t.faces.values()))
        self.assertTrue(any(t.faces[f].tag == "Caixa" for f in r["faces"]))


class TestCombinar(unittest.TestCase):
    """Sólidos de modelos separados (grupos) que se encostam ou coincidem em faces inteiras."""

    def _par(self, deslocamento):
        ta, tb = Topology(), Topology()
        return ta, cubo(ta, 0, 0, 0, 10), tb, cubo(tb, *deslocamento, 10)

    def test_encostados_uniao_vira_caixa_maior(self):
        ta, fa, tb, fb = self._par((10, 0, 0))
        w = combinar(ta, fa, tb, fb, "uniao")
        self.assertEqual(len(w.faces), 10)  # a face comum some dos dois lados
        self.assertAlmostEqual(volume(w, list(w.faces)), 2000.0)

    def test_encostados_subtracao_devolve_a_e_interseccao_e_vazia(self):
        ta, fa, tb, fb = self._par((10, 0, 0))
        w = combinar(ta, fa, tb, fb, "subtracao")
        self.assertEqual(len(w.faces), 6)
        self.assertAlmostEqual(volume(w, list(w.faces)), 1000.0)
        self.assertEqual(combinar(ta, fa, tb, fb, "intersecao").faces, {})

    def test_copia_identica(self):
        ta, fa, tb, fb = self._par((0, 0, 0))
        for op, faces in (("uniao", 6), ("intersecao", 6), ("subtracao", 0)):
            w = combinar(ta, fa, tb, fb, op)
            self.assertEqual(len(w.faces), faces, op)
            if faces:
                self.assertAlmostEqual(volume(w, list(w.faces)), 1000.0, msg=op)

    def test_menor_encostado_numa_parte_da_face(self):
        # as faces laterais do menor cortam a face de A e deixam pedaços idênticos dos dois lados
        ta, fa = Topology(), None
        fa = cubo(ta, 0, 0, 0, 10)
        tc = Topology()
        pequeno = cubo(tc, 10, 0, 0, 5)
        w = combinar(ta, fa, tc, pequeno, "uniao")
        self.assertAlmostEqual(volume(w, list(w.faces)), 1000 + 125)
        w = combinar(ta, fa, tc, pequeno, "subtracao")
        self.assertAlmostEqual(volume(w, list(w.faces)), 1000.0)
        self.assertEqual(combinar(ta, fa, tc, pequeno, "intersecao").faces, {})

    def test_que_passa_da_borda(self):
        ta, fa, tb, fb = self._par((10, 5, 0))  # a face de B ultrapassa a de A em y
        w = combinar(ta, fa, tb, fb, "uniao")
        self.assertAlmostEqual(volume(w, list(w.faces)), 2000.0)

    def test_dentro_de_um_vazio_tangente(self):
        ta, fa, tb, fb = self._par((0, 0, 10))  # B sobre o topo de A, mesma pegada
        w = combinar(ta, fa, tb, fb, "uniao")
        self.assertEqual(len(w.faces), 10)
        self.assertAlmostEqual(volume(w, list(w.faces)), 2000.0)

    def test_combinar_valida_os_solidos(self):
        ta, fa, tb, fb = self._par((10, 0, 0))
        with self.assertRaises(ValueError):
            combinar(ta, fa[:5], tb, fb, "uniao")
        with self.assertRaises(ValueError):
            combinar(ta, fa, tb, fb, "xor")


class TestCortePorPercurso(unittest.TestCase):
    def test_laco_que_encosta_no_contorno_divide_a_face(self):
        t = Topology()
        f = t.add_face([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)])
        nova = t.add_face([(5, 5, 0), (10, 5, 0), (10, 10, 0), (5, 10, 0)])  # canto de dentro até a borda
        self.assertEqual(len(t.faces), 2)
        areas = sorted(round(t.face_area(i), 6) for i in t.faces)
        self.assertEqual(areas, [25.0, 75.0])  # o resto virou um L, sem sobrepor
        self.assertIn(nova, t.faces)
        self.assertEqual(len(t.faces[f].outer), 6)

    def test_nova_face_herda_tag_e_pintura(self):
        t = Topology()
        f = t.add_face([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)])
        t.faces[f].tag, t.faces[f].frente = "Piso", "Tinta"
        nova = t.add_face([(0, 0, 0), (4, 0, 0), (4, 4, 0), (0, 4, 0)])
        self.assertEqual((t.faces[nova].tag, t.faces[nova].frente), ("Piso", "Tinta"))


if __name__ == "__main__":
    unittest.main()
