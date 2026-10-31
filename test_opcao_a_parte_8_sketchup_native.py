"""
Testes Unitários Automatizados - Opção A (Parte 8): Ferramentas Nativas Oficiais do SketchUp Desktop.

Valida a engenharia reversa das 7 ferramentas e motores em Zero DLL / Pure Python:
1. LeaderTextCalloutEngine: Rótulos de chamada (Leader Text) e cálculo automático de área de face 3D.
2. FromContoursSandboxEngine: Reconstrução de malha TIN a partir de curvas de nível (Sandbox - From Contours).
3. SolidInspectorEngine: Auditoria de sólidos 2-manifold, furos, arestas internas e volume fechado m³.
4. ConstructionGuideEngine: Linhas guias infinitas paralelas, guias angulares e interseção para snap.
5. AlignedDimensionEngine: Cotas lineares alinhadas e ortogonais projetadas em X/Y/Z com linhas testemunhas.
6. RadialArcDimensionEngine: Cotas de raio (R), diâmetro (Ø) e comprimento de arco de curva.
7. SoftSmoothAngleEngine: Suavização angular com ângulo diédrico limite e normais contínuas de Phong.
8. Integração assíncrona de ponta a ponta com SceneController.
"""

import asyncio
import unittest

from core.leader_text_callout_engine import LeaderTextCalloutEngine
from core.from_contours_sandbox_engine import FromContoursSandboxEngine
from core.solid_inspector_engine import SolidInspectorEngine
from core.construction_guide_engine import ConstructionGuideEngine
from core.aligned_dimension_engine import AlignedDimensionEngine
from core.radial_arc_dimension_engine import RadialArcDimensionEngine
from core.soft_smooth_angle_engine import SoftSmoothAngleEngine

from app.controllers.scene_controller import SceneController
from app.services.scene_service import SceneService
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.schemas.scene import (
    LeaderTextCalloutRequest,
    FromContoursRequest,
    SolidInspectorRequest,
    ConstructionGuideRequest,
    AlignedDimensionRequest,
    RadialArcDimensionRequest,
    SoftSmoothAngleRequest,
)


