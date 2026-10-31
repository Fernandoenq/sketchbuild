"""
Testes Unitários Automatizados - Frentes 76 a 80
SketchBuild - Engenharia Reversa do SketchUp (Zero DLL)
Frente 76: DimensionRadialEngine (SUDimensionRadialRef - Cotas de Raio e Diâmetro)
Frente 77: FogDepthEngine (SUStyleRef - Névoa Atmosférica e Profundidade)
Frente 78: SmoothSoftEdgesEngine (Soften & Smooth Edges - Phong Normals)
Frente 79: SectionHatchPatternEngine (Hachuras Gráficas NBR 6492 / ISO 128)
Frente 80: GeoReferenceEngine (SUGeoReferenceRef - WGS84 & UTM)
"""

import math
import unittest

from core.dimension_radial_engine import DimensionRadialEngine
from core.fog_depth_engine import FogDepthEngine
from core.smooth_soft_edges_engine import SmoothSoftEdgesEngine
from core.section_hatch_engine import SectionHatchPatternEngine
from core.geo_reference_engine import GeoReferenceEngine


class TestFrentes76A80(unittest.TestCase):

    def test_frente_76_dimension_radial_engine(self):
        # 1. Cota Radial de raio 3.0m
        r_dim = DimensionRadialEngine.create_radial_dimension(
            center=(0.0, 0.0, 0.0),
            radius=3.0,
            angle_deg=45.0,
            is_diameter=False,
            unit="m",
            precision=2,
        )
        self.assertEqual(r_dim["type"], "SUDimensionRadialRef")
        self.assertFalse(r_dim["is_diameter"])
        self.assertEqual(r_dim["radius_m"], 3.0)
        self.assertEqual(r_dim["text"], "R 3.00 m")
        self.assertGreater(len(r_dim["line_segments"]), 1)

        # 2. Cota Diamétrica de raio 1.5m -> Ø 3.00 m
        d_dim = DimensionRadialEngine.create_radial_dimension(
            center=(0.0, 0.0, 0.0),
            radius=1.5,
            angle_deg=0.0,
            is_diameter=True,
            unit="m",
            precision=2,
        )
        self.assertTrue(d_dim["is_diameter"])
        self.assertEqual(d_dim["text"], "Ø 3.00 m")

    def test_frente_77_fog_depth_engine(self):
        # 1. Configuração direta de névoa
        fog = FogDepthEngine.configure_fog(enabled=True, start_dist_m=15.0, end_dist_m=80.0, color_hex="#cccccc")
        self.assertEqual(fog["entity_type"], "SUStyleFog")
        self.assertTrue(fog["enabled"])
        self.assertEqual(fog["three_fog"]["near"], 15.0)
        self.assertEqual(fog["three_fog"]["far"], 80.0)

        # 2. Auto-fog derivado da Bounding Box de um modelo de 10x10x10m
        auto_fog = FogDepthEngine.calculate_auto_fog_from_bbox((0.0, 0.0, 0.0), (10.0, 10.0, 10.0))
        self.assertTrue(auto_fog["enabled"])
        diag = math.sqrt(300.0)
        self.assertAlmostEqual(auto_fog["start_distance_m"], round(diag * 0.6, 2), places=1)

    def test_frente_78_smooth_soft_edges_engine(self):
        # Malha de 2 triângulos quase coplanares formando um retângulo suave (ângulo diedro pequeno)
        verts = [(0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.1), (0.0, 2.0, 0.1)]
        faces = [[0, 1, 2], [0, 2, 3]]  # Aresta (0, 2) compartilhada
        res = SmoothSoftEdgesEngine.process_mesh_smoothing(verts, faces, angle_threshold_deg=35.0)

        self.assertEqual(res["entity_type"], "MeshSmoothingResult")
        self.assertEqual(res["total_edges"], 5)  # 4 bordas + 1 diagonal interna
        self.assertEqual(res["soft_edges_count"], 1)
        self.assertEqual(len(res["vertex_normals"]), 4)

    def test_frente_79_section_hatch_engine(self):
        # Seção quadrada de 1.0m x 1.0m cortada no plano horizontal Z = 0
        loop = [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (0.0, 1.0, 0.0),
        ]
        hatch = SectionHatchPatternEngine.generate_hatch_lines(
            closed_loop_3d=loop,
            pattern="WOOD",
            spacing_m=0.1,
            angle_deg=45.0,
        )
        self.assertEqual(hatch["entity_type"], "SectionHatchResult")
        self.assertEqual(hatch["pattern"], "WOOD")
        self.assertGreater(hatch["hatch_lines_count"], 5)

    def test_frente_80_geo_reference_engine(self):
        # São Paulo (-23.5505, -46.6333)
        geo = GeoReferenceEngine.set_geo_location(
            latitude=-23.5505,
            longitude=-46.6333,
            altitude_m=760.0,
            north_angle_deg=15.0,
            city="São Paulo",
            country="Brasil",
        )
        self.assertEqual(geo["type"], "SUGeoReferenceRef")
        self.assertEqual(geo["utm"]["zone"], 23)
        self.assertEqual(geo["utm"]["hemisphere"], "S")

        # Conversão de ponto local (100m ao norte) para coordenada WGS84
        pt_geo = GeoReferenceEngine.local_point_to_wgs84(
            local_xyz_m=(0.0, 100.0, 0.0),
            origin_lat=-23.5505,
            origin_lon=-46.6333,
            origin_alt_m=760.0,
            north_angle_deg=0.0,
        )
        self.assertGreater(pt_geo["latitude"], -23.5505)  # Deslocou para o Norte


if __name__ == "__main__":
    unittest.main()
