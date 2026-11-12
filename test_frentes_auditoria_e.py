"""Auditoria (A5), parte E: reexibir entidades e esboço técnico, com valores calculados à mão."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.art_report_generator import ArtReportGenerator  # noqa: E402
from core.field_inspection_exporter import FieldInspectionExporter  # noqa: E402
from core.technical_drawing_exporter import TechnicalDrawingExporter  # noqa: E402
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


def _cena_quadrado(lado_pol=100.0, dx_pol=0.0):
    """Um quadrado de `lado_pol` polegadas (2 triângulos) deslocado `dx_pol` em x."""
    v = [0, 0, 0, lado_pol, 0, 0, lado_pol, lado_pol, 0, 0, lado_pol, 0]
    t = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, dx_pol, 0, 0, 1]
    return {"definitions": [{"definition_id": 1, "vertices": v, "indices": [0, 1, 2, 0, 2, 3]}],
            "instances": [{"definition_id": 1, "transform": t}]}


class TestDesenhoTecnico(unittest.TestCase):
    def test_cota_total_vem_da_geometria_em_metros(self):
        # 100 pol = 2,54 m; instância deslocada não muda a largura
        svg = TechnicalDrawingExporter.generate_svg(_cena_quadrado(100, 500), "top")
        self.assertIn("2.54 m</text>", svg)
        # 5 arestas distintas (4 do contorno + diagonal) no grupo de arestas
        grupo = svg.split('<!-- Arestas do Modelo 2D -->')[1].split('</g>')[0]
        self.assertEqual(grupo.count("<line"), 5)

    def test_vista_invalida_vira_planta_e_titulo_e_escapado(self):
        svg = TechnicalDrawingExporter.generate_svg(_cena_quadrado(), "xyz", title="A<b>&c")
        self.assertIn("PLANTA BAIXA", svg)
        self.assertIn("A&lt;b&gt;&amp;c", svg)
        self.assertNotIn("A<b>", svg)

    def test_elevacao_frontal_de_quadrado_no_plano_xy_nao_tem_arestas_verticais(self):
        svg = TechnicalDrawingExporter.generate_svg(_cena_quadrado(), "front")
        grupo = svg.split('<!-- Arestas do Modelo 2D -->')[1].split('</g>')[0]
        self.assertEqual(grupo.count("<line"), 1)  # vira um segmento só (z constante)

    def test_sem_geometria_usa_limites_padrao_e_exporta_arquivo(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "sub", "t.svg")
            r = TechnicalDrawingExporter.export_svg({}, p, scale="1:100")
            self.assertTrue(os.path.isfile(p))
            self.assertEqual((r["scale"], r["file_size_bytes"] == os.path.getsize(p)), ("1:100", True))
            with open(p, encoding="utf-8") as fh:
                self.assertIn("4.00 m</text>", fh.read())  # sem geometria: limites padrão de -2 a 2 m


class TestMinutaArt(unittest.TestCase):
    def _gerar(self, prof, proj):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "art.pdf")
            r = ArtReportGenerator.generate_art_pdf(prof, proj, p)
            with open(p, "rb") as fh:
                return r, fh.read()

    def test_pdf_tem_estrutura_e_xref_aponta_para_os_objetos(self):
        r, b = self._gerar({"name": "Ana"}, {})
        self.assertTrue(b.startswith(b"%PDF-1.4") and b.rstrip().endswith(b"%%EOF"))
        self.assertEqual(r["size_bytes"], len(b))
        xref = int(b.split(b"startxref\n")[1].split(b"\n")[0])
        self.assertEqual(b[xref:xref + 4], b"xref")
        linhas = b[xref:].split(b"\n")
        for n in range(1, 7):
            off = int(linhas[2 + n].split()[0])
            self.assertEqual(b[off:off + len(f"{n} 0 obj")], f"{n} 0 obj".encode())

    def test_nome_com_parenteses_e_barra_nao_quebra_a_string_do_pdf(self):
        bs = chr(92)
        _, b = self._gerar({"name": "Ana (Eng) " + bs + " Filho"}, {"project_name": "Gira)Gira"})
        self.assertIn(("Ana " + bs + "(Eng" + bs + ") " + bs * 2 + " Filho").encode(), b)
        self.assertIn(("Gira" + bs + ")Gira").encode(), b)

    def test_caractere_fora_do_latin1_vira_interrogacao_e_o_length_bate(self):
        _, b = self._gerar({"name": "Ana " + chr(0x2603)}, {})
        corpo = b.split(b"\nendstream")[0].split(b">>\nstream\n")[1]
        declarado = int(b.split(b"/Length ")[1].split(b" ")[0])
        self.assertEqual(declarado, len(corpo))
        self.assertIn(b"Ana ?", corpo)


class TestFichaDeCampo(unittest.TestCase):
    def test_campos_do_usuario_sao_escapados_no_html(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "f.html")
            r = FieldInspectionExporter.generate_inspection_html("Parque <script>x</script> & Cia", "Ana", "2026-11-12", output_path=p)
            with open(p, "rb") as fh:
                b = fh.read()
            html = b.decode("utf-8")
        self.assertNotIn("<script>x", html)
        self.assertIn("Parque &lt;script&gt;x&lt;/script&gt; &amp; Cia", html)
        self.assertEqual(r["size_bytes"], len(b))  # sem troca de fim de linha ao gravar
        self.assertEqual(r["items_count"], html.count("<tr>") - 3)  # 3 linhas de cabeçalho de tabela

    def test_lista_de_equipamentos_padrao_e_informada(self):
        padrao = FieldInspectionExporter.generate_inspection_html("P", "I", "D")
        self.assertEqual(padrao["file_path"], "")
        from core import field_inspection_exporter as m  # noqa: F401
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "g.html")
            FieldInspectionExporter.generate_inspection_html("P", "I", "D", ["A", "B"], p)
            with open(p, encoding="utf-8") as fh:
                self.assertIn("2 unidades", fh.read())


if __name__ == "__main__":
    unittest.main()
