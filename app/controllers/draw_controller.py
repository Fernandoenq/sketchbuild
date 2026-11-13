from __future__ import annotations

from fastapi import HTTPException, status

from app.schemas.draw import DrawRequest, DrawResponse, SaveDrawRequest, SaveDrawResponse, DrawStateResponse, EditRequest, EraseRequest, FollowMeRequest, GroupRequest, InstanceRequest, GroupSolidRequest, IntersectRequest, OffsetRequest, PaintRequest, PaintResponse, TagRequest, CenaRequest, SoftenRequest, SelecaoRequest, SelecaoResponse, SolidoRequest, SolidoResponse, GuiaRequest, NotaRequest, PosicionarRequest, ComportamentoRequest, PushPullRequest, SceneSummaryResponse
from app.services.draw_service import DrawService


class DrawController:
    def __init__(self, service: DrawService | None = None):
        self._service = service or DrawService()

    async def desenhar(self, body: DrawRequest) -> DrawResponse:
        params = body.model_dump(exclude={"ferramenta"})
        try:
            return DrawResponse(**await self._service.desenhar(body.ferramenta, **params))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def empurrar(self, body: PushPullRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.empurrar(body.face_id, body.distancia, body.criar_nova))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def editar(self, body: EditRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.editar(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def apagar(self, body: EraseRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.apagar(body.arestas, body.faces))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def offset(self, body: OffsetRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.offset(body.face_id, body.distancia))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def siga_me(self, body: FollowMeRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.siga_me(body.face_id, body.arestas))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def intersectar(self, body: IntersectRequest) -> DrawResponse:
        try:
            return DrawResponse(**await self._service.intersectar(body.faces))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def _cena(self, chamada) -> dict:
        try:
            return await chamada
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def agrupar(self, body: GroupRequest) -> dict:
        return await self._cena(self._service.agrupar(body.tipo, body.faces, body.arestas, body.nome))

    async def instanciar(self, body: InstanceRequest) -> dict:
        return await self._cena(self._service.instanciar(body.instancia, body.transformacao))

    async def combinar_grupos(self, body: GroupSolidRequest) -> SceneSummaryResponse:
        return SceneSummaryResponse(**await self._cena(self._service.combinar_grupos(**body.model_dump())))

    async def apagar_instancia(self, body: InstanceRequest) -> SceneSummaryResponse:
        return SceneSummaryResponse(**await self._cena(self._service.apagar_instancia(body.instancia)))

    async def explodir(self, body: InstanceRequest) -> SceneSummaryResponse:
        return SceneSummaryResponse(**await self._cena(self._service.explodir(body.instancia)))

    async def entrar(self, body: InstanceRequest) -> SceneSummaryResponse:
        return SceneSummaryResponse(**await self._cena(self._service.entrar(body.instancia)))

    async def sair(self) -> SceneSummaryResponse:
        return SceneSummaryResponse(**await self._cena(self._service.sair()))

    async def cena(self) -> SceneSummaryResponse:
        return SceneSummaryResponse(**await self._service.cena())

    async def salvar(self, body: SaveDrawRequest) -> SaveDrawResponse:
        try:
            return SaveDrawResponse(**await self._service.salvar(body.path, body.sobrescrever))
        except FileExistsError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "arquivo_existe", "message": "o arquivo ja existe; confirme para sobrescrever", "path": str(e)},
            ) from e
        except (ValueError, OSError) as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def pintar(self, body: PaintRequest) -> PaintResponse:
        try:
            return PaintResponse(**await self._service.pintar(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def marcar(self, body: TagRequest) -> DrawStateResponse:
        try:
            return DrawStateResponse(**await self._service.marcar(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def nota(self, body: NotaRequest) -> DrawStateResponse:
        try:
            return DrawStateResponse(**await self._service.nota(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def comportamento(self, body: ComportamentoRequest) -> SceneSummaryResponse:
        try:
            return SceneSummaryResponse(**await self._service.comportamento(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def posicionar(self, body: PosicionarRequest) -> DrawStateResponse:
        try:
            return DrawStateResponse(**await self._service.posicionar(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def guia(self, body: GuiaRequest) -> DrawStateResponse:
        try:
            return DrawStateResponse(**await self._service.guia(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def suavizar(self, body: SoftenRequest) -> DrawStateResponse:
        try:
            return DrawStateResponse(**await self._service.suavizar(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def selecionar(self, body: SelecaoRequest) -> SelecaoResponse:
        try:
            r = await self._service.selecionar(**body.model_dump())
            return SelecaoResponse(faces=r["faces"], edges=r["edges"], vertices=r["vertices"])
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def solido(self, body: SolidoRequest) -> SolidoResponse:
        try:
            return SolidoResponse(**await self._service.solido(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def adicionar_cena(self, body: CenaRequest) -> DrawStateResponse:
        try:
            return DrawStateResponse(**await self._service.adicionar_cena(**body.model_dump()))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def desfazer(self) -> DrawStateResponse:
        try:
            return DrawStateResponse(**await self._service.desfazer())
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def refazer(self) -> DrawStateResponse:
        try:
            return DrawStateResponse(**await self._service.refazer())
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def historico(self) -> dict:
        return await self._service.historico()

    async def estado(self) -> DrawStateResponse:
        return DrawStateResponse(**await self._service.estado())

    async def limpar(self) -> None:
        await self._service.limpar()
