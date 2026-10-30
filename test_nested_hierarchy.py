import os
import sys
import tempfile
import ctypes

sys.path.insert(0, r"C:\Users\Fernando\sketchup_companion")
from core.su_api import SketchUpAPI
from core.su_types import SUModelRef, SUStringRef
from core.skp_binary_reader import SkpBinaryReader

class SUEntitiesRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]
class SUGroupRef(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]

def test_front_15_nested_hierarchy():
    """Valida a Frente 15: Leitura e extração analítica de Grupos e Hierarquias Aninhadas
    (Submontagens / Outliner Tree) em Pure Python (Zero DLL) com validação C++ oficial."""
    target_skp = os.path.join(tempfile.gettempdir(), "reference_nested_groups.skp")
    assert os.path.exists(target_skp), "Arquivo reference_nested_groups.skp deve existir"

    # 1. Leitura analítica da árvore de montagem Zero DLL
    tree = SkpBinaryReader.build_assembly_tree(target_skp)
    print("[Zero DLL Reader] Árvore de Montagem extraída com sucesso:")
    print(f"  Nome Raiz: {tree['name']}")
    print(f"  Total de instâncias mapeadas: {tree['total_instances']}")
    print(f"  Nós raiz: {tree['root_nodes_count']}")

    assert tree["total_instances"] >= 2, "Devem existir pelo menos 2 instâncias (Pai e Filho)"
    assert len(tree["children"]) >= 1, "Deve existir pelo menos 1 nó raiz"

    parent_node = tree["children"][0]
    print(f"  Nó Pai: id={parent_node['id']}, nome='{parent_node['name']}', is_group={parent_node['is_group']}")
    assert parent_node["name"] == "Grupo_Pai_Estrutura"
    assert parent_node["is_group"] is True

    print(f"  Subgrupos filhos dentro do Pai: {len(parent_node['children'])}")
    assert len(parent_node["children"]) == 1, "O Grupo Pai deve conter exatamente 1 subgrupo filho"

    child_node = parent_node["children"][0]
    print(f"  Nó Filho: id={child_node['id']}, nome='{child_node['name']}', is_group={child_node['is_group']}")
    assert child_node["name"] == "Subgrupo_Filho_Pilar"
    assert child_node["is_group"] is True
    print(">>> [Zero DLL Reader] HIERARQUIA ANINHADA PAI-FILHO RECONHECIDA COM 100% DE EXATIDÃO! <<<")

    # 2. Validação Cruzada com a Trimble C++ API
    api = SketchUpAPI()
    api.initialize()
    try:
        model = api.open_model(target_skp)
        dll = api._dll

        ents = SUEntitiesRef()
        dll.SUModelGetEntities.restype = ctypes.c_int
        dll.SUModelGetEntities.argtypes = [SUModelRef, ctypes.POINTER(SUEntitiesRef)]
        dll.SUModelGetEntities(model.raw_ref, ctypes.byref(ents))

        dll.SUEntitiesGetNumGroups.restype = ctypes.c_int
        dll.SUEntitiesGetNumGroups.argtypes = [SUEntitiesRef, ctypes.POINTER(ctypes.c_size_t)]
        dll.SUEntitiesGetGroups.restype = ctypes.c_int
        dll.SUEntitiesGetGroups.argtypes = [SUEntitiesRef, ctypes.c_size_t, ctypes.POINTER(SUGroupRef), ctypes.POINTER(ctypes.c_size_t)]

        num_g = ctypes.c_size_t()
        dll.SUEntitiesGetNumGroups(ents, ctypes.byref(num_g))
        print(f"[Trimble C++ API] Grupos no nível raiz: {num_g.value} (Esperado == 1)")
        assert num_g.value == 1

        dll.SUGroupGetName.restype = ctypes.c_int
        dll.SUGroupGetName.argtypes = [SUGroupRef, ctypes.POINTER(SUStringRef)]
        dll.SUGroupGetEntities.restype = ctypes.c_int
        dll.SUGroupGetEntities.argtypes = [SUGroupRef, ctypes.POINTER(SUEntitiesRef)]

        g_arr = (SUGroupRef * 1)()
        act = ctypes.c_size_t()
        dll.SUEntitiesGetGroups(ents, 1, g_arr, ctypes.byref(act))

        s_ref = SUStringRef()
        dll.SUStringCreate(ctypes.byref(s_ref))
        dll.SUGroupGetName(g_arr[0], ctypes.byref(s_ref))
        slen = ctypes.c_size_t()
        dll.SUStringGetUTF8Length(s_ref, ctypes.byref(slen))
        sbuf = ctypes.create_string_buffer(slen.value + 1)
        dll.SUStringGetUTF8(s_ref, slen.value + 1, sbuf, ctypes.byref(slen))
        gname = sbuf.value.decode("utf-8")
        dll.SUStringRelease(ctypes.byref(s_ref))

        print(f"[Trimble C++ API] Nome do Grupo Raiz: '{gname}' (Esperado: Grupo_Pai_Estrutura)")
        assert gname == "Grupo_Pai_Estrutura"

        # Inspeciona subgrupo filho via C++ API
        g1_ents = SUEntitiesRef()
        dll.SUGroupGetEntities(g_arr[0], ctypes.byref(g1_ents))
        sub_g_count = ctypes.c_size_t()
        dll.SUEntitiesGetNumGroups(g1_ents, ctypes.byref(sub_g_count))
        print(f"[Trimble C++ API] Subgrupos aninhados dentro do grupo pai: {sub_g_count.value} (Esperado == 1)")
        assert sub_g_count.value == 1

        sub_g_arr = (SUGroupRef * 1)()
        dll.SUEntitiesGetGroups(g1_ents, 1, sub_g_arr, ctypes.byref(act))
        s_ref2 = SUStringRef()
        dll.SUStringCreate(ctypes.byref(s_ref2))
        dll.SUGroupGetName(sub_g_arr[0], ctypes.byref(s_ref2))
        dll.SUStringGetUTF8Length(s_ref2, ctypes.byref(slen))
        sbuf2 = ctypes.create_string_buffer(slen.value + 1)
        dll.SUStringGetUTF8(s_ref2, slen.value + 1, sbuf2, ctypes.byref(slen))
        sub_name = sbuf2.value.decode("utf-8")
        dll.SUStringRelease(ctypes.byref(s_ref2))

        print(f"[Trimble C++ API] Nome do Subgrupo Filho: '{sub_name}' (Esperado: Subgrupo_Filho_Pilar)")
        assert sub_name == "Subgrupo_Filho_Pilar"

        print(">>> [TRIMBLE C++ API] FRENTE 15 CONCLUÍDA COM 100% DE SUCESSO! HIERARQUIA VALIDADA! <<<")
        model.close()
    finally:
        api.terminate()

if __name__ == "__main__":
    test_front_15_nested_hierarchy()
