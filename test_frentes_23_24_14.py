import os
import sys
import ctypes
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.skp_binary_writer import SkpBinaryWriter
from core.cutlist_exporter import CutlistExporter
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    ExportCutlistRequest,
    AddCircleGeometryRequest,
    AddCylinderGeometryRequest,
    ExtrudeFaceGeometryRequest,
)


class SUEntitiesRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class TestFrentes23_24_14(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    def test_01_frente_23_cutlist_and_budget_xlsx(self):
        """Frente 23: Valida a compilação OpenXML .xlsx da lista de corte e orçamento Parkelô."""
        mock_bim = {
            "items": [
                {
                    "definition_name": "200416 - ESCORREGADOR TUBO H1200",
                    "instance_count": 2,
                    "unit_volume_m3": 0.45,
                    "unit_area_m2": 3.8,
                    "material": "Plastico Rotomoldado",
                    "unit_price": 2500.0,
                },
                {
                    "definition_name": "200338 - PASSARELA TUBO RETO L1600MM",
                    "instance_count": 1,
                    "unit_volume_m3": 0.32,
                    "unit_area_m2": 2.4,
                    "material": "Aço Carbono Galvanizado",
                    "unit_price": 3855.21,
                },
                {
                    "definition_name": "Deck Assoalho Madeira Plástica 140x30",
                    "instance_count": 8,
                    "unit_volume_m3": 0.04,
                    "unit_area_m2": 0.85,
                    "material": "Madeira Plastica",
                    "unit_price": 120.0,
                }
            ],
            "summary": {
                "total_items_count": 11,
                "total_volume_m3": 1.54,
                "total_area_m2": 13.0,
                "estimated_cost": 9815.21,
            }
        }
        out_xlsx = os.path.join(self.tmp_dir, "test_frente23_cutlist.xlsx")
        res = CutlistExporter.export_xlsx(mock_bim, out_xlsx)

        self.assertTrue(os.path.exists(out_xlsx))
        self.assertGreater(res["file_size_bytes"], 2000)
        self.assertEqual(res["total_pecas"], 11)
        self.assertGreater(res["total_custo_brl"], 5000.0)

        # Valida partes internas OpenXML
        with zipfile.ZipFile(out_xlsx, "r") as z:
            names = z.namelist()
            self.assertIn("xl/worksheets/sheet1.xml", names)
            self.assertIn("xl/worksheets/sheet2.xml", names)
            self.assertIn("xl/worksheets/sheet3.xml", names)
            self.assertIn("xl/styles.xml", names)

    def test_02_frente_14_cylinder_and_circle_brep(self):
        """Frente 14: Valida Círculo e Cilindro 3D Manifold (Zero DLL) com C++ Ground Truth."""
        # 1. Cria Círculo Plano
        SkpBinaryWriter.open_session(self.template_path)
        circle_res = SkpBinaryWriter.add_circle(radius_m=0.8, num_segments=16)
        self.assertEqual(circle_res["entity_type"], "Face")
        self.assertEqual(circle_res["vertex_count"], 16)
        self.assertEqual(len(circle_res["edge_ids"]), 16)

        # 2. Cria Cilindro Manifold
        cyl_res = SkpBinaryWriter.add_cylinder(radius_m=0.25, height_m=1.8, num_segments=12)
        self.assertEqual(cyl_res["entity_type"], "Cylinder")
        self.assertEqual(cyl_res["face_count"], 14)
        self.assertEqual(cyl_res["edge_count"], 36)
        self.assertEqual(cyl_res["vertex_count"], 24)

        out_skp = os.path.join(self.tmp_dir, "test_frente14_cylinder.skp")
        SkpBinaryWriter.save_session(out_skp, overwrite_confirmed=True)
        SkpBinaryWriter.close_session()

        # Validação Ground Truth C++ API da Trimble
        api = SketchUpAPI()
        api.initialize()
        try:
            dll = api._dll
            dll.SUModelGetEntities.restype = ctypes.c_int
            dll.SUModelGetEntities.argtypes = [SUModelRef, ctypes.POINTER(SUEntitiesRef)]
            dll.SUEntitiesGetNumFaces.restype = ctypes.c_int
            dll.SUEntitiesGetNumFaces.argtypes = [SUEntitiesRef, ctypes.POINTER(ctypes.c_size_t)]
            dll.SUEntitiesGetNumEdges.restype = ctypes.c_int
            dll.SUEntitiesGetNumEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.POINTER(ctypes.c_size_t)]

            model = api.open_model(out_skp)
            entities = SUEntitiesRef()
            self.assertEqual(dll.SUModelGetEntities(model._model, ctypes.byref(entities)), 0)

            num_faces = ctypes.c_size_t(0)
            self.assertEqual(dll.SUEntitiesGetNumFaces(entities, ctypes.byref(num_faces)), 0)
            num_edges = ctypes.c_size_t(0)
            self.assertEqual(dll.SUEntitiesGetNumEdges(entities, False, ctypes.byref(num_edges)), 0)

            # Esperado: 1 face do círculo + 14 faces do cilindro = 15 faces no mínimo
            self.assertGreaterEqual(num_faces.value, 15)
            self.assertGreaterEqual(num_edges.value, 52)
            print(f"\n[Ground Truth C++] Frente 14 validada: {num_faces.value} faces, {num_edges.value} arestas oficiais!")
            model.close()
        finally:
            api.terminate()

    def test_03_frente_24_pushpull_extrusion(self):
        """Frente 24: Valida Extrusão Push/Pull de face (Zero DLL) com C++ Ground Truth."""
        SkpBinaryWriter.open_session(self.template_path)

        # Face triangular de teste no chão
        pts_tri = [
            (0.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (1.0, 1.5, 0.0),
        ]
        # Extrude 1.2m para cima
        res = SkpBinaryWriter.extrude_face(pts_tri, distance_m=1.2, normal_xyz=(0.0, 0.0, 1.0))
        self.assertEqual(res["entity_type"], "Extrusion")
        self.assertEqual(res["vertex_count"], 6)
        self.assertEqual(res["face_count"], 5)  # 1 base + 1 topo + 3 laterais
        self.assertEqual(res["edge_count"], 9)

        out_skp = os.path.join(self.tmp_dir, "test_frente24_pushpull.skp")
        SkpBinaryWriter.save_session(out_skp, overwrite_confirmed=True)
        SkpBinaryWriter.close_session()

        # Validação Ground Truth C++ API da Trimble
        api = SketchUpAPI()
        api.initialize()
        try:
            dll = api._dll
            dll.SUModelGetEntities.restype = ctypes.c_int
            dll.SUModelGetEntities.argtypes = [SUModelRef, ctypes.POINTER(SUEntitiesRef)]
            dll.SUEntitiesGetNumFaces.restype = ctypes.c_int
            dll.SUEntitiesGetNumFaces.argtypes = [SUEntitiesRef, ctypes.POINTER(ctypes.c_size_t)]
            dll.SUEntitiesGetNumEdges.restype = ctypes.c_int
            dll.SUEntitiesGetNumEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.POINTER(ctypes.c_size_t)]

            model = api.open_model(out_skp)
            entities = SUEntitiesRef()
            self.assertEqual(dll.SUModelGetEntities(model._model, ctypes.byref(entities)), 0)

            num_faces = ctypes.c_size_t(0)
            self.assertEqual(dll.SUEntitiesGetNumFaces(entities, ctypes.byref(num_faces)), 0)
            num_edges = ctypes.c_size_t(0)
            self.assertEqual(dll.SUEntitiesGetNumEdges(entities, False, ctypes.byref(num_edges)), 0)

            self.assertGreaterEqual(num_faces.value, 5)
            self.assertGreaterEqual(num_edges.value, 9)
            print(f"[Ground Truth C++] Frente 24 validada: {num_faces.value} faces, {num_edges.value} arestas oficiais!")
            model.close()
        finally:
            api.terminate()

    async def test_04_fastapi_endpoints_frentes_23_14_24(self):
        """Valida a execução assíncrona dos endpoints FastAPI das Frentes 23, 14 e 24."""
        # 1. Abre sessão
        await self.controller.open_binary_scene(self.template_path)

        # 2. Endpoint Frente 23: Exportar Cutlist XLSX
        out_xlsx = os.path.join(self.tmp_dir, "api_cutlist.xlsx")
        resp_cutlist = await self.controller.export_cutlist_xlsx(ExportCutlistRequest(path=out_xlsx))
        self.assertTrue(resp_cutlist.saved)
        self.assertTrue(os.path.exists(out_xlsx))

        # 3. Endpoint Frente 14: Círculo e Cilindro
        req_circ = AddCircleGeometryRequest(radius_m=1.2, center_xyz_m=[0.0, 0.0, 0.0], num_segments=20)
        resp_circ = await self.controller.add_circle_geometry(req_circ)
        self.assertTrue(resp_circ.success)
        self.assertEqual(resp_circ.entity["segments"], 20)

        req_cyl = AddCylinderGeometryRequest(radius_m=0.4, height_m=2.2, center_xyz_m=[1.0, 1.0, 0.0], num_segments=16)
        resp_cyl = await self.controller.add_cylinder_geometry(req_cyl)
        self.assertTrue(resp_cyl.success)
        self.assertEqual(resp_cyl.entity["face_count"], 18)

        # 4. Endpoint Frente 24: Push/Pull
        req_pp = ExtrudeFaceGeometryRequest(
            points_m=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0]],
            distance_m=1.5,
            normal=[0.0, 0.0, 1.0],
        )
        resp_pp = await self.controller.extrude_face_geometry(req_pp)
        self.assertTrue(resp_pp.success)
        self.assertEqual(resp_pp.entity["face_count"], 6)


if __name__ == "__main__":
    unittest.main()
