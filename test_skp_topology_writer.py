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
