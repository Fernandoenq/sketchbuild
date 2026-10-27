"""
Regra de negocio do modulo de cena/visualizador. Nunca fala com
`ctypes`/`core.*` diretamente -- sempre via SkpEngineRepository.
Validacoes de dominio (caminho valido, arquivo existe) vivem aqui,
mesmo padrao do ModelService (ver app/services/model_service.py).

O metodo do repository e sincrono (chamada ctypes bloqueante contra a
SketchUpAPI.dll). Como o FastAPI roda isso dentro de um event loop
async, despachamos pra uma threadpool (`run_in_threadpool`) pra nao
bloquear o loop enquanto a DLL parseia o .skp.
"""

from __future__ import annotations

import os

from starlette.concurrency import run_in_threadpool

from app.domain.exceptions import InvalidModelPathError, ModelFileNotFoundError
from app.repositories.skp_engine_repository import SkpEngineRepository

VALID_MODEL_EXTENSION = ".skp"


class SceneService:
    def __init__(self, repository: SkpEngineRepository | None = None):
        self._repository = repository or SkpEngineRepository()

    async def open_scene(self, file_path: str) -> dict:
        self._validate_model_path(file_path)
        return await run_in_threadpool(self._repository.open, file_path)

    async def update_instance_transform(
        self, instance_id: str, transform: list[float]
    ) -> None:
        await run_in_threadpool(
            self._repository.set_instance_transform, instance_id, transform
        )

    async def save_scene(self, path: str | None) -> str:
        return await run_in_threadpool(self._repository.save, path)

    # -- validacoes de dominio ------------------------------------------------

    def _validate_model_path(self, file_path: str) -> None:
        if not file_path or not file_path.strip():
            raise InvalidModelPathError("caminho do modelo nao pode ser vazio")

        if not file_path.lower().endswith(VALID_MODEL_EXTENSION):
            raise InvalidModelPathError(
                f"caminho deve apontar para um arquivo {VALID_MODEL_EXTENSION} "
                f"(recebido: {file_path!r})"
            )

        if not os.path.exists(file_path):
            raise ModelFileNotFoundError(f"arquivo nao encontrado: {file_path}")
