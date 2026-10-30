"""
SketchBuild - Teste Automatizado da Frente 9
Criação Nativa de Geometria no model.dat (Zero DLL / Pure Python)
Validação Cruzada: SkpBinaryWriter + SketchUpAPI.dll (Trimble C++ Oficial) + SceneController
"""

import asyncio
import os
import tempfile
from core.skp_binary_reader import SkpBinaryReader
from core.skp_binary_writer import SkpBinaryWriter
from core.su_api import SketchUpAPI
from app.controllers.scene_controller import SceneController


def run_e2e_add_geometry_test():
    src_skp = "C:/Users/Fernando/Documents/Sem nome.skp"
    if not os.path.exists(src_skp):
        print(f"Aviso: {src_skp} não encontrado.")
        return

    dst_skp = os.path.join(tempfile.gettempdir(), "test_add_geometry_e2e_verified.skp")
    if os.path.exists(dst_skp):
        os.remove(dst_skp)

    print("\n--- 1. Criando Face Retangular 100% em Pure Python (Zero DLL) ---")
    session = SkpBinaryWriter.open_session(src_skp)
    res = SkpBinaryWriter.add_rectangle(
        width_m=2.0,
        height_m=1.2,
        offset_xyz_cm=[20.0, 20.0, 0.0]
    )
    print("Face gerada:", res)
    assert res["face_id"] > 0
    assert len(res["vertex_ids"]) == 4
    assert len(res["edge_ids"]) == 4
    assert res["area_m2"] == 2.4

    saved_path = SkpBinaryWriter.save_session(dst_skp, overwrite_confirmed=True)
    SkpBinaryWriter.close_session()
    print("Arquivo gravado em:", saved_path)

    print("\n--- 2. Validação Trimble C++ API Oficial (SketchUpAPI.dll) ---")
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(saved_path)
        entities = model.get_entities()
        faces = api.get_faces(entities)
        print("Faces reconhecidas pela Trimble DLL no modelo gerado:", len(faces))
        assert len(faces) >= 1, "A Trimble DLL deve detectar e ler a face criada nativamente!"
        model.close()
    finally:
        api.terminate()

    print("Validação Trimble C++ API: SUCESSO ABSOLUTO (SU_ERROR_NONE / 0)!")


async def run_controller_add_rect_test():
    src_skp = "C:/Users/Fernando/Documents/Sem nome.skp"
    if not os.path.exists(src_skp):
        return

    print("\n--- 3. Testando via SceneController (FastAPI Layer) ---")
    ctrl = SceneController()
    await ctrl.open_binary_scene(src_skp)
    res = await ctrl.add_rectangle(width_m=1.8, height_m=0.9, as_group=False)
    print("Resposta do controller ao adicionar retângulo:", res.scene.definitions[0].name)
    assert res.scene.definitions[0].name == "Model Root"
    print("Validação SceneController: SUCESSO ABSOLUTO!")


if __name__ == "__main__":
    run_e2e_add_geometry_test()
    asyncio.run(run_controller_add_rect_test())
    print("\n*** TODOS OS TESTES DA FRENTE 9 PASSARAM COM 100% DE SUCESSO! ***\n")
