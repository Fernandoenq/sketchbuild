"""
Testes unitários automatizados para as Ferramentas Nativas Oficiais do SketchUp (Opção A - Parte 2).
Cobre todos os 7 novos motores em Pure Python (Zero DLL) e as camadas da arquitetura:
1. IfcClassificationEngine (Classificação IFC4/IFC2x3 e auditoria BIM)
2. ThreeDTextEngine (Geração de Texto 3D B-Rep paramétrico com extrusão)
3. GenerateReportEngine (Gerador Oficial de Relatórios CSV/JSON)
4. AxesSystemEngine (Axes Tool: eixos customizados, alinhamento à face e reset)
5. EntityMetricsInspectorEngine (Entity Info: arestas, faces e Solid Inspector 2-manifold)
6. ComponentEditModesEngine (Hide/Fade Rest of Model)
7. ModelUnitsPrecisionEngine (Unidades, precisão decimal, formatação VCB e snaps)
"""

import unittest
import asyncio

from core.ifc_classification_engine import IfcClassificationEngine
from core.three_d_text_engine import ThreeDTextEngine
from core.generate_report_engine import GenerateReportEngine
from core.axes_system_engine import AxesSystemEngine
from core.entity_metrics_inspector_engine import EntityMetricsInspectorEngine
from core.component_edit_modes_engine import ComponentEditModesEngine
from core.model_units_precision_engine import ModelUnitsPrecisionEngine

from app.schemas.scene import (
    IfcClassifyComponentRequest,
    IfcAuditRequest,
    ThreeDTextGenerateRequest,
    GenerateReportRequest,
    AxesCustomSetRequest,
    AxesAlignFaceRequest,
    EntityInspectEdgeRequest,
    EntityInspectFaceRequest,
    EntityInspectSolidRequest,
    ComponentEditModeRequest,
    ModelUnitsConfigRequest,
    ModelUnitsFormatRequest,
)
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController


