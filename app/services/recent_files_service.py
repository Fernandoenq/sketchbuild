"""
Regra de negocio da lista de "Arquivos recentes" da Pagina Inicial.
Nunca toca o JSON/disco diretamente -- sempre via RecentFilesRepository
(mesmo padrao do SceneService com o SkpEngineRepository). Os metodos do
repository sao sincronos (I/O de arquivo) -- despachados pra uma
threadpool pra nao bloquear o event loop.
"""

from __future__ import annotations

from starlette.concurrency import run_in_threadpool

from app.repositories.recent_files_repository import RecentFilesRepository


class RecentFilesService:
    def __init__(self, repository: RecentFilesRepository | None = None):
        self._repository = repository or RecentFilesRepository()

    async def list_recent(self) -> list[dict]:
        return await run_in_threadpool(self._repository.list_all)

    async def register_opened(self, file_path: str) -> str:
        return await run_in_threadpool(self._repository.register_opened, file_path)

    async def save_thumbnail(self, file_path: str, image_base64: str) -> str:
        return await run_in_threadpool(
            self._repository.save_thumbnail, file_path, image_base64
        )
