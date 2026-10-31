"""
Testes Unitários Automatizados - Frentes 96 a 100 (Marco 100 Frentes!)
SketchBuild - Engenharia Reversa do SketchUp (Zero DLL)
Frente 96: ArchitecturalWallWindowEngine (Paredes e Vãos de Janelas/Portas)
Frente 97: SheetMetalUnfoldEngine (Planificação de Chapa Metálica DIN 6935)
Frente 98: ShadowCastingSurfaceEngine (Projeção de Sombras em Superfícies)
Frente 99: WaterCausticsShaderEngine (Shader PBR de Água, Ondas e Cáusticas)
Frente 100: SkpLODOptimizerEngine (Cadeia de Níveis de Detalhe LOD Three.js)
"""

import unittest

from core.architectural_wall_engine import ArchitecturalWallWindowEngine
from core.sheet_metal_unfold_engine import SheetMetalUnfoldEngine
from core.shadow_casting_surface_engine import ShadowCastingSurfaceEngine
from core.water_caustics_shader_engine import WaterCausticsShaderEngine
from core.skp_lod_optimizer_engine import SkpLODOptimizerEngine


class TestFrentes96A100(unittest.IsolatedAsyncioTestCase):

    def test_frente_96_architectural_wall_engine(self):
        # Parede de 6m de comprimento com 1 janela (largura 1.5m, peitoril 1.0m)
        openings = [
            {"name": "Janela Sala", "dist_from_start_m": 2.0, "width_m": 1.5, "sill_height_m": 1.0, "height_m": 1.2}
        ]
        res = ArchitecturalWallWindowEngine.generate_wall_with_openings(
            start_pt=(0.0, 0.0, 0.0),
            end_pt=(6.0, 0.0, 0.0),
            height_m=2.8,
            thickness_m=0.15,
            openings=openings
        )
        self.assertEqual(res["entity_type"], "ArchitecturalWallResult")
        self.assertEqual(res["wall_length_m"], 6.0)
        self.assertEqual(res["openings_count"], 1)
        self.assertGreater(res["blocks_count"], 1)
        self.assertLess(res["net_volume_m3"], res["gross_volume_m3"])
        self.assertGreater(res["triangles_count"], 12)

    def test_frente_97_sheet_metal_unfold_engine(self):
        # Perfil U com base 100x50mm e duas abas de 30mm dobradas a 90°
        flanges = [
            {"edge": "LEFT", "length_mm": 30.0, "angle_deg": 90.0},
            {"edge": "RIGHT", "length_mm": 30.0, "angle_deg": 90.0},
        ]
        res = SheetMetalUnfoldEngine.unfold_flanges(
            base_length_mm=100.0,
            base_width_mm=50.0,
            thickness_mm=2.0,
            inner_radius_mm=2.0,
            flanges=flanges
        )
        self.assertEqual(res["entity_type"], "SheetMetalUnfoldResult")
        self.assertEqual(res["flanges_count"], 2)
        # Comprimento total do blank deve ser maior que 100mm e condizente com a tolerância de dobra DIN
        self.assertGreater(res["blank_dimensions_mm"][0], 100.0)
        self.assertLess(res["blank_dimensions_mm"][0], 170.0)
        self.assertEqual(len(res["bend_lines"]), 2)

    def test_frente_98_shadow_casting_surface_engine(self):
        # Torre cúbica de 10m de altura em (0,0) a (2,2)
        verts = [
            (0.0, 0.0, 10.0), (2.0, 0.0, 10.0), (2.0, 2.0, 10.0), (0.0, 2.0, 10.0)
        ]
        # Sol a 45° de altitude vindo do Norte-Leste (vetor descendente sz = -1.0)
        sun_vec = (-1.0, -1.0, -1.0)

        res = ShadowCastingSurfaceEngine.project_shadow_on_plane(
            occluder_vertices=verts,
            sun_direction=sun_vec,
            ground_elevation_z=0.0
        )
        self.assertEqual(res["entity_type"], "ProjectedShadowResult")
        self.assertEqual(res["projected_vertices_count"], 4)
        self.assertGreater(res["shadow_throw_length_m"], 5.0)
        self.assertGreater(res["shadow_bbox_area_m2"], 0.0)

    def test_frente_99_water_caustics_shader_engine(self):
        res = WaterCausticsShaderEngine.configure_water_surface(
            shallow_color_hex="#3498db",
            deep_color_hex="#1a252f",
            wave_amplitude_m=0.08,
            wave_wavelength_m=1.5
        )
        self.assertEqual(res["entity_type"], "PBRWaterMaterialConfig")
        self.assertEqual(res["optical_properties"]["refraction_index_ior"], 1.333)
        self.assertGreater(res["wave_dynamics"]["angular_frequency_omega"], 0.0)
        self.assertEqual(len(res["wave_dynamics"]["gerstner_waves"]), 3)
        self.assertIn("uWaveHeight", res["three_uniforms"])

    def test_frente_100_skp_lod_optimizer_engine(self):
        # Malha de 12 triângulos com 2 vértices duplicados propositais
        verts = [
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0),
            (0.0, 0.0, 0.0),  # Duplicata do vert 0
            (1.0, 1.0, 1.0),  # Duplicata do vert 6
        ]
        tris = [
            [0, 1, 2], [0, 2, 3],
            [4, 5, 6], [4, 6, 7],
            [0, 1, 5], [0, 5, 4],
            [2, 3, 7], [2, 7, 6],
            [0, 3, 7], [0, 7, 4],
            [1, 2, 6], [1, 6, 5],
            [8, 1, 2],        # Usa duplicata 8
            [0, 0, 1],        # Degenerado
        ]

        res = SkpLODOptimizerEngine.generate_lod_chain(verts, tris)
        self.assertEqual(res["entity_type"], "SkpLODChainResult")
        self.assertEqual(len(res["lod_levels"]), 3)
        # LOD0 não deve ter o triângulo degenerado
        self.assertLess(res["lod_levels"][0]["triangles_count"], len(tris))
        # LOD1 e LOD2 devem decrescer em triângulos
        self.assertLessEqual(res["lod_levels"][1]["triangles_count"], res["lod_levels"][0]["triangles_count"])
        self.assertLessEqual(res["lod_levels"][2]["triangles_count"], res["lod_levels"][1]["triangles_count"])
        self.assertGreater(res["lod_levels"][1]["switch_distance_m"], 0.0)

    async def test_controller_layers_frentes_96_a_100(self):
        from app.repositories.skp_engine_repository import SkpEngineRepository
        from app.services.scene_service import SceneService
        from app.controllers.scene_controller import SceneController
        from app.schemas.scene import (
            ArchitecturalWallRequest,
            SheetMetalUnfoldRequest,
            ShadowCastingRequest,
            WaterMaterialConfigRequest,
            SkpLODChainRequest,
        )

        repo = SkpEngineRepository()
        service = SceneService(repository=repo)
        controller = SceneController(service=service)

        # 96. Controller Wall with Openings
        req_96 = ArchitecturalWallRequest(
            start_pt=[0.0, 0.0, 0.0],
            end_pt=[5.0, 0.0, 0.0],
            height_m=2.8,
            thickness_m=0.15,
            openings=[{"name": "Porta", "dist_from_start_m": 1.0, "width_m": 0.9, "sill_height_m": 0.0, "height_m": 2.1}]
        )
        res_96 = await controller.generate_wall_with_openings(req_96)
        self.assertEqual(res_96.entity_type, "ArchitecturalWallResult")
        self.assertEqual(res_96.openings_count, 1)

        # 97. Controller Sheet Metal Unfold
        req_97 = SheetMetalUnfoldRequest(
            base_length_mm=120.0,
            base_width_mm=60.0,
            thickness_mm=1.5,
            inner_radius_mm=2.0,
            flanges=[{"edge": "RIGHT", "length_mm": 25.0, "angle_deg": 90.0}]
        )
        res_97 = await controller.unfold_sheet_metal(req_97)
        self.assertEqual(res_97.entity_type, "SheetMetalUnfoldResult")
        self.assertEqual(res_97.flanges_count, 1)

        # 98. Controller Projected Shadow
        req_98 = ShadowCastingRequest(
            occluder_vertices=[[0.0, 0.0, 5.0], [2.0, 0.0, 5.0], [2.0, 2.0, 5.0]],
            sun_direction=[-1.0, -1.0, -1.0],
            ground_elevation_z=0.0
        )
        res_98 = await controller.calculate_projected_shadow(req_98)
        self.assertEqual(res_98.entity_type, "ProjectedShadowResult")
        self.assertEqual(res_98.projected_vertices_count, 3)

        # 99. Controller Water Material
        req_99 = WaterMaterialConfigRequest(
            shallow_color_hex="#00a8ff",
            deep_color_hex="#192a56"
        )
        res_99 = await controller.configure_water_surface(req_99)
        self.assertEqual(res_99.entity_type, "PBRWaterMaterialConfig")

        # 100. Controller LOD Chain (MARCO 100 FRENTES!)
        req_100 = SkpLODChainRequest(
            vertices=[
                [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0], [0.0, 1.0, 1.0]
            ],
            triangles=[
                [0, 1, 2], [0, 2, 3], [4, 5, 6], [4, 6, 7],
                [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
            ]
        )
        res_100 = await controller.generate_mesh_lod_chain(req_100)
        self.assertEqual(res_100.entity_type, "SkpLODChainResult")
        self.assertEqual(len(res_100.lod_levels), 3)


if __name__ == "__main__":
    unittest.main()
