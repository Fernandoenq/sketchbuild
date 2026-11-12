"""Auditoria (A5): testes de valor exato, calculados à mão, para módulos que estavam SEM TESTE (parte A).

Cada valor esperado vem de conta feita aqui no teste, não de rodar o código. Isso prova que o módulo faz a conta
que o nome promete; não prova que as constantes (fatores de emissão, tensões) são as da norma citada.
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.angle_dimension_tool import AngleDimensionTool  # noqa: E402
from core.carbon_footprint_calculator import CarbonFootprintCalculator  # noqa: E402
from core.cargo_load_optimizer import CargoLoadOptimizer  # noqa: E402
from core.exploded_view_trail_tool import ExplodedViewTrailTool  # noqa: E402
from core.fastener_torque_optimizer import FastenerTorqueOptimizer  # noqa: E402


class TestAnguloCotado(unittest.TestCase):
    def test_noventa_graus(self):
        r = AngleDimensionTool.calculate_angle_dimension((0, 0, 0), (1, 0, 0), (0, 1, 0))
        self.assertEqual(r["angle_degrees"], 90.0)
        self.assertEqual(r["angle_radians"], 1.5708)
        self.assertEqual(r["angle_gms"], "90° 00' 00\"")
        self.assertEqual(r["plane_normal"], [0.0, 0.0, 1.0])
        self.assertEqual(r["arc_points_count"], 17)
        self.assertEqual(r["arc_points"][0], [0.6, 0.0, 0.0])
        self.assertEqual(r["arc_points"][-1], [0.0, 0.6, 0.0])
        meio = 0.69 * math.cos(math.pi / 4)  # rótulo a 115% do raio, na metade do arco
        self.assertEqual(r["label_position"], [round(meio, 4), round(meio, 4), 0.0])
        self.assertEqual(r["text_label"], "90.0°")

    def test_sessenta_graus_em_3d_e_colinear(self):
        r = AngleDimensionTool.calculate_angle_dimension(
            (1, 1, 1), (2, 1, 1), (1 + math.cos(math.pi / 3), 1 + math.sin(math.pi / 3), 1))
        self.assertEqual(r["angle_degrees"], 60.0)
        r = AngleDimensionTool.calculate_angle_dimension((0, 0, 0), (1, 0, 0), (-1, 0, 0))
        self.assertEqual(r["angle_degrees"], 180.0)
        self.assertEqual(r["plane_normal"], [0.0, 0.0, 1.0])  # colinear: normal arbitrária documentada

    def test_ponto_igual_ao_vertice(self):
        with self.assertRaises(ValueError):
            AngleDimensionTool.calculate_angle_dimension((0, 0, 0), (0, 0, 0), (1, 0, 0))


class TestPegadaDeCarbono(unittest.TestCase):
    def test_padrao(self):
        r = CarbonFootprintCalculator.calculate_footprint()
        # 2,8 m3 * 950 = 2660 ; aço 95*2,1 = 199,5 ; plástico 45*1,95 = 87,75
        # peso 2,8*0,75 + 0,095 + 0,045 = 2,24 t ; transporte 2,24*350*0,12 = 94,08 ; fábrica 18
        self.assertEqual(r["co2_sequestered_kg"], 2660.0)
        self.assertEqual(r["co2_steel_emissions_kg"], 199.5)
        self.assertEqual(r["co2_transport_emissions_kg"], 94.1)
        self.assertEqual(r["total_emissions_kg"], 399.3)  # 199,5 + 87,75 + 94,08 + 18 = 399,33
        self.assertEqual(r["net_carbon_balance_kg"], 2260.7)
        self.assertTrue(r["is_carbon_negative"])
        self.assertEqual(r["equivalent_trees_planted_years"], 102.8)  # 2260,67 / 22

    def test_sem_madeira_emite_mais_do_que_sequestra(self):
        r = CarbonFootprintCalculator.calculate_footprint(
            timber_volume_m3=0, steel_weight_kg=100, plastic_weight_kg=0, transport_distance_km=0)
        self.assertEqual(r["total_emissions_kg"], 228.0)  # 100*2,1 + fábrica 18
        self.assertEqual(r["net_carbon_balance_kg"], -228.0)
        self.assertFalse(r["is_carbon_negative"])
        self.assertEqual(r["equivalent_trees_planted_years"], 0.0)
        self.assertEqual(r["sustainability_badge"], "NEUTRO EM CARBONO")


class TestCargaDoCaminhao(unittest.TestCase):
    PACOTES = [
        {"name": "A", "length_m": 2, "width_m": 2, "height_m": 1, "weight_kg": 100, "quantity": 1},
        {"name": "B", "length_m": 1, "width_m": 1, "height_m": 1, "weight_kg": 50, "quantity": 2},
    ]

    def test_posicoes_e_centro_de_gravidade(self):
        r = CargoLoadOptimizer.optimize_load(self.PACOTES, "caminhao_toco")
        self.assertEqual([i["position"] for i in r["packed_items"]], [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [3.0, 0.0, 0.0]])
        self.assertEqual(r["packed_items"][0]["name"], "A")  # a mais pesada vai primeiro
        # cg_x = (1*100 + 2,5*50 + 3,5*50)/200 = 2 ; cg_y = 0,75 ; cg_z = 0,5
        self.assertEqual(r["center_of_gravity"], [2.0, 0.75, 0.5])
        self.assertEqual(r["total_cargo_weight_kg"], 200.0)
        self.assertEqual(r["total_cargo_volume_m3"], 6.0)
        self.assertEqual(r["vehicle_volume_m3"], 35.71)  # 6,2 * 2,4 * 2,4
        self.assertEqual(r["volumetric_occupancy_pct"], 16.8)
        self.assertEqual(r["weight_occupancy_pct"], 3.3)
        self.assertEqual(r["status"], "CARGA 100% ALOCADA")

    def test_excesso_de_peso(self):
        r = CargoLoadOptimizer.optimize_load(self.PACOTES, "caminhao_toco", {"payload_kg": 120.0})
        self.assertEqual(r["packed_items_count"], 1)
        self.assertEqual(r["unpacked_items_count"], 2)
        self.assertEqual({i["reason"] for i in r["unpacked_items"]}, {"Excesso de peso máximo do veículo"})
        self.assertEqual(r["status"], "2 ITENS NÃO COUBERAM")

    def test_falta_de_espaco(self):
        grande = [{"name": "G", "length_m": 7, "width_m": 1, "height_m": 1, "weight_kg": 10, "quantity": 1}]
        r = CargoLoadOptimizer.optimize_load(grande, "caminhao_toco")  # baú de 6,2 m
        self.assertEqual(r["packed_items_count"], 0)
        self.assertEqual(r["unpacked_items"][0]["reason"], "Volume maior que as dimensões do baú")  # era empacotado por engano

    def test_falta_de_espaco_volumetrico(self):
        # baú 6,2 x 2,4 x 2,4: cada volume de 6 x 2,4 x 2,4 ocupa o baú todo; o segundo não cabe
        dois = [{"name": "V", "length_m": 6, "width_m": 2.4, "height_m": 2.4, "weight_kg": 10, "quantity": 2}]
        r = CargoLoadOptimizer.optimize_load(dois, "caminhao_toco")
        self.assertEqual((r["packed_items_count"], r["unpacked_items_count"]), (1, 1))
        self.assertEqual(r["unpacked_items"][0]["reason"], "Falta de espaço volumétrico no baú")


class TestTrilhaDaVistaExplodida(unittest.TestCase):
    def test_trilha_e_tracejado(self):
        partes = [
            {"id": "base", "name": "Base", "original_pos": [0, 0, 0], "exploded_pos": [0, 0, 0.005]},  # < 1 cm: sem trilha
            {"id": "p1", "name": "Peça 1", "original_pos": [0, 0, 0], "exploded_pos": [0, 0, 1]},
            {"id": "p2", "name": "Peça 2", "original_pos": [1, 0, 0], "exploded_pos": [4, 4, 0]},
        ]
        r = ExplodedViewTrailTool.calculate_trails(partes)
        self.assertEqual(r["parts_with_trails_count"], 2)
        self.assertEqual(r["total_trail_length_m"], 6.0)  # 1 + 5
        t = r["trails"][0]
        self.assertEqual(t["length_m"], 1.0)
        self.assertEqual(t["direction"], [0.0, 0.0, 1.0])
        self.assertEqual(t["segments_count"], 12)  # int(1 / (0,05 + 0,03))
        self.assertEqual(t["dashed_segments"][0], [[0.0, 0.0, 0.0], [0.0, 0.0, 0.05]])
        self.assertEqual(t["dashed_segments"][-1], [[0.0, 0.0, 0.88], [0.0, 0.0, 0.93]])
        self.assertEqual(r["trails"][1]["direction"], [0.6, 0.8, 0.0])


class TestTorqueDeParafuso(unittest.TestCase):
    def test_meia_polegada_padrao(self):
        r = FastenerTorqueOptimizer.calculate_connection_fasteners()
        # pacote 160 + 4,75 + 6 (arruelas) + 1,2*12,7 (porca) + 6 (rosca) = 191,99 -> comercial 200
        self.assertEqual(r["grip_length_mm"], 164.75)
        self.assertEqual(r["min_required_bolt_length_mm"], 192.0)
        self.assertEqual(r["commercial_bolt_length_mm"], 200.0)
        # F = 6 N/mm2 * 1008 mm2 = 6048 N ; Fp = 0,75 F = 4536 N ; T = 0,18 * 0,0127 m * 4536 = 10,37 N.m
        self.assertEqual(r["max_wood_crushing_force_kn"], 6.05)
        self.assertEqual(r["pretension_force_kn"], 4.54)
        self.assertEqual(r["recommended_torque_n_m"], 10.4)
        self.assertEqual(r["recommended_torque_kgf_m"], 1.06)  # 10,369 / 9,80665
        self.assertEqual(r["socket_tool_size_mm"], 19)

    def test_m16_e_padrao_desconhecido(self):
        r = FastenerTorqueOptimizer.calculate_connection_fasteners(
            timber_thickness_mm=100, steel_plate_thickness_mm=0, bolt_standard="M16")
        # 100 + 0 + 6 + 19,2 + 6 = 131,2 -> 140 ; F = 6*1767 = 10602 ; Fp = 7951,5 ; T = 0,18*0,016*7951,5 = 22,90
        self.assertEqual(r["commercial_bolt_length_mm"], 140.0)
        self.assertEqual(r["recommended_torque_n_m"], 22.9)
        r2 = FastenerTorqueOptimizer.calculate_connection_fasteners(bolt_standard="XYZ")
        self.assertEqual(r2["nominal_diameter_mm"], 12.7)  # cai no padrão de 1/2 polegada


if __name__ == "__main__":
    unittest.main()
