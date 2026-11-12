"""Oráculo do M11 (soften/smooth): o que a SketchUpAPI devolve de normal por vértice (`SUMeshHelperGetNormals`) numa
aresta compartilhada por duas faces de áreas bem diferentes, com a aresta lisa, suave, as duas ou nenhuma.

As áreas diferentes separam os pesos possíveis: por área, por ângulo do vértice (aqui os dois cantos são de 90 graus, então
dá a bissetriz) e média simples (também a bissetriz).
Uso:  py -3.12 tools/conferir_normais_sdk.py
"""
import ctypes
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUPoint3D, SUVector3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


P = ctypes.POINTER


def telhado(largura_a=10.0, largura_b=2.0, graus=60.0):
    """Face A no plano z=0 (x de -largura_a a 0) e face B inclinada (largura_b), compartilhando a aresta x=0."""
    a = math.radians(graus)
    v = [(0, 0, 0), (0, 10, 0), (-largura_a, 10, 0), (-largura_a, 0, 0),
         (largura_b * math.cos(a), 0, largura_b * math.sin(a)), (largura_b * math.cos(a), 10, largura_b * math.sin(a))]
    return v, [[0, 3, 2, 1], [0, 4, 5, 1]]  # A com a normal para cima (+z); B para cima e para a esquerda


def gerar(variacao: str, **kw) -> dict:
    """Devolve {face: {"area": a, "normal": n, "vertices": [(ponto, normal_do_mesh), ...]}}."""
    v, faces = telhado(**kw)
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        ents, mr = m.get_entities(), m._model
        gi = _Ref()
        d.SUGeometryInputCreate.argtypes = [P(_Ref)]
        assert d.SUGeometryInputCreate(ctypes.byref(gi)) == 0
        d.SUGeometryInputAddVertex.argtypes = [_Ref, P(SUPoint3D)]
        for x, y, z in v:
            assert d.SUGeometryInputAddVertex(gi, ctypes.byref(SUPoint3D(x=x, y=y, z=z))) == 0
        d.SULoopInputCreate.argtypes = [P(_Ref)]
        d.SULoopInputAddVertexIndex.argtypes = [_Ref, ctypes.c_size_t]
        d.SUGeometryInputAddFace.argtypes = [_Ref, P(_Ref), P(ctypes.c_size_t)]
        for f in faces:
            lp = _Ref()
            assert d.SULoopInputCreate(ctypes.byref(lp)) == 0
            for i in f:
                assert d.SULoopInputAddVertexIndex(lp, i) == 0
            assert d.SUGeometryInputAddFace(gi, ctypes.byref(lp), ctypes.byref(ctypes.c_size_t())) == 0
        d.SUEntitiesFill.argtypes = [type(ents), _Ref, ctypes.c_bool]
        assert d.SUEntitiesFill(ents, gi, True) == 0

        n = ctypes.c_size_t()
        d.SUEntitiesGetNumEdges.argtypes = [type(ents), ctypes.c_bool, P(ctypes.c_size_t)]
        assert d.SUEntitiesGetNumEdges(ents, False, ctypes.byref(n)) == 0
        arestas, got = (_Ref * n.value)(), ctypes.c_size_t()
        d.SUEntitiesGetEdges.argtypes = [type(ents), ctypes.c_bool, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
        assert d.SUEntitiesGetEdges(ents, False, n.value, arestas, ctypes.byref(got)) == 0
        d.SUEdgeGetNumFaces.argtypes = [_Ref, P(ctypes.c_size_t)]
        d.SUEdgeSetSmooth.argtypes = [_Ref, ctypes.c_bool]
        d.SUEdgeSetSoft.argtypes = [_Ref, ctypes.c_bool]
        for e in arestas:
            nf = ctypes.c_size_t()
            assert d.SUEdgeGetNumFaces(e, ctypes.byref(nf)) == 0
            if nf.value == 2:
                if variacao in ("lisa", "ambas"):
                    assert d.SUEdgeSetSmooth(e, True) == 0
                if variacao in ("suave", "ambas"):
                    assert d.SUEdgeSetSoft(e, True) == 0

        d.SUEntitiesGetNumFaces.argtypes = [type(ents), P(ctypes.c_size_t)]
        assert d.SUEntitiesGetNumFaces(ents, ctypes.byref(n)) == 0
        fs, got = (_Ref * n.value)(), ctypes.c_size_t()
        d.SUEntitiesGetFaces.argtypes = [type(ents), ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
        assert d.SUEntitiesGetFaces(ents, n.value, fs, ctypes.byref(got)) == 0
        saida = {}
        d.SUFaceGetArea.argtypes = [_Ref, P(ctypes.c_double)]
        d.SUFaceGetNormal.argtypes = [_Ref, P(SUVector3D)]
        d.SUMeshHelperCreate.argtypes = [P(_Ref), _Ref]
        d.SUMeshHelperGetNumVertices.argtypes = [_Ref, P(ctypes.c_size_t)]
        d.SUMeshHelperGetVertices.argtypes = [_Ref, ctypes.c_size_t, P(SUPoint3D), P(ctypes.c_size_t)]
        d.SUMeshHelperGetNormals.argtypes = [_Ref, ctypes.c_size_t, P(SUVector3D), P(ctypes.c_size_t)]
        d.SUMeshHelperRelease.argtypes = [P(_Ref)]
        for i, f in enumerate(fs):
            area, nrm = ctypes.c_double(), SUVector3D()
            assert d.SUFaceGetArea(f, ctypes.byref(area)) == 0
            assert d.SUFaceGetNormal(f, ctypes.byref(nrm)) == 0
            mh = _Ref()
            assert d.SUMeshHelperCreate(ctypes.byref(mh), f) == 0
            nv = ctypes.c_size_t()
            assert d.SUMeshHelperGetNumVertices(mh, ctypes.byref(nv)) == 0
            pts, nms, c1, c2 = (SUPoint3D * nv.value)(), (SUVector3D * nv.value)(), ctypes.c_size_t(), ctypes.c_size_t()
            assert d.SUMeshHelperGetVertices(mh, nv.value, pts, ctypes.byref(c1)) == 0
            assert d.SUMeshHelperGetNormals(mh, nv.value, nms, ctypes.byref(c2)) == 0
            saida[i] = {"area": round(area.value, 6), "normal": (nrm.x, nrm.y, nrm.z),
                        "vertices": [((p.x, p.y, p.z), (q.x, q.y, q.z)) for p, q in zip(pts, nms)]}
            d.SUMeshHelperRelease(ctypes.byref(mh))
        m.close()
        return saida
    finally:
        api.terminate()


def _fmt(v):
    return "(" + ", ".join(f"{c:.4f}" for c in v) + ")"


if __name__ == "__main__":
    for var in ("nenhuma", "lisa", "suave", "ambas"):
        print("==", var)
        for i, f in gerar(var).items():
            print(" face", i, "area", f["area"], "normal", _fmt(f["normal"]))
            for p, q in f["vertices"]:
                print("    ", _fmt(p), "->", _fmt(q))
