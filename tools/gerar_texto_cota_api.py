"""Gera, pela SketchUpAPI (Python 3.12), modelos com um texto livre e uma cota para conferir a ordem dos ids.

Variantes: criar e adicionar na ordem texto->cota (tc), cota->texto (ct), e criar texto antes mas adicionar a cota
primeiro (tc_add_ct). Uso: py -3.12 tools/gerar_texto_cota_api.py [PASTA]  (compare com tools/tlv_diff.py)."""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUModelRef, SUPoint3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


P = ctypes.POINTER


def _pt(x, y, z):
    p = SUPoint3D()
    p.x, p.y, p.z = x, y, z
    return p


# nome -> (ordem de criação, ordem de inclusão nas entidades)
VARIANTES = {"tc": ("tc", "tc"), "ct": ("ct", "ct"), "tc_add_ct": ("tc", "ct")}
# as letras são "t" (texto) e "c" (cota)


def gerar(pasta: str, nome: str) -> str:
    criar_ordem, add_ordem = VARIANTES[nome]
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, f"tc_{nome}.skp")
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        e, mr = m.get_entities(), m._model

        def criar_texto():
            n = ctypes.c_size_t()
            d.SUModelGetNumFonts.argtypes = [SUModelRef, P(ctypes.c_size_t)]
            assert d.SUModelGetNumFonts(mr, ctypes.byref(n)) == 0
            fontes, got = (_Ref * n.value)(), ctypes.c_size_t()
            d.SUModelGetFonts.argtypes = [SUModelRef, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
            assert d.SUModelGetFonts(mr, n.value, fontes, ctypes.byref(got)) == 0
            r = _Ref()
            d.SUTextCreate.argtypes = [P(_Ref)]
            assert d.SUTextCreate(ctypes.byref(r)) == 0
            d.SUTextSetString.argtypes = [_Ref, ctypes.c_char_p]
            assert d.SUTextSetString(r, b"Nota") == 0
            d.SUTextSetPoint.argtypes = [_Ref, P(SUPoint3D), _Ref]
            assert d.SUTextSetPoint(r, ctypes.byref(_pt(10, 20, 30)), _Ref()) == 0
            d.SUTextSetFont.argtypes = [_Ref, _Ref]
            assert d.SUTextSetFont(r, fontes[0]) == 0
            return r

        def criar_cota():
            r = _Ref()
            d.SUDimensionLinearCreate.argtypes = [P(_Ref), P(SUPoint3D), _Ref, P(SUPoint3D), _Ref]
            assert d.SUDimensionLinearCreate(ctypes.byref(r), ctypes.byref(_pt(0, 0, 0)), _Ref(),
                                             ctypes.byref(_pt(100, 0, 0)), _Ref()) == 0
            return r

        objs = {}
        for k in criar_ordem.replace("c", "c"):
            objs[k] = criar_texto() if k == "t" else criar_cota()
        d.SUEntitiesAddTexts.argtypes = [type(e), ctypes.c_size_t, P(_Ref)]
        d.SUEntitiesAddDimensions.argtypes = [type(e), ctypes.c_size_t, P(_Ref)]
        for k in add_ordem:
            if k == "t":
                assert d.SUEntitiesAddTexts(e, 1, (_Ref * 1)(objs["t"])) == 0
            else:
                assert d.SUEntitiesAddDimensions(e, 1, (_Ref * 1)(objs["c"])) == 0
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "textos")
    for nome in VARIANTES:
        print(gerar(pasta, nome))
