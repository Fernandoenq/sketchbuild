"""Apagar: o núcleo (`edit.apagar`) tem de deixar o mesmo que `SUEntitiesErase` da SketchUpAPI (faces e arestas, por posição)."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology import Topology  # noqa: E402
from core.topology.edit import apagar  # noqa: E402

try:
    import tools.conferir_apagar_sdk as oraculo
    from core.su_api import SketchUpAPI
    SketchUpAPI().initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False

_Q = [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)]
_CUBO_V = [(x, y, z) for z in (0, 10) for (x, y) in ((0, 0), (10, 0), (10, 10), (0, 10))]
_CUBO_F = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
_L = [(0, 0, 0), (20, 0, 0), (20, 10, 0), (10, 10, 0), (10, 20, 0), (0, 20, 0), (0, 10, 0)]
_FAIXAS = [(0, 0, 0), (30, 0, 0), (30, 10, 0), (0, 10, 0), (10, 0, 0), (10, 10, 0), (20, 0, 0), (20, 10, 0)]
_HOLE = [(0, 0, 0), (100, 0, 0), (100, 100, 0), (0, 100, 0), (20, 20, 0), (40, 20, 0), (40, 40, 0), (20, 40, 0)]

# nome: (vértices, faces, arestas soltas, alvos)
CASOS = {
    "quadrado_aresta": (_Q, [[0, 1, 2, 3]], [], [("aresta", _Q[0], _Q[1])]),
    "quadrado_face": (_Q, [[0, 1, 2, 3]], [], [("face", _Q)]),
    "cubo_aresta": (_CUBO_V, _CUBO_F, [], [("aresta", _CUBO_V[0], _CUBO_V[1])]),
    "cubo_face": (_CUBO_V, _CUBO_F, [], [("face", _CUBO_V[4:8])]),
    "dois_quadrados_aresta_comum": ([(0, 0, 0), (10, 0, 0), (20, 0, 0), (20, 10, 0), (10, 10, 0), (0, 10, 0)],
                                    [[0, 1, 4, 5], [1, 2, 3, 4]], [], [("aresta", (10, 0, 0), (10, 10, 0))]),
    "dois_quadrados_aresta_de_fora": ([(0, 0, 0), (10, 0, 0), (20, 0, 0), (20, 10, 0), (10, 10, 0), (0, 10, 0)],
                                      [[0, 1, 4, 5], [1, 2, 3, 4]], [], [("aresta", (0, 0, 0), (10, 0, 0))]),
    "L_aresta_comum": (_L, [[0, 1, 2, 3, 6], [6, 3, 4, 5]], [], [("aresta", _L[6], _L[3])]),
    "tres_faixas_divisoria": (_FAIXAS, [[0, 4, 5, 3], [4, 6, 7, 5], [6, 1, 2, 7]], [], [("aresta", _FAIXAS[4], _FAIXAS[5])]),
    "furo_aresta_do_furo": (_HOLE, [{"outer": [0, 1, 2, 3], "holes": [[4, 7, 6, 5]]}, [4, 5, 6, 7]], [],
                            [("aresta", _HOLE[4], _HOLE[5])]),
    "furo_apaga_a_face_interna": (_HOLE, [{"outer": [0, 1, 2, 3], "holes": [[4, 7, 6, 5]]}, [4, 5, 6, 7]], [], [("face", _HOLE[4:8])]),
    "aresta_solta": ([(0, 0, 0), (5, 0, 0)], [], [(0, 1)], [("aresta", (0, 0, 0), (5, 0, 0))]),
    "galho_de_T": ([(0, 0, 0), (10, 0, 0), (20, 0, 0), (10, 10, 0)], [], [(0, 1), (1, 2), (1, 3)], [("aresta", (10, 0, 0), (10, 10, 0))]),
    "aresta_pendurada_na_face": (_Q + [(5, 5, 0)], [[0, 1, 2, 3]], [(0, 4)], [("aresta", (0, 0, 0), (5, 5, 0))]),
}


def _pos(t, v):
    return tuple(round(c, 6) + 0.0 for c in t.verts[v])


def _foto(t):
    faces = {frozenset(_pos(t, v) for lp in f.loops() for v in lp) for f in t.faces.values()}  # a SDK lista os vértices de todos os laços
    arestas = {frozenset((_pos(t, a), _pos(t, b))) for a, b in t.edges.values()}
    return faces, arestas


def _aresta_do_nucleo(t, a, b):
    for e, (u, v) in t.edges.items():
        if {_pos(t, u), _pos(t, v)} == {tuple(map(float, a)), tuple(map(float, b))}:
            return e
    raise AssertionError(f"aresta {a}-{b} não existe no núcleo")


def _face_do_nucleo(t, vertices):
    alvo = {tuple(map(float, v)) for v in vertices}
    for fid, f in t.faces.items():
        if {_pos(t, v) for lp in f.loops() for v in lp} == alvo:
            return fid
    raise AssertionError("face não existe no núcleo")


# apagar face leva as arestas SUAVES que ficam sem face (REA FUN_18045dad0 + FUN_1801909a0; medido na SDK)
CASOS_SUAVES = {
    "quadrado_face_suave": (_Q, [[0, 1, 2, 3]], [], [("face", _Q)]),
    "dois_quadrados_face_suave": ([(0, 0, 0), (10, 0, 0), (20, 0, 0), (20, 10, 0), (10, 10, 0), (0, 10, 0)],
                                  [[0, 1, 4, 5], [1, 2, 3, 4]], [], [("face", [(0, 0, 0), (10, 0, 0), (10, 10, 0), (0, 10, 0)])]),
    "cubo_face_suave": (_CUBO_V, _CUBO_F, [], [("face", _CUBO_V[4:8])]),
}


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestApagarContraASdk(unittest.TestCase):
    def test_bate_com_a_sdk(self):
        for nome, (verts, faces, soltas, alvos) in CASOS.items():
            with self.subTest(nome):
                sdk = oraculo.apagar(verts, faces, soltas, alvos)
                t = Topology()
                for f in faces:
                    spec = f if isinstance(f, dict) else {"outer": f, "holes": []}
                    t.add_face([verts[i] for i in spec["outer"]])
                from core.topology.draw import desenhar
                for a, b in soltas:
                    desenhar(t, "linha", pontos=[verts[a], verts[b]])
                arestas = [_aresta_do_nucleo(t, a[1], a[2]) for a in alvos if a[0] == "aresta"]
                faces_alvo = [_face_do_nucleo(t, a[1]) for a in alvos if a[0] == "face"]
                apagar(t, arestas=arestas, faces=faces_alvo)
                faces_n, arestas_n = _foto(t)
                self.assertEqual(arestas_n, sdk["arestas"], "arestas")
                self.assertEqual(faces_n, sdk["faces"], "faces")

    def test_face_leva_arestas_suaves_sem_face(self):
        from core.topology.soften import definir
        for nome, (verts, faces, soltas, alvos) in CASOS_SUAVES.items():
            with self.subTest(nome):
                sdk = oraculo.apagar(verts, faces, soltas, alvos, suaves=True)
                t = Topology()
                for f in faces:
                    t.add_face([verts[i] for i in f])
                definir(t, list(t.edges), suave=True, lisa=False)
                apagar(t, faces=[_face_do_nucleo(t, a[1]) for a in alvos])
                faces_n, arestas_n = _foto(t)
                self.assertEqual(arestas_n, sdk["arestas"], "arestas")
                self.assertEqual(faces_n, sdk["faces"], "faces")


if __name__ == "__main__":
    unittest.main()
