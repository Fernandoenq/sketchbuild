"""M13: seleção no núcleo (tudo, inverter, conectados, tag, material, janela e cruzamento)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.selecao import (arestas_das_faces, conectados, faces_das_arestas, inverter,  # noqa: E402
                                   por_material, por_retangulo, por_tag, tudo)

# projeção ortográfica olhando de cima: tela = (x, y)
TOPO = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]


def dois_quadrados():
    t = Topology()
    a = t.add_face([(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)])
    b = t.add_face([(100, 0, 0), (110, 0, 0), (110, 10, 0), (100, 10, 0)])
    return t, a, b


class TestSelecao(unittest.TestCase):
    def test_tudo_e_inverter(self):
        t, a, b = dois_quadrados()
        self.assertEqual(len(tudo(t)["edges"]), 8)
        r = inverter(t, faces=[a], edges=[1, 2])
        self.assertEqual(r["faces"], [b])
        self.assertEqual(r["edges"], [3, 4, 5, 6, 7, 8])
        self.assertEqual(inverter(t)["faces"], sorted([a, b]))

    def test_faces_e_arestas(self):
        t, a, b = dois_quadrados()
        r = arestas_das_faces(t, [a])
        self.assertEqual((r["faces"], len(r["edges"])), ([a], 4))
        self.assertEqual(faces_das_arestas(t, r["edges"])["faces"], [a])
        self.assertEqual(faces_das_arestas(t, r["edges"][:3])["faces"], [])

    def test_conectados(self):
        t, a, b = dois_quadrados()
        t.add_edge((10, 10, 0), (20, 20, 0))  # liga ao primeiro quadrado, não ao segundo
        r = conectados(t, faces=[a])
        self.assertEqual(r["faces"], [a])
        self.assertEqual(len(r["edges"]), 5)
        with self.assertRaises(ValueError):
            conectados(t, faces=[999])

    def test_tag_e_material(self):
        t, a, b = dois_quadrados()
        t.tags["Parede"] = {"visivel": True}
        t.faces[a].tag = "Parede"
        t.materiais["Tinta"] = {"rgb": (1, 2, 3), "alpha": 255}
        t.faces[b].verso = "Tinta"
        self.assertEqual(por_tag(t, "Parede")["faces"], [a])
        self.assertEqual(por_material(t, "Tinta")["faces"], [b])
        for f in (por_tag, por_material):
            with self.assertRaises(ValueError):
                f(t, "nada")

    def test_janela_so_o_que_cabe_inteiro(self):
        t, a, b = dois_quadrados()
        self.assertEqual(por_retangulo(t, TOPO, (-1, -1, 11, 11))["faces"], [a])
        self.assertEqual(len(por_retangulo(t, TOPO, (-1, -1, 11, 11))["edges"]), 4)
        self.assertEqual(por_retangulo(t, TOPO, (-1, -1, 5, 5))["faces"], [])  # corta o quadrado
        self.assertEqual(sorted(por_retangulo(t, TOPO, (-1, -1, 120, 11))["faces"]), sorted([a, b]))

    def test_cruzamento_toca_ou_esta_dentro_da_face(self):
        t, a, b = dois_quadrados()
        r = por_retangulo(t, TOPO, (-1, -1, 5, 5), cruzamento=True)
        self.assertEqual(r["faces"], [a])
        self.assertEqual(len(r["edges"]), 2)
        dentro = por_retangulo(t, TOPO, (4, 4, 6, 6), cruzamento=True)  # retângulo no miolo da face
        self.assertEqual((dentro["faces"], dentro["edges"]), ([a], []))
        self.assertEqual(por_retangulo(t, TOPO, (30, 30, 40, 40), cruzamento=True)["faces"], [])

    def test_atras_da_camera_fica_de_fora(self):
        t, a, b = dois_quadrados()
        persp = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, -5]  # w = z - 5: z=0 fica atrás
        self.assertEqual(por_retangulo(t, persp, (-999, -999, 999, 999), cruzamento=True)["faces"], [])
        with self.assertRaises(ValueError):
            por_retangulo(t, [1, 0], (0, 0, 1, 1))


if __name__ == "__main__":
    unittest.main()
