import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.skp_binary_writer import SkpBinaryWriter
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    CreateBoxRequest,
    SetStyleRequest,
    ConvertDxfRequest,
    ExplodedViewRequest,
)


class TestFaseOpcoes1E2(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_set_rendering_style(self):
        req = SetStyleRequest(
            mode="hidden_line",
            xray=True,
            profiles_width=3,
            background_rgb=[255, 255, 255],
            sky_rgb=[220, 230, 240],
        )
        res = await self.controller.set_rendering_style(req)
        self.assertTrue(res.success)
        self.assertEqual(res.mode, "hidden_line")
        self.assertTrue(res.xray)
        self.assertEqual(res.profiles_width, 3)
        print("[OK] test_01_set_rendering_style aprovado!")

    async def test_02_add_box(self):
        template_file = r"C:\Users\Fernando\Documents\Sem nome.skp"
        SkpBinaryWriter.open_session(template_file)
        
        req = CreateBoxRequest(width_m=1.5, length_m=0.8, height_m=0.75, offset_xyz_cm=[10.0, 20.0, 0.0])
        res = await self.controller.add_box(req)
        self.assertEqual(res.box.entity_type, "Box")
        self.assertEqual(res.box.vertex_count, 8)
        self.assertEqual(res.box.edge_count, 12)
        self.assertEqual(res.box.face_count, 6)
        self.assertAlmostEqual(res.box.volume_m3, 0.9, places=2)
        self.assertTrue(len(res.scene.definitions) >= 1)
        print("[OK] test_02_add_box aprovado!")

    async def test_03_get_assembly_tree(self):
        res = await self.controller.get_assembly_tree()
        self.assertEqual(res.name, "Model Root")
        self.assertIsInstance(res.children, list)
        print(f"[OK] test_03_get_assembly_tree aprovado (total={res.total_instances}, root_nodes={res.root_nodes_count})!")

    async def test_04_calculate_exploded_view(self):
        req = ExplodedViewRequest(expansion_factor=0.8)
        res = await self.controller.calculate_exploded_view(req)
        self.assertEqual(res.expansion_factor, 0.8)
        self.assertIsInstance(res.instance_transforms, dict)
        print(f"[OK] test_04_calculate_exploded_view aprovado ({len(res.instance_transforms)} instancias transformadas)!")

    async def test_05_calculate_bim_bom(self):
        res = await self.controller.get_bim_bom_report()
        self.assertTrue(res.summary.total_items_count >= 1)
        self.assertTrue(res.summary.total_area_m2 > 0)
        self.assertTrue(res.summary.estimated_cost > 0)
        self.assertEqual(res.summary.currency, "BRL")
        self.assertTrue(len(res.items) >= 1)
        print(f"[OK] test_05_calculate_bim_bom aprovado: Total R$ {res.summary.estimated_cost:.2f}, Volume={res.summary.total_volume_m3}m3, Area={res.summary.total_area_m2}m2")

    async def test_06_convert_dxf(self):
        dxf_content = """0
SECTION
2
HEADER
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
10
0.0
20
0.0
30
0.0
11
300.0
21
0.0
31
0.0
0
3DFACE
10
0.0
20
0.0
30
0.0
11
300.0
21
0.0
31
0.0
12
300.0
22
200.0
32
0.0
13
0.0
23
200.0
33
0.0
0
ENDSEC
0
EOF
"""
        with tempfile.NamedTemporaryFile("w", suffix=".dxf", delete=False) as tf:
            tf.write(dxf_content)
            temp_dxf = tf.name

        try:
            req = ConvertDxfRequest(dxf_path=temp_dxf, scale_factor=1.0)
            res = await self.controller.convert_dxf(req)
            self.assertTrue(res.success)
            self.assertTrue(os.path.exists(res.output_skp_path))
            self.assertEqual(res.faces_count, 1)
            self.assertEqual(res.lines_count, 1)
            self.assertAlmostEqual(res.total_area_m2, 6.0, places=1)
            print("[OK] test_06_convert_dxf aprovado!")
            if os.path.exists(res.output_skp_path):
                os.remove(res.output_skp_path)
        finally:
            if os.path.exists(temp_dxf):
                os.remove(temp_dxf)


if __name__ == "__main__":
    unittest.main()
