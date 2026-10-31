"""
Testes de Integracao e Regressao para as Frentes 56 a 60 (Zero DLL).

- Frente 56: Gerador de Telhados de Quatro Águas / Piramidais (Hip Roof)
- Frente 57: Simulador de Impacto e Altura Crítica de Queda HIC (NBR 16071-3)
- Frente 58: Exportador de Ficha de Produção e Etiqueta Térmica Zebra (ZPL II / EPL)
- Frente 59: Ferramenta de Vistas Explodidas com Linhas de Trajetória (Exploded Trails)
- Frente 60: Calculador de Pegada de Carbono e Créditos de Carbono de Madeira
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    HipRoofRequest,
    HicRequest,
    ZebraLabelRequest,
    ExplodedTrailsRequest,
    CarbonFootprintRequest,
)


class TestFrentes56a60(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_frente_56_hip_roof(self):
        """Valida gerador paramétrico de telhados de 4 águas para quiosques (Frente 56)."""
        req = HipRoofRequest(
            base_width_m=2.40,
            base_length_m=3.20,
            base_height_m=2.80,
            pitch_deg=30.0,
            overhang_m=0.35
        )
        res = await self.controller.generate_hip_roof(req)
        self.assertEqual(res.entity_type, "HipRoofGeometry")
        self.assertEqual(res.base_width_m, 2.40)
        self.assertGreater(res.apex_height_m, 2.80)
        self.assertGreater(res.ridge_length_m, 0.5)
        self.assertGreater(res.sloped_roof_area_m2, 10.0)
        self.assertEqual(len(res.vertices), 6)  # 4 beirais + 2 cumeeira
        self.assertEqual(len(res.faces), 5)  # 4 aguas + 1 forro
        self.assertIn("Quatro Águas", res.roof_type)
        print(f"[Frente 56] Telhado 4 Aguas: {res.roof_type} (Area: {res.sloped_roof_area_m2}m2, Cumeeira: {res.ridge_length_m}m, Altura Apice: {res.apex_height_m}m)")

    async def test_02_frente_57_hic_impact(self):
        """Valida simulador de impacto HIC e piso amortecedor NBR 16071-3 (Frente 57)."""
        req = HicRequest(
            fall_height_m=1.80,
            surface_type="areia_lavada",
            installed_thickness_mm=300.0
        )
        res = await self.controller.simulate_hic_impact(req)
        self.assertEqual(res.entity_type, "HicImpactAnalysis")
        self.assertEqual(res.surface_type, "areia_lavada")
        self.assertGreater(res.impact_velocity_m_s, 5.0)
        self.assertLess(res.hic_score, 1000.0)
        self.assertLess(res.peak_deceleration_g, 200.0)
        self.assertTrue(res.is_compliant)
        self.assertEqual(len(res.curve_points), 21)
        self.assertIn("CONFORMIDADE", res.safety_verdict)
        print(f"[Frente 57] Simulacao HIC NBR 16071-3: {res.safety_verdict} (HIC={res.hic_score}, Pico={res.peak_deceleration_g}g, V={res.impact_velocity_m_s}m/s)")

    async def test_03_frente_58_zebra_label(self):
        """Valida emissor de etiquetas térmicas industriais Zebra ZPL II (Frente 58)."""
        zpl_file = os.path.join(self.tmp_dir, "test_etiqueta.zpl")
        svg_file = os.path.join(self.tmp_dir, "test_etiqueta.svg")
        if os.path.exists(zpl_file):
            os.remove(zpl_file)
        if os.path.exists(svg_file):
            os.remove(svg_file)

        req = ZebraLabelRequest(
            part_name="Pilar Eucalipto Citriodora",
            part_sku="PKL-EUC-16-220",
            dimensions_mm="D160 x L2200 mm",
            lot_batch="LOTE-2026-X84",
            output_zpl_filename=zpl_file,
            output_svg_filename=svg_file
        )
        res = await self.controller.export_zebra_label(req)
        self.assertTrue(os.path.exists(res.zpl_file_path))
        self.assertTrue(os.path.exists(res.svg_file_path))
        self.assertGreater(res.zpl_size_bytes, 100)
        self.assertEqual(res.part_sku, "PKL-EUC-16-220")

        # Verifica código ZPL nativo
        with open(res.zpl_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("^XA", content)
            self.assertIn("^XZ", content)
            self.assertIn("^BC", content)  # Code 128
            self.assertIn("PKL-EUC-16-220", content)

        print(f"[Frente 58] Etiqueta Zebra ZPL exportada: {res.zpl_size_bytes} bytes ({res.zpl_file_path})")
        if os.path.exists(zpl_file):
            os.remove(zpl_file)
        if os.path.exists(svg_file):
            os.remove(svg_file)

    async def test_04_frente_59_exploded_trails(self):
        """Valida gerador analítico de trilhas e linhas de vista explodida (Frente 59)."""
        parts = [
            {
                "id": "pilar_01",
                "name": "Pilar Mestre",
                "original_pos": [0.0, 0.0, 0.0],
                "exploded_pos": [0.0, 0.0, 0.0],  # Raiz / fixa
            },
            {
                "id": "deck_01",
                "name": "Deck Superior",
                "original_pos": [0.0, 0.0, 1.40],
                "exploded_pos": [0.0, 0.0, 2.60],  # Explodida em Z
            },
            {
                "id": "escorregador_01",
                "name": "Prancha Escorregador",
                "original_pos": [1.50, 0.0, 1.40],
                "exploded_pos": [3.00, 0.0, 1.40],  # Explodida em X
            }
        ]
        req = ExplodedTrailsRequest(parts=parts, dash_size_m=0.05, gap_size_m=0.03)
        res = await self.controller.calculate_exploded_trails(req)
        self.assertEqual(res.entity_type, "ExplodedViewTrails")
        self.assertEqual(res.parts_with_trails_count, 2)  # Apenas as que se moveram
        self.assertGreater(res.total_trail_length_m, 2.0)
        self.assertEqual(len(res.trails), 2)
        print(f"[Frente 59] Linhas de Vista Explodida: {res.parts_with_trails_count} trilhas geradas (Extensao Total: {res.total_trail_length_m}m)")

    async def test_05_frente_60_carbon_footprint(self):
        """Valida calculador de pegada de carbono e créditos sustentáveis (Frente 60)."""
        req = CarbonFootprintRequest(
            timber_volume_m3=2.80,
            steel_weight_kg=95.0,
            plastic_weight_kg=45.0,
            transport_distance_km=350.0
        )
        res = await self.controller.calculate_carbon_footprint(req)
        self.assertEqual(res.entity_type, "CarbonFootprintAnalysis")
        self.assertGreater(res.co2_sequestered_kg, 2000.0)
        self.assertGreater(res.net_carbon_balance_kg, 1000.0)
        self.assertTrue(res.is_carbon_negative)
        self.assertGreater(res.equivalent_trees_planted_years, 50.0)
        self.assertIn("CLIMA-POSITIVO", res.sustainability_badge)
        print(f"[Frente 60] Pegada de Carbono: {res.sustainability_badge} (Retencao Liquida: {res.net_carbon_balance_kg}kg CO2e, Equivalente a {res.equivalent_trees_planted_years} arvores/ano)")


if __name__ == "__main__":
    unittest.main()
