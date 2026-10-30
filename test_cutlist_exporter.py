import os
import tempfile
import zipfile
import unittest

from core.cutlist_exporter import CutlistExporter


class TestCutlistExporter(unittest.TestCase):
    def test_cutlist_generation(self):
        tmp_dir = tempfile.gettempdir()
        out_xlsx = os.path.join(tmp_dir, "test_cutlist_parkelo.xlsx")
        if os.path.exists(out_xlsx):
            os.remove(out_xlsx)

        mock_bim_report = {
            "items": [
                {
                    "definition_name": "200416 - ESCORREGADOR TUBO H1200",
                    "instance_count": 2,
                    "unit_volume_m3": 0.45,
                    "unit_area_m2": 3.8,
                    "material": "Polietileno Rotomoldado",
                    "unit_price": 2500.0,
                },
                {
                    "definition_name": "Painel Assoalho Deck Madeira",
                    "instance_count": 6,
                    "unit_volume_m3": 0.08,
                    "unit_area_m2": 1.2,
                    "material": "Madeira Plastica",
                    "unit_price": 180.0,
                },
                {
                    "definition_name": "Coluna Estrutural 90x90",
                    "instance_count": 4,
                    "unit_volume_m3": 0.05,
                    "unit_area_m2": 0.9,
                    "material": "Aluminio",
                    "unit_price": 320.0,
                }
            ],
            "summary": {
                "total_items_count": 12,
                "total_volume_m3": 1.58,
                "total_area_m2": 18.4,
                "estimated_cost": 7360.0,
            }
        }

        res = CutlistExporter.export_xlsx(mock_bim_report, out_xlsx)
        self.assertTrue(os.path.exists(out_xlsx))
        self.assertGreater(res["file_size_bytes"], 1500)
        self.assertEqual(res["total_pecas"], 12)
        print("[OK] Arquivo XLSX gerado com sucesso:", res)

        # Valida estrutura interna OpenXML ZIP
        with zipfile.ZipFile(out_xlsx, "r") as z:
            names = z.namelist()
            self.assertIn("[Content_Types].xml", names)
            self.assertIn("xl/workbook.xml", names)
            self.assertIn("xl/worksheets/sheet1.xml", names)
            self.assertIn("xl/worksheets/sheet2.xml", names)
            self.assertIn("xl/worksheets/sheet3.xml", names)
            print("[OK] Validação de integridade OpenXML ECMA-376 aprovada!")


if __name__ == "__main__":
    unittest.main()
