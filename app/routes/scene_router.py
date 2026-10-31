"""
Rotas do modulo de cena/visualizador 3D. So roteamento -- declara
path, metodo, schema de entrada/saida, e delega pro controller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Response, UploadFile, status

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
    PolyMeshHolesRequest,
    PolyMeshResponse,
    AlignViewRequest,
    AlignViewResponse,
    BackgroundSkyStyleRequest,
    BackgroundSkyStyleResponse,
    DimensionToleranceRequest,
    DimensionToleranceResponse,
    UndoRedoRecordRequest,
    UndoRedoActionResponse,
    UndoRedoStatusResponse,
    SubDSubdivisionRequest,
    SubDMeshResponse,
    SectionDimensionRequest,
    SectionDimensionResponse,
    PanoramaSphericalRequest,
    PanoramaSphericalResponse,
    ClashDetectionRequest,
    ClashDetectionResponse,
    MassPropertiesRequest,
    MassPropertiesResponse,
    SolidShellRequest,
    SolidShellResponse,
    PhotometricSpotLightRequest,
    PhotometricSpotLightResponse,
    PipingRouteRequest,
    PipingRouteResponse,
    CameraAnimationPathRequest,
    CameraAnimationPathResponse,
    CamCutlistRequest,
    CamCutlistResponse,
    ArchitecturalWallRequest,
    ArchitecturalWallResponse,
    SheetMetalUnfoldRequest,
    SheetMetalUnfoldResponse,
    ShadowCastingRequest,
    ShadowCastingResponse,
    WaterMaterialConfigRequest,
    WaterMaterialConfigResponse,
    SkpLODChainRequest,
    SkpLODChainResponse,
    StairGeneratorRequest,
    StairGeneratorResponse,
    VoronoiPanelRequest,
    VoronoiPanelResponse,
    WindPressureRequest,
    WindPressureResponse,
    AtmosphericSkyRequest,
    AtmosphericSkyResponse,
    IFC4BimExportRequest,
    IFC4BimExportResponse,
    RigidBodyPhysicsRequest,
    RigidBodyPhysicsResponse,
    Slicing3dPrintRequest,
    Slicing3dPrintResponse,
    RetainingWallRequest,
    RetainingWallResponse,
    HydraulicPipingRequest,
    HydraulicPipingResponse,
    ElectricalConduitRequest,
    ElectricalConduitResponse,
    ThermalComfortRequest,
    ThermalComfortResponse,
    RoomAcousticsRequest,
    RoomAcousticsResponse,
    DaylightFactorRequest,
    DaylightFactorResponse,
    SteelProfileRequest,
    SteelProfileResponse,
    Bim5dSinapiCostRequest,
    Bim5dSinapiCostResponse,
    StormwaterDrainageRequest,
    StormwaterDrainageResponse,
    PermeablePavementRequest,
    PermeablePavementResponse,
    SewerNetworkGravityRequest,
    SewerNetworkGravityResponse,
    DetentionBasinHydrologyRequest,
    DetentionBasinHydrologyResponse,
    EarthworkBrucknerRequest,
    EarthworkBrucknerResponse,
    SlopeStabilityBishopRequest,
    SlopeStabilityBishopResponse,
    DeepFoundationsPilesRequest,
    DeepFoundationsPilesResponse,
    ShallowFootingsRequest,
    ShallowFootingsResponse,
    GabionRetainingWallRequest,
    GabionRetainingWallResponse,
    ConcreteFormworkShoringRequest,
    ConcreteFormworkShoringResponse,
    ReinforcedConcreteBeamRequest,
    ReinforcedConcreteBeamResponse,
    WaffleSlabRequest,
    WaffleSlabResponse,
    PrestressedConcreteRequest,
    PrestressedConcreteResponse,
    GlulamCltTimberRequest,
    GlulamCltTimberResponse,
    SpaceTrussRequest,
    SpaceTrussResponse,
    FuelGasPipingRequest,
    FuelGasPipingResponse,
    LightningProtectionSpdaRequest,
    LightningProtectionSpdaResponse,
    FireEgressRouteRequest,
    FireEgressRouteResponse,
    HvacThermalLoadRequest,
    HvacThermalLoadResponse,
    PhotometricLumenDesignRequest,
    PhotometricLumenDesignResponse,
    SolarPhotovoltaicArrayRequest,
    SolarPhotovoltaicArrayResponse,
    NaturalVentilationRequest,
    NaturalVentilationResponse,
    GlazingFenestrationRequest,
    GlazingFenestrationResponse,
    VentilatedFacadeRequest,
    VentilatedFacadeResponse,
    MiniWindCfd2dRequest,
    MiniWindCfd2dResponse,
    Bim4dGanttScheduleRequest,
    Bim4dGanttScheduleResponse,
    Bim7dAssetManagementCobieRequest,
    Bim7dAssetManagementCobieResponse,
    ConstructionSiteLogisticsRequest,
    ConstructionSiteLogisticsResponse,
    UniversalAccessibilityRequest,
    UniversalAccessibilityResponse,
    LifeCycleAssessmentRequest,
    LifeCycleAssessmentResponse,
    PositionCameraNativeRequest,
    PositionCameraNativeResponse,
    LookAroundNativeRequest,
    LookAroundNativeResponse,
    WalkStepNativeRequest,
    WalkStepNativeResponse,
    SandboxSmooveRequest,
    SandboxSmooveResponse,
    SandboxStampRequest,
    SandboxStampResponse,
    SandboxDrapeRequest,
    SandboxDrapeResponse,
    SandboxFlipEdgeRequest,
    SandboxFlipEdgeResponse,
    MatchPhotoCalibrateRequest,
    MatchPhotoCalibrateResponse,
    WatermarkStyleConfigureRequest,
    WatermarkStyleConfigureResponse,
    DynamicComponentInteractRequest,
    DynamicComponentInteractResponse,
    TrimbleSolidToolsRequest,
    TrimbleSolidToolsResponse,
    IfcClassifyComponentRequest,
    IfcClassifyComponentResponse,
    IfcAuditRequest,
    IfcAuditResponse,
    ThreeDTextGenerateRequest,
    ThreeDTextGenerateResponse,
    GenerateReportRequest,
    GenerateReportResponse,
    AxesCustomSetRequest,
    AxesCustomSetResponse,
    AxesAlignFaceRequest,
    AxesAlignFaceResponse,
    AxesResetResponse,
    EntityInspectEdgeRequest,
    EntityInspectEdgeResponse,
    EntityInspectFaceRequest,
    EntityInspectFaceResponse,
    EntityInspectSolidRequest,
    EntityInspectSolidResponse,
    ComponentEditModeRequest,
    ComponentEditModeResponse,
    ModelUnitsConfigRequest,
    ModelUnitsConfigResponse,
    ModelUnitsFormatRequest,
    ModelUnitsFormatResponse,
    TexturePinTransformRequest,
    TexturePinTransformResponse,
    ColorByTagApplyRequest,
    ColorByTagApplyResponse,
    PurgeUnusedRequest,
    PurgeUnusedResponse,
    MakeComponentDefinitionRequest,
    MakeComponentDefinitionResponse,
    AdvancedSelectionRequest,
    AdvancedSelectionResponse,
    HiddenGeometryConfigRequest,
    HiddenGeometryConfigResponse,
    ModelStatisticsRequest,
    ModelStatisticsResponse,
    RegularPolygonRequest,
    RegularPolygonResponse,
    FreehandCurveRequest,
    FreehandCurveResponse,
    ReverseOrientFacesRequest,
    ReverseOrientFacesResponse,
    DollyFovLensRequest,
    DollyFovLensResponse,
    IntersectFacesRequest,
    IntersectFacesResponse,
    AxisLockInferenceRequest,
    AxisLockInferenceResponse,
    GroundSkyStyleRequest,
    GroundSkyStyleResponse,
    StampTerrainRequest,
    StampTerrainResponse,
    DrapePathRequest,
    DrapePathResponse,
    SectionCutFillRequest,
    SectionCutFillResponse,
    SoftSmoothEdgesRequest,
    SoftSmoothEdgesResponse,
    EdgeDivideRequest,
    EdgeDivideResponse,
    PushPullCreateFaceRequest,
    PushPullCreateFaceResponse,
    BimIfcPropertySetRequest,
    BimIfcPropertySetResponse,

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


@router.get(
    "/download-skp",
    summary="Exporta e baixa os bytes binários do modelo .skp ativo para gravação in-place via File System Access API",
)
async def download_current_skp(
    controller: SceneController = Depends(get_controller),
) -> Response:
    content = await controller.get_skp_bytes()
    return Response(
        content=content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": 'attachment; filename="modelo.skp"'},
    )


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


@router.post(
    "/polymesh/triangulate",
    response_model=PolyMeshResponse,
    summary="Triangula face plana com furos internos SUPolyMeshRef (Frente 81)",
)
async def triangulate_face_with_holes(
    body: PolyMeshHolesRequest,
    controller: SceneController = Depends(get_controller),
) -> PolyMeshResponse:
    return await controller.triangulate_face_with_holes(body)


@router.post(
    "/camera/align-view",
    response_model=AlignViewResponse,
    summary="Calcula parâmetros de câmera perpendicular à face (Align View) (Frente 82)",
)
async def calculate_align_view(
    body: AlignViewRequest,
    controller: SceneController = Depends(get_controller),
) -> AlignViewResponse:
    return await controller.calculate_align_view(body)


@router.post(
    "/styles/background-sky",
    response_model=BackgroundSkyStyleResponse,
    summary="Configura estilos de céu, solo e horizonte SUStyleRef (Frente 83)",
)
async def configure_background_sky(
    body: BackgroundSkyStyleRequest,
    controller: SceneController = Depends(get_controller),
) -> BackgroundSkyStyleResponse:
    return await controller.configure_background_sky(body)


@router.post(
    "/dimensions/tolerance",
    response_model=DimensionToleranceResponse,
    summary="Calcula tolerâncias dimensionais ISO 2768 / NBR 6492 (Frente 84)",
)
async def calculate_dimension_tolerance(
    body: DimensionToleranceRequest,
    controller: SceneController = Depends(get_controller),
) -> DimensionToleranceResponse:
    return await controller.calculate_dimension_tolerance(body)


@router.post(
    "/history/record",
    response_model=UndoRedoActionResponse,
    summary="Registra operação reversível na pilha transacional (Frente 85)",
)
async def record_undo_operation(
    body: UndoRedoRecordRequest,
    controller: SceneController = Depends(get_controller),
) -> UndoRedoActionResponse:
    return await controller.record_undo_operation(body)


@router.post(
    "/history/undo",
    response_model=UndoRedoActionResponse,
    summary="Desfaz a última operação registrada (Frente 85)",
)
async def execute_undo(
    controller: SceneController = Depends(get_controller),
) -> UndoRedoActionResponse:
    return await controller.execute_undo()


@router.post(
    "/history/redo",
    response_model=UndoRedoActionResponse,
    summary="Refaz a última operação desfeita (Frente 85)",
)
async def execute_redo(
    controller: SceneController = Depends(get_controller),
) -> UndoRedoActionResponse:
    return await controller.execute_redo()


@router.get(
    "/history/status",
    response_model=UndoRedoStatusResponse,
    summary="Retorna histórico e profundidade das pilhas de Undo e Redo (Frente 85)",
)
async def get_undo_redo_history(
    controller: SceneController = Depends(get_controller),
) -> UndoRedoStatusResponse:
    return await controller.get_undo_redo_history()


@router.post(
    "/geometry/subd",
    response_model=SubDMeshResponse,
    summary="Aplica subdivisão Catmull-Clark sobre malha de controle QuadFace (Frente 86)",
)
async def subdivide_quad_mesh(
    body: SubDSubdivisionRequest,
    controller: SceneController = Depends(get_controller),
) -> SubDMeshResponse:
    return await controller.subdivide_quad_mesh(body)


@router.post(
    "/section-planes/dimensions",
    response_model=SectionDimensionResponse,
    summary="Gera cotas ortogonais e marcas de nível NBR 6492 em cortes (Frente 87)",
)
async def generate_auto_section_dimensions(
    body: SectionDimensionRequest,
    controller: SceneController = Depends(get_controller),
) -> SectionDimensionResponse:
    return await controller.generate_auto_section_dimensions(body)


@router.post(
    "/camera/panorama-360",
    response_model=PanoramaSphericalResponse,
    summary="Calcula cubemap de 6 câmeras e malha de raios equirretangulares 360° (Frente 88)",
)
async def calculate_spherical_panorama(
    body: PanoramaSphericalRequest,
    controller: SceneController = Depends(get_controller),
) -> PanoramaSphericalResponse:
    return await controller.calculate_spherical_panorama(body)


@router.post(
    "/clash/detect",
    response_model=ClashDetectionResponse,
    summary="Detecta colisões físicas (Hard Clash) e folgas (Clearance Clash) entre componentes (Frente 89)",
)
async def detect_component_clashes(
    body: ClashDetectionRequest,
    controller: SceneController = Depends(get_controller),
) -> ClashDetectionResponse:
    return await controller.detect_component_clashes(body)


@router.post(
    "/engineering/mass-properties",
    response_model=MassPropertiesResponse,
    summary="Calcula volume, massa, Centro de Gravidade e inércia de malha B-Rep fechada (Frente 90)",
)
async def calculate_mesh_mass_properties(
    body: MassPropertiesRequest,
    controller: SceneController = Depends(get_controller),
) -> MassPropertiesResponse:
    return await controller.calculate_mesh_mass_properties(body)


@router.post(
    "/geometry/solid-shell",
    response_model=SolidShellResponse,
    summary="Gera casca sólida volumétrica B-Rep a partir de superfícies (Frente 91)",
)
async def create_solid_shell(
    body: SolidShellRequest,
    controller: SceneController = Depends(get_controller),
) -> SolidShellResponse:
    return await controller.create_solid_shell(body)


@router.post(
    "/lighting/spotlight",
    response_model=PhotometricSpotLightResponse,
    summary="Configura parâmetros de holofote fotométrico spot Three.js (Frente 92)",
)
async def configure_spot_light(
    body: PhotometricSpotLightRequest,
    controller: SceneController = Depends(get_controller),
) -> PhotometricSpotLightResponse:
    return await controller.configure_spot_light(body)


@router.post(
    "/mep/piping-route",
    response_model=PipingRouteResponse,
    summary="Roteia tubulação e dutos paramétricos 3D com cotovelos e curvas (Frente 93)",
)
async def generate_pipe_route(
    body: PipingRouteRequest,
    controller: SceneController = Depends(get_controller),
) -> PipingRouteResponse:
    return await controller.generate_pipe_route(body)


@router.post(
    "/animation/camera-path",
    response_model=CameraAnimationPathResponse,
    summary="Gera trajetória cinematográfica contínua de câmera (Orbit ou Flythrough) (Frente 94)",
)
async def generate_camera_animation_path(
    body: CameraAnimationPathRequest,
    controller: SceneController = Depends(get_controller),
) -> CameraAnimationPathResponse:
    return await controller.generate_camera_animation_path(body)


@router.post(
    "/factory/cutlist-cnc",
    response_model=CamCutlistResponse,
    summary="Processa peças e produz tabela industrial de corte CNC com CSV (Frente 95)",
)
async def generate_cnc_cutlist(
    body: CamCutlistRequest,
    controller: SceneController = Depends(get_controller),
) -> CamCutlistResponse:
    return await controller.generate_cnc_cutlist(body)


@router.post(
    "/architecture/wall",
    response_model=ArchitecturalWallResponse,
    summary="Gera parede paramétrica 3D com vãos de portas e janelas (Frente 96)",
)
async def generate_wall_with_openings(
    body: ArchitecturalWallRequest,
    controller: SceneController = Depends(get_controller),
) -> ArchitecturalWallResponse:
    return await controller.generate_wall_with_openings(body)


@router.post(
    "/manufacturing/sheet-metal-unfold",
    response_model=SheetMetalUnfoldResponse,
    summary="Calcula o blank planificado e linhas de dobra DIN 6935 (Frente 97)",
)
async def unfold_sheet_metal(
    body: SheetMetalUnfoldRequest,
    controller: SceneController = Depends(get_controller),
) -> SheetMetalUnfoldResponse:
    return await controller.unfold_sheet_metal(body)


@router.post(
    "/shadows/projected-surface",
    response_model=ShadowCastingResponse,
    summary="Calcula projeção de sombra do oclusor sobre o solo ou superfície (Frente 98)",
)
async def calculate_projected_shadow(
    body: ShadowCastingRequest,
    controller: SceneController = Depends(get_controller),
) -> ShadowCastingResponse:
    return await controller.calculate_projected_shadow(body)


@router.post(
    "/materials/water-pbr",
    response_model=WaterMaterialConfigResponse,
    summary="Configura shader PBR de água, ondas Gerstner e cáusticas (Frente 99)",
)
async def configure_water_surface(
    body: WaterMaterialConfigRequest,
    controller: SceneController = Depends(get_controller),
) -> WaterMaterialConfigResponse:
    return await controller.configure_water_surface(body)


@router.post(
    "/geometry/lod-chain",
    response_model=SkpLODChainResponse,
    summary="Gera cadeia de 3 níveis de detalhe (LOD0, LOD1, LOD2) para Three.js (Frente 100)",
)
async def generate_mesh_lod_chain(
    body: SkpLODChainRequest,
    controller: SceneController = Depends(get_controller),
) -> SkpLODChainResponse:
    return await controller.generate_mesh_lod_chain(body)


@router.post(
    "/architecture/stair",
    response_model=StairGeneratorResponse,
    summary="Gera escada paramétrica e dimensionamento ergonômico Blondel NBR 9050 (Frente 101)",
)
async def generate_stair(
    body: StairGeneratorRequest,
    controller: SceneController = Depends(get_controller),
) -> StairGeneratorResponse:
    return await controller.generate_stair(body)


@router.post(
    "/architecture/voronoi-panel",
    response_model=VoronoiPanelResponse,
    summary="Gera painel decorativo ou estrutural com perfurações Voronoi (Frente 102)",
)
async def generate_voronoi_panel(
    body: VoronoiPanelRequest,
    controller: SceneController = Depends(get_controller),
) -> VoronoiPanelResponse:
    return await controller.generate_voronoi_panel(body)


@router.post(
    "/engineering/wind-pressure",
    response_model=WindPressureResponse,
    summary="Calcula pressão dinâmica e forças estáticas de vento NBR 6123 (Frente 103)",
)
async def calculate_wind_pressure(
    body: WindPressureRequest,
    controller: SceneController = Depends(get_controller),
) -> WindPressureResponse:
    return await controller.calculate_wind_pressure(body)


@router.post(
    "/environment/atmospheric-sky",
    response_model=AtmosphericSkyResponse,
    summary="Configura céu físico Rayleigh/Mie e sol Three.js (Frente 104)",
)
async def configure_atmospheric_sky(
    body: AtmosphericSkyRequest,
    controller: SceneController = Depends(get_controller),
) -> AtmosphericSkyResponse:
    return await controller.configure_atmospheric_sky(body)


@router.post(
    "/bim/export-ifc4",
    response_model=IFC4BimExportResponse,
    summary="Compila modelo no formato texto físico STEP ISO-10303-21 IFC4 LOD 350 (Frente 105)",
)
async def export_ifc4_bim(
    body: IFC4BimExportRequest,
    controller: SceneController = Depends(get_controller),
) -> IFC4BimExportResponse:
    return await controller.export_ifc4_bim(body)


@router.post(
    "/physics/simulate-rigid-body",
    response_model=RigidBodyPhysicsResponse,
    summary="Simulação de física newtoniana de corpos rígidos e colisões (Frente 106)",
)
async def simulate_rigid_body_physics(
    body: RigidBodyPhysicsRequest,
    controller: SceneController = Depends(get_controller),
) -> RigidBodyPhysicsResponse:
    return await controller.simulate_rigid_body_physics(body)


@router.post(
    "/manufacturing/slice-3d-print",
    response_model=Slicing3dPrintResponse,
    summary="Fatiamento 3D FDM, estimativa de filamento e exportação STL/3MF (Frente 107)",
)
async def slice_3d_print_fdm(
    body: Slicing3dPrintRequest,
    controller: SceneController = Depends(get_controller),
) -> Slicing3dPrintResponse:
    return await controller.slice_3d_print_fdm(body)


@router.post(
    "/geotechnics/retaining-wall",
    response_model=RetainingWallResponse,
    summary="Cálculo geotécnico e B-Rep de muro de arrimo com estabilidade NBR 11682 (Frente 108)",
)
async def calculate_retaining_wall_stability(
    body: RetainingWallRequest,
    controller: SceneController = Depends(get_controller),
) -> RetainingWallResponse:
    return await controller.calculate_retaining_wall_stability(body)


@router.post(
    "/mep/hydraulic-piping",
    response_model=HydraulicPipingResponse,
    summary="Dimensionamento de tubulação predial e perda de carga NBR 5626 (Frente 109)",
)
async def calculate_hydraulic_piping(
    body: HydraulicPipingRequest,
    controller: SceneController = Depends(get_controller),
) -> HydraulicPipingResponse:
    return await controller.calculate_hydraulic_piping(body)


@router.post(
    "/mep/electrical-conduit",
    response_model=ElectricalConduitResponse,
    summary="Dimensionamento de eletrodutos e taxa de ocupação NBR 5410 (Frente 110)",
)
async def calculate_electrical_conduit(
    body: ElectricalConduitRequest,
    controller: SceneController = Depends(get_controller),
) -> ElectricalConduitResponse:
    return await controller.calculate_electrical_conduit(body)


@router.post(
    "/environment/thermal-comfort",
    response_model=ThermalComfortResponse,
    summary="Transmitância e capacidade térmica de envoltória NBR 15220 / PBE Edifica (Frente 111)",
)
async def calculate_thermal_comfort(
    body: ThermalComfortRequest,
    controller: SceneController = Depends(get_controller),
) -> ThermalComfortResponse:
    return await controller.calculate_thermal_comfort(body)


@router.post(
    "/environment/room-acoustics",
    response_model=RoomAcousticsResponse,
    summary="Tempo de reverberação RT60 e acústica de salas NBR 10152 (Frente 112)",
)
async def calculate_room_acoustics(
    body: RoomAcousticsRequest,
    controller: SceneController = Depends(get_controller),
) -> RoomAcousticsResponse:
    return await controller.calculate_room_acoustics(body)


@router.post(
    "/environment/daylight-factor",
    response_model=DaylightFactorResponse,
    summary="Fator de Luz Diurna (FLD %) e iluminância natural NBR 15215 (Frente 113)",
)
async def calculate_daylight_factor(
    body: DaylightFactorRequest,
    controller: SceneController = Depends(get_controller),
) -> DaylightFactorResponse:
    return await controller.calculate_daylight_factor(body)


@router.post(
    "/structures/steel-profile",
    response_model=SteelProfileResponse,
    summary="Geração de perfil metálico e propriedades de seção NBR 8800 (Frente 114)",
)
async def generate_steel_profile(
    body: SteelProfileRequest,
    controller: SceneController = Depends(get_controller),
) -> SteelProfileResponse:
    return await controller.generate_steel_profile(body)


@router.post(
    "/bim/5d-sinapi-budget",
    response_model=Bim5dSinapiCostResponse,
    summary="Orçamento paramétrico BIM 5D, curva ABC e BDI com tabela SINAPI (Frente 115)",
)
async def calculate_bim_5d_sinapi_budget(
    body: Bim5dSinapiCostRequest,
    controller: SceneController = Depends(get_controller),
) -> Bim5dSinapiCostResponse:
    return await controller.calculate_bim_5d_sinapi_budget(body)


# ---------------------------------------------------------
# Frentes 116 a 145: Endpoints FastAPI
# ---------------------------------------------------------
@router.post("/mep/stormwater-drainage", response_model=StormwaterDrainageResponse, summary="Drenagem pluvial e calhas NBR 10844 (Frente 116)")
async def calculate_stormwater_drainage(body: StormwaterDrainageRequest, controller: SceneController = Depends(get_controller)) -> StormwaterDrainageResponse:
    return await controller.calculate_stormwater_drainage(body)

@router.post("/environment/permeable-pavement", response_model=PermeablePavementResponse, summary="Pavimentação permeável e amortecimento NBR 16416 (Frente 117)")
async def calculate_permeable_pavement(body: PermeablePavementRequest, controller: SceneController = Depends(get_controller)) -> PermeablePavementResponse:
    return await controller.calculate_permeable_pavement(body)

@router.post("/mep/sewer-network", response_model=SewerNetworkGravityResponse, summary="Rede de esgoto sanitário por gravidade NBR 9649 (Frente 118)")
async def calculate_sewer_network(body: SewerNetworkGravityRequest, controller: SceneController = Depends(get_controller)) -> SewerNetworkGravityResponse:
    return await controller.calculate_sewer_network(body)

@router.post("/hydrology/detention-basin", response_model=DetentionBasinHydrologyResponse, summary="Bacia de detenção e amortecimento de cheias (Frente 119)")
async def calculate_detention_basin(body: DetentionBasinHydrologyRequest, controller: SceneController = Depends(get_controller)) -> DetentionBasinHydrologyResponse:
    return await controller.calculate_detention_basin(body)

@router.post("/infrastructure/earthwork-bruckner", response_model=EarthworkBrucknerResponse, summary="Terraplenagem e curva de massas de Brückner (Frente 120)")
async def calculate_earthwork_bruckner(body: EarthworkBrucknerRequest, controller: SceneController = Depends(get_controller)) -> EarthworkBrucknerResponse:
    return await controller.calculate_earthwork_bruckner(body)

@router.post("/geotechnics/slope-stability-bishop", response_model=SlopeStabilityBishopResponse, summary="Estabilidade de taludes método de Bishop (Frente 121)")
async def calculate_slope_stability_bishop(body: SlopeStabilityBishopRequest, controller: SceneController = Depends(get_controller)) -> SlopeStabilityBishopResponse:
    return await controller.calculate_slope_stability_bishop(body)

@router.post("/geotechnics/deep-foundations-piles", response_model=DeepFoundationsPilesResponse, summary="Estacas e fundações profundas NBR 6122 (Frente 122)")
async def calculate_deep_foundations_piles(body: DeepFoundationsPilesRequest, controller: SceneController = Depends(get_controller)) -> DeepFoundationsPilesResponse:
    return await controller.calculate_deep_foundations_piles(body)

@router.post("/structures/shallow-footings", response_model=ShallowFootingsResponse, summary="Sapatas rígidas rasas NBR 6118/6122 (Frente 123)")
async def calculate_shallow_footings(body: ShallowFootingsRequest, controller: SceneController = Depends(get_controller)) -> ShallowFootingsResponse:
    return await controller.calculate_shallow_footings(body)

@router.post("/geotechnics/gabion-wall", response_model=GabionRetainingWallResponse, summary="Muros de contenção de gabião NBR 10328 (Frente 124)")
async def calculate_gabion_wall(body: GabionRetainingWallRequest, controller: SceneController = Depends(get_controller)) -> GabionRetainingWallResponse:
    return await controller.calculate_gabion_wall(body)

@router.post("/structures/concrete-formwork", response_model=ConcreteFormworkShoringResponse, summary="Fôrmas e escoramento NBR 15696 / DIN 18218 (Frente 125)")
async def calculate_concrete_formwork(body: ConcreteFormworkShoringRequest, controller: SceneController = Depends(get_controller)) -> ConcreteFormworkShoringResponse:
    return await controller.calculate_concrete_formwork(body)

@router.post("/structures/reinforced-concrete-beam", response_model=ReinforcedConcreteBeamResponse, summary="Vigas de concreto armado no ELU NBR 6118 (Frente 126)")
async def calculate_reinforced_concrete_beam(body: ReinforcedConcreteBeamRequest, controller: SceneController = Depends(get_controller)) -> ReinforcedConcreteBeamResponse:
    return await controller.calculate_reinforced_concrete_beam(body)

@router.post("/structures/waffle-slab", response_model=WaffleSlabResponse, summary="Lajes nervuradas com cubetas NBR 6118 (Frente 127)")
async def calculate_waffle_slab(body: WaffleSlabRequest, controller: SceneController = Depends(get_controller)) -> WaffleSlabResponse:
    return await controller.calculate_waffle_slab(body)

@router.post("/structures/prestressed-concrete", response_model=PrestressedConcreteResponse, summary="Concreto protendido e perdas NBR 6118 (Frente 128)")
async def calculate_prestressed_concrete(body: PrestressedConcreteRequest, controller: SceneController = Depends(get_controller)) -> PrestressedConcreteResponse:
    return await controller.calculate_prestressed_concrete(body)

@router.post("/structures/glulam-timber", response_model=GlulamCltTimberResponse, summary="Madeira laminada colada e CLT NBR 7190 (Frente 129)")
async def calculate_glulam_timber(body: GlulamCltTimberRequest, controller: SceneController = Depends(get_controller)) -> GlulamCltTimberResponse:
    return await controller.calculate_glulam_timber(body)

@router.post("/structures/space-truss", response_model=SpaceTrussResponse, summary="Treliças espaciais tubulares 3D (Frente 130)")
async def generate_space_truss(body: SpaceTrussRequest, controller: SceneController = Depends(get_controller)) -> SpaceTrussResponse:
    return await controller.generate_space_truss(body)

@router.post("/mep/fuel-gas-piping", response_model=FuelGasPipingResponse, summary="Instalações de gás GLP/GN NBR 15526 (Frente 131)")
async def calculate_fuel_gas_piping(body: FuelGasPipingRequest, controller: SceneController = Depends(get_controller)) -> FuelGasPipingResponse:
    return await controller.calculate_fuel_gas_piping(body)

@router.post("/mep/lightning-spda", response_model=LightningProtectionSpdaResponse, summary="SPDA método esfera rolante NBR 5419 (Frente 132)")
async def calculate_lightning_spda(body: LightningProtectionSpdaRequest, controller: SceneController = Depends(get_controller)) -> LightningProtectionSpdaResponse:
    return await controller.calculate_lightning_spda(body)

@router.post("/safety/fire-egress", response_model=FireEgressRouteResponse, summary="Rotas de fuga e saídas de emergência NBR 9077 (Frente 133)")
async def calculate_fire_egress(body: FireEgressRouteRequest, controller: SceneController = Depends(get_controller)) -> FireEgressRouteResponse:
    return await controller.calculate_fire_egress(body)

@router.post("/mep/hvac-cooling-load", response_model=HvacThermalLoadResponse, summary="Carga térmica HVAC ASHRAE / NBR 16401 (Frente 134)")
async def calculate_hvac_cooling_load(body: HvacThermalLoadRequest, controller: SceneController = Depends(get_controller)) -> HvacThermalLoadResponse:
    return await controller.calculate_hvac_cooling_load(body)

@router.post("/lighting/photometric-lumen", response_model=PhotometricLumenDesignResponse, summary="Iluminação interior método dos lúmens NBR 8995 (Frente 135)")
async def calculate_photometric_lighting(body: PhotometricLumenDesignRequest, controller: SceneController = Depends(get_controller)) -> PhotometricLumenDesignResponse:
    return await controller.calculate_photometric_lighting(body)

@router.post("/energy/solar-photovoltaic", response_model=SolarPhotovoltaicArrayResponse, summary="Usinas solares fotovoltaicas (Frente 136)")
async def calculate_solar_pv(body: SolarPhotovoltaicArrayRequest, controller: SceneController = Depends(get_controller)) -> SolarPhotovoltaicArrayResponse:
    return await controller.calculate_solar_pv(body)

@router.post("/environment/natural-ventilation", response_model=NaturalVentilationResponse, summary="Ventilação natural e efeito chaminé NBR 15220 (Frente 137)")
async def calculate_natural_ventilation(body: NaturalVentilationRequest, controller: SceneController = Depends(get_controller)) -> NaturalVentilationResponse:
    return await controller.calculate_natural_ventilation(body)

@router.post("/architecture/glazing-fenestration", response_model=GlazingFenestrationResponse, summary="Esquadrias paramétricas e pele de vidro (Frente 138)")
async def generate_glazing_fenestration(body: GlazingFenestrationRequest, controller: SceneController = Depends(get_controller)) -> GlazingFenestrationResponse:
    return await controller.generate_glazing_fenestration(body)

@router.post("/architecture/ventilated-facade", response_model=VentilatedFacadeResponse, summary="Fachadas ventiladas e câmara convectiva (Frente 139)")
async def calculate_ventilated_facade(body: VentilatedFacadeRequest, controller: SceneController = Depends(get_controller)) -> VentilatedFacadeResponse:
    return await controller.calculate_ventilated_facade(body)

@router.post("/aerodynamics/mini-wind-cfd-2d", response_model=MiniWindCfd2dResponse, summary="Túnel de vento CFD 2D e vórtices de Kármán (Frente 140)")
async def simulate_wind_cfd_2d(body: MiniWindCfd2dRequest, controller: SceneController = Depends(get_controller)) -> MiniWindCfd2dResponse:
    return await controller.simulate_wind_cfd_2d(body)

@router.post("/bim/4d-gantt-schedule", response_model=Bim4dGanttScheduleResponse, summary="Cronograma BIM 4D e curva S (Frente 141)")
async def generate_bim_4d_schedule(body: Bim4dGanttScheduleRequest, controller: SceneController = Depends(get_controller)) -> Bim4dGanttScheduleResponse:
    return await controller.generate_bim_4d_schedule(body)

@router.post("/bim/7d-cobie-assets", response_model=Bim7dAssetManagementCobieResponse, summary="Gestão de ativos BIM 7D e COBie (Frente 142)")
async def generate_bim_7d_cobie(body: Bim7dAssetManagementCobieRequest, controller: SceneController = Depends(get_controller)) -> Bim7dAssetManagementCobieResponse:
    return await controller.generate_bim_7d_cobie(body)

@router.post("/safety/construction-site-logistics", response_model=ConstructionSiteLogisticsResponse, summary="Logística de canteiro e raio de gruas NR-18 (Frente 143)")
async def calculate_site_logistics(body: ConstructionSiteLogisticsRequest, controller: SceneController = Depends(get_controller)) -> ConstructionSiteLogisticsResponse:
    return await controller.calculate_site_logistics(body)

@router.post("/accessibility/universal-audit", response_model=UniversalAccessibilityResponse, summary="Acessibilidade universal NBR 9050 (Frente 144)")
async def audit_universal_accessibility(body: UniversalAccessibilityRequest, controller: SceneController = Depends(get_controller)) -> UniversalAccessibilityResponse:
    return await controller.audit_universal_accessibility(body)

@router.post("/sustainability/lca-emissions", response_model=LifeCycleAssessmentResponse, summary="Avaliação de ciclo de vida ACV ISO 14040 (Frente 145)")
async def calculate_lca_emissions(body: LifeCycleAssessmentRequest, controller: SceneController = Depends(get_controller)) -> LifeCycleAssessmentResponse:
    return await controller.calculate_lca_emissions(body)

# ------------------------------------------------------------------------------
# OPÇÃO A: ENDPOINTS NATIVOS DO SKETCHUP
# ------------------------------------------------------------------------------

@router.post(
    "/camera/position-camera",
    response_model=PositionCameraNativeResponse,
    status_code=status.HTTP_200_OK,
    summary="Posiciona câmera na coordenada com altura de observador nativa do SketchUp"
)
async def position_camera_native(
    body: PositionCameraNativeRequest,
    controller: SceneController = Depends(get_controller)
) -> PositionCameraNativeResponse:
    return await controller.position_camera_native(body)


@router.post(
    "/camera/look-around",
    response_model=LookAroundNativeResponse,
    status_code=status.HTTP_200_OK,
    summary="Gira o ângulo de visão do observador sem mover os pés (Look Around)"
)
async def look_around_native(
    body: LookAroundNativeRequest,
    controller: SceneController = Depends(get_controller)
) -> LookAroundNativeResponse:
    return await controller.look_around_native(body)


@router.post(
    "/camera/walk-step",
    response_model=WalkStepNativeResponse,
    status_code=status.HTTP_200_OK,
    summary="Executa passo de caminhada em primeira pessoa com colisão e degraus (Walk)"
)
async def walk_step_native(
    body: WalkStepNativeRequest,
    controller: SceneController = Depends(get_controller)
) -> WalkStepNativeResponse:
    return await controller.walk_step_native(body)


@router.post(
    "/sandbox/smoove",
    response_model=SandboxSmooveResponse,
    status_code=status.HTTP_200_OK,
    summary="Deforma terreno organicamente com raio de influência cossenoidal (Smoove)"
)
async def sandbox_smoove(
    body: SandboxSmooveRequest,
    controller: SceneController = Depends(get_controller)
) -> SandboxSmooveResponse:
    return await controller.sandbox_smoove(body)


@router.post(
    "/sandbox/stamp",
    response_model=SandboxStampResponse,
    status_code=status.HTTP_200_OK,
    summary="Estampa platô e saia de talude de edificação sobre terreno (Stamp)"
)
async def sandbox_stamp(
    body: SandboxStampRequest,
    controller: SceneController = Depends(get_controller)
) -> SandboxStampResponse:
    return await controller.sandbox_stamp(body)


@router.post(
    "/sandbox/drape",
    response_model=SandboxDrapeResponse,
    status_code=status.HTTP_200_OK,
    summary="Projeta caminhos 2D verticalmente sobre as faces do terreno 3D (Drape)"
)
async def sandbox_drape(
    body: SandboxDrapeRequest,
    controller: SceneController = Depends(get_controller)
) -> SandboxDrapeResponse:
    return await controller.sandbox_drape(body)


@router.post(
    "/sandbox/flip-edge",
    response_model=SandboxFlipEdgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Inverte a diagonal entre triângulos adjacentes do terreno (Flip Edge)"
)
async def sandbox_flip_edge(
    body: SandboxFlipEdgeRequest,
    controller: SceneController = Depends(get_controller)
) -> SandboxFlipEdgeResponse:
    return await controller.sandbox_flip_edge(body)


@router.post(
    "/match-photo/calibrate",
    response_model=MatchPhotoCalibrateResponse,
    status_code=status.HTTP_200_OK,
    summary="Calibra perspectiva e câmera a partir de linhas de fuga de foto (Match Photo)"
)
async def match_photo_calibrate(
    body: MatchPhotoCalibrateRequest,
    controller: SceneController = Depends(get_controller)
) -> MatchPhotoCalibrateResponse:
    return await controller.match_photo_calibrate(body)


@router.post(
    "/styles/watermark",
    response_model=WatermarkStyleConfigureResponse,
    status_code=status.HTTP_200_OK,
    summary="Configura marca d'água no viewport (Overlay/Background nos 9 pontos)"
)
async def watermark_style_configure(
    body: WatermarkStyleConfigureRequest,
    controller: SceneController = Depends(get_controller)
) -> WatermarkStyleConfigureResponse:
    return await controller.watermark_style_configure(body)


@router.post(
    "/components/interact",
    response_model=DynamicComponentInteractResponse,
    status_code=status.HTTP_200_OK,
    summary="Executa ação de clique da ferramenta Interagir em Componente Dinâmico"
)
async def dynamic_component_interact(
    body: DynamicComponentInteractRequest,
    controller: SceneController = Depends(get_controller)
) -> DynamicComponentInteractResponse:
    return await controller.dynamic_component_interact(body)


@router.post(
    "/solid-tools/execute",
    response_model=TrimbleSolidToolsResponse,
    status_code=status.HTTP_200_OK,
    summary="Executa operações booleanas de sólidos oficiais (Intersect, Union, Subtract, Trim, Split)"
)
async def trimble_solid_tools_execute(
    body: TrimbleSolidToolsRequest,
    controller: SceneController = Depends(get_controller)
) -> TrimbleSolidToolsResponse:
    return await controller.trimble_solid_tools_execute(body)

# ------------------------------------------------------------------------------
# OPÇÃO A (PARTE 2): ENDPOINTS NATIVOS ADICIONAIS DO SKETCHUP
# ------------------------------------------------------------------------------

@router.post(
    "/bim/ifc/classify",
    response_model=IfcClassifyComponentResponse,
    status_code=status.HTTP_200_OK,
    summary="Atribui classe IFC oficial do SketchUp ao componente com GlobalId (GUID)"
)
async def ifc_classify_component(
    body: IfcClassifyComponentRequest,
    controller: SceneController = Depends(get_controller)
) -> IfcClassifyComponentResponse:
    return await controller.ifc_classify_component(body)


@router.post(
    "/bim/ifc/audit",
    response_model=IfcAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Audita conformidade de classificação IFC de todas as instâncias da cena"
)
async def ifc_audit_classifications(
    body: IfcAuditRequest,
    controller: SceneController = Depends(get_controller)
) -> IfcAuditResponse:
    return await controller.ifc_audit_classifications(body)


@router.post(
    "/geometry/3d-text",
    response_model=ThreeDTextGenerateResponse,
    status_code=status.HTTP_200_OK,
    summary="Gera geometria analítica da ferramenta Texto 3D com extrusão e preenchimento"
)
async def generate_3d_text(
    body: ThreeDTextGenerateRequest,
    controller: SceneController = Depends(get_controller)
) -> ThreeDTextGenerateResponse:
    return await controller.generate_3d_text(body)


@router.post(
    "/reports/generate",
    response_model=GenerateReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Gera relatório oficial de componentes e quantitativos em JSON e CSV (Generate Report)"
)
async def generate_report(
    body: GenerateReportRequest,
    controller: SceneController = Depends(get_controller)
) -> GenerateReportResponse:
    return await controller.generate_report(body)


@router.post(
    "/axes/custom",
    response_model=AxesCustomSetResponse,
    status_code=status.HTTP_200_OK,
    summary="Define sistema de eixos personalizado na cena via origem e vetores direcionais (Axes Tool)"
)
async def axes_set_custom(
    body: AxesCustomSetRequest,
    controller: SceneController = Depends(get_controller)
) -> AxesCustomSetResponse:
    return await controller.axes_set_custom(body)


@router.post(
    "/axes/align-face",
    response_model=AxesAlignFaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Alinha o sistema de eixos perpendicularmente à face selecionada (Align Axes to Face)"
)
async def axes_align_to_face(
    body: AxesAlignFaceRequest,
    controller: SceneController = Depends(get_controller)
) -> AxesAlignFaceResponse:
    return await controller.axes_align_to_face(body)


@router.post(
    "/axes/reset",
    response_model=AxesResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Restaura os eixos cartesianos para a origem canônica global do SketchUp (Reset Axes)"
)
async def axes_reset(
    controller: SceneController = Depends(get_controller)
) -> AxesResetResponse:
    return await controller.axes_reset()


@router.post(
    "/entity-info/edge",
    response_model=EntityInspectEdgeResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspeciona propriedades de comprimento e suavização de aresta (Entity Info)"
)
async def inspect_entity_edge(
    body: EntityInspectEdgeRequest,
    controller: SceneController = Depends(get_controller)
) -> EntityInspectEdgeResponse:
    return await controller.inspect_entity_edge(body)


@router.post(
    "/entity-info/face",
    response_model=EntityInspectFaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Inspeciona área, normal e materiais aplicados na face (Entity Info)"
)
async def inspect_entity_face(
    body: EntityInspectFaceRequest,
    controller: SceneController = Depends(get_controller)
) -> EntityInspectFaceResponse:
    return await controller.inspect_entity_face(body)


@router.post(
    "/entity-info/solid",
    response_model=EntityInspectSolidResponse,
    status_code=status.HTTP_200_OK,
    summary="Verifica estanqueidade 2-manifold e calcula volume líquido de sólido (Solid Inspector)"
)
async def inspect_entity_solid(
    body: EntityInspectSolidRequest,
    controller: SceneController = Depends(get_controller)
) -> EntityInspectSolidResponse:
    return await controller.inspect_entity_solid(body)


@router.post(
    "/components/edit-mode",
    response_model=ComponentEditModeResponse,
    status_code=status.HTTP_200_OK,
    summary="Aplica modos de visualização de edição de componente (Hide Rest of Model, Fade Rest)"
)
async def component_edit_mode_apply(
    body: ComponentEditModeRequest,
    controller: SceneController = Depends(get_controller)
) -> ComponentEditModeResponse:
    return await controller.component_edit_mode_apply(body)


@router.post(
    "/units/configure",
    response_model=ModelUnitsConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Configura formato de unidades, precisão decimal e snaps do modelo (Model Units)"
)
async def model_units_configure(
    body: ModelUnitsConfigRequest,
    controller: SceneController = Depends(get_controller)
) -> ModelUnitsConfigResponse:
    return await controller.model_units_configure(body)


@router.post(
    "/units/format",
    response_model=ModelUnitsFormatResponse,
    status_code=status.HTTP_200_OK,
    summary="Formata comprimento numérico para a string métrica correspondente"
)
async def model_units_format(
    body: ModelUnitsFormatRequest,
    controller: SceneController = Depends(get_controller)
) -> ModelUnitsFormatResponse:
    return await controller.model_units_format(body)

# ------------------------------------------------------------------------------
# OPÇÃO A (PARTE 3): ENDPOINTS NATIVOS ADICIONAIS DO SKETCHUP
# ------------------------------------------------------------------------------

@router.post(
    "/textures/pin-transform",
    response_model=TexturePinTransformResponse,
    status_code=status.HTTP_200_OK,
    summary="Mapeia UV da textura usando os 4 pinos oficiais (Vermelho, Verde, Azul, Amarelo)"
)
async def texture_pin_transform(
    body: TexturePinTransformRequest,
    controller: SceneController = Depends(get_controller)
) -> TexturePinTransformResponse:
    return await controller.texture_pin_transform(body)


@router.post(
    "/styles/color-by-tag",
    response_model=ColorByTagApplyResponse,
    status_code=status.HTTP_200_OK,
    summary="Ativa ou desativa a substituição de materiais por cores de etiqueta (Color by Tag)"
)
async def color_by_tag_apply(
    body: ColorByTagApplyRequest,
    controller: SceneController = Depends(get_controller)
) -> ColorByTagApplyResponse:
    return await controller.color_by_tag_apply(body)


@router.post(
    "/cleanup/purge-unused",
    response_model=PurgeUnusedResponse,
    status_code=status.HTTP_200_OK,
    summary="Elimina componentes, materiais e tags não utilizados do modelo (Purge Unused)"
)
async def purge_unused_items(
    body: PurgeUnusedRequest,
    controller: SceneController = Depends(get_controller)
) -> PurgeUnusedResponse:
    return await controller.purge_unused_items(body)


@router.post(
    "/components/make-component",
    response_model=MakeComponentDefinitionResponse,
    status_code=status.HTTP_200_OK,
    summary="Cria definição de componente oficial com comportamentos (Glue to, Cut Opening, Face-Me)"
)
async def make_component_definition(
    body: MakeComponentDefinitionRequest,
    controller: SceneController = Depends(get_controller)
) -> MakeComponentDefinitionResponse:
    return await controller.make_component_definition(body)


@router.post(
    "/selection/advanced",
    response_model=AdvancedSelectionResponse,
    status_code=status.HTTP_200_OK,
    summary="Executa seleção avançada: Inverter, Mesma Tag, Mesmo Material ou Conectados (Triplo Clique)"
)
async def advanced_selection_execute(
    body: AdvancedSelectionRequest,
    controller: SceneController = Depends(get_controller)
) -> AdvancedSelectionResponse:
    return await controller.advanced_selection_execute(body)


@router.post(
    "/styles/hidden-geometry",
    response_model=HiddenGeometryConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Configura exibição de geometria oculta (tracejada) e objetos ocultos (fantasma)"
)
async def hidden_geometry_configure(
    body: HiddenGeometryConfigRequest,
    controller: SceneController = Depends(get_controller)
) -> HiddenGeometryConfigResponse:
    return await controller.hidden_geometry_configure(body)


@router.post(
    "/model/statistics",
    response_model=ModelStatisticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcula o censo de entidades e classificação de complexidade do modelo (Model Statistics)"
)
async def model_statistics_calculate(
    body: ModelStatisticsRequest,
    controller: SceneController = Depends(get_controller)
) -> ModelStatisticsResponse:
    return await controller.model_statistics_calculate(body)


# ============================================================================
# OPÇÃO A (PARTE 4): ROTAS DE FERRAMENTAS OFICIAIS DO SKETCHUP
# ============================================================================

@router.post(
    "/tools/regular-polygon",
    response_model=RegularPolygonResponse,
    status_code=status.HTTP_200_OK,
    summary="Gera polígono regular paramétrico nativo (Polygon Tool - VCB 6s, 8s)"
)
async def regular_polygon_generate(
    body: RegularPolygonRequest,
    controller: SceneController = Depends(get_controller)
) -> RegularPolygonResponse:
    return await controller.regular_polygon_generate(body)


@router.post(
    "/tools/freehand-curve",
    response_model=FreehandCurveResponse,
    status_code=status.HTTP_200_OK,
    summary="Processa traçado de mão livre com simplificação RDP e fechamento de face (Freehand Tool)"
)
async def freehand_curve_process(
    body: FreehandCurveRequest,
    controller: SceneController = Depends(get_controller)
) -> FreehandCurveResponse:
    return await controller.freehand_curve_process(body)


@router.post(
    "/geometry/reverse-orient-faces",
    response_model=ReverseOrientFacesResponse,
    status_code=status.HTTP_200_OK,
    summary="Inverte normais de faces selecionadas ou orienta faces conexas (Reverse & Orient Faces)"
)
async def reverse_orient_faces(
    body: ReverseOrientFacesRequest,
    controller: SceneController = Depends(get_controller)
) -> ReverseOrientFacesResponse:
    return await controller.reverse_orient_faces(body)


@router.post(
    "/camera/dolly-fov-lens",
    response_model=DollyFovLensResponse,
    status_code=status.HTTP_200_OK,
    summary="Controla Dolly de câmera e equivalência entre FOV (graus) e Lente 35mm (mm)"
)
async def dolly_fov_lens_control(
    body: DollyFovLensRequest,
    controller: SceneController = Depends(get_controller)
) -> DollyFovLensResponse:
    return await controller.dolly_fov_lens_control(body)


@router.post(
    "/geometry/intersect-faces",
    response_model=IntersectFacesResponse,
    status_code=status.HTTP_200_OK,
    summary="Intersecciona faces com o modelo ou com a seleção gerando arestas de corte (Intersect Faces)"
)
async def intersect_faces_compute(
    body: IntersectFacesRequest,
    controller: SceneController = Depends(get_controller)
) -> IntersectFacesResponse:
    return await controller.intersect_faces_compute(body)


@router.post(
    "/tools/axis-lock-inference",
    response_model=AxisLockInferenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Interpreta bloqueio de eixos (Setas X/Y/Z) e projeta cursor na inferência restrita"
)
async def axis_lock_inference(
    body: AxisLockInferenceRequest,
    controller: SceneController = Depends(get_controller)
) -> AxisLockInferenceResponse:
    return await controller.axis_lock_inference(body)


@router.post(
    "/styles/ground-sky",
    response_model=GroundSkyStyleResponse,
    status_code=status.HTTP_200_OK,
    summary="Configura plano de fundo, solo com transparência e cúpula de céu do Estilo (Styles Panel)"
)
async def ground_sky_style_configure(
    body: GroundSkyStyleRequest,
    controller: SceneController = Depends(get_controller)
) -> GroundSkyStyleResponse:
    return await controller.ground_sky_style_configure(body)


# -----------------------------------------------------------------------------
# OPÇÃO A (PARTE 5): ROTAS DE FERRAMENTAS NATIVAS OFICIAIS DO SKETCHUP
# -----------------------------------------------------------------------------

@router.post(
    "/tools/stamp-terrain",
    response_model=StampTerrainResponse,
    status_code=status.HTTP_200_OK,
    summary="Aplica a ferramenta Carimbo (Stamp Tool) criando platô nivelado e talude suave na malha TIN"
)
async def stamp_terrain_apply(
    body: StampTerrainRequest,
    controller: SceneController = Depends(get_controller)
) -> StampTerrainResponse:
    return await controller.stamp_terrain_apply(body)


@router.post(
    "/tools/drape-path",
    response_model=DrapePathResponse,
    status_code=status.HTTP_200_OK,
    summary="Projeta caminhos ou contornos 2D sobre o relevo da malha de terreno 3D (Drape Tool)"
)
async def drape_path_apply(
    body: DrapePathRequest,
    controller: SceneController = Depends(get_controller)
) -> DrapePathResponse:
    return await controller.drape_path_apply(body)


@router.post(
    "/geometry/section-cut-fill",
    response_model=SectionCutFillResponse,
    status_code=status.HTTP_200_OK,
    summary="Calcula tampas poligonais de preenchimento (Section Fill) e inversão de plano de corte"
)
async def section_cut_fill_compute(
    body: SectionCutFillRequest,
    controller: SceneController = Depends(get_controller)
) -> SectionCutFillResponse:
    return await controller.section_cut_fill_compute(body)


@router.post(
    "/geometry/soft-smooth-edges",
    response_model=SoftSmoothEdgesResponse,
    status_code=status.HTTP_200_OK,
    summary="Aplica suavização de arestas e gera normais interpoladas (Soften / Smooth Edges Dialog)"
)
async def soft_smooth_edges_process(
    body: SoftSmoothEdgesRequest,
    controller: SceneController = Depends(get_controller)
) -> SoftSmoothEdgesResponse:
    return await controller.soft_smooth_edges_process(body)


@router.post(
    "/tools/edge-divide",
    response_model=EdgeDivideResponse,
    status_code=status.HTTP_200_OK,
    summary="Divide aresta linear em N segmentos perfeitamente equidistantes (Divide Tool com VCB)"
)
async def edge_divide_execute(
    body: EdgeDivideRequest,
    controller: SceneController = Depends(get_controller)
) -> EdgeDivideResponse:
    return await controller.edge_divide_execute(body)


@router.post(
    "/geometry/push-pull-create-face",
    response_model=PushPullCreateFaceResponse,
    status_code=status.HTTP_200_OK,
    summary="Extruda face criando sólido mantendo a face inicial preservada (Ctrl + Push/Pull Tool)"
)
async def push_pull_create_face_extrude(
    body: PushPullCreateFaceRequest,
    controller: SceneController = Depends(get_controller)
) -> PushPullCreateFaceResponse:
    return await controller.push_pull_create_face_extrude(body)


@router.post(
    "/bim/ifc-property-set",
    response_model=BimIfcPropertySetResponse,
    status_code=status.HTTP_200_OK,
    summary="Valida atributos buildingSMART e gera entidades STEP de conjuntos de propriedades (IFC Psets)"
)
async def bim_ifc_property_set_build(
    body: BimIfcPropertySetRequest,
    controller: SceneController = Depends(get_controller)
) -> BimIfcPropertySetResponse:
    return await controller.bim_ifc_property_set_build(body)


