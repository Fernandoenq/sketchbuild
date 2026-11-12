"""Gera, pela SketchUpAPI (Python 3.12), um .skp com arestas e faces ocultas em situações conhecidas.

Serve de oráculo para a poda de geometria oculta (core/skp_hidden_pruner.py, modo "total"):
  A  x=0     face visível, arestas visíveis
  B  x=200   face OCULTA, arestas visíveis        -> a face some, as arestas ficam
  C  x=400   face OCULTA e as 4 arestas ocultas   -> tudo some
  D  x=600   face visível com 1 aresta oculta     -> nada some (a aresta é de face viva)
  E  aresta solta oculta                          -> some
  F  aresta solta visível                         -> fica
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUEntitiesRef, SUPoint3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


def _quadrado(x):
    return [(x, 0, 0), (x + 100, 0, 0), (x + 100, 100, 0), (x, 100, 0)]


def gerar(destino: str) -> None:
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        e = m.get_entities()
        for x in (0, 200, 400, 600):
            api.add_face(e, _quadrado(x))
        faces = api.get_faces(e)
        # as faces voltam na ordem de criação; confere pelo x do primeiro vértice via área/ordem
        d.SUFaceToDrawingElement.restype = _Ref
        d.SUFaceToDrawingElement.argtypes = [type(faces[0])]
        d.SUEdgeToDrawingElement.restype = _Ref
        d.SUDrawingElementSetHidden.argtypes = [_Ref, ctypes.c_bool]

        def esconder_face(f):
            assert d.SUDrawingElementSetHidden(d.SUFaceToDrawingElement(f), True) == 0

        esconder_face(faces[1])
        esconder_face(faces[2])

        # arestas soltas E (oculta) e F (visível)
        d.SUEdgeCreate.argtypes = [ctypes.POINTER(_Ref), ctypes.POINTER(SUPoint3D), ctypes.POINTER(SUPoint3D)]
        d.SUEntitiesAddEdges.argtypes = [SUEntitiesRef, ctypes.c_size_t, ctypes.POINTER(_Ref)]
        d.SUEdgeToDrawingElement.argtypes = [_Ref]
        novas = []
        for y in (500, 700):
            ed = _Ref()
            p0, p1 = SUPoint3D(), SUPoint3D()
            p0.x, p0.y, p0.z = 0, y, 0
            p1.x, p1.y, p1.z = 100, y, 0
            assert d.SUEdgeCreate(ctypes.byref(ed), ctypes.byref(p0), ctypes.byref(p1)) == 0
            novas.append(ed)
        assert d.SUEntitiesAddEdges(e, 2, (_Ref * 2)(*novas)) == 0
        assert d.SUDrawingElementSetHidden(d.SUEdgeToDrawingElement(novas[0]), True) == 0

        # arestas das faces C (todas) e D (uma): precisa listar as arestas do modelo
        n = ctypes.c_size_t()
        d.SUEntitiesGetNumEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.POINTER(ctypes.c_size_t)]
        d.SUEntitiesGetNumEdges(e, False, ctypes.byref(n))
        arr = (_Ref * n.value)()
        got = ctypes.c_size_t()
        d.SUEntitiesGetEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.c_size_t, ctypes.POINTER(_Ref), ctypes.POINTER(ctypes.c_size_t)]
        d.SUEntitiesGetEdges(e, False, n.value, arr, ctypes.byref(got))
        d.SUEdgeGetStartVertex.argtypes = [_Ref, ctypes.POINTER(_Ref)]
        d.SUVertexGetPosition.argtypes = [_Ref, ctypes.POINTER(SUPoint3D)]
        d.SUEdgeGetEndVertex.argtypes = [_Ref, ctypes.POINTER(_Ref)]
        marcadas_d = False
        for i in range(got.value):
            v, w = _Ref(), _Ref()
            d.SUEdgeGetStartVertex(arr[i], ctypes.byref(v))
            d.SUEdgeGetEndVertex(arr[i], ctypes.byref(w))
            a, b = SUPoint3D(), SUPoint3D()
            d.SUVertexGetPosition(v, ctypes.byref(a))
            d.SUVertexGetPosition(w, ctypes.byref(b))
            xs = (a.x, b.x)
            if a.y in (500, 700) and b.y in (500, 700):
                continue
            if min(xs) >= 400 and max(xs) <= 500:  # face C
                assert d.SUDrawingElementSetHidden(d.SUEdgeToDrawingElement(arr[i]), True) == 0
            elif min(xs) >= 600 and not marcadas_d:  # face D: uma aresta só
                assert d.SUDrawingElementSetHidden(d.SUEdgeToDrawingElement(arr[i]), True) == 0
                marcadas_d = True
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        m.save(destino)
        m.close()
    finally:
        api.terminate()


def gerar_curva(destino: str) -> None:
    """Arco de 8 segmentos (curva de arco) com UMA aresta oculta, mais uma curva simples inteira visível."""
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        e = m.get_entities()

        def pt(x, y, z):
            q = SUPoint3D()
            q.x, q.y, q.z = x, y, z
            return q

        from core.su_types import SUVector3D
        v = SUVector3D()
        v.x, v.y, v.z = 0, 0, 1
        d.SUArcCurveCreate.argtypes = [ctypes.POINTER(_Ref), ctypes.POINTER(SUPoint3D), ctypes.POINTER(SUPoint3D),
                                       ctypes.POINTER(SUPoint3D), ctypes.POINTER(SUVector3D), ctypes.c_size_t]
        d.SUEntitiesAddArcCurves.argtypes = [SUEntitiesRef, ctypes.c_size_t, ctypes.POINTER(_Ref)]
        cv = _Ref()
        assert d.SUArcCurveCreate(ctypes.byref(cv), ctypes.byref(pt(0, 0, 0)), ctypes.byref(pt(50, 0, 0)),
                                  ctypes.byref(pt(0, 50, 0)), ctypes.byref(v), 8) == 0
        assert d.SUEntitiesAddArcCurves(e, 1, (_Ref * 1)(cv)) == 0
        n = ctypes.c_size_t()
        d.SUEntitiesGetNumEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.POINTER(ctypes.c_size_t)]
        d.SUEntitiesGetNumEdges(e, False, ctypes.byref(n))
        arr = (_Ref * n.value)()
        got = ctypes.c_size_t()
        d.SUEntitiesGetEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.c_size_t, ctypes.POINTER(_Ref), ctypes.POINTER(ctypes.c_size_t)]
        d.SUEntitiesGetEdges(e, False, n.value, arr, ctypes.byref(got))
        d.SUEdgeToDrawingElement.restype = _Ref
        d.SUEdgeToDrawingElement.argtypes = [_Ref]
        d.SUDrawingElementSetHidden.argtypes = [_Ref, ctypes.c_bool]
        assert d.SUDrawingElementSetHidden(d.SUEdgeToDrawingElement(arr[3]), True) == 0
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        m.save(destino)
        m.close()
    finally:
        api.terminate()


if __name__ == "__main__":
    gerar(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "ocultos_api.skp"))
    print("ok")
