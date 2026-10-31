"""
Testes Unitários Automatizados - Opção A (Parte 7): Ferramentas Nativas Oficiais do SketchUp Desktop.

Valida a engenharia reversa das 7 ferramentas e motores em Zero DLL / Pure Python:
1. AttributeDictionaryEngine: Dicionários de atributos e componentes dinâmicos (dynamic_attributes).
2. EdgeStylesEngine: Estilos de arestas oficiais (Profiles, Back Edges atalho K, Depth Cue).
3. TagFolderEngine: Pastas de etiquetas hierárquicas (Tag Folders) e visibilidade em cascata.
4. TextureProjectionEngine: Projeção UV analítica planar e cilíndrica.
5. TwoPointPerspectiveEngine: Câmera perspectiva de dois pontos com Lens Shift e linhas verticais estritamente paralelas.
6. FlipAlongAxesEngine: Inversão ao longo dos eixos (Flip Along Red/Green/Blue) com Householder e winding invertido.
7. WeldEdgesEngine: Soldagem de arestas em curvas contínuas (Weld Edges / SUCurveRef).
8. Integração ponta-a-ponta assíncrona com SceneController.
"""

import asyncio
import unittest

from core.attribute_dictionary_engine import AttributeDictionaryEngine
from core.edge_styles_engine import EdgeStylesEngine
from core.tag_folder_engine import TagFolderEngine
from core.texture_projection_engine import TextureProjectionEngine
from core.two_point_perspective_engine import TwoPointPerspectiveEngine
from core.flip_along_axes_engine import FlipAlongAxesEngine
from core.weld_edges_engine import WeldEdgesEngine

from app.controllers.scene_controller import SceneController
from app.services.scene_service import SceneService
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.schemas.scene import (
    AttributeDictionaryRequest,
    TagFolderRequest,
    EdgeStylesRequest,
    TwoPointPerspectiveRequest,
    TextureProjectionRequest,
    CurveWeldRequest,
    FlipAlongRequest,
)


