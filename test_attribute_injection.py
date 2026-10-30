import os
import sys
import tempfile
import ctypes

sys.path.insert(0, r"C:\Users\Fernando\sketchup_companion")
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef, SUStringRef
from core.skp_binary_writer import SkpBinaryWriter
from core.skp_binary_reader import SkpBinaryReader

def test_bim_attribute_dictionary_injection():
    """Valida a injeção nativa de Dicionários de Atributos (BIM/Metadados)
    tanto via Pure Python (Zero DLL) quanto pela Trimble C++ API oficial."""
    src_skp = r"C:\Users\Fernando\Documents\Sem nome.skp"
    dst_skp = os.path.join(tempfile.gettempdir(), "test_model_attr_dict_official.skp")
    if os.path.exists(dst_skp):
        os.remove(dst_skp)

    # 1. Abre sessão binária Pure Python (Zero DLL)
    session = SkpBinaryWriter.open_session(src_skp)

    dict_name = "DadosOrcamento"
    attributes = {
        "PrecoUnitario": 4850.50,
        "Fabricante": "PicBrand Brinquedos",
        "CodigoSKU": "PB-PARQUE-2026",
        "Quantidade": 3,
        "AprovadoEngenharia": True
    }

    # 2. Injeta dicionário de atributos no contêiner do modelo
    res_inject = SkpBinaryWriter.set_attribute_dictionary(dict_name, attributes)
    print(f"[Zero DLL Writer] Dicionário '{dict_name}' injetado:", res_inject)

    # Salva arquivo
    saved_path = SkpBinaryWriter.save_session(dst_skp, overwrite_confirmed=True)
    SkpBinaryWriter.close_session()
    print(f"[Zero DLL Writer] Arquivo gravado em: {saved_path}")

    # 3. Leitura e validação analítica via Pure Python (Zero DLL Reader)
    all_dicts = SkpBinaryReader.read_attribute_dictionaries(saved_path)
    print(f"[Zero DLL Reader] Dicionários encontrados no modelo: {list(all_dicts.keys())}")
    assert dict_name in all_dicts, f"Dicionário '{dict_name}' não encontrado pelo leitor nativo!"
    read_attrs = all_dicts[dict_name]
    print(f"[Zero DLL Reader] Atributos lidos:", read_attrs)

    assert read_attrs["PrecoUnitario"] == 4850.50
    assert read_attrs["Fabricante"] == "PicBrand Brinquedos"
    assert read_attrs["CodigoSKU"] == "PB-PARQUE-2026"
    assert read_attrs["Quantidade"] == 3
    assert read_attrs["AprovadoEngenharia"] is True
    print(">>> [Zero DLL Reader] 100% de integridade nos tipos bool, int32, double, string! <<<")

    # 4. Validação Cruzada com a Trimble C++ API Oficial (SketchUpAPI.dll)
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(saved_path)
        dll = api._dll

        class SUAttributeDictionaryRef(ctypes.Structure):
            _fields_ = [("ptr", ctypes.c_void_p)]
        class SUTypedValueRef(ctypes.Structure):
            _fields_ = [("ptr", ctypes.c_void_p)]

        dll.SUModelGetAttributeDictionary.restype = ctypes.c_int
        dll.SUModelGetAttributeDictionary.argtypes = [SUModelRef, ctypes.c_char_p, ctypes.POINTER(SUAttributeDictionaryRef)]
        dll.SUAttributeDictionaryGetNumKeys.restype = ctypes.c_int
        dll.SUAttributeDictionaryGetNumKeys.argtypes = [SUAttributeDictionaryRef, ctypes.POINTER(ctypes.c_size_t)]
        dll.SUAttributeDictionaryGetValue.restype = ctypes.c_int
        dll.SUAttributeDictionaryGetValue.argtypes = [SUAttributeDictionaryRef, ctypes.c_char_p, ctypes.POINTER(SUTypedValueRef)]

        dll.SUTypedValueCreate.restype = ctypes.c_int
        dll.SUTypedValueCreate.argtypes = [ctypes.POINTER(SUTypedValueRef)]
        dll.SUTypedValueRelease.restype = ctypes.c_int
        dll.SUTypedValueRelease.argtypes = [ctypes.POINTER(SUTypedValueRef)]
        dll.SUTypedValueGetDouble.restype = ctypes.c_int
        dll.SUTypedValueGetDouble.argtypes = [SUTypedValueRef, ctypes.POINTER(ctypes.c_double)]
        dll.SUTypedValueGetInt32.restype = ctypes.c_int
        dll.SUTypedValueGetInt32.argtypes = [SUTypedValueRef, ctypes.POINTER(ctypes.c_int32)]
        dll.SUTypedValueGetString.restype = ctypes.c_int
        dll.SUTypedValueGetString.argtypes = [SUTypedValueRef, ctypes.POINTER(SUStringRef)]
        dll.SUTypedValueGetBool.restype = ctypes.c_int
        dll.SUTypedValueGetBool.argtypes = [SUTypedValueRef, ctypes.POINTER(ctypes.c_bool)]

        attr_dict = SUAttributeDictionaryRef()
        res = dll.SUModelGetAttributeDictionary(model.raw_ref, dict_name.encode("utf-8"), ctypes.byref(attr_dict))
        print(f"[Trimble C++ API] SUModelGetAttributeDictionary('{dict_name}'): status={res}")
        assert res == 0 and attr_dict.ptr is not None

        num_keys = ctypes.c_size_t()
        dll.SUAttributeDictionaryGetNumKeys(attr_dict, ctypes.byref(num_keys))
        print(f"[Trimble C++ API] Número de chaves: {num_keys.value} (Esperado: {len(attributes)})")
        assert num_keys.value == len(attributes)

        # Checa PrecoUnitario
        v_ref = SUTypedValueRef()
        dll.SUTypedValueCreate(ctypes.byref(v_ref))
        dll.SUAttributeDictionaryGetValue(attr_dict, b"PrecoUnitario", ctypes.byref(v_ref))
        d_val = ctypes.c_double()
        dll.SUTypedValueGetDouble(v_ref, ctypes.byref(d_val))
        dll.SUTypedValueRelease(ctypes.byref(v_ref))
        print(f"[Trimble C++ API] PrecoUnitario: {d_val.value}")
        assert abs(d_val.value - 4850.50) < 0.001

        # Checa Fabricante
        v_ref2 = SUTypedValueRef()
        dll.SUTypedValueCreate(ctypes.byref(v_ref2))
        dll.SUAttributeDictionaryGetValue(attr_dict, b"Fabricante", ctypes.byref(v_ref2))
        s_ref = SUStringRef()
        dll.SUStringCreate(ctypes.byref(s_ref))
        dll.SUTypedValueGetString(v_ref2, ctypes.byref(s_ref))
        slen = ctypes.c_size_t()
        dll.SUStringGetUTF8Length(s_ref, ctypes.byref(slen))
        sbuf = ctypes.create_string_buffer(slen.value + 1)
        dll.SUStringGetUTF8(s_ref, slen.value + 1, sbuf, ctypes.byref(slen))
        fab_str = sbuf.value.decode("utf-8")
        dll.SUStringRelease(ctypes.byref(s_ref))
        dll.SUTypedValueRelease(ctypes.byref(v_ref2))
        print(f"[Trimble C++ API] Fabricante: '{fab_str}'")
        assert fab_str == "PicBrand Brinquedos"

        # Checa Quantidade
        v_ref3 = SUTypedValueRef()
        dll.SUTypedValueCreate(ctypes.byref(v_ref3))
        dll.SUAttributeDictionaryGetValue(attr_dict, b"Quantidade", ctypes.byref(v_ref3))
        i_val = ctypes.c_int32()
        dll.SUTypedValueGetInt32(v_ref3, ctypes.byref(i_val))
        dll.SUTypedValueRelease(ctypes.byref(v_ref3))
        print(f"[Trimble C++ API] Quantidade: {i_val.value}")
        assert i_val.value == 3

        # Checa AprovadoEngenharia
        v_ref4 = SUTypedValueRef()
        dll.SUTypedValueCreate(ctypes.byref(v_ref4))
        dll.SUAttributeDictionaryGetValue(attr_dict, b"AprovadoEngenharia", ctypes.byref(v_ref4))
        b_val = ctypes.c_bool()
        dll.SUTypedValueGetBool(v_ref4, ctypes.byref(b_val))
        dll.SUTypedValueRelease(ctypes.byref(v_ref4))
        print(f"[Trimble C++ API] AprovadoEngenharia: {b_val.value}")
        assert b_val.value is True

        print(">>> [TRIMBLE C++ API] VALIDAÇÃO CRUZADA 100% BEM-SUCEDIDA! MODELO CONFORME E HOMOLOGADO! <<<")
        model.close()
    finally:
        api.terminate()

if __name__ == "__main__":
    test_bim_attribute_dictionary_injection()
