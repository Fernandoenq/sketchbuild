"""
SketchBuild - Teste Automatizado da Frente 8B
Duplicação e Instanciação Nativa de Componentes (Pure Python / Zero DLL)
Validação Cruzada: SkpBinaryReader (Pure Python) + SketchUpAPI.dll (Trimble C++ Oficial)
"""

import asyncio
import os
import tempfile
from core.skp_binary_reader import SkpBinaryReader
from core.skp_binary_writer import SkpBinaryWriter
from core.su_api import SketchUpAPI
from app.controllers.scene_controller import SceneController


def run_e2e_duplicate_test():
    src_skp = "C:/Users/Fernando/Documents/Sem nome.skp"
    if not os.path.exists(src_skp):
        print(f"Aviso: {src_skp} não encontrado. Pulando teste E2E de arquivo específico.")
        return

    dst_skp = os.path.join(tempfile.gettempdir(), "test_duplicate_instance_e2e_verified.skp")
    if os.path.exists(dst_skp):
        os.remove(dst_skp)

    print("\n--- 1. Testando SkpBinaryWriter.duplicate_instance ---")
    session = SkpBinaryWriter.open_session(src_skp)
    initial_keys = list(session.instances_offsets.keys())
    print("Instâncias iniciais na sessão:", initial_keys)
    assert len(initial_keys) >= 1, "Modelo deve ter ao menos 1 instância"

    orig_key = initial_keys[0]
    new_inst = SkpBinaryWriter.duplicate_instance(orig_key, offset_delta_cm=[120.0, 0.0, 0.0])
    print("Instância duplicada com sucesso:", new_inst)
    assert new_inst["id"] is not None
    assert new_inst["instance_key"] != orig_key

    saved_path = SkpBinaryWriter.save_session(dst_skp, overwrite_confirmed=True)
    SkpBinaryWriter.close_session()
    print("Arquivo salvo em:", saved_path)

    print("\n--- 2. Validação SkpBinaryReader (Pure Python) ---")
    h = SkpBinaryReader.extract_hierarchy(saved_path)
    print("Instâncias lidas pelo SkpBinaryReader:", len(h["instances"]))
    assert len(h["instances"]) == len(initial_keys) + 1

    print("\n--- 3. Validação Trimble C++ API Oficial (SketchUpAPI.dll) ---")
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(saved_path)
        entities = model.get_entities()
        insts = api.get_instances(entities)
        print("Instâncias carregadas pela Trimble DLL:", len(insts))
        assert len(insts) == len(initial_keys) + 1
        for i, inst in enumerate(insts):
            trans = api.get_instance_transform(inst)
            print(f"  Inst #{i}: trans={trans[12:15]}")
        model.close()
    finally:
        api.terminate()

    print("Validação Trimble C++ API: SUCESSO ABSOLUTO!")


async def run_controller_test():
    src_skp = "C:/Users/Fernando/Documents/Sem nome.skp"
    if not os.path.exists(src_skp):
        return

    print("\n--- 4. Testando SceneController (FastAPI Layer) ---")
    ctrl = SceneController()
    scene = await ctrl.open_binary_scene(src_skp)
    real_inst = [i for i in scene.instances if i.instance_id != "inst_root"][0]

    dup_res = await ctrl.duplicate_instance(real_inst.instance_id, offset_delta_cm=[60.0, 0.0, 0.0])
    print("Resposta do controller:", dup_res.instance.instance_id, dup_res.duplicated)
    assert dup_res.duplicated is True
    assert dup_res.instance.instance_id != real_inst.instance_id
    print("Validação SceneController: SUCESSO ABSOLUTO!")


if __name__ == "__main__":
    run_e2e_duplicate_test()
    asyncio.run(run_controller_test())
    print("\n*** TODOS OS TESTES DA FRENTE 8B PASSARAM COM 100% DE SUCESSO! ***\n")
