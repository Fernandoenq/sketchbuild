"""Auditoria (A5), parte D: sol, tobogã espiral e cache de malhas, com conferência independente do código."""
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import cache_malhas  # noqa: E402
from core.assembly_sequencer import AssemblySequencer  # noqa: E402
from core.solar_calculator import SolarCalculator  # noqa: E402
from core.spiral_tube_generator import SpiralTubeGenerator  # noqa: E402


class TestSol(unittest.TestCase):
    def test_meio_dia_no_equador_no_equinocio_o_sol_esta_a_pino(self):
        r = SolarCalculator.calculate_sun_position(day_of_year=80, solar_hour=12.0, latitude_deg=0.0, longitude_deg=-45.0)
        self.assertGreater(r["altitude_deg"], 87.0)  # declinação ~ -0,4 e equação do tempo ~ -7 min (ângulo horário ~ 2 graus)
        self.assertTrue(r["is_daylight"])

    def test_altitude_ao_meio_dia_solar_segue_90_menos_latitude_menos_declinacao(self):
        # solstício de verão no hemisfério sul (dia 355, declinação ~ -23,4): em -23,55 o sol passa quase a pino
        verao = SolarCalculator.calculate_sun_position(day_of_year=355, solar_hour=12.0, latitude_deg=-23.55, longitude_deg=-45.0)
        inverno = SolarCalculator.calculate_sun_position(day_of_year=172, solar_hour=12.0, latitude_deg=-23.55, longitude_deg=-45.0)
        self.assertAlmostEqual(verao["altitude_deg"], 90 - abs(-23.55 + 23.4), delta=1.5)
        self.assertAlmostEqual(inverno["altitude_deg"], 90 - 23.55 - 23.4, delta=1.5)

    def test_noite_e_vetor_unitario(self):
        n = SolarCalculator.calculate_sun_position(solar_hour=0.0)
        self.assertFalse(n["is_daylight"])
        self.assertEqual(n["light_direction_3d"], [0.0, -1.0, 0.0])
        self.assertEqual(n["shadow_length_multiplier"], 0.0)
        d = SolarCalculator.calculate_sun_position(solar_hour=15.0)
        self.assertAlmostEqual(math.sqrt(sum(c * c for c in d["light_direction_3d"])), 1.0, places=3)

    def test_sol_da_manha_a_leste_e_da_tarde_a_oeste(self):
        manha = SolarCalculator.calculate_sun_position(day_of_year=80, solar_hour=8.0)
        tarde = SolarCalculator.calculate_sun_position(day_of_year=80, solar_hour=16.0)
        self.assertLess(manha["azimuth_deg"], 180.0)
        self.assertGreater(tarde["azimuth_deg"], 180.0)
        self.assertGreater(manha["sun_vector"][0], 0.0)  # x = leste
        self.assertLess(tarde["sun_vector"][0], 0.0)

    def test_curva_do_dia(self):
        c = SolarCalculator.generate_day_curve(day_of_year=355)
        self.assertEqual(len(c["hourly_positions"]), 13)  # 06h às 18h
        self.assertEqual(c["conforto_termico_status"], "Alta Radiação Solar")  # sol acima de 65 graus
        self.assertEqual(SolarCalculator.generate_day_curve(day_of_year=172)["conforto_termico_status"], "Adequado")


class TestTobogaEspiral(unittest.TestCase):
    def test_tubo_fechado_padrao(self):
        r = SpiralTubeGenerator.generate_spiral()
        self.assertEqual(r["faces_count"], 20 * 8)  # 1,25 volta * 16 passos = 20 anéis a mais 1, 8 lados
        self.assertEqual(r["vertices_count"], 21 * 8)
        helice = math.hypot(1.2 * 1.25 * 2 * math.pi, 2.4)  # comprimento exato da hélice
        self.assertAlmostEqual(r["path_length_m"], helice, delta=0.1)  # a poligonal fica um pouco abaixo
        self.assertLess(r["path_length_m"], helice)
        self.assertEqual(r["average_slope_deg"], 14.3)  # atan(2,4 / 9,4248)
        # v = sqrt(2 g H (1 - 0,2 / tan 14,3 graus))
        self.assertAlmostEqual(r["estimated_exit_speed_m_s"], math.sqrt(2 * 9.80665 * 2.4 * (1 - 0.2 / math.tan(math.radians(14.3)))), delta=0.02)
        self.assertTrue(all(0 <= i < r["vertices_count"] for f in r["faces"] for i in f))

    def test_calha_aberta_tem_mais_pontos_por_anel_e_a_mesma_contagem_de_faces(self):
        r = SpiralTubeGenerator.generate_spiral(is_open_gutter=True)
        self.assertEqual(r["vertices_count"], 21 * 9)
        self.assertEqual(r["faces_count"], 20 * 8)

    def test_altura_do_inicio_e_do_fim(self):
        r = SpiralTubeGenerator.generate_spiral(tube_radius_m=0.0001, tube_segments=4)
        zs = [v[2] for v in r["vertices"]]
        self.assertAlmostEqual(max(zs), 2.4, delta=0.01)
        self.assertAlmostEqual(min(zs), 0.0, delta=0.01)


