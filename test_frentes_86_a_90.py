"""
Testes Unitários Automatizados - Frentes 86 a 90
SketchBuild - Engenharia Reversa do SketchUp (Zero DLL)
Frente 86: QuadMeshSubDEngine (Subdivisão Catmull-Clark & QuadMesh)
Frente 87: SectionDimensionEngine (Cotas Automáticas de Seção & Níveis NBR 6492)
Frente 88: EquirectangularPanoramaEngine (Panorama 360° & Cubemap 6 Câmeras)
Frente 89: CollisionClashDetectionEngine (Clash Detection BIM & Interferências)
Frente 90: MassPropertiesCenterOfGravityEngine (Volume B-Rep, Massa & CG)
"""

import math
import unittest

from core.quad_mesh_subd_engine import QuadMeshSubDEngine
from core.section_dimension_engine import SectionDimensionEngine
from core.panorama_spherical_engine import EquirectangularPanoramaEngine
from core.clash_collision_engine import CollisionClashDetectionEngine
from core.mass_properties_engine import MassPropertiesCenterOfGravityEngine


class TestFrentes86A90(unittest.IsolatedAsyncioTestCase):

    def test_frente_86_quad_mesh_subd_engine(self):
        # Cubo unitário com 8 vértices e 6 faces quadriláteras
        verts = [
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0), (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0), (0.0, 1.0, 1.0),
        ]
        faces = [
            [0, 1, 2, 3],  # base
            [4, 5, 6, 7],  # topo
            [0, 1, 5, 4],  # frente
            [2, 3, 7, 6],  # tras
            [0, 3, 7, 4],  # esquerda
            [1, 2, 6, 5],  # direita
        ]

        res = QuadMeshSubDEngine.subdivide_catmull_clark(verts, faces, iterations=1)
        self.assertEqual(res["entity_type"], "SubDMeshResult")
        self.assertEqual(res["original_faces_count"], 6)
        # 1 iteração de Catmull-Clark em 6 quads gera 6 * 4 = 24 quads
        self.assertEqual(res["subdivided_quad_faces_count"], 24)
        self.assertEqual(res["triangles_count"], 48)

    def test_frente_87_section_dimension_engine(self):
        # Retângulo de corte de 4.0m de largura x 2.5m de altura
        loop = [
            (0.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
            (4.0, 0.0, 2.5),
            (0.0, 0.0, 2.5),
        ]
        res = SectionDimensionEngine.generate_auto_section_dimensions([loop], offset_m=0.3)
        self.assertEqual(res["entity_type"], "SectionDimensionResult")
        self.assertEqual(res["span_horizontal_m"], 4.0)
        self.assertEqual(res["span_vertical_m"], 2.5)
        self.assertEqual(len(res["level_marks"]), 2)
        self.assertIn("4.00 m", res["dimensions"][0]["text"])

    def test_frente_88_equirectangular_panorama_engine(self):
        # Ponto de vista do observador
        eye = (0.0, 0.0, 1.65)
        cubemap = EquirectangularPanoramaEngine.calculate_cubemap_cameras(eye)
        self.assertEqual(cubemap["entity_type"], "CubemapCameraSet")
        self.assertEqual(cubemap["faces_count"], 6)

        grid = EquirectangularPanoramaEngine.calculate_equirectangular_grid(eye, horizontal_samples=8, vertical_samples=4)
        self.assertEqual(grid["entity_type"], "EquirectangularProjectionGrid")
        self.assertEqual(grid["horizontal_fov_deg"], 360.0)
        self.assertGreater(grid["total_sample_rays"], 30)

    def test_frente_89_clash_collision_engine(self):
        components = [
            {"id": "comp_1", "name": "Viga Aço", "bbox_min": [0.0, 0.0, 0.0], "bbox_max": [2.0, 0.2, 0.2]},
            {"id": "comp_2", "name": "Pilar Concreto", "bbox_min": [1.5, -0.1, -0.5], "bbox_max": [1.8, 0.3, 2.0]},  # Colisão real
            {"id": "comp_3", "name": "Tubo Hidráulico", "bbox_min": [2.005, 0.0, 0.0], "bbox_max": [2.5, 0.1, 0.1]},  # Folga < 1cm
        ]

        res = CollisionClashDetectionEngine.detect_clashes(components, clearance_tolerance_m=0.01)
        self.assertEqual(res["entity_type"], "ClashDetectionReport")
        self.assertEqual(res["hard_clashes_count"], 1)
        self.assertEqual(res["clearance_clashes_count"], 1)
        self.assertEqual(res["clashes"][0]["severity"], "CRITICAL")

    def test_frente_90_mass_properties_engine(self):
        # Caixa de 2m x 1m x 0.5m = Volume 1.0 m³
        # Vértices
        v = [
            (0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 1.0, 0.0), (0.0, 1.0, 0.0),
            (0.0, 0.0, 0.5), (2.0, 0.0, 0.5), (2.0, 1.0, 0.5), (0.0, 1.0, 0.5),
        ]
        # Triângulos com normais apontando para fora
        t = [
            # Base (z=0)
            [0, 2, 1], [0, 3, 2],
            # Topo (z=0.5)
            [4, 5, 6], [4, 6, 7],
            # Frente (y=0)
            [0, 1, 5], [0, 5, 4],
            # Trás (y=1)
            [2, 3, 7], [2, 7, 6],
            # Esquerda (x=0)
            [0, 4, 7], [0, 7, 3],
            # Direita (x=2)
            [1, 6, 5], [1, 2, 6],
        ]

        res = MassPropertiesCenterOfGravityEngine.calculate_mesh_properties(
            v, t, material_type="madeira_eucalipto"
        )
        self.assertEqual(res["entity_type"], "MassPropertiesReport")
        self.assertAlmostEqual(res["volume_m3"], 1.0, places=2)
        # Centro de Gravidade esperado: (1.0, 0.5, 0.25)
        self.assertAlmostEqual(res["center_of_gravity"][0], 1.0, places=2)
        self.assertAlmostEqual(res["center_of_gravity"][1], 0.5, places=2)
        self.assertAlmostEqual(res["center_of_gravity"][2], 0.25, places=2)
        # Madeira Eucalipto = 650 kg/m³ -> Massa = 650 kg
        self.assertAlmostEqual(res["total_mass_kg"], 650.0, places=1)

    async def test_controller_layers_frentes_86_a_90(self):
        from app.repositories.skp_engine_repository import SkpEngineRepository
        from app.services.scene_service import SceneService
        from app.controllers.scene_controller import SceneController
        from app.schemas.scene import (
            SubDSubdivisionRequest,
            SectionDimensionRequest,
            PanoramaSphericalRequest,
            ClashDetectionRequest,
            MassPropertiesRequest,
        )

        repo = SkpEngineRepository()
        service = SceneService(repository=repo)
        controller = SceneController(service=service)

        # 86. Controller SubD
        req_86 = SubDSubdivisionRequest(
            vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]],
            faces=[[0, 1, 2, 3]],
            iterations=1
        )
        res_86 = await controller.subdivide_quad_mesh(req_86)
        self.assertEqual(res_86.entity_type, "SubDMeshResult")
        self.assertEqual(res_86.subdivided_quad_faces_count, 4)

        # 87. Controller Section Dimension
        req_87 = SectionDimensionRequest(
            cut_loops_3d=[[[0.0, 0.0, 0.0], [3.0, 0.0, 0.0], [3.0, 0.0, 2.0], [0.0, 0.0, 2.0]]],
            offset_m=0.2
        )
        res_87 = await controller.generate_auto_section_dimensions(req_87)
        self.assertEqual(res_87.entity_type, "SectionDimensionResult")
        self.assertEqual(res_87.span_horizontal_m, 3.0)

        # 88. Controller Panorama
        req_88 = PanoramaSphericalRequest(
            eye_position=[0.0, 0.0, 1.7],
            horizontal_samples=8,
            vertical_samples=4
        )
        res_88 = await controller.calculate_spherical_panorama(req_88)
        self.assertEqual(res_88.cubemap["faces_count"], 6)

        # 89. Controller Clash Detection
        req_89 = ClashDetectionRequest(
            components=[
                {"id": "c1", "name": "A", "bbox_min": [0.0, 0.0, 0.0], "bbox_max": [1.0, 1.0, 1.0]},
                {"id": "c2", "name": "B", "bbox_min": [0.5, 0.5, 0.5], "bbox_max": [1.5, 1.5, 1.5]},
            ],
            clearance_tolerance_m=0.01
        )
        res_89 = await controller.detect_component_clashes(req_89)
        self.assertEqual(res_89.hard_clashes_count, 1)

        # 90. Controller Mass Properties
        req_90 = MassPropertiesRequest(
            vertices=[
                [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0], [0.0, 1.0, 1.0],
            ],
            triangles=[
                [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
                [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
                [0, 4, 7], [0, 7, 3], [1, 6, 5], [1, 2, 6],
            ],
            material_type="aco"
        )
        res_90 = await controller.calculate_mesh_mass_properties(req_90)
        self.assertEqual(res_90.entity_type, "MassPropertiesReport")
        self.assertAlmostEqual(res_90.total_mass_kg, 7850.0, places=1)


if __name__ == "__main__":
    unittest.main()
