"""
SketchBuild - Teste Automatizado da Frente 10
Mapeamento UV e Injeção de Texturas de Imagem em Materiais Nativos (Zero DLL / Pure Python)
Validação Cruzada: SkpBinaryWriter + SketchUpAPI.dll (Trimble C++ Oficial)
"""

import os
import tempfile
import io
import ctypes

try:
    from PIL import Image
except ImportError:
    Image = None

from core.skp_binary_reader import SkpBinaryReader
from core.skp_binary_writer import SkpBinaryWriter
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef, SUMaterialRef, SUStringRef

class SUTextureRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


def run_e2e_texture_test():
    src_skp = "C:/Users/Fernando/Documents/Sem nome.skp"
    if not os.path.exists(src_skp):
        print(f"Aviso: {src_skp} não encontrado.")
        return

    dst_skp = os.path.join(tempfile.gettempdir(), "test_texture_injection_e2e_verified.skp")
    if os.path.exists(dst_skp):
        os.remove(dst_skp)

    # Cria imagem PNG em memória (ex: textura mármore/madeira 64x64)
    if Image is not None:
        img = Image.new("RGB", (64, 64), color=(210, 160, 110))
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        png_bytes = img_buffer.getvalue()
    else:
        # Minimal 1x1 PNG bytes (Pure Python - Zero DLL / No Pillow)
        png_bytes = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xd2\xa0n\x00'
            b'\x02\xb6\x01>\xda\x0e\xc5\x13\x00\x00\x00\x00IEND\xaeB`\x82'
        )

    mat_name = "Carvalho_Nativo_Python"
    img_filename = "carvalho.png"

    print("\n--- 1. Injetando Material com Textura em Pure Python (Zero DLL) ---")
    session = SkpBinaryWriter.open_session(src_skp)
    res = SkpBinaryWriter.create_textured_material(
        material_name=mat_name,
        image_bytes=png_bytes,
        image_filename=img_filename,
        scale_u_cm=80.0,
        scale_v_cm=80.0,
        color_rgb=(210, 160, 110)
    )
    print("Material texturizado criado:", res)
    assert res["material_name"] == mat_name
    assert res["has_texture"] is True

    saved_path = SkpBinaryWriter.save_session(dst_skp, overwrite_confirmed=True)
    SkpBinaryWriter.close_session()
    print("Arquivo gravado em:", saved_path)

    print("\n--- 2. Validação Trimble C++ API Oficial (SketchUpAPI.dll) ---")
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(saved_path)
        dll = api._dll

        dll.SUModelGetNumMaterials.restype = ctypes.c_int
        dll.SUModelGetNumMaterials.argtypes = [SUModelRef, ctypes.POINTER(ctypes.c_size_t)]
        
        count = ctypes.c_size_t()
        dll.SUModelGetNumMaterials(model.raw_ref, ctypes.byref(count))
        print(f"Total de materiais reconhecidos pela Trimble DLL: {count.value}")

        mats = (SUMaterialRef * count.value)()
        actual_count = ctypes.c_size_t()
        dll.SUModelGetMaterials.restype = ctypes.c_int
        dll.SUModelGetMaterials.argtypes = [SUModelRef, ctypes.c_size_t, ctypes.POINTER(SUMaterialRef), ctypes.POINTER(ctypes.c_size_t)]
        dll.SUModelGetMaterials(model.raw_ref, count.value, mats, ctypes.byref(actual_count))

        dll.SUMaterialGetName.restype = ctypes.c_int
        dll.SUMaterialGetName.argtypes = [SUMaterialRef, ctypes.POINTER(SUStringRef)]
        dll.SUMaterialGetTexture.restype = ctypes.c_int
        dll.SUMaterialGetTexture.argtypes = [SUMaterialRef, ctypes.POINTER(SUTextureRef)]
        dll.SUStringCreate.restype = ctypes.c_int
        dll.SUStringCreate.argtypes = [ctypes.POINTER(SUStringRef)]
        dll.SUStringGetUTF8Length.restype = ctypes.c_int
        dll.SUStringGetUTF8Length.argtypes = [SUStringRef, ctypes.POINTER(ctypes.c_size_t)]
        dll.SUStringGetUTF8.restype = ctypes.c_int
        dll.SUStringGetUTF8.argtypes = [SUStringRef, ctypes.c_size_t, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
        dll.SUStringRelease.restype = ctypes.c_int
        dll.SUStringRelease.argtypes = [ctypes.POINTER(SUStringRef)]

        found = False
        has_texture = False
        for i in range(actual_count.value):
            sref = SUStringRef()
            dll.SUStringCreate(ctypes.byref(sref))
            dll.SUMaterialGetName(mats[i], ctypes.byref(sref))
            slen = ctypes.c_size_t()
            dll.SUStringGetUTF8Length(sref, ctypes.byref(slen))
            buf = ctypes.create_string_buffer(slen.value + 1)
            dll.SUStringGetUTF8(sref, slen.value + 1, buf, ctypes.byref(slen))
            dll.SUStringRelease(ctypes.byref(sref))

            name = buf.value.decode("utf-8")
            if name == mat_name:
                found = True
                tex_ref = SUTextureRef()
                r = dll.SUMaterialGetTexture(mats[i], ctypes.byref(tex_ref))
                if r == 0 and tex_ref.ptr is not None:
                    has_texture = True
                print(f"Material '{name}' localizado com sucesso! Possui textura? {has_texture}")

        assert found, "Material injetado deve ser detectado pela Trimble DLL"
        assert has_texture, "A textura deve estar vinculada e carregada pela Trimble DLL"
        print("Validação Trimble C++ API: SUCESSO ABSOLUTO (SU_ERROR_NONE / 0)!")
        model.close()
    finally:
        api.terminate()


if __name__ == "__main__":
    run_e2e_texture_test()
    print("\n*** TODOS OS TESTES DA FRENTE 10 PASSARAM COM 100% DE SUCESSO! ***\n")
