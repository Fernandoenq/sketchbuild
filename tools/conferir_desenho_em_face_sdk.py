"""Oráculo do desenho sobre geometria existente: o que a SketchUpAPI faz quando uma linha, um retângulo ou um círculo
é desenhado em cima de uma face ou aresta que já existe (divide a face? cria furo? parte a aresta?).

Cada caso monta a cena em passos (cada passo é um `SUGeometryInput` aplicado com `SUEntitiesFill`) e devolve
{"faces": set de frozenset(posições), "arestas": ...}. Uso:  py -3.12 tools/conferir_desenho_em_face_sdk.py
"""
import ctypes
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUPoint3D  # noqa: E402
from tools.conferir_apagar_sdk import P, _arestas, _faces, _Ref  # noqa: E402


def _passo(d, ents, verts, faces=(), arestas=(), weld=True):
    gi = _Ref()
    d.SUGeometryInputCreate.argtypes = [P(_Ref)]
    assert d.SUGeometryInputCreate(ctypes.byref(gi)) == 0
    d.SUGeometryInputAddVertex.argtypes = [_Ref, P(SUPoint3D)]
    for x, y, z in verts:
        assert d.SUGeometryInputAddVertex(gi, ctypes.byref(SUPoint3D(x=x, y=y, z=z))) == 0
    d.SULoopInputCreate.argtypes = [P(_Ref)]
    d.SULoopInputAddVertexIndex.argtypes = [_Ref, ctypes.c_size_t]
    d.SUGeometryInputAddFace.argtypes = [_Ref, P(_Ref), P(ctypes.c_size_t)]
    d.SUGeometryInputAddEdge.argtypes = [_Ref, ctypes.c_size_t, ctypes.c_size_t, P(ctypes.c_size_t)]
    for f in faces:
        lp = _Ref()
        assert d.SULoopInputCreate(ctypes.byref(lp)) == 0
        for i in f:
            assert d.SULoopInputAddVertexIndex(lp, i) == 0
        idx = ctypes.c_size_t()
        assert d.SUGeometryInputAddFace(gi, ctypes.byref(lp), ctypes.byref(idx)) == 0
    for a, b in arestas:
        idx = ctypes.c_size_t()
        assert d.SUGeometryInputAddEdge(gi, a, b, ctypes.byref(idx)) == 0
    d.SUEntitiesFill.argtypes = [type(ents), _Ref, ctypes.c_bool]
    r = d.SUEntitiesFill(ents, gi, weld)
    assert r == 0, f"SUEntitiesFill devolveu {r}"


def cena(passos, weld=True) -> dict:
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        ents = m.get_entities()
        for p in passos:
            _passo(d, ents, p["verts"], p.get("faces", ()), p.get("arestas", ()), weld)
        return {"faces": set(_faces(d, ents)), "arestas": set(_arestas(d, ents))}
    finally:
        api.terminate()


GRANDE = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]


def casos():
    out = {}
    base = {"verts": GRANDE, "faces": [[0, 1, 2, 3]]}
    out["linha de borda a borda"] = cena([base, {"verts": [(0, 5, 0), (10, 5, 0)], "arestas": [(0, 1)]}])
    out["linha no meio da face (nao toca a borda)"] = cena([base, {"verts": [(3, 5, 0), (7, 5, 0)], "arestas": [(0, 1)]}])
    out["linha de um canto ao oposto"] = cena([base, {"verts": [(0, 0, 0), (10, 10, 0)], "arestas": [(0, 1)]}])
    out["retangulo dentro da face"] = cena([base, {"verts": [(3, 3, 0), (7, 3, 0), (7, 7, 0), (3, 7, 0)], "faces": [[0, 1, 2, 3]]}])
    out["retangulo encostado numa borda"] = cena([base, {"verts": [(0, 0, 0), (4, 0, 0), (4, 4, 0), (0, 4, 0)], "faces": [[0, 1, 2, 3]]}])
    out["retangulo meio fora"] = cena([base, {"verts": [(6, 6, 0), (14, 6, 0), (14, 14, 0), (6, 14, 0)], "faces": [[0, 1, 2, 3]]}])
    k = 12
    circ = [(5 + 2 * math.cos(2 * math.pi * i / k), 5 + 2 * math.sin(2 * math.pi * i / k), 0) for i in range(k)]
    out["circulo (12 lados) dentro da face"] = cena([base, {"verts": circ, "faces": [list(range(k))]}])
    out["linha vertical que cruza duas arestas e a face"] = cena([base, {"verts": [(5, -2, 0), (5, 12, 0)], "arestas": [(0, 1)]}])
    out["sem weld: linha de borda a borda"] = cena([base, {"verts": [(0, 5, 0), (10, 5, 0)], "arestas": [(0, 1)]}], weld=False)
    return out


if __name__ == "__main__":
    for nome, r in casos().items():
        print(f"{nome}: {len(r['faces'])} faces, {len(r['arestas'])} arestas")
