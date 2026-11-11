from __future__ import annotations

from fastapi import HTTPException, status

from app.schemas.draw import DrawRequest, DrawResponse, DrawStateResponse, EditRequest, OffsetRequest, PushPullRequest
from app.services.draw_service import DrawService


class DrawController:
    def __init__(self, service: DrawService | None = None):
        self._service = service or DrawService()

    async def desenhar(self, body: DrawRequest) -> DrawResponse:
        params = body.model_dump(exclude={"ferramenta"})
        try:
            return DrawResponse(**await self._service.desenhar(body.ferramenta, **params))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def empurrar(self, body: PushPullRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.empurrar(body.face_id, body.distancia, body.criar_nova))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def editar(self, body: EditRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.editar(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def offset(self, body: OffsetRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.offset(body.face_id, body.distancia))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def estado(self) -> DrawStateResponse:
        return DrawStateResponse(**await self._service.estado())

    async def limpar(self) -> None:
        await self._service.limpar()
