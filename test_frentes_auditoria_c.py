"""Auditoria (A5), parte C: espessura de parede, etiqueta Zebra e exportador OBJ, com valores calculados à mão."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.obj_exporter import write_obj  # noqa: E402
from core.wall_thickness_inspector import WallThicknessInspector  # noqa: E402
from core.zebra_label_exporter import ZebraLabelExporter  # noqa: E402


def _par(espessura_m):
    """Duas faces opostas (normais contrárias) separadas por `espessura_m` em z."""
    quad = lambda z: [[0, 0, z], [1, 0, z], [1, 1, z], [0, 1, z]]  # noqa: E731
    return [
        {"vertices": quad(0.0), "normal": [0.0, 0.0, 1.0]},
        {"vertices": quad(espessura_m), "normal": [0.0, 0.0, -1.0]},
    ]


class TestEspessuraDeParede(unittest.TestCase):
    def test_parede_de_8_mm_aprovada(self):
        r = WallThicknessInspector.inspect_thickness(_par(0.008))
        self.assertEqual(r["samples_count"], 2)
        self.assertEqual((r["min_thickness_mm"], r["max_thickness_mm"], r["avg_thickness_mm"]), (8.0, 8.0, 8.0))
        self.assertTrue(r["is_compliant"])
        self.assertFalse(r["amostra_demonstrativa"])
        self.assertEqual(r["status"], "APROVADO PARA PRODUÇÃO")

    def test_parede_de_4_mm_reprovada_por_subespessura(self):
        r = WallThicknessInspector.inspect_thickness(_par(0.004))
        self.assertFalse(r["is_compliant"])
        self.assertEqual(r["thin_wall_defects_count"], 2)
        self.assertEqual(r["min_thickness_mm"], 4.0)
        self.assertIn("REPROVADO", r["status"])

    def test_parede_de_20_mm_e_sobre_espessura_mas_nao_reprova(self):
        r = WallThicknessInspector.inspect_thickness(_par(0.020))
        self.assertEqual((r["thick_wall_defects_count"], r["thin_wall_defects_count"]), (2, 0))
        self.assertTrue(r["is_compliant"])

    def test_sem_faces_nao_aprova(self):
        with self.assertRaises(ValueError):
            WallThicknessInspector.inspect_thickness([])

    def test_exemplo_pedido_e_marcado_como_demonstracao(self):
        r = WallThicknessInspector.inspect_thickness([], usar_exemplo=True)
        self.assertTrue(r["amostra_demonstrativa"])
        self.assertIn("DEMONSTRATIVA", r["status"])


class TestEtiquetaZebra(unittest.TestCase):
    def test_zpl_tem_um_unico_formato_e_campos_fechados(self):
        z = ZebraLabelExporter.generate_zpl(part_name="Viga ^FS^XZ~DG", serial_number="SN-1")
        self.assertEqual((z.count("^XA"), z.count("^XZ")), (1, 1))
        self.assertTrue(z.startswith("^XA") and z.endswith("^XZ"))
        self.assertIn("^FDPECA: VIGA  FS XZ DG^FS", z)  # '^' e '~' viram espaço
        self.assertIn("SERIAL: SN-1", z)
        self.assertEqual(z.count("^FD"), z.count("^FS") - 2)  # 2 caixas (^GB) fecham com ^FS sem ^FD

    def test_svg_escapa_xml(self):
        s = ZebraLabelExporter.generate_preview_svg("A<b>&\"c\"", "SKU", "1x1", "L", "S")
        self.assertIn("A&lt;b&gt;&amp;", s)
        self.assertNotIn("<b>", s)

    def test_export_grava_arquivos_e_repassa_serial(self):
        with tempfile.TemporaryDirectory() as d:
            zpl, svg = os.path.join(d, "e.zpl"), os.path.join(d, "e.svg")
            r = ZebraLabelExporter.export_label("Peça", "SKU-1", "10x10", "L1", zpl, svg, serial_number="SN-777")
            with open(zpl, encoding="utf-8") as fh:
                self.assertIn("SERIAL: SN-777", fh.read())
            with open(svg, encoding="utf-8") as fh:
                self.assertIn("SERIAL: SN-777", fh.read())
            self.assertEqual((r["part_sku"], r["zpl_size_bytes"] > 0), ("SKU-1", True))


class TestExportadorObj(unittest.TestCase):
    def test_polegadas_viram_metros_e_matriz_translada(self):
        dto = {
            "definitions": [{
                "definition_id": 1, "name": "Tri angulo",
                "vertices": [0, 0, 0, 100, 0, 0, 0, 100, 0],
                "normals": [0, 0, 1, 0, 0, 1, 0, 0, 1],
                "indices": [0, 1, 2],
            }],
            "instances": [
                {"instance_id": 7, "definition_id": 1,
                 "transform": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 10, 0, 0, 1]},
                {"instance_id": 8, "definition_id": 99, "transform": [1] * 16},  # sem definição: pulada
            ],
        }
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "o.obj")
            write_obj(dto, p)
            with open(p, encoding="utf-8") as fh:
                linhas = fh.read().splitlines()
        self.assertIn("o Tri_angulo_7", linhas)
        self.assertEqual([l for l in linhas if l.startswith("v ")],
                         ["v 0.254000 0.000000 0.000000", "v 2.794000 0.000000 0.000000", "v 0.254000 2.540000 0.000000"])  # 10 pol = 0,254 m; 100 pol = 2,54 m
        self.assertEqual(linhas.count("vn 0.000000 0.000000 1.000000"), 3)
        self.assertIn("f 1//1 2//2 3//3", linhas)
        self.assertEqual(len([l for l in linhas if l.startswith("o ")]), 1)


if __name__ == "__main__":
    unittest.main()
