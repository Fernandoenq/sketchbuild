"""
Rotas do modulo de cena/visualizador 3D. So roteamento -- declara
path, metodo, schema de entrada/saida, e delega pro controller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    ActivateScenePageResponse,
    AddRectangleRequest,
    AddRectangleResponse,
    CreateScenePageRequest,
    CreateScenePageResponse,
    DeleteInstanceResponse,
    DiscardAutosaveDraftResponse,
    DuplicateInstanceRequest,
    DuplicateInstanceResponse,
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
    SceneAttributesResponse,
    SetInstanceAxesRequest,
    SetInstanceAxesResponse,
    SetTagVisibilityRequest,
    SetTagVisibilityResponse,
    TagInstanceRequest,
    TagInstanceResponse,
    ListTagsResponse,
    UpdateCameraRequest,
    UpdateCameraResponse,
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
    "/open-binary",
    response_model=SceneResponse,
    summary="Abre um .skp via motor nativo SkpBinaryReader (Pure Python / Zero DLL) com UVs analíticas, materiais PBR e instâncias",
)
async def open_binary_scene(
    body: OpenSceneRequest, controller: SceneController = Depends(get_controller)
) -> SceneResponse:
    return await controller.open_binary_scene(body.path)


@router.get(
    "/attributes",
    response_model=SceneAttributesResponse,
    summary="Extrai dicionários de atributos e componentes dinâmicos (dynamic_attributes) do .skp via Pure Python",
)
async def get_scene_attributes(
    path: str, controller: SceneController = Depends(get_controller)
) -> SceneAttributesResponse:
    return await controller.get_attributes(path)


@router.get(
    "/texture",
    summary="Serve texturas embutidas no container ZIP do .skp para renderização PBR no Three.js",
)
async def get_scene_texture(path: str, texture_path: str):
    import os
    import zipfile
    import mimetypes
    from fastapi import HTTPException
    from fastapi.responses import Response

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Arquivo .skp não encontrado no disco")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            if texture_path not in zf.namelist():
                raise HTTPException(status_code=404, detail="Textura não encontrada dentro do arquivo .skp")
            img_bytes = zf.read(texture_path)
            media_type, _ = mimetypes.guess_type(texture_path)
            return Response(content=img_bytes, media_type=media_type or "image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao extrair textura: {e}")


@router.post(
    "/open-upload",
    response_model=SceneResponse,
    summary="Abre um .skp enviado via upload do navegador (seletor nativo de arquivo do SO, sem precisar digitar o caminho)",
)
async def open_uploaded_scene(
    file: UploadFile = File(...),
    controller: SceneController = Depends(get_controller),
) -> SceneResponse:
    data = await file.read()
    return await controller.open_uploaded_scene(data)


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
    "/camera",
    response_model=UpdateCameraResponse,
    summary="Grava a orientação e posição da Câmera 3D in-place no .skp nativo via SkpBinaryWriter",
)
async def update_camera(
    body: UpdateCameraRequest,
    controller: SceneController = Depends(get_controller),
) -> UpdateCameraResponse:
    return await controller.update_camera(body)


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
    return await controller.save_scene(body.path, body.overwrite_confirmed)


@router.post(
    "/instances/{instance_id}/duplicate",
    response_model=DuplicateInstanceResponse,
    summary="Duplica nativamente uma instância na sessão ativa (Pure Python / Zero DLL)",
)
async def duplicate_instance(
    instance_id: str,
    body: DuplicateInstanceRequest | None = None,
    controller: SceneController = Depends(get_controller),
) -> DuplicateInstanceResponse:
    trans = body.transform if body else None
    delta = body.offset_delta_cm if body else None
    return await controller.duplicate_instance(instance_id, trans, delta)


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
    "/tags",
    response_model=ListTagsResponse,
    summary="Lista todas as Etiquetas reais do modelo aberto (equivalente a Janela > Bandeja padrao > Etiquetas)",
)
async def list_tags(
    controller: SceneController = Depends(get_controller),
) -> ListTagsResponse:
    return await controller.list_tags()


@router.patch(
    "/tags/{tag_name}/visibility",
    response_model=SetTagVisibilityResponse,
    summary="Alterna a visibilidade real de uma Etiqueta (SULayerSetVisibility, equivalente ao icone de olho da Bandeja padrao)",
)
async def set_tag_visibility(
    tag_name: str,
    body: SetTagVisibilityRequest,
    controller: SceneController = Depends(get_controller),
) -> SetTagVisibilityResponse:
    return await controller.set_tag_visibility(tag_name, body.visible)


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
