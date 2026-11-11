"""Lê curvas de arco (círculo/arco) de um .skp via SketchUpAPI.dll (oráculo do registro 0x1397). Python 3.12.

Uso:  py -3.12 tools/su_curvas.py arquivo.skp
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUPoint3D, SUVector3D, SUEntitiesRef  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


def curvas(caminho: str) -> list:
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    out = []
    try:
        with api.open_model(caminho) as m:
            ents = m.get_entities()
            n = ctypes.c_size_t()
            d.SUEntitiesGetNumArcCurves.argtypes = [SUEntitiesRef, ctypes.POINTER(ctypes.c_size_t)]
            d.SUEntitiesGetNumArcCurves(ents, ctypes.byref(n))
            arr = (_Ref * max(n.value, 1))()
            got = ctypes.c_size_t()
            d.SUEntitiesGetArcCurves.argtypes = [SUEntitiesRef, ctypes.c_size_t, ctypes.POINTER(_Ref), ctypes.POINTER(ctypes.c_size_t)]
            d.SUEntitiesGetArcCurves(ents, n.value, arr, ctypes.byref(got))
            for i in range(got.value):
                a = arr[i]
                r = ctypes.c_double()
                s = ctypes.c_double()
                e = ctypes.c_double()
                for nome, v in (("Radius", r), ("StartAngle", s), ("EndAngle", e)):
                    f = getattr(d, "SUArcCurveGet" + nome)
                    f.argtypes = [_Ref, ctypes.POINTER(ctypes.c_double)]
                    f(a, ctypes.byref(v))
                vet = {}
                for nome, T in (("Center", SUPoint3D), ("Normal", SUVector3D), ("XAxis", SUVector3D), ("YAxis", SUVector3D)):
                    f = getattr(d, "SUArcCurveGet" + nome)
                    f.argtypes = [_Ref, ctypes.POINTER(T)]
                    t = T()
                    f(a, ctypes.byref(t))
                    vet[nome.lower()] = (round(t.x, 6), round(t.y, 6), round(t.z, 6))
                out.append({"raio": round(r.value, 6), "ini": round(s.value, 6), "fim": round(e.value, 6), **vet})
    finally:
        api.terminate()
    return out


if __name__ == "__main__":
    for c in curvas(sys.argv[1]):
        print(c)
