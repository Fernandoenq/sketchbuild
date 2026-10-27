"""
Handlers de exceção globais -- defesa em profundidade.

Cada controller já traduz as exceções de dominio que conhece em
HTTPException (ver app/controllers/model_controller.py). Estes
handlers aqui cobrem o que escapar disso: uma exceção de dominio que
um controller futuro esqueceu de tratar, ou qualquer bug inesperado.
Sem isso, o cliente HTTP veria um 500 com stack trace cru (ou nada, em
produção com debug desligado) -- aqui ele sempre recebe um JSON
previsível.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import BridgeUnavailableError, SketchBuildError

logger = logging.getLogger("sketchbuild")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BridgeUnavailableError)
    async def handle_bridge_unavailable(
        request: Request, exc: BridgeUnavailableError
    ) -> JSONResponse:
        logger.warning("Bridge unavailable: %s", exc)
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(SketchBuildError)
    async def handle_sketchbuild_error(
        request: Request, exc: SketchBuildError
    ) -> JSONResponse:
        # Qualquer excecao de dominio que um controller especifico nao
        # tenha capturado explicitamente. 502: o problema esta na
        # comunicacao com o SketchUp, nao no proprio backend.
        logger.warning("Unhandled domain error: %s: %s", exc.__class__.__name__, exc)
        return JSONResponse(status_code=502, content={"detail": str(exc)})

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        # Ultima linha de defesa: nunca deixar um traceback cru vazar
        # pro cliente HTTP.
        logger.exception("Unexpected error handling %s %s", request.method, request.url)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error. Check server logs for details."},
        )
