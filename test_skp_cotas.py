"""Cotas lineares (FORMATO-SKP 7k): o gravador tem de reproduzir byte a byte o registro 0x1399 que a SketchUpAPI grava."""
import os
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.skp_topology_writer import gravar_topologia  # noqa: E402
from core.topology import Topology  # noqa: E402
from core.topology.cotas import apagar_cota, cota_linear  # noqa: E402

try:
    from tools.gerar_cotas_api import VARIACOES, gerar
    from core.su_api import SketchUpAPI
    _api = SketchUpAPI()
    _api.initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False


def registro_1399(caminho):
    """Bytes do registro 0x1399 (raiz do modelo) de um .skp."""
    with zipfile.ZipFile(caminho) as z:
        dat = z.read("model.dat")
    i = dat.find(struct.pack("<H", 0x1399))
    while i >= 0:
        n = struct.unpack("<I", dat[i + 2:i + 6])[0]
        if dat[i + 6:i + 8] == struct.pack("<H", 0x5BCC):  # 0x1399 > 0x5bcc
            return dat[i:i + 6 + n]
        i = dat.find(struct.pack("<H", 0x1399), i + 1)
    return None


# variação do oráculo -> argumentos de cota_linear que a reproduzem
CASOS = {
    "base": {},
    "pontos": dict(inicio=(10, 20, 30), fim=(110, 50, 30)),
    "posicao": dict(desloc=(50.0, 25.0)),
    "normal_y": dict(normal=(0, 1, 0)),
    "xaxis_y": dict(eixo_x=(0, 1, 0)),
    "seta1": dict(seta=1),
    "seta2": dict(seta=2),
    "valign1": dict(alinhamento_v=0),  # SetVerticalAlignment(1) grava 0; o padrão grava 1
    "texto": dict(texto="Meu texto"),
}


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestCotaContraASdk(unittest.TestCase):
    def test_registro_igual_ao_da_sdk(self):
        with tempfile.TemporaryDirectory() as d:
            for nome, args in CASOS.items():
                with self.subTest(nome):
                    ini, fim, _ = VARIACOES[nome]
                    t = Topology()
                    cota_linear(t, **{"inicio": ini, "fim": fim, **args})
                    meu = os.path.join(d, f"meu_{nome}.skp")
                    gravar_topologia(t, meu)
                    sdk = gerar(d, nome)
                    self.assertIsNotNone(registro_1399(sdk))
                    self.assertEqual(registro_1399(meu), registro_1399(sdk))

    def test_dll_abre_o_arquivo_gravado(self):
        t = Topology()
        cota_linear(t, (0, 0, 0), (100, 0, 0), texto="x")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.skp")
            gravar_topologia(t, p)
            m = _api.open_model(p)
            m.close()


class TestCotaNoNucleo(unittest.TestCase):
    def test_validacoes(self):
        t = Topology()
        with self.assertRaises(ValueError):
            cota_linear(t, (0, 0, 0), (0, 0, 0))
        with self.assertRaises(ValueError):
            cota_linear(t, (0, 0, 0), (1, 0, 0), normal=(0, 0, 0))
        with self.assertRaises(ValueError):
            cota_linear(t, (0, 0, 0), (1, 0, 0), seta=-1)

    def test_normaliza_e_apaga(self):
        t = Topology()
        cid = cota_linear(t, (0, 0, 0), (1, 0, 0), normal=(0, 0, 5))
        self.assertEqual(t.cotas[cid]["normal"], (0.0, 0.0, 1.0))
        apagar_cota(t, cid)
        self.assertEqual(t.cotas, {})
        with self.assertRaises(ValueError):
            apagar_cota(t, cid)


if __name__ == "__main__":
    unittest.main()
