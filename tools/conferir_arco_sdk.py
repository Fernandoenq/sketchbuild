"""Oráculo do M10 (arcos): o que a SketchUpAPI gera com `SUArcCurveCreate(centro, início, fim, normal, nº de arestas)`.

Assinatura lida no REA (0xf9d9): param_2 = centro, param_3 = ponto inicial, param_4 = ponto final, param_5 = normal,
param_6 = número de arestas. Devolve os vértices, o raio, os ângulos e os eixos que a SDK calcula.
Uso:  py -3.12 tools/conferir_arco_sdk.py
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUEntitiesRef, SUPoint3D, SUVector3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


P = ctypes.POINTER


def _vec(T, v):
    return T(x=v[0], y=v[1], z=v[2])


def arco(centro, inicio, fim, normal, arestas=12) -> dict:
    """Cria o arco na SDK e devolve {vertices, raio, ang_ini, ang_fim, xaxis, yaxis, normal, centro}."""
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        ents = m.get_entities()
        a = _Ref()
        d.SUArcCurveCreate.argtypes = [P(_Ref), P(SUPoint3D), P(SUPoint3D), P(SUPoint3D), P(SUVector3D), ctypes.c_size_t]
        r = d.SUArcCurveCreate(ctypes.byref(a), ctypes.byref(_vec(SUPoint3D, centro)), ctypes.byref(_vec(SUPoint3D, inicio)),
                               ctypes.byref(_vec(SUPoint3D, fim)), ctypes.byref(_vec(SUVector3D, normal)), arestas)
        assert r == 0, f"SUArcCurveCreate devolveu {r}"
        d.SUEntitiesAddArcCurves.argtypes = [SUEntitiesRef, ctypes.c_size_t, P(_Ref)]
        assert d.SUEntitiesAddArcCurves(ents, 1, (_Ref * 1)(a)) == 0
        saida = {}
        for nome in ("Radius", "StartAngle", "EndAngle"):
            f = getattr(d, "SUArcCurveGet" + nome)
            f.argtypes = [_Ref, P(ctypes.c_double)]
            v = ctypes.c_double()
            assert f(a, ctypes.byref(v)) == 0
            saida[{"Radius": "raio", "StartAngle": "ang_ini", "EndAngle": "ang_fim"}[nome]] = v.value
        for nome, T, chave in (("Center", SUPoint3D, "centro"), ("Normal", SUVector3D, "normal"),
                               ("XAxis", SUVector3D, "xaxis"), ("YAxis", SUVector3D, "yaxis")):
            f = getattr(d, "SUArcCurveGet" + nome)
            f.argtypes = [_Ref, P(T)]
            t = T()
            assert f(a, ctypes.byref(t)) == 0
            saida[chave] = (t.x, t.y, t.z)
        n = ctypes.c_size_t()
        d.SUEntitiesGetNumEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, P(ctypes.c_size_t)]
        assert d.SUEntitiesGetNumEdges(ents, False, ctypes.byref(n)) == 0
        arestas_ref, got = (_Ref * n.value)(), ctypes.c_size_t()
        d.SUEntitiesGetEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
        assert d.SUEntitiesGetEdges(ents, False, n.value, arestas_ref, ctypes.byref(got)) == 0
        d.SUEdgeGetStartVertex.argtypes = [_Ref, P(_Ref)]
        d.SUEdgeGetEndVertex.argtypes = [_Ref, P(_Ref)]
        d.SUVertexGetPosition.argtypes = [_Ref, P(SUPoint3D)]
        pts = []
        for e in arestas_ref:
            par = []
            for f in (d.SUEdgeGetStartVertex, d.SUEdgeGetEndVertex):
                v = _Ref()
                assert f(e, ctypes.byref(v)) == 0
                p = SUPoint3D()
                assert d.SUVertexGetPosition(v, ctypes.byref(p)) == 0
                par.append((p.x, p.y, p.z))
            pts.append(tuple(par))
        saida["arestas"] = pts
        m.close()
        return saida
    finally:
        api.terminate()


if __name__ == "__main__":
    r = arco((0, 0, 0), (10, 0, 0), (0, 10, 0), (0, 0, 1), 6)
    for k, v in r.items():
        print(k, v)
