import os
import sys
import json
import struct
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.glb_exporter import GlbExporter
from core.ifc_exporter import IfcExporter
from core.skp_binary_writer import SkpBinaryWriter
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController
from app.schemas.scene import ExportGlbRequest, ExportIfcRequest


class TestMultiFormatExporter(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    def test_01_direct_glb_compilation(self):
        """Valida a compilação binária do glTF 2.0 (GLB) conforme a especificação Khronos."""
        glb_out = os.path.join(self.tmp_dir, "test_output.glb")
        if os.path.exists(glb_out):
            os.remove(glb_out)

        # Mock de cena 3D (um cubo unitário 1x1x1m com material)
        half_in = (1.0 * 100.0 / 2.54) / 2
        verts = [
            -half_in, -half_in, 0.0,
             half_in, -half_in, 0.0,
             half_in,  half_in, 0.0,
            -half_in,  half_in, 0.0,
        ]
        scene_mock = {
            "definitions": [{
                "definition_id": "def_box",
                "name": "Box_1x1m",
                "vertices": verts,
                "normals": [0.0, 0.0, 1.0] * 4,
                "indices": [0, 1, 2, 0, 2, 3],
                "uvs": [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0],
                "material_name": "Madeira",
            }],
            "instances": [{
                "instance_id": "inst_1",
                "definition_id": "def_box",
                "name": "Instancia_Box",
                "transform": [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    0, 0, 0, 1,
                ],
            }],
            "materials": {
                "Madeira": {
                    "color": [180, 120, 80],
                    "opacity": 1.0,
                    "roughness": 0.7,
                    "metalness": 0.1,
                }
            },
        }

        res = GlbExporter.export_from_scene_data(scene_mock, glb_out)
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(glb_out))
        self.assertTrue(res["file_size_bytes"] > 0)

        # Validação do Container Binário GLB
        with open(glb_out, "rb") as f:
            data = f.read()

        # 1. Header de 12 bytes
        magic, version, length = struct.unpack_from("<III", data, 0)
        self.assertEqual(magic, 0x46546C67, "Magic byte deve ser 0x46546C67 (glTF)")
        self.assertEqual(version, 2, "Versão do glTF deve ser 2")
        self.assertEqual(length, len(data), "Comprimento no cabeçalho deve ser idêntico ao arquivo real")

        # 2. Chunk 0: JSON
        c0_len, c0_type = struct.unpack_from("<II", data, 12)
        self.assertEqual(c0_type, 0x4E4F534A, "Chunk 0 deve ser do tipo JSON (0x4E4F534A)")
        json_bytes = data[20 : 20 + c0_len]
        manifest = json.loads(json_bytes.decode("utf-8").strip())
        self.assertEqual(manifest["asset"]["version"], "2.0")
        self.assertEqual(len(manifest["meshes"]), 1)
        self.assertEqual(len(manifest["nodes"]), 1)
        self.assertEqual(len(manifest["materials"]), 1)

        # 3. Chunk 1: BIN
        c1_pos = 20 + c0_len
        c1_len, c1_type = struct.unpack_from("<II", data, c1_pos)
        self.assertEqual(c1_type, 0x004E4942, "Chunk 1 deve ser do tipo BIN (0x004E4942)")
        self.assertTrue(c1_len > 0)
        print(f"[OK] test_01_direct_glb_compilation aprovado! (Arquivo={len(data)} bytes, JSON={c0_len} bytes, BIN={c1_len} bytes)")
        if os.path.exists(glb_out):
            os.remove(glb_out)

    def test_02_direct_ifc_compilation(self):
        """Valida a compilação do modelo BIM IFC4 / STEP ISO 10303-21."""
        ifc_out = os.path.join(self.tmp_dir, "test_output.ifc")
        if os.path.exists(ifc_out):
            os.remove(ifc_out)

        scene_mock = {
            "definitions": [{
                "definition_id": "def_coluna",
                "name": "Coluna_Eucalipto",
                "vertices": [
                    0.0, 0.0, 0.0,
                    10.0, 0.0, 0.0,
                    10.0, 10.0, 0.0,
                    0.0, 10.0, 0.0,
                ],
                "normals": [0.0, 0.0, 1.0] * 4,
                "indices": [0, 1, 2, 0, 2, 3],
            }],
            "instances": [{
                "instance_id": "inst_coluna_1",
                "definition_id": "def_coluna",
                "name": "Poste Principal 1",
                "transform": [
                    1, 0, 0, 0,
                    0, 1, 0, 0,
                    0, 0, 1, 0,
                    100, 200, 0, 1,
                ],
                "attributes": {
                    "DadosBIM": {
                        "Fabricante": "Parkelô",
                        "Material": "Eucalipto Autoclavado",
                        "Custo": "150.00",
                    }
                },
            }],
        }

        res = IfcExporter.export_from_scene_data(scene_mock, ifc_out, project_name="Parque Infantil Teste")
        self.assertTrue(res["success"])
        self.assertTrue(os.path.exists(ifc_out))

        with open(ifc_out, "r", encoding="utf-8") as f:
            content = f.read()

        # Validação da estrutura STEP ISO 10303-21
        self.assertTrue(content.startswith("ISO-10303-21;"))
        self.assertIn("FILE_SCHEMA(('IFC4'));", content)
        self.assertIn("IFCPROJECT", content)
        self.assertIn("IFCSITE", content)
        self.assertIn("IFCBUILDING", content)
        self.assertIn("IFCBUILDINGSTOREY", content)
        self.assertIn("IFCFACETEDBREP", content)
        self.assertIn("IFCCLOSEDSHELL", content)
        self.assertIn("IFCBUILDINGELEMENTPROXY", content)
        self.assertIn("IFCPROPERTYSET", content)
        self.assertIn("Eucalipto Autoclavado", content)
        self.assertIn("END-ISO-10303-21;", content)
        print(f"[OK] test_02_direct_ifc_compilation aprovado! (Arquivo={len(content)} caracteres, Elementos={res['elements_count']})")
        if os.path.exists(ifc_out):
            os.remove(ifc_out)

    async def test_03_fastapi_endpoints_export(self):
        """Valida os endpoints FastAPI de exportação GLB e IFC."""
        src_skp = r"C:\Users\Fernando\Documents\Sem nome.skp"
        SkpBinaryWriter.open_session(src_skp)

        glb_target = os.path.join(self.tmp_dir, "api_export.glb")
        ifc_target = os.path.join(self.tmp_dir, "api_export.ifc")

        try:
            # 1. Exportação GLB via Controller
            req_glb = ExportGlbRequest(path=glb_target)
            res_glb = await self.controller.export_model_glb(req_glb.path)
            self.assertTrue(res_glb.saved)
            self.assertTrue(os.path.exists(res_glb.path))
            self.assertTrue(res_glb.file_size_bytes > 0)
            print(f"[OK] test_03_fastapi_endpoints_export (GLB): {res_glb.path} ({res_glb.file_size_bytes} bytes)")

            # 2. Exportação IFC via Controller
            req_ifc = ExportIfcRequest(path=ifc_target, project_name="Modelo Oficial SketchBuild")
            res_ifc = await self.controller.export_model_ifc(req_ifc.path, project_name=req_ifc.project_name)
            self.assertTrue(res_ifc.saved)
            self.assertTrue(os.path.exists(res_ifc.path))
            self.assertTrue(res_ifc.file_size_bytes > 0)
            print(f"[OK] test_03_fastapi_endpoints_export (IFC): {res_ifc.path} ({res_ifc.file_size_bytes} bytes)")
        finally:
            if os.path.exists(glb_target): os.remove(glb_target)
            if os.path.exists(ifc_target): os.remove(ifc_target)


if __name__ == "__main__":
    unittest.main()
