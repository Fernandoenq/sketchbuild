"""Gera, pela SketchUpAPI (Python 3.12), arquivos para o REA de anotações e guias (compare com tools/tlv_diff.py).

  a_base         uma face
  a_guia_ponto   + ponto de guia
  a_guia_inf     + linha de guia infinita
  a_guia_fin     + linha de guia finita
  a_secao        + plano de seção
  a_texto        + texto (nota) com ponteiro

Uso:  py -3.12 tools/gerar_anotacoes_api.py PASTA
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUEntitiesRef, SUPoint3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class _Vec(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


class _Plano(ctypes.Structure):
    _fields_ = [("a", ctypes.c_double), ("b", ctypes.c_double), ("c", ctypes.c_double), ("d", ctypes.c_double)]


VARIACOES = ("a_base", "a_guia_ponto", "a_guia_inf", "a_guia_fin", "a_secao", "a_texto")


def _pt(x, y, z):
    p = SUPoint3D()
    p.x, p.y, p.z = x, y, z
    return p


def gerar(pasta: str, modo: str) -> str:
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, modo + ".skp")
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    P = ctypes.POINTER
    try:
        m = api.create_blank_model()
        e = m.get_entities()
        api.add_face(e, [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)])

        def adicionar(nome_add, ref):
            f = getattr(d, nome_add)
            f.argtypes = [SUEntitiesRef, ctypes.c_size_t, P(_Ref)]
            assert f(e, 1, (_Ref * 1)(ref)) == 0, nome_add

        if modo == "a_guia_ponto":
            d.SUGuidePointCreate.argtypes = [P(_Ref), P(SUPoint3D)]
            r = _Ref()
            assert d.SUGuidePointCreate(ctypes.byref(r), ctypes.byref(_pt(10, 20, 30))) == 0
            adicionar("SUEntitiesAddGuidePoints", r)
        elif modo == "a_guia_inf":
            d.SUGuideLineCreateInfinite.argtypes = [P(_Ref), P(SUPoint3D), P(_Vec)]
            r, v = _Ref(), _Vec(0, 0, 1)
            assert d.SUGuideLineCreateInfinite(ctypes.byref(r), ctypes.byref(_pt(10, 20, 0)), ctypes.byref(v)) == 0
            adicionar("SUEntitiesAddGuideLines", r)
        elif modo == "a_guia_fin":
            d.SUGuideLineCreateFinite.argtypes = [P(_Ref), P(SUPoint3D), P(SUPoint3D)]
            r = _Ref()
            assert d.SUGuideLineCreateFinite(ctypes.byref(r), ctypes.byref(_pt(0, 0, 0)), ctypes.byref(_pt(50, 50, 0))) == 0
            adicionar("SUEntitiesAddGuideLines", r)
        elif modo == "a_secao":
            d.SUSectionPlaneCreate.argtypes = [P(_Ref)]
            r = _Ref()
            assert d.SUSectionPlaneCreate(ctypes.byref(r)) == 0
            d.SUSectionPlaneSetPlane.argtypes = [_Ref, P(_Plano)]
            assert d.SUSectionPlaneSetPlane(r, ctypes.byref(_Plano(0, 0, 1, -50))) == 0
            adicionar("SUEntitiesAddSectionPlanes", r)
        elif modo == "a_texto":
            d.SUTextCreate.argtypes = [P(_Ref)]
            r = _Ref()
            assert d.SUTextCreate(ctypes.byref(r)) == 0
            d.SUTextSetString.argtypes = [_Ref, ctypes.c_char_p]
            assert d.SUTextSetString(r, "Nota de teste".encode("utf-8")) == 0
            d.SUTextSetLeaderType.argtypes = [_Ref, ctypes.c_int]
            assert d.SUTextSetLeaderType(r, 0) == 0  # sem linha de chamada: o texto fica no ponto padrão
            adicionar("SUEntitiesAddTexts", r)
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "anotacoes")
    for modo in VARIACOES:
        try:
            print(gerar(pasta, modo))
        except (AssertionError, AttributeError) as ex:
            print("falhou", modo, ex)
