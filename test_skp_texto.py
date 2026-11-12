"""Texto livre (FORMATO-SKP 7l): o gravador tem de reproduzir byte a byte o registro 0x1398 que a SketchUpAPI grava."""
import os
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.skp_topology_writer import gravar_topologia  # noqa: E402
from core.topology import Topology  # noqa: E402
from core.topology.cotas import cota_linear  # noqa: E402
from core.topology.texto import apagar_texto, texto_livre  # noqa: E402

try:
    from tools.gerar_texto_api import VARIACOES, gerar
    from core.su_api import SketchUpAPI
    _api = SketchUpAPI()
    _api.initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False


def registro_1398(caminho):
    """Bytes do registro 0x1398 (texto) da raiz de um .skp."""
    with zipfile.ZipFile(caminho) as z:
        dat = z.read("model.dat")
    marca = struct.pack("<H", 0x1398)
    i = dat.find(marca)
    while i >= 0:
        n = struct.unpack("<I", dat[i + 2:i + 6])[0]
        if dat[i + 6:i + 8] == struct.pack("<H", 0x55F0):
            return dat[i:i + 6 + n]
        i = dat.find(marca, i + 1)
    return None


CASOS = {
    "base": {},
    "ponto2": dict(ponto=(110, -20, 5)),
    "texto": dict(texto="Outro texto"),
    "tipo1": dict(tipo=1),
    "tipo2": dict(tipo=2),
    "vetor": dict(tipo=1, vetor=(0, 0, 40)),
    "seta1": dict(seta=1),
    "fonte1": dict(fonte=3),
}


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestTextoContraASdk(unittest.TestCase):
    def test_registro_igual_ao_da_sdk(self):
        with tempfile.TemporaryDirectory() as d:
            for nome, args in CASOS.items():
                with self.subTest(nome):
                    padrao = {"texto": "Nota", "ponto": (10, 20, 30)}
                    t = Topology()
                    texto_livre(t, **{**padrao, **args})
                    meu = os.path.join(d, f"meu_{nome}.skp")
                    gravar_topologia(t, meu)
                    sdk = gerar(d, nome)
                    self.assertIsNotNone(registro_1398(sdk))
                    self.assertEqual(registro_1398(meu), registro_1398(sdk))

    def test_dll_abre_o_arquivo_com_texto_e_cota(self):
        t = Topology()
        cota_linear(t, (0, 0, 0), (100, 0, 0))
        texto_livre(t, "Olá, mundo", (5, 5, 5))
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "tc.skp")
            gravar_topologia(t, p)
            _api.open_model(p).close()


class TestTextoNoNucleo(unittest.TestCase):
    def test_validacoes(self):
        t = Topology()
        for args in (dict(texto="  ", ponto=(0, 0, 0)), dict(texto="x", ponto=(0, 0, 0), tipo=3),
                     dict(texto="x", ponto=(0, 0, 0), seta=-1), dict(texto="x", ponto=(float("nan"), 0, 0))):
            with self.assertRaises(ValueError):
                texto_livre(t, **args)

    def test_apagar(self):
        t = Topology()
        tid = texto_livre(t, "x", (0, 0, 0))
        apagar_texto(t, tid)
        self.assertEqual(t.textos, {})
        with self.assertRaises(ValueError):
            apagar_texto(t, tid)


if __name__ == "__main__":
    unittest.main()