def _inst(i, did, z_pol=0.0):
    return {"instance_id": i, "definition_id": did, "transform": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, z_pol, 1]}


class TestSequenciaDeMontagem(unittest.TestCase):
    def test_categorias_e_ordem_das_etapas(self):
        cena = {
            "definitions": [{"definition_id": n, "name": nome} for n, nome in
                            enumerate(["Tubo azul", "Coluna 160", "Sapata", "Escada", "Deck", "Tampa"], 1)],
            "instances": [_inst(i, i) for i in range(1, 7)],
        }
        r = AssemblySequencer.generate_steps(cena)
        self.assertEqual([s["category"] for s in r["steps"]], ["fundacao", "estruturas", "assoalhos", "escadas", "tubos", "outros"])
        self.assertEqual((r["total_steps"], r["total_instances"]), (6, 6))
        self.assertEqual(r["steps"][0]["instance_ids"], [3])
        self.assertEqual(r["steps"][0]["hardware_estimate"], "4 Parafusos Inox c/ Porca Travante")

    def test_pe_so_conta_como_palavra(self):
        self.assertEqual(AssemblySequencer._categorizar_peca("Tubo pequeno"), "tubos")
        self.assertEqual(AssemblySequencer._categorizar_peca("Pé de apoio"), "outros")  # sem acento no match: não vira fundação por engano
        self.assertEqual(AssemblySequencer._categorizar_peca("PE regulável"), "fundacao")

    def test_mesma_etapa_ordena_por_altura_e_agrupa_pecas(self):
        cena = {
            "definitions": [{"definition_id": 1, "name": "Coluna"}],
            "instances": [_inst(1, 1, 100.0), _inst(2, 1, 0.0)],  # 100 pol = 2,54 m
        }
        r = AssemblySequencer.generate_steps(cena)
        self.assertEqual(r["steps"][0]["instance_ids"], [2, 1])
        self.assertEqual(r["steps"][0]["parts"], [{"name": "Coluna", "count": 2}])

    def test_cena_vazia(self):
        self.assertEqual(AssemblySequencer.generate_steps({}), {"steps": [], "total_steps": 0, "total_instances": 0})


class _Face:
    def __init__(self, ptr):
        self.ptr = ptr


class _Api:
    def build_face_mesh(self, face):
        return {"vertices": [face.ptr, 0.0, 0.0]}


class TestCacheMalhas(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.antes = cache_malhas.PASTA
        cache_malhas.PASTA = Path(self.tmp.name)
        self.addCleanup(setattr, cache_malhas, "PASTA", self.antes)

    def test_chave_muda_com_nome_quantidade_e_geometria(self):
        fs = [_Face(1), _Face(2), _Face(3)]
        k = cache_malhas.chave(_Api(), "peca", fs)
        self.assertEqual(k, cache_malhas.chave(_Api(), "peca", fs))
        self.assertNotEqual(k, cache_malhas.chave(_Api(), "outra", fs))
        self.assertNotEqual(k, cache_malhas.chave(_Api(), "peca", fs[:2]))
        self.assertNotEqual(k, cache_malhas.chave(_Api(), "peca", [_Face(9), _Face(2), _Face(3)]))

    def test_ler_sem_arquivo_devolve_none(self):
        self.assertIsNone(cache_malhas.ler("inexistente", [_Face(1)]))

    def test_gravar_e_ler_devolve_a_mesma_malha(self):
        fs = [_Face(10), _Face(20)]
        malha = {
            "vertices": [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 1],
            "normals": [0, 0, 1] * 3 + [0, 1, 0] * 3,
            "indices": [0, 1, 2, 3, 4, 5],
            "face_ranges": [
                {"face_id": "face_a", "triangle_start": 0, "triangle_count": 1, "color": [255, 0, 0]},
                {"face_id": "face_14", "triangle_start": 1, "triangle_count": 1, "color": None},
            ],
        }
        cache_malhas.gravar("k1", malha, fs)
        lido = cache_malhas.ler("k1", fs)
        self.assertIsNotNone(lido)
        m, registro = lido
        self.assertEqual(set(registro), {"face_a", "face_14"})
        self.assertIs(registro["face_a"], fs[0])
        self.assertEqual([r["triangle_count"] for r in m["face_ranges"]], [1, 1])
        self.assertEqual(m["face_ranges"][0]["color"], [255, 0, 0])
        self.assertIsNone(m["face_ranges"][1]["color"])
        self.assertEqual(len(m["indices"]), 6)


if __name__ == "__main__":
    unittest.main()
