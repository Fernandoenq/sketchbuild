"""
Testes Unitários Automatizados - Frentes 66 a 70
SketchBuild - Engenharia Reversa do SketchUp (Zero DLL)
Frente 66: CurveEngine (SUCurveRef / SUArcCurveRef)
Frente 67: SectionPlaneEngine (SUSectionPlaneRef / Slicing / Inversion)
Frente 68: FaceStylesEngine (FaceRenderModes / Glass Shader)
Frente 69: ScenesAnimationEngine (SUSceneRef / Page Transitions)
Frente 70: ShadowHeliodonEngine (SUShadowInfoRef / Sun Vector)
"""

import math
import unittest

from core.curve_engine import CurveEngine
from core.section_plane_engine import SectionPlaneEngine
from core.face_styles_engine import FaceStylesEngine, FaceRenderMode
from core.scenes_animation_engine import ScenesAnimationEngine
from core.shadow_heliodon_engine import ShadowHeliodonEngine


class TestFrentes66A70(unittest.TestCase):

    def test_frente_66_curve_engine(self):
        # 1. Teste de soldagem de arestas (weld_edges)
        edges = [
            ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
            ((2.0, 0.0, 0.0), (3.0, 0.0, 0.0)),
            ((1.0, 0.0, 0.0), (2.0, 0.0, 0.0)),
        ]
        chains = CurveEngine.weld_edges(edges)
        self.assertEqual(len(chains), 1)
        self.assertEqual(len(chains[0]), 4)
        self.assertEqual(chains[0][0], (0.0, 0.0, 0.0))
        self.assertEqual(chains[0][-1], (3.0, 0.0, 0.0))

        # 2. Teste de criação e detecção de arco analítico
        arc = CurveEngine.create_arc(
            center=(0.0, 0.0, 0.0),
            radius=5.0,
            normal=(0.0, 0.0, 1.0),
            start_angle_rad=0.0,
            end_angle_rad=math.pi,
            num_segments=16,
        )
        self.assertEqual(arc["type"], "SUArcCurveRef")
        self.assertFalse(arc["is_circle"])
        self.assertEqual(arc["num_segments"], 16)
        self.assertEqual(len(arc["vertices"]), 17)

        # Detectar se os vértices gerados formam arco analítico
        detected = CurveEngine.detect_arc([tuple(v) for v in arc["vertices"]])
        self.assertIsNotNone(detected)
        self.assertAlmostEqual(detected["radius"], 5.0, places=2)
        self.assertAlmostEqual(detected["center"][0], 0.0, places=2)
        self.assertAlmostEqual(detected["center"][1], 0.0, places=2)

    def test_frente_67_section_plane_engine(self):
        # 1. Criação e inversão de plano
        plane = SectionPlaneEngine.create_plane(
            name="Corte Transversal",
            normal=(0.0, 1.0, 0.0),
            distance=-2.0,
        )
        self.assertEqual(plane["normal"], [0.0, 1.0, 0.0])
        self.assertEqual(plane["distance"], -2.0)

        rev = SectionPlaneEngine.reverse_plane(plane)
        self.assertEqual(rev["normal"], [0.0, -1.0, 0.0])
        self.assertEqual(rev["distance"], 2.0)

        # 2. Fatiamento de um cubo 3D por um plano horizontal Z = 1.0
        # Vértices de um cubo unitário centrado em Z de 0 a 2
        verts = [
            (0.0, 0.0, 0.0), (2.0, 0.0, 0.0), (2.0, 2.0, 0.0), (0.0, 2.0, 0.0),
            (0.0, 0.0, 2.0), (2.0, 0.0, 2.0), (2.0, 2.0, 2.0), (0.0, 2.0, 2.0),
        ]
        # Faces trianguladas das paredes verticais
        faces = [
            [0, 1, 5], [0, 5, 4],  # Frente
            [1, 2, 6], [1, 6, 5],  # Direita
            [2, 3, 7], [2, 7, 6],  # Fundo
            [3, 0, 4], [3, 4, 7],  # Esquerda
        ]
        # Plano Z = 1.0 -> 0*x + 0*y + 1*z - 1.0 = 0
        slice_res = SectionPlaneEngine.slice_mesh(verts, faces, (0.0, 0.0, 1.0, -1.0))
        self.assertGreater(slice_res["total_cut_segments"], 0)
        self.assertGreaterEqual(slice_res["closed_loops_count"], 1)

    def test_frente_68_face_styles_engine(self):
        # 1. Wireframe
        wf = FaceStylesEngine.resolve_material_render_properties(FaceRenderMode.WIRE_FRAME)
        self.assertFalse(wf["visible"])
        self.assertTrue(wf["wireframe"])

        # 2. Monochrome (Front vs Back)
        mono_front = FaceStylesEngine.resolve_material_render_properties(FaceRenderMode.MONOCHROME, is_back_face=False)
        mono_back = FaceStylesEngine.resolve_material_render_properties(FaceRenderMode.MONOCHROME, is_back_face=True)
        self.assertEqual(mono_front["color"], FaceStylesEngine.DEFAULT_FRONT_COLOR)
        self.assertEqual(mono_back["color"], FaceStylesEngine.DEFAULT_BACK_COLOR)

        # 3. X-Ray
        xray = FaceStylesEngine.resolve_material_render_properties(FaceRenderMode.XRAY, material_color="#ff0000")
        self.assertTrue(xray["transparent"])
        self.assertEqual(xray["opacity"], 0.5)

        # 4. Glass Material
        glass = FaceStylesEngine.create_glass_material("Vidro Fumê", color="#34495e", opacity=0.4)
        self.assertTrue(glass["is_glass"])
        self.assertTrue(glass["three_pbr"]["transparent"])
        self.assertEqual(glass["three_pbr"]["transmission"], 0.92)

    def test_frente_69_scenes_animation_engine(self):
        # Criar 2 cenas
        s1 = ScenesAnimationEngine.create_scene(
            name="Fachada Frontal",
            eye=[0.0, -10.0, 2.0],
            target=[0.0, 0.0, 1.0],
            transition_time=1.0,
            delay_time=0.5,
        )
        s2 = ScenesAnimationEngine.create_scene(
            name="Vista Superior",
            eye=[0.0, 0.0, 15.0],
            target=[0.0, 0.0, 0.0],
            transition_time=2.0,
            delay_time=1.0,
        )
        self.assertEqual(s1["type"], "SUSceneRef")

        timeline = ScenesAnimationEngine.generate_animation_timeline([s1, s2], fps=10, loop=False)
        self.assertEqual(timeline["scenes_count"], 2)
        # Transição s1 -> s2 leva 2.0s + 1.0s delay = 3.0s total -> 30 frames a 10fps
        self.assertAlmostEqual(timeline["total_duration_sec"], 3.0, places=1)
        self.assertEqual(timeline["total_frames"], 30)
        self.assertEqual(len(timeline["keyframes"]), 1)

    def test_frente_70_shadow_heliodon_engine(self):
        # Equinócio em São Paulo às 12h00
        shadow = ShadowHeliodonEngine.calculate_shadow_info(
            year=2026,
            month=3,
            day=21,
            hour=12,
            minute=0,
            latitude=-23.55,
            longitude=-46.63,
            tz_offset=-3.0,
            light_intensity=90,
            dark_intensity=40,
        )
        self.assertEqual(shadow["type"], "SUShadowInfoRef")
        self.assertTrue(shadow["astronomy"]["is_daylight"])
        self.assertGreater(shadow["astronomy"]["solar_altitude_deg"], 50.0)
        self.assertEqual(len(shadow["sun_direction"]), 3)
        self.assertGreater(shadow["three_lighting"]["directional_light"]["intensity"], 1.0)
        self.assertTrue(shadow["three_lighting"]["directional_light"]["cast_shadow"])


if __name__ == "__main__":
    unittest.main()
