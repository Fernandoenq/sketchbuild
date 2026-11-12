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
        lo, hi = caixa_instancia([(1, 1, 1)], [0] * 16, face_me=True)  # escala nula: caixa degenera num ponto
        self.assertEqual((lo, hi), ((0, 0, 0), (0, 0, 0)))


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

    def test_giros_em_x_y_z_e_escala_uniforme(self):
        rnd = random.Random(11)
        for _ in range(25):
            pontos = [(rnd.uniform(-20, 20), rnd.uniform(-20, 20), rnd.uniform(0, 60)) for _ in range(3)]
            ax, ay, az, s = rnd.uniform(-3, 3), rnd.uniform(-1.5, 1.5), rnd.uniform(-3, 3), rnd.uniform(0.3, 3)
            cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
            r = [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
                 [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx], [-sy, cy * sx, cy * cx]]
            matriz = [0.0] * 16
            for j in range(3):
                for i in range(3):
                    matriz[4 * j + i] = r[i][j] * s
            matriz[12:16] = [rnd.uniform(-300, 300), rnd.uniform(-300, 300), rnd.uniform(0, 50), 1.0]
            for face_me in (False, True):
                with self.subTest(face_me=face_me, pontos=pontos):
                    sdk = caixa_da_sdk(pontos, matriz, face_me)
                    lo, hi = caixa_instancia(pontos, matriz, face_me)
                    for got, want in zip(lo + hi, sdk[0] + sdk[1]):
                        self.assertAlmostEqual(got, want, places=4)


def caixa_da_raiz(caminho):
    """Seis f64 do 0x13a0 que fecha o 0x1388 da raiz do modelo (ou None)."""
    import struct
    import zipfile
    dat = zipfile.ZipFile(caminho).read("model.dat")
    i = dat.rfind(struct.pack("<HI", 0x13A0, 48))
    return struct.unpack("<6d", dat[i + 6:i + 54]) if i >= 0 else None


class TestCaixaNoGravador(unittest.TestCase):
    def _cena(self):
        from core.topology import Topology  # noqa: F401
        from core.topology.cena import Cena
        from core.topology.draw import desenhar
        c = Cena()
        desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        desenhar(c.topo, "retangulo", p0=(500, 0, 0), p1=(540, 40, 0))
        g = c.criar_grupo(faces=[max(c.topo.faces)], nome="G")
        c.instancias[g].transformacao = _giro_z(33, (1000, 2000, 50))
        return c

    def test_raiz_leva_a_uniao_da_geometria_com_as_instancias(self):
        import tempfile
        from core.skp_topology_writer import gravar_cena
        c = self._cena()
        raiz, grupo = c.defs[0], c.defs[next(i for i in c.defs if i)]
        lo_g, hi_g = caixa_instancia(list(grupo.verts.values()), next(iter(c.instancias.values())).transformacao)
        pts = list(raiz.verts.values()) + [lo_g, hi_g]
        esperado = [min(p[k] for p in pts) for k in range(3)] + [max(p[k] for p in pts) for k in range(3)]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.skp")
            gravar_cena(c, p)
            for got, want in zip(caixa_da_raiz(p), esperado):
                self.assertAlmostEqual(got, want, places=6)

    @unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
    def test_caixa_da_instancia_gravada_bate_com_a_da_sdk(self):
        import tempfile
        from core.skp_topology_writer import gravar_cena
        c = self._cena()
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.skp")
            gravar_cena(c, p)
            d_ = _api._dll
            m = _api.open_model(p)
            try:
                e = m.get_entities()
                n = ctypes.c_size_t()
                d_.SUEntitiesGetNumInstances.argtypes = [type(e), P(ctypes.c_size_t)]
                d_.SUEntitiesGetNumInstances(e, ctypes.byref(n))
                grupos = ctypes.c_size_t()
                d_.SUEntitiesGetNumGroups.argtypes = [type(e), P(ctypes.c_size_t)]
                d_.SUEntitiesGetNumGroups(e, ctypes.byref(grupos))
                self.assertEqual(grupos.value, 1)
                arr = (_Ref * 1)()
                got = ctypes.c_size_t()
                d_.SUEntitiesGetGroups.argtypes = [type(e), ctypes.c_size_t, P(_Ref), P(ctypes.c_size_t)]
                d_.SUEntitiesGetGroups(e, 1, arr, ctypes.byref(got))
                d_.SUGroupToDrawingElement.restype = _Ref
                d_.SUGroupToDrawingElement.argtypes = [_Ref]
                d_.SUDrawingElementGetBoundingBox.argtypes = [_Ref, P(_BB)]
                b = _BB()
                self.assertEqual(d_.SUDrawingElementGetBoundingBox(d_.SUGroupToDrawingElement(arr[0]), ctypes.byref(b)), 0)
                sdk = (b.a.x, b.a.y, b.a.z, b.b.x, b.b.y, b.b.z)
            finally:
                m.close()
            grupo = c.defs[next(i for i in c.defs if i)]
            lo, hi = caixa_instancia(list(grupo.verts.values()), next(iter(c.instancias.values())).transformacao)
            for got, want in zip(lo + hi, sdk):
                self.assertAlmostEqual(got, want, places=4)