class TestOpcaoAParte8SketchupNative(unittest.TestCase):
    """Suíte de testes das ferramentas oficiais nativas do SketchUp Desktop (Opção A - Parte 8)."""

    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    def test_01_leader_text_callout_engine(self):
        """Testa cálculo de área 3D Shoelace e anotação com linha líder dobrada."""
        # Retângulo 3x4 no plano XY -> Área 12 m²
        face_pts = [
            (0.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (3.0, 4.0, 0.0),
            (0.0, 4.0, 0.0),
        ]
        area = LeaderTextCalloutEngine.calculate_polygon_area_3d(face_pts)
        self.assertAlmostEqual(area, 12.0, places=2)

        centroid = LeaderTextCalloutEngine.calculate_face_centroid(face_pts)
        self.assertEqual(centroid, (1.5, 2.0, 0.0))

        callout = LeaderTextCalloutEngine.create_face_area_callout(face_pts)
        self.assertEqual(callout["entity_type"], "SUTextRef")
        self.assertIn("12.00 m²", callout["text"])
        self.assertTrue(callout["is_leader"])
        self.assertEqual(len(callout["leader_segments"]), 2)  # Cotovelo BENT

    def test_02_from_contours_sandbox_engine(self):
        """Testa triangulação ótima entre curvas de nível de altimetria."""
        # Curva 1: Z=0.0m
        c1 = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (4.0, 0.0, 0.0)]
        # Curva 2: Z=1.5m
        c2 = [(0.0, 2.0, 1.5), (2.0, 2.0, 1.5), (4.0, 2.0, 1.5)]
        # Curva 3: Z=3.0m
        c3 = [(0.0, 4.0, 3.0), (2.0, 4.0, 3.0), (4.0, 4.0, 3.0)]

        res = FromContoursSandboxEngine.generate_terrain_from_contours([c1, c2, c3])
        self.assertEqual(res["entity_type"], "SUGeometryInput")
        self.assertEqual(res["total_contours"], 3)
        self.assertEqual(res["min_elevation_m"], 0.0)
        self.assertEqual(res["max_elevation_m"], 3.0)
        self.assertEqual(res["elevation_delta_m"], 3.0)
        self.assertGreater(res["total_triangles"], 4)
        self.assertGreater(res["terrain_surface_area_m2"], 10.0)

    def test_03_solid_inspector_engine(self):
        """Testa auditoria 2-manifold estrita, bordas abertas e volume fechado."""
        # 1. Cubo Fechado 1x1x1m (Sólido Manifold Perfeito)
        cube_verts = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
            (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
        ]
        cube_tris = [
            (0, 1, 2), (0, 2, 3),  # base
            (4, 6, 5), (4, 7, 6),  # topo
            (0, 4, 5), (0, 5, 1),  # frente
            (1, 5, 6), (1, 6, 2),  # direita
            (2, 6, 7), (2, 7, 3),  # tras
            (3, 7, 4), (3, 4, 0),  # esquerda
        ]
        insp_solid = SolidInspectorEngine.inspect_mesh(cube_verts, cube_tris)
        self.assertTrue(insp_solid["is_solid"])
        self.assertEqual(insp_solid["open_boundary_edges_count"], 0)
        self.assertEqual(insp_solid["internal_edges_count"], 0)
        self.assertAlmostEqual(insp_solid["volume_m3"], 1.0, places=2)
        self.assertTrue(insp_solid["solid_tools_ready"])

        # 2. Malha Aberta (Cubo sem a tampa do topo -> 4 arestas abertas)
        open_tris = cube_tris[:-2]  # remove faces
        insp_open = SolidInspectorEngine.inspect_mesh(cube_verts, open_tris)
        self.assertFalse(insp_open["is_solid"])
        self.assertGreater(insp_open["open_boundary_edges_count"], 0)

    def test_04_construction_guide_engine(self):
        """Testa linhas guias infinitas paralelas, angulares e snap de interseção."""
        # Guia paralela ao eixo X
        p1 = (0.0, 0.0, 0.0)
        p2 = (5.0, 0.0, 0.0)
        guide_par = ConstructionGuideEngine.create_parallel_guide(p1, p2, offset_distance=1.0)
        self.assertEqual(guide_par["entity_type"], "SUGuideLineRef")
        self.assertTrue(guide_par["is_infinite"])
        self.assertAlmostEqual(guide_par["offset_distance_m"], 1.0)

        # Guia angular a 90 graus
        guide_ang = ConstructionGuideEngine.create_angular_guide((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), angle_deg=90.0)
        self.assertAlmostEqual(guide_ang["direction"][1], 1.0, places=3)

        # Interseção entre guia Y=1.0 e guia X=2.0
        # Guia 1: passa por (0, 1, 0) na direção X (1, 0, 0)
        # Guia 2: passa por (2, 0, 0) na direção Y (0, 1, 0)
        inter = ConstructionGuideEngine.calculate_guide_intersection(
            p1=(0.0, 1.0, 0.0), d1=(1.0, 0.0, 0.0),
            p2=(2.0, 0.0, 0.0), d2=(0.0, 1.0, 0.0),
        )
        self.assertIsNotNone(inter)
        self.assertTrue(inter["intersecting"])
        self.assertEqual(inter["point"], [2.0, 1.0, 0.0])

    def test_05_aligned_dimension_engine(self):
        """Testa cotas lineares alinhadas e ortogonais rotacionadas."""
        # Cota alinhada de (0,0,0) a (3,4,0) -> Distância 5.0m
        dim_al = AlignedDimensionEngine.create_aligned_dimension((0.0, 0.0, 0.0), (3.0, 4.0, 0.0), offset_distance=0.2)
        self.assertEqual(dim_al["entity_type"], "SUDimensionLinearRef")
        self.assertEqual(dim_al["dimension_type"], "ALIGNED")
        self.assertAlmostEqual(dim_al["distance_m"], 5.0, places=2)
        self.assertEqual(len(dim_al["witness_lines"]), 2)

        # Cota rotacionada no eixo X de (0,0,0) a (3,4,0) -> Projeção X = 3.0m
        dim_rot = AlignedDimensionEngine.create_rotated_dimension((0.0, 0.0, 0.0), (3.0, 4.0, 0.0), axis="X")
        self.assertEqual(dim_rot["dimension_type"], "ROTATED")
        self.assertEqual(dim_rot["axis"], "X")
        self.assertAlmostEqual(dim_rot["distance_m"], 3.0, places=2)

    def test_06_radial_arc_dimension_engine(self):
        """Testa cotas de raio, diâmetro e comprimento de arco."""
        center = (0.0, 0.0, 0.0)
        radius = 2.5

        # Cota de Raio
        dim_r = RadialArcDimensionEngine.create_radial_dimension(center, radius, is_diameter=False)
        self.assertEqual(dim_r["dimension_type"], "RADIUS")
        self.assertIn("R 2.50 m", dim_r["formatted_text"])

        # Cota de Diâmetro
        dim_d = RadialArcDimensionEngine.create_radial_dimension(center, radius, is_diameter=True)
        self.assertEqual(dim_d["dimension_type"], "DIAMETER")
        self.assertIn("Ø 5.00 m", dim_d["formatted_text"])

        # Comprimento de Arco de 90° com raio 2.0m: s = r * pi/2 = 3.1416m
        dim_arc = RadialArcDimensionEngine.create_arc_length_dimension(center, radius=2.0, start_angle_deg=0.0, end_angle_deg=90.0)
        self.assertEqual(dim_arc["dimension_type"], "ARC_LENGTH")
        self.assertAlmostEqual(dim_arc["arc_length_m"], 3.1416, places=2)

    def test_07_soft_smooth_angle_engine(self):
        """Testa suavização angular diédrica e cálculo de normais por vértice."""
        # Dois triângulos coplanares formando um quadrado
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        tris = [(0, 1, 2), (0, 2, 3)]

        res = SoftSmoothAngleEngine.apply_soft_smooth(verts, tris, max_angle_deg=35.0, soften_coplanar=True)
        self.assertEqual(res["entity_type"], "SUSoftEdgeSettings")
        self.assertGreaterEqual(res["soft_edges_count"], 1)  # A aresta diagonal é coplanar
        self.assertEqual(len(res["vertex_normals"]), 4)
        for vn in res["vertex_normals"]:
            self.assertEqual(vn, [0.0, 0.0, 1.0])

    def test_08_async_controller_integration(self):
        """Testa a integração assíncrona ponta a ponta com SceneController."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_pipeline():
            # 1. Leader Text
            req_lt = LeaderTextCalloutRequest(
                face_vertices=[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [2.0, 2.0, 0.0], [0.0, 2.0, 0.0]]
            )
            res_lt = await self.controller.leader_text_callout_create(req_lt)
            self.assertEqual(res_lt.status, "success")
            self.assertIn("4.00 m²", res_lt.callout["text"])

            # 2. From Contours
            req_fc = FromContoursRequest(
                contour_curves=[
                    [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0]],
                    [[0.0, 2.0, 1.0], [2.0, 2.0, 1.0]]
                ]
            )
            res_fc = await self.controller.from_contours_sandbox_generate(req_fc)
            self.assertEqual(res_fc.status, "success")

            # 3. Solid Inspector
            req_si = SolidInspectorRequest(
                vertices=[[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]],
                triangles=[[0, 1, 2], [0, 2, 3], [4, 6, 5], [4, 7, 6], [0, 4, 5], [0, 5, 1], [1, 5, 6], [1, 6, 2], [2, 6, 7], [2, 7, 3], [3, 7, 4], [3, 4, 0]]
            )
            res_si = await self.controller.solid_inspector_check(req_si)
            self.assertTrue(res_si.inspection["is_solid"])

            # 4. Construction Guide
            req_cg = ConstructionGuideRequest(guide_type="parallel", offset_distance=1.5)
            res_cg = await self.controller.construction_guide_create(req_cg)
            self.assertEqual(res_cg.status, "success")

            # 5. Aligned Dimension
            req_ad = AlignedDimensionRequest(start_point=[0, 0, 0], end_point=[3, 4, 0], mode="aligned")
            res_ad = await self.controller.aligned_dimension_create(req_ad)
            self.assertEqual(res_ad.dimension["distance_m"], 5.0)

            # 6. Radial Dimension
            req_rd = RadialArcDimensionRequest(center=[0, 0, 0], radius=1.8, mode="radius")
            res_rd = await self.controller.radial_arc_dimension_create(req_rd)
            self.assertEqual(res_rd.dimension["measured_value_m"], 1.8)

            # 7. Soft Smooth Angle
            req_ss = SoftSmoothAngleRequest(
                vertices=[[0, 0, 0], [1, 0, 0], [1, 1, 0]],
                triangles=[[0, 1, 2]],
                max_angle_deg=35.0
            )
            res_ss = await self.controller.soft_smooth_angle_apply(req_ss)
            self.assertEqual(res_ss.status, "success")

        loop.run_until_complete(run_pipeline())
        loop.close()


if __name__ == "__main__":
    unittest.main()
