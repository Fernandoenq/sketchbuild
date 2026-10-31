"""
Testes Unitários Automatizados - Frentes 81 a 85
SketchBuild - Engenharia Reversa do SketchUp (Zero DLL)
Frente 81: PolyMeshLoopEngine (SULoopRef & SUPolyMeshRef - Face com Furos)
Frente 82: AlignViewEngine (Align Camera to Face - Normal Viewport)
Frente 83: BackgroundSkyStyleEngine (SUStyleRef - Céu, Solo e Horizonte)
Frente 84: DimensionToleranceEngine (Dimension Tolerances - ISO 2768)
Frente 85: UndoRedoCommandEngine (SUModelStartOperation & Undo/Redo Stack)
"""

import math
import unittest

from core.polymesh_loop_engine import PolyMeshLoopEngine
from core.align_view_engine import AlignViewEngine
from core.background_sky_style_engine import BackgroundSkyStyleEngine
from core.dimension_tolerance_engine import DimensionToleranceEngine
from core.undo_redo_engine import UndoRedoCommandEngine


class TestFrentes81A85(unittest.IsolatedAsyncioTestCase):

    def test_frente_81_polymesh_loop_engine(self):
        # 1. Face retangular simples (sem furo)
        outer = [(0.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 4.0, 0.0), (0.0, 4.0, 0.0)]
        res_simple = PolyMeshLoopEngine.triangulate_face_with_holes(outer)
        self.assertEqual(res_simple["face_count"], 2)

        # 2. Face retangular com 1 furo quadrado no centro (1.0 a 3.0)
        hole = [(1.0, 1.0, 0.0), (3.0, 1.0, 0.0), (3.0, 3.0, 0.0), (1.0, 3.0, 0.0)]
        res_hole = PolyMeshLoopEngine.triangulate_face_with_holes(outer, [hole])
        self.assertEqual(res_hole["entity_type"], "SUPolyMeshRef")
        self.assertEqual(res_hole["holes_count"], 1)
        self.assertGreater(res_hole["face_count"], 4)

    def test_frente_82_align_view_engine(self):
        # Face vertical em X = 2.0 (plano YZ) com normal apontando para -X (-1, 0, 0)
        face_pts = [(2.0, 0.0, 0.0), (2.0, 2.0, 0.0), (2.0, 2.0, 2.0), (2.0, 0.0, 2.0)]
        cam = AlignViewEngine.calculate_align_view(face_pts, fov_deg=35.0)

        self.assertEqual(cam["entity_type"], "AlignViewCamera")
        self.assertEqual(cam["target"][0], 2.0)
        self.assertEqual(cam["target"][1], 1.0)
        self.assertEqual(cam["target"][2], 1.0)
        # Eye deve estar afastado ao longo da normal da face
        self.assertNotEqual(cam["eye"][0], 2.0)
        self.assertEqual(cam["up"][2], 1.0)  # Z aponta para cima na tela

    def test_frente_83_background_sky_style_engine(self):
        # Estilo de céu e solo padrão
        style = BackgroundSkyStyleEngine.configure_background_sky(
            sky_enabled=True,
            ground_enabled=True,
            sky_color="#b4d5fe",
            ground_color="#c2b8a3",
            ground_transparency_percent=40,
        )
        self.assertEqual(style["entity_type"], "SUStyleBackgroundSky")
        self.assertTrue(style["sky_enabled"])
        self.assertTrue(style["ground_enabled"])
        self.assertEqual(style["ground_opacity"], 0.4)
        self.assertIn("linear-gradient", style["three_config"]["css_background"])

    def test_frente_84_dimension_tolerance_engine(self):
        # 1. Tolerância bilateral
        tol_bi = DimensionToleranceEngine.calculate_tolerance(50.0, unit="mm", tolerance_type="BILATERAL", upper_tol=0.05)
        self.assertEqual(tol_bi["max_limit"], 50.05)
        self.assertEqual(tol_bi["min_limit"], 49.95)
        self.assertIn("±", tol_bi["formatted_text"])

        # 2. Tolerância pela norma ISO 2768 classe m (média para 50mm -> ±0.3mm)
        tol_iso = DimensionToleranceEngine.calculate_tolerance(50.0, unit="mm", tolerance_type="ISO_CLASS", iso_class="m")
        self.assertEqual(tol_iso["upper_tolerance"], 0.3)
        self.assertIn("ISO 2768-m", tol_iso["formatted_text"])

    def test_frente_85_undo_redo_engine(self):
        engine = UndoRedoCommandEngine(max_history=10)
        # Registrar movimento de peça
        res_rec = engine.record_operation(
            name="Mover Viga 01",
            action_type="TRANSFORM_INSTANCE",
            target_id="inst_viga_1",
            before_state={"x": 0.0, "y": 0.0, "z": 0.0},
            after_state={"x": 5.0, "y": 0.0, "z": 0.0},
        )
        self.assertTrue(res_rec["can_undo"])
        self.assertFalse(res_rec["can_redo"])

        # Desfazer (Undo)
        res_undo = engine.undo()
        self.assertIsNotNone(res_undo)
        self.assertEqual(res_undo["action"], "UNDO")
        self.assertEqual(res_undo["restore_state"]["x"], 0.0)
        self.assertTrue(res_undo["can_redo"])

        # Refazer (Redo)
        res_redo = engine.redo()
        self.assertIsNotNone(res_redo)
        self.assertEqual(res_redo["action"], "REDO")
        self.assertEqual(res_redo["restore_state"]["x"], 5.0)

    async def test_controller_layers_frentes_81_a_85(self):
        from app.repositories.skp_engine_repository import SkpEngineRepository
        from app.services.scene_service import SceneService
        from app.controllers.scene_controller import SceneController
        from app.schemas.scene import (
            PolyMeshHolesRequest,
            AlignViewRequest,
            BackgroundSkyStyleRequest,
            DimensionToleranceRequest,
            UndoRedoRecordRequest,
        )

        repo = SkpEngineRepository()
        service = SceneService(repository=repo)
        controller = SceneController(service=service)

        # 81. Controller Triangulate
        req_81 = PolyMeshHolesRequest(
            outer_loop_3d=[[0.0, 0.0, 0.0], [5.0, 0.0, 0.0], [5.0, 5.0, 0.0], [0.0, 5.0, 0.0]],
            inner_loops_3d=[[[1.0, 1.0, 0.0], [3.0, 1.0, 0.0], [3.0, 3.0, 0.0], [1.0, 3.0, 0.0]]]
        )
        res_81 = await controller.triangulate_face_with_holes(req_81)
        self.assertEqual(res_81.entity_type, "SUPolyMeshRef")
        self.assertEqual(res_81.mesh_data["holes_count"], 1)

        # 82. Controller Align View
        req_82 = AlignViewRequest(
            face_vertices=[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [2.0, 2.0, 0.0], [0.0, 2.0, 0.0]]
        )
        res_82 = await controller.calculate_align_view(req_82)
        self.assertEqual(res_82.entity_type, "AlignViewCamera")

        # 83. Controller Background Sky
        req_83 = BackgroundSkyStyleRequest(
            sky_enabled=True,
            ground_enabled=True
        )
        res_83 = await controller.configure_background_sky(req_83)
        self.assertEqual(res_83.entity_type, "SUStyleBackgroundSky")

        # 84. Controller Dimension Tolerance
        req_84 = DimensionToleranceRequest(
            nominal_val=100.0,
            tolerance_type="BILATERAL",
            upper_tol=0.2
        )
        res_84 = await controller.calculate_dimension_tolerance(req_84)
        self.assertEqual(res_84.entity_type, "DimensionTolerance")

        # 85. Controller Undo/Redo
        req_85 = UndoRedoRecordRequest(
            name="Add Box",
            action_type="CREATE_GEOMETRY",
            target_id="box_1",
            before_state={},
            after_state={"created": True}
        )
        res_rec = await controller.record_undo_operation(req_85)
        self.assertTrue(res_rec.can_undo)

        res_undo = await controller.execute_undo()
        self.assertEqual(res_undo.action, "UNDO")

        res_status = await controller.get_undo_redo_history()
        self.assertTrue(res_status.can_redo)


if __name__ == "__main__":
    unittest.main()
