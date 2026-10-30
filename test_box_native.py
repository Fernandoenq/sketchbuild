import os
import sys
import tempfile
import ctypes

sys.path.insert(0, r"C:\Users\Fernando\sketchup_companion")
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef
from core.skp_binary_writer import SkpBinaryWriter
from core.skp_binary_reader import SkpBinaryReader

class SUEntitiesRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]

def test_front_13_box_push_pull():
    """Valida a Frente 13: Push/Pull Nativo e criação de Sólidos 3D Manifold
    (6 faces, 12 arestas, 8 vértices) em Pure Python (Zero DLL) com validação C++ oficial."""
    src_skp = r"C:\Users\Fernando\Documents\Sem nome.skp"
    dst_skp = os.path.join(tempfile.gettempdir(), "test_box_front_13.skp")
    if os.path.exists(dst_skp):
        os.remove(dst_skp)

    # 1. Cria a caixa usando o método nativo Zero DLL
    session = SkpBinaryWriter.open_session(src_skp)
    box_info = SkpBinaryWriter.add_box(
        width_m=2.0,
        length_m=1.5,
        height_m=1.0,
        offset_xyz_cm=[0.0, 0.0, 0.0]
    )
    print("[Zero DLL Writer] Caixa 3D criada:", box_info)

    saved_path = SkpBinaryWriter.save_session(dst_skp, overwrite_confirmed=True)
    SkpBinaryWriter.close_session()
    print("[Zero DLL Writer] Arquivo salvo em:", saved_path)

    # 2. Leitura e cálculo analítico via SkpBinaryReader
    faces = SkpBinaryReader.extract_faces_and_triangles(saved_path)
    print(f"[Zero DLL Reader] Total de faces no modelo: {len(faces)}")
    assert len(faces) >= 6, f"Esperado pelo menos 6 faces, encontrado {len(faces)}"

    box_faces = faces[-6:]
    total_area_m2 = sum(f["area_m2"] for f in box_faces)
    print(f"[Zero DLL Reader] Área superficial das 6 faces do sólido: {total_area_m2:.2f} m² (Esperado: 13.00 m²)")
    assert abs(total_area_m2 - 13.0) < 0.01

    # 3. Validação Cruzada Oficial com a Trimble C++ API
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(saved_path)
        dll = api._dll

        dll.SUModelGetEntities.restype = ctypes.c_int
        dll.SUModelGetEntities.argtypes = [SUModelRef, ctypes.POINTER(SUEntitiesRef)]
        dll.SUEntitiesGetNumFaces.restype = ctypes.c_int
        dll.SUEntitiesGetNumFaces.argtypes = [SUEntitiesRef, ctypes.POINTER(ctypes.c_size_t)]
        dll.SUEntitiesGetNumEdges.restype = ctypes.c_int
        dll.SUEntitiesGetNumEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.POINTER(ctypes.c_size_t)]

        entities = SUEntitiesRef()
        dll.SUModelGetEntities(model.raw_ref, ctypes.byref(entities))

        num_faces = ctypes.c_size_t()
        dll.SUEntitiesGetNumFaces(entities, ctypes.byref(num_faces))
        print(f"[Trimble C++ API] Faces detectadas no modelo: {num_faces.value} (Esperado: 6)")
        assert num_faces.value == 6

        num_edges = ctypes.c_size_t()
        dll.SUEntitiesGetNumEdges(entities, False, ctypes.byref(num_edges))
        print(f"[Trimble C++ API] Arestas totais detectadas no modelo: {num_edges.value} (Esperado: 12)")
        assert num_edges.value == 12

        print(">>> [TRIMBLE C++ API] FRENTE 13 CONCLUÍDA COM 100% DE CONFORMIDADE! <<<")
        model.close()
    finally:
        api.terminate()

if __name__ == "__main__":
    test_front_13_box_push_pull()
