"""
Controller do modulo de modelos: orquestra o service e traduz
excecoes de dominio para HTTPException. Nenhuma regra de negocio
mora aqui -- isso e papel do service.
"""

from __future__ import annotations

from fastapi import HTTPException, status

from app.domain.exceptions import (
    BridgeCommandError,
    BridgeUnavailableError,
    InvalidModelPathError,
    ModelFileNotFoundError,
)
from app.schemas.model import (
    CloseModelResponse,
    ModelSummaryResponse,
    OpenModelResponse,
    PingResponse,
)
from app.services.model_service import ModelService


class ModelController:
    def __init__(self, service: ModelService | None = None):
        self._service = service or ModelService()

    async def ping(self) -> PingResponse:
        try:
            result = await self._service.ping_bridge()
        except BridgeUnavailableError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
            ) from e
        return PingResponse.model_validate(result)

    async def open_model(self, file_path: str) -> OpenModelResponse:
        try:
            result = await self._service.open_model(file_path)
        except (InvalidModelPathError, ModelFileNotFoundError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except BridgeUnavailableError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
            ) from e
        except BridgeCommandError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e
        return OpenModelResponse.model_validate(result)

    async def get_model_summary(self) -> ModelSummaryResponse:
        try:
            result = await self._service.get_model_summary()
        except BridgeUnavailableError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
            ) from e
        except BridgeCommandError as e:
            # ex.: "nenhum modelo ativo" -- ver cmd_model_summary no lado Ruby
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            ) from e
        return ModelSummaryResponse.model_validate(result)

    async def close_model(self) -> CloseModelResponse:
        try:
            result = await self._service.close_model()
        except BridgeUnavailableError as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e)
            ) from e
        except BridgeCommandError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e
        return CloseModelResponse.model_validate(result)
