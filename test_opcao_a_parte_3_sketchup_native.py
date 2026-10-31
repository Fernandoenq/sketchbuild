"""
Testes unitários automatizados para as Ferramentas Nativas Oficiais do SketchUp (Opção A - Parte 3).
Cobre todos os 7 novos motores em Pure Python (Zero DLL) e as camadas da arquitetura:
1. TexturePinMappingEngine (Posicionamento por 4 pinos: Vermelho, Verde, Azul, Amarelo)
2. ColorByTagEngine (Modo de visualização Colorir por Etiqueta / Color by Tag)
3. PurgeUnusedEngine (Eliminar não utilizados: componentes, materiais, tags)
4. MakeComponentBehaviorEngine (Criar Componente: Glue to, Cut Opening, Face-Me)
5. AdvancedSelectionEngine (Inverter seleção, Mesma Tag, Mesmo Material, Triplo Clique)
6. HiddenGeometryEngine (Geometria Oculta tracejada vs Objetos Ocultos fantasma)
7. ModelStatisticsEngine (Censo canônico de entidades e perfil de complexidade)
"""

import unittest
import asyncio

from core.texture_pin_mapping_engine import TexturePinMappingEngine
from core.color_by_tag_engine import ColorByTagEngine
from core.purge_unused_engine import PurgeUnusedEngine
from core.make_component_behavior_engine import MakeComponentBehaviorEngine
from core.advanced_selection_engine import AdvancedSelectionEngine
from core.hidden_geometry_engine import HiddenGeometryEngine
from core.model_statistics_engine import ModelStatisticsEngine

from app.schemas.scene import (
    TexturePinTransformRequest,
    ColorByTagApplyRequest,
    PurgeUnusedRequest,
    MakeComponentDefinitionRequest,
    AdvancedSelectionRequest,
    HiddenGeometryConfigRequest,
    ModelStatisticsRequest,
)
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController


