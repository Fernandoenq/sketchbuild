"""Oráculo da fusão de faces coplanares: o que `SUModelMergeCoplanarFaces` e `SUEntitiesWeld` da SketchUpAPI fazem.
Uso: py -3.12 tools/conferir_fundir_sdk.py"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from tools.conferir_apagar_sdk import P, _arestas, _faces, _Ref  # noqa: E402
from tools.conferir_desenho_em_face_sdk import _passo  # noqa: E402


def fundir(passos, como="modelo") -> dict:
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        ents = m.get_entities()
        for p in passos:
            _passo(d, ents, p["verts"], p.get("faces", ()), p.get("arestas", ()))
        antes = (len(_faces(d, ents)), len(_arestas(d, ents)))
        if como == "modelo":
            f = d.SUModelMergeCoplanarFaces
            f.argtypes = [type(m._model) if hasattr(m, "_model") else _Ref]
            r = f(m._model if hasattr(m, "_model") else m)
        else:
            f = d.SUEntitiesWeld
            r = -1
        return {"codigo": r, "antes": antes, "depois": (len(_faces(d, ents)), len(_arestas(d, ents)))}
    finally:
        api.terminate()


if __name__ == "__main__":
    dois = [{"verts": [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)], "faces": [[0, 1, 2, 3]]},
            {"verts": [(10, 0, 0), (20, 0, 0), (20, 10, 0), (10, 10, 0)], "faces": [[0, 1, 2, 3]]}]
    print("dois quadrados coplanares:", fundir(dois))
