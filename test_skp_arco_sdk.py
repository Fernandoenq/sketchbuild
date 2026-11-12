"""M10: os vértices dos arcos do núcleo têm de bater com os de `SUArcCurveCreate` da SketchUpAPI."""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.topology.draw import arco_por_3_pontos, arco_por_corda, pontos_arco  # noqa: E402

try:
    import tools.conferir_arco_sdk as oraculo
    from core.su_api import SketchUpAPI
    SketchUpAPI().initialize()
    DISPONIVEL = sys.version_info[:2] == (3, 12)
except Exception:
    DISPONIVEL = False


def _unit(v):
    n = math.sqrt(sum(c * c for c in v))
    return tuple(c / n for c in v)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _gira(p, c, eixo, graus):
    """Rotaciona p em torno de c pelo eixo unitário (Rodrigues), no sentido anti-horário visto da ponta do eixo."""
    a = math.radians(graus)
    v = tuple(p[i] - c[i] for i in range(3))
    k = eixo
    kv = _cross(k, v)
    kd = sum(k[i] * v[i] for i in range(3))
    r = tuple(v[i] * math.cos(a) + kv[i] * math.sin(a) + k[i] * kd * (1 - math.cos(a)) for i in range(3))
    return tuple(c[i] + r[i] for i in range(3))


def _caso(centro, normal, ponto_inicial, varredura):
    n = _unit(normal)
    i = ponto_inicial
    return centro, n, i, _gira(i, centro, n, varredura / 2), _gira(i, centro, n, varredura)


CASOS = {
    "xy_90": _caso((0, 0, 0), (0, 0, 1), (10, 0, 0), 90),
    "xy_270": _caso((0, 0, 0), (0, 0, 1), (10, 0, 0), 270),
    "xy_deslocado": _caso((5, -3, 2), (0, 0, 1), (5, 7, 2), 120),
    "parede_normal_menos_y": _caso((0, 0, 0), (0, -1, 0), (10, 0, 0), 90),
    "plano_inclinado": _caso((1, 2, 3), (1, 1, 1), (1 + 7.0710678118654755, 2 - 7.0710678118654755, 3), 150),
    "plano_inclinado_270": _caso((0, 0, 0), (1, -2, 0.5), (_cross((1, -2, 0.5), (0, 0, 1))), 270),
}


def _perto(a, b, tol=1e-9):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def _contem(lista, p, tol=1e-9):
    return any(_perto(q, p, tol) for q in lista)


@unittest.skipUnless(DISPONIVEL, "SketchUpAPI.dll / Python 3.12 indisponível")
class TestArcoContraASdk(unittest.TestCase):
    def test_tres_pontos_gera_os_mesmos_vertices_que_a_sdk(self):
        for nome, (c, n, p0, p1, p2) in CASOS.items():
            for lados in (6, 12):
                with self.subTest(f"{nome}_{lados}"):
                    centro, raio, normal, a0, a1 = arco_por_3_pontos(p0, p1, p2)
                    self.assertTrue(_perto(centro, c, 1e-7), (centro, c))
                    self.assertAlmostEqual(raio, math.dist(p0, c), places=7)
                    # a normal do triângulo é a do arco (ou a oposta, se o sentido for horário visto de `n`)
                    meus = pontos_arco(centro, raio, a0, a1, normal, lados)
                    sdk = oraculo.arco(centro, p0, p2, normal, lados)
                    self.assertAlmostEqual(sdk["raio"], raio, places=7)
                    pontos_sdk = [par[0] for par in sdk["arestas"]] + [sdk["arestas"][-1][1]]
                    self.assertEqual(len(meus), len(pontos_sdk))
                    for p in meus:
                        self.assertTrue(_contem(pontos_sdk, p, 1e-7), f"{nome}: {p} não está no arco da SDK")

    def test_corda_e_flecha_gera_os_mesmos_vertices_que_a_sdk(self):
        for flecha in (2.5, -2.5, 8.0):
            with self.subTest(flecha=flecha):
                p0, p1 = (0, 0, 0), (10, 0, 0)
                centro, raio, normal, a0, a1 = arco_por_corda(p0, p1, flecha)
                meus = pontos_arco(centro, raio, a0, a1, normal, 12)
                sdk = oraculo.arco(centro, p0, p1, normal, 12)
                pontos_sdk = [par[0] for par in sdk["arestas"]] + [sdk["arestas"][-1][1]]
                for p in meus:
                    self.assertTrue(_contem(pontos_sdk, p, 1e-7))
                topo = max(abs(p[1]) for p in meus)  # distância máxima à corda (o eixo x)
                self.assertAlmostEqual(topo, abs(flecha), places=6)  # a flecha é a altura do arco


class TestArcoSemSdk(unittest.TestCase):
    def test_sentido_anti_horario_em_torno_da_normal(self):
        for nome, (c, n, p0, p1, p2) in CASOS.items():
            with self.subTest(nome):
                centro, raio, normal, a0, a1 = arco_por_3_pontos(p0, p1, p2)
                meio = pontos_arco(centro, raio, a0, a1, normal, 2)[1]
                self.assertTrue(_perto(meio, p1, 1e-7) or math.dist(meio, p1) < raio)  # o ponto do meio fica no mesmo lado


if __name__ == "__main__":
    unittest.main()
