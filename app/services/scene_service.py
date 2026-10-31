"""
Regra de negocio do modulo de cena/visualizador. Nunca fala com
`ctypes`/`core.*` diretamente -- sempre via SkpEngineRepository.
Validacoes de dominio (caminho valido, arquivo existe) vivem aqui,
mesmo padrao do ModelService (ver app/services/model_service.py).

O metodo do repository e sincrono (chamada ctypes bloqueante contra a
SketchUpAPI.dll). Como o FastAPI roda isso dentro de um event loop
async, despachamos pra uma threadpool (`run_in_threadpool`) pra nao
bloquear o loop enquanto a DLL parseia o .skp.
"""

from __future__ import annotations

import os

from starlette.concurrency import run_in_threadpool

from app.domain.exceptions import (
    InvalidModelPathError,
    ModelFileNotFoundError,
    SceneParseError,
)
from app.repositories.skp_engine_repository import SkpEngineRepository
from core.skp_binary_reader import SkpBinaryReader
from urllib.parse import quote

VALID_MODEL_EXTENSION = ".skp"

TEMPLATES_DIR = (
    r"C:\Program Files\SketchUp\SketchUp 2026\SketchUp\resources\pt-br\Templates"
)

# Templates reais da Trimble usados pela secao "Criar novo modelo" da
# Pagina Inicial (ver frontend/index.html). A unidade de cada arquivo foi
# confirmada EMPIRICAMENTE via SUModelGetUnits (nao adivinhada pelo nome
# do arquivo) -- ver REVERSE_ENGINEERING_NOTES.md secao 24.
TEMPLATES: dict[str, str] = {
    "simple_meters": "Temp01b - Simple.skp",
    "simple_inches": "Temp01a - Simple.skp",
    "visualization_inches": "Temp02a - Vis.skp",
    "visualization_millimeters": "Temp02b - Vis.skp",
    "architectural_inches": "Temp03a - Arch.skp",
    "architectural_millimeters": "Temp03b - Arch.skp",
}


