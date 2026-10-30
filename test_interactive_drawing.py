import os
import sys
import ctypes
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.skp_binary_writer import SkpBinaryWriter
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef
from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController
from app.schemas.scene import AddLineGeometryRequest, AddFaceGeometryRequest


class SUEntitiesRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class TestInteractiveDrawing(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    def test_01_binary_writer_add_line_edge(self):
        """Testa a criação de aresta 3D nativa no binário .skp (Zero DLL)."""
        SkpBinaryWriter.open_session(self.template_path)
        
        start_m = (0.0, 0.0, 0.0)
        end_m = (2.5, 0.0, 0.0)
        res = SkpBinaryWriter.add_line_edge(start_m, end_m)

        self.assertEqual(res["entity_type"], "Edge")
        self.assertIn("edge_id", res)
        self.assertEqual(len(res["vertex_ids"]), 2)
        self.assertEqual(res["length_m"], 2.5)

        out_skp = os.path.join(self.tmp_dir, "test_interactive_line.skp")
        SkpBinaryWriter.save_session(out_skp, overwrite_confirmed=True)
        SkpBinaryWriter.close_session()
        self.assertTrue(os.path.exists(out_skp))
        self.assertGreater(os.path.getsize(out_skp), 1000)

    def test_02_binary_writer_add_polygon_face(self):
        """Testa a criação de Face coplanar nativa B-Rep com 4 vértices no .skp (Zero DLL)."""
        SkpBinaryWriter.open_session(self.template_path)

        # Retângulo 3x2m no plano XY (chão horizontal Z=0)
        pts = [
            (0.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (3.0, 2.0, 0.0),
            (0.0, 2.0, 0.0),
        ]
        res = SkpBinaryWriter.add_polygon_face(pts)

        self.assertEqual(res["entity_type"], "Face")
        self.assertIn("face_id", res)
        self.assertEqual(res["vertex_count"], 4)
        self.assertEqual(len(res["edge_ids"]), 4)
        self.assertEqual(len(res["vertex_ids"]), 4)

        # Normal deve apontar para cima em Z: [0, 0, 1]
        self.assertAlmostEqual(res["normal"][0], 0.0, places=2)
        self.assertAlmostEqual(res["normal"][1], 0.0, places=2)
        self.assertAlmostEqual(res["normal"][2], 1.0, places=2)

        out_skp = os.path.join(self.tmp_dir, "test_interactive_face.skp")
        SkpBinaryWriter.save_session(out_skp, overwrite_confirmed=True)
        SkpBinaryWriter.close_session()
        self.assertTrue(os.path.exists(out_skp))
        self.assertGreater(os.path.getsize(out_skp), 1000)

    async def test_03_fastapi_endpoints_line_and_face(self):
        """Testa os endpoints FastAPI POST /geometry/line e POST /geometry/face."""
        # 1. Abre a sessão binária
        await self.controller.open_binary_scene(self.template_path)

        # 2. Adiciona Aresta via Controller
        req_line = AddLineGeometryRequest(start_m=(1.0, 1.0, 0.0), end_m=(4.0, 1.0, 0.0))
        resp_line = await self.controller.add_line_geometry(req_line)
        self.assertTrue(resp_line.success)
        self.assertEqual(resp_line.entity["entity_type"], "Edge")
        self.assertEqual(resp_line.entity["length_m"], 3.0)

        # 3. Adiciona Face poligonal coplanar via Controller
        req_face = AddFaceGeometryRequest(points_m=[
            (1.0, 1.0, 0.0),
            (5.0, 1.0, 0.0),
            (5.0, 4.0, 0.0),
            (1.0, 4.0, 0.0),
        ])
        resp_face = await self.controller.add_face_geometry(req_face)
        self.assertTrue(resp_face.success)
        self.assertEqual(resp_face.entity["entity_type"], "Face")
        self.assertEqual(resp_face.entity["vertex_count"], 4)

    def test_04_ground_truth_validation_cpp_dll(self):
        """Validação Ground Truth: abre os arquivos gerados com a SketchUpAPI.dll oficial da Trimble."""
        face_skp = os.path.join(self.tmp_dir, "test_interactive_face.skp")
        line_skp = os.path.join(self.tmp_dir, "test_interactive_line.skp")
        self.assertTrue(os.path.exists(face_skp))
        self.assertTrue(os.path.exists(line_skp))

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

            # 1. Valida Face gerada
            model_face = api.open_model(face_skp)
            entities_face = SUEntitiesRef()
            self.assertEqual(dll.SUModelGetEntities(model_face._model, ctypes.byref(entities_face)), 0)

            num_faces = ctypes.c_size_t(0)
            self.assertEqual(dll.SUEntitiesGetNumFaces(entities_face, ctypes.byref(num_faces)), 0)

            num_edges = ctypes.c_size_t(0)
            self.assertEqual(dll.SUEntitiesGetNumEdges(entities_face, False, ctypes.byref(num_edges)), 0)

            self.assertGreaterEqual(num_faces.value, 1)
            self.assertGreaterEqual(num_edges.value, 4)
            model_face.close()

            # 2. Valida Aresta livre gerada
            model_line = api.open_model(line_skp)
            entities_line = SUEntitiesRef()
            self.assertEqual(dll.SUModelGetEntities(model_line._model, ctypes.byref(entities_line)), 0)

            num_standalone_edges = ctypes.c_size_t(0)
            self.assertEqual(dll.SUEntitiesGetNumEdges(entities_line, True, ctypes.byref(num_standalone_edges)), 0)
            self.assertGreaterEqual(num_standalone_edges.value, 1)
            model_line.close()

            print(f"\n[Ground Truth C++ API] Modelo lido com sucesso!")
            print(f" - Face SKP: {num_faces.value} faces, {num_edges.value} arestas totais")
            print(f" - Line SKP: {num_standalone_edges.value} arestas livres (standalone)")
        finally:
            api.terminate()


if __name__ == "__main__":
    unittest.main()
