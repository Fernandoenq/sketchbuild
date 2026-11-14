"""Oráculo de Mover/Rotacionar/Escalar: o que `SUEntitiesTransform` da SketchUpAPI faz com a geometria.

Mede (a) posição dos vértices após a matriz, (b) normal e ordem dos vértices da face após escala negativa (espelho),
(c) se arestas/faces não transformadas continuam ligadas (deformação). Uso: py -3.12 tools/conferir_transformar_sdk.py
"""
import ctypes
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUPoint3D, SUTransformation, SUVector3D  # noqa: E402
from tools.conferir_apagar_sdk import P, _arestas, _faces, _lista, _pos, _Ref  # noqa: E402
from tools.conferir_desenho_em_face_sdk import _passo  # noqa: E402


def matriz(m):
    """m: 16 números em ordem de coluna (column-major), como a SDK."""
    t = SUTransformation()
    for i, v in enumerate(m):
        t.values[i] = v
    return t


def translacao(dx, dy, dz):
    return [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, dx, dy, dz, 1]


def escala(sx, sy, sz):
    return [sx, 0, 0, 0, 0, sy, 0, 0, 0, 0, sz, 0, 0, 0, 0, 1]


def rot_z(graus):
    c, s = math.cos(math.radians(graus)), math.sin(math.radians(graus))
    return [c, s, 0, 0, -s, c, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


def _normal(d, f):
    d.SUFaceGetNormal.argtypes = [_Ref, P(SUVector3D)]
    v = SUVector3D()
    assert d.SUFaceGetNormal(f, ctypes.byref(v)) == 0
    return tuple(round(c, 6) + 0.0 for c in (v.x, v.y, v.z))


def _ordem(d, f):
    d.SUFaceGetNumVertices.argtypes = [_Ref, P(ctypes.c_size_t)]
    d.SUFaceGetVertices.argtypes = [_Ref, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
    n = ctypes.c_size_t()
    d.SUFaceGetNumVertices(f, ctypes.byref(n))
    vs, got = (_Ref * n.value)(), ctypes.c_size_t()
    d.SUFaceGetVertices(f, n.value, vs, ctypes.byref(got))
    return [_pos(d, v) for v in vs]


def transformar(passos, m) -> dict:
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        mod = api.create_blank_model()
        ents = mod.get_entities()
        for p in passos:
            _passo(d, ents, p["verts"], p.get("faces", ()), p.get("arestas", ()))
        d.SUEntitiesTransform.argtypes = [type(ents), ctypes.c_size_t, P(_Ref), P(SUTransformation)]
        # todas as faces e arestas soltas
        refs = []
        d.SUFaceToEntity.argtypes = [_Ref]
        d.SUFaceToEntity.restype = _Ref
        d.SUEdgeToEntity.argtypes = [_Ref]
        d.SUEdgeToEntity.restype = _Ref
        for f in _lista(d, ents, "SUEntitiesGetNumFaces", "SUEntitiesGetFaces"):
            refs.append(d.SUFaceToEntity(f))
        for e in _lista(d, ents, "SUEntitiesGetNumEdges", "SUEntitiesGetEdges"):
            refs.append(d.SUEdgeToEntity(e))
        t = matriz(m)
        r = d.SUEntitiesTransform(ents, len(refs), (_Ref * len(refs))(*refs), ctypes.byref(t))
        faces = _lista(d, ents, "SUEntitiesGetNumFaces", "SUEntitiesGetFaces")
        return {"codigo": r, "faces": [{"normal": _normal(d, f), "ordem": _ordem(d, f)} for f in faces],
                "arestas": len(_arestas(d, ents))}
    finally:
        api.terminate()


Q = {"verts": [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)], "faces": [[0, 1, 2, 3]]}

if __name__ == "__main__":
    for nome, m in (("mover (5,0,0)", translacao(5, 0, 0)), ("rotar 90 em z", rot_z(90)), ("escala 2,2,2", escala(2, 2, 2)),
                    ("espelho x (-1,1,1)", escala(-1, 1, 1))):
        r = transformar([Q], m)
        print(nome, "->", r["codigo"], r["faces"][0]["normal"], r["faces"][0]["ordem"], f"{r['arestas']} arestas")
