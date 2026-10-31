"""
Testes de Integracao e Regressao para as Frentes 61 a 65 (Engenharia Reversa SketchUp - Zero DLL).

- Frente 61: Dicionários de Atributos e Componentes Dinâmicos (Attribute Dictionaries)
- Frente 62: Pastas de Tags e Hierarquia de Camadas (TagFolder no model.dat)
- Frente 63: Motor de Estilos de Arestas Nativos (Profiles, Depth Cue, Extensions, Back Edges K)
- Frente 64: Câmera com Perspectiva de 2 Pontos (Two-Point Perspective / Tilt-Shift)
- Frente 65: Projeção de Texturas & Mapeamento UV Cilíndrico/Planar em B-Rep Curvo
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    AttributeDictionaryRequest,
    TagFolderRequest,
    EdgeStylesRequest,
    TwoPointPerspectiveRequest,
    TextureProjectionRequest,
)


class TestFrentes61a65(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_frente_61_attribute_dictionary(self):
        """Valida dicionários de atributos nativos e componentes dinâmicos (Frente 61)."""
        req = AttributeDictionaryRequest(
            dict_name="dynamic_attributes",
            key="_lenx_formula",
            value="=BaseWidth * 2 + 10",
            evaluate_formula=True,
            context_vars={"BaseWidth": 120.0}
        )
        res = await self.controller.manage_attribute_dictionary(req)
        self.assertEqual(res.entity_type, "AttributeDictionaryResult")
        self.assertEqual(res.dict_name, "dynamic_attributes")
        self.assertEqual(res.key, "_lenx_formula")
        self.assertEqual(res.evaluated_result, 250.0)  # 120 * 2 + 10 = 250
        print(f"[Frente 61] Attribute Dictionary: {res.dict_name}['{res.key}'] = {res.value} -> Avaliado: {res.evaluated_result}")

    async def test_02_frente_62_tag_folder(self):
        """Valida pastas de tags e herança de visibilidade em cascata (Frente 62)."""
        # Cria pasta "Estrutura" e move tags para dentro
        req = TagFolderRequest(
            folder_id="folder_estrutural",
            name="Estrutura de Madeira",
            parent_id=None,
            visible=True,
            tags_to_add=["Pilares", "Vigas", "Decks"]
        )
        res = await self.controller.manage_tag_folder(req)
        self.assertEqual(res.entity_type, "TagFolderHierarchy")
        self.assertEqual(res.folder_id, "folder_estrutural")
        self.assertEqual(res.tags_count, 3)
        self.assertTrue(res.visible)
        self.assertIn("folders", res.tree_summary)
        print(f"[Frente 62] Tag Folder criada: {res.name} ({res.tags_count} tags aninhadas)")

    async def test_03_frente_63_edge_styles(self):
        """Valida motor de estilos de arestas nativos do SketchUp e atalho K (Frente 63)."""
        req = EdgeStylesRequest(
            profiles_enabled=True,
            profile_width=3,
            depth_cue_enabled=True,
            extensions_enabled=True,
            extension_length_px=6,
            endpoints_enabled=True,
            endpoint_size_px=5,
            back_edges_enabled=True  # Atalho K
        )
        res = await self.controller.configure_edge_styles(req)
        self.assertEqual(res.entity_type, "EdgeStylesConfiguration")
        self.assertTrue(res.back_edges_shortcut_active)
        self.assertEqual(res.settings["profile_width"], 3)
        self.assertTrue(res.settings["extensions_enabled"])
        print(f"[Frente 63] Edge Styles: Profiles={res.settings['profiles_enabled']} ({res.settings['profile_width']}px), BackEdges(K)={res.back_edges_shortcut_active}")

    async def test_04_frente_64_two_point_perspective(self):
        """Valida câmera com perspectiva de 2 pontos e paralelismo vertical (Frente 64)."""
        # Câmera olhando para cima (eye Z=1.5, target Z=4.0)
        req = TwoPointPerspectiveRequest(
            eye=[10.0, -10.0, 1.5],
            target=[0.0, 0.0, 4.0],
            fov_deg=35.0,
            aspect_ratio=1.777
        )
        res = await self.controller.calculate_two_point_perspective(req)
        self.assertEqual(res.entity_type, "TwoPointPerspectiveCamera")
        self.assertTrue(res.vertical_lines_parallel)
        # O alvo corrigido deve ter a mesma cota Z do olho para eliminar convergência vertical
        self.assertEqual(res.corrected_target[2], req.eye[2])
        self.assertNotEqual(res.lens_shift_y, 0.0)
        self.assertEqual(len(res.projection_matrix_16), 16)
        print(f"[Frente 64] Two-Point Perspective: Pitch corrigido de {res.original_pitch_deg} deg com Lens Shift={res.lens_shift_y} (Linhas verticais estritamente paralelas)")

    async def test_05_frente_65_texture_projection(self):
        """Valida motor analítico de projeção UV planar e cilíndrica (Frente 65)."""
        # 1. Teste de Projeção Planar
        verts_planar = [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [2.0, 2.0, 0.0], [0.0, 2.0, 0.0]]
        req_planar = TextureProjectionRequest(
            vertices=verts_planar,
            projection_type="planar",
            plane_normal=[0.0, 0.0, 1.0],
            scale_u_m=1.0,
            scale_v_m=1.0
        )
        res_planar = await self.controller.project_texture_uv(req_planar)
        self.assertEqual(res_planar.projection_type, "planar")
        self.assertEqual(len(res_planar.uv_coordinates), 4)
        self.assertEqual(res_planar.uv_coordinates[0], [0.0, 0.0])
        self.assertEqual(res_planar.uv_coordinates[2], [2.0, 2.0])

        # 2. Teste de Projeção Cilíndrica (para toras redondas)
        verts_cyl = [[1.0, 0.0, 0.0], [0.0, 1.0, 1.0], [-1.0, 0.0, 2.0]]
        req_cyl = TextureProjectionRequest(
            vertices=verts_cyl,
            projection_type="cylindrical",
            scale_v_m=2.0
        )
        res_cyl = await self.controller.project_texture_uv(req_cyl)
        self.assertEqual(res_cyl.projection_type, "cylindrical")
        self.assertEqual(len(res_cyl.uv_coordinates), 3)
        self.assertAlmostEqual(res_cyl.uv_coordinates[0][0], 0.0, places=2)  # Ângulo 0
        self.assertAlmostEqual(res_cyl.uv_coordinates[1][0], 0.25, places=2)  # Ângulo 90 graus (pi/2)
        print(f"[Frente 65] Projecao UV: Planar ({len(res_planar.uv_coordinates)} pts) e Cilindrica ({len(res_cyl.uv_coordinates)} pts) calculadas com sucesso")


if __name__ == "__main__":
    unittest.main()