class TestOpcaoAParte2SketchupNative(unittest.TestCase):
    """Suíte de testes para a segunda rodada de ferramentas nativas oficiais do SketchUp."""

    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(self.repo)
        self.controller = SceneController(self.service)

    # 1. IfcClassificationEngine
    def test_ifc_classification_and_audit(self):
        res = IfcClassificationEngine.classify_component(
            instance_id="inst_pilar_01",
            definition_name="Pilar Central",
            schema_name="IFC4",
            ifc_class="IfcColumn",
            predefined_type="COLUMN"
        )
        self.assertEqual(res["ifc_class"], "IfcColumn")
        self.assertTrue(res["is_valid_bim"])
        self.assertIn("global_id", res)

        # Auditoria de cena
        mock_instances = [
            {"id": "inst_1", "classification": {"ifc_class": "IfcColumn"}},
            {"id": "inst_2", "classification": None}
        ]
        audit = IfcClassificationEngine.audit_scene_classifications(mock_instances)
        self.assertEqual(audit["total_instances"], 2)
        self.assertEqual(audit["classified_count"], 1)
        self.assertEqual(audit["unclassified_count"], 1)
        self.assertEqual(audit["compliance_percentage"], 50.0)

    # 2. ThreeDTextEngine
    def test_three_d_text_generation(self):
        res = ThreeDTextEngine.generate_3d_text(
            text="SKETCH",
            font_family="Arial",
            height_m=0.30,
            extrusion_depth_m=0.05,
            is_filled=True,
            is_extruded=True
        )
        self.assertEqual(res["text"], "SKETCH")
        self.assertGreater(res["faces_count"], 0)
        self.assertGreater(res["edges_count"], 0)
        self.assertAlmostEqual(res["height_m"], 0.30)
        self.assertAlmostEqual(res["extrusion_depth_m"], 0.05)

    # 3. GenerateReportEngine
    def test_generate_report_csv_and_rows(self):
        instances = [
            {"id": "p1", "definition_name": "Pilar", "volume_m3": 0.5, "area_m2": 4.0, "tag": "Estrutura", "material": "Concreto", "ifc_class": "IfcColumn", "bounds": [0.3, 0.3, 3.0]},
            {"id": "p2", "definition_name": "Pilar", "volume_m3": 0.5, "area_m2": 4.0, "tag": "Estrutura", "material": "Concreto", "ifc_class": "IfcColumn", "bounds": [0.3, 0.3, 3.0]},
            {"id": "v1", "definition_name": "Viga", "volume_m3": 0.8, "area_m2": 6.0, "tag": "Estrutura", "material": "Concreto", "ifc_class": "IfcBeam", "bounds": [5.0, 0.3, 0.4]}
        ]
        res = GenerateReportEngine.generate_report(instances, scope="entire_model", group_by_definition=True)
        self.assertEqual(res["total_instances_count"], 3)
        self.assertEqual(res["total_items_count"], 2)  # Agrupado por Pilar e Viga
        self.assertAlmostEqual(res["total_volume_m3"], 1.8)
        self.assertIn("Pilar", res["csv_content"])
        self.assertIn("Viga", res["csv_content"])

    # 4. AxesSystemEngine
    def test_axes_system_custom_align_and_reset(self):
        # Eixos customizados
        res_custom = AxesSystemEngine.set_custom_axes(
            origin=(1.0, 2.0, 3.0),
            x_point=(2.0, 2.0, 3.0),
            y_point=(1.0, 3.0, 3.0)
        )
        self.assertEqual(res_custom["origin"], (1.0, 2.0, 3.0))
        self.assertEqual(res_custom["axis_x_red"], (1.0, 0.0, 0.0))
        self.assertEqual(res_custom["axis_y_green"], (0.0, 1.0, 0.0))
        self.assertEqual(res_custom["axis_z_blue"], (0.0, 0.0, 1.0))

        # Alinhar à face inclinada
        face_pts = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 1.0)]
        res_face = AxesAlignFaceEngine = AxesSystemEngine.align_axes_to_face(face_pts)
        self.assertTrue(res_face["aligned_to_face"])
        self.assertIn("matrix4x4", res_face)

        # Reset
        res_reset = AxesSystemEngine.reset_axes()
        self.assertTrue(res_reset["is_global"])
        self.assertEqual(res_reset["origin"], (0.0, 0.0, 0.0))

    # 5. EntityMetricsInspectorEngine
    def test_entity_metrics_inspector(self):
        # Aresta
        edge = EntityMetricsInspectorEngine.inspect_edge((0, 0, 0), (3, 4, 0))
        self.assertAlmostEqual(edge["length_m"], 5.0)
        self.assertAlmostEqual(edge["length_cm"], 500.0)

        # Face
        face_pts = [(0, 0, 0), (2, 0, 0), (2, 3, 0), (0, 3, 0)]
        face = EntityMetricsInspectorEngine.inspect_face(face_pts)
        self.assertAlmostEqual(face["area_m2"], 6.0)
        self.assertEqual(face["normal"], (0.0, 0.0, 1.0))

        # Sólido 2-Manifold Fechado (Cubo 1x1x1)
        cube_tris = [
            [[0,0,0], [1,0,0], [1,1,0]], [[0,0,0], [1,1,0], [0,1,0]],
            [[0,0,1], [1,1,1], [1,0,1]], [[0,0,1], [0,1,1], [1,1,1]],
            [[0,0,0], [0,0,1], [1,0,1]], [[0,0,0], [1,0,1], [1,0,0]],
            [[1,0,0], [1,0,1], [1,1,1]], [[1,0,0], [1,1,1], [1,1,0]],
            [[1,1,0], [1,1,1], [0,1,1]], [[1,1,0], [0,1,1], [0,1,0]],
            [[0,1,0], [0,1,1], [0,0,1]], [[0,1,0], [0,0,1], [0,0,0]]
        ]
        solid = EntityMetricsInspectorEngine.inspect_solid_component("Cubo", "c1", cube_tris)
        self.assertTrue(solid["is_solid"])
        self.assertAlmostEqual(solid["volume_m3"], 1.0)
        self.assertAlmostEqual(solid["total_area_m2"], 6.0)

    # 6. ComponentEditModesEngine
    def test_component_edit_modes(self):
        instances = [
            {"id": "inst_1", "name": "Porta"},
            {"id": "inst_2", "name": "Porta"},
            {"id": "inst_3", "name": "Parede"}
        ]
        res = ComponentEditModesEngine.apply_component_edit_mode(
            active_instance_id="inst_1",
            active_definition_name="Porta",
            all_instances=instances,
            hide_rest_of_model=True,
            fade_similar_components=True,
            fade_opacity=0.30
        )
        self.assertTrue(res["is_editing"])
        self.assertEqual(res["instances_state"]["inst_1"]["mode"], "active_editing")
        self.assertEqual(res["instances_state"]["inst_2"]["mode"], "faded")
        self.assertEqual(res["instances_state"]["inst_3"]["mode"], "hidden")

    # 7. ModelUnitsPrecisionEngine
    def test_model_units_and_precision(self):
        cfg = ModelUnitsPrecisionEngine.configure_units("DECIMAL", "METERS", 3, True, 0.05, True, 15.0)
        self.assertEqual(cfg["unit"], "METERS")
        self.assertEqual(cfg["precision_digits"], 3)

        # Formatação
        fmt = ModelUnitsPrecisionEngine.format_length(1.23456, "METERS", 2)
        self.assertEqual(fmt, "1.23m")

        # Parsing de entrada do usuário no VCB
        self.assertAlmostEqual(ModelUnitsPrecisionEngine.parse_user_input("2.5m"), 2.5)
        self.assertAlmostEqual(ModelUnitsPrecisionEngine.parse_user_input("150cm"), 1.5)
        self.assertAlmostEqual(ModelUnitsPrecisionEngine.parse_user_input("2000mm"), 2.0)

        # Snaps
        self.assertAlmostEqual(ModelUnitsPrecisionEngine.apply_snapping(1.234, 0.05), 1.25)
        self.assertAlmostEqual(ModelUnitsPrecisionEngine.apply_angle_snapping(16.5, 15.0), 15.0)

    # 8. Testes Assíncronos do Controller
    def test_async_controllers_native_part_2(self):
        async def run_controllers():
            # IFC Classify
            req_ifc = IfcClassifyComponentRequest(instance_id="c_1", ifc_class="IfcBeam")
            res_ifc = await self.controller.ifc_classify_component(req_ifc)
            self.assertEqual(res_ifc.entity_type, "sketchup_native_ifc_classification")

            # 3D Text
            req_text = ThreeDTextGenerateRequest(text="TESTE 3D")
            res_text = await self.controller.generate_3d_text(req_text)
            self.assertEqual(res_text.entity_type, "sketchup_native_3d_text")

            # Generate Report
            req_rep = GenerateReportRequest(instances=[{"id": "1", "name": "A"}])
            res_rep = await self.controller.generate_report(req_rep)
            self.assertEqual(res_rep.entity_type, "sketchup_native_generate_report")

            # Axes Reset
            res_axes = await self.controller.axes_reset()
            self.assertEqual(res_axes.entity_type, "sketchup_native_axes_system")

            # Units Config
            req_units = ModelUnitsConfigRequest()
            res_units = await self.controller.model_units_configure(req_units)
            self.assertEqual(res_units.entity_type, "sketchup_native_model_units")

        asyncio.run(run_controllers())


if __name__ == "__main__":
    unittest.main()
