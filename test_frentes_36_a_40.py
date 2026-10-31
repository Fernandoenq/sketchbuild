"""
Testes de Integração e Regressão para as Frentes 36 a 40 (Zero DLL).

- Frente 36: Otimizador de Plano de Corte de Estoque (Nesting 1D e 2D)
- Frente 37: Gerador de Terrenos Paramétricos e Malha Topográfica Sandbox
- Frente 38: Analisador Estrutural de Vigas e Tensões (NBR 7190)
- Frente 39: Ferramenta de Escala Paramétrica (Scale Tool)
- Frente 40: Exportador de Arquivos para CNC / Corte a Laser em DXF
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
    NestingRequest,
    TerrainRequest,
    StructuralAnalysisRequest,
    ScaleRequest,
    ExportCamDxfRequest,
)
from core.nesting_optimizer import NestingOptimizer
from core.terrain_generator import TerrainGenerator
from core.structural_analyzer import StructuralAnalyzer
from core.scale_tool import ScaleTool
from core.cam_dxf_exporter import CamDxfExporter
from core.skp_binary_writer import SkpBinaryWriter


class TestFrentes36a40(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_frente_36_nesting_optimizer(self):
        """Valida otimização de plano de corte de barras de madeira (Frente 36)."""
        await self.controller.open_binary_scene(self.template_path)

        demanded = [
            {"name": "Pilar Principal", "length_m": 1.40, "quantity": 4},
            {"name": "Travessa Inferior", "length_m": 0.90, "quantity": 4},
            {"name": "Montante Guarda-corpo", "length_m": 0.70, "quantity": 6},
        ]
        req = NestingRequest(demanded_pieces=demanded, stock_bar_length_m=3.00)
        res = await self.controller.calculate_nesting_optimizer(req)

        self.assertEqual(res.stock_bar_length_m, 3.00)
        self.assertGreater(res.total_bars_required, 0)
        self.assertEqual(res.total_pieces_cut, 14)
        self.assertGreaterEqual(res.efficiency_percent, 70.0)
        print(f"\n[Frente 36] Nesting 1D Otimizado: {res.total_pieces_cut} peças alocadas em {res.total_bars_required} barras brutas (Aproveitamento: {res.efficiency_percent}%, Perda: {res.scrap_percent}%)")

    async def test_02_frente_37_terrain_generator(self):
        """Valida geração paramétrica de terreno topográfico Sandbox (Frente 37)."""
        await self.controller.open_binary_scene(self.template_path)

        req = TerrainRequest(
            width_m=8.0,
            length_m=8.0,
            grid_resolution_m=1.0,
            slope_x_pct=2.0,
            slope_y_pct=5.0
        )
        res = await self.controller.create_terrain_geometry(req)
        self.assertEqual(res.entity_type, "TerrainMesh")
        self.assertEqual(res.vertex_count, 81)  # 9 x 9 pontos
        self.assertEqual(res.triangle_count, 128)  # 8 x 8 * 2 triângulos
        self.assertGreater(res.earthwork_cut_m3, 0.0)
        print(f"[Frente 37] Terreno Sandbox 3D: Malha TIN com {res.vertex_count} vértices e {res.triangle_count} triângulos (Corte: {res.earthwork_cut_m3}m³, Aterro: {res.earthwork_fill_m3}m³)")

    async def test_03_frente_38_structural_analysis(self):
        """Valida cálculo de tensões e flechas em vigas de eucalipto NBR 7190 (Frente 38)."""
        await self.controller.open_binary_scene(self.template_path)

        req = StructuralAnalysisRequest(
            span_length_m=2.20,
            load_kn_per_m=3.00,
            section_type="circular",
            diameter_m=0.16
        )
        res = await self.controller.calculate_structural_analysis(req)
        self.assertEqual(res.section_type, "circular")
        self.assertEqual(res.span_length_m, 2.20)
        self.assertGreater(res.max_bending_moment_kn_m, 0.0)
        self.assertTrue(res.deflection_compliant)
        self.assertTrue(res.stress_compliant)
        self.assertGreaterEqual(res.safety_factor, 1.5)
        print(f"[Frente 38] Análise Estrutural NBR 7190: {res.structural_status} (Tensão: {res.bending_stress_mpa} MPa, Flecha: {res.max_deflection_mm}mm / Limite: {res.deflection_limit_mm}mm, FS={res.safety_factor})")

    async def test_04_frente_39_scale_transform(self):
        """Valida ferramenta de escala analítica e redimensionamento (Frente 39)."""
        await self.controller.open_binary_scene(self.template_path)

        session = SkpBinaryWriter.get_session()
        inst_keys = list(session.instances_offsets.keys()) if session else []
        target_inst_id = inst_keys[0] if inst_keys else "inst_0_Model Root"

        req = ScaleRequest(
            instance_id=target_inst_id,
            scale_factors=[1.5, 1.5, 2.0],
            pivot=[0.0, 0.0, 0.0]
        )
        res = await self.controller.apply_scale_transform(req)
        self.assertEqual(res.instance_id, target_inst_id)
        self.assertEqual(res.scale_factors, [1.5, 1.5, 2.0])
        self.assertEqual(len(res.transform_matrix_16), 16)
        print(f"[Frente 39] Scale Tool: Escala não-uniforme [1.5, 1.5, 2.0] aplicada com sucesso")

    async def test_05_frente_40_cam_dxf_exporter(self):
        """Valida exportador DXF para fabricação digital CNC e Corte a Laser (Frente 40)."""
        await self.controller.open_binary_scene(self.template_path)

        parts = [
            {
                "name": "Lateral Escorregador PEAD 15mm",
                "outer_loop": [(0, 0), (2000, 0), (2000, 500), (0, 500)],  # em mm
                "holes": [
                    [(100, 100), (120, 100), (120, 120), (100, 120)],
                    [(1900, 100), (1920, 100), (1920, 120), (1900, 120)],
                ]
            }
        ]
        req = ExportCamDxfRequest(
            parts=parts,
            output_filename="test_usinagem_cnc.dxf"
        )
        res = await self.controller.export_cam_dxf(req)
        self.assertTrue(os.path.exists(res.file_path))
        self.assertGreater(res.size_bytes, 200)
        self.assertEqual(res.parts_count, 1)

        # Checa conteúdo DXF
        with open(res.file_path, "r", encoding="utf-8") as f:
            dxf_text = f.read()
        self.assertTrue("CAM_CORTE_EXTERNO" in dxf_text)
        self.assertTrue("CAM_FUROS_INTERNOS" in dxf_text)
        self.assertTrue("$INSUNITS" in dxf_text)
        print(f"[Frente 40] Exportador CAM DXF: Arquivo CNC gerado em {res.file_path} ({res.size_bytes} bytes com camadas CAM)")


if __name__ == "__main__":
    unittest.main()
