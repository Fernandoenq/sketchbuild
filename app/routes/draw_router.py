"""Rotas de desenho (F2): só roteamento, a lógica está em core/topology."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from app.controllers.draw_controller import DrawController
from app.schemas.draw import DrawRequest, DrawResponse, SaveDrawRequest, SaveDrawResponse, DrawStateResponse, EditRequest, FollowMeRequest, GroupRequest, InstanceRequest, IntersectRequest, OffsetRequest, PushPullRequest, SceneSummaryResponse

router = APIRouter(prefix="/draw", tags=["draw"])


def get_controller() -> DrawController:
    return DrawController()


@router.post("", response_model=DrawResponse, summary="Desenha (linha, retângulo, círculo, polígono, arco, mão livre) e devolve o delta da topologia")
async def desenhar(body: DrawRequest, controller: DrawController = Depends(get_controller)) -> DrawResponse:
    return await controller.desenhar(body)


@router.post("/pushpull", response_model=DrawResponse, summary="Empurrar/Puxar uma face e devolve o delta da topologia")
async def empurrar(body: PushPullRequest, controller: DrawController = Depends(get_controller)) -> DrawResponse:
    return await controller.empurrar(body)


@router.post("/edit", response_model=DrawResponse, summary="Mover, rotacionar ou escalar a selecao (vertices, arestas, faces)")
async def editar(body: EditRequest, controller: DrawController = Depends(get_controller)) -> DrawResponse:
    return await controller.editar(body)


@router.post("/offset", response_model=DrawResponse, summary="Offset de uma face (negativo para dentro)")
async def offset(body: OffsetRequest, controller: DrawController = Depends(get_controller)) -> DrawResponse:
    return await controller.offset(body)


@router.post("/followme", response_model=DrawResponse, summary="Siga-me: varre a face ao longo de um caminho de arestas")
async def siga_me(body: FollowMeRequest, controller: DrawController = Depends(get_controller)) -> DrawResponse:
    return await controller.siga_me(body)


@router.post("/intersect", response_model=DrawResponse, summary="Intersect Faces na definicao ativa (todas ou as faces dadas)")
async def intersectar(body: IntersectRequest, controller: DrawController = Depends(get_controller)) -> DrawResponse:
    return await controller.intersectar(body)


@router.get("/scene", response_model=SceneSummaryResponse, summary="Definicoes, instancias e definicao ativa")
async def cena(controller: DrawController = Depends(get_controller)) -> SceneSummaryResponse:
    return await controller.cena()


@router.post("/group", summary="Cria grupo ou componente a partir da selecao (faces e arestas)")
async def agrupar(body: GroupRequest, controller: DrawController = Depends(get_controller)) -> dict:
    return await controller.agrupar(body)


@router.post("/instance", summary="Nova instancia de um componente")
async def instanciar(body: InstanceRequest, controller: DrawController = Depends(get_controller)) -> dict:
    return await controller.instanciar(body)


@router.post("/explode", response_model=SceneSummaryResponse, summary="Explode uma instancia na definicao ativa")
async def explodir(body: InstanceRequest, controller: DrawController = Depends(get_controller)) -> SceneSummaryResponse:
    return await controller.explodir(body)


@router.post("/enter", response_model=SceneSummaryResponse, summary="Entra na definicao de uma instancia para editar")
async def entrar(body: InstanceRequest, controller: DrawController = Depends(get_controller)) -> SceneSummaryResponse:
    return await controller.entrar(body)


@router.post("/exit", response_model=SceneSummaryResponse, summary="Sai da definicao em edicao")
async def sair(controller: DrawController = Depends(get_controller)) -> SceneSummaryResponse:
    return await controller.sair()


@router.post("/save", response_model=SaveDrawResponse, summary="Grava o desenho (raiz) num .skp novo; nunca sobrescreve sem confirmar")
async def salvar(body: SaveDrawRequest, controller: DrawController = Depends(get_controller)) -> SaveDrawResponse:
    return await controller.salvar(body)


@router.post("/undo", response_model=DrawStateResponse, summary="Desfaz a ultima operacao (devolve o estado completo)")
async def desfazer(controller: DrawController = Depends(get_controller)) -> DrawStateResponse:
    return await controller.desfazer()


@router.post("/redo", response_model=DrawStateResponse, summary="Refaz a operacao desfeita (devolve o estado completo)")
async def refazer(controller: DrawController = Depends(get_controller)) -> DrawStateResponse:
    return await controller.refazer()


@router.get("/history", summary="Passos para desfazer e refazer e o log de operacoes")
async def historico(controller: DrawController = Depends(get_controller)) -> dict:
    return await controller.historico()


@router.get("/state", response_model=DrawStateResponse, summary="Estado completo da topologia de desenho")
async def estado(controller: DrawController = Depends(get_controller)) -> DrawStateResponse:
    return await controller.estado()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Zera a topologia de desenho")
async def limpar(controller: DrawController = Depends(get_controller)) -> Response:
    await controller.limpar()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
