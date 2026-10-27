"""
Rotas do modulo de modelos. So roteamento -- declara path, metodo,
schema de entrada/saida, e delega pro controller. Zero logica de
negocio aqui.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.model_controller import ModelController
from app.schemas.model import (
    CloseModelResponse,
    ModelSummaryResponse,
    OpenModelRequest,
    OpenModelResponse,
    PingResponse,
)

router = APIRouter(prefix="/models", tags=["models"])


def get_controller() -> ModelController:
    return ModelController()


@router.get("/bridge/ping", response_model=PingResponse, summary="Testa a conexao com a Sketchup Bridge")
async def ping_bridge(controller: ModelController = Depends(get_controller)) -> PingResponse:
    return await controller.ping()


@router.post("/open", response_model=OpenModelResponse, summary="Abre um .skp no SketchUp ativo")
async def open_model(
    body: OpenModelRequest, controller: ModelController = Depends(get_controller)
) -> OpenModelResponse:
    return await controller.open_model(body.path)


@router.get("/current", response_model=ModelSummaryResponse, summary="Resumo do modelo ativo no SketchUp")
async def get_current_model(
    controller: ModelController = Depends(get_controller),
) -> ModelSummaryResponse:
    return await controller.get_model_summary()


@router.post("/current/close", response_model=CloseModelResponse, summary="Fecha o modelo ativo (abre um em branco)")
async def close_current_model(
    controller: ModelController = Depends(get_controller),
) -> CloseModelResponse:
    return await controller.close_model()
