"""Gera, pela SketchUpAPI (Python 3.12), variações de cena para o REA (compare com tools/tlv_diff.py).

  c_base        uma cena só com nome
  c_desc        + descrição
  c_camera      + câmera em outra posição (SUSceneSetCamera)
  c_sem_camera  SUSceneSetUseCamera(False)
  c_tag         tag "Parede" desligada nesta cena (SUSceneAddLayer)
  c_anim        fora da animação (SUSceneSetIncludeInAnimation False)
  c_duas        duas cenas

Uso:  py -3.12 tools/gerar_cenas_api.py PASTA
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUPoint3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class _Vec(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


VARIACOES = ("c_base", "c_desc", "c_camera", "c_sem_camera", "c_tag", "c_anim", "c_duas")


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
        lay = None
        if modo == "c_tag":
            d.SULayerCreate.argtypes = [P(_Ref)]
            d.SULayerSetName.argtypes = [_Ref, ctypes.c_char_p]
            lay = _Ref()
            assert d.SULayerCreate(ctypes.byref(lay)) == 0
            assert d.SULayerSetName(lay, b"Parede") == 0
            d.SUModelAddLayers.argtypes = [mr, ctypes.c_size_t, P(_Ref)]
            assert d.SUModelAddLayers(m._model, 1, (_Ref * 1)(lay)) == 0
        d.SUSceneCreate.argtypes = [P(_Ref)]
        d.SUSceneSetName.argtypes = [_Ref, ctypes.c_char_p]
        d.SUModelAddScenes.argtypes = [mr, ctypes.c_size_t, P(_Ref)]
        n_cenas = 2 if modo == "c_duas" else 1
        cenas = []
        for k in range(n_cenas):
            sc = _Ref()
            assert d.SUSceneCreate(ctypes.byref(sc)) == 0
            assert d.SUSceneSetName(sc, f"Cena {k + 1}".encode("utf-8")) == 0
            if modo == "c_desc":
                d.SUSceneSetDescription.argtypes = [_Ref, ctypes.c_char_p]
                assert d.SUSceneSetDescription(sc, b"Descricao teste") == 0
            if modo == "c_camera":
                cam = _Ref()
                d.SUModelGetCamera.argtypes = [mr, P(_Ref)]
                assert d.SUModelGetCamera(m._model, ctypes.byref(cam)) == 0
                pos, alvo, up = SUPoint3D(), SUPoint3D(), _Vec()
                pos.x, pos.y, pos.z = 300, -400, 200
                alvo.x, alvo.y, alvo.z = 50, 50, 0
                up.x, up.y, up.z = 0, 0, 1
                d.SUCameraSetOrientation.argtypes = [_Ref, P(SUPoint3D), P(SUPoint3D), P(_Vec)]
                assert d.SUCameraSetOrientation(cam, ctypes.byref(pos), ctypes.byref(alvo), ctypes.byref(up)) == 0
                d.SUSceneSetCamera.argtypes = [_Ref, P(_Ref)]
                assert d.SUSceneSetCamera(sc, ctypes.byref(cam)) == 0
            if modo == "c_sem_camera":
                d.SUSceneSetUseCamera.argtypes = [_Ref, ctypes.c_bool]
                assert d.SUSceneSetUseCamera(sc, False) == 0
            if modo == "c_anim":
                d.SUSceneSetIncludeInAnimation.argtypes = [_Ref, ctypes.c_bool]
                assert d.SUSceneSetIncludeInAnimation(sc, False) == 0
            cenas.append(sc)
        assert d.SUModelAddScenes(m._model, n_cenas, (_Ref * n_cenas)(*cenas)) == 0
        if modo == "c_tag":
            d.SUSceneAddLayer.argtypes = [_Ref, _Ref]
            assert d.SUSceneAddLayer(cenas[0], lay) == 0
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "cenas")
    for modo in VARIACOES:
        try:
            print(gerar(pasta, modo))
        except AssertionError as ex:
            print("falhou", modo, ex)
