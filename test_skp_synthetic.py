"""A7: gravador de .skp conferido SEM a SketchUpAPI (roda em qualquer Python e no CI).

Lê o arquivo gravado com o próprio TLV (core.skp_hidden_pruner._parse) e confere a estrutura documentada em
docs/FORMATO-SKP.md. O que só a DLL ou o SketchUp real confirmam fica em test_skp_topology_writer.py.
"""
import io
import os
import struct
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.skp_hidden_pruner import _parse, verificar_skp  # noqa: E402
from core.skp_topology_writer import MODELO_VAZIO, gravar_cena, gravar_topologia  # noqa: E402
from core.topology import Topology  # noqa: E402
from core.topology.cena import Cena  # noqa: E402
from core.topology.draw import desenhar  # noqa: E402
from core.topology.pushpull import empurrar  # noqa: E402


def dat_de(caminho):
    with open(caminho, "rb") as fh:
        b = fh.read()
    return zipfile.ZipFile(io.BytesIO(b[b.find(b"PK\x03\x04"):])).read("model.dat")


def achar(d, tag, ini=0, fim=None, acc=None):
    acc = [] if acc is None else acc
    for t, l, p in _parse(d, ini, len(d) if fim is None else fim):
        if t == tag:
            acc.append((t, l, p))
        elif l >= 6:
            try:
                achar(d, tag, p + 6, p + 6 + l, acc)
            except ValueError:
                pass
    return acc


def ids_de(d, regs):
    """Ids (0x05dc > 0x05de) dos registros, em qualquer profundidade."""
    out = []
    for _, l, p in regs:
        a = achar(d, 0x05DE, p + 6, p + 6 + l)
        out.append(int.from_bytes(d[a[0][2] + 6:a[0][2] + 6 + a[0][1]], "little"))
    return out


