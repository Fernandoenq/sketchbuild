"""F1: o núcleo de topologia contra os dados golden do SketchUp real (docs/f0)."""
import json
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402

GOLDEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "f0", "f0_resultados.json")
with open(GOLDEN, encoding="utf-8") as fh:
    RECEITAS = json.load(fh)["receitas"]


def etapa(receita, nome):
    return next(v for k, v in RECEITAS.items() if k.startswith(receita))["etapas"][nome]


def square(t, x0, y0, x1, y1, z=0):
    return t.add_face([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)])


class GoldenCase(unittest.TestCase):
    def confere(self, t, gold):
        self.assertEqual(
            (len(t.verts), len(t.edges), len(t.faces)),
            (gold["vertices"], gold["edges"], gold["faces"]),
        )
        areas = sorted(round(t.face_area(f), 4) for f in t.faces)
        for got, want in zip(areas, gold["face_areas_in2"]):
            self.assertAlmostEqual(got, want, places=3)
        self.assertEqual(sorted(len(f.loops()) for f in t.faces.values()), gold["face_loops"])
        got_ebf = {str(k): v for k, v in t.edges_by_face_count().items()}
        self.assertEqual(got_ebf, {k: v for k, v in gold["edges_by_face_count"].items()})


class TestTopologiaGolden(GoldenCase):
    def test_r01_linha_solta(self):
        t = Topology()
        t.add_edge((0, 0, 0), (100, 0, 0))
        self.confere(t, etapa("r01", "depois"))

    def test_r02_laco_de_linhas_e_find_faces(self):
        t = Topology()
        for a, b in [((0, 0, 0), (100, 0, 0)), ((100, 0, 0), (100, 100, 0)),
                     ((100, 100, 0), (0, 100, 0)), ((0, 100, 0), (0, 0, 0))]:
            t.add_edge(a, b)
        self.confere(t, etapa("r02", "apos_4_linhas"))
        t.find_faces(next(iter(t.edges)))
        self.confere(t, etapa("r02", "apos_find_faces"))
        self.assertEqual(next(iter(t.faces.values())).normal, (0.0, 0.0, -1.0))

    def test_r03_retangulo(self):
        t = Topology()
        square(t, 0, 0, 100, 100)
        self.confere(t, etapa("r03", "depois"))

    def test_r06_linha_divide_face(self):
        t = Topology()
        square(t, 0, 0, 100, 100)
        t.add_edge((50, 0, 0), (50, 100, 0))
        self.confere(t, etapa("r06", "depois"))

    def test_r07_linha_em_t(self):
        t = Topology()
        t.add_edge((0, 0, 0), (100, 0, 0))
        t.add_edge((50, 50, 0), (50, 0, 0))
        self.confere(t, etapa("r07", "depois"))

    def test_r08_linhas_em_x_nao_dividem(self):
        t = Topology()
        t.add_edge((0, 0, 0), (100, 100, 0))
        t.add_edge((0, 100, 0), (100, 0, 0))
        self.confere(t, etapa("r08", "depois"))

    def test_r09_circulo(self):
        t = Topology()
        pts = [(50 * math.cos(2 * math.pi * i / 24), 50 * math.sin(2 * math.pi * i / 24), 0) for i in range(24)]
        for i, p in enumerate(pts):
            t.add_edge(p, pts[(i + 1) % 24])
        self.confere(t, etapa("r09", "so_arestas"))
        t.find_faces(next(iter(t.edges)))
        self.confere(t, etapa("r09", "com_face"))

    def test_r10_face_dentro_de_face_vira_furo(self):
        t = Topology()
        square(t, 0, 0, 200, 200)
        square(t, 50, 50, 150, 150)
        self.confere(t, etapa("r10", "depois"))

    def test_r12_apagar_aresta_funde_faces(self):
        t = Topology()
        square(t, 0, 0, 100, 100)
        t.add_edge((50, 0, 0), (50, 100, 0))
        self.confere(t, etapa("r12", "dividido"))
        meio = next(e for e, (a, b) in t.edges.items()
                    if abs(t.verts[a][0] - 50) < 1e-6 and abs(t.verts[b][0] - 50) < 1e-6)
        t.erase_edge(meio)
        self.confere(t, etapa("r12", "apos_apagar_aresta"))

    def test_r13_arco_e_raios(self):
        t = Topology()
        arco = [(50 * math.cos(math.radians(7.5 * i)), 0, 50 * math.sin(math.radians(7.5 * i))) for i in range(13)]
        for a, b in zip(arco, arco[1:]):
            t.add_edge(a, b)
        t.add_edge((0, 0, 0), arco[0])
        t.add_edge((0, 0, 0), arco[-1])
        self.confere(t, etapa("r13", "arco_e_raios"))
        t.find_faces(next(iter(t.edges)))
        self.confere(t, etapa("r13", "apos_find_faces"))


if __name__ == "__main__":
    unittest.main()
