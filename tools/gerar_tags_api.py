"""Gera, pela SketchUpAPI (Python 3.12), .skp para o REA de tags (camadas) e cenas. Compare com tools/tlv_diff.py.

  base.skp   uma face, sem tag nova
  tag.skp    mesma face numa tag "Parede" (visível)
  tag_off.skp  mesma face numa tag "Oculta" com visibilidade desligada
  cena.skp   mesma face e uma cena "Cena 1" (SUSceneCreate)

Uso:  py -3.12 tools/gerar_tags_api.py PASTA
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


def gerar(pasta: str, modo: str) -> str:
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, modo + ".skp")
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    P = ctypes.POINTER
    try:
        m = api.create_blank_model()
        mr = type(m._model)
        e = m.get_entities()
        api.add_face(e, [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0)])
        face = api.get_faces(e)[0]
        if modo in ("tag", "tag_off"):
            nome = "Parede" if modo == "tag" else "Oculta"
            d.SULayerCreate.argtypes = [P(_Ref)]
            d.SULayerSetName.argtypes = [_Ref, ctypes.c_char_p]
            lay = _Ref()
            assert d.SULayerCreate(ctypes.byref(lay)) == 0
            assert d.SULayerSetName(lay, nome.encode("utf-8")) == 0
            if modo == "tag_off":
                d.SULayerSetVisibility.argtypes = [_Ref, ctypes.c_bool]
                assert d.SULayerSetVisibility(lay, False) == 0
            d.SUModelAddLayers.argtypes = [mr, ctypes.c_size_t, P(_Ref)]
            assert d.SUModelAddLayers(m._model, 1, (_Ref * 1)(lay)) == 0
            d.SUFaceToDrawingElement.restype = _Ref
            d.SUFaceToDrawingElement.argtypes = [type(face)]
            d.SUDrawingElementSetLayer.argtypes = [_Ref, _Ref]
            assert d.SUDrawingElementSetLayer(d.SUFaceToDrawingElement(face), lay) == 0
        elif modo == "cena":
            d.SUSceneCreate.argtypes = [P(_Ref)]
            d.SUSceneSetName.argtypes = [_Ref, ctypes.c_char_p]
            sc = _Ref()
            assert d.SUSceneCreate(ctypes.byref(sc)) == 0
            assert d.SUSceneSetName(sc, b"Cena 1") == 0
            d.SUModelAddScenes.argtypes = [mr, ctypes.c_size_t, P(_Ref)]
            assert d.SUModelAddScenes(m._model, 1, (_Ref * 1)(sc)) == 0
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "tags")
    for modo in ("base", "tag", "tag_off", "cena"):
        print(gerar(pasta, modo))
