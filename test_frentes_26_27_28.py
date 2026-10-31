import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.repositories.skp_engine_repository import SkpEngineRepository
from app.services.scene_service import SceneService
from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    ExportAssemblyManualRequest,
    ExportDrawing2DRequest,
    SolarStudyRequest,
)


class TestFrentes26_27_28_Integration(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_fastapi_assembly_steps_and_manual(self):
        """Frente 26: Valida os endpoints FastAPI de etapas de montagem e manual HTML."""
        await self.controller.open_binary_scene(self.template_path)

        # 1. GET /assembly-steps
        res_steps = await self.controller.get_assembly_steps()
        self.assertGreaterEqual(res_steps.total_steps, 0)
        print(f"\n[Frente 26] Etapas calculadas: {res_steps.total_steps}, Instâncias: {res_steps.total_instances}")

        # 2. POST /export/assembly-manual
        out_html = os.path.join(self.tmp_dir, "api_manual_montagem.html")
        req_manual = ExportAssemblyManualRequest(project_name="Playground Parkelô Oficial", path=out_html)
        res_manual = await self.controller.export_assembly_manual(req_manual)
        self.assertTrue(res_manual.saved)
        self.assertTrue(os.path.exists(out_html))
        self.assertGreater(os.path.getsize(out_html), 500)
        print(f"[Frente 26] Manual HTML exportado: {out_html} ({os.path.getsize(out_html)} bytes)")

    async def test_02_fastapi_drawing_2d(self):
        """Frente 27: Valida o endpoint FastAPI de exportação de desenho técnico 2D vetorial SVG."""
        await self.controller.open_binary_scene(self.template_path)

        out_svg = os.path.join(self.tmp_dir, "api_planta_baixa.svg")
        req_svg = ExportDrawing2DRequest(
            path=out_svg,
            view_type="top",
            title="Prancha Técnica - Planta Baixa",
            scale="1:50",
        )
        res_svg = await self.controller.export_drawing_2d(req_svg)
        self.assertTrue(res_svg.saved)
        self.assertTrue(os.path.exists(out_svg))
        self.assertEqual(res_svg.view_type, "top")
        self.assertGreater(res_svg.file_size_bytes, 1000)
        print(f"[Frente 27] Desenho 2D SVG exportado: {out_svg} ({res_svg.file_size_bytes} bytes)")

    async def test_03_fastapi_solar_study(self):
        """Frente 28: Valida o endpoint FastAPI de estudo solar e sombras analíticas NBR 16071."""
        req_solar = SolarStudyRequest(day_of_year=80, hour=14.0, latitude=-23.5505, longitude=-46.6333)
        res_solar = await self.controller.calculate_solar_study(req_solar)

        self.assertIn("altitude_deg", res_solar.position)
        self.assertIn("azimuth_deg", res_solar.position)
        self.assertIn("conforto_termico_status", res_solar.day_curve)
        self.assertEqual(len(res_solar.day_curve["hourly_positions"]), 13)
        print(f"[Frente 28] Estudo Solar: Altitude={res_solar.position['altitude_deg']}°, Azimute={res_solar.position['azimuth_deg']}°, Status={res_solar.day_curve['conforto_termico_status']}")


if __name__ == "__main__":
    unittest.main()
