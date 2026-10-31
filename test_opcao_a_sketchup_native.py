"""
Testes unitários automatizados para as Ferramentas Nativas Oficiais do SketchUp (Opção A).
Cobre todos os 6 motores em Pure Python (Zero DLL) e as camadas da arquitetura:
1. WalkLookAroundEngine (Position Camera, Look Around, Walk com colisão e degraus)
2. SandboxToolsEngine (Smoove, Stamp, Drape, Flip Edge)
3. MatchPhotoEngine (Calibração fotográfica de câmera e perspectiva)
4. WatermarkStyleEngine (Estilos de marca d'água Overlay/Background nos 9 pontos)
5. DynamicComponentInteractionEngine (Interação de clique oficial Trimble DC onClick)
6. TrimbleSolidToolsEngine (Intersect, Union, Subtract, Trim, Split)
"""

import unittest
import asyncio

from core.walk_look_around_engine import WalkLookAroundEngine
from core.sandbox_tools_engine import SandboxToolsEngine
from core.match_photo_engine import MatchPhotoEngine
from core.watermark_style_engine import WatermarkStyleEngine
from core.dynamic_component_interaction_engine import DynamicComponentInteractionEngine
from core.trimble_solid_tools_engine import TrimbleSolidToolsEngine

from app.schemas.scene import (
    PositionCameraNativeRequest,
    LookAroundNativeRequest,
    WalkStepNativeRequest,
    SandboxSmooveRequest,
    SandboxStampRequest,
    SandboxDrapeRequest,
    SandboxFlipEdgeRequest,
    MatchPhotoCalibrateRequest,
    WatermarkStyleConfigureRequest,
    DynamicComponentInteractRequest,
    TrimbleSolidToolsRequest,
)
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController


class TestOpcaoASketchupNative(unittest.TestCase):
    """Suíte de testes para as ferramentas nativas oficiais do SketchUp."""

    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    # 1. WalkLookAroundEngine
    def test_position_camera_core(self):
        res = WalkLookAroundEngine.position_camera(
            eye_x=0.0, eye_y=-5.0, eye_z=0.0,
            target_x=0.0, target_y=0.0, target_z=1.0,
            eye_height_m=1.68
        )
        self.assertEqual(res["eye"], (0.0, -5.0, 1.68))
        self.assertEqual(res["eye_height_m"], 1.68)
        self.assertEqual(res["up"], (0.0, 0.0, 1.0))
        self.assertAlmostEqual(res["fov_deg"], 35.0)

    def test_look_around_core(self):
        res = WalkLookAroundEngine.look_around(
            eye=(0.0, -5.0, 1.68),
            current_yaw_deg=0.0,
            current_pitch_deg=0.0,
            delta_yaw_deg=30.0,
            delta_pitch_deg=10.0
        )
        self.assertEqual(res["eye"], (0.0, -5.0, 1.68))
        self.assertAlmostEqual(res["yaw_deg"], 30.0)
        self.assertAlmostEqual(res["pitch_deg"], 10.0)

    def test_walk_step_core_free_and_collision(self):
        # Passo livre
        res_free = WalkLookAroundEngine.walk_step(
            current_eye=(0.0, 0.0, 1.68),
            yaw_deg=0.0,
            move_forward=1.0,
            move_strafe=0.0
        )
        self.assertTrue(res_free["moved"])
        self.assertFalse(res_free["collision_detected"])
        self.assertAlmostEqual(res_free["eye"][1], 1.0)

        # Passo com colisão em obstáculo intransponível (> 0.22m)
        obs = [{"min_x": -1.0, "max_x": 1.0, "min_y": 0.5, "max_y": 2.0, "max_z": 2.0}]
        res_col = WalkLookAroundEngine.walk_step(
            current_eye=(0.0, 0.0, 1.68),
            yaw_deg=0.0,
            move_forward=1.0,
            move_strafe=0.0,
            obstacles_aabb=obs
        )
        self.assertTrue(res_col["collision_detected"])
        self.assertFalse(res_col["moved"])

        # Passo com degrau transponível (step-up <= 0.22m)
        step_obs = [{"min_x": -1.0, "max_x": 1.0, "min_y": 0.5, "max_y": 2.0, "max_z": 0.18}]
        res_step = WalkLookAroundEngine.walk_step(
            current_eye=(0.0, 0.0, 1.68),
            yaw_deg=0.0,
            move_forward=1.0,
            move_strafe=0.0,
            obstacles_aabb=step_obs
        )
        self.assertFalse(res_step["collision_detected"])
        self.assertTrue(res_step["step_up_applied"])
        self.assertAlmostEqual(res_step["eye"][2], 1.68 + 0.18)

    # 2. SandboxToolsEngine
    def test_sandbox_smoove(self):
        verts = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (10.0, 10.0, 0.0)]
        res = SandboxToolsEngine.smoove(verts, center_x=0.0, center_y=0.0, radius_m=3.0, offset_z_m=2.0)
        self.assertEqual(res["affected_vertices_count"], 2)
        # O vértice do centro deve subir exatamente 2.0m
        self.assertAlmostEqual(res["vertices"][0][2], 2.0)
        # O vértice fora do raio não deve mudar
        self.assertAlmostEqual(res["vertices"][2][2], 0.0)

    def test_sandbox_stamp(self):
        verts = [(0.0, 0.0, 0.5), (10.0, 10.0, 0.5)]
        footprint = [(-2.0, -2.0), (2.0, -2.0), (2.0, 2.0), (-2.0, 2.0)]
        res = SandboxToolsEngine.stamp(verts, footprint, plateau_elevation_z=1.5, skirt_offset_m=1.0)
        self.assertEqual(res["plateau_vertices_count"], 1)
        self.assertAlmostEqual(res["vertices"][0][2], 1.5)

    def test_sandbox_drape(self):
        path = [(0.0, 0.0), (2.0, 0.0)]
        triangles = [[(0.0, -1.0, 1.0), (3.0, -1.0, 1.0), (1.5, 2.0, 1.0)]]
        res = SandboxToolsEngine.drape(path, triangles)
        self.assertEqual(res["draped_points_count"], 2)
        self.assertAlmostEqual(res["draped_path_3d"][0][2], 1.0)
        self.assertGreater(res["total_3d_length_m"], 0.0)

    def test_sandbox_flip_edge(self):
        tri_a = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (1.0, 1.0, 0.0)]
        tri_b = [(0.0, 0.0, 0.0), (1.0, 1.0, 0.0), (-1.0, 1.0, 0.0)]
        res = SandboxToolsEngine.flip_edge(tri_a, tri_b)
        self.assertTrue(res["success"])
        self.assertEqual(len(res["flipped_triangles"]), 2)

    # 3. MatchPhotoEngine
    def test_match_photo_calibrate(self):
        r1 = ((100.0, 200.0), (400.0, 250.0))
        r2 = ((100.0, 500.0), (400.0, 480.0))
        g1 = ((500.0, 250.0), (900.0, 210.0))
        g2 = ((500.0, 480.0), (900.0, 510.0))
        res = MatchPhotoEngine.calibrate_camera(1920, 1080, r1, r2, g1, g2, reference_height_m=3.0)
        self.assertIn("vanishing_points", res)
        self.assertGreater(res["focal_length_px"], 0.0)
        self.assertGreater(res["fov_vertical_deg"], 0.0)
        self.assertIn("recommended_camera", res)

    # 4. WatermarkStyleEngine
    def test_watermark_style_configure(self):
        res = WatermarkStyleEngine.configure_watermark(
            name="Selo Parkelô",
            image_url="/static/stamp.png",
            layer="overlay",
            placement="screen_position",
            anchor="bottom-right",
            opacity_pct=80.0
        )
        self.assertEqual(res["anchor"], "bottom-right")
        self.assertEqual(res["css_styles"]["opacity"], "0.80")
        self.assertEqual(res["css_styles"]["z-index"], "15")

    # 5. DynamicComponentInteractionEngine
    def test_dynamic_component_interact(self):
        attrs = {
            "onclick": 'ANIMATE("roty", 0, 90); ALERT("Porta aberta!")',
            "roty": 0
        }
        res = DynamicComponentInteractionEngine.execute_interaction("porta_1", attrs)
        self.assertTrue(res["success"])
        self.assertEqual(res["updated_attributes"]["roty"], 90.0)
        self.assertIn("Porta aberta!", res["alerts"])
        self.assertIn("target_transform", res)

        # Segundo clique deve ciclar de volta para 0
        res2 = DynamicComponentInteractionEngine.execute_interaction("porta_1", res["updated_attributes"])
        self.assertEqual(res2["updated_attributes"]["roty"], 0.0)

    # 6. TrimbleSolidToolsEngine
    def test_solid_tools_operations(self):
        box_a = {"name": "A", "origin": (0, 0, 0), "size": (2, 2, 2)}
        box_b = {"name": "B", "origin": (1, 1, 1), "size": (2, 2, 2)}

        # Intersect
        res_inter = TrimbleSolidToolsEngine.execute_solid_operation("intersect", box_a, box_b)
        self.assertTrue(res_inter["has_intersection"])
        self.assertAlmostEqual(res_inter["intersection_volume_m3"], 1.0)

        # Union
        res_union = TrimbleSolidToolsEngine.execute_solid_operation("union", box_a, box_b)
        self.assertTrue(res_union["success"])
        self.assertEqual(res_union["resulting_solids_count"], 1)

        # Trim (preserva ferramenta B)
        res_trim = TrimbleSolidToolsEngine.execute_solid_operation("trim", box_a, box_b)
        self.assertTrue(res_trim["success"])
        self.assertEqual(res_trim["resulting_solids_count"], 2)

        # Split (gera 3 partes)
        res_split = TrimbleSolidToolsEngine.execute_solid_operation("split", box_a, box_b)
        self.assertTrue(res_split["success"])
        self.assertEqual(res_split["resulting_solids_count"], 3)

    # Testes Assíncronos do Controller
    def test_async_controllers_native(self):
        async def run_controllers():
            # Position Camera
            req_pos = PositionCameraNativeRequest(eye_x=0.0, eye_y=-5.0, eye_z=0.0)
            res_pos = await self.controller.position_camera_native(req_pos)
            self.assertEqual(res_pos.entity_type, "sketchup_native_position_camera")

            # Look Around
            req_look = LookAroundNativeRequest()
            res_look = await self.controller.look_around_native(req_look)
            self.assertEqual(res_look.entity_type, "sketchup_native_look_around")

            # Walk Step
            req_walk = WalkStepNativeRequest()
            res_walk = await self.controller.walk_step_native(req_walk)
            self.assertEqual(res_walk.entity_type, "sketchup_native_walk_step")

            # Sandbox Smoove
            req_smoove = SandboxSmooveRequest(vertices=[(0, 0, 0), (1, 1, 0)], center_x=0.0, center_y=0.0)
            res_smoove = await self.controller.sandbox_smoove(req_smoove)
            self.assertEqual(res_smoove.entity_type, "sketchup_native_sandbox_smoove")

            # Solid Tools Trim
            req_solid = TrimbleSolidToolsRequest(
                operation="trim",
                solid_a={"origin": (0, 0, 0), "size": (1, 1, 1)},
                solid_b={"origin": (0.5, 0.5, 0.5), "size": (1, 1, 1)}
            )
            res_solid = await self.controller.trimble_solid_tools_execute(req_solid)
            self.assertEqual(res_solid.entity_type, "sketchup_native_trimble_solid_tools")

        asyncio.run(run_controllers())


if __name__ == "__main__":
    unittest.main()
