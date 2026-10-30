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
    InspectBinaryRequest,
    InspectBinaryResponse,
    ModelSummaryResponse,
    OpenModelRequest,
    OpenModelResponse,
    PingResponse,
)
from core.skp_binary_reader import SkpBinaryReader
from fastapi import HTTPException

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


@router.post(
    "/inspect-binary",
    response_model=InspectBinaryResponse,
    summary="Inspeciona Bounding Box e contagem de vértices diretamente do model.dat sem DLL",
)
async def inspect_binary_skp(body: InspectBinaryRequest) -> InspectBinaryResponse:
    info = SkpBinaryReader.extract_bounds(body.path)
    if not info:
        raise HTTPException(status_code=400, detail="Não foi possível ler o container ZIP ou model.dat do arquivo .skp")
    return InspectBinaryResponse(
        num_vertices=info["num_vertices"],
        largura_cm=info["largura_cm"],
        profundidade_cm=info["profundidade_cm"],
        altura_cm=info["altura_cm"],
        min_pt_cm=list(info["min_pt_cm"]),
        max_pt_cm=list(info["max_pt_cm"]),
        is_empty=info["is_empty"],
    )
