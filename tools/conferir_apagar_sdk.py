"""Oráculo da borracha (Apagar): o que `SUEntitiesErase` da SketchUpAPI faz com arestas, faces e curvas.

A DLL só exporta `SUEntitiesErase(entities, len, SUEntityRef[])`: apagar é uma operação genérica sobre entidades. Aqui se
monta a geometria com `SUGeometryInput` (faces, arestas soltas e curvas), apaga-se uma entidade e lê-se o que sobrou.
Uso:  py -3.12 tools/conferir_apagar_sdk.py
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUPoint3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


P = ctypes.POINTER
_N = 6  # casas decimais para comparar posições


def _pos(d, v):
    p = SUPoint3D()
    d.SUVertexGetPosition.argtypes = [_Ref, P(SUPoint3D)]
    assert d.SUVertexGetPosition(v, ctypes.byref(p)) == 0
    return (round(p.x, _N) + 0.0, round(p.y, _N) + 0.0, round(p.z, _N) + 0.0)


def _lista(d, ents, nome_num, nome_get):
    n = ctypes.c_size_t()
    getattr(d, nome_num).argtypes = [type(ents), P(ctypes.c_size_t)] if nome_num != "SUEntitiesGetNumEdges" else [type(ents), ctypes.c_bool, P(ctypes.c_size_t)]
    if nome_num == "SUEntitiesGetNumEdges":
        assert getattr(d, nome_num)(ents, False, ctypes.byref(n)) == 0
        getattr(d, nome_get).argtypes = [type(ents), ctypes.c_bool, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
        arr, got = (_Ref * max(n.value, 1))(), ctypes.c_size_t()
        assert getattr(d, nome_get)(ents, False, n.value, arr, ctypes.byref(got)) == 0
    else:
        assert getattr(d, nome_num)(ents, ctypes.byref(n)) == 0
        getattr(d, nome_get).argtypes = [type(ents), ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
        arr, got = (_Ref * max(n.value, 1))(), ctypes.c_size_t()
        assert getattr(d, nome_get)(ents, n.value, arr, ctypes.byref(got)) == 0
    return list(arr)[: n.value]


def _arestas(d, ents):
    d.SUEdgeGetStartVertex.argtypes = [_Ref, P(_Ref)]
    d.SUEdgeGetEndVertex.argtypes = [_Ref, P(_Ref)]
    out = []
    for e in _lista(d, ents, "SUEntitiesGetNumEdges", "SUEntitiesGetEdges"):
        a, b = _Ref(), _Ref()
        assert d.SUEdgeGetStartVertex(e, ctypes.byref(a)) == 0 and d.SUEdgeGetEndVertex(e, ctypes.byref(b)) == 0
        out.append(frozenset((_pos(d, a), _pos(d, b))))
    return out


def _faces(d, ents):
    d.SUFaceGetNumVertices.argtypes = [_Ref, P(ctypes.c_size_t)]
    d.SUFaceGetVertices.argtypes = [_Ref, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
    out = []
    for f in _lista(d, ents, "SUEntitiesGetNumFaces", "SUEntitiesGetFaces"):
        n = ctypes.c_size_t()
        assert d.SUFaceGetNumVertices(f, ctypes.byref(n)) == 0
        vs, got = (_Ref * n.value)(), ctypes.c_size_t()
        assert d.SUFaceGetVertices(f, n.value, vs, ctypes.byref(got)) == 0
        out.append(frozenset(_pos(d, v) for v in vs))
    return out


def _curvas(d, ents):
    n = ctypes.c_size_t()
    d.SUEntitiesGetNumCurves.argtypes = [type(ents), P(ctypes.c_size_t)]
    assert d.SUEntitiesGetNumCurves(ents, ctypes.byref(n)) == 0
    return n.value


def _entidade_da_aresta(d, ents, a, b):
    d.SUEdgeToEntity.argtypes = [_Ref]
    d.SUEdgeToEntity.restype = _Ref
    d.SUEdgeGetStartVertex.argtypes = [_Ref, P(_Ref)]
    d.SUEdgeGetEndVertex.argtypes = [_Ref, P(_Ref)]
    for e in _lista(d, ents, "SUEntitiesGetNumEdges", "SUEntitiesGetEdges"):
        v1, v2 = _Ref(), _Ref()
        d.SUEdgeGetStartVertex(e, ctypes.byref(v1))
        d.SUEdgeGetEndVertex(e, ctypes.byref(v2))
        if frozenset((_pos(d, v1), _pos(d, v2))) == frozenset((a, b)):
            return d.SUEdgeToEntity(e)
    raise AssertionError(f"aresta {a}-{b} não existe")


def _entidade_da_face(d, ents, vertices):
    d.SUFaceToEntity.argtypes = [_Ref]
    d.SUFaceToEntity.restype = _Ref
    d.SUFaceGetNumVertices.argtypes = [_Ref, P(ctypes.c_size_t)]
    d.SUFaceGetVertices.argtypes = [_Ref, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
    for f in _lista(d, ents, "SUEntitiesGetNumFaces", "SUEntitiesGetFaces"):
        n = ctypes.c_size_t()
        d.SUFaceGetNumVertices(f, ctypes.byref(n))
        vs, got = (_Ref * n.value)(), ctypes.c_size_t()
        d.SUFaceGetVertices(f, n.value, vs, ctypes.byref(got))
        if frozenset(_pos(d, v) for v in vs) == frozenset(vertices):
            return d.SUFaceToEntity(f)
    raise AssertionError("face não existe")


def apagar(verts, faces=(), arestas_soltas=(), alvos=(), arcos=(), suaves=False) -> dict:
    """Monta a geometria, apaga os `alvos` e devolve {"faces": set de frozenset(posições), "arestas": ..., "curvas": n}.

    verts: lista de pontos; faces: listas de índices ou {"outer", "holes"}; arestas_soltas: pares de índices;
    alvos: [("aresta", a, b) | ("face", [posições dos vértices])] em posições; arcos: [(centro, início, fim, normal, nº)]."""
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        ents = m.get_entities()
        gi = _Ref()
        d.SUGeometryInputCreate.argtypes = [P(_Ref)]
        assert d.SUGeometryInputCreate(ctypes.byref(gi)) == 0
        d.SUGeometryInputAddVertex.argtypes = [_Ref, P(SUPoint3D)]
        for x, y, z in verts:
            assert d.SUGeometryInputAddVertex(gi, ctypes.byref(SUPoint3D(x=x, y=y, z=z))) == 0
        d.SULoopInputCreate.argtypes = [P(_Ref)]
        d.SULoopInputAddVertexIndex.argtypes = [_Ref, ctypes.c_size_t]
        d.SUGeometryInputAddFace.argtypes = [_Ref, P(_Ref), P(ctypes.c_size_t)]
        d.SUGeometryInputFaceAddInnerLoop.argtypes = [_Ref, ctypes.c_size_t, P(_Ref)]
        d.SUGeometryInputAddEdge.argtypes = [_Ref, ctypes.c_size_t, ctypes.c_size_t, P(ctypes.c_size_t)]

        def laco(idx):
            lp = _Ref()
            assert d.SULoopInputCreate(ctypes.byref(lp)) == 0
            for i in idx:
                assert d.SULoopInputAddVertexIndex(lp, i) == 0
            return lp

        for f in faces:
            spec = f if isinstance(f, dict) else {"outer": f, "holes": []}
            lp = laco(spec["outer"])
            indice = ctypes.c_size_t()
            assert d.SUGeometryInputAddFace(gi, ctypes.byref(lp), ctypes.byref(indice)) == 0
            for h in spec.get("holes", []):
                lh = laco(h)
                assert d.SUGeometryInputFaceAddInnerLoop(gi, indice.value, ctypes.byref(lh)) == 0
        for a, b in arestas_soltas:
            idx = ctypes.c_size_t()
            assert d.SUGeometryInputAddEdge(gi, a, b, ctypes.byref(idx)) == 0
        if verts:
            d.SUEntitiesFill.argtypes = [type(ents), _Ref, ctypes.c_bool]
            assert d.SUEntitiesFill(ents, gi, True) == 0
        arco_refs = []
        if arcos:
            from tools.conferir_arco_sdk import _vec
            from core.su_types import SUVector3D
            d.SUArcCurveCreate.argtypes = [P(_Ref), P(SUPoint3D), P(SUPoint3D), P(SUPoint3D), P(SUVector3D), ctypes.c_size_t]
            d.SUEntitiesAddArcCurves.argtypes = [type(ents), ctypes.c_size_t, P(_Ref)]
            for c, i, f, n, k in arcos:
                arco = _Ref()
                assert d.SUArcCurveCreate(ctypes.byref(arco), ctypes.byref(_vec(SUPoint3D, c)), ctypes.byref(_vec(SUPoint3D, i)),
                                          ctypes.byref(_vec(SUPoint3D, f)), ctypes.byref(_vec(SUVector3D, n)), k) == 0
                assert d.SUEntitiesAddArcCurves(ents, 1, (_Ref * 1)(arco)) == 0
                arco_refs.append(arco)
        if suaves:  # todas as arestas suaves (SUEdgeSetSoft) antes de apagar
            d.SUEdgeSetSoft.argtypes = [_Ref, ctypes.c_bool]
            for e in _lista(d, ents, "SUEntitiesGetNumEdges", "SUEntitiesGetEdges"):
                assert d.SUEdgeSetSoft(e, True) == 0
        inicial = {"faces": set(_faces(d, ents)), "arestas": set(_arestas(d, ents)), "curvas": _curvas(d, ents)}
        refs = []
        for alvo in alvos:
            if alvo[0] == "arco":  # a curva inteira, como entidade
                d.SUArcCurveToCurve.argtypes = [_Ref]
                d.SUArcCurveToCurve.restype = _Ref
                d.SUCurveToEntity.argtypes = [_Ref]
                d.SUCurveToEntity.restype = _Ref
                refs.append(d.SUCurveToEntity(d.SUArcCurveToCurve(arco_refs[alvo[1]])))
            elif alvo[0] == "aresta":
                refs.append(_entidade_da_aresta(d, ents, alvo[1], alvo[2]))
            else:
                refs.append(_entidade_da_face(d, ents, alvo[1]))
        d.SUEntitiesErase.argtypes = [type(ents), ctypes.c_size_t, P(_Ref)]
        r = d.SUEntitiesErase(ents, len(refs), (_Ref * len(refs))(*refs))
        assert r == 0, f"SUEntitiesErase devolveu {r}"
        return {"faces": set(_faces(d, ents)), "arestas": set(_arestas(d, ents)), "curvas": _curvas(d, ents), "inicial": inicial}
    finally:
        api.terminate()


if __name__ == "__main__":
    q = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
    r = apagar(q, [[0, 1, 2, 3]], alvos=[("aresta", q[0], q[1])])
    print("quadrado, aresta apagada:", len(r["faces"]), "faces,", len(r["arestas"]), "arestas")
    r = apagar(q, [[0, 1, 2, 3]], alvos=[("face", q)])
    print("quadrado, face apagada:", len(r["faces"]), "faces,", len(r["arestas"]), "arestas")
