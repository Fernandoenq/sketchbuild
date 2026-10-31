"""
Testes de Integracao e Regressao para as Frentes 51 a 55 (Zero DLL).

- Frente 51: Gerador de Tubos e Tobogãs Espirais Paramétricos (Spiral Tube)
- Frente 52: Calculador de Centro de Gravidade e Estabilidade ao Tombamento (NBR 16071 / NBR 6123)
- Frente 53: Exportador de Ficha de Inspeção e Checklist de Campo Offline (HTML5 / PWA)
- Frente 54: Ferramenta de Cota Angular e Transferidor 3D (Angle Dimension)
- Frente 55: Otimizador de Parafusos, Buchas e Fixadores com Torque Recomendado (NBR 7190 / ISO 898)
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
    SpiralTubeRequest,
    OverturnStabilityRequest,
    FieldInspectionRequest,
    AngleDimensionRequest,
    FastenerTorqueRequest,
)


class TestFrentes51a55(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_frente_51_spiral_tube(self):
        """Valida gerador de tobogãs e tubos helicoidais paramétricos 3D (Frente 51)."""
        req = SpiralTubeRequest(
            radius_m=1.20,
            height_m=2.40,
            turns=1.25,
            tube_radius_m=0.38,
            segments_per_turn=16,
            tube_segments=8,
            is_open_gutter=False
        )
        res = await self.controller.generate_spiral_tube(req)
        self.assertEqual(res.entity_type, "SpiralTubeGeometry")
        self.assertEqual(res.radius_m, 1.20)
        self.assertGreater(res.vertices_count, 50)
        self.assertGreater(res.faces_count, 50)
        self.assertGreater(res.path_length_m, 5.0)
        self.assertGreater(res.estimated_exit_speed_m_s, 2.0)
        print(f"[Frente 51] Toboga Espiral: {res.vertices_count} vertices, {res.faces_count} faces (Comprimento: {res.path_length_m}m, Inclinacao: {res.average_slope_deg} deg, V_saida: {res.estimated_exit_speed_m_s}m/s)")

    async def test_02_frente_52_overturn_stability(self):
        """Valida estabilidade ao tombamento sob ação de vento NBR 6123 e empuxo de multidão (Frente 52)."""
        req = OverturnStabilityRequest(
            total_mass_kg=850.0,
            cg_position=[1.50, 1.20, 1.45],
            base_support_points=[[0.0, 0.0], [3.0, 0.0], [3.0, 2.4], [0.0, 2.4]],
            wind_speed_km_h=100.0,
            exposed_frontal_area_m2=6.50,
            lateral_live_load_n=500.0,
            live_load_height_m=1.80
        )
        res = await self.controller.calculate_overturn_stability(req)
        self.assertEqual(res.entity_type, "OverturnStabilityAnalysis")
        self.assertGreater(res.restoring_moment_kn_m, 5.0)
        self.assertGreater(res.overturning_moment_kn_m, 1.0)
        self.assertGreater(res.safety_factor, 1.0)
        print(f"[Frente 52] Estabilidade ao Tombamento: {res.status} (M_rest={res.restoring_moment_kn_m} kN.m, M_tomb={res.overturning_moment_kn_m} kN.m, FS={res.safety_factor})")

    async def test_03_frente_53_field_inspection_html(self):
        """Valida exportação de ficha de inspeção e checklist de campo NBR 16071 em HTML5 offline (Frente 53)."""
        output_file = os.path.join(self.tmp_dir, "test_checklist_campo.html")
        if os.path.exists(output_file):
            os.remove(output_file)

        req = FieldInspectionRequest(
            park_name="Parque Villa-Lobos - Setor Ludico",
            inspector_name="Eng. Fernando Henrique",
            inspection_date="2026-03-01",
            output_filename=output_file
        )
        res = await self.controller.export_field_inspection_html(req)
        self.assertTrue(os.path.exists(res.file_path))
        self.assertGreater(res.size_bytes, 2000)
        self.assertEqual(res.items_count, 10)

        with open(res.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("FICHA TÉCNICA DE INSPEÇÃO EM CAMPO", content)
            self.assertIn("signature-pad", content)
            self.assertIn("Parque Villa-Lobos", content)

        print(f"[Frente 53] Ficha de Inspecao HTML5 gerada: {res.size_bytes} bytes ({res.file_path})")
        if os.path.exists(output_file):
            os.remove(output_file)

    async def test_04_frente_54_angle_dimension(self):
        """Valida ferramenta de cota angular e arco gráfico 3D (Frente 54)."""
        # Teste com ângulo de 90 graus: V=(0,0,0), A=(1,0,0), B=(0,1,0)
        req = AngleDimensionRequest(
            vertex_point=[0.0, 0.0, 0.0],
            point_a=[1.0, 0.0, 0.0],
            point_b=[0.0, 1.0, 0.0],
            arc_radius_m=0.60
        )
        res = await self.controller.calculate_angle_dimension(req)
        self.assertEqual(res.entity_type, "AngleDimension")
        self.assertAlmostEqual(res.angle_degrees, 90.0, places=1)
        self.assertEqual(res.plane_normal, [0.0, 0.0, 1.0])
        self.assertGreater(res.arc_points_count, 10)
        self.assertIn("90", res.text_label)
        print(f"[Frente 54] Cota Angular: {res.text_label} ({res.angle_gms}) no plano Z com {res.arc_points_count} pontos de arco")

    async def test_05_frente_55_fastener_torque(self):
        """Valida dimensionador de fixadores e cálculo de torque normativo NBR 7190 (Frente 55)."""
        req = FastenerTorqueRequest(
            timber_thickness_mm=160.0,
            steel_plate_thickness_mm=4.75,
            bolt_standard="1/2_POL",
            material_grade="Inox_304",
            friction_factor_k=0.18
        )
        res = await self.controller.calculate_fastener_torque(req)
        self.assertEqual(res.entity_type, "FastenerTorqueSpecification")
        self.assertEqual(res.bolt_standard, "1/2_POL")
        self.assertGreater(res.commercial_bolt_length_mm, 180.0)
        self.assertGreater(res.recommended_torque_n_m, 5.0)
        self.assertIn("DIN 985", res.recommended_nut)
        self.assertIn("DIN 9021", res.recommended_washer)
        print(f"[Frente 55] Otimizador de Fixadores: Parafuso {res.bolt_standard} x {res.commercial_bolt_length_mm}mm, Torque={res.recommended_torque_n_m} N.m ({res.recommended_torque_kgf_m} kgf.m)")


if __name__ == "__main__":
    unittest.main()
