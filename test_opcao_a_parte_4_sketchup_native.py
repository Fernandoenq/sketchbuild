"""
Testes unitários automatizados para as Ferramentas Nativas Oficiais do SketchUp (Opção A - Parte 4).
Cobre todos os 7 novos motores em Pure Python (Zero DLL) e as camadas da arquitetura:
1. RegularPolygonEngine (Polígono regular paramétrico VCB 6s, 8s, raio circunscrito/inscrito)
2. FreehandCurveEngine (Mão livre com simplificação RDP e fechamento de face plana)
3. ReverseOrientFacesEngine (Inversão e Orientação coerente de faces conexas 2-manifold)
4. DollyFovLensEngine (Dolly de câmera, FOV em graus e distância focal de lente 35mm em mm)
5. IntersectFacesEngine (Interseção 3D de faces com o modelo / seleção gerando arestas de corte)
6. AxisLockInferenceEngine (Bloqueio de eixos por setas X/Y/Z e projeção restrita do cursor)
7. GroundSkyStyleEngine (Céu, solo com transparência e plano de fundo dos estilos)
"""

import unittest
import asyncio

from core.regular_polygon_engine import RegularPolygonEngine
from core.freehand_curve_engine import FreehandCurveEngine
from core.reverse_orient_faces_engine import ReverseOrientFacesEngine
from core.dolly_fov_lens_engine import DollyFovLensEngine
from core.intersect_faces_engine import IntersectFacesEngine
from core.axis_lock_inference_engine import AxisLockInferenceEngine
from core.ground_sky_style_engine import GroundSkyStyleEngine

from app.schemas.scene import (
    RegularPolygonRequest,
    FreehandCurveRequest,
    ReverseOrientFacesRequest,
    DollyFovLensRequest,
    IntersectFacesRequest,
    AxisLockInferenceRequest,
    GroundSkyStyleRequest,
)
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController


