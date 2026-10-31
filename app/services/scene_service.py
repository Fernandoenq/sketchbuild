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
