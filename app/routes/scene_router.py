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
    ExportGlbRequest,
    ExportGlbResponse,
    ExportIfcRequest,
    ExportIfcResponse,
    AddLineGeometryRequest,
    AddFaceGeometryRequest,
    AddGeometryEntityResponse,
    ExportCutlistRequest,
    ExportCutlistResponse,
    AddCircleGeometryRequest,
    AddCylinderGeometryRequest,
    ExtrudeFaceGeometryRequest,
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
    CreateBoxRequest,
    CreateBoxResponse,
    SetStyleRequest,
    SetStyleResponse,
    AssemblyTreeResponse,
    ConvertDxfRequest,
    ConvertDxfResponse,
    BimBomReportResponse,
    ExplodedViewRequest,
    ExplodedViewResponse,
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


@router.post(
    "/box",
    response_model=CreateBoxResponse,
    summary="Cria um Sólido 3D Manifold paramétrico na cena (Frente 13)",
)
async def create_box(
    body: CreateBoxRequest,
    controller: SceneController = Depends(get_controller),
) -> CreateBoxResponse:
    return await controller.add_box(body)


@router.post(
    "/style",
    response_model=SetStyleResponse,
    summary="Configura estilo de renderização/exibição técnica (Frente 19)",
)
async def set_rendering_style(
    body: SetStyleRequest,
    controller: SceneController = Depends(get_controller),
) -> SetStyleResponse:
    return await controller.set_rendering_style(body)


@router.get(
    "/assembly-tree",
    response_model=AssemblyTreeResponse,
    summary="Obtém a árvore hierárquica do Outliner e montagens aninhadas (Frente 15)",
)
async def get_assembly_tree(
    controller: SceneController = Depends(get_controller),
) -> AssemblyTreeResponse:
    return await controller.get_assembly_tree()


@router.post(
    "/convert-dxf",
    response_model=ConvertDxfResponse,
    summary="Converte um arquivo DXF para SKP nativo (Frente 20)",
)
async def convert_dxf(
    body: ConvertDxfRequest,
    controller: SceneController = Depends(get_controller),
) -> ConvertDxfResponse:
    return await controller.convert_dxf(body)


@router.get(
    "/bim-report",
    response_model=BimBomReportResponse,
    summary="Gera relatório analítico de Orçamento BIM e Lista de Materiais (BOM)",
)
async def get_bim_bom_report(
    controller: SceneController = Depends(get_controller),
) -> BimBomReportResponse:
    return await controller.get_bim_bom_report()


@router.post(
    "/exploded-view",
    response_model=ExplodedViewResponse,
    summary="Calcula matrizes transformadas da Vista Explodida paramétrica",
)
async def calculate_exploded_view(
    body: ExplodedViewRequest,
    controller: SceneController = Depends(get_controller),
) -> ExplodedViewResponse:
    return await controller.calculate_exploded_view(body)


@router.post(
    "/export/glb",
    response_model=ExportGlbResponse,
    summary="Exporta nativamente a cena para glTF 2.0 Binary (.glb) com PBR (Frente 21 - Zero DLL)",
)
async def export_model_glb(
    body: ExportGlbRequest,
    controller: SceneController = Depends(get_controller),
) -> ExportGlbResponse:
    return await controller.export_model_glb(body.path)


@router.post(
    "/export/ifc",
    response_model=ExportIfcResponse,
    summary="Exporta nativamente a cena para modelo BIM aberto IFC4 STEP ISO 10303-21 (Frente 21 - Zero DLL)",
)
async def export_model_ifc(
    body: ExportIfcRequest,
    controller: SceneController = Depends(get_controller),
) -> ExportIfcResponse:
    return await controller.export_model_ifc(body.path, project_name=body.project_name)


@router.post(
    "/geometry/line",
    response_model=AddGeometryEntityResponse,
    summary="Cria uma aresta/linha 3D livre na cena (Frente 22)",
)
async def add_line_geometry(
    body: AddLineGeometryRequest,
    controller: SceneController = Depends(get_controller),
) -> AddGeometryEntityResponse:
    return await controller.add_line_geometry(body)


@router.post(
    "/geometry/face",
    response_model=AddGeometryEntityResponse,
    summary="Cria uma face coplanar fechada poligonal na cena (Frente 22)",
)
async def add_face_geometry(
    body: AddFaceGeometryRequest,
    controller: SceneController = Depends(get_controller),
) -> AddGeometryEntityResponse:
    return await controller.add_face_geometry(body)


@router.post(
    "/export/cutlist-xlsx",
    response_model=ExportCutlistResponse,
    summary="Exporta lista de corte e orçamento industrial em Excel .xlsx (Frente 23 - Zero DLL)",
)
async def export_cutlist_xlsx(
    body: ExportCutlistRequest,
    controller: SceneController = Depends(get_controller),
) -> ExportCutlistResponse:
    return await controller.export_cutlist_xlsx(body)


@router.post(
    "/geometry/circle",
    response_model=AddGeometryEntityResponse,
    summary="Cria um círculo plano B-Rep paramétrico (Frente 14 - Zero DLL)",
)
async def add_circle_geometry(
    body: AddCircleGeometryRequest,
    controller: SceneController = Depends(get_controller),
) -> AddGeometryEntityResponse:
    return await controller.add_circle_geometry(body)


@router.post(
    "/geometry/cylinder",
    response_model=AddGeometryEntityResponse,
    summary="Cria um cilindro 3D manifold paramétrico (Frente 14 - Zero DLL)",
)
async def add_cylinder_geometry(
    body: AddCylinderGeometryRequest,
    controller: SceneController = Depends(get_controller),
) -> AddGeometryEntityResponse:
    return await controller.add_cylinder_geometry(body)


@router.post(
    "/geometry/pushpull",
    response_model=AddGeometryEntityResponse,
    summary="Extrude uma face coplanar para sólido 3D Push/Pull (Frente 24 - Zero DLL)",
)
async def extrude_face_geometry(
    body: ExtrudeFaceGeometryRequest,
    controller: SceneController = Depends(get_controller),
) -> AddGeometryEntityResponse:
    return await controller.extrude_face_geometry(body)
