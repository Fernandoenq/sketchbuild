"""Gera, pela SketchUpAPI (Python 3.12), modelos com uma cota linear e uma variação cada, para decifrar o `0x1399`.

Assinatura lida no REA da DLL: `SUDimensionLinearCreate(dim*, SUPoint3D* inicio, caminho, SUPoint3D* fim, caminho)`;
os caminhos de instância são opcionais (referência nula = ponto no espaço do modelo).
Uso:  py -3.12 tools/gerar_cotas_api.py PASTA   e depois   py -3.12 -I tools/tlv_diff.py PASTA/c_base.skp PASTA/c_<variação>.skp
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


def _pt(x, y, z):
    p = SUPoint3D()
    p.x, p.y, p.z = x, y, z
    return p


P = ctypes.POINTER


def _vetor(d, nome, vec):
    f = getattr(d, nome)
    f.argtypes = [_Ref, P(_Vec)]
    assert f(vec[0], ctypes.byref(_Vec(*vec[1]))) == 0, nome


def _ponto(d, nome, ref, pt):
    f = getattr(d, nome)
    f.argtypes = [_Ref, P(SUPoint3D)]
    assert f(ref, ctypes.byref(_pt(*pt))) == 0, nome


def _inteiro(d, nome, ref, v):
    f = getattr(d, nome)
    f.argtypes = [_Ref, ctypes.c_int]
    assert f(ref, v) == 0, nome


# nome da variação -> (início, fim, função(d, ref) que aplica a mudança)
VARIACOES = {
    "base": ((0, 0, 0), (100, 0, 0), None),
    "pontos": ((10, 20, 30), (110, 50, 30), None),
    "posicao": ((0, 0, 0), (100, 0, 0), lambda d, r: _ponto(d, "SUDimensionLinearSetPosition", r, (50, 25, 5))),
    "normal_y": ((0, 0, 0), (100, 0, 0), lambda d, r: _vetor(d, "SUDimensionLinearSetNormal", (r, (0, 1, 0)))),
    "xaxis_y": ((0, 0, 0), (100, 0, 0), lambda d, r: _vetor(d, "SUDimensionLinearSetXAxis", (r, (0, 1, 0)))),
    "seta1": ((0, 0, 0), (100, 0, 0), lambda d, r: _inteiro(d, "SUDimensionSetArrowType", r, 1)),
    "seta2": ((0, 0, 0), (100, 0, 0), lambda d, r: _inteiro(d, "SUDimensionSetArrowType", r, 2)),
    "halign1": ((0, 0, 0), (100, 0, 0), lambda d, r: _inteiro(d, "SUDimensionLinearSetHorizontalAlignment", r, 1)),
    "valign1": ((0, 0, 0), (100, 0, 0), lambda d, r: _inteiro(d, "SUDimensionLinearSetVerticalAlignment", r, 1)),
}


for _h in (0, 2, 3, 4):
    VARIACOES[f"halign{_h}"] = ((0, 0, 0), (100, 0, 0), lambda d, r, _h=_h: _inteiro(d, "SUDimensionLinearSetHorizontalAlignment", r, _h))
VARIACOES["halign1_pos"] = ((0, 0, 0), (100, 0, 0), lambda d, r: (_inteiro(d, "SUDimensionLinearSetHorizontalAlignment", r, 1),
                                                                  _ponto(d, "SUDimensionLinearSetPosition", r, (50, 25, 5))))
VARIACOES["pos_halign1"] = ((0, 0, 0), (100, 0, 0), lambda d, r: (_ponto(d, "SUDimensionLinearSetPosition", r, (50, 25, 5)),
                                                                  _inteiro(d, "SUDimensionLinearSetHorizontalAlignment", r, 1)))


def _texto(d, r):
    d.SUDimensionSetText.argtypes = [_Ref, ctypes.c_char_p]
    assert d.SUDimensionSetText(r, "Meu texto".encode("utf-8")) == 0


VARIACOES["texto"] = ((0, 0, 0), (100, 0, 0), _texto)


def gerar(pasta: str, nome: str) -> str:
    ini, fim, aplicar = VARIACOES[nome]
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, f"c_{nome}.skp")
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        e = m.get_entities()
        r = _Ref()
        d.SUDimensionLinearCreate.argtypes = [P(_Ref), P(SUPoint3D), _Ref, P(SUPoint3D), _Ref]
        assert d.SUDimensionLinearCreate(ctypes.byref(r), ctypes.byref(_pt(*ini)), _Ref(), ctypes.byref(_pt(*fim)), _Ref()) == 0
        if aplicar:
            aplicar(d, r)
        d.SUEntitiesAddDimensions.argtypes = [type(e), ctypes.c_size_t, P(_Ref)]
        assert d.SUEntitiesAddDimensions(e, 1, (_Ref * 1)(r)) == 0
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "cotas")
    for nome in VARIACOES:
        try:
            print(gerar(pasta, nome))
        except (AssertionError, AttributeError, OSError, RuntimeError) as ex:
            print("falhou", nome, ex)
