"""
Testes de Integracao e Regressao para as Frentes 46 a 50 (Zero DLL).

- Frente 46: Simulador de Trajetória e Cinemática de Balanço / Pêndulo (NBR 16071)
- Frente 47: Gerador de Relatório Técnico de ART / RRT em PDF
- Frente 48: Inspetor de Espessura de Parede e Detecção de Casca Fina
- Frente 49: Empacotador de Carga para Transporte / Cubagem de Frete 3D
- Frente 50: Renderizador Estilizado Linha Oculta / Esboço Técnico (NPR Cartoon / Overshoot)
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    SwingKinematicsRequest,
    ArtReportRequest,
    WallThicknessRequest,
    CargoLoadRequest,
    TechnicalSketchRequest,
)


class TestFrentes46a50(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_frente_46_swing_kinematics(self):
        """Valida cinemática e envelope de segurança do balanço segundo NBR 16071 (Frente 46)."""
        req = SwingKinematicsRequest(
            chain_length_m=2.20,
            user_mass_kg=50.0,
            initial_angle_deg=45.0,
            seat_height_at_rest_m=0.45,
            damping_ratio=0.05,
            total_time_s=3.0,
            fps=20
        )
        res = await self.controller.simulate_swing_kinematics(req)
        self.assertEqual(res.entity_type, "SwingKinematicsAnalysis")
        self.assertEqual(res.chain_length_m, 2.20)
        self.assertTrue(res.seat_clearance_compliant)
        self.assertGreater(res.max_tangential_speed_m_s, 2.0)
        self.assertGreater(res.max_chain_tension_kn, 0.5)
        self.assertGreater(res.required_impact_zone_length_m, 2.5)
        self.assertGreater(res.trajectory_points_count, 10)
        self.assertIn("CONFORME", res.safety_status)
        print(f"[Frente 46] Balanco NBR 16071: {res.safety_status} (Vmax={res.max_tangential_speed_m_s}m/s, Tracao={res.max_chain_tension_kn}kN, Zona Queda={res.required_impact_zone_length_m}m)")

    async def test_02_frente_47_art_report_pdf(self):
        """Valida compilador de minuta de ART / RRT em PDF 1.4 nativo (Frente 47)."""
        output_file = os.path.join(self.tmp_dir, "test_minuta_art.pdf")
        if os.path.exists(output_file):
            os.remove(output_file)

        req = ArtReportRequest(
            professional_name="Eng. Fernando Henrique",
            crea_cau="CREA-SP 5060708090/D",
            rnp="2619087654",
            contractor="Condomínio Residencial Parque das Árvores",
            location="Av. das Nações Unidas, 14261 - São Paulo/SP",
            project_name="Playground Modular Parkelô Floresta NBR 16071",
            output_filename=output_file
        )
        res = await self.controller.generate_art_pdf(req)
        self.assertTrue(os.path.exists(res.file_path))
        self.assertGreater(res.size_bytes, 1000)
        self.assertEqual(res.professional_name, "Eng. Fernando Henrique")

        # Verifica cabeçalho oficial do PDF
        with open(res.file_path, "rb") as f:
            header = f.read(8)
            self.assertEqual(header[:5], b"%PDF-")

        print(f"[Frente 47] Minuta de ART / RRT em PDF gerada: {res.size_bytes} bytes ({res.file_path})")
        if os.path.exists(output_file):
            os.remove(output_file)

    async def test_03_frente_48_wall_thickness(self):
        """Valida inspetor analítico de espessura de parede em rotomoldados (Frente 48)."""
        await self.controller.open_binary_scene(self.template_path)
        req = WallThicknessRequest(min_thickness_mm=6.0, max_thickness_mm=14.0)
        res = await self.controller.inspect_wall_thickness(req)
        self.assertEqual(res.entity_type, "WallThicknessInspection")
        self.assertGreater(res.samples_count, 0)
        self.assertGreater(res.avg_thickness_mm, 5.0)
        self.assertIn("APROVADO", res.status)
        print(f"[Frente 48] Inspetor de Espessura de Parede: {res.status} (Media: {res.avg_thickness_mm}mm, Min: {res.min_thickness_mm}mm, Defeitos: {res.thin_wall_defects_count})")

    async def test_04_frente_49_cargo_load_optimizer(self):
        """Valida otimizador de cubagem de frete e carregamento 3D de caminhão (Frente 49)."""
        packages = [
            {"name": "Colunas Eucalipto 16cm Amarradas", "length_m": 3.00, "width_m": 0.80, "height_m": 0.60, "weight_kg": 650.0, "quantity": 2},
            {"name": "Decks e Plataformas Pre-Montadas", "length_m": 1.20, "width_m": 1.20, "height_m": 0.50, "weight_kg": 220.0, "quantity": 4},
            {"name": "Pallet Ferragens e Fixadores Inox", "length_m": 1.00, "width_m": 1.00, "height_m": 0.80, "weight_kg": 400.0, "quantity": 1},
        ]
        req = CargoLoadRequest(packages=packages, vehicle_type="caminhao_truck")
        res = await self.controller.optimize_cargo_load(req)
        self.assertEqual(res.entity_type, "CargoLoadPlan")
        self.assertEqual(res.vehicle_type, "caminhao_truck")
        self.assertEqual(res.packed_items_count, 7)  # 2 + 4 + 1
        self.assertEqual(res.unpacked_items_count, 0)
        self.assertGreater(res.total_cargo_weight_kg, 2000.0)
        self.assertGreater(res.volumetric_occupancy_pct, 5.0)
        self.assertEqual(len(res.center_of_gravity), 3)
        print(f"[Frente 49] Otimizador de Carga 3D: {res.status} ({res.packed_items_count} volumes, Peso: {res.total_cargo_weight_kg}kg, Ocupacao: {res.volumetric_occupancy_pct}% bau)")

    async def test_05_frente_50_technical_sketch(self):
        """Valida renderizador estilizado com traço arquitetônico e overshoot (Frente 50)."""
        output_file = os.path.join(self.tmp_dir, "test_esboco_arquitetonico.svg")
        if os.path.exists(output_file):
            os.remove(output_file)

        req = TechnicalSketchRequest(
            dihedral_angle_threshold_deg=25.0,
            overshoot_mm=8.0,
            output_filename=output_file
        )
        res = await self.controller.generate_technical_sketch(req)
        self.assertTrue(os.path.exists(res.file_path))
        self.assertGreater(res.size_bytes, 500)
        self.assertGreater(res.sharp_edges_count, 0)
        self.assertEqual(res.overshoot_mm, 8.0)

        with open(res.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<svg", content)
            self.assertIn("OVERSHOOT", content)
            self.assertIn("hand-drawn-filter", content)

        print(f"[Frente 50] Esboco Tecnico Arquitetonico gerado: {res.sharp_edges_count} arestas com overshoot {res.overshoot_mm}mm ({res.size_bytes} bytes)")
        if os.path.exists(output_file):
            os.remove(output_file)


if __name__ == "__main__":
    unittest.main()
