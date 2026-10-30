import os
import sys
import ctypes
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.skp_binary_writer import SkpBinaryWriter
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef


class SUEntitiesRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class TestCylinderAndExtrusion(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")

    def test_01_add_cylinder_brep(self):
        """Valida criação de Cilindro 3D Manifold (Frente 14 - Zero DLL)."""
        SkpBinaryWriter.open_session(self.template_path)
        res = SkpBinaryWriter.add_cylinder(radius_m=0.3, height_m=2.0, num_segments=12)

        self.assertEqual(res["entity_type"], "Cylinder")
        self.assertEqual(res["vertex_count"], 24)
        self.assertEqual(res["edge_count"], 36)
        self.assertEqual(res["face_count"], 14)  # 1 base + 1 topo + 12 laterais

        out_skp = os.path.join(self.tmp_dir, "test_cylinder_out.skp")
        SkpBinaryWriter.save_session(out_skp, overwrite_confirmed=True)
        SkpBinaryWriter.close_session()

        # Validação Ground Truth C++ API
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

            print(f"\n[Ground Truth C++ API] Cilindro: {num_faces.value} faces, {num_edges.value} arestas oficiais!")
            self.assertGreaterEqual(num_faces.value, 14)
            self.assertGreaterEqual(num_edges.value, 36)
            model.close()
        finally:
            api.terminate()

    def test_02_extrude_face_pushpull(self):
        """Valida a extrusão Push/Pull de face coplanar para sólido 3D (Frente 24 - Zero DLL)."""
        SkpBinaryWriter.open_session(self.template_path)
        # Face quadrada de 1.5 x 1.5m no chão
        pts = [
            (0.0, 0.0, 0.0),
            (1.5, 0.0, 0.0),
            (1.5, 1.5, 0.0),
            (0.0, 1.5, 0.0),
        ]
        # Extrude 2.5 metros para cima ao longo de Z (+Normal)
        res = SkpBinaryWriter.extrude_face(pts, distance_m=2.5, normal_xyz=(0.0, 0.0, 1.0))

        self.assertEqual(res["entity_type"], "Extrusion")
        self.assertEqual(res["vertex_count"], 8)
        self.assertEqual(res["face_count"], 6)
        self.assertEqual(res["edge_count"], 12)

        out_skp = os.path.join(self.tmp_dir, "test_pushpull_extrusion.skp")
        SkpBinaryWriter.save_session(out_skp, overwrite_confirmed=True)
        SkpBinaryWriter.close_session()

        # Validação Ground Truth C++ API
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

            print(f"[Ground Truth C++ API] Extrusão Push/Pull: {num_faces.value} faces, {num_edges.value} arestas oficiais!")
            self.assertGreaterEqual(num_faces.value, 6)
            self.assertGreaterEqual(num_edges.value, 12)
            model.close()
        finally:
            api.terminate()


if __name__ == "__main__":
    unittest.main()
