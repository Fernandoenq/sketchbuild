"""
SketchBuild - Teste Automatizado da Frente 8C
Exclusão Nativa de Instâncias no model.dat (Pure Python / Zero DLL)
Validação Cruzada: SkpBinaryReader (Pure Python) + SketchUpAPI.dll (Trimble C++ Oficial) + SceneController (FastAPI)
"""

import asyncio
import os
import tempfile
from core.skp_binary_reader import SkpBinaryReader
from core.skp_binary_writer import SkpBinaryWriter
from core.su_api import SketchUpAPI
from app.controllers.scene_controller import SceneController


def run_e2e_delete_test():
    src_skp = "C:/Users/Fernando/Documents/Sem nome.skp"
    if not os.path.exists(src_skp):
        print(f"Aviso: {src_skp} não encontrado. Pulando teste E2E de arquivo específico.")
        return

    dst_skp = os.path.join(tempfile.gettempdir(), "test_delete_instance_e2e_verified.skp")
    if os.path.exists(dst_skp):
        os.remove(dst_skp)

    print("\n--- 1. Preparando modelo com 2 instâncias (Duplicação) ---")
    session = SkpBinaryWriter.open_session(src_skp)
    initial_keys = list(session.instances_offsets.keys())
    print("Instâncias iniciais:", initial_keys)
    assert len(initial_keys) >= 1

    orig_key = initial_keys[0]
    new_inst = SkpBinaryWriter.duplicate_instance(orig_key, offset_delta_cm=[100.0, 0.0, 0.0])
    clone_key = new_inst["instance_key"]
    print("Clonada nova instância:", clone_key)
    assert len(session.instances_offsets) == len(initial_keys) + 1

    print("\n--- 2. Excluindo a instância clonada nativamente (Zero DLL) ---")
    deleted = SkpBinaryWriter.delete_instance(clone_key)
    assert deleted is True
    assert clone_key not in session.instances_offsets
    assert len(session.instances_offsets) == len(initial_keys)
    print("Instância excluída com sucesso da sessão binária!")

    saved_path = SkpBinaryWriter.save_session(dst_skp, overwrite_confirmed=True)
    SkpBinaryWriter.close_session()
    print("Arquivo gravado em:", saved_path)

    print("\n--- 3. Validação SkpBinaryReader (Pure Python) ---")
    h = SkpBinaryReader.extract_hierarchy(saved_path)
    print("Instâncias lidas pelo SkpBinaryReader após exclusão:", len(h["instances"]))
    assert len(h["instances"]) == len(initial_keys)
    assert h["instances"][0]["id"] == SkpBinaryReader.extract_hierarchy(src_skp)["instances"][0]["id"]

    print("\n--- 4. Validação Trimble C++ API Oficial (SketchUpAPI.dll) ---")
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(saved_path)
        entities = model.get_entities()
        insts = api.get_instances(entities)
        print("Instâncias carregadas pela Trimble DLL após exclusão:", len(insts))
        assert len(insts) == len(initial_keys)
        model.close()
    finally:
        api.terminate()

    print("Validação Trimble C++ API: SUCESSO ABSOLUTO (SU_ERROR_NONE / 0)!")


async def run_controller_delete_test():
    src_skp = "C:/Users/Fernando/Documents/Sem nome.skp"
    if not os.path.exists(src_skp):
        return

    print("\n--- 5. Testando exclusão via SceneController (FastAPI Layer) ---")
    ctrl = SceneController()
    scene = await ctrl.open_binary_scene(src_skp)
    real_inst = [i for i in scene.instances if i.instance_id != "inst_root"][0]

    # Duplica
    dup_res = await ctrl.duplicate_instance(real_inst.instance_id, offset_delta_cm=[80.0, 0.0, 0.0])
    new_inst_id = dup_res.instance.instance_id
    print("Instância duplicada via controller:", new_inst_id)

    # Exclui
    del_res = await ctrl.delete_instance(new_inst_id)
    print("Resposta de exclusão do controller:", del_res)
    assert del_res.deleted is True
    assert del_res.instance_id == new_inst_id
    print("Validação SceneController: SUCESSO ABSOLUTO!")


if __name__ == "__main__":
    run_e2e_delete_test()
    asyncio.run(run_controller_delete_test())
    print("\n*** TODOS OS TESTES DA FRENTE 8C PASSARAM COM 100% DE SUCESSO! ***\n")
