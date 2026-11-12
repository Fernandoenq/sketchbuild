"""Gera, pela SketchUpAPI (Python 3.12), modelos com um texto livre e uma variação cada, para decifrar o registro do texto.

Causa do antigo `SU_ERROR_SERIALIZATION` (achada no REA da DLL em 12/11/2026): o texto novo nasce sem fonte; é preciso
aplicar uma das fontes do modelo (`SUModelGetFonts` + `SUTextSetFont`). `SUTextSetPoint(texto, ponto, caminho)` tem 3
parâmetros (o caminho de instância é opcional).
Uso:  py -3.12 tools/gerar_texto_api.py PASTA   e depois   py -3.12 -I tools/tlv_diff.py PASTA/t_base.skp PASTA/t_<variação>.skp
"""
import ctypes
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.su_api import SketchUpAPI  # noqa: E402
from core.su_types import SUModelRef, SUPoint3D  # noqa: E402


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class _Vec(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double), ("z", ctypes.c_double)]


class _Cor(ctypes.Structure):
    _fields_ = [("r", ctypes.c_ubyte), ("g", ctypes.c_ubyte), ("b", ctypes.c_ubyte), ("a", ctypes.c_ubyte)]


P = ctypes.POINTER


class _FontInput(ctypes.Structure):
    """Entrada de `SUModelAddFont(modelo, entrada, saida)` (lida no pseudocódigo da DLL): versão 1, nome, dois bytes
    (negrito/itálico, ordem a confirmar pelo diff), tamanho em pontos, flag de tamanho no mundo e esse tamanho."""
    _fields_ = [("versao", ctypes.c_int), ("nome", ctypes.c_char_p), ("b0", ctypes.c_ubyte), ("b1", ctypes.c_ubyte),
                ("pontos", ctypes.c_int), ("mundo", ctypes.c_ubyte), ("tam_mundo", ctypes.c_double)]


def _pt(x, y, z):
    p = SUPoint3D()
    p.x, p.y, p.z = x, y, z
    return p


# nome -> dict(texto, ponto, tipo (linha de chamada), vetor, seta, cor, fonte (índice em SUModelGetFonts))
VARIACOES = {
    "base": dict(),
    "ponto": dict(ponto=(10, 20, 30)),
    "ponto2": dict(ponto=(110, -20, 5)),
    "texto": dict(texto="Outro texto"),
    "tipo1": dict(tipo=1),
    "tipo2": dict(tipo=2),
    "vetor": dict(tipo=1, vetor=(0, 0, 40)),
    "seta1": dict(seta=1),
    "cor": dict(cor=(10, 20, 30, 255)),
    "fonte1": dict(fonte=1),
    # fonte nova do modelo (face, byte0, byte1, pontos); o modelo só serializa a fonte se algum texto a usa
    "tela": dict(tela=(0.2, 0.7)),
    "tela2": dict(tela=(1.0, 0.0)),
    "fn_base": dict(fonte_nova=(b"Arial", 0, 0, 12)),
    "fn_b0": dict(fonte_nova=(b"Arial", 1, 0, 12)),
    "fn_b1": dict(fonte_nova=(b"Arial", 0, 1, 12)),
    "fn_tam": dict(fonte_nova=(b"Arial", 0, 0, 24)),
    "fn_nome": dict(fonte_nova=(b"Courier New", 0, 0, 12)),
    "fn_cor_antes": dict(fonte_nova=(b"Arial", 1, 1, 18), cor=(10, 20, 30, 255), cor_antes=True),
    "fn_cor": dict(fonte_nova=(b"Arial", 1, 1, 18), cor=(10, 20, 30, 255)),
}


