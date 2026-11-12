"""Gera, pela SketchUpAPI (Python 3.12), modelos com cota radial/diâmetro sobre um arco (REA de FORMATO-SKP 7o).

`SUDimensionRadialCreate(saida, curva)` (assinatura lida no pseudocódigo da DLL). A cota fica ancorada na curva de arco já
incluída nas entidades. Variações pelo que a SDK expõe. Uso: py -3.12 tools/gerar_cota_radial_api.py [PASTA]
e depois tools/tlv_diff.py PASTA/r_base.skp PASTA/r_<variação>.skp

STATUS (12/11/2026): ainda NÃO funciona. `SUDimensionRadialCreate` dá access violation (leitura em 0x15) com o arco
recém-incluído nas entidades, com ou sem passar por `SUEntitiesGetArcCurves`/`SUArcCurveToCurve`. Pelo pseudocódigo ela
valida que a curva é de arco e lê o objeto do arco em `curva + 0x20`; a causa do crash não foi achada (ver FORMATO-SKP 7n)."""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUEntitiesRef, SUPoint3D, SUVector3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


P = ctypes.POINTER


def _pt(x, y, z):
    p = SUPoint3D()
    p.x, p.y, p.z = x, y, z
    return p


def _texto(d, r):
    d.SUDimensionSetText.argtypes = [_Ref, ctypes.c_char_p]
    assert d.SUDimensionSetText(r, b"Meu raio") == 0


def _seta(d, r):
    d.SUDimensionSetArrowType.argtypes = [_Ref, ctypes.c_int]
    assert d.SUDimensionSetArrowType(r, 1) == 0


# nome -> (centro, raio, função(d, ref) opcional)
VARIACOES = {
    "base": ((0, 0, 0), 50, None),
    "centro": ((10, 20, 5), 50, None),
    "raio": ((0, 0, 0), 30, None),
    "texto": ((0, 0, 0), 50, _texto),
    "seta1": ((0, 0, 0), 50, _seta),
}


def gerar(pasta: str, nome: str) -> str:
    centro, raio, aplicar = VARIACOES[nome]
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, f"r_{nome}.skp")
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        e = m.get_entities()
        v = SUVector3D()
        v.x, v.y, v.z = 0, 0, 1
        d.SUArcCurveCreate.argtypes = [P(_Ref), P(SUPoint3D), P(SUPoint3D), P(SUPoint3D), P(SUVector3D), ctypes.c_size_t]
        d.SUEntitiesAddArcCurves.argtypes = [SUEntitiesRef, ctypes.c_size_t, P(_Ref)]
        cv = _Ref()
        ini = (centro[0] + raio, centro[1], centro[2])
        fim = (centro[0], centro[1] + raio, centro[2])
        assert d.SUArcCurveCreate(ctypes.byref(cv), ctypes.byref(_pt(*centro)), ctypes.byref(_pt(*ini)),
                                  ctypes.byref(_pt(*fim)), ctypes.byref(v), 8) == 0
        assert d.SUEntitiesAddArcCurves(e, 1, (_Ref * 1)(cv)) == 0
        r = _Ref()
        d.SUDimensionRadialCreate.argtypes = [P(_Ref), _Ref]
        assert d.SUDimensionRadialCreate(ctypes.byref(r), cv) == 0
        if aplicar:
            aplicar(d, r)
        d.SUEntitiesAddDimensions.argtypes = [SUEntitiesRef, ctypes.c_size_t, P(_Ref)]
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
