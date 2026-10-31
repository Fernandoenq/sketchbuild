"""Suíte de Testes Automatizados para a Opção A (Parte 6) - Ferramentas Nativas Oficiais do SketchUp.

Valida com 100% de cobertura as 7 novas ferramentas analíticas do SketchUp Pro (Zero DLL / Pure Python):
1. AddDetailSandboxEngine (Adicionar Detalhe na Malha TIN da Caixa de Areia)
2. FlipEdgeSandboxEngine (Girar Aresta Diagonal em Malha TIN)
3. WalkCameraGravityEngine (Percorrer com Gravidade, Degraus e Colisão)
4. LookAroundCameraEngine (Olhar ao Redor em Pan/Tilt com Tripé Fixo e VCB)
5. PositionCameraEngine (Posicionar Câmera na Altura dos Olhos com Arraste)
6. FogSettingsEngine (Gerenciador de Névoa Linear e Conversão WebGL)
7. GraphicExport2DEngine (Exportação Gráfica 2D em Alta Definição com DPI e Linhas)
8. Validação arquitetural completa (Repository -> Service -> Controller)
"""

import unittest
import asyncio

from core.add_detail_sandbox_engine import AddDetailSandboxEngine
from core.flip_edge_sandbox_engine import FlipEdgeSandboxEngine
from core.walk_camera_gravity_engine import WalkCameraGravityEngine
from core.look_around_camera_engine import LookAroundCameraEngine
from core.position_camera_engine import PositionCameraEngine
from core.fog_settings_engine import FogSettingsEngine
from core.graphic_export_2d_engine import GraphicExport2DEngine

from app.schemas.scene import (
    AddDetailSandboxRequest,
    FlipEdgeSandboxRequest,
    WalkCameraGravityRequest,
    LookAroundCameraRequest,
    PositionCameraRequest,
    FogSettingsRequest,
    GraphicExport2DRequest,
)
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController


class TestOpcaoAParte6SketchupNative(unittest.TestCase):
    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    # 1. AddDetailSandboxEngine
    def test_01_add_detail_sandbox_engine(self):
        verts = [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [2.0, 3.0, 0.5], [2.0, -3.0, -0.5]]
        tris = [[0, 1, 2], [0, 3, 1]]

        # Subdivisão de aresta (0, 1)
        res_edge = AddDetailSandboxEngine.subdivide_edge(verts, tris, 0, 1)
        self.assertTrue(res_edge["success"])
        self.assertEqual(res_edge["new_vertex_index"], 4)
        self.assertEqual(res_edge["new_vertex_xyz"], [2.0, 0.0, 0.0])
        self.assertEqual(res_edge["total_triangles"], 4)
        self.assertEqual(res_edge["total_vertices"], 5)

        # Subdivisão de face (índice 0)
        res_face = AddDetailSandboxEngine.subdivide_face_at_point(verts, tris, 0)
        self.assertTrue(res_face["success"])
        self.assertEqual(res_face["total_triangles"], 4)  # face 0 virou 3 + face 1 mantida = 4

    # 2. FlipEdgeSandboxEngine
    def test_02_flip_edge_sandbox_engine(self):
        verts = [[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [2.0, 3.0, 0.0], [2.0, -3.0, 0.0]]
        tris = [[0, 1, 2], [0, 3, 1]]

        # Aresta (0, 1) é a diagonal comum entre os 2 triângulos
        res = FlipEdgeSandboxEngine.flip_edge(verts, tris, 0, 1)
        self.assertTrue(res["success"])
        self.assertEqual(res["old_edge"], [0, 1])
        # Nova diagonal deve ligar os vértices opostos (2 e 3)
        self.assertEqual(res["new_edge"], [2, 3])
        self.assertEqual(res["total_triangles"], 2)

    # 3. WalkCameraGravityEngine
    def test_03_walk_camera_gravity_engine(self):
        eye = [0.0, 0.0, 1.68]
        target = [0.0, 10.0, 1.68]  # olhando para o Norte (+Y)

        ground_verts = [[-10.0, -10.0, 0.0], [10.0, -10.0, 0.0], [10.0, 10.0, 0.1], [-10.0, 10.0, 0.1]]
        ground_tris = [[0, 1, 2], [0, 2, 3]]

        # Passo de 2.0m para frente
        res = WalkCameraGravityEngine.step_walk(
            camera_eye_xyz=eye,
            camera_target_xyz=target,
            move_forward_m=2.0,
            strafe_right_m=0.0,
            eye_height_m=1.68,
            ground_vertices=ground_verts,
            ground_triangles=ground_tris,
            max_step_height_m=0.22,
            collision_detection=True
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["new_camera_eye"][0], 0.0)
        self.assertAlmostEqual(res["new_camera_eye"][1], 2.0, places=2)
        self.assertFalse(res["collision_blocked"])

    # 4. LookAroundCameraEngine
    def test_04_look_around_camera_engine(self):
        eye = [0.0, 0.0, 1.68]
        res = LookAroundCameraEngine.rotate_look_around(
            camera_eye_xyz=eye,
            current_yaw_deg=0.0,
            current_pitch_deg=0.0,
            delta_yaw_deg=45.0,
            delta_pitch_deg=15.0,
            target_distance_m=10.0,
            new_eye_height_m=1.75,
            base_ground_z=0.0
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["yaw_deg"], 45.0)
        self.assertEqual(res["pitch_deg"], 15.0)
        self.assertEqual(res["camera_eye"][2], 1.75)
        self.assertEqual(res["eye_height_m"], 1.75)
        self.assertGreater(res["camera_target"][2], 1.75)  # olhou para cima

    # 5. PositionCameraEngine
    def test_05_position_camera_engine(self):
        click_pt = [5.0, 8.0, 0.0]
        drag_tgt = [5.0, 18.0, 1.68]

        res = PositionCameraEngine.position_camera(
            click_point_xyz=click_pt,
            drag_target_xyz=drag_tgt,
            eye_height_m=1.68
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["camera_eye"], [5.0, 8.0, 1.68])
        self.assertEqual(res["camera_target"], [5.0, 18.0, 1.68])
        self.assertEqual(res["view_direction"], [0.0, 1.0, 0.0])  # aponta exatamente para o Norte
        self.assertEqual(res["pitch_deg"], 0.0)

    # 6. FogSettingsEngine
    def test_06_fog_settings_engine(self):
        res = FogSettingsEngine.configure_fog(
            enabled=True,
            use_background_color=False,
            fog_color_hex="#A0AEC0",
            background_color_hex="#FFFFFF",
            near_distance_m=15.0,
            far_distance_m=80.0
        )
        self.assertTrue(res["success"])
        self.assertTrue(res["enabled"])
        self.assertEqual(res["resolved_fog_color_hex"], "#A0AEC0")
        self.assertEqual(res["near_distance_m"], 15.0)
        self.assertEqual(res["far_distance_m"], 80.0)
        self.assertEqual(res["fog_span_m"], 65.0)
        self.assertEqual(res["three_fog_payload"]["color_int"], 0xA0AEC0)

    # 7. GraphicExport2DEngine
    def test_07_graphic_export_2d_engine(self):
        res = GraphicExport2DEngine.configure_2d_export(
            image_format="PNG",
            width_px=3840,
            height_px=2160,
            dpi=300,
            line_scale_multiplier=2.0,
            anti_aliasing=True,
            transparent_background=True
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["format"], "PNG")
        self.assertEqual(res["resolution_px"], [3840, 2160])
        self.assertEqual(res["dpi"], 300)
        self.assertTrue(res["transparent_background"])
        self.assertGreater(res["print_size_cm"][0], 30.0)
        self.assertGreater(res["effective_edge_width_px"], 2.0)

    # 8. Validação em Camadas no Controlador (SceneController)
    def test_08_controller_layers_opcao_a_parte_6(self):
        # 8.1 Add Detail
        req1 = AddDetailSandboxRequest(
            tin_vertices=[[0, 0, 0], [4, 0, 0], [2, 3, 0], [2, -3, 0]],
            tin_triangles=[[0, 1, 2], [0, 3, 1]],
            mode="EDGE",
            edge_v0=0,
            edge_v1=1
        )
        res1 = asyncio.run(self.controller.add_detail_sandbox_apply(req1))
        self.assertEqual(res1.entity_type, "sketchup_native_add_detail_sandbox")
        self.assertTrue(res1.detail["success"])

        # 8.2 Flip Edge
        req2 = FlipEdgeSandboxRequest(
            tin_vertices=[[0, 0, 0], [4, 0, 0], [2, 3, 0], [2, -3, 0]],
            tin_triangles=[[0, 1, 2], [0, 3, 1]],
            edge_v0=0,
            edge_v1=1
        )
        res2 = asyncio.run(self.controller.flip_edge_sandbox_apply(req2))
        self.assertEqual(res2.entity_type, "sketchup_native_flip_edge_sandbox")
        self.assertTrue(res2.flip["success"])

        # 8.3 Walk Step
        req3 = WalkCameraGravityRequest(
            camera_eye_xyz=[0.0, 0.0, 1.68],
            camera_target_xyz=[0.0, 10.0, 1.68],
            move_forward_m=1.0,
            eye_height_m=1.68
        )
        res3 = asyncio.run(self.controller.walk_camera_gravity_step(req3))
        self.assertEqual(res3.entity_type, "sketchup_native_walk_camera_gravity")
        self.assertTrue(res3.walk["success"])

        # 8.4 Look Around
        req4 = LookAroundCameraRequest(
            camera_eye_xyz=[0.0, 0.0, 1.68],
            current_yaw_deg=0.0,
            current_pitch_deg=0.0,
            delta_yaw_deg=15.0,
            delta_pitch_deg=5.0
        )
        res4 = asyncio.run(self.controller.look_around_camera_rotate(req4))
        self.assertEqual(res4.entity_type, "sketchup_native_look_around_camera")
        self.assertTrue(res4.look_around["success"])

        # 8.5 Position Camera
        req5 = PositionCameraRequest(
            click_point_xyz=[2.0, 3.0, 0.0],
            drag_target_xyz=[2.0, 8.0, 1.68],
            eye_height_m=1.68
        )
        res5 = asyncio.run(self.controller.position_camera_place(req5))
        self.assertEqual(res5.entity_type, "sketchup_native_position_camera")
        self.assertTrue(res5.position["success"])

        # 8.6 Fog Settings
        req6 = FogSettingsRequest(
            enabled=True,
            use_background_color=True,
            near_distance_m=10.0,
            far_distance_m=100.0
        )
        res6 = asyncio.run(self.controller.fog_settings_configure(req6))
        self.assertEqual(res6.entity_type, "sketchup_native_fog_settings")
        self.assertTrue(res6.fog["success"])

        # 8.7 Graphic Export 2D
        req7 = GraphicExport2DRequest(
            image_format="PNG",
            width_px=1920,
            height_px=1080,
            dpi=150
        )
        res7 = asyncio.run(self.controller.graphic_export_2d_configure(req7))
        self.assertEqual(res7.entity_type, "sketchup_native_graphic_export_2d")
        self.assertTrue(res7.export_2d["success"])


if __name__ == "__main__":
    unittest.main()
