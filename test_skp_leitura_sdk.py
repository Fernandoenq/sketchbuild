"""Releitura pela SketchUpAPI de textos e cotas gravados pelo gravador: os getters da SDK confirmam o significado dos campos
(complementa a comparação byte a byte, que só prova igualdade com um arquivo da própria SDK)."""
import ctypes
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.skp_topology_writer import gravar_topologia  # noqa: E402
from core.topology import Topology  # noqa: E402
from core.topology.cotas import cota_linear  # noqa: E402
from core.topology.texto import texto_livre  # noqa: E402

try:
    from core.su_api import SketchUpAPI
    from core.su_types import SUEntitiesRef, SUPoint3D, SUVector3D
    _api = SketchUpAPI()
    _api.initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class _Str(ctypes.Structure):
    _fields_ = [("d", ctypes.c_void_p), ("n", ctypes.c_size_t), ("c", ctypes.c_size_t), ("e", ctypes.c_int)]


P = ctypes.POINTER


def _lista(d, ents, tipo):
    n = ctypes.c_size_t()
    getattr(d, f"SUEntitiesGetNum{tipo}").argtypes = [SUEntitiesRef, P(ctypes.c_size_t)]
    assert getattr(d, f"SUEntitiesGetNum{tipo}")(ents, ctypes.byref(n)) == 0
    arr, got = (_Ref * max(n.value, 1))(), ctypes.c_size_t()
    getattr(d, f"SUEntitiesGet{tipo}").argtypes = [SUEntitiesRef, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
    assert getattr(d, f"SUEntitiesGet{tipo}")(ents, n.value, arr, ctypes.byref(got)) == 0
    return list(arr)[:got.value]


def _get(d, nome, ref, tipo):
    f = getattr(d, nome)
    f.argtypes = [_Ref, P(tipo)]
    v = tipo()
    assert f(ref, ctypes.byref(v)) == 0, nome
    return v


def _com_caminho(d, nome, ref):
    """Getters de ponto (`SUTextGetPoint`, `SUDimensionLinearGet{Start,End}Point`) têm um 3º parâmetro de saída, o caminho
    de instância, que precisa existir (`SUInstancePathCreate`); com NULL a SDK devolve SU_ERROR_NULL_POINTER_OUTPUT."""
    caminho = _Ref()
    d.SUInstancePathCreate.argtypes = [P(_Ref)]
    assert d.SUInstancePathCreate(ctypes.byref(caminho)) == 0
    f = getattr(d, nome)
    f.argtypes = [_Ref, P(SUPoint3D), P(_Ref)]
    v = SUPoint3D()
    assert f(ref, ctypes.byref(v), ctypes.byref(caminho)) == 0, nome
    d.SUInstancePathRelease.argtypes = [P(_Ref)]
    d.SUInstancePathRelease(ctypes.byref(caminho))
    return v


def _pt(p):
    return (round(p.x, 6), round(p.y, 6), round(p.z, 6))


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestLeituraPelaSdk(unittest.TestCase):
    def _abrir(self, t):
        d = _tmp = tempfile.TemporaryDirectory()
        self.addCleanup(_tmp.cleanup)
        p = os.path.join(d.name, "x.skp")
        gravar_topologia(t, p)
        return _api._dll, _api.open_model(p)

    def test_texto(self):
        t = Topology()
        texto_livre(t, "Olá", (10, 20, 30), tipo=1, vetor=(0, 0, 40), seta=1, fonte=3)
        d, m = self._abrir(t)
        try:
            r = _lista(d, m.get_entities(), "Texts")[0]
            self.assertEqual(_pt(_com_caminho(d, "SUTextGetPoint", r)), (10.0, 20.0, 30.0))
            self.assertEqual(_pt(_get(d, "SUTextGetLeaderVector", r, SUVector3D)), (0.0, 0.0, 40.0))
            self.assertEqual(_get(d, "SUTextGetLeaderType", r, ctypes.c_int).value, 1)
            self.assertEqual(_get(d, "SUTextGetArrowType", r, ctypes.c_int).value, 1)
        finally:
            m.close()

    def test_texto_com_tela(self):
        t = Topology()
        texto_livre(t, "Nota", (1, 2, 3), tela=(0.2, 0.7))
        d, m = self._abrir(t)
        try:
            r = _lista(d, m.get_entities(), "Texts")[0]
            x, y = ctypes.c_double(), ctypes.c_double()
            d.SUTextGetScreenPosition.argtypes = [_Ref, P(ctypes.c_double), P(ctypes.c_double)]
            self.assertEqual(d.SUTextGetScreenPosition(r, ctypes.byref(x), ctypes.byref(y)), 0)
            self.assertEqual((round(x.value, 6), round(y.value, 6)), (0.2, 0.7))
        finally:
            m.close()

    def test_cota(self):
        t = Topology()
        cota_linear(t, (10, 20, 30), (110, 20, 30), normal=(0, 1, 0), eixo_x=(1, 0, 0), seta=2, desloc=(50.0, 25.0))
        d, m = self._abrir(t)
        try:
            r = _lista(d, m.get_entities(), "Dimensions")[0]
            d.SUDimensionLinearFromDimension.restype = _Ref
            d.SUDimensionLinearFromDimension.argtypes = [_Ref]
            lin = d.SUDimensionLinearFromDimension(r)
            self.assertEqual(_pt(_com_caminho(d, "SUDimensionLinearGetStartPoint", lin)), (10.0, 20.0, 30.0))
            self.assertEqual(_pt(_com_caminho(d, "SUDimensionLinearGetEndPoint", lin)), (110.0, 20.0, 30.0))
            self.assertEqual(_pt(_get(d, "SUDimensionLinearGetNormal", lin, SUVector3D)), (0.0, 1.0, 0.0))
            self.assertEqual(_pt(_get(d, "SUDimensionLinearGetXAxis", lin, SUVector3D)), (1.0, 0.0, 0.0))
            self.assertEqual(_get(d, "SUDimensionGetArrowType", r, ctypes.c_int).value, 2)
        finally:
            m.close()

    def test_alinhamentos_da_cota(self):
        casos = ((dict(alinhamento_h=0), 0, 1), (dict(alinhamento_h=1), 1, 1), (dict(alinhamento_h=2), 2, 1),
                 (dict(alinhamento_v=0), 0, 1))
        for args, h, _ in casos:
            with self.subTest(args):
                t = Topology()
                cota_linear(t, (0, 0, 0), (100, 0, 0), **args)
                d, m = self._abrir(t)
                try:
                    r = _lista(d, m.get_entities(), "Dimensions")[0]
                    d.SUDimensionLinearFromDimension.restype = _Ref
                    d.SUDimensionLinearFromDimension.argtypes = [_Ref]
                    lin = d.SUDimensionLinearFromDimension(r)
                    lido = {}
                    for nome in ("Horizontal", "Vertical"):
                        f = getattr(d, f"SUDimensionLinearGet{nome}Alignment")
                        f.argtypes = [_Ref, P(ctypes.c_int)]
                        v = ctypes.c_int()
                        self.assertEqual(f(lin, ctypes.byref(v)), 0)
                        lido[nome] = v.value
                    if "alinhamento_h" in args:
                        self.assertEqual((lido["Horizontal"], lido["Vertical"]), (h, 0))  # 0x5bd4 padrão (1) lê vertical 0
                    else:
                        self.assertEqual(lido["Vertical"], 1)  # 0x5bd4 = 0 lê vertical 1 (a SDK grava 0 para SetVerticalAlignment(1))
                finally:
                    m.close()

    def test_comportamento_do_componente(self):
        from core.skp_topology_writer import gravar_cena
        from core.su_types import SUModelRef
        from core.topology.cena import Cena
        from core.topology.draw import desenhar
        casos = (dict(face_me=True), dict(corta_abertura=True), dict(sombra_sol=True), dict(snap=3), dict(face_me=True, snap=1))
        for args in casos:
            with self.subTest(args):
                c = Cena()
                desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(30, 20, 0))
                i = c.criar_componente(faces=[max(c.topo.faces)], nome="Boneco")
                c.definir_comportamento(c.instancias[i].definicao, **args)
                with tempfile.TemporaryDirectory() as tmp:
                    p = os.path.join(tmp, "c.skp")
                    gravar_cena(c, p)
                    d, m = _api._dll, _api.open_model(p)
                    try:
                        n = ctypes.c_size_t()
                        d.SUModelGetNumComponentDefinitions.argtypes = [SUModelRef, P(ctypes.c_size_t)]
                        self.assertEqual(d.SUModelGetNumComponentDefinitions(m._model, ctypes.byref(n)), 0)
                        arr, got = (_Ref * max(n.value, 1))(), ctypes.c_size_t()
                        d.SUModelGetComponentDefinitions.argtypes = [SUModelRef, ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
                        self.assertEqual(d.SUModelGetComponentDefinitions(m._model, n.value, arr, ctypes.byref(got)), 0)
                        raw = (ctypes.c_ubyte * 16)()
                        d.SUComponentDefinitionGetBehavior.argtypes = [_Ref, ctypes.c_void_p]
                        self.assertEqual(d.SUComponentDefinitionGetBehavior(arr[0], raw), 0)
                        # estrutura SUComponentBehavior: byte 0 snap, 4 corta abertura, 5 face-me, 6 sombra segue o sol
                        self.assertEqual((raw[0], bool(raw[4]), bool(raw[5]), bool(raw[6])),
                                         (args.get("snap", 0), args.get("corta_abertura", False),
                                          args.get("face_me", False), args.get("sombra_sol", False)))
                    finally:
                        m.close()


if __name__ == "__main__":
    unittest.main()
