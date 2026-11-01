"""
Suíte de Testes Automatizados - Frentes LayOut ABNT e Marcenaria Industrial Sob Medida
Cobre os 5 motores analíticos Zero DLL / Pure Python e seus endpoints FastAPI:
1. AbntDrawingSheetEngine (NBR 10068 / NBR 6492)
2. ArchitecturalHatchingEngine (Hachuras Normativas)
3. FurnitureEdgeBandingEngine (Fita de Borda e Desconto de Corte NBR 14810)
4. CabinetHardwareDrillingEngine (Sistema 32 DIN 68858, Dobradiça 35mm e Minifix)
5. SheetNesting2DEngine (Otimizador de Corte Guilhotinado para Chapas MDF 2750x1830)
"""

import asyncio
import unittest

from core.abnt_drawing_sheet_engine import AbntDrawingSheetEngine
from core.architectural_hatching_engine import ArchitecturalHatchingEngine
from core.furniture_edge_banding_engine import FurnitureEdgeBandingEngine
from core.cabinet_hardware_drilling_engine import CabinetHardwareDrillingEngine
from core.sheet_nesting_2d_engine import SheetNesting2DEngine

from app.controllers.scene_controller import SceneController
from app.services.scene_service import SceneService
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.schemas.scene import (
    AbntDrawingSheetRequest,
    ArchitecturalHatchingRequest,
    FurnitureEdgeBandingRequest,
    CabinetHardwareDrillingRequest,
    SheetNesting2DRequest,
)