def _registro_1b58(caminho, em_definicao=True):
    """Bytes do primeiro 0x1b58 dentro de 0x157c (definição) do arquivo."""
    import struct
    import zipfile
    dat = zipfile.ZipFile(caminho).read("model.dat")
    i = dat.find(struct.pack("<H", 0x157C))
    j = dat.find(struct.pack("<HI", 0x1B58, 48), i)
    return dat[j:j + 54]


class TestComportamentoDoComponente(unittest.TestCase):
    def _cena_face_me(self, **comportamento):
        from core.topology.cena import Cena
        from core.topology.draw import desenhar
        c = Cena()
        desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(30, 20, 0))
        comp = c.criar_componente(faces=[max(c.topo.faces)], nome="Boneco")
        c.instancias[comp].transformacao = _giro_z(33, (100, 200, 0))
        c.definir_comportamento(c.instancias[comp].definicao, **comportamento)
        return c, comp

    def test_validacoes(self):
        from core.topology.cena import Cena
        from core.topology.draw import desenhar
        c = Cena()
        desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(30, 20, 0))
        grupo = c.criar_grupo(faces=[max(c.topo.faces)])
        with self.assertRaises(ValueError):
            c.definir_comportamento(c.instancias[grupo].definicao, face_me=True)  # grupo não tem comportamento
        with self.assertRaises(ValueError):
            c.definir_comportamento(0, face_me=True)  # raiz
        with self.assertRaises(ValueError):
            c.definir_comportamento(99, face_me=True)

    @unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
    def test_registro_igual_ao_da_sdk_e_caixa_face_me_igual(self):
        import tempfile
        from core.skp_topology_writer import gravar_cena
        casos = {"base": {}, "facame": dict(face_me=True), "corta": dict(corta_abertura=True), "sombra": dict(sombra_sol=True),
                  "snap1": dict(snap=1), "snap2": dict(snap=2), "snap3": dict(snap=3), "snap4": dict(snap=4)}
        gerado = os.path.join(os.path.expanduser("~"), "sketchup_gerados", "comport")
        with tempfile.TemporaryDirectory() as d:
            for nome, args in casos.items():
                with self.subTest(nome):
                    c, _ = self._cena_face_me(**args)
                    p = os.path.join(d, nome + ".skp")
                    gravar_cena(c, p)
                    sdk = os.path.join(gerado, nome + ".skp")
                    if not os.path.exists(sdk):
                        self.skipTest("rode tools/gerar_comportamento_api.py antes")
                    self.assertEqual(_registro_1b58(p), _registro_1b58(sdk))
            c, comp = self._cena_face_me(face_me=True)
            p = os.path.join(d, "fm.skp")
            gravar_cena(c, p)
            m = _api.open_model(p)  # a DLL abre e a caixa gravada é a da fórmula face-me
            m.close()
            gravada = caixa_da_raiz(p)
            lo, hi = caixa_instancia(list(c.defs[c.instancias[comp].definicao].verts.values()), c.instancias[comp].transformacao, True)
            for got, want in zip(gravada, lo + hi):
                self.assertAlmostEqual(got, want, places=6)


if __name__ == "__main__":
    unittest.main()
