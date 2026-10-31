"""
Testes Unitários Automatizados - Frentes 91 a 95
SketchBuild - Engenharia Reversa do SketchUp (Zero DLL)
Frente 91: ShellSolidOffsetEngine (Espessura de Casca Sólida B-Rep)
Frente 92: PhotometricSpotLightEngine (Spotlights Fotométricos & Kelvin)
Frente 93: PipingDuctworkEngine (Tubulações Paramétricas 3D & Conexões)
Frente 94: OrbitFlythroughPathEngine (Trajetória Órbita & Flythrough Spline)
Frente 95: CamCutlistFabricationEngine (Lista de Corte CNC CSV/JSON)
"""

import unittest

from core.shell_solid_offset_engine import ShellSolidOffsetEngine
from core.photometric_spot_light_engine import PhotometricSpotLightEngine
from core.piping_ductwork_engine import PipingDuctworkEngine
from core.orbit_flythrough_path_engine import OrbitFlythroughPathEngine
from core.cam_cutlist_fabrication_engine import CamCutlistFabricationEngine


class TestFrentes91A95(unittest.IsolatedAsyncioTestCase):

    def test_frente_91_shell_solid_offset_engine(self):
        # Plano horizontal simples de 2m x 2m com 4 vértices e 1 face
        verts = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0), (0.0, 2.0, 0.0)]
        faces = [[0, 1, 2, 3]]

        res = ShellSolidOffsetEngine.create_solid_shell(verts, faces, thickness_m=0.1, inwards=False)
        self.assertEqual(res["entity_type"], "SolidShellResult")
        self.assertEqual(res["thickness_m"], 0.1)
        self.assertEqual(res["total_vertices_count"], 8)
        # 1 face frente + 1 face fundo + 4 quads laterais de borda = 6 faces
        self.assertEqual(res["total_faces_count"], 6)
        self.assertEqual(res["boundary_quads_count"], 4)
        self.assertTrue(res["is_solid_manifold"])

    def test_frente_92_photometric_spot_light_engine(self):
        # Lâmpada spot 3000K (Warm White) apontando para baixo
        pos = (0.0, 0.0, 3.0)
        target = (0.0, 0.0, 0.0)

        spot = PhotometricSpotLightEngine.configure_spot_light(
            pos, target, lumens=1500.0, color_temperature_k=3000.0, beam_angle_deg=60.0
        )
        self.assertEqual(spot["entity_type"], "PhotometricSpotLight")
        self.assertEqual(spot["direction"], [0.0, 0.0, -1.0])
        self.assertIn("#", spot["photometrics"]["color_hex"])
        self.assertAlmostEqual(spot["beam_geometry"]["beam_angle_deg"], 60.0)
        self.assertEqual(spot["three_config"]["decay"], 2)

    def test_frente_93_piping_ductwork_engine(self):
        # Trajetória em L com 3 pontos (cotovelo de 90°)
        route = [
            (0.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (3.0, 3.0, 0.0),
        ]
        res = PipingDuctworkEngine.generate_pipe_route(route, outer_diameter_mm=100.0, radial_segments=8)
        self.assertEqual(res["entity_type"], "PipingRouteResult")
        self.assertEqual(res["segments_count"], 2)
        self.assertEqual(res["fittings_count"], 1)
        self.assertEqual(res["fittings"][0]["fitting_type"], "ELBOW")
        self.assertAlmostEqual(res["fittings"][0]["angle_deg"], 90.0, places=1)
        self.assertGreater(len(res["triangles"]), 10)

    def test_frente_94_orbit_flythrough_path_engine(self):
        # Órbita ao redor de (0,0,0) por 2 segundos a 10 fps = 20 frames
        orbit = OrbitFlythroughPathEngine.generate_orbit_path(
            target_point=(0.0, 0.0, 0.0),
            radius_m=5.0,
            duration_seconds=2.0,
            fps=10
        )
        self.assertEqual(orbit["entity_type"], "CameraAnimationPath")
        self.assertEqual(orbit["mode"], "ORBIT")
        self.assertEqual(orbit["total_frames"], 20)
        self.assertEqual(len(orbit["frames"]), 20)

        # Flythrough por 3 waypoints
        waypoints = [(0.0, 0.0, 2.0), (5.0, 2.0, 3.0), (10.0, 0.0, 2.0)]
        fly = OrbitFlythroughPathEngine.generate_flythrough_path(
            waypoints=waypoints,
            target_point=(5.0, 5.0, 0.0),
            duration_seconds=2.0,
            fps=10
        )
        self.assertEqual(fly["mode"], "FLYTHROUGH")
        self.assertEqual(len(fly["frames"]), 20)

    def test_frente_95_cam_cutlist_fabrication_engine(self):
        parts = [
            {"id": "VIGA_01", "name": "Viga Principal", "length_mm": 2000.0, "width_mm": 150.0, "thickness_mm": 45.0, "quantity": 4},
            {"id": "MONT_01", "name": "Montante Lateral", "length_mm": 1200.0, "width_mm": 90.0, "thickness_mm": 45.0, "quantity": 8},
        ]
        res = CamCutlistFabricationEngine.generate_cnc_cutlist(parts, trim_margin_mm=10.0, export_csv=True)
        self.assertEqual(res["entity_type"], "CamCutlistReport")
        self.assertEqual(res["unique_parts_count"], 2)
        self.assertEqual(res["total_items_count"], 12)
        self.assertIn("PartID;Name;Material", res["csv_data"])
        self.assertIn("VIGA_01", res["csv_data"])
        self.assertGreater(res["cutting_yield_percent"], 80.0)

    async def test_controller_layers_frentes_91_a_95(self):
        from app.repositories.skp_engine_repository import SkpEngineRepository
        from app.services.scene_service import SceneService
        from app.controllers.scene_controller import SceneController
        from app.schemas.scene import (
            SolidShellRequest,
            PhotometricSpotLightRequest,
            PipingRouteRequest,
            CameraAnimationPathRequest,
            CamCutlistRequest,
        )

        repo = SkpEngineRepository()
        service = SceneService(repository=repo)
        controller = SceneController(service=service)

        # 91. Controller Solid Shell
        req_91 = SolidShellRequest(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]],
            faces=[[0, 1, 2, 3]],
            thickness_m=0.08
        )
        res_91 = await controller.create_solid_shell(req_91)
        self.assertEqual(res_91.entity_type, "SolidShellResult")
        self.assertEqual(res_91.total_vertices_count, 8)

        # 92. Controller Spotlight
        req_92 = PhotometricSpotLightRequest(
            position=[0.0, 0.0, 3.0],
            target=[0.0, 0.0, 0.0],
            lumens=1600.0,
            color_temperature_k=3200.0
        )
        res_92 = await controller.configure_spot_light(req_92)
        self.assertEqual(res_92.entity_type, "PhotometricSpotLight")
        self.assertEqual(res_92.photometrics["lumens"], 1600.0)

        # 93. Controller Piping Route
        req_93 = PipingRouteRequest(
            route_points=[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [2.0, 2.0, 0.0]],
            outer_diameter_mm=88.9
        )
        res_93 = await controller.generate_pipe_route(req_93)
        self.assertEqual(res_93.entity_type, "PipingRouteResult")
        self.assertEqual(res_93.fittings_count, 1)

        # 94. Controller Camera Animation Path
        req_94 = CameraAnimationPathRequest(
            mode="ORBIT",
            target_point=[0.0, 0.0, 0.0],
            radius_m=6.0,
            duration_seconds=1.0,
            fps=10
        )
        res_94 = await controller.generate_camera_animation_path(req_94)
        self.assertEqual(res_94.entity_type, "CameraAnimationPath")
        self.assertEqual(res_94.total_frames, 10)

        # 95. Controller CNC Cutlist
        req_95 = CamCutlistRequest(
            parts=[
                {"id": "PAINEL_01", "name": "Painel Superior", "length_mm": 1800.0, "width_mm": 600.0, "thickness_mm": 18.0, "quantity": 2}
            ],
            export_csv=True
        )
        res_95 = await controller.generate_cnc_cutlist(req_95)
        self.assertEqual(res_95.entity_type, "CamCutlistReport")
        self.assertEqual(res_95.total_items_count, 2)
        self.assertIn("PAINEL_01", res_95.csv_data)


if __name__ == "__main__":
    unittest.main()