class TestFrentesLayoutEMarcenariaAvancada(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = SkpEngineRepository()
        cls.service = SceneService(cls.repo)
        cls.controller = SceneController(cls.service)

    # --------------------------------------------------------------------------
    # 1. TESTES MOTOR ABNT DRAWING SHEET
    # --------------------------------------------------------------------------
    def test_abnt_drawing_sheet_formats_and_margins(self):
        sheet_a3 = AbntDrawingSheetEngine.create_drawing_sheet(
            sheet_format="A3",
            orientation="landscape",
            title_block={
                "title": "Casa de Campo",
                "author": "Arq. SketchBuild",
                "scale": "1:50",
            },
            viewports=[
                {
                    "name": "Planta Térreo",
                    "scale": "1:50",
                    "model_bounds": {"min_x": 0.0, "min_y": 0.0, "max_x": 10.0, "max_y": 5.0},
                    "x_mm": 50.0,
                    "y_mm": 50.0,
                }
            ],
        )
        self.assertEqual(sheet_a3["status"], "success")
        self.assertEqual(sheet_a3["format"], "A3")
        self.assertEqual(sheet_a3["dimensions_mm"]["width"], 420.0)
        self.assertEqual(sheet_a3["dimensions_mm"]["height"], 297.0)
        self.assertEqual(sheet_a3["margins_mm"]["left"], 25.0)  # Margem normativa de encadernação
        self.assertEqual(sheet_a3["margins_mm"]["right"], 7.0)
        self.assertIn("usable_area_mm", sheet_a3)
        self.assertEqual(len(sheet_a3["viewports"]), 1)
        vp = sheet_a3["viewports"][0]
        self.assertEqual(vp["scale"], "1:50")
        # 10 metros em escala 1:50 = 200 mm na prancha
        self.assertAlmostEqual(vp["paper_size_mm"]["width"], 200.0, places=1)
        # 5 metros em escala 1:50 = 100 mm na prancha
        self.assertAlmostEqual(vp["paper_size_mm"]["height"], 100.0, places=1)

    # --------------------------------------------------------------------------
    # 2. TESTES MOTOR ARCHITECTURAL HATCHING
    # --------------------------------------------------------------------------
    def test_architectural_hatching_patterns(self):
        polygon = [(0.0, 0.0), (2.0, 0.0), (2.0, 2.0), (0.0, 2.0)]
        # Alvenaria
        hatch_masonry = ArchitecturalHatchingEngine.generate_hatch_lines(
            polygon_points=polygon,
            pattern="MASONRY",
            spacing_m=0.2,
            angle_deg=45.0,
        )
        self.assertEqual(hatch_masonry["status"], "success")
        self.assertEqual(hatch_masonry["pattern"], "MASONRY")
        self.assertGreater(hatch_masonry["lines_count"], 0)
        for seg in hatch_masonry["segments"]:
            self.assertEqual(len(seg), 2)  # [start, end]

        # Concreto
        hatch_concrete = ArchitecturalHatchingEngine.generate_hatch_lines(
            polygon_points=polygon,
            pattern="CONCRETE",
            spacing_m=0.2,
        )
        self.assertEqual(hatch_concrete["status"], "success")
        self.assertIn("symbols", hatch_concrete)

        # Polígono degenerado
        hatch_invalid = ArchitecturalHatchingEngine.generate_hatch_lines(
            polygon_points=[(0.0, 0.0), (1.0, 1.0)],
        )
        self.assertEqual(hatch_invalid["status"], "warning")
        self.assertEqual(hatch_invalid["lines_count"], 0)

    # --------------------------------------------------------------------------
    # 3. TESTES MOTOR FURNITURE EDGE BANDING
    # --------------------------------------------------------------------------
    def test_furniture_edge_banding_and_cut_deduction(self):
        # Painel com fita de 1.0mm nas laterais (deve abater da chapa crua)
        panel = FurnitureEdgeBandingEngine.calculate_panel_edges(
            panel_id="P01",
            name="Porta Basculante",
            width_mm=600.0,
            height_mm=400.0,
            thickness_mm=18.0,
            edges={
                "top": {"enabled": True, "thickness_mm": 1.0, "material": "PVC Branco", "cost_per_meter": 2.0},
                "bottom": {"enabled": True, "thickness_mm": 1.0, "material": "PVC Branco", "cost_per_meter": 2.0},
                "left": {"enabled": False},
                "right": {"enabled": False},
            },
            overhead_ratio=0.10,
        )
        self.assertEqual(panel["finished_dimensions_mm"]["height"], 400.0)
        # 400mm - 2*1.0mm = 398.0mm de corte na chapa crua
        self.assertAlmostEqual(panel["raw_cut_dimensions_mm"]["height"], 398.0, places=2)
        self.assertAlmostEqual(panel["raw_cut_dimensions_mm"]["width"], 600.0, places=2)
        # Metragem líquida = 0.6m + 0.6m = 1.2m
        self.assertAlmostEqual(panel["summary"]["total_linear_meters"], 1.2, places=2)
        # Com 10% de refilo = 1.32m
        self.assertAlmostEqual(panel["summary"]["total_with_overhead_meters"], 1.32, places=2)
        # Custo = 1.32 * 2.0 = 2.64
        self.assertAlmostEqual(panel["summary"]["total_cost"], 2.64, places=2)

    def test_furniture_cabinet_processing(self):
        panels = [
            {
                "panel_id": "L1",
                "name": "Lateral",
                "width_mm": 550,
                "height_mm": 720,
                "thickness_mm": 18,
                "edges": {
                    "top": {"enabled": True, "thickness_mm": 0.45, "material": "PVC Carvalho"},
                    "bottom": {"enabled": True, "thickness_mm": 0.45, "material": "PVC Carvalho"},
                },
            }
        ]
        res = FurnitureEdgeBandingEngine.process_furniture_cabinet("Balcão 2 Portas", panels)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["panel_count"], 1)
        self.assertGreater(res["totals"]["net_linear_meters"], 0.0)

    # --------------------------------------------------------------------------
    # 4. TESTES MOTOR CABINET HARDWARE DRILLING
    # --------------------------------------------------------------------------
    def test_cabinet_hardware_drilling_system_32(self):
        s32 = CabinetHardwareDrillingEngine.calculate_system_32_shelf_holes(
            side_height_mm=720.0,
            side_depth_mm=550.0,
            front_setback_mm=37.0,
            rear_setback_mm=37.0,
        )
        self.assertEqual(s32["status"], "success")
        self.assertEqual(s32["step_mm"], 32.0)
        self.assertGreater(s32["hole_count"], 10)
        # Verifica se o primeiro furo frontal está a 37mm da borda
        self.assertEqual(s32["holes"][0]["x_mm"], 37.0)

    def test_cabinet_hardware_drilling_hinges_and_minifix(self):
        # Dobradiças para porta de 715mm (2 dobradiças)
        hinges = CabinetHardwareDrillingEngine.calculate_door_hinge_drillings(
            door_height_mm=715.0,
            door_width_mm=395.0,
        )
        self.assertEqual(hinges["status"], "success")
        self.assertEqual(hinges["recommended_hinge_count"], 2)
        self.assertGreater(len(hinges["door_cup_drillings"]), 0)
        self.assertGreater(len(hinges["cabinet_mounting_plates"]), 0)

        # Minifix
        minifix = CabinetHardwareDrillingEngine.calculate_minifix_joint(
            joint_width_mm=550.0,
            panel_thickness_mm=18.0,
        )
        self.assertEqual(minifix["status"], "success")
        self.assertEqual(minifix["joint_count"], 2)
        self.assertGreater(minifix["total_holes"], 0)

    # --------------------------------------------------------------------------
    # 5. TESTES MOTOR SHEET NESTING 2D
    # --------------------------------------------------------------------------
    def test_sheet_nesting_2d_optimizer(self):
        parts = [
            {"id": "LAT", "name": "Lateral", "width_mm": 550, "height_mm": 720, "quantity": 2, "can_rotate": False},
            {"id": "BASE", "name": "Base", "width_mm": 550, "height_mm": 764, "quantity": 2, "can_rotate": False},
            {"id": "PORTA", "name": "Porta", "width_mm": 395, "height_mm": 715, "quantity": 2, "can_rotate": False},
        ]
        nesting = SheetNesting2DEngine.optimize_cut_list(
            parts=parts,
            sheet_width_mm=2750.0,
            sheet_height_mm=1830.0,
            trim_margin_mm=10.0,
            saw_kerf_mm=3.2,
        )
        self.assertEqual(nesting["status"], "success")
        self.assertEqual(nesting["parts_requested"], 6)
        self.assertEqual(nesting["parts_placed"], 6)
        self.assertEqual(nesting["unplaced_count"], 0)
        self.assertEqual(nesting["sheet_count"], 1)  # 6 peças cabem tranquilamente em 1 chapa
        self.assertGreater(nesting["global_yield_percent"], 0.0)
        self.assertLessEqual(nesting["global_yield_percent"], 100.0)
        first_sheet = nesting["sheets"][0]
        self.assertEqual(len(first_sheet["placed_parts"]), 6)

    # --------------------------------------------------------------------------
    # 6. TESTES INTEGRAÇÃO COM SCENE CONTROLLER
    # --------------------------------------------------------------------------
    def test_controller_integration(self):
        # 1. Prancha ABNT
        req_sheet = AbntDrawingSheetRequest(sheet_format="A4", orientation="portrait")
        res_sheet = asyncio.run(self.controller.abnt_drawing_sheet_create(req_sheet))
        self.assertEqual(res_sheet.sheet["format"], "A4")

        # 2. Hachura NBR 6492
        req_hatch = ArchitecturalHatchingRequest(
            polygon_points=[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]],
            pattern="MASONRY",
            spacing_m=0.1,
        )
        res_hatch = asyncio.run(self.controller.architectural_hatching_generate(req_hatch))
        self.assertGreater(res_hatch.hatching["lines_count"], 0)

        # 3. Fita de Borda
        req_band = FurnitureEdgeBandingRequest(
            cabinet_name="Criado Mudo",
            panels=[
                {
                    "panel_id": "TAMPO",
                    "name": "Tampo",
                    "width_mm": 500,
                    "height_mm": 400,
                    "thickness_mm": 18,
                    "edges": {"top": {"enabled": True, "thickness_mm": 0.45}},
                }
            ],
        )
        res_band = asyncio.run(self.controller.furniture_edge_banding_process(req_band))
        self.assertEqual(res_band.banding_plan["panel_count"], 1)

        # 4. Furação
        req_drill = CabinetHardwareDrillingRequest(
            operation="system_32",
            params={"side_height_mm": 720, "side_depth_mm": 550},
        )
        res_drill = asyncio.run(self.controller.cabinet_hardware_drilling_calculate(req_drill))
        self.assertGreater(res_drill.drilling_plan["hole_count"], 0)

        # 5. Nesting 2D
        req_nest = SheetNesting2DRequest(
            parts=[{"id": "P1", "width_mm": 400, "height_mm": 300, "quantity": 2, "can_rotate": True}],
            sheet_width_mm=2750,
            sheet_height_mm=1830,
        )
        res_nest = asyncio.run(self.controller.sheet_nesting_2d_optimize(req_nest))
        self.assertEqual(res_nest.nesting_plan["parts_placed"], 2)


if __name__ == "__main__":
    unittest.main()
