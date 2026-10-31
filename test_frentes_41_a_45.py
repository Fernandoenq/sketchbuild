"""
Testes de Integracao e Regressao para as Frentes 41 a 45 (Zero DLL).

- Frente 41: Interpolador de Caminho de Camera e Voo Panoramico (Catmull-Rom)
- Frente 42: Exportador de Nuvem de Pontos LiDAR (ASCII XYZ)
- Frente 43: Planejador de Manutencao Preventiva NBR 16071-7
- Frente 44: Ferramenta de Espelhamento e Simetria 3D (Householder)
- Frente 45: Gerador de QR Code Tecnico e Placa Patrimonial (SVG)
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
    CameraPathRequest,
    PointCloudExportRequest,
    MaintenancePlanRequest,
    MirrorRequest,
    QrTagExportRequest,
)
from core.camera_path_interpolator import CameraPathInterpolator
from core.point_cloud_exporter import PointCloudExporter
from core.maintenance_planner import MaintenancePlanner
from core.mirror_tool import MirrorTool
from core.qr_tag_generator import QrTagGenerator
from core.skp_binary_writer import SkpBinaryWriter


class TestFrentes41a45(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_frente_41_camera_path(self):
        """Valida interpolacao de sobrevoo de camera Catmull-Rom (Frente 41)."""
        waypoints = [
            {"position": [0.0, -10.0, 5.0], "target": [0.0, 0.0, 1.0]},
            {"position": [10.0, 0.0, 4.0], "target": [0.0, 0.0, 1.0]},
            {"position": [0.0, 10.0, 5.0], "target": [0.0, 0.0, 1.0]},
        ]
        req = CameraPathRequest(waypoints=waypoints, frames_per_segment=10)
        res = await self.controller.calculate_camera_path(req)
        self.assertEqual(res.entity_type, "FlythroughPath")
        self.assertEqual(res.waypoints_count, 3)
        self.assertEqual(res.total_frames, 21)
        self.assertGreater(res.duration_seconds, 0.0)
        self.assertEqual(len(res.camera_positions), 21)
        self.assertEqual(len(res.camera_targets), 21)
        print(f"[Frente 41] Camera Path: {res.total_frames} frames gerados ({res.duration_seconds}s a 24fps)")

    async def test_02_frente_42_point_cloud_export(self):
        """Valida exportacao de nuvem de pontos LiDAR ASCII XYZ (Frente 42)."""
        await self.controller.open_binary_scene(self.template_path)
        output_file = os.path.join(self.tmp_dir, "test_nuvem_lidar.xyz")
        if os.path.exists(output_file):
            os.remove(output_file)

        req = PointCloudExportRequest(output_filename=output_file)
        res = await self.controller.export_point_cloud_xyz(req)
        self.assertTrue(os.path.exists(res.file_path))
        self.assertGreater(res.size_bytes, 0)

        with open(res.file_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith("#")]
            self.assertGreater(len(lines), 0)
            parts = lines[0].split()
            self.assertEqual(len(parts), 7)  # X Y Z R G B Intensity

        print(f"[Frente 42] Point Cloud LiDAR exportado: {res.size_bytes} bytes ({len(lines)} pontos amostrados)")
        if os.path.exists(output_file):
            os.remove(output_file)

    async def test_03_frente_43_maintenance_plan(self):
        """Valida plano de manutencao preventiva NBR 16071-7 (Frente 43)."""
        await self.controller.open_binary_scene(self.template_path)
        req = MaintenancePlanRequest(installation_date_iso="2026-03-01", environment_type="coastal")
        res = await self.controller.generate_maintenance_plan(req)
        self.assertEqual(res.entity_type, "MaintenancePlan")
        self.assertIn("Litor", res.environment)
        self.assertGreater(len(res.tasks), 0)

        frequencies = {t["frequency"] for t in res.tasks}
        self.assertIn("Semanal", frequencies)
        self.assertTrue("Trimestral" in frequencies or "A cada 60 dias" in frequencies)
        self.assertIn("Anual", frequencies)
        print(f"[Frente 43] Plano de Manutencao: {len(res.tasks)} tarefas normativas, vida util esperada {res.expected_lifespan_years} anos")

    async def test_04_frente_44_mirror_tool(self):
        """Valida reflexao e simetria de Householder (Frente 44)."""
        await self.controller.open_binary_scene(self.template_path)
        plane_normal = [1.0, 0.0, 0.0]
        plane_point = [0.0, 0.0, 0.0]

        # Teste unitario na classe MirrorTool
        matrix = MirrorTool.create_mirror_matrix(tuple(plane_normal), tuple(plane_point))
        self.assertAlmostEqual(matrix[0], -1.0)
        self.assertAlmostEqual(matrix[5], 1.0)
        self.assertAlmostEqual(matrix[10], 1.0)

        face_vertices = [(1.0, 0.0, 0.0), (1.0, 2.0, 0.0), (1.0, 2.0, 2.0)]
        mirrored_face = MirrorTool.mirror_face_loop(face_vertices, tuple(plane_normal), tuple(plane_point))
        self.assertEqual(len(mirrored_face), 3)
        self.assertAlmostEqual(mirrored_face[0][0], -1.0)

        # Teste via controller com instancia ativa
        session = SkpBinaryWriter.get_session()
        inst_keys = list(session.instances_offsets.keys()) if session else []
        target_inst_id = inst_keys[0] if inst_keys else "inst_0_Model Root"

        req = MirrorRequest(instance_id=target_inst_id, plane_normal=plane_normal, plane_point=plane_point)
        res = await self.controller.apply_mirror_transform(req)
        self.assertEqual(res.instance_id, target_inst_id)
        self.assertEqual(len(res.transform_matrix_16), 16)
        print(f"[Frente 44] Mirror Tool: Reflexao Householder aplicada em {target_inst_id}")

    async def test_05_frente_45_qr_tag_generator(self):
        """Valida geracao de etiqueta patrimonial e QR Code em SVG (Frente 45)."""
        output_file = os.path.join(self.tmp_dir, "test_etiqueta_pkl.svg")
        if os.path.exists(output_file):
            os.remove(output_file)

        req = QrTagExportRequest(
            serial_number="PKL-2026-X84",
            product_name="Playground Parkelo NBR 16071",
            output_filename=output_file
        )
        res = await self.controller.export_qr_tag_svg(req)
        self.assertTrue(os.path.exists(res.file_path))
        self.assertGreater(res.size_bytes, 0)

        with open(res.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<svg", content)
            self.assertIn("PKL-2026-X84", content)
            self.assertIn("Parkelo", content)

        print(f"[Frente 45] QR Tag SVG gerado com sucesso: {res.size_bytes} bytes")
        if os.path.exists(output_file):
            os.remove(output_file)


if __name__ == "__main__":
    unittest.main()
