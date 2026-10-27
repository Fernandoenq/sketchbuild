"""
Regra de negocio do modulo de modelos. Nunca fala com socket/JSON
diretamente -- sempre via BridgeRepository. Validacoes de dominio (
caminho valido, arquivo existe) vivem aqui, nao no controller nem no
repository.

Os metodos do repository sao sincronos (socket bloqueante). Como o
FastAPI roda tudo isso dentro de um event loop async, cada chamada ao
repository e despachada pra uma threadpool (`run_in_threadpool`) pra
nao bloquear o loop enquanto o socket espera a resposta do SketchUp --
isso importa principalmente em open_model, que pode levar bem mais que
um segundo num arquivo grande (ver REVERSE_ENGINEERING_NOTES.md secao
10.7/10.8).
"""

from __future__ import annotations

import os

from starlette.concurrency import run_in_threadpool

from app.domain.exceptions import InvalidModelPathError, ModelFileNotFoundError
from app.repositories.bridge_repository import BridgeRepository

VALID_MODEL_EXTENSION = ".skp"


class ModelService:
    def __init__(self, repository: BridgeRepository | None = None):
        self._repository = repository or BridgeRepository()

    async def ping_bridge(self) -> dict:
        return await run_in_threadpool(self._repository.ping)

    async def open_model(self, file_path: str) -> dict:
        self._validate_model_path(file_path)
        return await run_in_threadpool(self._repository.open_model, file_path)

    async def get_model_summary(self) -> dict:
        return await run_in_threadpool(self._repository.model_summary)

    async def close_model(self) -> dict:
        return await run_in_threadpool(self._repository.close_model)

    # -- validacoes de dominio ------------------------------------------------

    def _validate_model_path(self, file_path: str) -> None:
        if not file_path or not file_path.strip():
            raise InvalidModelPathError("caminho do modelo nao pode ser vazio")

        if not file_path.lower().endswith(VALID_MODEL_EXTENSION):
            raise InvalidModelPathError(
                f"caminho deve apontar para um arquivo {VALID_MODEL_EXTENSION} "
                f"(recebido: {file_path!r})"
            )

        # NOTA: isso assume que o backend Python roda na MESMA maquina
        # Windows que o SketchUp (e o caso hoje). Se um dia o backend
        # rodar em outra maquina/container, este check local perde o
        # sentido e so o check feito dentro de cmd_open_model no lado
        # Ruby (File.exist?) continua valendo -- ver pendencia em
        # REVERSE_ENGINEERING_NOTES.md secao 11.
        if not os.path.exists(file_path):
            raise ModelFileNotFoundError(f"arquivo nao encontrado: {file_path}")