class SceneService:
    def __init__(self, repository: SkpEngineRepository | None = None):
        self._repository = repository or SkpEngineRepository()

    async def open_scene(self, file_path: str) -> dict:
        self._validate_model_path(file_path)
        return await run_in_threadpool(self._repository.open, file_path)

    async def open_binary_scene(self, file_path: str) -> dict:
        """Abre um arquivo .skp diretamente via SkpBinaryReader (Pure Python / Zero DLL),
        extraindo topologia, normais, UVs analíticas, materiais PBR e hierarquia de instâncias,
        e inicializa a sessão de gravação nativa (SkpBinaryWriter)."""
        self._validate_model_path(file_path)
        from core.skp_binary_writer import SkpBinaryWriter
        await run_in_threadpool(SkpBinaryWriter.open_session, file_path)
        return await run_in_threadpool(self._extract_binary_scene, file_path)

    def _extract_binary_scene(self, file_path: str) -> dict:
        mesh = SkpBinaryReader.extract_mesh(file_path)
        if not mesh:
            raise SceneParseError(f"falha ao decodificar a malha nativa de {file_path}")

        # Vértices em polegadas para que sceneBuilder.js (INCHES_TO_METERS = 0.0254) escale exatamente para metros
        verts_in = [v / 2.54 for v in mesh["vertices"]]

        hierarchy = mesh.get("hierarchy") or {}
        model_attrs = hierarchy.get("model_attributes") or {}

        root_def = {
            "definition_id": "def_root",
            "name": "Model Root",
            "vertices": verts_in,
            "normals": mesh["normals"],
            "indices": mesh["indices"],
            "uvs": mesh["uvs"],
            "face_materials": mesh["face_materials"],
            "face_ranges": mesh.get("face_ranges", []),
            "always_faces_camera": False,
            "attributes": model_attrs,
        }

        definitions = [root_def]
        instances = []

        if hierarchy.get("instances"):
            for idx, inst in enumerate(hierarchy["instances"]):
                inst_id = f"inst_{idx}_{inst['definition_name']}"
                m_in = inst.get("matrix_4x4_inches") or inst.get("matrix_4x4")
                instances.append({
                    "instance_id": inst_id,
                    "definition_id": "def_root",
                    "transform": m_in,
                    "parent_instance_id": "inst_root",
                    "tag": None,
                    "attributes": inst.get("attributes") or {},
                })

        instances.insert(0, {
            "instance_id": "inst_root",
            "definition_id": "def_root",
            "transform": [
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            ],
            "parent_instance_id": None,
            "tag": None,
            "attributes": model_attrs,
        })

        materials_dict = {}
        for mname, mdata in mesh["materials"].items():
            tex_url = None
            if mdata["hasTexture"] and mdata["texturePath"]:
                tex_url = f"/api/v1/scene/texture?path={quote(file_path)}&texture_path={quote(mdata['texturePath'])}"

            materials_dict[mname] = {
                "name": mname,
                "color": mdata["color"],
                "opacity": mdata["opacity"],
                "has_texture": mdata["hasTexture"],
                "texture_url": tex_url,
                "metalness": mdata["metalness"],
                "roughness": mdata["roughness"],
                "attributes": mdata.get("attributes") or {},
            }

        # Câmera Real 3D (Frente 7): decodificada diretamente do model.dat via Tag 0x34bd..0x34c6
        real_cam = mesh.get("camera")
        if real_cam:
            camera = {
                "eye": real_cam["eye_inches"],
                "target": real_cam["target_inches"],
                "up": real_cam["up"],
                "perspective": real_cam["is_perspective"],
                "fov_deg": real_cam["fov_degrees"],
                "fov_is_height": real_cam["fov_is_height"],
            }
        else:
            b = mesh["bounds"]
            min_in = [p / 2.54 for p in b["min_pt_cm"]]
            max_in = [p / 2.54 for p in b["max_pt_cm"]]
            cx = (min_in[0] + max_in[0]) / 2.0
            cy = (min_in[1] + max_in[1]) / 2.0
            cz = (min_in[2] + max_in[2]) / 2.0
            diag = ((max_in[0] - min_in[0])**2 + (max_in[1] - min_in[1])**2 + (max_in[2] - min_in[2])**2)**0.5
            dist = max(diag * 1.5, 50.0)

            camera = {
                "eye": [round(cx + dist * 0.7, 3), round(cy - dist * 0.7, 3), round(cz + dist * 0.5, 3)],
                "target": [round(cx, 3), round(cy, 3), round(cz, 3)],
                "up": [0.0, 0.0, 1.0],
                "perspective": True,
                "fov_deg": 35.0,
                "fov_is_height": True,
            }

        tags_dto = mesh.get("tags") or []
        scenes_dto = mesh.get("scenes") or []

        return {
            "model_path": file_path,
            "definitions": definitions,
            "instances": instances,
            "materials": materials_dict,
            "camera": camera,
            "tags": tags_dto,
            "scenes": scenes_dto,
            "reader_mode": "binary_native",
            "model_attributes": model_attrs,
        }

    async def get_attributes(self, file_path: str) -> dict:
        """Extrai todos os dicionários de atributos de um .skp em milissegundos via Pure Python."""
        self._validate_model_path(file_path)
        attrs = await run_in_threadpool(SkpBinaryReader.extract_attributes, file_path)
        if not attrs:
            raise SceneParseError(f"falha ao extrair atributos de {file_path}")
        return attrs

    async def new_scene_from_template(self, template_id: str) -> dict:
        filename = TEMPLATES.get(template_id)
        if filename is None:
            raise InvalidModelPathError(f"template desconhecido: {template_id!r}")

        template_path = os.path.join(TEMPLATES_DIR, filename)
        if not os.path.exists(template_path):
            raise ModelFileNotFoundError(
                f"arquivo de template nao encontrado: {template_path}"
            )

        return await run_in_threadpool(
            self._repository.open_new_from_template, template_path
        )

    async def open_uploaded_scene(self, data: bytes) -> dict:
        if not data:
            raise InvalidModelPathError("arquivo enviado esta vazio")
        return await run_in_threadpool(self._repository.open_from_upload, data)

    async def update_instance_transform(
        self, instance_id: str, transform: list[float]
    ) -> None:
        await run_in_threadpool(
            self._repository.set_instance_transform, instance_id, transform
        )

    async def save_scene(self, path: str | None, overwrite_confirmed: bool = False) -> str:
        return await run_in_threadpool(self._repository.save, path, overwrite_confirmed)

    async def duplicate_instance(
        self,
        instance_id: str,
        transform: list[float] | None = None,
        offset_delta_cm: list[float] | None = None,
    ) -> dict:
        return await run_in_threadpool(
            self._repository.duplicate_instance, instance_id, transform, offset_delta_cm
        )

    async def delete_instance(self, instance_id: str) -> None:
        await run_in_threadpool(self._repository.delete_instance, instance_id)

    async def export_model_obj(self, path: str) -> str:
        self._validate_export_path(path)
        return await run_in_threadpool(self._repository.export_obj, path)

    async def add_rectangle(
        self, width_m: float, height_m: float, as_group: bool = False
    ) -> dict:
        self._validate_rectangle_dimensions(width_m, height_m)
        return await run_in_threadpool(
            self._repository.add_rectangle, width_m, height_m, as_group
        )

    async def paint_instance(self, instance_id: str, r: int, g: int, b: int) -> None:
        self._validate_rgb(r, g, b)
        await run_in_threadpool(self._repository.paint_instance, instance_id, r, g, b)

    async def tag_instance(self, instance_id: str, tag_name: str) -> None:
        self._validate_tag_name(tag_name)
        await run_in_threadpool(self._repository.tag_instance, instance_id, tag_name)

    async def paint_face(self, face_id: str, r: int, g: int, b: int) -> None:
        self._validate_rgb(r, g, b)
        await run_in_threadpool(self._repository.paint_face, face_id, r, g, b)

    async def list_scenes(self) -> list[dict]:
        from core.skp_binary_writer import SkpBinaryWriter
        session = SkpBinaryWriter.get_session()
        if session and session.scenes:
            return session.scenes
        return await run_in_threadpool(self._repository.list_scenes)

    async def list_tags(self) -> list[dict]:
        from core.skp_binary_writer import SkpBinaryWriter
        session = SkpBinaryWriter.get_session()
        if session and session.tags_offsets:
            tags = []
            for tname, vis_offset in session.tags_offsets.items():
                vis = (session.model_bytes[vis_offset] == 0)
                tags.append({
                    "name": tname,
                    "visible": vis,
                    "is_default": (tname in ("Layer0", "Sem etiquetas")),
                })
            return tags
        return await run_in_threadpool(self._repository.list_tags)

    async def set_tag_visibility(self, tag_name: str, visible: bool) -> dict:
        from core.skp_binary_writer import SkpBinaryWriter
        session = SkpBinaryWriter.get_session()
        if session and tag_name in session.tags_offsets:
            SkpBinaryWriter.set_tag_visibility(tag_name, visible)
            return {"name": tag_name, "visible": visible}
        return await run_in_threadpool(self._repository.set_tag_visibility, tag_name, visible)

    async def update_camera(
        self,
        eye: list[float],
        target: list[float],
        up: list[float] | None = None,
        fov_deg: float | None = None,
    ) -> None:
        from core.skp_binary_writer import SkpBinaryWriter
        session = SkpBinaryWriter.get_session()
        if session and session.camera_offset is not None:
            SkpBinaryWriter.set_camera(eye, target, up, fov_deg, in_inches=True)

    async def create_scene(self, name: str) -> dict:
        self._validate_scene_name(name)
        return await run_in_threadpool(self._repository.create_scene, name)

    async def activate_scene(self, scene_id: str) -> None:
        from core.skp_binary_writer import SkpBinaryWriter
        session = SkpBinaryWriter.get_session()
        if session and session.scenes:
            SkpBinaryWriter.activate_scene(scene_id)
            return
        await run_in_threadpool(self._repository.activate_scene, scene_id)

    async def get_current_session(self) -> dict | None:
        """Cobre o caso de F5 na pagina com o backend ainda rodando --
        ver app/repositories/skp_engine_repository.py
        get_current_session(). None quando nao ha sessao aberta."""
        return await run_in_threadpool(self._repository.get_current_session)

    async def list_autosave_drafts(self) -> list[dict]:
        return await run_in_threadpool(self._repository.list_autosave_drafts)

    async def recover_autosave_draft(self, draft_id: str) -> dict:
        return await run_in_threadpool(self._repository.recover_draft, draft_id)

    async def discard_autosave_draft(self, draft_id: str) -> None:
        await run_in_threadpool(self._repository.discard_autosave_draft, draft_id)

    async def set_instance_axes(
        self,
        instance_id: str,
        origin: list[float],
        x_point: list[float],
        y_point: list[float],
    ) -> dict:
        return await run_in_threadpool(
            self._repository.set_instance_axes,
            instance_id,
            tuple(origin),
            tuple(x_point),
            tuple(y_point),
        )


    async def add_box(
        self, width_m: float, length_m: float, height_m: float, offset_xyz_cm: list[float] | None = None
    ) -> dict:
        if width_m <= 0 or length_m <= 0 or height_m <= 0:
            raise InvalidModelPathError("Dimensões do bloco devem ser positivas (width, length, height > 0)")
        return await run_in_threadpool(self._repository.add_box, width_m, length_m, height_m, offset_xyz_cm)

    async def set_rendering_style(
        self,
        mode: str = "textured",
        xray: bool = False,
        profiles_width: int = 2,
        background_rgb: list[int] | None = None,
        sky_rgb: list[int] | None = None,
    ) -> dict:
        return await run_in_threadpool(
            self._repository.set_rendering_style,
            mode=mode,
            xray=xray,
            profiles_width=profiles_width,
            background_rgb=background_rgb,
            sky_rgb=sky_rgb,
        )

    async def get_assembly_tree(self) -> dict:
        return await run_in_threadpool(self._repository.get_assembly_tree)

    async def convert_dxf(self, dxf_path: str, scale_factor: float = 1.0) -> dict:
        if not dxf_path or not dxf_path.lower().endswith(".dxf"):
            raise InvalidModelPathError("Arquivo deve possuir extensão .dxf")
        return await run_in_threadpool(self._repository.convert_dxf, dxf_path, scale_factor)

    async def calculate_bim_bom(self) -> dict:
        return await run_in_threadpool(self._repository.calculate_bim_bom)

    async def calculate_exploded_view(self, expansion_factor: float = 0.5) -> dict:
        if expansion_factor < 0.0:
            raise InvalidModelPathError("Fator de expansão deve ser >= 0")
        return await run_in_threadpool(self._repository.calculate_exploded_view, expansion_factor)

    async def export_model_glb(self, file_path: str) -> dict:
        if not file_path or not file_path.strip() or not file_path.lower().endswith(".glb"):
            raise InvalidModelPathError(f"Caminho de exportação deve apontar para um arquivo .glb (recebido: {file_path!r})")
        return await run_in_threadpool(self._repository.export_glb, file_path)

    async def export_model_ifc(self, file_path: str, project_name: str = "Projeto SketchBuild") -> dict:
        if not file_path or not file_path.strip() or not file_path.lower().endswith(".ifc"):
            raise InvalidModelPathError(f"Caminho de exportação deve apontar para um arquivo .ifc (recebido: {file_path!r})")
        return await run_in_threadpool(self._repository.export_ifc, file_path, project_name)

    async def add_line_geometry(self, start_m: list[float], end_m: list[float]) -> dict:
        return await run_in_threadpool(self._repository.add_line_geometry, start_m, end_m)

    async def add_face_geometry(self, points_m: list[list[float]]) -> dict:
        if len(points_m) < 3:
            raise InvalidModelPathError("Face requer pelo menos 3 pontos coplanares.")
        return await run_in_threadpool(self._repository.add_face_geometry, points_m)

    # -- validacoes de dominio ------------------------------------------------

    def _validate_model_path(self, file_path: str) -> None:
        if not file_path or not file_path.strip():
            raise InvalidModelPathError("caminho do modelo nao pode ser vazio")

        if not file_path.lower().endswith(VALID_MODEL_EXTENSION):
            raise InvalidModelPathError(
                f"caminho deve apontar para um arquivo {VALID_MODEL_EXTENSION} "
                f"(recebido: {file_path!r})"
            )

        if not os.path.exists(file_path):
            raise ModelFileNotFoundError(f"arquivo nao encontrado: {file_path}")

    def _validate_export_path(self, file_path: str) -> None:
        if not file_path or not file_path.strip():
            raise InvalidModelPathError("caminho de exportacao nao pode ser vazio")
        if not file_path.lower().endswith(".obj"):
            raise InvalidModelPathError(
                f"caminho deve apontar para um arquivo .obj (recebido: {file_path!r})"
            )

    def _validate_rectangle_dimensions(self, width_m: float, height_m: float) -> None:
        if width_m <= 0 or height_m <= 0:
            raise InvalidModelPathError(
                f"largura/profundidade do retângulo devem ser positivas (recebido: {width_m}x{height_m})"
            )

    def _validate_rgb(self, r: int, g: int, b: int) -> None:
        if not all(0 <= c <= 255 for c in (r, g, b)):
            raise InvalidModelPathError(
                f"componentes de cor devem estar entre 0 e 255 (recebido: {r},{g},{b})"
            )

    def _validate_tag_name(self, tag_name: str) -> None:
        if not tag_name or not tag_name.strip():
            raise InvalidModelPathError("nome da etiqueta nao pode ser vazio")

    def _validate_scene_name(self, name: str) -> None:
        if not name or not name.strip():
            raise InvalidModelPathError("nome da cena nao pode ser vazio")

    async def export_cutlist_xlsx(self, file_path: str) -> dict:
        """Exporta lista de corte e orçamento em Excel .xlsx (Frente 23)."""
        return await run_in_threadpool(self._repository.export_cutlist_xlsx, file_path)

    async def add_circle_geometry(self, radius_m: float, center_xyz_m: list, num_segments: int = 24) -> dict:
        """Cria círculo plano B-Rep (Frente 14)."""
        return await run_in_threadpool(self._repository.add_circle_geometry, radius_m, center_xyz_m, num_segments)

    async def add_cylinder_geometry(self, radius_m: float, height_m: float, center_xyz_m: list, num_segments: int = 16) -> dict:
        """Cria cilindro manifold paramétrico (Frente 14)."""
        return await run_in_threadpool(self._repository.add_cylinder_geometry, radius_m, height_m, center_xyz_m, num_segments)

    async def extrude_face_geometry(self, points_m: list, distance_m: float, normal: list | None = None) -> dict:
        """Extrude face coplanar para sólido 3D Push/Pull (Frente 24)."""
        return await run_in_threadpool(self._repository.extrude_face_geometry, points_m, distance_m, normal)

    async def get_assembly_steps(self) -> dict:
        """Calcula etapas sequenciais de montagem (Frente 26)."""
        return await run_in_threadpool(self._repository.get_assembly_steps)

    async def export_assembly_manual(self, project_name: str = "Playground Parkelô", path: str | None = None) -> dict:
        """Gera manual de montagem em HTML (Frente 26)."""
        return await run_in_threadpool(self._repository.export_assembly_manual, project_name, path)

    async def export_drawing_2d(self, file_path: str, view_type: str = "top", title: str = "Prancha Técnica", scale: str = "1:50") -> dict:
        """Exporta desenho técnico 2D vetorial em SVG (Frente 27)."""
        return await run_in_threadpool(self._repository.export_drawing_2d, file_path, view_type, title, scale)

    async def calculate_solar_study(self, day_of_year: int = 80, hour: float = 14.0, latitude: float = -23.5505, longitude: float = -46.6333) -> dict:
        """Calcula estudo solar e insolação NBR 16071 (Frente 28)."""
        return await run_in_threadpool(self._repository.calculate_solar_study, day_of_year, hour, latitude, longitude)

    async def add_section_plane(self, plane_abcd: list[float], name: str = "Corte A-A", symbol: str = "A1") -> dict:
        """Adiciona um Plano de Corte de Seção (Frente 17)."""
        return await run_in_threadpool(self._repository.add_section_plane, plane_abcd, name, symbol)

    async def get_section_planes(self) -> list[dict]:
        """Retorna os Planos de Seção da cena (Frente 17)."""
        return await run_in_threadpool(self._repository.get_section_planes)

    async def add_guide_line(self, start: list[float], end: list[float], is_infinite: bool = False) -> dict:
        """Adiciona uma Linha de Guia / Trena (Frente 18)."""
        return await run_in_threadpool(self._repository.add_guide_line, start, end, is_infinite)

    async def add_guide_point(self, position: list[float]) -> dict:
        """Adiciona um Ponto de Construção (Frente 18)."""
        return await run_in_threadpool(self._repository.add_guide_point, position)

    async def get_guides(self) -> dict:
        """Retorna todas as guias e pontos de construção da cena (Frente 18)."""
        return await run_in_threadpool(self._repository.get_guides)

    async def apply_boolean_operation(self, operation: str, main_shape: dict, tool_shape: dict) -> dict:
        """Aplica operação booleana sólida CSG (Frente 25)."""
        return await run_in_threadpool(self._repository.apply_boolean_operation, operation, main_shape, tool_shape)

    async def add_offset_face(self, points: list[list[float]], distance: float, inside: bool = True, create_frame: bool = False) -> dict:
        """Gera face ou moldura equidistante via Offset (Frente 30)."""
        return await run_in_threadpool(self._repository.add_offset_face, points, distance, inside, create_frame)

    async def export_executive_pdf(self, project_name: str, author: str, client_name: str, output_path: str) -> dict:
        """Exporta Proposta Executiva e Prancha Técnica em PDF Nativo (Frente 29)."""
        return await run_in_threadpool(self._repository.export_executive_pdf, project_name, author, client_name, output_path)

    async def create_follow_me_geometry(self, path_points: list, profile_type: str = "circle", radius: float = 0.10, profile_points: list | None = None, close_caps: bool = True) -> dict:
        """Gera sólido extrudado ao longo de caminho 3D Follow Me (Frente 31)."""
        return await run_in_threadpool(self._repository.create_follow_me_geometry, path_points, profile_type, radius, profile_points, close_caps)

    async def create_arc_geometry(self, start: list, end: list, sagitta: float = 0.30, num_segments: int = 12) -> dict:
        """Gera arco circular 3D paramétrico (Frente 32)."""
        return await run_in_threadpool(self._repository.create_arc_geometry, start, end, sagitta, num_segments)

    async def apply_rotation_transform(self, instance_id: str, pivot: list, axis: list, angle_degrees: float) -> dict:
        """Aplica rotação analítica com transferidor (Frente 33)."""
        return await run_in_threadpool(self._repository.apply_rotation_transform, instance_id, pivot, axis, angle_degrees)

    async def audit_nbr16071_safety(self) -> dict:
        """Audita conformidade normativa de segurança infantil NBR 16071 (Frente 34)."""
        return await run_in_threadpool(self._repository.audit_nbr16071_safety)

    async def import_obj_geometry(self, file_path: str, scale: float = 1.0) -> dict:
        """Importa arquivo Wavefront OBJ e converte para entidades B-Rep do .SKP (Frente 35)."""
        return await run_in_threadpool(self._repository.import_obj_geometry, file_path, scale)

    async def calculate_nesting_optimizer(self, demanded_pieces: list, stock_bar_length_m: float = 3.00) -> dict:
        """Calcula otimização de plano de corte de barras (Frente 36)."""
        return await run_in_threadpool(self._repository.calculate_nesting_optimizer, demanded_pieces, stock_bar_length_m)

    async def create_terrain_geometry(self, width_m: float = 10.0, length_m: float = 10.0, grid_res: float = 1.0, slope_x: float = 0.0, slope_y: float = 5.0) -> dict:
        """Gera terreno paramétrico e malha topográfica Sandbox (Frente 37)."""
        return await run_in_threadpool(self._repository.create_terrain_geometry, width_m, length_m, grid_res, slope_x, slope_y)

    async def calculate_structural_analysis(self, span_m: float, load_kn_m: float, section_type: str = "circular", diameter_m: float = 0.16, width_m: float = 0.08, height_m: float = 0.16) -> dict:
        """Calcula tensões, flecha e estabilidade de viga segundo NBR 7190 (Frente 38)."""
        return await run_in_threadpool(self._repository.calculate_structural_analysis, span_m, load_kn_m, section_type, diameter_m, width_m, height_m)

    async def apply_scale_transform(self, instance_id: str, scale_factors: list, pivot: list) -> dict:
        """Aplica escala paramétrica à instância (Frente 39)."""
        return await run_in_threadpool(self._repository.apply_scale_transform, instance_id, scale_factors, pivot)

    async def export_cam_dxf(self, parts: list, output_filename: str) -> dict:
        """Exporta contornos para máquinas CNC e Corte a Laser em DXF (Frente 40)."""
        return await run_in_threadpool(self._repository.export_cam_dxf, parts, output_filename)

    async def calculate_camera_path(self, waypoints: list, frames_per_segment: int = 24) -> dict:
        """Gera interpolação suave Catmull-Rom para sobrevoo de câmera (Frente 41)."""
        return await run_in_threadpool(self._repository.calculate_camera_path, waypoints, frames_per_segment)

    async def export_point_cloud_xyz(self, output_filename: str) -> dict:
        """Exporta nuvem de pontos 3D LiDAR em formato ASCII XYZ (Frente 42)."""
        return await run_in_threadpool(self._repository.export_point_cloud_xyz, output_filename)

    async def generate_maintenance_plan(self, installation_date: str = "2026-03-01", env_type: str = "urban") -> dict:
        """Gera plano normativo de manutenção preventiva NBR 16071-7 (Frente 43)."""
        return await run_in_threadpool(self._repository.generate_maintenance_plan, installation_date, env_type)

    async def apply_mirror_transform(self, instance_id: str, plane_normal: list, plane_point: list) -> dict:
        """Aplica espelhamento e simetria 3D de Householder (Frente 44)."""
        return await run_in_threadpool(self._repository.apply_mirror_transform, instance_id, plane_normal, plane_point)

    async def export_qr_tag_svg(self, serial_number: str, product_name: str, output_filename: str) -> dict:
        """Gera placa de identificação patrimonial com QR Code em SVG (Frente 45)."""
        return await run_in_threadpool(self._repository.export_qr_tag_svg, serial_number, product_name, output_filename)

    async def simulate_swing_kinematics(
        self,
        chain_length_m: float = 2.20,
        user_mass_kg: float = 50.0,
        initial_angle_deg: float = 45.0,
        seat_height_at_rest_m: float = 0.45,
        damping_ratio: float = 0.05,
        total_time_s: float = 4.0,
        fps: int = 24
    ) -> dict:
        """Simula cinemática, tração e envelope de segurança de balanço NBR 16071 (Frente 46)."""
        return await run_in_threadpool(
            self._repository.simulate_swing_kinematics,
            chain_length_m,
            user_mass_kg,
            initial_angle_deg,
            seat_height_at_rest_m,
            damping_ratio,
            total_time_s,
            fps
        )

    async def generate_art_pdf(
        self,
        professional_name: str,
        crea_cau: str,
        rnp: str,
        contractor: str,
        location: str,
        project_name: str,
        output_filename: str
    ) -> dict:
        """Gera minuta de ART / RRT em formato PDF vetorial (Frente 47)."""
        return await run_in_threadpool(
            self._repository.generate_art_pdf,
            professional_name,
            crea_cau,
            rnp,
            contractor,
            location,
            project_name,
            output_filename
        )

    async def inspect_wall_thickness(self, min_thickness_mm: float = 6.0, max_thickness_mm: float = 14.0) -> dict:
        """Inspeciona espessura de paredes de peças rotomoldadas (Frente 48)."""
        return await run_in_threadpool(self._repository.inspect_wall_thickness, min_thickness_mm, max_thickness_mm)

    async def optimize_cargo_load(self, packages: list, vehicle_type: str = "caminhao_truck") -> dict:
        """Otimiza a cubagem e alocação 3D de volumes no transporte (Frente 49)."""
        return await run_in_threadpool(self._repository.optimize_cargo_load, packages, vehicle_type)

    async def generate_technical_sketch(
        self,
        dihedral_angle_threshold_deg: float = 25.0,
        overshoot_mm: float = 8.0,
        output_filename: str = "esboco_tecnico_arquitetura.svg"
    ) -> dict:
        """Gera prancha em SVG com traço arquitetônico estilizado e overshoot (Frente 50)."""
        return await run_in_threadpool(
            self._repository.generate_technical_sketch,
            dihedral_angle_threshold_deg,
            overshoot_mm,
            output_filename
        )

    async def generate_spiral_tube(
        self,
        radius_m: float = 1.20,
        height_m: float = 2.40,
        turns: float = 1.25,
        tube_radius_m: float = 0.38,
        segments_per_turn: int = 16,
        tube_segments: int = 8,
        is_open_gutter: bool = False
    ) -> dict:
        """Gera geometria 3D de tobogã espiral helicoidal (Frente 51)."""
        return await run_in_threadpool(
            self._repository.generate_spiral_tube,
            radius_m,
            height_m,
            turns,
            tube_radius_m,
            segments_per_turn,
            tube_segments,
            is_open_gutter
        )

    async def calculate_overturn_stability(
        self,
        total_mass_kg: float = 850.0,
        cg_position: list = None,
        base_support_points: list = None,
        wind_speed_km_h: float = 100.0,
        exposed_frontal_area_m2: float = 6.50,
        lateral_live_load_n: float = 500.0,
        live_load_height_m: float = 1.80
    ) -> dict:
        """Calcula estabilidade ao tombamento sob vento e empuxo (Frente 52)."""
        return await run_in_threadpool(
            self._repository.calculate_overturn_stability,
            total_mass_kg,
            cg_position,
            base_support_points,
            wind_speed_km_h,
            exposed_frontal_area_m2,
            lateral_live_load_n,
            live_load_height_m
        )

    async def export_field_inspection_html(
        self,
        park_name: str,
        inspector_name: str,
        inspection_date: str,
        equipment_list: list = None,
        output_filename: str = "ficha_inspecao_nbr16071.html"
    ) -> dict:
        """Exporta checklist de inspeção de campo NBR 16071-7 em HTML5 offline (Frente 53)."""
        return await run_in_threadpool(
            self._repository.export_field_inspection_html,
            park_name,
            inspector_name,
            inspection_date,
            equipment_list,
            output_filename
        )

    async def calculate_angle_dimension(
        self,
        vertex_point: list,
        point_a: list,
        point_b: list,
        arc_radius_m: float = 0.60
    ) -> dict:
        """Calcula cota angular e arco gráfico 3D entre 3 pontos (Frente 54)."""
        return await run_in_threadpool(
            self._repository.calculate_angle_dimension,
            vertex_point,
            point_a,
            point_b,
            arc_radius_m
        )

    async def calculate_fastener_torque(
        self,
        timber_thickness_mm: float = 160.0,
        steel_plate_thickness_mm: float = 4.75,
        bolt_standard: str = "1/2_POL",
        material_grade: str = "Inox_304",
        friction_factor_k: float = 0.18
    ) -> dict:
        """Dimensiona fixador e calcula torque normativo NBR 7190 / ISO 898 (Frente 55)."""
        return await run_in_threadpool(
            self._repository.calculate_fastener_torque,
            timber_thickness_mm,
            steel_plate_thickness_mm,
            bolt_standard,
            material_grade,
            friction_factor_k
        )

    async def generate_hip_roof(
        self,
        base_width_m: float = 2.40,
        base_length_m: float = 3.20,
        base_height_m: float = 2.80,
        pitch_deg: float = 30.0,
        overhang_m: float = 0.35
    ) -> dict:
        """Gera geometria 3D de telhado de 4 águas ou piramidal (Frente 56)."""
        return await run_in_threadpool(
            self._repository.generate_hip_roof,
            base_width_m,
            base_length_m,
            base_height_m,
            pitch_deg,
            overhang_m
        )

    async def simulate_hic_impact(
        self,
        fall_height_m: float = 1.80,
        surface_type: str = "areia_lavada",
        installed_thickness_mm: float = 300.0
    ) -> dict:
        """Simula impacto HIC e piso amortecedor NBR 16071-3 (Frente 57)."""
        return await run_in_threadpool(
            self._repository.simulate_hic_impact,
            fall_height_m,
            surface_type,
            installed_thickness_mm
        )

    async def export_zebra_label(
        self,
        part_name: str,
        part_sku: str,
        dimensions_mm: str,
        lot_batch: str,
        output_zpl_filename: str = "etiqueta_zebra.zpl",
        output_svg_filename: str = "etiqueta_zebra.svg"
    ) -> dict:
        """Exporta etiqueta térmica industrial Zebra ZPL II e SVG (Frente 58)."""
        return await run_in_threadpool(
            self._repository.export_zebra_label,
            part_name,
            part_sku,
            dimensions_mm,
            lot_batch,
            output_zpl_filename,
            output_svg_filename
        )

    async def calculate_exploded_trails(
        self,
        parts: list,
        dash_size_m: float = 0.05,
        gap_size_m: float = 0.03
    ) -> dict:
        """Calcula linhas tracejadas de trajetória para vista explodida (Frente 59)."""
        return await run_in_threadpool(
            self._repository.calculate_exploded_trails,
            parts,
            dash_size_m,
            gap_size_m
        )

    async def calculate_carbon_footprint(
        self,
        timber_volume_m3: float = 2.80,
        steel_weight_kg: float = 95.0,
        plastic_weight_kg: float = 45.0,
        transport_distance_km: float = 350.0
    ) -> dict:
        """Calcula balanço de carbono e sustentabilidade florestal (Frente 60)."""
        return await run_in_threadpool(
            self._repository.calculate_carbon_footprint,
            timber_volume_m3,
            steel_weight_kg,
            plastic_weight_kg,
            transport_distance_km
        )

    async def manage_attribute_dictionary(
        self,
        dict_name: str = "dynamic_attributes",
        key: str = "_lenx_formula",
        value: Any = "=100 * 2",
        evaluate_formula: bool = False,
        context_vars: dict = None
    ) -> dict:
        """Manipula dicionários de atributos nativos e componentes dinâmicos (Frente 61)."""
        return await run_in_threadpool(
            self._repository.manage_attribute_dictionary,
            dict_name,
            key,
            value,
            evaluate_formula,
            context_vars
        )

    async def manage_tag_folder(
        self,
        folder_id: str,
        name: str,
        parent_id: str | None = None,
        visible: bool = True,
        tags_to_add: list = None
    ) -> dict:
        """Cria e gerencia pastas de tags hierárquicas (Frente 62)."""
        return await run_in_threadpool(
            self._repository.manage_tag_folder,
            folder_id,
            name,
            parent_id,
            visible,
            tags_to_add
        )

    async def configure_edge_styles(self, settings: dict) -> dict:
        """Configura opções nativas de estilos de arestas do SketchUp (Frente 63)."""
        return await run_in_threadpool(self._repository.configure_edge_styles, settings)

    async def calculate_two_point_perspective(
        self,
        eye: list,
        target: list,
        fov_deg: float = 35.0,
        aspect_ratio: float = 16.0 / 9.0
    ) -> dict:
        """Calcula matriz de câmera com Perspectiva de Dois Pontos (Frente 64)."""
        return await run_in_threadpool(
            self._repository.calculate_two_point_perspective,
            eye,
            target,
            fov_deg,
            aspect_ratio
        )

    async def project_texture_uv(
        self,
        vertices: list,
        projection_type: str = "planar",
        plane_normal: list = None,
        scale_u_m: float = 1.0,
        scale_v_m: float = 1.0,
        rotation_deg: float = 0.0
    ) -> dict:
        """Calcula coordenadas UV analíticas para projeção planar ou cilíndrica (Frente 65)."""
        return await run_in_threadpool(
            self._repository.project_texture_uv,
            vertices,
            projection_type,
            plane_normal,
            scale_u_m,
            scale_v_m,
            rotation_deg
        )


    async def weld_curve_edges(self, edges: list, tolerance: float = 0.0001) -> dict:
        """Solda arestas contíguas em curvas SUCurveRef (Frente 66)."""
        return await run_in_threadpool(self._repository.weld_curve_edges, edges, tolerance)

    async def create_arc_curve(
        self,
        center: list,
        radius: float,
        normal: list,
        start_angle_rad: float = 0.0,
        end_angle_rad: float = 6.283185,
        num_segments: int = 24
    ) -> dict:
        """Cria arco analítico paramétrico SUArcCurveRef (Frente 66)."""
        return await run_in_threadpool(
            self._repository.create_arc_curve,
            center,
            radius,
            normal,
            start_angle_rad,
            end_angle_rad,
            num_segments
        )

    async def create_or_reverse_section_plane(
        self,
        name: str = "Corte Transversal",
        symbol: str = "A",
        normal: list = None,
        distance: float = 1.0,
        is_active: bool = True,
        reverse: bool = False
    ) -> dict:
        """Cria ou inverte plano de corte SUSectionPlaneRef (Frente 67)."""
        return await run_in_threadpool(
            self._repository.create_or_reverse_section_plane,
            name,
            symbol,
            normal,
            distance,
            is_active,
            reverse
        )

    async def slice_geometry_by_plane(
        self,
        vertices: list,
        faces: list,
        plane_equation: list
    ) -> dict:
        """Fatia malha 3D gerando contornos e loops de corte transversal (Frente 67)."""
        return await run_in_threadpool(
            self._repository.slice_geometry_by_plane,
            vertices,
            faces,
            plane_equation
        )

    async def resolve_face_render_style(
        self,
        mode: str = "SHADED_WITH_TEXTURES",
        material_color: str = None,
        texture_path: str = None,
        opacity: float = 1.0,
        is_back_face: bool = False
    ) -> dict:
        """Resolve shaders e propriedades PBR de estilos de faces (Frente 68)."""
        return await run_in_threadpool(
            self._repository.resolve_face_render_style,
            mode,
            material_color,
            texture_path,
            opacity,
            is_back_face
        )

    async def create_glass_pbr_material(
        self,
        name: str = "Vidro Arquitetônico Transparente",
        color: str = "#dff9fb",
        opacity: float = 0.3,
        refraction_index: float = 1.52
    ) -> dict:
        """Cria material de vidro físico PBR (Frente 68)."""
        return await run_in_threadpool(
            self._repository.create_glass_pbr_material,
            name,
            color,
            opacity,
            refraction_index
        )

    async def create_presentation_scene(
        self,
        name: str,
        eye: list,
        target: list,
        up: list = None,
        fov: float = 35.0,
        is_orthographic: bool = False,
        transition_time: float = 1.5,
        delay_time: float = 1.0,
        include_in_animation: bool = True
    ) -> dict:
        """Cria definição canônica de cena SUSceneRef (Frente 69)."""
        return await run_in_threadpool(
            self._repository.create_presentation_scene,
            name,
            eye,
            target,
            up,
            fov,
            is_orthographic,
            transition_time,
            delay_time,
            include_in_animation
        )

    async def generate_scene_animation_timeline(
        self,
        scenes: list,
        fps: int = 30,
        loop: bool = True
    ) -> dict:
        """Gera timeline contínua de transição entre cenas (Frente 69)."""
        return await run_in_threadpool(
            self._repository.generate_scene_animation_timeline,
            scenes,
            fps,
            loop
        )

    async def calculate_shadow_and_sun_info(
        self,
        year: int = 2026,
        month: int = 3,
        day: int = 21,
        hour: int = 14,
        minute: int = 0,
        latitude: float = -23.5505,
        longitude: float = -46.6333,
        tz_offset: float = -3.0,
        north_angle: float = 0.0,
        light_intensity: int = 80,
        dark_intensity: int = 45,
        display_shadows: bool = True,
        use_sun_for_shading: bool = True,
        edges_cast_shadows: bool = False
    ) -> dict:
        """Calcula parâmetros de iluminação solar e sombreamento SUShadowInfoRef (Frente 70)."""
        return await run_in_threadpool(
            self._repository.calculate_shadow_and_sun_info,
            year,
            month,
            day,
            hour,
            minute,
            latitude,
            longitude,
            tz_offset,
            north_angle,
            light_intensity,
            dark_intensity,
            display_shadows,
            use_sun_for_shading,
            edges_cast_shadows
        )


    async def create_screen_text(
        self,
        text: str,
        screen_x: float = 20.0,
        screen_y: float = 20.0,
        font_name: str = "Arial",
        font_size_pt: int = 12,
        color_hex: str = "#000000",
        bold: bool = False,
        italic: bool = False
    ) -> dict:
        """Cria anotação de texto 2D fixada em tela (Frente 71)."""
        return await run_in_threadpool(
            self._repository.create_screen_text,
            text,
            screen_x,
            screen_y,
            font_name,
            font_size_pt,
            color_hex,
            bold,
            italic
        )

    async def create_leader_text(
        self,
        text: str,
        anchor_point: list,
        offset_vector: list = None,
        arrow_type: str = "ARROW",
        font_name: str = "Arial",
        font_size_pt: int = 10,
        color_hex: str = "#000000"
    ) -> dict:
        """Cria rótulo anotativo com linha de chamada 3D (Frente 71)."""
        return await run_in_threadpool(
            self._repository.create_leader_text,
            text,
            anchor_point,
            offset_vector,
            arrow_type,
            font_name,
            font_size_pt,
            color_hex
        )

    async def create_dimension_linear(
        self,
        start_pt: list,
        end_pt: list,
        offset_distance: float = 0.2,
        plane_normal: list = None,
        arrow_type: str = "SLASH",
        unit: str = "m",
        precision: int = 2,
        custom_text: str = None
    ) -> dict:
        """Calcula cota linear com linhas de extensão e tiques arquitetônicos (Frente 72)."""
        return await run_in_threadpool(
            self._repository.create_dimension_linear,
            start_pt,
            end_pt,
            offset_distance,
            plane_normal,
            arrow_type,
            unit,
            precision,
            custom_text
        )

    async def create_guide_line_infinite(
        self,
        point: list,
        direction: list = None,
        end_point: list = None,
        is_infinite: bool = True,
        extent_m: float = 500.0
    ) -> dict:
        """Cria linha de guia infinita ou finita SUGuideLineRef (Frente 73)."""
        return await run_in_threadpool(
            self._repository.create_guide_line_infinite,
            point,
            direction,
            end_point,
            is_infinite,
            extent_m
        )

    async def create_guide_point(self, point: list) -> dict:
        """Cria ponto de construção SUGuidePointRef (Frente 73)."""
        return await run_in_threadpool(self._repository.create_guide_point, point)

    async def intersect_guide_lines(self, line1: dict, line2: dict, tolerance: float = 0.001) -> dict:
        """Calcula interseção 3D analítica entre duas linhas de guia (Frente 73)."""
        return await run_in_threadpool(self._repository.intersect_guide_lines, line1, line2, tolerance)

    async def configure_alpha_material(
        self,
        name: str,
        texture_path: str,
        alpha_mode: str = "MASK",
        alpha_threshold: float = 0.5,
        double_sided: bool = True
    ) -> dict:
        """Configura material com canal alfa e recorte de profundidade (Frente 74)."""
        return await run_in_threadpool(
            self._repository.configure_alpha_material,
            name,
            texture_path,
            alpha_mode,
            alpha_threshold,
            double_sided
        )

    async def calculate_face_me_matrix(
        self,
        instance_position: list,
        camera_position: list,
        axial_only: bool = True
    ) -> dict:
        """Calcula matriz de rotação Face-Me para componente de vegetação/figura humana (Frente 74)."""
        return await run_in_threadpool(
            self._repository.calculate_face_me_matrix,
            instance_position,
            camera_position,
            axial_only
        )

    async def resolve_nested_hierarchy_node(self, node_id: str, path_to_node: list) -> dict:
        """Resolve matriz mundial acumulada e decomposição de nó aninhado (Frente 75)."""
        return await run_in_threadpool(self._repository.resolve_nested_hierarchy_node, node_id, path_to_node)

    async def convert_world_transform_to_local(self, desired_world_matrix: list, parent_world_matrix: list) -> dict:
        """Converte matriz mundial de edição para matriz local de nó aninhado (Frente 75)."""
        return await run_in_threadpool(
            self._repository.convert_world_transform_to_local,
            desired_world_matrix,
            parent_world_matrix
        )
