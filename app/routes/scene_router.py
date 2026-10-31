"""
Rotas do modulo de cena/visualizador 3D. So roteamento -- declara
path, metodo, schema de entrada/saida, e delega pro controller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from app.controllers.scene_controller import SceneController
from app.schemas.scene import (
    NestingRequest,
    NestingResponse,
    TerrainRequest,
    TerrainResponse,
    StructuralAnalysisRequest,
    StructuralAnalysisResponse,
    ScaleRequest,
    ScaleResponse,
    ExportCamDxfRequest,
    ExportCamDxfResponse,
    CameraPathRequest,
    CameraPathResponse,
    PointCloudExportRequest,
    PointCloudExportResponse,
    MaintenancePlanRequest,
    MaintenancePlanResponse,
    MirrorRequest,
    MirrorResponse,
    QrTagExportRequest,
    QrTagExportResponse,
    SwingKinematicsRequest,
    SwingKinematicsResponse,
    ArtReportRequest,
    ArtReportResponse,
    WallThicknessRequest,
    WallThicknessResponse,
    CargoLoadRequest,
    CargoLoadResponse,
    TechnicalSketchRequest,
    TechnicalSketchResponse,
    SpiralTubeRequest,
    SpiralTubeResponse,
    OverturnStabilityRequest,
    OverturnStabilityResponse,
    FieldInspectionRequest,
    FieldInspectionResponse,
    AngleDimensionRequest,
    AngleDimensionResponse,
    FastenerTorqueRequest,
    FastenerTorqueResponse,
    HipRoofRequest,
    HipRoofResponse,
    HicRequest,
    HicResponse,
    ZebraLabelRequest,
    ZebraLabelResponse,
    ExplodedTrailsRequest,
    ExplodedTrailsResponse,
    CarbonFootprintRequest,
    CarbonFootprintResponse,
    AttributeDictionaryRequest,
    AttributeDictionaryResponse,
    TagFolderRequest,
    TagFolderResponse,
    EdgeStylesRequest,
    EdgeStylesResponse,
    TwoPointPerspectiveRequest,
    TwoPointPerspectiveResponse,
    TextureProjectionRequest,
    TextureProjectionResponse,
    CurveWeldRequest,
    CurveArcCreateRequest,
    CurveResponse,
    SectionPlaneCreateRequest,
    SectionPlaneSliceRequest,
    SUSectionPlaneResponse,
    FaceStyleResolveRequest,
    GlassMaterialRequest,
    FaceStyleResponse,
    SceneCreateRequest,
    SceneAnimationTimelineRequest,
    SceneAnimationResponse,
    ShadowInfoRequest,
    ShadowInfoResponse,
    ScreenTextRequest,
    LeaderTextRequest,
    TextResponse,
    DimensionLinearRequest,
    DimensionLinearResponse,
    GuideLineInfiniteRequest,
    GuidePointCreateRequest,
    GuideLineIntersectRequest,
    InfiniteGuideResponse,
    AlphaMaterialRequest,
    FaceMeRequest,
    AlphaTextureResponse,
    NestedHierarchyResolveRequest,
    WorldToLocalRequest,
    NestedHierarchyResponse,
    DimensionRadialRequest,
    DimensionRadialResponse,
    FogStyleRequest,
    AutoFogRequest,
    FogStyleResponse,
    MeshSmoothingRequest,
    MeshSmoothingResponse,
    SectionHatchRequest,
    SectionHatchResponse,
    GeoReferenceRequest,
    LocalToGeoRequest,
    GeoReferenceResponse,

    FollowMeRequest,
    FollowMeResponse,
    ArcRequest,
    ArcResponse,
    RotateTransformRequest,
    RotateTransformResponse,
    SafetyAuditResponse,
    ImportObjRequest,
    ImportObjResponse,

    SectionPlaneRequest,
    SectionPlaneResponse,
    GuideLineRequest,
    GuidePointRequest,
    GuidesResponse,
    BooleanOperationRequest,
    BooleanOperationResponse,
    OffsetFaceRequest,
    OffsetFaceResponse,
    ExecutivePdfExportRequest,
    ExecutivePdfExportResponse,

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
    AssemblyStepsResponse,
    ExportAssemblyManualRequest,
    ExportAssemblyManualResponse,
    ExportDrawing2DRequest,
    ExportDrawing2DResponse,
    SolarStudyRequest,
    SolarStudyResponse,
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


@router.get(
    "/assembly-steps",
    response_model=AssemblyStepsResponse,
    summary="Calcula as etapas sequenciais de montagem (Frente 26)",
)
async def get_assembly_steps(
    controller: SceneController = Depends(get_controller),
) -> AssemblyStepsResponse:
    return await controller.get_assembly_steps()


@router.post(
    "/export/assembly-manual",
    response_model=ExportAssemblyManualResponse,
    summary="Gera manual técnico de montagem em HTML (Frente 26)",
)
async def export_assembly_manual(
    body: ExportAssemblyManualRequest,
    controller: SceneController = Depends(get_controller),
) -> ExportAssemblyManualResponse:
    return await controller.export_assembly_manual(body)


@router.post(
    "/export/drawing-2d",
    response_model=ExportDrawing2DResponse,
    summary="Exporta desenho técnico 2D vetorial em SVG (Frente 27)",
)
async def export_drawing_2d(
    body: ExportDrawing2DRequest,
    controller: SceneController = Depends(get_controller),
) -> ExportDrawing2DResponse:
    return await controller.export_drawing_2d(body)


@router.post(
    "/solar-study",
    response_model=SolarStudyResponse,
    summary="Calcula estudo solar e insolação NBR 16071 (Frente 28)",
)
async def calculate_solar_study(
    body: SolarStudyRequest,
    controller: SceneController = Depends(get_controller),
) -> SolarStudyResponse:
    return await controller.calculate_solar_study(body)


# ============================================================================
# Frente 17: Planos e Cortes de Seção (SectionPlane)
# ============================================================================

@router.post(
    "/section-plane",
    response_model=SectionPlaneResponse,
    summary="Adiciona um Plano de Corte de Seção (Frente 17)",
)
async def add_section_plane(
    body: SectionPlaneRequest,
    controller: SceneController = Depends(get_controller),
) -> SectionPlaneResponse:
    return await controller.add_section_plane(body)


@router.get(
    "/section-planes",
    response_model=list[SectionPlaneResponse],
    summary="Lista todos os Planos de Corte de Seção da cena (Frente 17)",
)
async def get_section_planes(
    controller: SceneController = Depends(get_controller),
) -> list[SectionPlaneResponse]:
    return await controller.get_section_planes()


# ============================================================================
# Frente 18: Linhas de Guia e Pontos de Construção (Tape Measure)
# ============================================================================

@router.post(
    "/geometry/guide-line",
    summary="Adiciona Linha de Guia / Tape Measure (Frente 18)",
)
async def add_guide_line(
    body: GuideLineRequest,
    controller: SceneController = Depends(get_controller),
) -> dict:
    return await controller.add_guide_line(body)


@router.post(
    "/geometry/guide-point",
    summary="Adiciona Ponto de Construção (Frente 18)",
)
async def add_guide_point(
    body: GuidePointRequest,
    controller: SceneController = Depends(get_controller),
) -> dict:
    return await controller.add_guide_point(body)


@router.get(
    "/geometry/guides",
    response_model=GuidesResponse,
    summary="Retorna linhas de guia e pontos da cena (Frente 18)",
)
async def get_guides(
    controller: SceneController = Depends(get_controller),
) -> GuidesResponse:
    return await controller.get_guides()


# ============================================================================
# Frente 25: Operações Booleanas de Sólidos (CSG / Solid Tools)
# ============================================================================

@router.post(
    "/geometry/boolean-operation",
    response_model=BooleanOperationResponse,
    summary="Aplica operação booleana sólida CSG (Frente 25)",
)
async def apply_boolean_operation(
    body: BooleanOperationRequest,
    controller: SceneController = Depends(get_controller),
) -> BooleanOperationResponse:
    return await controller.apply_boolean_operation(body)


# ============================================================================
# Frente 29: Exportador Executivo de Proposta Comercial em PDF Vetorial
# ============================================================================

@router.post(
    "/export/executive-pdf",
    response_model=ExecutivePdfExportResponse,
    summary="Exporta proposta executiva e prancha técnica em PDF (Frente 29)",
)
async def export_executive_pdf(
    body: ExecutivePdfExportRequest,
    controller: SceneController = Depends(get_controller),
) -> ExecutivePdfExportResponse:
    return await controller.export_executive_pdf(body)


# ============================================================================
# Frente 30: Ferramenta de Offset / Equidistância 2D/3D (Ferramenta F)
# ============================================================================

@router.post(
    "/geometry/offset",
    response_model=OffsetFaceResponse,
    summary="Gera face ou moldura equidistante via Offset (Frente 30)",
)
async def add_offset_face(
    body: OffsetFaceRequest,
    controller: SceneController = Depends(get_controller),
) -> OffsetFaceResponse:
    return await controller.add_offset_face(body)


# ============================================================================
# Frentes 31 a 35: Follow Me, Arcos 3D, Rotação, Auditoria NBR 16071 e OBJ
# ============================================================================

@router.post(
    "/geometry/follow-me",
    response_model=FollowMeResponse,
    summary="Extrusão 3D Follow Me ao longo de caminho (Frente 31)",
)
async def create_follow_me_geometry(
    body: FollowMeRequest,
    controller: SceneController = Depends(get_controller),
) -> FollowMeResponse:
    return await controller.create_follow_me_geometry(body)


@router.post(
    "/geometry/arc",
    response_model=ArcResponse,
    summary="Gera arco circular 3D paramétrico (Frente 32)",
)
async def create_arc_geometry(
    body: ArcRequest,
    controller: SceneController = Depends(get_controller),
) -> ArcResponse:
    return await controller.create_arc_geometry(body)


@router.post(
    "/geometry/rotate",
    response_model=RotateTransformResponse,
    summary="Aplica rotação analítica com transferidor (Frente 33)",
)
async def apply_rotation_transform(
    body: RotateTransformRequest,
    controller: SceneController = Depends(get_controller),
) -> RotateTransformResponse:
    return await controller.apply_rotation_transform(body)


@router.get(
    "/safety-audit-nbr16071",
    response_model=SafetyAuditResponse,
    summary="Audita conformidade normativa de segurança infantil NBR 16071 (Frente 34)",
)
async def audit_nbr16071_safety(
    controller: SceneController = Depends(get_controller),
) -> SafetyAuditResponse:
    return await controller.audit_nbr16071_safety()


@router.post(
    "/import-obj",
    response_model=ImportObjResponse,
    summary="Importa modelo Wavefront OBJ e converte para B-Rep no .SKP (Frente 35)",
)
async def import_obj_geometry(
    body: ImportObjRequest,
    controller: SceneController = Depends(get_controller),
) -> ImportObjResponse:
    return await controller.import_obj_geometry(body)


# ============================================================================
# Frentes 36 a 40: Nesting 1D/2D, Terrenos, FEA Estrutural, Escala e CAM DXF
# ============================================================================

@router.post(
    "/factory/nesting-optimizer",
    response_model=NestingResponse,
    summary="Calcula otimização de plano de corte de barras e toras (Frente 36)",
)
async def calculate_nesting_optimizer(
    body: NestingRequest,
    controller: SceneController = Depends(get_controller),
) -> NestingResponse:
    return await controller.calculate_nesting_optimizer(body)


@router.post(
    "/geometry/terrain",
    response_model=TerrainResponse,
    summary="Gera terreno paramétrico e malha topográfica Sandbox (Frente 37)",
)
async def create_terrain_geometry(
    body: TerrainRequest,
    controller: SceneController = Depends(get_controller),
) -> TerrainResponse:
    return await controller.create_terrain_geometry(body)


@router.post(
    "/engineering/structural-analysis",
    response_model=StructuralAnalysisResponse,
    summary="Calcula tensões, flecha e estabilidade de viga NBR 7190 (Frente 38)",
)
async def calculate_structural_analysis(
    body: StructuralAnalysisRequest,
    controller: SceneController = Depends(get_controller),
) -> StructuralAnalysisResponse:
    return await controller.calculate_structural_analysis(body)


@router.post(
    "/geometry/scale",
    response_model=ScaleResponse,
    summary="Aplica escala paramétrica à instância (Frente 39)",
)
async def apply_scale_transform(
    body: ScaleRequest,
    controller: SceneController = Depends(get_controller),
) -> ScaleResponse:
    return await controller.apply_scale_transform(body)


@router.post(
    "/export/cam-dxf",
    response_model=ExportCamDxfResponse,
    summary="Exporta contornos para máquinas CNC e Corte a Laser em DXF (Frente 40)",
)
async def export_cam_dxf(
    body: ExportCamDxfRequest,
    controller: SceneController = Depends(get_controller),
) -> ExportCamDxfResponse:
    return await controller.export_cam_dxf(body)


@router.post(
    "/camera-path",
    response_model=CameraPathResponse,
    summary="Interpola sobrevoo de camera Catmull-Rom (Frente 41)",
)
async def calculate_camera_path(
    body: CameraPathRequest,
    controller: SceneController = Depends(get_controller),
) -> CameraPathResponse:
    return await controller.calculate_camera_path(body)


@router.post(
    "/export/point-cloud-xyz",
    response_model=PointCloudExportResponse,
    summary="Exporta nuvem de pontos LiDAR ASCII XYZ (Frente 42)",
)
async def export_point_cloud_xyz(
    body: PointCloudExportRequest,
    controller: SceneController = Depends(get_controller),
) -> PointCloudExportResponse:
    return await controller.export_point_cloud_xyz(body)


@router.post(
    "/maintenance-plan",
    response_model=MaintenancePlanResponse,
    summary="Gera plano normativo de manutencao preventiva NBR 16071-7 (Frente 43)",
)
async def generate_maintenance_plan(
    body: MaintenancePlanRequest,
    controller: SceneController = Depends(get_controller),
) -> MaintenancePlanResponse:
    return await controller.generate_maintenance_plan(body)


@router.post(
    "/geometry/mirror",
    response_model=MirrorResponse,
    summary="Aplica espelhamento e simetria 3D de Householder (Frente 44)",
)
async def apply_mirror_transform(
    body: MirrorRequest,
    controller: SceneController = Depends(get_controller),
) -> MirrorResponse:
    return await controller.apply_mirror_transform(body)


@router.post(
    "/export/qr-tag-svg",
    response_model=QrTagExportResponse,
    summary="Exporta placa tecnica com QR Code em SVG (Frente 45)",
)
async def export_qr_tag_svg(
    body: QrTagExportRequest,
    controller: SceneController = Depends(get_controller),
) -> QrTagExportResponse:
    return await controller.export_qr_tag_svg(body)


@router.post(
    "/engineering/swing-kinematics",
    response_model=SwingKinematicsResponse,
    summary="Simula cinematica e envelope de impacto de balanco NBR 16071 (Frente 46)",
)
async def simulate_swing_kinematics(
    body: SwingKinematicsRequest,
    controller: SceneController = Depends(get_controller),
) -> SwingKinematicsResponse:
    return await controller.simulate_swing_kinematics(body)


@router.post(
    "/export/art-report-pdf",
    response_model=ArtReportResponse,
    summary="Gera minuta executiva de ART / RRT em PDF vetorial (Frente 47)",
)
async def generate_art_pdf(
    body: ArtReportRequest,
    controller: SceneController = Depends(get_controller),
) -> ArtReportResponse:
    return await controller.generate_art_pdf(body)


@router.post(
    "/engineering/wall-thickness",
    response_model=WallThicknessResponse,
    summary="Inspeciona espessura de paredes de pecas rotomoldadas (Frente 48)",
)
async def inspect_wall_thickness(
    body: WallThicknessRequest,
    controller: SceneController = Depends(get_controller),
) -> WallThicknessResponse:
    return await controller.inspect_wall_thickness(body)


@router.post(
    "/factory/cargo-load",
    response_model=CargoLoadResponse,
    summary="Otimiza cubagem e carregamento de carga 3D no transporte (Frente 49)",
)
async def optimize_cargo_load(
    body: CargoLoadRequest,
    controller: SceneController = Depends(get_controller),
) -> CargoLoadResponse:
    return await controller.optimize_cargo_load(body)


@router.post(
    "/export/technical-sketch-svg",
    response_model=TechnicalSketchResponse,
    summary="Exporta esboco arquitetonico estilizado com overshoot em SVG (Frente 50)",
)
async def generate_technical_sketch(
    body: TechnicalSketchRequest,
    controller: SceneController = Depends(get_controller),
) -> TechnicalSketchResponse:
    return await controller.generate_technical_sketch(body)


@router.post(
    "/geometry/spiral-tube",
    response_model=SpiralTubeResponse,
    summary="Gera geometria 3D de toboga espiral helicoidal (Frente 51)",
)
async def generate_spiral_tube(
    body: SpiralTubeRequest,
    controller: SceneController = Depends(get_controller),
) -> SpiralTubeResponse:
    return await controller.generate_spiral_tube(body)


@router.post(
    "/engineering/overturn-stability",
    response_model=OverturnStabilityResponse,
    summary="Calcula estabilidade ao tombamento sob vento e empuxo (Frente 52)",
)
async def calculate_overturn_stability(
    body: OverturnStabilityRequest,
    controller: SceneController = Depends(get_controller),
) -> OverturnStabilityResponse:
    return await controller.calculate_overturn_stability(body)


@router.post(
    "/export/field-inspection-html",
    response_model=FieldInspectionResponse,
    summary="Exporta checklist de inspecao de campo NBR 16071-7 em HTML5 offline (Frente 53)",
)
async def export_field_inspection_html(
    body: FieldInspectionRequest,
    controller: SceneController = Depends(get_controller),
) -> FieldInspectionResponse:
    return await controller.export_field_inspection_html(body)


@router.post(
    "/geometry/angle-dimension",
    response_model=AngleDimensionResponse,
    summary="Calcula cota angular e arco grafico 3D entre 3 pontos (Frente 54)",
)
async def calculate_angle_dimension(
    body: AngleDimensionRequest,
    controller: SceneController = Depends(get_controller),
) -> AngleDimensionResponse:
    return await controller.calculate_angle_dimension(body)


@router.post(
    "/engineering/fastener-torque",
    response_model=FastenerTorqueResponse,
    summary="Dimensiona fixador e calcula torque normativo NBR 7190 / ISO 898 (Frente 55)",
)
async def calculate_fastener_torque(
    body: FastenerTorqueRequest,
    controller: SceneController = Depends(get_controller),
) -> FastenerTorqueResponse:
    return await controller.calculate_fastener_torque(body)


@router.post(
    "/geometry/hip-roof",
    response_model=HipRoofResponse,
    summary="Gera geometria 3D de telhado de 4 aguas ou piramidal (Frente 56)",
)
async def generate_hip_roof(
    body: HipRoofRequest,
    controller: SceneController = Depends(get_controller),
) -> HipRoofResponse:
    return await controller.generate_hip_roof(body)


@router.post(
    "/engineering/hic-impact",
    response_model=HicResponse,
    summary="Simula impacto HIC e piso amortecedor NBR 16071-3 (Frente 57)",
)
async def simulate_hic_impact(
    body: HicRequest,
    controller: SceneController = Depends(get_controller),
) -> HicResponse:
    return await controller.simulate_hic_impact(body)


@router.post(
    "/export/zebra-label",
    response_model=ZebraLabelResponse,
    summary="Exporta etiqueta termica industrial Zebra ZPL II e SVG (Frente 58)",
)
async def export_zebra_label(
    body: ZebraLabelRequest,
    controller: SceneController = Depends(get_controller),
) -> ZebraLabelResponse:
    return await controller.export_zebra_label(body)


@router.post(
    "/geometry/exploded-trails",
    response_model=ExplodedTrailsResponse,
    summary="Calcula linhas tracejadas de trajetoria para vista explodida (Frente 59)",
)
async def calculate_exploded_trails(
    body: ExplodedTrailsRequest,
    controller: SceneController = Depends(get_controller),
) -> ExplodedTrailsResponse:
    return await controller.calculate_exploded_trails(body)


@router.post(
    "/engineering/carbon-footprint",
    response_model=CarbonFootprintResponse,
    summary="Calcula balanco de carbono e sustentabilidade florestal (Frente 60)",
)
async def calculate_carbon_footprint(
    body: CarbonFootprintRequest,
    controller: SceneController = Depends(get_controller),
) -> CarbonFootprintResponse:
    return await controller.calculate_carbon_footprint(body)


@router.post(
    "/attributes/dictionary",
    response_model=AttributeDictionaryResponse,
    summary="Manipula dicionarios de atributos nativos e componentes dinamicos (Frente 61)",
)
async def manage_attribute_dictionary(
    body: AttributeDictionaryRequest,
    controller: SceneController = Depends(get_controller),
) -> AttributeDictionaryResponse:
    return await controller.manage_attribute_dictionary(body)


@router.post(
    "/tags/folder",
    response_model=TagFolderResponse,
    summary="Cria e gerencia pastas de tags hierarquicas (Frente 62)",
)
async def manage_tag_folder(
    body: TagFolderRequest,
    controller: SceneController = Depends(get_controller),
) -> TagFolderResponse:
    return await controller.manage_tag_folder(body)


@router.post(
    "/styles/edge-rendering",
    response_model=EdgeStylesResponse,
    summary="Configura opcoes nativas de estilos de arestas do SketchUp (Frente 63)",
)
async def configure_edge_styles(
    body: EdgeStylesRequest,
    controller: SceneController = Depends(get_controller),
) -> EdgeStylesResponse:
    return await controller.configure_edge_styles(body)


@router.post(
    "/camera/two-point-perspective",
    response_model=TwoPointPerspectiveResponse,
    summary="Calcula matriz de camera com Perspectiva de Dois Pontos (Frente 64)",
)
async def calculate_two_point_perspective(
    body: TwoPointPerspectiveRequest,
    controller: SceneController = Depends(get_controller),
) -> TwoPointPerspectiveResponse:
    return await controller.calculate_two_point_perspective(body)


@router.post(
    "/materials/project-uv",
    response_model=TextureProjectionResponse,
    summary="Calcula coordenadas UV analiticas para projecao planar ou cilindrica (Frente 65)",
)
async def project_texture_uv(
    body: TextureProjectionRequest,
    controller: SceneController = Depends(get_controller),
) -> TextureProjectionResponse:
    return await controller.project_texture_uv(body)


@router.post(
    "/curves/weld",
    response_model=CurveResponse,
    summary="Solda arestas contiguas em curvas SUCurveRef (Frente 66)",
)
async def weld_curve_edges(
    body: CurveWeldRequest,
    controller: SceneController = Depends(get_controller),
) -> CurveResponse:
    return await controller.weld_curve_edges(body)


@router.post(
    "/curves/arc",
    response_model=CurveResponse,
    summary="Cria arco analitico parametrico SUArcCurveRef (Frente 66)",
)
async def create_arc_curve(
    body: CurveArcCreateRequest,
    controller: SceneController = Depends(get_controller),
) -> CurveResponse:
    return await controller.create_arc_curve(body)


@router.post(
    "/section-planes/create",
    response_model=SUSectionPlaneResponse,
    summary="Cria ou configura plano de corte SUSectionPlaneRef (Frente 67)",
)
async def create_or_reverse_section_plane(
    body: SectionPlaneCreateRequest,
    controller: SceneController = Depends(get_controller),
) -> SUSectionPlaneResponse:
    return await controller.create_or_reverse_section_plane(body)


@router.post(
    "/section-planes/slice",
    response_model=SUSectionPlaneResponse,
    summary="Fatia malha 3D gerando contornos e loops de corte transversal (Frente 67)",
)
async def slice_geometry_by_plane(
    body: SectionPlaneSliceRequest,
    controller: SceneController = Depends(get_controller),
) -> SUSectionPlaneResponse:
    return await controller.slice_geometry_by_plane(body)


@router.post(
    "/styles/face-rendering",
    response_model=FaceStyleResponse,
    summary="Resolve shaders e propriedades PBR de estilos de faces (Frente 68)",
)
async def resolve_face_render_style(
    body: FaceStyleResolveRequest,
    controller: SceneController = Depends(get_controller),
) -> FaceStyleResponse:
    return await controller.resolve_face_render_style(body)


@router.post(
    "/materials/glass-pbr",
    response_model=FaceStyleResponse,
    summary="Cria material de vidro fisico PBR (Frente 68)",
)
async def create_glass_pbr_material(
    body: GlassMaterialRequest,
    controller: SceneController = Depends(get_controller),
) -> FaceStyleResponse:
    return await controller.create_glass_pbr_material(body)


@router.post(
    "/scenes/create",
    response_model=SceneAnimationResponse,
    summary="Cria definicao canonica de cena SUSceneRef (Frente 69)",
)
async def create_presentation_scene(
    body: SceneCreateRequest,
    controller: SceneController = Depends(get_controller),
) -> SceneAnimationResponse:
    return await controller.create_presentation_scene(body)


@router.post(
    "/scenes/animate",
    response_model=SceneAnimationResponse,
    summary="Gera timeline continua de transicao entre cenas (Frente 69)",
)
async def generate_scene_animation_timeline(
    body: SceneAnimationTimelineRequest,
    controller: SceneController = Depends(get_controller),
) -> SceneAnimationResponse:
    return await controller.generate_scene_animation_timeline(body)


@router.post(
    "/shadows/heliodon",
    response_model=ShadowInfoResponse,
    summary="Calcula parametros de iluminacao solar e sombreamento SUShadowInfoRef (Frente 70)",
)
async def calculate_shadow_and_sun_info(
    body: ShadowInfoRequest,
    controller: SceneController = Depends(get_controller),
) -> ShadowInfoResponse:
    return await controller.calculate_shadow_and_sun_info(body)


@router.post(
    "/text/screen",
    response_model=TextResponse,
    summary="Cria anotacao de texto 2D fixada em tela HUD (Frente 71)",
)
async def create_screen_text(
    body: ScreenTextRequest,
    controller: SceneController = Depends(get_controller),
) -> TextResponse:
    return await controller.create_screen_text(body)


@router.post(
    "/text/leader",
    response_model=TextResponse,
    summary="Cria rotulo anotativo com linha de chamada 3D (Frente 71)",
)
async def create_leader_text(
    body: LeaderTextRequest,
    controller: SceneController = Depends(get_controller),
) -> TextResponse:
    return await controller.create_leader_text(body)


@router.post(
    "/dimensions/linear",
    response_model=DimensionLinearResponse,
    summary="Calcula cota linear com linhas de extensao e tiques arquitetonicos (Frente 72)",
)
async def create_dimension_linear(
    body: DimensionLinearRequest,
    controller: SceneController = Depends(get_controller),
) -> DimensionLinearResponse:
    return await controller.create_dimension_linear(body)


@router.post(
    "/guides/infinite",
    response_model=InfiniteGuideResponse,
    summary="Cria linha de guia infinita ou finita SUGuideLineRef (Frente 73)",
)
async def create_guide_line_infinite(
    body: GuideLineInfiniteRequest,
    controller: SceneController = Depends(get_controller),
) -> InfiniteGuideResponse:
    return await controller.create_guide_line_infinite(body)


@router.post(
    "/guides/point",
    response_model=InfiniteGuideResponse,
    summary="Cria ponto de construcao SUGuidePointRef (Frente 73)",
)
async def create_guide_point(
    body: GuidePointCreateRequest,
    controller: SceneController = Depends(get_controller),
) -> InfiniteGuideResponse:
    return await controller.create_guide_point(body)


@router.post(
    "/guides/intersect",
    response_model=InfiniteGuideResponse,
    summary="Calcula intersecao 3D analitica entre duas linhas de guia (Frente 73)",
)
async def intersect_guide_lines(
    body: GuideLineIntersectRequest,
    controller: SceneController = Depends(get_controller),
) -> InfiniteGuideResponse:
    return await controller.intersect_guide_lines(body)


@router.post(
    "/materials/alpha-mask",
    response_model=AlphaTextureResponse,
    summary="Configura material com canal alfa e recorte de profundidade (Frente 74)",
)
async def configure_alpha_material(
    body: AlphaMaterialRequest,
    controller: SceneController = Depends(get_controller),
) -> AlphaTextureResponse:
    return await controller.configure_alpha_material(body)


@router.post(
    "/components/face-me",
    response_model=AlphaTextureResponse,
    summary="Calcula matriz de rotacao Face-Me para componente de vegetacao/figura humana (Frente 74)",
)
async def calculate_face_me_matrix(
    body: FaceMeRequest,
    controller: SceneController = Depends(get_controller),
) -> AlphaTextureResponse:
    return await controller.calculate_face_me_matrix(body)


@router.post(
    "/hierarchy/resolve",
    response_model=NestedHierarchyResponse,
    summary="Resolve matriz mundial acumulada e decomposicao de no aninhado (Frente 75)",
)
async def resolve_nested_hierarchy_node(
    body: NestedHierarchyResolveRequest,
    controller: SceneController = Depends(get_controller),
) -> NestedHierarchyResponse:
    return await controller.resolve_nested_hierarchy_node(body)


@router.post(
    "/hierarchy/world-to-local",
    response_model=NestedHierarchyResponse,
    summary="Converte matriz mundial de edicao para matriz local de no aninhado (Frente 75)",
)
async def convert_world_transform_to_local(
    body: WorldToLocalRequest,
    controller: SceneController = Depends(get_controller),
) -> NestedHierarchyResponse:
    return await controller.convert_world_transform_to_local(body)


@router.post(
    "/dimensions/radial",
    response_model=DimensionRadialResponse,
    summary="Calcula cota radial ou diametrica SUDimensionRadialRef (Frente 76)",
)
async def create_dimension_radial(
    body: DimensionRadialRequest,
    controller: SceneController = Depends(get_controller),
) -> DimensionRadialResponse:
    return await controller.create_dimension_radial(body)


@router.post(
    "/styles/fog",
    response_model=FogStyleResponse,
    summary="Configura parametros de nevoa de cena SUStyleFog (Frente 77)",
)
async def configure_fog_style(
    body: FogStyleRequest,
    controller: SceneController = Depends(get_controller),
) -> FogStyleResponse:
    return await controller.configure_fog_style(body)


@router.post(
    "/styles/auto-fog",
    response_model=FogStyleResponse,
    summary="Calcula parametros ideais de nevoa a partir da Bounding Box (Frente 77)",
)
async def calculate_auto_fog_from_bbox(
    body: AutoFogRequest,
    controller: SceneController = Depends(get_controller),
) -> FogStyleResponse:
    return await controller.calculate_auto_fog_from_bbox(body)


@router.post(
    "/geometry/smoothing",
    response_model=MeshSmoothingResponse,
    summary="Calcula suavizacao de arestas Soft & Smooth e normais de vertices (Frente 78)",
)
async def process_mesh_smoothing(
    body: MeshSmoothingRequest,
    controller: SceneController = Depends(get_controller),
) -> MeshSmoothingResponse:
    return await controller.process_mesh_smoothing(body)


@router.post(
    "/section-planes/hatch",
    response_model=SectionHatchResponse,
    summary="Gera hachuras graficas normativas NBR 6492 / ISO 128 em cortes (Frente 79)",
)
async def generate_section_hatch_lines(
    body: SectionHatchRequest,
    controller: SceneController = Depends(get_controller),
) -> SectionHatchResponse:
    return await controller.generate_section_hatch_lines(body)


@router.post(
    "/geo/reference",
    response_model=GeoReferenceResponse,
    summary="Define georreferenciamento e calcula coordenadas UTM WGS84 (Frente 80)",
)
async def set_geo_location(
    body: GeoReferenceRequest,
    controller: SceneController = Depends(get_controller),
) -> GeoReferenceResponse:
    return await controller.set_geo_location(body)


@router.post(
    "/geo/local-to-wgs84",
    response_model=GeoReferenceResponse,
    summary="Converte ponto 3D local em coordenadas geograficas WGS84 (Frente 80)",
)
async def local_point_to_wgs84(
    body: LocalToGeoRequest,
    controller: SceneController = Depends(get_controller),
) -> GeoReferenceResponse:
    return await controller.local_point_to_wgs84(body)
