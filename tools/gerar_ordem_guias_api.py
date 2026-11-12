"""Gera, pela SketchUpAPI (Python 3.12), modelos com vários tipos de guia/seção incluídos em ordens diferentes, para
conferir como a SDK numera os ids (FORMATO-SKP 7l). Nome = letras na ordem de inclusão: p ponto de guia, l linha de guia,
s plano de seção. Uso: py -3.12 tools/gerar_ordem_guias_api.py [PASTA]  (compare com tools/tlv_diff.py)."""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUEntitiesRef, SUPoint3D  # noqa: E402
from tools.gerar_anotacoes_api import _Plano, _Ref, _Vec, _pt  # noqa: E402

P = ctypes.POINTER
ORDENS = ["psl", "slp", "lps", "spl"]


def gerar(pasta: str, ordem: str) -> str:
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, f"g_{ordem}.skp")
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        e = m.get_entities()
        api.add_face(e, [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)])

        def adicionar(nome_add, ref):
            f = getattr(d, nome_add)
            f.argtypes = [SUEntitiesRef, ctypes.c_size_t, P(_Ref)]
            assert f(e, 1, (_Ref * 1)(ref)) == 0, nome_add

        for k in ordem:
            r = _Ref()
            if k == "p":
                d.SUGuidePointCreate.argtypes = [P(_Ref), P(SUPoint3D)]
                assert d.SUGuidePointCreate(ctypes.byref(r), ctypes.byref(_pt(10, 20, 30))) == 0
                adicionar("SUEntitiesAddGuidePoints", r)
            elif k == "l":
                d.SUGuideLineCreateFinite.argtypes = [P(_Ref), P(SUPoint3D), P(SUPoint3D)]
                assert d.SUGuideLineCreateFinite(ctypes.byref(r), ctypes.byref(_pt(0, 0, 0)), ctypes.byref(_pt(50, 50, 0))) == 0
                adicionar("SUEntitiesAddGuideLines", r)
            else:
                d.SUSectionPlaneCreate.argtypes = [P(_Ref)]
                assert d.SUSectionPlaneCreate(ctypes.byref(r)) == 0
                d.SUSectionPlaneSetPlane.argtypes = [_Ref, P(_Plano)]
                assert d.SUSectionPlaneSetPlane(r, ctypes.byref(_Plano(0, 0, 1, -50))) == 0
                adicionar("SUEntitiesAddSectionPlanes", r)
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "guias")
    for o in ORDENS:
        print(gerar(pasta, o))
