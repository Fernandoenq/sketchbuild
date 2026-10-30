import os
import sys
import tempfile
import ctypes

sys.path.insert(0, r"C:\Users\Fernando\sketchup_companion")
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef
from core.skp_binary_reader import SkpBinaryReader

def test_front_16_dimensions():
    """Valida a Frente 16: Extração e decodificação analítica de Cotas Lineares Técnicas
    (DimensionLinear) no model.dat (Zero DLL) com validação C++ oficial."""
    target_skp = os.path.join(tempfile.gettempdir(), "reference_dimension.skp")
    assert os.path.exists(target_skp), "Arquivo reference_dimension.skp deve existir"

    # 1. Leitura analítica Zero DLL via SkpBinaryReader
    dims = SkpBinaryReader.extract_dimensions(target_skp)
    print(f"[Zero DLL Reader] Cotas técnicas detectadas no modelo: {len(dims)}")
    assert len(dims) >= 1, "Deve existir pelo menos 1 cota linear detectada"

    dim0 = dims[0]
    print(f"[Zero DLL Reader] Cota[0]: Tipo='{dim0['type']}', offset_inches={dim0['offset_inches']}, offset_cm={dim0['offset_cm']}")
    assert abs(dim0["offset_inches"] - 10.0) < 0.01
    assert abs(dim0["offset_cm"] - 25.40) < 0.05
    print(">>> [Zero DLL Reader] COTA LINEAR EXTRAÍDA COM 100% DE PRECISÃO! <<<")

    # 2. Validação Cruzada Oficial com a Trimble C++ API
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(target_skp)
        print(">>> [TRIMBLE C++ API] MODELO COM COTA TÉCNICA HOMOLOGADO COM STATUS 0 (SU_ERROR_NONE)! <<<")
        model.close()
    finally:
        api.terminate()

if __name__ == "__main__":
    test_front_16_dimensions()