def gerar(pasta: str, nome: str) -> str:
    v = {"texto": "Nota", "ponto": (10, 20, 30), "tipo": 0, "vetor": None, "seta": None, "cor": None, "fonte": 0}
    v.update(VARIACOES[nome])
    os.makedirs(pasta, exist_ok=True)
    destino = os.path.join(pasta, f"t_{nome}.skp")
    api = SketchUpAPI()
    api.initialize()
    d = api._dll
    try:
        m = api.create_blank_model()
        e, mr = m.get_entities(), m._model
        n = ctypes.c_size_t()
        d.SUModelGetNumFonts.argtypes = [SUModelRef, P(ctypes.c_size_t)]
        assert d.SUModelGetNumFonts(mr, ctypes.byref(n)) == 0 and n.value > v["fonte"]
        fontes, got = (_Ref * n.value)(), ctypes.c_size_t()
        d.SUModelGetFonts.argtypes = [SUModelRef, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
        assert d.SUModelGetFonts(mr, n.value, fontes, ctypes.byref(got)) == 0
        r = _Ref()
        d.SUTextCreate.argtypes = [P(_Ref)]
        assert d.SUTextCreate(ctypes.byref(r)) == 0
        d.SUTextSetString.argtypes = [_Ref, ctypes.c_char_p]
        assert d.SUTextSetString(r, v["texto"].encode("utf-8")) == 0
        d.SUTextSetLeaderType.argtypes = [_Ref, ctypes.c_int]
        assert d.SUTextSetLeaderType(r, v["tipo"]) == 0
        d.SUTextSetPoint.argtypes = [_Ref, P(SUPoint3D), _Ref]
        assert d.SUTextSetPoint(r, ctypes.byref(_pt(*v["ponto"])), _Ref()) == 0
        d.SUTextSetFont.argtypes = [_Ref, _Ref]
        if v.get("cor_antes"):  # cor antes da fonte nova: confere a ordem dos ids
            d.SUTextSetColor.argtypes = [_Ref, P(_Cor)]
            assert d.SUTextSetColor(r, ctypes.byref(_Cor(*v["cor"]))) == 0
        fonte = fontes[v["fonte"]]
        if v.get("fonte_nova"):
            fn = v["fonte_nova"]
            d.SUModelAddFont.argtypes = [SUModelRef, P(_FontInput), P(_Ref)]
            fonte = _Ref()
            assert d.SUModelAddFont(mr, ctypes.byref(_FontInput(1, fn[0], fn[1], fn[2], fn[3], 0, 0.0)), ctypes.byref(fonte)) == 0
        assert d.SUTextSetFont(r, fonte) == 0
        if v.get("tela"):
            d.SUTextSetScreenPosition.argtypes = [_Ref, ctypes.c_double, ctypes.c_double]
            assert d.SUTextSetScreenPosition(r, v["tela"][0], v["tela"][1]) == 0  # só com linha de chamada tipo 0
        if v["vetor"]:
            d.SUTextSetLeaderVector.argtypes = [_Ref, P(_Vec)]
            assert d.SUTextSetLeaderVector(r, ctypes.byref(_Vec(*v["vetor"]))) == 0
        if v["seta"] is not None:
            d.SUTextSetArrowType.argtypes = [_Ref, ctypes.c_int]
            assert d.SUTextSetArrowType(r, v["seta"]) == 0
        if v["cor"] and not v.get("cor_antes"):
            d.SUTextSetColor.argtypes = [_Ref, P(_Cor)]
            assert d.SUTextSetColor(r, ctypes.byref(_Cor(*v["cor"]))) == 0
        d.SUEntitiesAddTexts.argtypes = [type(e), ctypes.c_size_t, P(_Ref)]
        assert d.SUEntitiesAddTexts(e, 1, (_Ref * 1)(r)) == 0
        m.save(destino)
        m.close()
    finally:
        api.terminate()
    return destino


if __name__ == "__main__":
    pasta = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.expanduser("~"), "sketchup_gerados", "textos")
    for nome in VARIACOES:
        try:
            print(gerar(pasta, nome))
        except (AssertionError, AttributeError, OSError, RuntimeError) as ex:
            print("falhou", nome, ex)
