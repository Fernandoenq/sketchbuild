"""B2/B3: núcleo -> .skp -> SketchUpAPI.dll (oráculo). Pula se a DLL ou o Python 3.12 não estiverem disponíveis."""
import math
import os
import random
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.draw import desenhar  # noqa: E402
from core.topology.pushpull import empurrar  # noqa: E402

try:
    from core.su_api import SketchUpAPI
    from core.mesh_extractor import extract_scene
    from core.skp_topology_writer import gravar_topologia
    from core.skp_hidden_pruner import verificar_skp
    _api = SketchUpAPI()
    _api.initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:  # DLL ausente ou carga falhou
    DISPONIVEL = False


def area_da_malha(api, m) -> float:
    dto = extract_scene(api, m)
    total = 0.0
    for d in dto["definitions"]:
        v = np.asarray(d.get("vertices") if d.get("vertices") is not None else [], dtype=float).reshape(-1, 3)
        i = np.asarray(d.get("indices") if d.get("indices") is not None else [], dtype=int).reshape(-1, 3)
        if len(i):
            a, b, c = v[i[:, 0]], v[i[:, 1]], v[i[:, 2]]
            total += float(np.linalg.norm(np.cross(b - a, c - a), axis=1).sum() / 2)
    return total


@unittest.skipUnless(DISPONIVEL, "precisa da SketchUpAPI.dll em Python 3.12")
class TestGravadorDeTopologia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def conferir(self, t: Topology, nome: str):
        p = os.path.join(self.tmp.name, nome + ".skp")
        gravar_topologia(t, p)
        verificar_skp(p)  # ZIP, cabeçalho de integridade, tamanho do registro externo
        m = _api.open_model(p)
        try:
            r = m.count_summary()
            area = area_da_malha(_api, m)
        finally:
            m.close()
        c = t.counts()
        self.assertEqual((r["faces"], r["edges"]), (c["faces"], c["edges"]), nome)
        esperado = sum(t.face_area(f) for f in t.faces) if nome != "furo" else None
        return area, esperado

    def test_retangulo(self):
        t = Topology(); desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        area, esp = self.conferir(t, "r03")
        self.assertAlmostEqual(area, esp, places=3)

    def test_cubo(self):
        t = Topology(); desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0)); empurrar(t, 1, -50)
        area, esp = self.conferir(t, "r04")
        self.assertAlmostEqual(area, 40000.0, places=3)

    def test_face_com_furo_a_dll_enxerga_o_furo(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(200, 200, 0))
        desenhar(t, "retangulo", p0=(50, 50, 0), p1=(150, 150, 0))
        area, _ = self.conferir(t, "r10")
        self.assertAlmostEqual(area, 40000.0, places=3)  # 30000 (anel) + 10000 (face de dentro)

    def test_circulo(self):
        t = Topology(); desenhar(t, "circulo", centro=(0, 0, 0), raio=50)
        area, esp = self.conferir(t, "r09")
        self.assertAlmostEqual(area, 7764.571, places=2)

    def test_furo_vazado(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0)); empurrar(t, 1, -50)
        topo = next(i for i, f in t.faces.items() if f.normal[2] > 0.9)
        desenhar(t, "retangulo", p0=(30, 30, 50), p1=(70, 70, 50))
        interna = min(t.faces, key=lambda i: t.face_area(i))
        empurrar(t, interna, -50)
        self.assertEqual(t.counts(), {"vertices": 16, "edges": 24, "faces": 10})
        self.conferir(t, "r11")

    def test_aleatorios_batem_com_a_dll(self):
        rng = random.Random(7)
        for k in range(12):
            t = Topology()
            for _ in range(rng.randint(1, 3)):
                x, y = rng.randint(0, 5) * 300, rng.randint(0, 5) * 300
                if rng.random() < 0.5:
                    desenhar(t, "retangulo", p0=(x, y, 0), p1=(x + rng.randint(50, 200), y + rng.randint(50, 200), 0))
                else:
                    desenhar(t, "circulo", centro=(x, y, 0), raio=rng.randint(20, 100), lados=rng.choice([8, 12, 24]))
            if rng.random() < 0.6:
                empurrar(t, rng.choice(list(t.faces)), rng.choice([-30, -80, 40]))
            self.conferir(t, "aleatorio%d" % k)

    def test_nao_sobrescreve_a_base(self):
        t = Topology(); desenhar(t, "retangulo", p0=(0, 0, 0), p1=(10, 10, 0))
        p = os.path.join(self.tmp.name, "a.skp")
        gravar_topologia(t, p)
        with self.assertRaises(ValueError):
            gravar_topologia(t, p, base=p)
        with self.assertRaises(ValueError):  # a base já tem geometria
            gravar_topologia(t, os.path.join(self.tmp.name, "b.skp"), base=p)

    def test_arco_vira_curva_de_arco(self):
        """0x1397/0x4c2d decifrados: a DLL relê raio, centro, normal e ângulos do arco gravado."""
        from tools.su_curvas import curvas
        t = Topology()
        desenhar(t, "arco", centro=(10, 20, 5), raio=30, ang_ini=0, ang_fim=90, normal=(0, 0, 1), lados=8)
        p = os.path.join(self.tmp.name, "arco.skp")
        gravar_topologia(t, p)
        verificar_skp(p)
        c = curvas(p)
        self.assertEqual(len(c), 1)
        self.assertAlmostEqual(c[0]["raio"], 30.0, 4)
        self.assertAlmostEqual(c[0]["fim"], math.pi / 2, 4)
        self.assertEqual(c[0]["center"], (10.0, 20.0, 5.0))
        self.assertEqual(c[0]["normal"], (0.0, 0.0, 1.0))

    def test_arco_com_normal_inclinada_e_inicio_fora_do_x(self):
        from tools.su_curvas import curvas
        t = Topology()
        desenhar(t, "arco", centro=(1, 2, 3), raio=20, ang_ini=90, ang_fim=270, normal=(1, -1, 0), lados=12)
        p = os.path.join(self.tmp.name, "arco2.skp")
        gravar_topologia(t, p)
        c = curvas(p)
        self.assertEqual(len(c), 1)
        self.assertAlmostEqual(c[0]["fim"], math.pi, 4)
        self.assertAlmostEqual(c[0]["raio"], 20.0, 4)
        self.assertAlmostEqual(c[0]["normal"][0], math.sqrt(0.5), 4)

    def test_curva_com_aresta_apagada_nao_e_gravada(self):
        from tools.su_curvas import curvas
        t = Topology()
        desenhar(t, "arco", centro=(0, 0, 0), raio=30, ang_ini=0, ang_fim=90, normal=(0, 0, 1), lados=8)
        t.erase_edge(next(iter(t.edges)))
        p = os.path.join(self.tmp.name, "arco3.skp")
        gravar_topologia(t, p)
        self.assertEqual(curvas(p), [])

    def test_material_frente_e_verso_com_alpha(self):
        """Seção 7c do FORMATO-SKP.md: 0x07d1 (frente), 0x0daf (verso), 0x32c8 e material.xml no ZIP."""
        import ctypes
        from core.su_types import SUMaterialRef, SUColor
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        t.materiais = {"Vermelho": {"rgb": (255, 0, 0)}, "Verde Folha": {"rgb": (1, 200, 3), "alpha": 100}}
        f = next(iter(t.faces.values()))
        f.frente, f.verso = "Vermelho", "Verde Folha"
        p = os.path.join(self.tmp.name, "mat.skp")
        gravar_topologia(t, p)
        verificar_skp(p)
        m = _api.open_model(p)
        try:
            face = _api.get_faces(m.get_entities())[0]
            self.assertEqual(_api.get_face_color(face), [255, 0, 0])
            mt = SUMaterialRef()
            self.assertEqual(_api._dll.SUFaceGetBackMaterial(face, ctypes.byref(mt)), 0)
            self.assertEqual(_api._material_rgb(mt), [1, 200, 3])
            c = SUColor()
            _api._dll.SUMaterialGetColor(mt, ctypes.byref(c))
            self.assertEqual(c.alpha, 100)
        finally:
            m.close()

    def test_material_com_textura_e_lido_pela_dll_como_texturizado(self):
        """Seção 7e do FORMATO-SKP.md: imagem no ZIP + type=1 + 0x32cd; a DLL enxerga textura no material."""
        import ctypes
        from core.su_types import SUMaterialRef
        from core.topology.material import definir_material
        from tools.gerar_textura_api import png_xadrez
        png = os.path.join(self.tmp.name, "xadrez.png")
        png_xadrez(png)
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        with open(png, "rb") as fh:
            definir_material(t, "Xadrez", (127, 0, 127), textura={"nome": "xadrez.png", "bytes": fh.read()})
        next(iter(t.faces.values())).frente = "Xadrez"
        p = os.path.join(self.tmp.name, "tex.skp")
        gravar_topologia(t, p)
        verificar_skp(p)
        m = _api.open_model(p)
        try:
            face = _api.get_faces(m.get_entities())[0]
            mt = SUMaterialRef()
            self.assertEqual(_api._dll.SUFaceGetFrontMaterial(face, ctypes.byref(mt)), 0)
            tipo = ctypes.c_int(-1)
            self.assertEqual(_api._dll.SUMaterialGetType(mt, ctypes.byref(tipo)), 0)
            self.assertEqual(tipo.value, 1)  # SUMaterialType_Textured
        finally:
            m.close()

    def test_tags_lidas_pela_dll(self):
        """Seção 7f do FORMATO-SKP.md: tag nova na lista 0x3c8c e 0x07d2 na face; a DLL vê a camada e a visibilidade."""
        import ctypes
        from core.su_types import SUStringRef
        from core.topology.tag import atribuir, definir_tag
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        definir_tag(t, "Parede")
        definir_tag(t, "Oculta", visivel=False)
        atribuir(t, [next(iter(t.faces))], "Oculta")
        p = os.path.join(self.tmp.name, "tg.skp")
        gravar_topologia(t, p)
        verificar_skp(p)
        d = _api._dll
        m = _api.open_model(p)
        try:
            n = ctypes.c_size_t()
            d.SUModelGetNumLayers.argtypes = [type(m._model), ctypes.POINTER(ctypes.c_size_t)]
            self.assertEqual(d.SUModelGetNumLayers(m._model, ctypes.byref(n)), 0)
            self.assertEqual(n.value, 2)  # Layer0 + Oculta (Parede não foi usada, então não é gravada)
        finally:
            m.close()

    def _tag_de(self, de) -> str:
        """Nome da tag de um SUDrawingElementRef pela DLL ("" se não tem)."""
        import ctypes
        from core.su_types import SUStringRef
        d = _api._dll

        class _R(ctypes.Structure):
            _fields_ = [("ptr", ctypes.c_void_p)]
        lay = _R()
        d.SUDrawingElementGetLayer.argtypes = [type(de), ctypes.POINTER(_R)]
        if d.SUDrawingElementGetLayer(de, ctypes.byref(lay)) != 0:
            return ""
        d.SULayerGetName.argtypes = [_R, ctypes.POINTER(SUStringRef)]
        s = SUStringRef()
        d.SUStringCreate(ctypes.byref(s))
        d.SULayerGetName(lay, ctypes.byref(s))
        n = ctypes.c_size_t()
        d.SUStringGetUTF8Length(s, ctypes.byref(n))
        buf = ctypes.create_string_buffer(n.value + 1)
        d.SUStringGetUTF8(s, n.value + 1, buf, ctypes.byref(ctypes.c_size_t()))
        return buf.value.decode("utf-8")

    def test_tag_em_face_aresta_solta_e_grupo_lida_pela_dll(self):
        """Face, aresta solta e grupo em tags diferentes: a DLL devolve o nome de cada uma."""
        import ctypes
        from core.skp_topology_writer import gravar_cena
        from core.topology.cena import Cena
        from core.topology.tag import atribuir, atribuir_arestas, atribuir_instancia, definir_tag
        c = Cena()
        t = c.topo
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        desenhar(t, "linha", pontos=[(500, 0, 0), (600, 0, 0)])
        desenhar(t, "retangulo", p0=(0, 300, 0), p1=(50, 350, 0))
        for n in ("Piso", "Linha", "Peca"):
            definir_tag(t, n)
        f1 = sorted(t.faces)[0]
        solta = next(e for e, (a, b) in t.edges.items() if t.verts[a][0] >= 500)
        atribuir(t, [f1], "Piso")
        atribuir_arestas(t, [solta], "Linha")
        g = c.criar_grupo(faces=[max(t.faces)], nome="G")
        atribuir_instancia(c, g, "Peca")
        p = os.path.join(self.tmp.name, "tags3.skp")
        gravar_cena(c, p)
        verificar_skp(p)
        d = _api._dll

        class _R(ctypes.Structure):
            _fields_ = [("ptr", ctypes.c_void_p)]
        m = _api.open_model(p)
        try:
            e = m.get_entities()
            face = _api.get_faces(e)[0]
            d.SUFaceToDrawingElement.restype = _R
            d.SUFaceToDrawingElement.argtypes = [type(face)]
            self.assertEqual(self._tag_de(d.SUFaceToDrawingElement(face)), "Piso")
            grupo = _api.get_groups(e)[0]
            d.SUGroupToDrawingElement.restype = _R
            d.SUGroupToDrawingElement.argtypes = [type(grupo)]
            self.assertEqual(self._tag_de(d.SUGroupToDrawingElement(grupo)), "Peca")
            from core.su_types import SUEntitiesRef
            n = ctypes.c_size_t()
            d.SUEntitiesGetNumEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.POINTER(ctypes.c_size_t)]
            d.SUEntitiesGetNumEdges(e, False, ctypes.byref(n))
            arr = (_R * n.value)()
            d.SUEntitiesGetEdges.argtypes = [SUEntitiesRef, ctypes.c_bool, ctypes.c_size_t, ctypes.POINTER(_R), ctypes.POINTER(ctypes.c_size_t)]
            d.SUEntitiesGetEdges(e, False, n.value, arr, ctypes.byref(ctypes.c_size_t()))
            d.SUEdgeToDrawingElement.restype = _R
            d.SUEdgeToDrawingElement.argtypes = [_R]
            nomes = sorted(self._tag_de(d.SUEdgeToDrawingElement(x)) for x in arr)
            self.assertIn("Linha", nomes)
        finally:
            m.close()

    def test_cenas_com_e_sem_camera_lidas_pela_dll(self):
        """Seção 7f: 0x7148 por cena; com câmera leva 0x714a (0x34bc). A DLL devolve nome, descrição e olho/alvo."""
        import ctypes
        from core.skp_topology_writer import gravar_cena
        from core.su_types import SUPoint3D
        from core.topology.cena import Cena
        c = Cena()
        desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        c.adicionar_cena("Vista geral", "tudo", animar=True)
        c.adicionar_cena("Frente", camera={"olho": (300, -400, 200), "alvo": (50, 50, 0), "cima": (0, 0, 1)}, animar=False)
        p = os.path.join(self.tmp.name, "cenas.skp")
        gravar_cena(c, p)
        verificar_skp(p)
        d = _api._dll

        class _R(ctypes.Structure):
            _fields_ = [("ptr", ctypes.c_void_p)]
        m = _api.open_model(p)
        try:
            n = ctypes.c_size_t()
            d.SUModelGetNumScenes.argtypes = [type(m._model), ctypes.POINTER(ctypes.c_size_t)]
            self.assertEqual(d.SUModelGetNumScenes(m._model, ctypes.byref(n)), 0)
            self.assertEqual(n.value, 2)
            arr = (_R * 2)()
            d.SUModelGetScenes.argtypes = [type(m._model), ctypes.c_size_t, ctypes.POINTER(_R), ctypes.POINTER(ctypes.c_size_t)]
            self.assertEqual(d.SUModelGetScenes(m._model, 2, arr, ctypes.byref(ctypes.c_size_t())), 0)
            from core.su_types import SUStringRef

            def texto(fn, obj):
                s_ = SUStringRef()
                d.SUStringCreate(ctypes.byref(s_))
                fn.argtypes = [_R, ctypes.POINTER(SUStringRef)]
                fn(obj, ctypes.byref(s_))
                k = ctypes.c_size_t()
                d.SUStringGetUTF8Length(s_, ctypes.byref(k))
                buf = ctypes.create_string_buffer(k.value + 1)
                d.SUStringGetUTF8(s_, k.value + 1, buf, ctypes.byref(ctypes.c_size_t()))
                return buf.value.decode("utf-8")
            self.assertEqual([texto(d.SUSceneGetName, x) for x in arr], ["Vista geral", "Frente"])
            self.assertEqual(texto(d.SUSceneGetDescription, arr[0]), "tudo")
            anim = ctypes.c_bool()
            d.SUSceneGetIncludeInAnimation.argtypes = [_R, ctypes.POINTER(ctypes.c_bool)]
            d.SUSceneGetIncludeInAnimation(arr[1], ctypes.byref(anim))
            self.assertFalse(anim.value)
            cam = _R()
            d.SUSceneGetCamera.argtypes = [_R, ctypes.POINTER(_R)]
            self.assertEqual(d.SUSceneGetCamera(arr[1], ctypes.byref(cam)), 0)
            pos, alvo, cima = SUPoint3D(), SUPoint3D(), SUPoint3D()
            original = d.SUCameraGetOrientation.argtypes  # a DLL é compartilhada: devolve o argtypes que o extrator usa
            d.SUCameraGetOrientation.argtypes = [_R, ctypes.POINTER(SUPoint3D), ctypes.POINTER(SUPoint3D), ctypes.POINTER(SUPoint3D)]
            try:
                self.assertEqual(d.SUCameraGetOrientation(cam, ctypes.byref(pos), ctypes.byref(alvo), ctypes.byref(cima)), 0)
            finally:
                d.SUCameraGetOrientation.argtypes = original
            self.assertEqual((pos.x, pos.y, pos.z), (300.0, -400.0, 200.0))
            self.assertEqual((alvo.x, alvo.y, alvo.z), (50.0, 50.0, 0.0))
        finally:
            m.close()

    def test_material_nao_definido_e_recusado(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(10, 10, 0))
        next(iter(t.faces.values())).frente = "Fantasma"
        with self.assertRaises(ValueError):
            gravar_topologia(t, os.path.join(self.tmp.name, "x.skp"))

    def _nome_grupo(self, g):
        import ctypes
        from core.su_types import SUStringRef
        d = _api._dll
        s = SUStringRef()
        d.SUStringCreate(ctypes.byref(s))
        d.SUGroupGetName.argtypes = [type(g), ctypes.POINTER(SUStringRef)]
        d.SUGroupGetName(g, ctypes.byref(s))
        n = ctypes.c_size_t()
        d.SUStringGetUTF8Length(s, ctypes.byref(n))
        buf = ctypes.create_string_buffer(n.value + 1)
        d.SUStringGetUTF8(s, n.value + 1, buf, ctypes.byref(ctypes.c_size_t()))
        return buf.value.decode("utf-8")

    def test_grupo_e_componente_com_transformacao(self):
        """Seção 7d do FORMATO-SKP.md: definições 0x157c, instâncias 0x138c/0x138d, transformação de 13 doubles."""
        from core.topology.cena import Cena
        from core.skp_topology_writer import gravar_cena
        c = Cena()
        desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        desenhar(c.topo, "retangulo", p0=(500, 0, 0), p1=(600, 100, 0))
        desenhar(c.topo, "retangulo", p0=(900, 0, 0), p1=(950, 50, 0))
        f = sorted(c.topo.faces)
        c.criar_grupo(faces=[f[0]], nome="G1")
        k = c.criar_componente(faces=[f[1]], nome="Peca")
        rot = [0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1, 0, 7, 8, 9, 1]
        esc = [2, 0, 0, 0, 0, 3, 0, 0, 0, 0, 4, 0, 0, 0, 0, 1]
        c.instanciar(k, rot)
        c.instanciar(k, esc)
        p = os.path.join(self.tmp.name, "cena.skp")
        r = gravar_cena(c, p)
        self.assertEqual((r["definicoes"], r["instancias"]), (2, 4))
        info = verificar_skp(p)
        self.assertEqual(info["refs_quebradas"], 0)
        m = _api.open_model(p)
        try:
            e = m.get_entities()
            self.assertEqual(m.count_summary()["faces"], 1)  # a terceira ficou solta na raiz
            grupos = _api.get_groups(e)
            self.assertEqual([self._nome_grupo(g) for g in grupos], ["G1"])
            self.assertEqual(_api.count_faces(_api.get_group_entities(grupos[0])), 1)
            inst = _api.get_instances(e)
            self.assertEqual(len(inst), 3)
            mats = sorted(tuple(round(x, 6) for x in _api.get_instance_transform(i)) for i in inst)
            esperado = sorted(tuple(float(x) for x in t) for t in (c.instancias[i].transformacao for i in c.instancias if c.instancias[i].tipo == "componente"))
            self.assertEqual([tuple(abs(x) if x == 0 else x for x in mt) for mt in mats],
                             [tuple(abs(x) if x == 0 else x for x in mt) for mt in esperado])
            for i in inst:
                d = _api.get_instance_definition(i)
                self.assertEqual(_api.get_definition_name(d), "Peca")
                self.assertEqual(_api.count_faces(_api.get_definition_entities(d)), 1)
        finally:
            m.close()

    def test_grupo_aninhado_e_material_na_definicao(self):
        import ctypes
        from core.su_types import SUMaterialRef
        from core.topology.cena import Cena
        from core.skp_topology_writer import gravar_cena
        c = Cena()
        desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        c.topo.materiais = {"Vermelho": {"rgb": (255, 0, 0)}}
        next(iter(c.topo.faces.values())).frente = "Vermelho"
        externo = c.criar_grupo(faces=list(c.topo.faces), nome="Externo")
        c.entrar(externo)
        desenhar(c.topo, "retangulo", p0=(200, 0, 0), p1=(300, 100, 0))
        interno = c.criar_grupo(faces=[max(c.topo.faces)], nome="Interno")
        c.sair()
        p = os.path.join(self.tmp.name, "aninhado.skp")
        gravar_cena(c, p)
        self.assertEqual(verificar_skp(p)["refs_quebradas"], 0)
        m = _api.open_model(p)
        try:
            raiz = _api.get_groups(m.get_entities())
            self.assertEqual([self._nome_grupo(g) for g in raiz], ["Externo"])
            ent = _api.get_group_entities(raiz[0])
            dentro = _api.get_groups(ent)
            self.assertEqual([self._nome_grupo(g) for g in dentro], ["Interno"])
            self.assertEqual(_api.count_faces(ent), 1)
            face = _api.get_faces(ent)[0]
            self.assertEqual(_api.get_face_color(face), [255, 0, 0])
        finally:
            m.close()

    def _num_curvas(self, m):
        import ctypes
        from core.su_types import SUEntitiesRef
        d = _api._dll
        d.SUEntitiesGetNumCurves.argtypes = [SUEntitiesRef, ctypes.POINTER(ctypes.c_size_t)]
        n = ctypes.c_size_t()
        d.SUEntitiesGetNumCurves(m.get_entities(), ctypes.byref(n))
        return n.value

    def test_curva_simples_mao_livre_e_arco_dividido(self):
        """0x1396 (curva simples) e arco cuja aresta foi dividida em T continua curva."""
        from tools.su_curvas import curvas
        t = Topology()
        desenhar(t, "mao_livre", pontos=[(0, 0, 0), (100, 0, 0), (150, 80, 0), (100, 160, 30)], fechar=False)
        self.assertEqual(t.curvas[1]["tipo"], "simples")
        p = os.path.join(self.tmp.name, "simples.skp")
        gravar_topologia(t, p)
        verificar_skp(p)
        m = _api.open_model(p)
        try:
            self.assertEqual(self._num_curvas(m), 1)
        finally:
            m.close()
        t2 = Topology()
        desenhar(t2, "arco", centro=(0, 0, 0), raio=30, ang_ini=0, ang_fim=90, normal=(0, 0, 1), lados=8)
        antes = len(t2.curvas[1]["arestas"])
        e0 = t2.curvas[1]["arestas"][2]
        a, b = t2.edges[e0]
        meio = tuple((x + y) / 2 for x, y in zip(t2.verts[a], t2.verts[b]))
        t2.add_edge(meio, (meio[0] + 10, meio[1] + 10, 0))  # T no meio da aresta do arco
        self.assertEqual(len(t2.curvas[1]["arestas"]), antes + 1)
        p2 = os.path.join(self.tmp.name, "arco_t.skp")
        gravar_topologia(t2, p2)
        c = curvas(p2)
        self.assertEqual(len(c), 1)
        self.assertAlmostEqual(c[0]["raio"], 30.0, 4)

    def test_modelo_vazio(self):
        p = os.path.join(self.tmp.name, "vazio.skp")
        gravar_topologia(Topology(), p)
        m = _api.open_model(p)
        try:
            self.assertEqual(m.count_summary()["faces"], 0)
        finally:
            m.close()


if __name__ == "__main__":
    unittest.main()
