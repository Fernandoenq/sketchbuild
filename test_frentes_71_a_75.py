"""
Testes Unitários Automatizados - Frentes 71 a 75
SketchBuild - Engenharia Reversa do SketchUp (Zero DLL)
Frente 71: TextEngine (SUTextRef - ScreenText & LeaderText)
Frente 72: DimensionLinearEngine (SUDimensionLinearRef - Cotas e Witness Lines)
Frente 73: InfiniteGuideEngine (SUGuideLineRef & SUGuidePointRef - Guias Infinitas)
Frente 74: AlphaTextureEngine (Alpha Masking & Face-Me Billboard Rotation)
Frente 75: NestedInstanceHierarchyEngine (World Matrix & Aninhamento Profundo)
"""

import math
import unittest

from core.text_engine import TextEngine
from core.dimension_linear_engine import DimensionLinearEngine
from core.infinite_guide_engine import InfiniteGuideEngine
from core.alpha_texture_engine import AlphaTextureEngine
from core.nested_instance_hierarchy_engine import NestedInstanceHierarchyEngine


class TestFrentes71A75(unittest.TestCase):

    def test_frente_71_text_engine(self):
        # 1. Screen Text (HUD)
        st = TextEngine.create_screen_text("Rótulo de Projeto", screen_x=50.0, screen_y=100.0)
        self.assertEqual(st["type"], "SUTextRef")
        self.assertTrue(st["is_screen_text"])
        self.assertEqual(st["screen_position"], [50.0, 100.0])

        # 2. Leader Text (3D Anchor + Vector)
        lt = TextEngine.create_leader_text(
            "Viga Principal 20x20cm",
            anchor_point=(1.0, 2.0, 3.0),
            offset_vector=(0.5, 0.0, 0.5),
            arrow_type="ARROW",
        )
        self.assertEqual(lt["type"], "SUTextRef")
        self.assertFalse(lt["is_screen_text"])
        self.assertEqual(lt["anchor_point"], [1.0, 2.0, 3.0])
        self.assertEqual(lt["text_position_3d"], [1.5, 2.0, 3.5])
        self.assertAlmostEqual(lt["leader_length_m"], math.sqrt(0.5), places=3)

    def test_frente_72_dimension_linear_engine(self):
        # Cota de uma parede de 4.0 metros no eixo X
        dim = DimensionLinearEngine.create_dimension(
            start_pt=(0.0, 0.0, 1.0),
            end_pt=(4.0, 0.0, 1.0),
            offset_distance=0.3,
            unit="m",
            precision=2,
        )
        self.assertEqual(dim["type"], "SUDimensionLinearRef")
        self.assertAlmostEqual(dim["distance_m"], 4.0, places=3)
        self.assertEqual(dim["text"], "4.00 m")
        # Ponto médio do texto deslocado no Y
        self.assertEqual(dim["text_position"][0], 2.0)
        self.assertAlmostEqual(dim["text_position"][1], 0.3, places=3)
        self.assertEqual(len(dim["witness_lines"]), 2)
        self.assertEqual(len(dim["ticks"]), 2)

    def test_frente_73_infinite_guide_engine(self):
        # 1. Linha de Guia Infinita pelo ponto (2, 0, 0) na direção Y (0, 1, 0)
        g1 = InfiniteGuideEngine.create_guide_line(point=(2.0, 0.0, 0.0), direction=(0.0, 1.0, 0.0), is_infinite=True)
        self.assertEqual(g1["type"], "SUGuideLineRef")
        self.assertTrue(g1["is_infinite"])
        self.assertEqual(g1["length_m"], 1000.0)

        # 2. Linha de Guia pelo ponto (0, 5, 0) na direção X (1, 0, 0)
        g2 = InfiniteGuideEngine.create_guide_line(point=(0.0, 5.0, 0.0), direction=(1.0, 0.0, 0.0), is_infinite=True)

        # 3. Teste de Interseção Analítica das duas guias
        inter = InfiniteGuideEngine.intersect_guide_lines(g1, g2)
        self.assertIsNotNone(inter)
        self.assertEqual(inter["intersection_point"], [2.0, 5.0, 0.0])

        # 4. Ponto de Construção (cruz)
        gp = InfiniteGuideEngine.create_guide_point((2.0, 5.0, 0.0))
        self.assertEqual(gp["type"], "SUGuidePointRef")
        self.assertEqual(len(gp["marker_cross_lines"]), 3)

    def test_frente_74_alpha_texture_engine(self):
        # 1. Configuração de textura PNG com alphaTest (recorte de folhagem)
        mat = AlphaTextureEngine.configure_alpha_material("Folhagem Pinus", "/textures/tree_leaf.png", alpha_mode="MASK", alpha_threshold=0.5)
        self.assertEqual(mat["type"], "SUMaterialRef")
        self.assertEqual(mat["alpha_mode"], "MASK")
        self.assertTrue(mat["three_pbr"]["depthWrite"])
        self.assertEqual(mat["three_pbr"]["alphaTest"], 0.5)

        # 2. Matriz Face-Me (Billboard axial girando em torno de Z)
        billboard = AlphaTextureEngine.calculate_face_me_matrix(
            instance_position=(0.0, 0.0, 0.0),
            camera_position=(10.0, 10.0, 2.0),
            axial_only=True,
        )
        self.assertEqual(billboard["entity_type"], "FaceMeTransform")
        self.assertAlmostEqual(billboard["yaw_rotation_deg"], 45.0, places=1)
        self.assertEqual(len(billboard["matrix_4x4_column_major"]), 16)

    def test_frente_75_nested_instance_hierarchy_engine(self):
        # Teste de 3 níveis de aninhamento:
        # Nível 1: Grupo transladado em X = 10
        m1 = [1,0,0,0,  0,1,0,0,  0,0,1,0,  10,0,0,1]
        # Nível 2: Sub-componente transladado em Y = 5
        m2 = [1,0,0,0,  0,1,0,0,  0,0,1,0,  0,5,0,1]
        # Nível 3: Peça transladada em Z = 2 com escala uniforme 2.0
        m3 = [2,0,0,0,  0,2,0,0,  0,0,2,0,  0,0,2,1]

        # 1. Resolver transformação acumulada
        world_mat = NestedInstanceHierarchyEngine.calculate_world_matrix_chain([m1, m2, m3])
        decomp = NestedInstanceHierarchyEngine.decompose_matrix(world_mat)
        self.assertEqual(decomp["translation"], [10.0, 5.0, 2.0])
        self.assertEqual(decomp["scale"], [2.0, 2.0, 2.0])

        # 2. Resolução de nó com caminho completo
        path = [
            {"id": "g1", "name": "Módulo Principal", "local_matrix_16": m1},
            {"id": "c2", "name": "Montante Lateral", "local_matrix_16": m2},
            {"id": "p3", "name": "Cavilha", "local_matrix_16": m3},
        ]
        res_node = NestedInstanceHierarchyEngine.resolve_hierarchy_node("p3", path)
        self.assertEqual(res_node["depth_level"], 3)
        self.assertEqual(res_node["decomposition"]["translation"], [10.0, 5.0, 2.0])

        # 3. Conversão de edição no espaço mundial para matriz local
        # Se quisermos mover a peça para a posição mundial (20, 15, 6)
        desired_world = [2,0,0,0,  0,2,0,0,  0,0,2,0,  20,15,6,1]
        parent_world = [1,0,0,0,  0,1,0,0,  0,0,1,0,  10,5,0,1]  # m1 x m2
        local_calc = NestedInstanceHierarchyEngine.convert_world_transform_to_local(desired_world, parent_world)
        self.assertEqual(local_calc[12], 10.0)  # 20 - 10
        self.assertEqual(local_calc[13], 10.0)  # 15 - 5
        self.assertEqual(local_calc[14], 6.0)   # 6 - 0


if __name__ == "__main__":
    unittest.main()