class TestOpcaoAParte4SketchupNative(unittest.TestCase):
    """Suíte de testes para a quarta rodada de ferramentas nativas oficiais do SketchUp."""

    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    # 1. RegularPolygonEngine
    def test_regular_polygon_generation(self):
        # Hexágono de raio 2.0m circunscrito
        res = RegularPolygonEngine.generate_regular_polygon(
            sides_count=6,
            radius_m=2.0,
            radius_mode="CIRCUMSCRIBED",
            center_xyz=(0.0, 0.0, 0.0)
        )
        self.assertEqual(res["sides_count"], 6)
        self.assertEqual(len(res["vertices"]), 6)
        self.assertEqual(res["edges_count"], 6)
        self.assertEqual(res["triangles_count"], 6)
        self.assertGreater(res["area_m2"], 10.0)

        # Octógono de raio 1.0m inscrito
        res_oct = RegularPolygonEngine.generate_regular_polygon(
            sides_count=8,
            radius_m=1.0,
            radius_mode="INSCRIBED"
        )
        self.assertEqual(res_oct["sides_count"], 8)
        self.assertEqual(len(res_oct["vertices"]), 8)

    # 2. FreehandCurveEngine
    def test_freehand_curve_rdp_simplification(self):
        raw_pts = [
            (0.0, 0.0, 0.0),
            (0.1, 0.001, 0.0),
            (0.2, -0.001, 0.0),
            (0.5, 0.0, 0.0),
            (1.0, 0.5, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.01, 0.02, 0.0)  # Quase fecha
        ]
        res = FreehandCurveEngine.process_freehand_curve(
            raw_points_xyz=raw_pts,
            tolerance_m=0.05,
            auto_close=True,
            close_threshold_m=0.1
        )
        self.assertTrue(res["is_closed"])
        self.assertLess(res["simplified_points_count"], res["raw_points_count"])
        self.assertIsNotNone(res["face"])
        self.assertGreater(res["face"]["area_m2"], 0.0)

    # 3. ReverseOrientFacesEngine
    def test_reverse_orient_faces(self):
        face1 = {
            "vertices": [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0)],
            "normal": [0.0, 0.0, 1.0]
        }
        # Inversão simples
        rev = ReverseOrientFacesEngine.reverse_face(face1)
        self.assertEqual(rev["normal"], [-0.0, -0.0, -1.0])
        self.assertEqual(rev["vertices"][0], face1["vertices"][-1])

        # Orient Faces conexas
        # Face2 compartilha aresta (1,0,0)-(1,1,0), mas está percorrida no mesmo sentido -> deve inverter
        face2 = {
            "vertices": [(1.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 1.0, 0.0), (1.0, 1.0, 0.0)],
            "normal": [0.0, 0.0, 1.0]
        }
        orient_res = ReverseOrientFacesEngine.orient_connected_faces([face1, face2], reference_face_index=0)
        self.assertEqual(orient_res["status"], "success")
        self.assertEqual(orient_res["connected_oriented_count"], 2)

    # 4. DollyFovLensEngine
    def test_dolly_fov_lens(self):
        # 50mm equivale a aprox 39.6 graus em full-frame
        fov = DollyFovLensEngine.focal_length_mm_to_fov_degrees(50.0)
        self.assertAlmostEqual(fov, 39.6, delta=0.5)

        # 35 graus equivale a aprox 57mm
        f_mm = DollyFovLensEngine.fov_degrees_to_focal_length_mm(35.0)
        self.assertAlmostEqual(f_mm, 57.0, delta=1.0)

        # Parse VCB
        vcb1 = DollyFovLensEngine.parse_vcb_camera_input("50mm")
        self.assertEqual(vcb1["input_type"], "FOCAL_LENGTH_MM")
        self.assertEqual(vcb1["focal_length_mm"], 50.0)

        vcb2 = DollyFovLensEngine.parse_vcb_camera_input("60 deg")
        self.assertEqual(vcb2["input_type"], "FOV_DEGREES")
        self.assertEqual(vcb2["fov_degrees"], 60.0)

        # Dolly camera
        dolly = DollyFovLensEngine.apply_camera_dolly(
            eye_xyz=(0.0, -10.0, 0.0),
            target_xyz=(0.0, 0.0, 0.0),
            delta_m=2.0,
            mode="KEEP_TARGET"
        )
        self.assertEqual(dolly["new_eye"][1], -8.0)
        self.assertEqual(dolly["new_distance_to_target_m"], 8.0)

    # 5. IntersectFacesEngine
    def test_intersect_faces(self):
        # Dois planos perpendiculares que se cortam:
        # Plano XY (z=0) e Plano YZ (x=0)
        face_xy = {
            "vertices": [(-2.0, -2.0, 0.0), (2.0, -2.0, 0.0), (2.0, 2.0, 0.0), (-2.0, 2.0, 0.0)],
            "normal": [0.0, 0.0, 1.0]
        }
        face_yz = {
            "vertices": [(0.0, -2.0, -2.0), (0.0, 2.0, -2.0), (0.0, 2.0, 2.0), (0.0, -2.0, 2.0)],
            "normal": [1.0, 0.0, 0.0]
        }
        res = IntersectFacesEngine.intersect_faces_sets([face_xy, face_yz], context_mode="WITH_MODEL")
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["intersection_edges_count"], 0)
        edge = res["intersection_edges"][0]
        self.assertAlmostEqual(edge["length_m"], 4.0, delta=0.1)

    # 6. AxisLockInferenceEngine
    def test_axis_lock_inference(self):
        # Seta Direita = Eixo X (Vermelho)
        lock_x = AxisLockInferenceEngine.resolve_arrow_key_lock("RIGHT")
        self.assertEqual(lock_x["axis_name"], "X")
        self.assertEqual(lock_x["direction_vector"], [1.0, 0.0, 0.0])
        self.assertTrue(lock_x["is_locked"])

        # Projeção no eixo
        proj = AxisLockInferenceEngine.project_point_onto_axis(
            cursor_point=(5.0, 3.2, 7.8),
            origin_point=(0.0, 0.0, 0.0),
            axis_direction=(1.0, 0.0, 0.0)
        )
        self.assertEqual(proj["projected_point"], [5.0, 0.0, 0.0])
        self.assertEqual(proj["distance_along_axis_m"], 5.0)

    # 7. GroundSkyStyleEngine
    def test_ground_sky_style(self):
        res = GroundSkyStyleEngine.configure_background_style(
            background_color="#EEEEEE",
            sky_enabled=True,
            sky_color="#B0D4F1",
            ground_enabled=True,
            ground_color="#C0B0A0",
            ground_transparency_pct=50
        )
        self.assertEqual(res["status"], "success")
        rp = res["render_payload"]
        self.assertTrue(rp["sky"]["enabled"])
        self.assertEqual(rp["sky"]["color_hex"], "#B0D4F1")
        self.assertEqual(rp["ground"]["opacity"], 0.5)

    # 8. Teste Assíncrono dos Controllers (Ponta a Ponta)
    def test_async_controllers_e2e(self):
        async def run_controllers():
            # Controller Polígono
            req_poly = RegularPolygonRequest(sides_count=5, radius_m=3.0)
            res_poly = await self.controller.regular_polygon_generate(req_poly)
            self.assertEqual(res_poly.polygon["sides_count"], 5)

            # Controller Mão Livre
            req_fh = FreehandCurveRequest(
                raw_points_xyz=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)],
                tolerance_m=0.01
            )
            res_fh = await self.controller.freehand_curve_process(req_fh)
            self.assertEqual(res_fh.curve["raw_points_count"], 3)

            # Controller Reversão de Faces
            req_rev = ReverseOrientFacesRequest(
                mode="REVERSE",
                faces=[{"vertices": [(0, 0, 0), (1, 0, 0), (0, 1, 0)], "normal": [0, 0, 1]}],
                selected_face_indices=[0]
            )
            res_rev = await self.controller.reverse_orient_faces(req_rev)
            self.assertEqual(res_rev.result["flipped_count"], 1)

            # Controller Dolly / FOV
            req_dolly = DollyFovLensRequest(operation="PARSE_VCB", vcb_input="85mm")
            res_dolly = await self.controller.dolly_fov_lens_control(req_dolly)
            self.assertEqual(res_dolly.result["focal_length_mm"], 85.0)

            # Controller Bloqueio de Eixo
            req_lock = AxisLockInferenceRequest(arrow_key="UP", cursor_point_xyz=(1.0, 2.0, 3.0))
            res_lock = await self.controller.axis_lock_inference(req_lock)
            self.assertEqual(res_lock.inference["axis_name"], "Z")
            self.assertEqual(res_lock.inference["projection"]["projected_point"], [0.0, 0.0, 3.0])

            # Controller Estilos Fundo/Solo
            req_style = GroundSkyStyleRequest(sky_enabled=False, background_color="#FFFFFF")
            res_style = await self.controller.ground_sky_style_configure(req_style)
            self.assertFalse(res_style.style["style_settings"]["sky_enabled"])

        asyncio.run(run_controllers())


if __name__ == "__main__":
    unittest.main()
