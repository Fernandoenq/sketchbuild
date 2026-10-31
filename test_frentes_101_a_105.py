"""
Testes Unitários Automatizados - Frentes 101 a 105
SketchBuild - Engenharia Reversa do SketchUp (Zero DLL)
Frente 101: StairGeneratorEngine (Escadas Paramétricas & Ergonomia Blondel NBR 9050)
Frente 102: VoronoiFractureEngine (Painéis Vazados e Células Voronoi 3D)
Frente 103: WindPressureEngine (Pressão Dinâmica e Cargas de Vento NBR 6123)
Frente 104: AtmosphericScatteringEngine (Céu Físico Rayleigh/Mie Three.js Sky)
Frente 105: IFC4BimExportEngine (Compilação STEP ISO-10303-21 IFC4 LOD 350)
"""

import unittest

from core.stair_generator_engine import StairGeneratorEngine
from core.voronoi_fracture_engine import VoronoiFractureEngine
from core.wind_pressure_engine import WindPressureEngine
from core.atmosphere_scattering_engine import AtmosphericScatteringEngine
from core.ifc4_bim_export_engine import IFC4BimExportEngine


class TestFrentes101A105(unittest.IsolatedAsyncioTestCase):

    def test_frente_101_stair_generator_engine(self):
        # Escada de 2.80m de desnível
        blondel = StairGeneratorEngine.calculate_blondel(2.80, target_riser_m=0.175)
        self.assertEqual(blondel["num_risers"], 16)
        self.assertAlmostEqual(blondel["riser_height_m"], 0.175, places=3)
        self.assertTrue(blondel["is_compliant_nbr9050"])

        stair = StairGeneratorEngine.generate_straight_stair(total_height_m=2.80, stair_width_m=1.20)
        self.assertEqual(stair["entity_type"], "StairGeometryResult")
        self.assertEqual(stair["steps_count"], 16)
        self.assertEqual(stair["stair_width_m"], 1.20)
        self.assertEqual(len(stair["handrail_path"]), 16)
        self.assertGreater(stair["triangles_count"], 50)

    def test_frente_102_voronoi_fracture_engine(self):
        panel = VoronoiFractureEngine.generate_voronoi_panel(
            width_m=2.0, height_m=1.0, num_seeds=8, cell_inset_ratio=0.15
        )
        self.assertEqual(panel["entity_type"], "VoronoiPanelResult")
        self.assertEqual(panel["seeds_count"], 8)
        self.assertEqual(len(panel["cells"]), 8)
        self.assertEqual(len(panel["cells"][0]["outer_loop"]), 12)
        self.assertEqual(len(panel["cells"][0]["inner_inset_loop"]), 12)

    def test_frente_103_wind_pressure_engine(self):
        wind = WindPressureEngine.calculate_wind_pressure(
            basic_speed_v0_m_s=45.0,
            terrain_category="IV",
            building_height_m=15.0,
            facade_width_m=25.0
        )
        self.assertEqual(wind["entity_type"], "WindPressureReport")
        self.assertGreater(wind["aerodynamics"]["characteristic_velocity_vk_m_s"], 30.0)
        self.assertGreater(wind["aerodynamics"]["dynamic_pressure_q_pa"], 500.0)
        self.assertGreater(wind["facade_loads"]["total_horizontal_drag_kn"], 10.0)

    def test_frente_104_atmosphere_scattering_engine(self):
        sky = AtmosphericScatteringEngine.configure_physical_sky(
            solar_elevation_deg=45.0,
            solar_azimuth_deg=180.0,
            turbidity=3.5,
            rayleigh=1.5
        )
        self.assertEqual(sky["entity_type"], "AtmosphericSkyConfig")
        self.assertEqual(len(sky["sun_position_vector"]), 3)
        self.assertGreater(sky["sun_position_vector"][1], 0.5)  # Y deve ser positivo (sol acima do horizonte)
        self.assertIn("sunPosition", sky["three_sky_uniforms"])
        self.assertGreater(sky["atmospheric_parameters"]["estimated_sun_kelvin"], 4000.0)

    def test_frente_105_ifc4_bim_export_engine(self):
        elements = [
            {
                "name": "Parede Externa",
                "ifc_type": "IfcWall",
                "vertices": [
                    [0.0, 0.0, 0.0], [5.0, 0.0, 0.0], [5.0, 0.2, 0.0], [0.0, 0.2, 0.0],
                    [0.0, 0.0, 3.0], [5.0, 0.0, 3.0], [5.0, 0.2, 3.0], [0.0, 0.2, 3.0],
                ],
                "triangles": [
                    [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
                    [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
                ]
            }
        ]
        step_text = IFC4BimExportEngine.compile_ifc4_step("Projeto Teste", elements)
        self.assertIn("ISO-10303-21;", step_text)
        self.assertIn("FILE_SCHEMA(('IFC4'));", step_text)
        self.assertIn("IFCWALL", step_text)
        self.assertIn("IFCFACETEDBREP", step_text)
        self.assertIn("END-ISO-10303-21;", step_text)

    async def test_controller_layers_frentes_101_a_105(self):
        from app.repositories.skp_engine_repository import SkpEngineRepository
        from app.services.scene_service import SceneService
        from app.controllers.scene_controller import SceneController
        from app.schemas.scene import (
            StairGeneratorRequest,
            VoronoiPanelRequest,
            WindPressureRequest,
            AtmosphericSkyRequest,
            IFC4BimExportRequest,
        )

        repo = SkpEngineRepository()
        service = SceneService(repository=repo)
        controller = SceneController(service=service)

        # 101. Controller Stair
        req_101 = StairGeneratorRequest(
            total_height_m=2.80,
            stair_width_m=1.0,
            stair_type="STRAIGHT",
            origin_xyz=[0.0, 0.0, 0.0],
            add_handrail=True
        )
        res_101 = await controller.generate_stair(req_101)
        self.assertEqual(res_101.entity_type, "StairGeometryResult")
        self.assertEqual(res_101.steps_count, 16)

        # 102. Controller Voronoi Panel
        req_102 = VoronoiPanelRequest(
            width_m=2.0,
            height_m=3.0,
            thickness_m=0.05,
            num_seeds=10,
            seed_random_seed=42,
            cell_inset_ratio=0.15
        )
        res_102 = await controller.generate_voronoi_panel(req_102)
        self.assertEqual(res_102.entity_type, "VoronoiPanelResult")
        self.assertEqual(res_102.seeds_count, 10)

        # 103. Controller Wind Pressure
        req_103 = WindPressureRequest(
            basic_speed_v0_m_s=45.0,
            terrain_category="IV",
            building_height_m=12.0,
            facade_width_m=20.0,
            facade_length_m=15.0,
            topographic_s1=1.0,
            statistical_s3=1.0
        )
        res_103 = await controller.calculate_wind_pressure(req_103)
        self.assertEqual(res_103.entity_type, "WindPressureReport")
        self.assertGreater(res_103.aerodynamics["dynamic_pressure_q_pa"], 0)

        # 104. Controller Atmospheric Sky
        req_104 = AtmosphericSkyRequest(
            solar_elevation_deg=35.0,
            solar_azimuth_deg=135.0,
            turbidity=3.0,
            rayleigh=1.2
        )
        res_104 = await controller.configure_atmospheric_sky(req_104)
        self.assertEqual(res_104.entity_type, "AtmosphericSkyConfig")
        self.assertIn("sunPosition", res_104.three_sky_uniforms)

        # 105. Controller IFC4 BIM Export
        req_105 = IFC4BimExportRequest(
            project_name="Edificio Controller Test",
            elements=[
                {
                    "name": "Parede Controller",
                    "ifc_type": "IfcWall",
                    "vertices": [[0,0,0], [1,0,0], [1,1,0], [0,1,0]],
                    "triangles": [[0,1,2], [0,2,3]]
                }
            ]
        )
        res_105 = await controller.export_ifc4_bim(req_105)
        self.assertEqual(res_105.entity_type, "IFC4StepExportResult")
        self.assertIn("ISO-10303-21;", res_105.step_content)


if __name__ == "__main__":
    unittest.main()
