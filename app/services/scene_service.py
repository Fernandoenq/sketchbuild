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

from app.domain.exceptions import InvalidModelPathError, ModelFileNotFoundError
from app.repositories.skp_engine_repository import SkpEngineRepository

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

    async def update_instance_transform(
        self, instance_id: str, transform: list[float]
    ) -> None:
        await run_in_threadpool(
            self._repository.set_instance_transform, instance_id, transform
        )

    async def save_scene(self, path: str | None) -> str:
        return await run_in_threadpool(self._repository.save, path)

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
        return await run_in_threadpool(self._repository.list_scenes)

    async def list_tags(self) -> list[dict]:
        return await run_in_threadpool(self._repository.list_tags)

    async def set_tag_visibility(self, tag_name: str, visible: bool) -> dict:
        return await run_in_threadpool(self._repository.set_tag_visibility, tag_name, visible)

    async def create_scene(self, name: str) -> dict:
        self._validate_scene_name(name)
        return await run_in_threadpool(self._repository.create_scene, name)

    async def activate_scene(self, scene_id: str) -> None:
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
