"""
Controller do modulo de cena/visualizador: orquestra o service e
traduz excecoes de dominio para HTTPException. Nenhuma regra de
negocio mora aqui.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status

from app.domain.exceptions import (
    InvalidModelPathError,
    ModelFileNotFoundError,
    SceneParseError,
    SceneSessionError,
)
from app.schemas.scene import (
    ActivateScenePageResponse,
    AddRectangleResponse,
    AutosaveDraftDTO,
    CreateScenePageResponse,
    DeleteInstanceResponse,
    DiscardAutosaveDraftResponse,
    ExportModelResponse,
    ListAutosaveDraftsResponse,
    ListScenePagesResponse,
    PaintFaceResponse,
    PaintInstanceResponse,
    SaveSceneResponse,
    SceneResponse,
    ScenePageDTO,
    SetInstanceAxesResponse,
    SetTagVisibilityResponse,
    TagDTO,
    TagInstanceResponse,
    ListTagsResponse,
    UpdateTransformResponse,
)
from app.services.recent_files_service import RecentFilesService
from app.services.scene_service import SceneService

logger = logging.getLogger("sketchbuild")


class SceneController:
    def __init__(
        self,
        service: SceneService | None = None,
        recent_files_service: RecentFilesService | None = None,
    ):
        self._service = service or SceneService()
        self._recent_files_service = recent_files_service or RecentFilesService()

    async def open_scene(self, file_path: str) -> SceneResponse:
        try:
            result = await self._service.open_scene(file_path)
        except (InvalidModelPathError, ModelFileNotFoundError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        try:
            await self._recent_files_service.register_opened(file_path)
        except OSError:
            # "Arquivos recentes" e um nice-to-have da Pagina Inicial --
            # uma falha ao gravar o JSON local nunca pode derrubar a
            # abertura do modelo em si.
            logger.warning("Falha ao registrar arquivo recente: %s", file_path)

        return SceneResponse.model_validate(result)

    async def new_scene_from_template(self, template_id: str) -> SceneResponse:
        """Cria um modelo novo a partir de um template real da Trimble --
        NAO registra em "Arquivos recentes": como `model_path` fica None
        (sem arquivo no disco ainda), nao ha caminho real pra gravar lá."""
        try:
            result = await self._service.new_scene_from_template(template_id)
        except (InvalidModelPathError, ModelFileNotFoundError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        return SceneResponse.model_validate(result)

    async def get_current_session(self) -> SceneResponse:
        """Cobre o F5 na pagina (ver REVERSE_ENGINEERING_NOTES.md nao se
        aplica -- isto nao e engenharia reversa, e persistencia de sessao
        no app em si, ver README.md "Persistencia de sessao"). 409 quando
        o backend nao tem nenhuma sessao aberta no momento (acabou de
        reiniciar, ou ninguem abriu nada ainda nesta execucao)."""
        result = await self._service.get_current_session()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="nenhuma sessao aberta nesta execucao do backend",
            )
        return SceneResponse.model_validate(result)

    async def list_autosave_drafts(self) -> ListAutosaveDraftsResponse:
        drafts = await self._service.list_autosave_drafts()
        return ListAutosaveDraftsResponse(
            drafts=[AutosaveDraftDTO.model_validate(d) for d in drafts]
        )

    async def recover_autosave_draft(self, draft_id: str) -> SceneResponse:
        try:
            result = await self._service.recover_autosave_draft(draft_id)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        original_path = result.get("model_path")
        if original_path:
            try:
                await self._recent_files_service.register_opened(original_path)
            except OSError:
                logger.warning("Falha ao registrar arquivo recente: %s", original_path)

        return SceneResponse.model_validate(result)

    async def discard_autosave_draft(self, draft_id: str) -> DiscardAutosaveDraftResponse:
        try:
            await self._service.discard_autosave_draft(draft_id)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return DiscardAutosaveDraftResponse(id=draft_id, discarded=True)

    async def update_instance_transform(
        self, instance_id: str, transform: list[float]
    ) -> UpdateTransformResponse:
        try:
            await self._service.update_instance_transform(instance_id, transform)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return UpdateTransformResponse(instance_id=instance_id, applied=True)

    async def save_scene(self, path: str | None) -> SaveSceneResponse:
        try:
            saved_path = await self._service.save_scene(path)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return SaveSceneResponse(saved=True, path=saved_path)

    async def delete_instance(self, instance_id: str) -> DeleteInstanceResponse:
        try:
            await self._service.delete_instance(instance_id)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return DeleteInstanceResponse(instance_id=instance_id, deleted=True)

    async def paint_instance(
        self, instance_id: str, r: int, g: int, b: int
    ) -> PaintInstanceResponse:
        """Equivalente real de "Ferramentas > Pintura" -- ver
        REVERSE_ENGINEERING_NOTES.md secao 28."""
        try:
            await self._service.paint_instance(instance_id, r, g, b)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return PaintInstanceResponse(instance_id=instance_id, painted=True, color=[r, g, b])

    async def tag_instance(self, instance_id: str, tag_name: str) -> TagInstanceResponse:
        """Equivalente real de "Ferramentas > Etiqueta" -- ver
        REVERSE_ENGINEERING_NOTES.md secao 28.17."""
        try:
            await self._service.tag_instance(instance_id, tag_name)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return TagInstanceResponse(instance_id=instance_id, tag_name=tag_name)

    async def paint_face(self, face_id: str, r: int, g: int, b: int) -> PaintFaceResponse:
        """Equivalente real de pintar UMA face especifica (nao a
        instancia inteira) -- ver REVERSE_ENGINEERING_NOTES.md secao
        28.19."""
        try:
            await self._service.paint_face(face_id, r, g, b)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return PaintFaceResponse(face_id=face_id, painted=True, color=[r, g, b])

    async def list_scenes(self) -> ListScenePagesResponse:
        """Equivalente real de "Janela > Bandeja padrao > Cenas" -- ver
        REVERSE_ENGINEERING_NOTES.md secao 28.20."""
        try:
            pages = await self._service.list_scenes()
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return ListScenePagesResponse(pages=[ScenePageDTO.model_validate(p) for p in pages])

    async def create_scene(self, name: str) -> CreateScenePageResponse:
        try:
            result = await self._service.create_scene(name)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return CreateScenePageResponse.model_validate(result)

    async def activate_scene(self, scene_id: str) -> ActivateScenePageResponse:
        try:
            await self._service.activate_scene(scene_id)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return ActivateScenePageResponse(scene_id=scene_id, activated=True)

    async def list_tags(self) -> ListTagsResponse:
        """Equivalente real de "Janela > Bandeja padrao > Etiquetas" --
        ver REVERSE_ENGINEERING_NOTES.md secao 28.22."""
        try:
            tags = await self._service.list_tags()
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return ListTagsResponse(tags=[TagDTO.model_validate(t) for t in tags])

    async def set_tag_visibility(self, tag_name: str, visible: bool) -> SetTagVisibilityResponse:
        try:
            result = await self._service.set_tag_visibility(tag_name, visible)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return SetTagVisibilityResponse.model_validate(result)

    async def set_instance_axes(
        self,
        instance_id: str,
        origin: list[float],
        x_point: list[float],
        y_point: list[float],
    ) -> SetInstanceAxesResponse:
        try:
            result = await self._service.set_instance_axes(
                instance_id, origin, x_point, y_point
            )
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return SetInstanceAxesResponse.model_validate(result)

    async def export_model_obj(self, path: str) -> ExportModelResponse:
        try:
            saved_path = await self._service.export_model_obj(path)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return ExportModelResponse(saved=True, path=saved_path)

    async def add_rectangle(
        self, width_m: float, height_m: float, as_group: bool = False
    ) -> AddRectangleResponse:
        """Equivalente real de "Desenho > Formas > Retângulo" -- ver
        REVERSE_ENGINEERING_NOTES.md secao 28."""
        try:
            scene = await self._service.add_rectangle(width_m, height_m, as_group)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return AddRectangleResponse(scene=SceneResponse.model_validate(scene))