class TestOpcaoAParte3SketchupNative(unittest.TestCase):
    """Suíte de testes para a terceira rodada de ferramentas nativas oficiais do SketchUp."""

    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    # 1. TexturePinMappingEngine
    def test_texture_pins_mapping(self):
        face_pts = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 1.0, 0.0), (0.0, 1.0, 0.0)]
        res = TexturePinMappingEngine.calculate_pin_transform(
            face_vertices=face_pts,
            red_pin_origin=(0.1, 0.1),
            green_pin_scale_rot=(2.0, 90.0),
            blue_pin_shear=5.0
        )
        self.assertIn("uv_coordinates", res)
        self.assertEqual(len(res["uv_coordinates"]), 4)
        self.assertAlmostEqual(res["pins_config"]["green_pin_scale"], 2.0)
        self.assertAlmostEqual(res["pins_config"]["green_pin_rotation_deg"], 90.0)

    # 2. ColorByTagEngine
    def test_color_by_tag_apply(self):
        tags = [{"name": "Estrutura", "color": "#E53E3E"}, {"name": "Paredes", "color": "#3182CE"}]
        instances = [{"id": "inst_1", "tag": "Estrutura"}, {"id": "inst_2", "tag": "Paredes"}]

        # Ativado
        res_on = ColorByTagEngine.apply_color_by_tag(tags, instances, enabled=True)
        self.assertTrue(res_on["color_by_tag_enabled"])
        self.assertEqual(res_on["instance_color_overrides"]["inst_1"]["override_color_hex"], "#E53E3E")
        self.assertEqual(res_on["instance_color_overrides"]["inst_2"]["override_color_hex"], "#3182CE")

        # Desativado
        res_off = ColorByTagEngine.apply_color_by_tag(tags, instances, enabled=False)
        self.assertFalse(res_off["color_by_tag_enabled"])
        self.assertIsNone(res_off["instance_color_overrides"]["inst_1"]["override_color_hex"])

    # 3. PurgeUnusedEngine
    def test_purge_unused(self):
        defs = [{"name": "Pilar Ativo"}, {"name": "Mesa Deletada"}]
        insts = [{"id": "1", "definition_name": "Pilar Ativo", "material": "Concreto", "tag": "Estrutura"}]
        mats = [{"name": "Concreto"}, {"name": "Tijolo Não Usado"}]
        tags = [{"name": "Layer0"}, {"name": "Estrutura"}, {"name": "Tag Fantasma"}]

        res = PurgeUnusedEngine.purge_unused_items(defs, insts, mats, tags)
        self.assertEqual(res["total_items_purged"], 3)
        self.assertIn("Mesa Deletada", res["purged_components"])
        self.assertIn("Tijolo Não Usado", res["purged_materials"])
        self.assertIn("Tag Fantasma", res["purged_tags"])
        # Layer0 nunca pode ser purgada
        self.assertNotIn("Layer0", res["purged_tags"])

    # 4. MakeComponentBehaviorEngine
    def test_make_component_behaviors(self):
        res = MakeComponentBehaviorEngine.create_component_definition(
            definition_name="Porta Balcão",
            description="Porta com abertura automática",
            glue_to="VERTICAL",
            cut_opening=True,
            always_face_camera=False
        )
        self.assertEqual(res["definition_name"], "Porta Balcão")
        self.assertEqual(res["behavior"]["glue_to"], "VERTICAL")
        self.assertTrue(res["behavior"]["cut_opening"])
        self.assertIsNotNone(res["behavior"]["opening_loop"])

        # Teste de compatibilidade de colagem
        self.assertTrue(MakeComponentBehaviorEngine.test_glue_compatibility("VERTICAL", (1.0, 0.0, 0.0)))
        self.assertFalse(MakeComponentBehaviorEngine.test_glue_compatibility("VERTICAL", (0.0, 0.0, 1.0)))

    # 5. AdvancedSelectionEngine
    def test_advanced_selection(self):
        # Inverter seleção
        all_ids = ["a", "b", "c", "d"]
        curr = ["a", "c"]
        inverted = AdvancedSelectionEngine.invert_selection(all_ids, curr)
        self.assertEqual(inverted, ["b", "d"])

        # Selecionar por tag
        insts = [{"id": "1", "tag": "Telhado"}, {"id": "2", "tag": "Parede"}, {"id": "3", "tag": "Telhado"}]
        by_tag = AdvancedSelectionEngine.select_by_tag("Telhado", insts)
        self.assertEqual(by_tag, ["1", "3"])

        # Conectados (Triplo clique)
        # Face 0 compartilha vértice com Face 1, Face 2 isolada
        faces = [
            [(0,0,0), (1,0,0), (0,1,0)],
            [(1,0,0), (2,0,0), (1,1,0)],
            [(10,10,10), (11,10,10), (10,11,10)]
        ]
        connected = AdvancedSelectionEngine.select_connected_geometry(0, faces)
        self.assertEqual(connected, [0, 1])

    # 6. HiddenGeometryEngine
    def test_hidden_geometry_configuration(self):
        insts = [{"id": "i1", "is_hidden": True}, {"id": "i2", "is_hidden": False}]
        edges = [{"id": "e1", "is_soft": True}, {"id": "e2", "is_soft": False}]

        res = HiddenGeometryEngine.configure_hidden_display(
            show_hidden_geometry=True,
            show_hidden_objects=True,
            instances=insts,
            edges=edges
        )
        self.assertEqual(res["instances_display_state"]["i1"]["display_mode"], "ghost_dashed")
        self.assertEqual(res["edges_display_state"]["e1"]["style"], "dashed")
        self.assertEqual(res["edges_display_state"]["e2"]["style"], "solid")

    # 7. ModelStatisticsEngine
    def test_model_statistics(self):
        stats = ModelStatisticsEngine.calculate_statistics(
            edges_count=1000,
            faces_count=500,
            component_definitions_count=10,
            component_instances_count=25
        )
        self.assertEqual(stats["total_geometry_entities"], 1500)
        self.assertEqual(stats["complexity_level"], "LEVE")
        self.assertIn("60+ FPS", stats["performance_profile"])

    # 8. Testes Assíncronos do Controller
    def test_async_controllers_native_part_3(self):
        async def run_controllers():
            # Texture Pin
            face_pts = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 1.0, 0.0)]
            req_pin = TexturePinTransformRequest(face_vertices=face_pts)
            res_pin = await self.controller.texture_pin_transform(req_pin)
            self.assertEqual(res_pin.entity_type, "sketchup_native_texture_pin_mapping")

            # Color by Tag
            req_cbt = ColorByTagApplyRequest(tags=[{"name": "Layer0"}], instances=[{"id": "1"}])
            res_cbt = await self.controller.color_by_tag_apply(req_cbt)
            self.assertEqual(res_cbt.entity_type, "sketchup_native_color_by_tag")

            # Purge Unused
            req_pu = PurgeUnusedRequest()
            res_pu = await self.controller.purge_unused_items(req_pu)
            self.assertEqual(res_pu.entity_type, "sketchup_native_purge_unused")

            # Make Component
            req_mc = MakeComponentDefinitionRequest(definition_name="Pilar Novo")
            res_mc = await self.controller.make_component_definition(req_mc)
            self.assertEqual(res_mc.entity_type, "sketchup_native_make_component")

            # Model Stats
            req_st = ModelStatisticsRequest(edges_count=200, faces_count=100)
            res_st = await self.controller.model_statistics_calculate(req_st)
            self.assertEqual(res_st.entity_type, "sketchup_native_model_statistics")

        asyncio.run(run_controllers())


if __name__ == "__main__":
    unittest.main()
