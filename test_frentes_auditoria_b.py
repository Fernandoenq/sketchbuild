"""Auditoria (A5), parte B: HIC, telhado de 4 águas, tombamento e balanço, com valores calculados fora do código.

HIC e balanço usam modelos simplificados do próprio módulo (deformação estimada, onda semi-senoidal): os testes
conferem a conta e as relações físicas, não a validade do modelo frente à NBR 16071.
"""
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.hic_simulator import HicSimulator  # noqa: E402
from core.hip_roof_generator import HipRoofGenerator  # noqa: E402
from core.overturn_stability_calculator import OverturnStabilityCalculator  # noqa: E402
from core.swing_kinematics_simulator import SwingKinematicsSimulator  # noqa: E402


def _area_poligono(v, face):
    """Área de um polígono 3D pelo vetor área (soma de produtos vetoriais)."""
    sx = sy = sz = 0.0
    for i in range(len(face)):
        a, b = v[face[i]], v[face[(i + 1) % len(face)]]
        sx += a[1] * b[2] - a[2] * b[1]
        sy += a[2] * b[0] - a[0] * b[2]
        sz += a[0] * b[1] - a[1] * b[0]
    return 0.5 * math.sqrt(sx * sx + sy * sy + sz * sz)


class TestHic(unittest.TestCase):
    def test_queda_de_1_80_na_areia(self):
        r = HicSimulator.simulate_impact()
        self.assertEqual(r["impact_velocity_m_s"], 5.94)  # sqrt(2 * 9,80665 * 1,8)
        self.assertEqual(r["impact_duration_ms"], 40.4)  # 2 * 0,12 m de deformação / 5,94
        self.assertEqual(r["peak_deceleration_g"], 23.6)
        self.assertEqual(r["hic_score"], 35.2)
        self.assertTrue(r["is_compliant"])
        self.assertEqual(r["recommended_thickness_mm"], 200.0)
        self.assertEqual(r["curve_points_count"], 21)
        self.assertEqual(r["curve_points"][0]["deceleration_g"], 0.0)
        self.assertEqual(r["curve_points"][10]["deceleration_g"], r["peak_deceleration_g"])  # meio da semi-senoide
        self.assertAlmostEqual(r["curve_points"][-1]["time_ms"], r["impact_duration_ms"], delta=0.05)

    def test_altura_acima_da_critica_nao_conforma(self):
        r = HicSimulator.simulate_impact(fall_height_m=3.5)  # areia: altura crítica de 3,0 m
        self.assertFalse(r["is_compliant"])
        self.assertEqual(r["recommended_thickness_mm"], 300.0)
        self.assertIn("NÃO CONFORME", r["safety_verdict"])
        self.assertTrue(HicSimulator.simulate_impact(fall_height_m=0.9, surface_type="grama_natural", installed_thickness_mm=100)["is_compliant"])  # 0,9 m < 1,0 m da grama
        self.assertFalse(HicSimulator.simulate_impact(fall_height_m=1.2, surface_type="grama_natural")["is_compliant"])

    def test_emborrachado_espessura_recomendada(self):
        self.assertEqual(HicSimulator.simulate_impact(fall_height_m=1.0, surface_type="borracha_epdm")["recommended_thickness_mm"], 30.0)
        self.assertEqual(HicSimulator.simulate_impact(fall_height_m=2.0, surface_type="borracha_epdm")["recommended_thickness_mm"], 60.0)


class TestTelhadoQuatroAguas(unittest.TestCase):
    def test_retangular_padrao(self):
        r = HipRoofGenerator.generate_hip_roof()
        self.assertEqual(r["roof_type"], "Quatro Águas (Hip Roof)")
        self.assertEqual(r["ridge_length_m"], 0.8)  # (3,2 - 2,4) sem diferença de beiral
        self.assertEqual(r["apex_height_m"], 3.695)  # 2,8 + 1,55 * tan 30
        self.assertEqual(r["sloped_roof_area_m2"], 13.96)  # 3,1 * 3,9 / cos 30
        self.assertEqual(r["hip_rafter_length_m"], 2.37)
        self.assertEqual((r["vertices_count"], r["faces_count"]), (6, 5))

    def test_area_da_malha_bate_com_a_area_inclinada(self):
        """Independente da fórmula do módulo: soma a área dos 4 planos de água da malha gerada."""
        for kw in ({}, {"base_width_m": 2.0, "base_length_m": 5.0, "pitch_deg": 20.0, "overhang_m": 0.5}):
            r = HipRoofGenerator.generate_hip_roof(**kw)
            v = r["vertices"]
            aguas = sum(_area_poligono(v, f) for f in r["faces"][:-1])  # a última face é o forro
            self.assertAlmostEqual(aguas, r["sloped_roof_area_m2"], delta=0.02)

    def test_piramidal_quando_a_base_e_quadrada(self):
        r = HipRoofGenerator.generate_hip_roof(base_width_m=2.4, base_length_m=2.4)
        self.assertEqual(r["roof_type"], "Piramidal")
        self.assertEqual((r["vertices_count"], r["faces_count"]), (5, 5))
        self.assertEqual(r["ridge_length_m"], 0.0)


