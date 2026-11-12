"""Poda de arestas e faces ocultas (modo "total"), com a SketchUpAPI como oráculo. Pula sem a DLL ou fora do Python 3.12."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.su_api import SketchUpAPI
    from core.skp_hidden_pruner import podar_skp, verificar_skp
    from tools.gerar_ocultos_api import gerar, gerar_curva
    _api = SketchUpAPI()
    _api.initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False


@unittest.skipUnless(DISPONIVEL, "precisa da SketchUpAPI.dll em Python 3.12")
class TestPodaDeGeometriaOculta(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def p(self, nome):
        return os.path.join(self.tmp.name, nome)

    def contar(self, caminho):
        m = _api.open_model(caminho)
        try:
            return m.count_summary()
        finally:
            m.close()

    def test_leitura_dos_flags(self):
        gerar(self.p("o.skp"))
        v = verificar_skp(self.p("o.skp"))
        # B e C ocultas; arestas de C (4) e a solta E somem, a de D fica por ser de face viva
        self.assertEqual((v["faces_ocultas"], v["arestas_ocultas"]), (2, 5))

    def test_total_remove_faces_e_arestas_ocultas(self):
        gerar(self.p("o.skp"))
        self.assertEqual(self.contar(self.p("o.skp")), {"faces": 4, "edges": 18, "instances": 0})
        rel = podar_skp(self.p("o.skp"), self.p("t.skp"), "total")
        self.assertEqual((rel["geometria_faces"], rel["geometria_arestas"], rel["geometria_vertices"]), (2, 5, 6))
        self.assertEqual(self.contar(self.p("t.skp")), {"faces": 2, "edges": 13, "instances": 0})
        v = verificar_skp(self.p("t.skp"))
        self.assertEqual((v["faces_ocultas"], v["arestas_ocultas"], v["refs_quebradas"]), (0, 0, 0))

    def test_completo_nao_mexe_na_geometria(self):
        gerar(self.p("o.skp"))
        podar_skp(self.p("o.skp"), self.p("c.skp"), "completo")
        self.assertEqual(self.contar(self.p("c.skp")), {"faces": 4, "edges": 18, "instances": 0})

    def test_idempotente(self):
        gerar(self.p("o.skp"))
        podar_skp(self.p("o.skp"), self.p("t.skp"), "total")
        rel = podar_skp(self.p("t.skp"), self.p("t2.skp"), "total")
        self.assertEqual((rel["geometria_faces"], rel["geometria_arestas"]), (0, 0))
        self.assertEqual(self.contar(self.p("t2.skp")), {"faces": 2, "edges": 13, "instances": 0})

    def test_curva_que_perde_aresta_vira_arestas_comuns(self):
        gerar_curva(self.p("c.skp"))
        self.assertEqual(self.contar(self.p("c.skp"))["edges"], 8)
        rel = podar_skp(self.p("c.skp"), self.p("t.skp"), "total")
        self.assertEqual((rel["geometria_arestas"], rel["geometria_curvas"]), (1, 1))
        self.assertEqual(self.contar(self.p("t.skp"))["edges"], 7)
        from tools.su_curvas import curvas
        self.assertEqual(curvas(self.p("t.skp")), [])  # a curva inteira foi desfeita


if __name__ == "__main__":
    unittest.main()
