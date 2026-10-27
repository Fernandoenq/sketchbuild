"""
Controller do modulo de cena/visualizador: orquestra o service e
traduz excecoes de dominio para HTTPException. Nenhuma regra de
negocio mora aqui.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.domain.exceptions import (
    InvalidModelPathError,
    ModelFileNotFoundError,
    SceneParseError,
    SceneSessionError,
)
from app.schemas.scene import (
    SaveSceneResponse,
    SceneResponse,
    UpdateTransformResponse,
)
from app.services.scene_service import SceneService


class SceneController:
    def __init__(self, service: SceneService | None = None):
        self._service = service or SceneService()

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
        return SceneResponse.model_validate(result)

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
