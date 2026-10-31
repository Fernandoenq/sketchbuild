"""
Testes de Integração e Regressão para as Frentes 17, 18, 25, 29 e 30 (Zero DLL).

- Frente 17: Planos e Cortes de Seção (SectionPlane)
- Frente 18: Linhas de Guia e Pontos de Construção (Tape Measure)
- Frente 25: Operações Booleanas de Sólidos (CSG / Solid Tools)
- Frente 29: Exportador Executivo de Proposta Comercial em PDF Vetorial
- Frente 30: Ferramenta de Offset / Equidistância 2D/3D
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
    SectionPlaneRequest,
    GuideLineRequest,
    GuidePointRequest,
    BooleanOperationRequest,
    OffsetFaceRequest,
    ExecutivePdfExportRequest,
)
from core.solid_tools import SolidTools
from core.offset_calculator import OffsetCalculator
from core.executive_pdf_exporter import ExecutivePdfExporter


class TestFrentesNovas(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_frente_17_section_plane(self):
        """Valida criação e persistência de Planos de Corte de Seção (SectionPlane)."""
        await self.controller.open_binary_scene(self.template_path)

        req = SectionPlaneRequest(
            plane_abcd=[0.0, 0.0, 1.0, -1.20],
            name="Corte Longitudinal B-B",
            symbol="B1"
        )
        res = await self.controller.add_section_plane(req)
        self.assertEqual(res.entity_type, "SectionPlane")
        self.assertEqual(res.name, "Corte Longitudinal B-B")
        self.assertEqual(res.symbol, "B1")
        self.assertEqual(res.plane[2], 1.0)
        self.assertEqual(res.plane[3], -1.20)

        # Listagem
        planes = await self.controller.get_section_planes()
        self.assertTrue(any(p.name == "Corte Longitudinal B-B" for p in planes))
        print(f"\n[Frente 17] SectionPlane criado e verificado: {res.name} (Plano Z={res.plane[3]}m)")

    async def test_02_frente_18_guides_and_tape_measure(self):
        """Valida Linhas de Guia e Pontos de Construção (Tape Measure)."""
        await self.controller.open_binary_scene(self.template_path)

        # 1. GuideLine
        req_line = GuideLineRequest(
            start=[0.0, 0.0, 0.0],
            end=[2.5, 0.0, 0.0],
            is_infinite=False
        )
        res_line = await self.controller.add_guide_line(req_line)
        self.assertEqual(res_line["entity_type"], "GuideLine")
        self.assertEqual(res_line["end"][0], 2.5)

        # 2. GuidePoint
        req_pt = GuidePointRequest(position=[1.25, 0.50, 2.10])
        res_pt = await self.controller.add_guide_point(req_pt)
        self.assertEqual(res_pt["entity_type"], "GuidePoint")
        self.assertEqual(res_pt["position"], [1.25, 0.50, 2.10])

        # 3. Consulta de guias
        guides_data = await self.controller.get_guides()
        self.assertGreaterEqual(len(guides_data.guide_lines), 1)
        self.assertGreaterEqual(len(guides_data.guide_points), 1)
        print(f"[Frente 18] Guias e Pontos de Construção ativos: {len(guides_data.guide_lines)} linhas, {len(guides_data.guide_points)} pontos")

    async def test_03_frente_25_solid_tools_csg(self):
        """Valida operações booleanas analíticas de sólidos (Furação e Subtração CSG)."""
        # 1. Subtração de Bloco por Bloco (ex: encaixe de sapata para pilar de 0.20x0.20m)
        main_box = {"origin": (0.0, 0.0, 0.0), "width": 1.0, "depth": 1.0, "height": 0.5}
        cut_box = {"origin": (0.4, 0.4, 0.2), "width": 0.2, "depth": 0.2, "height": 0.4}
        sub_res = SolidTools.subtract_box_from_box(main_box, cut_box)
        self.assertEqual(sub_res["operation"], "subtract")
        self.assertGreater(len(sub_res["faces"]), 6)

        # 2. Furação cilíndrica de poste (furo de barra roscada Ø 1/2")
        post_box = {"origin": (0.0, 0.0, 0.0), "width": 0.15, "depth": 0.15, "height": 2.50}
        hole_cylinder = {"center": (0.075, 0.075, 1.20), "radius": 0.015, "height": 0.15, "axis": "y"}
        drill_res = SolidTools.subtract_cylinder_from_box(post_box, hole_cylinder, segments=12)
        self.assertEqual(drill_res["operation"], "subtract_hole")
        self.assertEqual(drill_res["hole_faces_count"], 12)

        # 3. Via Controlador
        req_b = BooleanOperationRequest(
            operation="subtract_hole",
            main_shape=post_box,
            tool_shape=hole_cylinder
        )
        b_data = await self.controller.apply_boolean_operation(req_b)
        self.assertEqual(b_data.operation, "subtract_hole")
        self.assertEqual(b_data.faces_count, 22)
        print(f"[Frente 25] Operação Booleana CSG: Subtração e furação geraram {b_data.faces_count} faces B-Rep manifold")

    async def test_04_frente_29_executive_pdf_exporter(self):
        """Valida compilação nativa de PDF-1.4 em Pure Python (Zero DLL)."""
        await self.controller.open_binary_scene(self.template_path)

        scene_data = {
            "instances": [
                {"name": "Torre Panorâmica Parkelô", "position": [0, 0, 0]},
                {"name": "Pilar Eucalipto Autoclavado 3.0m", "position": [1, 0, 0]},
                {"name": "Escorregador em Tubo Curvo", "position": [0, 1.5, 0]}
            ]
        }
        pdf_bytes = ExecutivePdfExporter.generate_pdf(scene_data, project_name="Playground Escola Modelo")
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"), "Cabeçalho PDF-1.4 inválido")
        self.assertTrue(b"%%EOF" in pdf_bytes, "Trailer PDF %%EOF ausente")
        self.assertTrue(b"xref" in pdf_bytes, "Tabela de referências cruzadas xref ausente")
        self.assertTrue(b"PARKELO" in pdf_bytes or b"Parkel" in pdf_bytes)

        # Teste do endpoint via controller
        req_pdf = ExecutivePdfExportRequest(
            project_name="Parque Infantil Escola Municipal",
            author="Eng. Fernando",
            client_name="Prefeitura",
            output_filename="teste_proposta_executiva.pdf"
        )
        pdf_info = await self.controller.export_executive_pdf(req_pdf)
        self.assertGreater(pdf_info.size_bytes, 1000)
        self.assertTrue(os.path.exists(pdf_info.file_path))
        print(f"[Frente 29] Proposta Executiva PDF exportada: {pdf_info.file_path} ({pdf_info.size_bytes} bytes)")

    async def test_05_frente_30_offset_calculator(self):
        """Valida algoritmo de deslocamento paralelo (Offset / Equidistância 2D e 3D)."""
        await self.controller.open_binary_scene(self.template_path)

        rect = [
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [2.0, 1.0, 0.0],
            [0.0, 1.0, 0.0]
        ]
        # Offset interno de 0.10m
        offset_rect = OffsetCalculator.offset_polygon_3d([tuple(p) for p in rect], distance=0.10, inside=True)
        self.assertEqual(len(offset_rect), 4)
        self.assertAlmostEqual(offset_rect[0][0], 0.10, places=2)
        self.assertAlmostEqual(offset_rect[0][1], 0.10, places=2)

        # Moldura (anel)
        frame = OffsetCalculator.generate_frame_faces([tuple(p) for p in rect], offset_rect)
        self.assertEqual(len(frame), 4)

        # Teste via controller
        req_off = OffsetFaceRequest(
            points=rect,
            distance=0.15,
            inside=True,
            create_frame=True
        )
        offset_data = await self.controller.add_offset_face(req_off)
        self.assertEqual(offset_data.entity_type, "OffsetFrame")
        self.assertEqual(offset_data.distance_m, 0.15)
        print(f"[Frente 30] Offset analítico: Retângulo 2.0x1.0m deslocado em 0.15m gerou moldura com {len(frame)} faces quadriláteras")


if __name__ == "__main__":
    unittest.main()
