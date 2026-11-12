"""Ids de guias e planos de seção seguem a ordem de inclusão da SDK, misturando os tipos (FORMATO-SKP 7l)."""
import os
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.skp_topology_writer import gravar_topologia  # noqa: E402
from core.topology import Topology, guias  # noqa: E402
from core.topology.draw import desenhar  # noqa: E402

try:
    from tools.gerar_ordem_guias_api import ORDENS, gerar
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False


def trechos(caminho):
    """Registros 0x1391 (linhas), 0x1392 (pontos), 0x1393 (seções) e os três últimos ids da tabela 0x138e do modelo
    (a SDK intercala vértices e arestas nos ids da geometria; o gravador numera vértices, arestas e faces em blocos, o que
    não muda o primeiro id livre)."""
    with zipfile.ZipFile(caminho) as z:
        dat = z.read("model.dat")
    out = []
    for tag in (0x1391, 0x1392, 0x1393, 0x138E):
        i = dat.find(struct.pack("<H", tag))
        reg = dat[i:i + 6 + struct.unpack("<I", dat[i + 2:i + 6])[0]]
        out.append(reg[-3 * 2:] if tag == 0x138E else reg)  # cada id da tabela ocupa 2 bytes (tamanho + id)
    return out


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestOrdemDeIdsDeGuias(unittest.TestCase):
    def test_ids_iguais_aos_da_sdk_em_todas_as_ordens(self):
        with tempfile.TemporaryDirectory() as d:
            for ordem in ORDENS:
                with self.subTest(ordem):
                    t = Topology()
                    desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
                    for k in ordem:
                        if k == "p":
                            guias.guia_ponto(t, (10, 20, 30))
                        elif k == "l":
                            guias.guia_linha(t, (0, 0, 0), alvo=(50, 50, 0))
                        else:
                            guias.plano_secao(t, (0, 0, 1), (0, 0, 50))
                    meu = os.path.join(d, f"meu_{ordem}.skp")
                    gravar_topologia(t, meu)
                    self.assertEqual(trechos(meu), trechos(gerar(d, ordem)))


if __name__ == "__main__":
    unittest.main()
