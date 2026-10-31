"""
Testes de Integração e Regressão para as Frentes 31 a 35 (Zero DLL).

- Frente 31: Follow Me / Extrusão ao Longo de Caminho 3D (RMF)
- Frente 32: Ferramenta Arco e Curvas Bézier 3D (Arc Tool)
- Frente 33: Ferramenta Rotacionar com Transferidor Interativo (Rotate Tool / Rodrigues)
- Frente 34: Validador Automático de Conformidade ABNT NBR 16071 para Playgrounds
- Frente 35: Importador Nativo de Formato OBJ para .SKP (Zero DLL)
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
    FollowMeRequest,
    ArcRequest,
    RotateTransformRequest,
    ImportObjRequest,
)
from core.follow_me_engine import FollowMeEngine
from core.arc_generator import ArcGenerator
from core.transformation_engine import TransformationEngine
from core.nbr16071_auditor import NBR16071Auditor
from core.obj_to_skp_importer import ObjToSkpImporter
from core.skp_binary_writer import SkpBinaryWriter


class TestFrentes31a35(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp_dir = tempfile.gettempdir()
        self.template_path = r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates\Temp01a - Simple.skp"
        if not os.path.exists(self.template_path):
            self.template_path = os.path.abspath("app/data/autosave/a8d2085483e63d57.skp")
        self.repo = SkpEngineRepository()
        self.service = SceneService(repository=self.repo)
        self.controller = SceneController(service=self.service)

    async def test_01_frente_31_follow_me_extrusion(self):
        """Valida extrusão Follow Me ao longo de caminho 3D curvo (Frente 31)."""
        await self.controller.open_binary_scene(self.template_path)

        # Caminho curvo de corrimão ou tubo de escorregador
        path_3d = [
            [0.0, 0.0, 0.0],
            [1.0, 0.5, 0.5],
            [2.0, 1.2, 1.0],
            [3.0, 1.5, 1.5],
        ]
        req = FollowMeRequest(
            path_points=path_3d,
            profile_type="circle",
            radius=0.15,
            close_caps=True
        )
        res = await self.controller.create_follow_me_geometry(req)
        self.assertEqual(res.entity_type, "FollowMeExtrusion")
        self.assertEqual(res.path_points_count, 4)
        self.assertEqual(res.profile_points_count, 12)
        # 3 segmentos de caminho * 12 faces laterais + 2 tampas = 38 faces
        self.assertEqual(res.faces_count, 38)
        print(f"\n[Frente 31] Follow Me 3D: Caminho de 4 nós gerou tubo com {res.faces_count} faces B-Rep manifold")

    async def test_02_frente_32_arc_generator(self):
        """Valida criação analítica de arcos circulares 3D (Frente 32)."""
        await self.controller.open_binary_scene(self.template_path)

        start = [0.0, 0.0, 1.0]
        end = [2.0, 0.0, 1.0]
        sagitta = 0.40  # 40 cm de flecha

        req = ArcRequest(start=start, end=end, sagitta=sagitta, num_segments=16)
        res = await self.controller.create_arc_geometry(req)
        self.assertEqual(res.entity_type, "Arc")
        self.assertEqual(res.segments_count, 16)
        self.assertEqual(len(res.points), 17)
        self.assertAlmostEqual(res.chord_length, 2.0, places=2)
        # Raio: R = (L^2 / 8s) + (s / 2) = (4.0 / 3.2) + 0.20 = 1.25 + 0.20 = 1.45m
        self.assertAlmostEqual(res.radius, 1.45, places=2)
        print(f"[Frente 32] Arco 3D criado: Corda={res.chord_length}m, Flecha={res.sagitta}m, Raio={res.radius}m ({res.segments_count} segmentos)")

    async def test_03_frente_33_rotation_transform(self):
        """Valida rotação analítica com transferidor (Frente 33)."""
        await self.controller.open_binary_scene(self.template_path)

        # Rotação de 90 graus no plano XY em torno de (1, 1, 0)
        pivot = [1.0, 1.0, 0.0]
        axis = [0.0, 0.0, 1.0]
        p_original = (2.0, 1.0, 0.0)

        p_rotated = TransformationEngine.rotate_point(p_original, tuple(pivot), tuple(axis), 90.0)
        # O ponto (2, 1) rotacionado 90° ao redor de (1, 1) deve ir para (1, 2)
        self.assertAlmostEqual(p_rotated[0], 1.0, places=4)
        self.assertAlmostEqual(p_rotated[1], 2.0, places=4)

        # Obtém o ID da primeira instância real existente no modelo aberto
        session = SkpBinaryWriter.get_session()
        inst_keys = list(session.instances_offsets.keys()) if session else []
        target_inst_id = inst_keys[0] if inst_keys else "inst_0_Model Root"

        # Via API Controller
        req = RotateTransformRequest(
            instance_id=target_inst_id,
            pivot=pivot,
            axis=axis,
            angle_degrees=90.0
        )
        res = await self.controller.apply_rotation_transform(req)
        self.assertEqual(res.instance_id, target_inst_id)
        self.assertEqual(res.angle_degrees, 90.0)
        self.assertEqual(len(res.transform_matrix_16), 16)
        print(f"[Frente 33] Rotate Tool (Transferidor): Rotação analítica de 90° aplicada com matriz 4x4")

    async def test_04_frente_34_safety_audit_nbr16071(self):
        """Valida auditoria automática de segurança de playgrounds NBR 16071 (Frente 34)."""
        await self.controller.open_binary_scene(self.template_path)

        audit_res = await self.controller.audit_nbr16071_safety()
        self.assertTrue(audit_res.compliant)
        self.assertEqual(audit_res.standard, "ABNT NBR 16071:2021")
        self.assertGreaterEqual(audit_res.safety_score, 80)
        self.assertEqual(audit_res.total_checks, 5)
        self.assertEqual(audit_res.approved_checks, 5)
        self.assertTrue("PARKELÔ" in audit_res.safety_seal)
        print(f"[Frente 34] Auditoria NBR 16071: {audit_res.safety_seal} (Score: {audit_res.safety_score}%, {audit_res.approved_checks}/{audit_res.total_checks} conformes)")

    async def test_05_frente_35_obj_to_skp_importer(self):
        """Valida importação nativa de modelo 3D OBJ (Frente 35)."""
        await self.controller.open_binary_scene(self.template_path)

        # Cria arquivo OBJ sintético com 1 cubo (8 vértices, 6 faces)
        obj_content = (
            "# Cubo de Teste OBJ\n"
            "v 0.0 0.0 0.0\n"
            "v 1.0 0.0 0.0\n"
            "v 1.0 1.0 0.0\n"
            "v 0.0 1.0 0.0\n"
            "v 0.0 0.0 1.0\n"
            "v 1.0 0.0 1.0\n"
            "v 1.0 1.0 1.0\n"
            "v 0.0 1.0 1.0\n"
            "f 1 2 3 4\n"
            "f 5 6 7 8\n"
            "f 1 2 6 5\n"
            "f 2 3 7 6\n"
            "f 3 4 8 7\n"
            "f 4 1 5 8\n"
        )
        temp_obj_path = os.path.join(self.tmp_dir, "test_cube.obj")
        with open(temp_obj_path, "w", encoding="utf-8") as f:
            f.write(obj_content)

        try:
            req = ImportObjRequest(file_path=temp_obj_path, scale=1.0)
            res = await self.controller.import_obj_geometry(req)
            self.assertTrue(res.success)
            self.assertEqual(res.imported_vertices, 8)
            self.assertEqual(res.imported_faces, 6)
            print(f"[Frente 35] Importador OBJ: {res.imported_vertices} vértices e {res.imported_faces} faces importados com sucesso para o .SKP")
        finally:
            if os.path.exists(temp_obj_path):
                os.remove(temp_obj_path)


if __name__ == "__main__":
    unittest.main()
