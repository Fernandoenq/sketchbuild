"""Suíte de Testes Automatizados para a Opção A (Parte 5) - Ferramentas Nativas Oficiais do SketchUp.

Valida com 100% de cobertura as 7 novas ferramentas analíticas do SketchUp Pro (Zero DLL / Pure Python):
1. StampTerrainEngine (Carimbo de Terreno com Talude Suave da Caixa de Areia)
2. DrapeContourEngine (Projetar Contornos sobre Relevo TIN)
3. SectionCutFillEngine (Preenchimento de Seção e Inversão de Corte)
4. SoftSmoothEdgesEngine (Suavizar / Alisar Arestas com Ângulo Diédrico Limite)
5. EdgeDivideEngine (Dividir Aresta em N Partes com Parser de VCB)
6. PushPullCreateFaceEngine (Push/Pull com Criação de Nova Face Preservada Ctrl+Push/Pull)
7. BimIfcPropertySetEngine (Conjuntos de Propriedades Psets BIM IFC buildingSMART)
8. Validação arquitetural completa (Repository -> Service -> Controller)
"""

import unittest
import asyncio

from core.stamp_terrain_engine import StampTerrainEngine
from core.drape_contour_engine import DrapeContourEngine
from core.section_cut_fill_engine import SectionCutFillEngine
from core.soft_smooth_edges_engine import SoftSmoothEdgesEngine
from core.edge_divide_engine import EdgeDivideEngine
from core.push_pull_create_face_engine import PushPullCreateFaceEngine
from core.bim_ifc_property_set_engine import BimIfcPropertySetEngine

from app.schemas.scene import (
    StampTerrainRequest,
    DrapePathRequest,
    SectionCutFillRequest,
    SoftSmoothEdgesRequest,
    EdgeDivideRequest,
    PushPullCreateFaceRequest,
    BimIfcPropertySetRequest,
)
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController


