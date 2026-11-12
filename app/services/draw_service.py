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

    async def siga_me(self, face_id: int, arestas: list[int]) -> dict:
        return await run_in_threadpool(self._repository.siga_me, face_id, arestas)

    async def intersectar(self, faces) -> dict:
        return await run_in_threadpool(self._repository.intersectar, faces)

    async def agrupar(self, tipo: str, faces, arestas, nome) -> dict:
        return await run_in_threadpool(self._repository.agrupar, tipo, faces, arestas, nome)

    async def instanciar(self, instancia: int, transformacao) -> dict:
        return await run_in_threadpool(self._repository.instanciar, instancia, transformacao)

    async def explodir(self, instancia: int) -> dict:
        return await run_in_threadpool(self._repository.explodir, instancia)

    async def entrar(self, instancia: int) -> dict:
        return await run_in_threadpool(self._repository.entrar, instancia)

    async def sair(self) -> dict:
        return await run_in_threadpool(self._repository.sair)

    async def cena(self) -> dict:
        return await run_in_threadpool(self._repository.cena)

    async def salvar(self, caminho: str, sobrescrever: bool) -> dict:
        return await run_in_threadpool(self._repository.salvar, caminho, sobrescrever)

    async def pintar(self, **params) -> dict:
        return await run_in_threadpool(lambda: self._repository.pintar(**params))

    async def marcar(self, **params) -> dict:
        return await run_in_threadpool(lambda: self._repository.marcar(**params))

    async def guia(self, **params) -> dict:
        return await run_in_threadpool(lambda: self._repository.guia(**params))

    async def suavizar(self, **params) -> dict:
        return await run_in_threadpool(lambda: self._repository.suavizar(**params))

    async def adicionar_cena(self, **params) -> dict:
        return await run_in_threadpool(lambda: self._repository.adicionar_cena(**params))

    async def desfazer(self) -> dict:
        return await run_in_threadpool(self._repository.desfazer)

    async def refazer(self) -> dict:
        return await run_in_threadpool(self._repository.refazer)

    async def historico(self) -> dict:
        return await run_in_threadpool(self._repository.historico)

    async def estado(self) -> dict:
        return await run_in_threadpool(self._repository.estado)

    async def limpar(self) -> None:
        await run_in_threadpool(self._repository.limpar)
