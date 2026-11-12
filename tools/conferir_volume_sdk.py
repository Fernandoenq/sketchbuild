"""Oráculo do M12: o volume que a SketchUpAPI calcula (`SUComponentInstanceComputeVolume`) para um grupo com sólido.

Casos: cubo de 10 (1000), cubo com cavidade interna cúbica de 4 (936) e cubo aberto (sem uma face: a SDK devolve erro ou 0).
Uso:  py -3.12 tools/conferir_volume_sdk.py
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUPoint3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class _Transf(ctypes.Structure):
    _fields_ = [("values", ctypes.c_double * 16)]


P = ctypes.POINTER

_LADOS = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]  # normais para fora


def _cubo(x, y, z, s, invertido=False, sem=None):
    v = [(x + i * s, y + j * s, z + k * s) for k in (0, 1) for j, i in ((0, 0), (0, 1), (1, 1), (1, 0))]
    faces = [list(reversed(f)) if invertido else f for n, f in enumerate(_LADOS) if n != sem]
    return v, faces


def volume(cubos) -> float:
    """Volume do grupo que contém os cubos (lista de (vértices, faces)); levanta AssertionError se a SDK recusar."""
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        raiz = m.get_entities()
        grupo = api.create_group(raiz, "g")
        ents = api.get_group_entities(grupo)
        gi = _Ref()
        d.SUGeometryInputCreate.argtypes = [P(_Ref)]
        assert d.SUGeometryInputCreate(ctypes.byref(gi)) == 0
        d.SUGeometryInputAddVertex.argtypes = [_Ref, P(SUPoint3D)]
        d.SULoopInputCreate.argtypes = [P(_Ref)]
        d.SULoopInputAddVertexIndex.argtypes = [_Ref, ctypes.c_size_t]
        d.SUGeometryInputAddFace.argtypes = [_Ref, P(_Ref), P(ctypes.c_size_t)]
        base = 0
        for v, faces in cubos:
            for x, y, z in v:
                assert d.SUGeometryInputAddVertex(gi, ctypes.byref(SUPoint3D(x=x, y=y, z=z))) == 0
            for f in faces:
                lp = _Ref()
                assert d.SULoopInputCreate(ctypes.byref(lp)) == 0
                for i in f:
                    assert d.SULoopInputAddVertexIndex(lp, base + i) == 0
                assert d.SUGeometryInputAddFace(gi, ctypes.byref(lp), ctypes.byref(ctypes.c_size_t())) == 0
            base += len(v)
        d.SUEntitiesFill.argtypes = [type(ents), _Ref, ctypes.c_bool]
        assert d.SUEntitiesFill(ents, gi, True) == 0
        d.SUGroupToComponentInstance.argtypes = [type(grupo)]
        d.SUGroupToComponentInstance.restype = _Ref
        inst = d.SUGroupToComponentInstance(grupo)
        ident = _Transf()
        for k in (0, 5, 10, 15):
            ident.values[k] = 1.0
        d.SUComponentInstanceComputeVolume.argtypes = [_Ref, P(_Transf), P(ctypes.c_double)]
        vol = ctypes.c_double()
        r = d.SUComponentInstanceComputeVolume(inst, ctypes.byref(ident), ctypes.byref(vol))
        assert r == 0, f"SUComponentInstanceComputeVolume devolveu {r}"
        m.close()
        return vol.value
    finally:
        api.terminate()


if __name__ == "__main__":
    casos = {
        "cubo 10": [_cubo(0, 0, 0, 10)],
        "cubo 10 com cavidade 4": [_cubo(0, 0, 0, 10), _cubo(3, 3, 3, 4, invertido=True)],
        "cubo 10 e cubo 4 solto dentro (sem inverter)": [_cubo(0, 0, 0, 10), _cubo(3, 3, 3, 4)],
        "cubo aberto (sem tampa)": [_cubo(0, 0, 0, 10, sem=1)],
    }
    for nome, c in casos.items():
        try:
            print(nome, "->", volume(c))
        except AssertionError as e:
            print(nome, "-> erro:", e)
