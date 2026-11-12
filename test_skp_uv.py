"""Textura posicionada (FORMATO-SKP 7j): matriz UV -> plano conferida contra os números que a SketchUpAPI gravou."""
import math
import os
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.skp_topology_writer import _bloco_uv, gravar_topologia  # noqa: E402
from core.topology import Topology  # noqa: E402
from core.topology.draw import desenhar  # noqa: E402
from core.topology.material import definir_material, matriz_uv, pintar, posicionar_textura  # noqa: E402
from core.topology.pushpull import empurrar  # noqa: E402

# quatro casos gerados por tools/gerar_uv_api.py (quadrado de 100 pol em z=0) e lidos de 0x2715: (a, b, c, d, tx, ty)
ORACULO = {
    "escala2": (dict(tamanho=50), (50.0, 0.0, 0.0, 50.0, 0.0, 0.0)),
    "escala4": (dict(tamanho=25), (25.0, 0.0, 0.0, 25.0, 0.0, 0.0)),
    "deslocado": (dict(tamanho=50, u0=0.25, v0=0.5), (50.0, 0.0, 0.0, 50.0, -12.5, -25.0)),
    "rot90": (dict(tamanho=50, graus=90), (0.0, -50.0, 50.0, 0.0, 0.0, 0.0)),
}
PNG_1x1 = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000001e221bc330000000049454e44ae426082")


def _matrizes_2715(caminho):
    """Todas as matrizes 3x3 (tag 0x2715) do model.dat, na ordem do arquivo."""
    with zipfile.ZipFile(caminho) as z:
        dat = z.read("model.dat")
    marca = struct.pack("<HI", 0x2715, 72)
    saida, i = [], dat.find(marca)
    while i >= 0:
        saida.append(struct.unpack("<9d", dat[i + 6:i + 78]))
        i = dat.find(marca, i + 6)
    return saida


class TestMatrizUV(unittest.TestCase):
    def test_bate_com_os_quatro_casos_da_sdk(self):
        for nome, (args, esperado) in ORACULO.items():
            with self.subTest(nome):
                for got, want in zip(matriz_uv(**args), esperado):
                    self.assertAlmostEqual(got, want, places=9)

    def test_tamanho_invalido(self):
        with self.assertRaises(ValueError):
            matriz_uv(0)

    def test_bloco_gravado_tem_frente_e_verso(self):
        b = _bloco_uv(matriz_uv(50))
        self.assertEqual(struct.unpack("<9d", b[b.find(struct.pack("<HI", 0x2715, 72)) + 6:][:72]),
                         (50.0, 0.0, 0.0, 0.0, 50.0, 0.0, 0.0, 0.0, 1.0))
        self.assertEqual(b.count(struct.pack("<HI", 0x2715, 72)), 2)


class TestPosicionarNoNucleo(unittest.TestCase):
    def _face_texturizada(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        fid = next(iter(t.faces))
        definir_material(t, "Tex", (10, 20, 30), textura={"nome": "t.png", "bytes": PNG_1x1})
        pintar(t, [fid], frente="Tex")
        return t, fid

    def test_exige_textura_na_frente(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        fid = next(iter(t.faces))
        with self.assertRaises(ValueError):
            posicionar_textura(t, [fid], matriz_uv(50))
        definir_material(t, "Liso", (1, 2, 3))
        pintar(t, [fid], frente="Liso")
        with self.assertRaises(ValueError):
            posicionar_textura(t, [fid], matriz_uv(50))

    def test_matriz_com_tamanho_errado_e_face_inexistente(self):
        t, fid = self._face_texturizada()
        with self.assertRaises(ValueError):
            posicionar_textura(t, [fid], (1, 2, 3))
        with self.assertRaises(ValueError):
            posicionar_textura(t, [99], matriz_uv(50))

    def test_limpar_a_frente_tira_o_posicionamento(self):
        t, fid = self._face_texturizada()
        posicionar_textura(t, [fid], matriz_uv(50))
        self.assertIsNotNone(t.faces[fid].uv)
        pintar(t, [fid], limpar_frente=True)
        self.assertIsNone(t.faces[fid].uv)

    def test_pushpull_leva_o_posicionamento_para_a_tampa_e_a_base(self):
        t, fid = self._face_texturizada()
        m = matriz_uv(40, 0.1, 0.2)
        posicionar_textura(t, [fid], m)
        empurrar(t, fid, -50)
        com_uv = [f for f in t.faces.values() if f.uv]
        self.assertEqual(len(com_uv), 2)  # a tampa nova e a original, que vira a base; as 4 paredes ficam sem
        self.assertTrue(all(f.uv == tuple(m) for f in com_uv))

    def test_gravador_escreve_a_matriz_e_so_com_textura(self):
        t, fid = self._face_texturizada()
        posicionar_textura(t, [fid], matriz_uv(50, 0.25, 0.5))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "uv.skp")
            gravar_topologia(t, p)
            ms = _matrizes_2715(p)
            self.assertEqual(len(ms), 2)  # frente posicionada e verso identidade
            self.assertEqual(ms[0], (50.0, 0.0, 0.0, 0.0, 50.0, 0.0, -12.5, -25.0, 1.0))
            self.assertEqual(ms[1], (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
            t.faces[fid].frente = None  # sem material na frente o posicionamento não vai
            gravar_topologia(t, p)
            self.assertEqual(_matrizes_2715(p), [])


if __name__ == "__main__":
    unittest.main()
