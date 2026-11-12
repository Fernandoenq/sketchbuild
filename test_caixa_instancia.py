"""Caixa limite de instância (core/caixa_instancia.py), conferida com a SketchUpAPI e com o arquivo real do SketchUp."""
import ctypes
import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.caixa_instancia import caixa_instancia  # noqa: E402

try:
    from core.su_api import SketchUpAPI
    from core.su_types import SUModelRef, SUPoint3D
    _api = SketchUpAPI()
    _api.initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False

P = ctypes.POINTER


class _Ref(ctypes.Structure):
    _fields_ = [("ptr", ctypes.c_void_p)]


class _BB(ctypes.Structure):
    _fields_ = [("a", SUPoint3D if DISPONIVEL else ctypes.c_double), ("b", SUPoint3D if DISPONIVEL else ctypes.c_double)]


class _Tr(ctypes.Structure):
    _fields_ = [("v", ctypes.c_double * 16)]


def _pt(x, y, z):
    p = SUPoint3D()
    p.x, p.y, p.z = x, y, z
    return p


def caixa_da_sdk(pontos, matriz, face_me):
    """Caixa que a SketchUpAPI calcula para uma instância (definição com um triângulo/retângulo por face dada)."""
    d = _api._dll
    m = _api.create_blank_model()
    try:
        e, mr = m.get_entities(), m._model
        df = _Ref()
        d.SUComponentDefinitionCreate.argtypes = [P(_Ref)]
        d.SUComponentDefinitionCreate(ctypes.byref(df))
        d.SUModelAddComponentDefinitions.argtypes = [SUModelRef, ctypes.c_size_t, P(_Ref)]
        d.SUModelAddComponentDefinitions(mr, 1, (_Ref * 1)(df))
        d.SUComponentDefinitionGetEntities.argtypes = [_Ref, P(type(e))]
        de = type(e)()
        d.SUComponentDefinitionGetEntities(df, ctypes.byref(de))
        _api.add_face(de, pontos)
        if face_me:
            raw = (ctypes.c_ubyte * 16)()
            d.SUComponentDefinitionGetBehavior.argtypes = [_Ref, ctypes.c_void_p]
            d.SUComponentDefinitionSetBehavior.argtypes = [_Ref, ctypes.c_void_p]
            d.SUComponentDefinitionGetBehavior(df, raw)
            raw[5] = 1  # always_face_camera
            assert d.SUComponentDefinitionSetBehavior(df, raw) == 0
        inst = _Ref()
        d.SUComponentDefinitionCreateInstance.argtypes = [_Ref, P(_Ref)]
        d.SUComponentDefinitionCreateInstance(df, ctypes.byref(inst))
        t = _Tr()
        for i, x in enumerate(matriz):
            t.v[i] = x
        d.SUComponentInstanceSetTransform.argtypes = [_Ref, P(_Tr)]
        d.SUComponentInstanceSetTransform(inst, ctypes.byref(t))
        d.SUEntitiesAddInstance.argtypes = [type(e), _Ref, ctypes.c_void_p]
        d.SUEntitiesAddInstance(e, inst, None)
        d.SUComponentInstanceToDrawingElement.restype = _Ref
        d.SUComponentInstanceToDrawingElement.argtypes = [_Ref]
        d.SUDrawingElementGetBoundingBox.argtypes = [_Ref, P(_BB)]
        b = _BB()
        assert d.SUDrawingElementGetBoundingBox(d.SUComponentInstanceToDrawingElement(inst), ctypes.byref(b)) == 0
        return (b.a.x, b.a.y, b.a.z), (b.b.x, b.b.y, b.b.z)
    finally:
        m.close()


def _giro_z(graus, trans, escala=1.0):
    c, s = math.cos(math.radians(graus)) * escala, math.sin(math.radians(graus)) * escala
    return [c, s, 0, 0, -s, c, 0, 0, 0, 0, escala, 0, trans[0], trans[1], trans[2], 1]


class TestCaixaDoArquivoReal(unittest.TestCase):
    def test_boneco_face_me_do_sketchup(self):
        """Valores do `Sem nome.skp` salvo pelo SketchUp: definição de x -7,2254 a 17,6068, y 0, z -0,0538 a 62,6806."""
        pontos = [(-7.225447495924147, 0.0, -0.05382196873400957), (17.60676097042799, 0.0, 62.68060281682699)]
        m = [0.83909, -0.543993, 0, 0, 0.543993, 0.83909, 0, 0, 0, 0, 1, 0, -14.433072, -24.632453, 0, 1]
        lo, hi = caixa_instancia(pontos, m, face_me=True)
        esperado = (-38.784679, -48.98406, -0.053822), (9.918535, -0.280846, 62.680603)
        for got, want in zip(lo + hi, esperado[0] + esperado[1]):
            self.assertAlmostEqual(got, want, delta=1e-3)

    def test_instancia_comum_usa_os_oito_cantos(self):
        lo, hi = caixa_instancia([(0, 0, 0), (10, 20, 30)], _giro_z(90, (100, 0, 5)))
        for got, want in zip(lo + hi, (80, 0, 5, 100, 10, 35)):
            self.assertAlmostEqual(got, want, places=9)

    def test_definicao_vazia_e_escala_nula(self):
        with self.assertRaises(ValueError):
            caixa_instancia([], _giro_z(0, (0, 0, 0)))
        with self.assertRaises(ValueError):
            caixa_instancia([(1, 1, 1)], [0] * 16, face_me=True)


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestCaixaContraASdk(unittest.TestCase):
    def test_formas_giros_e_deslocamentos_aleatorios(self):
        rnd = random.Random(7)
        for _ in range(25):
            pontos = [(rnd.uniform(-20, 20), rnd.uniform(-20, 20), rnd.uniform(0, 60)) for _ in range(3)]
            # a face precisa ser plana e não degenerada: três pontos sempre formam um triângulo
            matriz = _giro_z(rnd.uniform(-180, 180), (rnd.uniform(-300, 300), rnd.uniform(-300, 300), rnd.uniform(0, 50)))
            for face_me in (False, True):
                with self.subTest(face_me=face_me, pontos=pontos):
                    sdk = caixa_da_sdk(pontos, matriz, face_me)
                    lo, hi = caixa_instancia(pontos, matriz, face_me)
                    for got, want in zip(lo + hi, sdk[0] + sdk[1]):
                        self.assertAlmostEqual(got, want, places=4)


if __name__ == "__main__":
    unittest.main()
