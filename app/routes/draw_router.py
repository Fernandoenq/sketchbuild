"""Rotas de desenho (F2): só roteamento, a lógica está em core/topology."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.controllers.draw_controller import DrawController
from app.schemas.draw import DrawRequest, DrawResponse, DrawStateResponse

router = APIRouter(prefix="/draw", tags=["draw"])


def get_controller() -> DrawController:
    return DrawController()


@router.post("", response_model=DrawResponse, summary="Desenha (linha, retângulo, círculo, polígono, arco, mão livre) e devolve o delta da topologia")
async def desenhar(body: DrawRequest, controller: DrawController = Depends(get_controller)) -> DrawResponse:
    return await controller.desenhar(body)


@router.get("/state", response_model=DrawStateResponse, summary="Estado completo da topologia de desenho")
async def estado(controller: DrawController = Depends(get_controller)) -> DrawStateResponse:
    return await controller.estado()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Zera a topologia de desenho")
async def limpar(controller: DrawController = Depends(get_controller)) -> Response:
    await controller.limpar()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