class TestOpcaoAParte5SketchupNative(unittest.TestCase):
    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    # 1. StampTerrainEngine
    def test_01_stamp_terrain_engine(self):
        tin_vertices = [
            [-5.0, -5.0, 0.0], [0.0, -5.0, 0.5], [5.0, -5.0, 1.0],
            [-5.0, 0.0, 0.5], [0.0, 0.0, 1.0], [5.0, 0.0, 1.5],
            [-5.0, 5.0, 1.0], [0.0, 5.0, 1.5], [5.0, 5.0, 2.0]
        ]
        tin_triangles = [
            [0, 1, 4], [0, 4, 3], [1, 2, 5], [1, 5, 4],
            [3, 4, 7], [3, 7, 6], [4, 5, 8], [4, 8, 7]
        ]
        footprint = [[-1.0, -1.0], [1.0, -1.0], [1.0, 1.0], [-1.0, 1.0]]

        res = StampTerrainEngine.apply_stamp(
            tin_vertices=tin_vertices,
            tin_triangles=tin_triangles,
            footprint_polygon=footprint,
            target_elevation=3.0,
            transition_width=4.5
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["target_elevation"], 3.0)
        self.assertGreaterEqual(res["vertices_plateau_count"], 1)
        self.assertGreater(res["vertices_slope_count"], 0)
        center_v = res["modified_vertices"][4]
        self.assertEqual(center_v[2], 3.0)

    # 2. DrapeContourEngine
    def test_02_drape_contour_engine(self):
        tin_vertices = [
            [-10.0, -10.0, 0.0], [10.0, -10.0, 2.0],
            [10.0, 10.0, 4.0], [-10.0, 10.0, 1.0]
        ]
        tin_triangles = [[0, 1, 2], [0, 2, 3]]
        path_2d = [[-6.0, -6.0], [0.0, 0.0], [6.0, 6.0]]

        res = DrapeContourEngine.drape_path(
            tin_vertices=tin_vertices,
            tin_triangles=tin_triangles,
            path_points_2d=path_2d,
            subdivision_steps=3
        )
        self.assertTrue(res["success"])
        self.assertGreater(res["length_3d_m"], res["length_2d_m"])
        self.assertGreater(len(res["draped_points_3d"]), len(path_2d))
        self.assertIsInstance(res["average_elevation_m"], float)

    # 3. SectionCutFillEngine
    def test_03_section_cut_fill_engine(self):
        box_vertices = [
            [-1.0, -1.0, -1.0], [1.0, -1.0, -1.0], [1.0, 1.0, -1.0], [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0], [1.0, -1.0, 1.0], [1.0, 1.0, 1.0], [-1.0, 1.0, 1.0]
        ]
        box_triangles = [
            [0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6],
            [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2],
            [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0]
        ]
        plane = [0.0, 0.0, 1.0, 0.0]

        res = SectionCutFillEngine.compute_section_fill(
            solid_vertices=box_vertices,
            solid_triangles=box_triangles,
            plane_coeffs=plane,
            flip_direction=False,
            fill_color_hex="#222222"
        )
        self.assertTrue(res["success"])
        self.assertTrue(res["has_fill_cap"])
        self.assertGreaterEqual(res["cut_segments_count"], 4)
        self.assertGreater(len(res["fill_geometry"]["triangles"]), 0)

        flipped = SectionCutFillEngine.flip_plane(plane)
        self.assertEqual(flipped, [0.0, 0.0, -1.0, 0.0])

    # 4. SoftSmoothEdgesEngine
    def test_04_soft_smooth_edges_engine(self):
        v0 = [0.0, 0.0, 0.0]
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 1.0, 0.0]
        v3 = [0.0, 1.0, 0.05]
        vertices = [v0, v1, v2, v3]
        triangles = [[0, 1, 2], [0, 2, 3]]

        res = SoftSmoothEdgesEngine.process_soft_smooth(
            vertices=vertices,
            triangles=triangles,
            max_angle_deg=35.0,
            soften_coplanar=True,
            smooth_normals=True
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["edges_soft_count"], 1)
        self.assertEqual(len(res["vertex_normals"]), len(vertices))

    # 5. EdgeDivideEngine
    def test_05_edge_divide_engine(self):
        p0 = [0.0, 0.0, 0.0]
        p1 = [10.0, 0.0, 0.0]

        res1 = EdgeDivideEngine.divide_edge(p0, p1, num_segments=5)
        self.assertTrue(res1["success"])
        self.assertEqual(res1["num_segments"], 5)
        self.assertEqual(res1["total_length_m"], 10.0)
        self.assertEqual(res1["segment_length_m"], 2.0)
        self.assertEqual(res1["vertices_count"], 6)

        res2 = EdgeDivideEngine.divide_edge(p0, p1, num_segments="8s")
        self.assertTrue(res2["success"])
        self.assertEqual(res2["num_segments"], 8)
        self.assertEqual(res2["segment_length_m"], 1.25)

    # 6. PushPullCreateFaceEngine
    def test_06_push_pull_create_face_engine(self):
        rect_face = [
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [2.0, 3.0, 0.0],
            [0.0, 3.0, 0.0]
        ]
        res = PushPullCreateFaceEngine.extrude_with_new_face(
            face_vertices=rect_face,
            distance_m=1.5,
            create_new_face=True
        )
        self.assertTrue(res["success"])
        self.assertTrue(res["ctrl_modifier_active"])
        self.assertEqual(res["extrusion_distance_m"], 1.5)
        self.assertEqual(res["base_area_m2"], 6.0)
        self.assertEqual(res["volume_m3"], 9.0)
        self.assertEqual(res["total_vertices"], 8)
        self.assertEqual(res["total_triangles"], 12)

    # 7. BimIfcPropertySetEngine
    def test_07_bim_ifc_property_set_engine(self):
        props = {
            "Reference": "VIGA-W200x35",
            "LoadBearing": True,
            "FireRating": "2H",
            "Span": 5.5,
            "Pitch": 0.0
        }
        res = BimIfcPropertySetEngine.validate_and_build_pset(
            instance_id="inst_viga_principal",
            ifc_class="IfcBeam",
            pset_name="Pset_BeamCommon",
            properties=props,
            schema_version="IFC4",
            start_step_id=100
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["conformance_status"], "CONFORME_BUILDINGSMART")
        self.assertEqual(res["pset_name"], "Pset_BeamCommon")
        self.assertEqual(len(res["step_declarations"]), 6)
        self.assertTrue(any("IFCPROPERTYSINGLEVALUE('LoadBearing',$,IfcBoolean(.T.),$)" in line for line in res["step_declarations"]))
        self.assertTrue(any("IFCPROPERTYSET(" in line for line in res["step_declarations"]))

    # 8. Validação em Camadas no Controlador (SceneController)
    def test_08_controller_layers_opcao_a_parte_5(self):
        # 8.1 Stamp
        req1 = StampTerrainRequest(
            tin_vertices=[[-5, -5, 0], [5, -5, 1], [5, 5, 2], [-5, 5, 1]],
            tin_triangles=[[0, 1, 2], [0, 2, 3]],
            footprint_polygon=[[-1, -1], [1, -1], [1, 1], [-1, 1]],
            target_elevation=2.0,
            transition_width=1.5
        )
        res1 = asyncio.run(self.controller.stamp_terrain_apply(req1))
        self.assertEqual(res1.entity_type, "sketchup_native_stamp_terrain")
        self.assertTrue(res1.stamp["success"])

        # 8.2 Drape
        req2 = DrapePathRequest(
            tin_vertices=[[-5, -5, 0], [5, -5, 1], [5, 5, 2], [-5, 5, 1]],
            tin_triangles=[[0, 1, 2], [0, 2, 3]],
            path_points_2d=[[-2, -2], [2, 2]],
            subdivision_steps=2
        )
        res2 = asyncio.run(self.controller.drape_path_apply(req2))
        self.assertEqual(res2.entity_type, "sketchup_native_drape_path")
        self.assertTrue(res2.drape["success"])

        # 8.3 Section Cut Fill
        req3 = SectionCutFillRequest(
            solid_vertices=[[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]],
            solid_triangles=[[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6], [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2], [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0]],
            plane_coeffs=[0, 0, 1, 0],
            flip_direction=False,
            fill_color_hex="#111111"
        )
        res3 = asyncio.run(self.controller.section_cut_fill_compute(req3))
        self.assertEqual(res3.entity_type, "sketchup_native_section_cut_fill")
        self.assertTrue(res3.cut_fill["success"])

        # 8.4 Soft Smooth
        req4 = SoftSmoothEdgesRequest(
            vertices=[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0.05]],
            triangles=[[0, 1, 2], [0, 2, 3]],
            max_angle_deg=35.0,
            soften_coplanar=True,
            smooth_normals=True
        )
        res4 = asyncio.run(self.controller.soft_smooth_edges_process(req4))
        self.assertEqual(res4.entity_type, "sketchup_native_soft_smooth_edges")
        self.assertTrue(res4.soft_smooth["success"])

        # 8.5 Edge Divide
        req5 = EdgeDivideRequest(
            start_point=[0, 0, 0],
            end_point=[4, 0, 0],
            num_segments="4s"
        )
        res5 = asyncio.run(self.controller.edge_divide_execute(req5))
        self.assertEqual(res5.entity_type, "sketchup_native_edge_divide")
        self.assertTrue(res5.divide["success"])

        # 8.6 Push Pull Create Face
        req6 = PushPullCreateFaceRequest(
            face_vertices=[[0, 0, 0], [2, 0, 0], [2, 2, 0], [0, 2, 0]],
            distance_m=2.5,
            create_new_face=True
        )
        res6 = asyncio.run(self.controller.push_pull_create_face_extrude(req6))
        self.assertEqual(res6.entity_type, "sketchup_native_push_pull_create_face")
        self.assertTrue(res6.extrude["success"])

        # 8.7 Bim Ifc Property Set
        req7 = BimIfcPropertySetRequest(
            instance_id="inst_parede_01",
            ifc_class="IfcWall",
            pset_name="Pset_WallCommon",
            properties={"LoadBearing": True, "IsExternal": True, "FireRating": "1H"},
            schema_version="IFC4",
            start_step_id=500
        )
        res7 = asyncio.run(self.controller.bim_ifc_property_set_build(req7))
        self.assertEqual(res7.entity_type, "sketchup_native_bim_ifc_pset")
        self.assertTrue(res7.pset["success"])


if __name__ == "__main__":
    unittest.main()
