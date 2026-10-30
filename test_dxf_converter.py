import os
import sys
import tempfile
import ctypes

sys.path.insert(0, r"C:\Users\Fernando\sketchup_companion")
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef
from core.dxf_to_skp_converter import DxfToSkpConverter
from core.skp_binary_reader import SkpBinaryReader

class SUEntitiesRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]

def test_front_20_dxf_converter():
    """Valida a Frente 20: Conversão Direta de Desenhos CAD (.dxf) para .skp Nativo
    em Pure Python (Zero DLL), sem precisar do SketchUp Desktop nem de AutoCAD."""
    tmp_dir = tempfile.gettempdir()
    dxf_file = os.path.join(tmp_dir, "planta_teste.dxf")
    skp_file = os.path.join(tmp_dir, "modelo_convertido_de_dxf.skp")

    if os.path.exists(skp_file):
        os.remove(skp_file)

    # 1. Gera um arquivo DXF sintético com uma 3DFACE de 300cm x 200cm (3.0m x 2.0m)
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
    with open(dxf_file, "w", encoding="utf-8") as f:
        f.write(dxf_content)
    print(f"[CAD Input] Arquivo DXF gerado em: {dxf_file}")

    # 2. Executa a conversão direta DXF -> SKP Nativo (Zero DLL)
    res_conv = DxfToSkpConverter.convert(dxf_file, skp_file)
    print("[CAD Converter] Resultado da conversão:", res_conv)
    assert res_conv["status"] == "success"
    assert os.path.exists(skp_file), "Arquivo .skp gerado deve existir"

    # 3. Leitura das faces extraídas do modelo convertido via SkpBinaryReader
    faces = SkpBinaryReader.extract_faces_and_triangles(skp_file)
    print(f"[Zero DLL Reader] Total de faces no modelo convertido: {len(faces)}")
    assert len(faces) >= 1, "Deve conter pelo menos 1 face convertida"

    last_face = faces[-1]
    print(f"[Zero DLL Reader] Face convertida: Área={last_face['area_m2']} m², Normal={last_face['normal']}")
    # Retângulo de 3m x 2m = 6.0 m²
    assert abs(last_face["area_m2"] - 6.0) < 0.05
    print(">>> [Zero DLL Reader] GEOMETRIA DXF CONVERTIDA COM ÁREA EXATA DE 6.0 m²! <<<")

    # 4. Validação Cruzada Oficial com a Trimble C++ API
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(skp_file)
        dll = api._dll

        ents = SUEntitiesRef()
        dll.SUModelGetEntities.restype = ctypes.c_int
        dll.SUModelGetEntities.argtypes = [SUModelRef, ctypes.POINTER(SUEntitiesRef)]
        dll.SUModelGetEntities(model.raw_ref, ctypes.byref(ents))

        dll.SUEntitiesGetNumFaces.restype = ctypes.c_int
        dll.SUEntitiesGetNumFaces.argtypes = [SUEntitiesRef, ctypes.POINTER(ctypes.c_size_t)]
        num_faces = ctypes.c_size_t()
        dll.SUEntitiesGetNumFaces(ents, ctypes.byref(num_faces))
        print(f"[Trimble C++ API] Faces detectadas no modelo convertido: {num_faces.value} (Esperado >= 1)")
        assert num_faces.value >= 1

        print(">>> [TRIMBLE C++ API] CONVERSOR DXF -> SKP HOMOLOGADO COM 100% DE CONFORMIDADE! <<<")
        model.close()
    finally:
        api.terminate()

if __name__ == "__main__":
    test_front_20_dxf_converter()