class TestGravadorSemDll(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def p(self, nome):
        return os.path.join(self.tmp.name, nome)

    def test_modelo_vazio_guardado_existe_e_e_valido(self):
        self.assertTrue(os.path.exists(MODELO_VAZIO))
        self.assertLess(os.path.getsize(MODELO_VAZIO), 20000)
        self.assertEqual(verificar_skp(MODELO_VAZIO)["refs_quebradas"], 0)

    def test_cubo_contagens_contador_e_tabela(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        empurrar(t, 1, -50)
        with open(MODELO_VAZIO, "rb") as fh:
            antes = fh.read()
        r = gravar_topologia(t, self.p("cubo.skp"))
        with open(MODELO_VAZIO, "rb") as fh:
            self.assertEqual(fh.read(), antes)  # a base nunca é alterada
        self.assertEqual((r["vertices"], r["arestas"], r["faces"]), (8, 12, 6))
        self.assertEqual(verificar_skp(self.p("cubo.skp"))["refs_quebradas"], 0)
        d = dat_de(self.p("cubo.skp"))
        self.assertEqual(len(achar(d, 0x09C4)), 8)
        self.assertEqual(len(achar(d, 0x0BB8)), 12)
        self.assertEqual(len(achar(d, 0x0DAC)), 6)
        todos = ids_de(d, achar(d, 0x09C4)) + ids_de(d, achar(d, 0x0BB8)) + ids_de(d, achar(d, 0x0DAC))
        self.assertEqual(len(set(todos)), 26)
        _, l, p = achar(d, 0x03E9)[0]
        self.assertEqual(int.from_bytes(d[p + 6:p + 6 + l], "little"), max(todos) + 1)  # contador = maior id + 1
        tabela = achar(d, 0x138E)[0]
        bruto = d[tabela[2] + 6:tabela[2] + 6 + tabela[1]]
        n_itens, i = 0, 0
        while i < len(bruto):
            i += 1 + bruto[i]
            n_itens += 1
        self.assertEqual(n_itens, 18)  # arestas + faces, sem vértices

    def test_curvas_arco_e_simples(self):
        t = Topology()
        desenhar(t, "arco", centro=(10, 20, 5), raio=30, ang_ini=0, ang_fim=90, lados=8)
        desenhar(t, "mao_livre", pontos=[(200, 0, 0), (300, 0, 0), (350, 80, 0)], fechar=False)
        gravar_topologia(t, self.p("c.skp"))
        d = dat_de(self.p("c.skp"))
        carga = achar(d, 0x4C2D)
        self.assertEqual(len(carga), 1)
        v = struct.unpack("<16d", d[carga[0][2] + 6:carga[0][2] + 6 + 128])
        self.assertEqual(v[0:3], (10.0, 20.0, 5.0))  # centro
        self.assertEqual(v[3:7], (0.0, 0.0, 1.0, -5.0))  # plano
        self.assertEqual(v[7:10], (30.0, 0.0, 0.0))  # X * raio
        self.assertEqual(v[13], 30.0)
        self.assertAlmostEqual(v[15], 1.5707963267948966)
        self.assertEqual(len(achar(d, 0x1397)), 1)
        self.assertEqual(len(achar(d, 0x1396)), 1)
        self.assertEqual(len(achar(d, 0x0BBB)), 8 + 2)  # cada aresta das duas curvas aponta para a sua

    def test_material_vira_xml_no_zip_e_ids_na_face(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(10, 10, 0))
        t.materiais = {"Azul": {"rgb": (0, 0, 255)}, "Vidro": {"rgb": (1, 2, 3), "alpha": 100}}
        f = next(iter(t.faces.values()))
        f.frente, f.verso = "Azul", "Vidro"
        gravar_topologia(t, self.p("m.skp"))
        with open(self.p("m.skp"), "rb") as fh:
            b = fh.read()
        z = zipfile.ZipFile(io.BytesIO(b[b.find(b"PK\x03\x04"):]))
        self.assertIn("materials/Azul/material.xml", z.namelist())
        xml = z.read("materials/Vidro/material.xml").decode()
        self.assertIn('colorRed="1" colorGreen="2" colorBlue="3"', xml)
        self.assertIn('useTrans="1"', xml)
        d = z.read("model.dat")
        self.assertEqual(len(achar(d, 0x32C8)), len(achar(dat_de(MODELO_VAZIO), 0x32C8)) + 2)
        self.assertEqual(len(achar(d, 0x07D1)), 1)  # frente
        self.assertEqual(len(achar(d, 0x0DAF)), 1)  # verso
        self.assertEqual(verificar_skp(self.p("m.skp"))["refs_quebradas"], 0)

    def test_hierarquia_definicoes_filhos_antes_dos_pais(self):
        c = Cena()
        desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        ext = c.criar_grupo(faces=list(c.topo.faces), nome="Externo")
        c.entrar(ext)
        desenhar(c.topo, "retangulo", p0=(200, 0, 0), p1=(300, 100, 0))
        c.criar_grupo(faces=[max(c.topo.faces)], nome="Interno")
        c.sair()
        r = gravar_cena(c, self.p("h.skp"))
        self.assertEqual((r["definicoes"], r["instancias"]), (2, 2))
        self.assertEqual(verificar_skp(self.p("h.skp"))["refs_quebradas"], 0)
        d = dat_de(self.p("h.skp"))
        defs = achar(d, 0x157C)
        self.assertEqual(len(defs), 2)
        # a primeira definição da lista é a que tem geometria (o filho); a segunda só instancia
        primeira, segunda = defs
        self.assertTrue(achar(d, 0x0DAC, primeira[2] + 6, primeira[2] + 6 + primeira[1]))
        self.assertTrue(achar(d, 0x138D, segunda[2] + 6, segunda[2] + 6 + segunda[1]))
        nomes = [bytes(d[a[2] + 6:a[2] + 6 + a[1]]) for a in achar(d, 0x1965)]
        self.assertEqual(sorted(nomes), [b"Externo", b"Interno"])

    def test_componente_matriz_por_linhas(self):
        c = Cena()
        desenhar(c.topo, "retangulo", p0=(0, 0, 0), p1=(100, 100, 0))
        k = c.criar_componente(faces=list(c.topo.faces), nome="Peca")
        c.instanciar(k, [0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1, 0, 7, 8, 9, 1])
        gravar_cena(c, self.p("k.skp"))
        d = dat_de(self.p("k.skp"))
        mats = sorted(struct.unpack("<13d", d[a[2] + 6:a[2] + 6 + 104]) for a in achar(d, 0x1966))
        self.assertEqual(mats[0], (0.0, -1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 7.0, 8.0, 9.0, 1.0))
        self.assertEqual(mats[1][9:12], (0.0, 0.0, 0.0))
        self.assertEqual(len(achar(d, 0x138C)), 1)

    def test_recusa_base_com_geometria_e_material_inexistente(self):
        t = Topology()
        desenhar(t, "retangulo", p0=(0, 0, 0), p1=(10, 10, 0))
        gravar_topologia(t, self.p("a.skp"))
        with self.assertRaises(ValueError):
            gravar_topologia(t, self.p("b.skp"), base=self.p("a.skp"))
        next(iter(t.faces.values())).frente = "Fantasma"
        with self.assertRaises(ValueError):
            gravar_topologia(t, self.p("c.skp"))


if __name__ == "__main__":
    unittest.main()