class TestTombamento(unittest.TestCase):
    def test_deck_padrao_estavel(self):
        r = OverturnStabilityCalculator.calculate_stability()
        self.assertEqual(r["restoring_arm_m"], 1.2)  # menor distância do CG às bordas do deck 3,0 x 2,4
        self.assertEqual(r["restoring_moment_kn_m"], 10.003)  # 850 * 9,80665 * 1,2
        self.assertEqual(r["wind_pressure_pa"], 473.0)  # 0,613 * (100 / 3,6)^2
        self.assertEqual(r["wind_force_kn"], 3.689)  # 473 * 6,5 * 1,2
        self.assertEqual(r["overturning_moment_kn_m"], 6.25)  # 3,689 * 1,45 + 500 * 1,8
        self.assertEqual(r["safety_factor"], 1.6)
        self.assertTrue(r["is_stable"])
        self.assertEqual(r["extra_ballast_kg"], 0.0)

    def test_leve_demais_pede_lastro(self):
        r = OverturnStabilityCalculator.calculate_stability(total_mass_kg=300.0)
        self.assertEqual(r["safety_factor"], 0.56)
        self.assertFalse(r["is_stable"])
        # (1,5 * M_tomb / braço - peso) / g = (1,5 * 6249,5 / 1,2 - 2941,995) / 9,80665 = 496,6 kg
        self.assertEqual(r["extra_ballast_kg"], 496.6)
        self.assertEqual(r["extra_concrete_volume_m3"], 0.207)  # 496,6 / 2400

    def test_sem_vento_e_sem_carga_fs_99(self):
        r = OverturnStabilityCalculator.calculate_stability(wind_speed_km_h=0, lateral_live_load_n=0)
        self.assertEqual(r["safety_factor"], 99.0)


class TestBalanco(unittest.TestCase):
    def test_pendulo_a_45_graus(self):
        r = SwingKinematicsSimulator.simulate_swing()
        self.assertEqual(r["max_tangential_speed_m_s"], 3.555)  # sqrt(2 g L (1 - cos 45))
        self.assertEqual(r["max_chain_tension_kn"], 0.778)  # m g (3 - 2 cos 45)
        self.assertEqual(r["suspension_height_m"], 2.65)
        self.assertEqual(r["required_impact_zone_length_m"], 3.161)  # 0,867 sqrt(2,65) + 1,75
        self.assertEqual(r["trajectory_points_count"], 121)  # 5 s a 24 fps, mais o instante zero
        p0 = r["trajectory_points"][0]
        self.assertEqual(p0["angle_deg"], 45.0)
        self.assertEqual(p0["position"], [1.5556, 0.0, 1.0944])  # L sin 45 ; H - L cos 45
        self.assertTrue(r["seat_clearance_compliant"])

    def test_amortecimento_reduz_a_amplitude(self):
        r = SwingKinematicsSimulator.simulate_swing(damping_ratio=0.2, total_time_s=10.0)
        angulos = [abs(p["angle_deg"]) for p in r["trajectory_points"]]
        self.assertLess(max(angulos[len(angulos) // 2:]), max(angulos[:len(angulos) // 2]))
        self.assertLess(angulos[-1], 5.0)

    def test_altura_do_assento_fora_da_norma(self):
        for h in (0.30, 0.70):
            self.assertFalse(SwingKinematicsSimulator.simulate_swing(seat_height_at_rest_m=h)["seat_clearance_compliant"])
        self.assertTrue(SwingKinematicsSimulator.simulate_swing(seat_height_at_rest_m=0.60)["seat_clearance_compliant"])


if __name__ == "__main__":
    unittest.main()
