"""
Health check do sidecar. Sempre responde 200 -- o status "degraded"
(bridge fora do ar) e informativo, nao um erro HTTP, porque o backend
em si esta saudavel mesmo que o SketchUp esteja fechado.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.model_controller import ModelController
from app.schemas.model import HealthResponse
from app.routes.model_router import get_controller

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Saude do sidecar e da conexao com a bridge")
async def health(controller: ModelController = Depends(get_controller)) -> HealthResponse:
    try:
        bridge_info = await controller.ping()
    except Exception as e:  # noqa: BLE001 -- health check nao deve propagar erro
        detail = (
            str(e.detail)
            if hasattr(e, "detail")
            else str(e)
        )
        return HealthResponse(status="degraded", bridge=None, detail=detail)
    return HealthResponse(status="ok", bridge=bridge_info)
