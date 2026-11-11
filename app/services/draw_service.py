from __future__ import annotations

from fastapi.concurrency import run_in_threadpool

from app.repositories.draw_repository import DrawRepository


class DrawService:
    def __init__(self, repository: DrawRepository | None = None):
        self._repository = repository or DrawRepository()

    async def desenhar(self, ferramenta: str, **params) -> dict:
        return await run_in_threadpool(self._repository.desenhar, ferramenta, **params)

    async def empurrar(self, face_id: int, distancia: float, criar_nova: bool) -> dict:
        return await run_in_threadpool(self._repository.empurrar, face_id, distancia, criar_nova)

    async def editar(self, **params) -> dict:
        return await run_in_threadpool(lambda: self._repository.editar(**params))

    async def offset(self, face_id: int, distancia: float) -> dict:
        return await run_in_threadpool(self._repository.offset, face_id, distancia)

    async def estado(self) -> dict:
        return await run_in_threadpool(self._repository.estado)

    async def limpar(self) -> None:
        await run_in_threadpool(self._repository.limpar)