class TestOpcaoAParte7SketchupNative(unittest.TestCase):
    """Suíte de testes das ferramentas oficiais nativas do SketchUp Desktop (Opção A - Parte 7)."""

    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    def test_01_attribute_dictionary_engine(self):
        """Testa criação, leitura e avaliação de fórmulas em Attribute Dictionaries nativos."""
        dicts = {}
        # 1. Criação e manipulação básica
        d = AttributeDictionaryEngine.set_attribute(dicts, "custom_meta", "author", "Fernando")
        self.assertEqual(d["attributes"]["author"], "Fernando")
        self.assertEqual(AttributeDictionaryEngine.get_attribute(dicts, "custom_meta", "author"), "Fernando")
        self.assertIsNone(AttributeDictionaryEngine.get_attribute(dicts, "custom_meta", "non_existent"))

        # 2. Componente Dinâmico Trimble (dynamic_attributes)
        dc = AttributeDictionaryEngine.configure_dynamic_component(
            dicts,
            lenx_cm=150.0,
            leny_cm=80.0,
            lenz_cm=210.0,
            formulas={"LenX": "=BaseWidth * 2 + 10"},
            onclick_action="ANIMATE('RotZ', 0, 90)",
            description="Porta de Giro Dinâmica"
        )
        self.assertEqual(dc["name"], "dynamic_attributes")
        self.assertEqual(dc["attributes"]["lenx"], 150.0)
        self.assertEqual(dc["attributes"]["_lenx_formula"], "=BaseWidth * 2 + 10")
        self.assertEqual(dc["attributes"]["onclick"], "ANIMATE('RotZ', 0, 90)")

        # 3. Avaliação de fórmula dinâmica
        res = AttributeDictionaryEngine.evaluate_dynamic_formula("=BaseWidth * 2 + 10", {"basewidth": 120.0})
        self.assertEqual(res, 250.0)

    def test_02_edge_styles_engine(self):
        """Testa classificação e estilos de arestas nativos (Profiles, Back Edges K, Depth Cue)."""
        engine = EdgeStylesEngine()
        settings = engine.settings
        self.assertTrue(settings["edges_enabled"])
        self.assertTrue(settings["profiles_enabled"])
        self.assertFalse(settings["back_edges_enabled"])

        # Alternância de atalho K (Back Edges)
        back_active = engine.toggle_back_edges()
        self.assertTrue(back_active)
        self.assertTrue(engine.settings["back_edges_enabled"])

        # Classificação de arestas em silhuetas e normais
        sample_edges = [
            # Aresta com 1 face = perfil de borda livre
            {"start": [0, 0, 0], "end": [1, 0, 0], "face_normals": [[0, 0, 1]]},
            # Aresta com 2 faces compartilhadas formando silhueta (uma vira pra câmera, outra não)
            {"start": [1, 0, 0], "end": [1, 1, 0], "face_normals": [[0, -1, 0], [1, 0, 0]]},
            # Aresta interna coplanar
            {"start": [0, 1, 0], "end": [1, 1, 0], "face_normals": [[0, 0, 1], [0, 0, 1]]},
        ]
        classified = engine.classify_edges(sample_edges, camera_direction=(0.0, -1.0, 0.0))
        self.assertGreaterEqual(classified["profiles_count"], 1)
        self.assertGreaterEqual(classified["back_edges_count"], 1)

    def test_03_tag_folder_engine(self):
        """Testa hierarquia de Tag Folders e resolução de visibilidade em cascata."""
        engine = TagFolderEngine()

        # Criação de pasta pai e pasta filha
        parent_folder = engine.create_folder("f_arch", "Arquitetura", parent_id=None, visible=True)
        child_folder = engine.create_folder("f_doors", "Esquadrias", parent_id="f_arch", visible=True)
        self.assertEqual(parent_folder["name"], "Arquitetura")
        self.assertEqual(child_folder["parent_id"], "f_arch")

        # Registro e movimentação de tag para dentro da pasta filha
        engine.add_tag("Portas de Madeira", color_hex="#8B4513")
        engine.move_tag_to_folder("Portas de Madeira", "f_doors")

        # Inicialmente visível
        self.assertTrue(engine.is_tag_effectively_visible("Portas de Madeira"))

        # Oculta pasta pai -> visibilidade em cascata deve ocultar tag filha
        engine.set_folder_visibility("f_arch", False)
        self.assertFalse(engine.is_tag_effectively_visible("Portas de Madeira"))

        # Reexibe pasta pai
        engine.set_folder_visibility("f_arch", True)
        self.assertTrue(engine.is_tag_effectively_visible("Portas de Madeira"))

    def test_04_texture_projection_engine(self):
        """Testa projeção analítica UV planar e cilíndrica."""
        # 1. Projeção Planar
        verts = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 3.0, 0.0), (0.0, 3.0, 0.0)]
        planar_uvs = TextureProjectionEngine.project_planar_uv(
            verts, plane_normal=(0.0, 0.0, 1.0), scale_u_m=1.0, scale_v_m=1.0
        )
        self.assertEqual(len(planar_uvs), 4)
        self.assertEqual(planar_uvs[0], (0.0, 0.0))
        self.assertEqual(planar_uvs[1], (2.0, 0.0))
        self.assertEqual(planar_uvs[2], (2.0, 3.0))

        # 2. Projeção Cilíndrica
        cyl_verts = [(1.0, 0.0, 0.0), (0.0, 1.0, 1.0), (-1.0, 0.0, 2.0)]
        cyl_uvs = TextureProjectionEngine.project_cylindrical_uv(
            cyl_verts, cylinder_center=(0.0, 0.0), cylinder_height_m=2.0
        )
        self.assertEqual(len(cyl_uvs), 3)
        self.assertAlmostEqual(cyl_uvs[0][0], 0.0, places=2)
        self.assertAlmostEqual(cyl_uvs[0][1], 0.0, places=2)
        self.assertAlmostEqual(cyl_uvs[2][1], 1.0, places=2)  # Z = 2.0m com altura 2.0m

    def test_05_two_point_perspective_engine(self):
        """Testa cálculo de perspectiva arquitetônica de 2 pontos (Tilt-Shift / Lens Shift)."""
        eye = (10.0, -10.0, 5.0)
        target = (0.0, 0.0, 1.0)  # Câmera inclinada para baixo
        res = TwoPointPerspectiveEngine.calculate_two_point_camera(eye, target, fov_deg=35.0)

        self.assertEqual(res["camera_type"], "TwoPointPerspective")
        self.assertTrue(res["vertical_lines_parallel"])
        # Alvo corrigido deve ter a mesma cota Z do olho (5.0m) para manter plano de visada horizontal
        self.assertEqual(res["corrected_target"][2], 5.0)
        self.assertEqual(len(res["projection_matrix_16"]), 16)
        self.assertNotEqual(res["lens_shift_y"], 0.0)

    def test_06_flip_along_axes_engine(self):
        """Testa inversão ao longo de eixos ortogonais com inversão de winding order."""
        verts = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 1.0, 0.0), (0.0, 1.0, 0.0)]
        indices = [0, 1, 2, 0, 2, 3]

        res = FlipAlongAxesEngine.flip_along(verts, indices, axis="red")
        self.assertEqual(res["axis"], "red")
        self.assertEqual(res["total_vertices"], 4)
        self.assertEqual(res["total_triangles"], 2)
        self.assertTrue(res["is_winding_inverted"])

        # O primeiro triângulo (0, 1, 2) deve ter invertido para (0, 2, 1)
        self.assertEqual(res["indices"][:3], [0, 2, 1])
        # Vértices em X devem ter sido refletidos em torno do centro cx = 1.0
        # V0 (x=0) -> x' = 2.0
        # V1 (x=2) -> x' = 0.0
        self.assertAlmostEqual(res["vertices"][0][0], 2.0, places=4)
        self.assertAlmostEqual(res["vertices"][1][0], 0.0, places=4)

    def test_07_weld_edges_engine(self):
        """Testa soldagem de arestas contíguas em curvas contínuas (Weld Edges / SUCurveRef)."""
        edges = [
            {"start": (0.0, 0.0, 0.0), "end": (1.0, 0.0, 0.0)},
            {"start": (1.0, 0.0, 0.0), "end": (2.0, 1.0, 0.0)},
            {"start": (2.0, 1.0, 0.0), "end": (3.0, 1.0, 0.0)},
        ]
        res = WeldEdgesEngine.weld_edges(edges)
        self.assertEqual(res["total_curves"], 1)
        self.assertEqual(res["total_edges"], 3)
        self.assertAlmostEqual(res["total_length_m"], 1.0 + 1.4142 + 1.0, places=2)

        curve = res["curves"][0]
        self.assertEqual(curve["entity_type"], "SUCurveRef")
        self.assertEqual(curve["curve_type"], "OpenCurve")
        self.assertEqual(curve["vertex_count"], 4)
        self.assertEqual(len(curve["deflection_angles_deg"]), 2)

    def test_08_scene_controller_async_endpoints(self):
        """Testa os endpoints assíncronos do SceneController para todas as 7 ferramentas."""
        async def run_checks():
            # 1. Attribute Dictionary
            req_attr = AttributeDictionaryRequest(
                dict_name="dynamic_attributes",
                key="_lenx_formula",
                value="=Base * 2",
                evaluate_formula=True,
                context_vars={"base": 50.0}
            )
            res_attr = await self.controller.manage_attribute_dictionary(req_attr)
            self.assertEqual(res_attr.evaluated_result, 100.0)

            # 2. Tag Folder
            req_folder = TagFolderRequest(folder_id="f_estrutural", name="Estrutural", visible=True)
            res_folder = await self.controller.manage_tag_folder(req_folder)
            self.assertEqual(res_folder.name, "Estrutural")

            # 3. Edge Styles
            req_edges = EdgeStylesRequest(profiles_enabled=True, back_edges_enabled=True)
            res_edges = await self.controller.configure_edge_styles(req_edges)
            self.assertTrue(res_edges.settings["back_edges_enabled"])

            # 4. Two Point Perspective
            req_cam = TwoPointPerspectiveRequest(eye=[10.0, -10.0, 6.0], target=[0.0, 0.0, 0.0], fov_deg=35.0)
            res_cam = await self.controller.calculate_two_point_perspective(req_cam)
            self.assertEqual(res_cam.corrected_target[2], 6.0)

            # 5. Texture Projection UV
            req_uv = TextureProjectionRequest(
                vertices=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0]],
                projection_type="planar",
                plane_normal=[0.0, 0.0, 1.0]
            )
            res_uv = await self.controller.project_texture_uv(req_uv)
            self.assertEqual(len(res_uv.uv_coordinates), 3)

            # 6. Weld Edges
            req_weld = CurveWeldRequest(
                edges=[
                    [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                    [[1.0, 0.0, 0.0], [2.0, 0.0, 0.0]]
                ]
            )
            res_weld = await self.controller.weld_curve_edges(req_weld)
            self.assertEqual(res_weld.curve_data["total_chains"], 1)

            # 7. Flip Along Axes
            req_flip = FlipAlongRequest(
                vertices=[[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [2.0, 2.0, 0.0]],
                indices=[0, 1, 2],
                axis="green"
            )
            res_flip = await self.controller.flip_along_axes(req_flip)
            self.assertEqual(res_flip.flip["axis"], "green")
            self.assertEqual(res_flip.flip["indices"], [0, 2, 1])

        asyncio.run(run_checks())


if __name__ == "__main__":
    unittest.main()
