"""
Rotas do modulo de cena/visualizador 3D. So roteamento -- declara
path, metodo, schema de entrada/saida, e delega pro controller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    ActivateScenePageResponse,
    AddRectangleRequest,
    AddRectangleResponse,
    CreateScenePageRequest,
    CreateScenePageResponse,
    DeleteInstanceResponse,
    DiscardAutosaveDraftResponse,
    ExportModelRequest,
    ExportModelResponse,
    ListAutosaveDraftsResponse,
    ListScenePagesResponse,
    NewSceneFromTemplateRequest,
    OpenSceneRequest,
    PaintFaceRequest,
    PaintFaceResponse,
    PaintInstanceRequest,
    PaintInstanceResponse,
    SaveSceneRequest,
    SaveSceneResponse,
    SceneResponse,
    SetInstanceAxesRequest,
    SetInstanceAxesResponse,
    TagInstanceRequest,
    TagInstanceResponse,
    UpdateTransformRequest,
    UpdateTransformResponse,
)

router = APIRouter(prefix="/scene", tags=["scene"])


def get_controller() -> SceneController:
    return SceneController()


@router.post(
    "/open",
    response_model=SceneResponse,
    summary="Abre um .skp via motor ctypes (standalone, sem SketchUp aberto) e extrai malha + arvore de componentes",
)
async def open_scene(
    body: OpenSceneRequest, controller: SceneController = Depends(get_controller)
) -> SceneResponse:
    return await controller.open_scene(body.path)


@router.post(
    "/new",
    response_model=SceneResponse,
    summary="Cria um modelo novo a partir de um template real da Trimble (sem arquivo no disco ate o 1o save)",
)
async def new_scene_from_template(
    body: NewSceneFromTemplateRequest,
    controller: SceneController = Depends(get_controller),
) -> SceneResponse:
    return await controller.new_scene_from_template(body.template_id)


@router.get(
    "/session",
    response_model=SceneResponse,
    summary="Reextrai a sessao JA ABERTA em memoria sem tocar o disco (cobre reload da pagina com o backend ainda rodando) -- 409 se nao ha sessao",
)
async def get_current_session(
    controller: SceneController = Depends(get_controller),
) -> SceneResponse:
    return await controller.get_current_session()


@router.get(
    "/autosave",
    response_model=ListAutosaveDraftsResponse,
    summary="Lista rascunhos de autosave reais (.skp em app/data/autosave/) disponiveis pra recuperacao",
)
async def list_autosave_drafts(
    controller: SceneController = Depends(get_controller),
) -> ListAutosaveDraftsResponse:
    return await controller.list_autosave_drafts()


@router.post(
    "/autosave/{draft_id}/recover",
    response_model=SceneResponse,
    summary="Reabre um rascunho de autosave, associando a sessao de volta ao caminho ORIGINAL (nao ao arquivo de rascunho)",
)
async def recover_autosave_draft(
    draft_id: str, controller: SceneController = Depends(get_controller)
) -> SceneResponse:
    return await controller.recover_autosave_draft(draft_id)


@router.delete(
    "/autosave/{draft_id}",
    response_model=DiscardAutosaveDraftResponse,
    summary="Descarta um rascunho de autosave sem recuperar (apaga o .skp interno e a entrada do manifesto)",
)
async def discard_autosave_draft(
    draft_id: str, controller: SceneController = Depends(get_controller)
) -> DiscardAutosaveDraftResponse:
    return await controller.discard_autosave_draft(draft_id)


@router.patch(
    "/instances/{instance_id}/transform",
    response_model=UpdateTransformResponse,
    summary="Aplica uma nova transformacao (mundial, column-major) a uma instancia da sessao aberta",
)
async def update_instance_transform(
    instance_id: str,
    body: UpdateTransformRequest,
    controller: SceneController = Depends(get_controller),
) -> UpdateTransformResponse:
    return await controller.update_instance_transform(instance_id, body.transform)


@router.post(
    "/save",
    response_model=SaveSceneResponse,
    summary="Grava o modelo editado em disco (sobrescreve o arquivo aberto se `path` for omitido)",
)
async def save_scene(
    body: SaveSceneRequest, controller: SceneController = Depends(get_controller)
) -> SaveSceneResponse:
    return await controller.save_scene(body.path)


@router.delete(
    "/instances/{instance_id}",
    response_model=DeleteInstanceResponse,
    summary="Exclui de verdade uma instancia da sessao aberta (equivalente a Editar > Excluir / Del)",
)
async def delete_instance(
    instance_id: str, controller: SceneController = Depends(get_controller)
) -> DeleteInstanceResponse:
    return await controller.delete_instance(instance_id)


@router.post(
    "/export/obj",
    response_model=ExportModelResponse,
    summary="Exporta a sessao aberta pra um arquivo .obj (equivalente parcial de Arquivo > Exportar > Modelo 3D)",
)
async def export_model_obj(
    body: ExportModelRequest, controller: SceneController = Depends(get_controller)
) -> ExportModelResponse:
    return await controller.export_model_obj(body.path)


@router.post(
    "/instances/{instance_id}/material",
    response_model=PaintInstanceResponse,
    summary="Aplica uma cor RGBA nova numa instancia da sessao aberta (equivalente a Ferramentas > Pintura)",
)
async def paint_instance(
    instance_id: str,
    body: PaintInstanceRequest,
    controller: SceneController = Depends(get_controller),
) -> PaintInstanceResponse:
    return await controller.paint_instance(instance_id, body.r, body.g, body.b)


@router.post(
    "/geometry/rectangle",
    response_model=AddRectangleResponse,
    summary="Cria uma face retangular nova no chao da sessao aberta (equivalente a Desenho > Formas > Retângulo), opcionalmente dentro de um Grupo novo",
)
async def add_rectangle(
    body: AddRectangleRequest, controller: SceneController = Depends(get_controller)
) -> AddRectangleResponse:
    return await controller.add_rectangle(body.width_m, body.height_m, body.as_group)


@router.post(
    "/instances/{instance_id}/tag",
    response_model=TagInstanceResponse,
    summary="Aplica uma Etiqueta (Tag) real numa instancia da sessao aberta (equivalente a Ferramentas > Etiqueta)",
)
async def tag_instance(
    instance_id: str,
    body: TagInstanceRequest,
    controller: SceneController = Depends(get_controller),
) -> TagInstanceResponse:
    return await controller.tag_instance(instance_id, body.name)


@router.post(
    "/faces/{face_id}/material",
    response_model=PaintFaceResponse,
    summary="Aplica uma cor RGBA nova numa FACE especifica da sessao aberta (pintura por face, nao a instancia inteira)",
)
async def paint_face(
    face_id: str,
    body: PaintFaceRequest,
    controller: SceneController = Depends(get_controller),
) -> PaintFaceResponse:
    return await controller.paint_face(face_id, body.r, body.g, body.b)


@router.get(
    "/pages",
    response_model=ListScenePagesResponse,
    summary="Lista todas as Cenas reais do modelo aberto (equivalente a Janela > Bandeja padrao > Cenas)",
)
async def list_scene_pages(
    controller: SceneController = Depends(get_controller),
) -> ListScenePagesResponse:
    return await controller.list_scenes()


@router.post(
    "/pages",
    response_model=CreateScenePageResponse,
    summary="Cria uma Cena real nova a partir do estado atual (SUSceneCreate/SUModelAddScenes)",
)
async def create_scene_page(
    body: CreateScenePageRequest,
    controller: SceneController = Depends(get_controller),
) -> CreateScenePageResponse:
    return await controller.create_scene(body.name)


@router.post(
    "/pages/{scene_id}/activate",
    response_model=ActivateScenePageResponse,
    summary="Ativa uma Cena real (SUModelSetActiveScene) -- nao move a camera do viewer nesta sessao",
)
async def activate_scene_page(
    scene_id: str,
    controller: SceneController = Depends(get_controller),
) -> ActivateScenePageResponse:
    return await controller.activate_scene(scene_id)


@router.post(
    "/instances/{instance_id}/axes",
    response_model=SetInstanceAxesResponse,
    summary="Redefine os eixos customizados (locais) da definicao por tras da instancia/Grupo clicado (equivalente a Ferramentas > Eixos)",
)
async def set_instance_axes(
    instance_id: str,
    body: SetInstanceAxesRequest,
    controller: SceneController = Depends(get_controller),
) -> SetInstanceAxesResponse:
    return await controller.set_instance_axes(
        instance_id, body.origin, body.x_point, body.y_point
    )
