"""Gera, pela SketchUpAPI (Python 3.12), modelos com um componente e uma variação do comportamento cada (oráculo do 0x1b58).

Comportamento (`SUComponentDefinitionSetBehavior`, FORMATO-SKP 7m): face-me, corta abertura, sombra segue o sol e
`snap`. Uso:  py -3.12 tools/gerar_comportamento_api.py [PASTA]  e depois  tools/tlv_diff.py PASTA/base.skp PASTA/facame.skp
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUModelRef  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


P = ctypes.POINTER
# nome -> (byte da estrutura SUComponentBehavior, valor): 0 snap, 4 corta abertura, 5 face-me, 6 sombra segue o sol
VARIACOES = {"base": None, "facame": (5, 1), "corta": (4, 1), "sombra": (6, 1), "snap1": (0, 1), "snap2": (0, 2)}


def gerar(pasta: str, nome: str, api: SketchUpAPI) -> str:
    d = api._dll
    m = api.create_blank_model()
    try:
        e, mr = m.get_entities(), m._model
        df = _Ref()
        d.SUComponentDefinitionCreate.argtypes = [P(_Ref)]
        d.SUComponentDefinitionCreate(ctypes.byref(df))
        d.SUModelAddComponentDefinitions.argtypes = [SUModelRef, ctypes.c_size_t, P(_Ref)]
        d.SUModelAddComponentDefinitions(mr, 1, (_Ref * 1)(df))
        d.SUComponentDefinitionGetEntities.argtypes = [_Ref, P(type(e))]
        de = type(e)()
        d.SUComponentDefinitionGetEntities(df, ctypes.byref(de))
        api.add_face(de, [(0, 0, 0), (30, 0, 0), (30, 20, 0), (0, 20, 0)])
        raw = (ctypes.c_ubyte * 16)()
        d.SUComponentDefinitionGetBehavior.argtypes = [_Ref, ctypes.c_void_p]
        d.SUComponentDefinitionSetBehavior.argtypes = [_Ref, ctypes.c_void_p]
        d.SUComponentDefinitionGetBehavior(df, raw)
        if VARIACOES[nome]:
            raw[VARIACOES[nome][0]] = VARIACOES[nome][1]
        assert d.SUComponentDefinitionSetBehavior(df, raw) == 0
        inst = _Ref()
        d.SUComponentDefinitionCreateInstance.argtypes = [_Ref, P(_Ref)]
        d.SUComponentDefinitionCreateInstance(df, ctypes.byref(inst))
        d.SUEntitiesAddInstance.argtypes = [type(e), _Ref, ctypes.c_void_p]
        d.SUEntitiesAddInstance(e, inst, None)
        destino = os.path.join(pasta, nome + ".skp")
        m.save(destino)
        return destino
    finally:
        m.close()


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "comport")
    os.makedirs(pasta, exist_ok=True)
    api = SketchUpAPI()
    api.initialize()
    for nome in VARIACOES:
        print(gerar(pasta, nome, api))
