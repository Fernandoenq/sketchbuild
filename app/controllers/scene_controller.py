"""
Controller do modulo de cena/visualizador: orquestra o service e
traduz excecoes de dominio para HTTPException. Nenhuma regra de
negocio mora aqui.
"""

from __future__ import annotations

import logging

from fastapi import HTTPException, status

from app.domain.exceptions import (
    InvalidModelPathError,
    ModelFileNotFoundError,
    SceneOverwriteConfirmationRequiredError,
    SceneParseError,
    SceneSessionError,
)
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
    AddDetailSandboxRequest,
    AddDetailSandboxResponse,
    FlipEdgeSandboxRequest,
    FlipEdgeSandboxResponse,
    WalkCameraGravityRequest,
    WalkCameraGravityResponse,
    LookAroundCameraRequest,
    LookAroundCameraResponse,
    PositionCameraRequest,
    PositionCameraResponse,
    FogSettingsRequest,
    FogSettingsResponse,
    GraphicExport2DRequest,
    GraphicExport2DResponse,
    FlipAlongRequest,
    FlipAlongResponse,

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
    AddRectangleResponse,
    AutosaveDraftDTO,
    CreateScenePageResponse,
    DeleteInstanceResponse,
    DiscardAutosaveDraftResponse,
    DuplicateInstanceResponse,
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
    PaintFaceResponse,
    PaintInstanceResponse,
    SaveSceneResponse,
    SceneResponse,
    SceneAttributesResponse,
    ScenePageDTO,
    SetInstanceAxesResponse,
    SetTagVisibilityResponse,
    TagDTO,
    TagInstanceResponse,
    ListTagsResponse,
    UpdateCameraRequest,
    UpdateCameraResponse,
    UpdateTransformResponse,
    CreateBoxRequest,
    CreateBoxResponse,
    BoxDetailsDTO,
    SetStyleRequest,
    SetStyleResponse,
    AssemblyTreeResponse,
    ConvertDxfRequest,
    ConvertDxfResponse,
    BimBomReportResponse,
    ExplodedViewRequest,
    ExplodedViewResponse,
)
from app.services.recent_files_service import RecentFilesService
from app.services.scene_service import SceneService

logger = logging.getLogger("sketchbuild")


class SceneController:
    def __init__(
        self,
        service: SceneService | None = None,
        recent_files_service: RecentFilesService | None = None,
    ):
        self._service = service or SceneService()
        self._recent_files_service = recent_files_service or RecentFilesService()

    async def open_scene(self, file_path: str) -> SceneResponse:
        try:
            result = await self._service.open_scene(file_path)
        except (InvalidModelPathError, ModelFileNotFoundError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        try:
            await self._recent_files_service.register_opened(file_path)
        except OSError:
            # "Arquivos recentes" e um nice-to-have da Pagina Inicial --
            # uma falha ao gravar o JSON local nunca pode derrubar a
            # abertura do modelo em si.
            logger.warning("Falha ao registrar arquivo recente: %s", file_path)

        return SceneResponse.model_validate(result)

    async def open_binary_scene(self, file_path: str) -> SceneResponse:
        try:
            result = await self._service.open_binary_scene(file_path)
        except (InvalidModelPathError, ModelFileNotFoundError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        try:
            await self._recent_files_service.register_opened(file_path)
        except OSError:
            logger.warning("Falha ao registrar arquivo recente: %s", file_path)

        return SceneResponse.model_validate(result)

    async def get_attributes(self, file_path: str) -> SceneAttributesResponse:
        try:
            result = await self._service.get_attributes(file_path)
        except (InvalidModelPathError, ModelFileNotFoundError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        return SceneAttributesResponse.model_validate(result)

    async def new_scene_from_template(self, template_id: str) -> SceneResponse:
        """Cria um modelo novo a partir de um template real da Trimble --
        NAO registra em "Arquivos recentes": como `model_path` fica None
        (sem arquivo no disco ainda), nao ha caminho real pra gravar lá."""
        try:
            result = await self._service.new_scene_from_template(template_id)
        except (InvalidModelPathError, ModelFileNotFoundError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        return SceneResponse.model_validate(result)

    async def open_uploaded_scene(self, data: bytes) -> SceneResponse:
        """Abre um .skp enviado via upload do navegador (<input
        type="file">, seletor nativo do SO) -- NAO registra em "Arquivos
        recentes": `model_path` fica None (sem arquivo no disco ainda),
        nao ha caminho real pra gravar la, mesma limitacao de
        new_scene_from_template()."""
        try:
            result = await self._service.open_uploaded_scene(data)
        except (InvalidModelPathError, ModelFileNotFoundError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        return SceneResponse.model_validate(result)

    async def get_current_session(self) -> SceneResponse:
        """Cobre o F5 na pagina (ver REVERSE_ENGINEERING_NOTES.md nao se
        aplica -- isto nao e engenharia reversa, e persistencia de sessao
        no app em si, ver README.md "Persistencia de sessao"). 409 quando
        o backend nao tem nenhuma sessao aberta no momento (acabou de
        reiniciar, ou ninguem abriu nada ainda nesta execucao)."""
        result = await self._service.get_current_session()
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="nenhuma sessao aberta nesta execucao do backend",
            )
        return SceneResponse.model_validate(result)

    async def list_autosave_drafts(self) -> ListAutosaveDraftsResponse:
        drafts = await self._service.list_autosave_drafts()
        return ListAutosaveDraftsResponse(
            drafts=[AutosaveDraftDTO.model_validate(d) for d in drafts]
        )

    async def recover_autosave_draft(self, draft_id: str) -> SceneResponse:
        try:
            result = await self._service.recover_autosave_draft(draft_id)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        except SceneParseError as e:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)
            ) from e

        original_path = result.get("model_path")
        if original_path:
            try:
                await self._recent_files_service.register_opened(original_path)
            except OSError:
                logger.warning("Falha ao registrar arquivo recente: %s", original_path)

        return SceneResponse.model_validate(result)

    async def discard_autosave_draft(self, draft_id: str) -> DiscardAutosaveDraftResponse:
        try:
            await self._service.discard_autosave_draft(draft_id)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return DiscardAutosaveDraftResponse(id=draft_id, discarded=True)

    async def update_instance_transform(
        self, instance_id: str, transform: list[float]
    ) -> UpdateTransformResponse:
        try:
            await self._service.update_instance_transform(instance_id, transform)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return UpdateTransformResponse(instance_id=instance_id, applied=True)

    async def save_scene(
        self, path: str | None, overwrite_confirmed: bool = False
    ) -> SaveSceneResponse:
        try:
            saved_path = await self._service.save_scene(path, overwrite_confirmed)
        except SceneOverwriteConfirmationRequiredError as e:
            # 409 estruturado (nao so string) -- o frontend distingue esse
            # caso do erro generico pelo campo "code" e mostra um
            # window.confirm() antes de re-enviar com overwrite_confirmed=true.
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "overwrite_confirmation_required",
                    "message": str(e),
                    "existing_path": e.existing_path,
                    "existing_size_bytes": e.existing_size_bytes,
                },
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return SaveSceneResponse(saved=True, path=saved_path)

    async def get_skp_bytes(self) -> bytes:
        try:
            return await self._service.get_skp_bytes()
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    async def duplicate_instance(
        self,
        instance_id: str,
        transform: list[float] | None = None,
        offset_delta_cm: list[float] | None = None,
    ) -> DuplicateInstanceResponse:
        try:
            res = await self._service.duplicate_instance(instance_id, transform, offset_delta_cm)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return DuplicateInstanceResponse(instance=res, duplicated=True)

    async def delete_instance(self, instance_id: str) -> DeleteInstanceResponse:
        try:
            await self._service.delete_instance(instance_id)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return DeleteInstanceResponse(instance_id=instance_id, deleted=True)

    async def paint_instance(
        self, instance_id: str, r: int, g: int, b: int
    ) -> PaintInstanceResponse:
        """Equivalente real de "Ferramentas > Pintura" -- ver
        REVERSE_ENGINEERING_NOTES.md secao 28."""
        try:
            await self._service.paint_instance(instance_id, r, g, b)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return PaintInstanceResponse(instance_id=instance_id, painted=True, color=[r, g, b])

    async def tag_instance(self, instance_id: str, tag_name: str) -> TagInstanceResponse:
        """Equivalente real de "Ferramentas > Etiqueta" -- ver
        REVERSE_ENGINEERING_NOTES.md secao 28.17."""
        try:
            await self._service.tag_instance(instance_id, tag_name)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return TagInstanceResponse(instance_id=instance_id, tag_name=tag_name)

    async def paint_face(self, face_id: str, r: int, g: int, b: int) -> PaintFaceResponse:
        """Equivalente real de pintar UMA face especifica (nao a
        instancia inteira) -- ver REVERSE_ENGINEERING_NOTES.md secao
        28.19."""
        try:
            await self._service.paint_face(face_id, r, g, b)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return PaintFaceResponse(face_id=face_id, painted=True, color=[r, g, b])

    async def list_scenes(self) -> ListScenePagesResponse:
        """Equivalente real de "Janela > Bandeja padrao > Cenas" -- ver
        REVERSE_ENGINEERING_NOTES.md secao 28.20."""
        try:
            pages = await self._service.list_scenes()
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return ListScenePagesResponse(pages=[ScenePageDTO.model_validate(p) for p in pages])

    async def create_scene(self, name: str) -> CreateScenePageResponse:
        try:
            result = await self._service.create_scene(name)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return CreateScenePageResponse.model_validate(result)

    async def activate_scene(self, scene_id: str) -> ActivateScenePageResponse:
        try:
            await self._service.activate_scene(scene_id)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return ActivateScenePageResponse(scene_id=scene_id, activated=True)

    async def list_tags(self) -> ListTagsResponse:
        """Equivalente real de "Janela > Bandeja padrao > Etiquetas" --
        ver REVERSE_ENGINEERING_NOTES.md secao 28.22."""
        try:
            tags = await self._service.list_tags()
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return ListTagsResponse(tags=[TagDTO.model_validate(t) for t in tags])

    async def set_tag_visibility(self, tag_name: str, visible: bool) -> SetTagVisibilityResponse:
        try:
            result = await self._service.set_tag_visibility(tag_name, visible)
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return SetTagVisibilityResponse.model_validate(result)

    async def set_instance_axes(
        self,
        instance_id: str,
        origin: list[float],
        x_point: list[float],
        y_point: list[float],
    ) -> SetInstanceAxesResponse:
        try:
            result = await self._service.set_instance_axes(
                instance_id, origin, x_point, y_point
            )
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return SetInstanceAxesResponse.model_validate(result)

    async def export_model_obj(self, path: str) -> ExportModelResponse:
        try:
            saved_path = await self._service.export_model_obj(path)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return ExportModelResponse(saved=True, path=saved_path)

    async def add_rectangle(
        self, width_m: float, height_m: float, as_group: bool = False
    ) -> AddRectangleResponse:
        """Equivalente real de "Desenho > Formas > Retângulo" -- ver
        REVERSE_ENGINEERING_NOTES.md secao 28."""
        try:
            scene = await self._service.add_rectangle(width_m, height_m, as_group)
        except InvalidModelPathError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
            ) from e
        except SceneSessionError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=str(e)
            ) from e
        return AddRectangleResponse(scene=SceneResponse.model_validate(scene))

    async def update_camera(self, body: UpdateCameraRequest) -> UpdateCameraResponse:
        try:
            await self._service.update_camera(
                eye=body.eye,
                target=body.target,
                up=body.up,
                fov_deg=body.fov_deg,
            )
            return UpdateCameraResponse(applied=True)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha ao atualizar câmera: {e}",
            ) from e

    async def add_box(self, body: CreateBoxRequest) -> CreateBoxResponse:
        try:
            res = await self._service.add_box(
                width_m=body.width_m,
                length_m=body.length_m,
                height_m=body.height_m,
                offset_xyz_cm=body.offset_xyz_cm,
            )
            return CreateBoxResponse(
                box=BoxDetailsDTO.model_validate(res["box"]),
                scene=SceneResponse.model_validate(res["scene"]),
            )
        except InvalidModelPathError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def set_rendering_style(self, body: SetStyleRequest) -> SetStyleResponse:
        try:
            res = await self._service.set_rendering_style(
                mode=body.mode,
                xray=body.xray,
                profiles_width=body.profiles_width,
                background_rgb=body.background_rgb,
                sky_rgb=body.sky_rgb,
            )
            return SetStyleResponse.model_validate(res)
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def get_assembly_tree(self) -> AssemblyTreeResponse:
        try:
            res = await self._service.get_assembly_tree()
            return AssemblyTreeResponse.model_validate(res)
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def convert_dxf(self, body: ConvertDxfRequest) -> ConvertDxfResponse:
        try:
            res = await self._service.convert_dxf(dxf_path=body.dxf_path, scale_factor=body.scale_factor)
            return ConvertDxfResponse.model_validate(res)
        except InvalidModelPathError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except SceneParseError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e

    async def get_bim_bom_report(self) -> BimBomReportResponse:
        try:
            res = await self._service.calculate_bim_bom()
            return BimBomReportResponse.model_validate(res)
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def calculate_exploded_view(self, body: ExplodedViewRequest) -> ExplodedViewResponse:
        try:
            res = await self._service.calculate_exploded_view(expansion_factor=body.expansion_factor)
            return ExplodedViewResponse.model_validate(res)
        except InvalidModelPathError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def export_model_glb(self, path: str) -> ExportGlbResponse:
        try:
            res = await self._service.export_model_glb(path)
            return ExportGlbResponse.model_validate(res)
        except InvalidModelPathError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def export_model_ifc(self, path: str, project_name: str = "Projeto SketchBuild") -> ExportIfcResponse:
        try:
            res = await self._service.export_model_ifc(path, project_name=project_name)
            return ExportIfcResponse.model_validate(res)
        except InvalidModelPathError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def add_line_geometry(self, body: AddLineGeometryRequest) -> AddGeometryEntityResponse:
        try:
            res = await self._service.add_line_geometry(body.start_m, body.end_m)
            return AddGeometryEntityResponse.model_validate(res)
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e

    async def add_face_geometry(self, body: AddFaceGeometryRequest) -> AddGeometryEntityResponse:
        try:
            res = await self._service.add_face_geometry(body.points_m)
            return AddGeometryEntityResponse.model_validate(res)
        except InvalidModelPathError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


    async def export_cutlist_xlsx(self, body: ExportCutlistRequest) -> ExportCutlistResponse:
        """Exporta lista de corte e orçamento para Excel .xlsx (Frente 23)."""
        try:
            res = await self._service.export_cutlist_xlsx(body.path)
            return ExportCutlistResponse(**res)
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def add_circle_geometry(self, body: AddCircleGeometryRequest) -> AddGeometryEntityResponse:
        """Cria um círculo plano B-Rep paramétrico (Frente 14)."""
        try:
            res = await self._service.add_circle_geometry(body.radius_m, body.center_xyz_m, body.num_segments)
            return AddGeometryEntityResponse(**res)
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def add_cylinder_geometry(self, body: AddCylinderGeometryRequest) -> AddGeometryEntityResponse:
        """Cria um cilindro sólido manifold paramétrico (Frente 14)."""
        try:
            res = await self._service.add_cylinder_geometry(body.radius_m, body.height_m, body.center_xyz_m, body.num_segments)
            return AddGeometryEntityResponse(**res)
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def extrude_face_geometry(self, body: ExtrudeFaceGeometryRequest) -> AddGeometryEntityResponse:
        """Extrude face coplanar para sólido 3D Push/Pull (Frente 24)."""
        try:
            res = await self._service.extrude_face_geometry(body.points_m, body.distance_m, body.normal)
            return AddGeometryEntityResponse(**res)
        except SceneSessionError as e:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


    async def get_assembly_steps(self) -> AssemblyStepsResponse:
        """Retorna etapas sequenciais de montagem (Frente 26)."""
        try:
            res = await self._service.get_assembly_steps()
            return AssemblyStepsResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_assembly_manual(self, body: ExportAssemblyManualRequest) -> ExportAssemblyManualResponse:
        """Gera manual de montagem em HTML (Frente 26)."""
        try:
            res = await self._service.export_assembly_manual(body.project_name, body.path)
            return ExportAssemblyManualResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_drawing_2d(self, body: ExportDrawing2DRequest) -> ExportDrawing2DResponse:
        """Exporta desenho técnico 2D vetorial em SVG (Frente 27)."""
        try:
            res = await self._service.export_drawing_2d(body.path, body.view_type, body.title, body.scale)
            return ExportDrawing2DResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_solar_study(self, body: SolarStudyRequest) -> SolarStudyResponse:
        """Calcula estudo solar e insolação NBR 16071 (Frente 28)."""
        try:
            res = await self._service.calculate_solar_study(body.day_of_year, body.hour, body.latitude, body.longitude)
            return SolarStudyResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def add_section_plane(self, body: SectionPlaneRequest) -> SectionPlaneResponse:
        """Adiciona um Plano de Corte de Seção (Frente 17)."""
        try:
            res = await self._service.add_section_plane(body.plane_abcd, body.name, body.symbol)
            return SectionPlaneResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def get_section_planes(self) -> list[SectionPlaneResponse]:
        """Retorna os Planos de Seção da cena (Frente 17)."""
        try:
            res = await self._service.get_section_planes()
            return [SectionPlaneResponse(**p) for p in res]
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def add_guide_line(self, body: GuideLineRequest) -> dict:
        """Adiciona uma Linha de Guia / Trena (Frente 18)."""
        try:
            return await self._service.add_guide_line(body.start, body.end, body.is_infinite)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def add_guide_point(self, body: GuidePointRequest) -> dict:
        """Adiciona um Ponto de Construção (Frente 18)."""
        try:
            return await self._service.add_guide_point(body.position)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def get_guides(self) -> GuidesResponse:
        """Retorna todas as guias e pontos da cena (Frente 18)."""
        try:
            res = await self._service.get_guides()
            return GuidesResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def apply_boolean_operation(self, body: BooleanOperationRequest) -> BooleanOperationResponse:
        """Aplica operação booleana sólida CSG (Frente 25)."""
        try:
            res = await self._service.apply_boolean_operation(body.operation, body.main_shape, body.tool_shape)
            return BooleanOperationResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def add_offset_face(self, body: OffsetFaceRequest) -> OffsetFaceResponse:
        """Gera face ou moldura equidistante via Offset (Frente 30)."""
        try:
            res = await self._service.add_offset_face(body.points, body.distance, body.inside, body.create_frame)
            return OffsetFaceResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_executive_pdf(self, body: ExecutivePdfExportRequest) -> ExecutivePdfExportResponse:
        """Exporta Proposta Executiva e Prancha Técnica em PDF Nativo (Frente 29)."""
        try:
            import tempfile, os
            out_dir = tempfile.gettempdir()
            out_path = os.path.join(out_dir, body.output_filename)
            res = await self._service.export_executive_pdf(body.project_name, body.author, body.client_name, out_path)
            return ExecutivePdfExportResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_follow_me_geometry(self, body: FollowMeRequest) -> FollowMeResponse:
        """Gera sólido extrudado ao longo de caminho 3D Follow Me (Frente 31)."""
        try:
            res = await self._service.create_follow_me_geometry(
                body.path_points,
                body.profile_type,
                body.radius,
                body.profile_points,
                body.close_caps
            )
            return FollowMeResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_arc_geometry(self, body: ArcRequest) -> ArcResponse:
        """Gera arco circular 3D paramétrico (Frente 32)."""
        try:
            res = await self._service.create_arc_geometry(body.start, body.end, body.sagitta, body.num_segments)
            return ArcResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def apply_rotation_transform(self, body: RotateTransformRequest) -> RotateTransformResponse:
        """Aplica rotação analítica com transferidor (Frente 33)."""
        try:
            res = await self._service.apply_rotation_transform(body.instance_id, body.pivot, body.axis, body.angle_degrees)
            return RotateTransformResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def audit_nbr16071_safety(self) -> SafetyAuditResponse:
        """Audita conformidade normativa de segurança infantil NBR 16071 (Frente 34)."""
        try:
            res = await self._service.audit_nbr16071_safety()
            return SafetyAuditResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def import_obj_geometry(self, body: ImportObjRequest) -> ImportObjResponse:
        """Importa arquivo Wavefront OBJ e converte para entidades B-Rep do .SKP (Frente 35)."""
        try:
            res = await self._service.import_obj_geometry(body.file_path, body.scale)
            return ImportObjResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_nesting_optimizer(self, body: NestingRequest) -> NestingResponse:
        """Calcula otimização de plano de corte de barras (Frente 36)."""
        try:
            res = await self._service.calculate_nesting_optimizer(body.demanded_pieces, body.stock_bar_length_m)
            return NestingResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_terrain_geometry(self, body: TerrainRequest) -> TerrainResponse:
        """Gera terreno paramétrico e malha topográfica Sandbox (Frente 37)."""
        try:
            res = await self._service.create_terrain_geometry(body.width_m, body.length_m, body.grid_resolution_m, body.slope_x_pct, body.slope_y_pct)
            return TerrainResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_structural_analysis(self, body: StructuralAnalysisRequest) -> StructuralAnalysisResponse:
        """Calcula tensões, flecha e estabilidade de viga segundo NBR 7190 (Frente 38)."""
        try:
            res = await self._service.calculate_structural_analysis(body.span_length_m, body.load_kn_per_m, body.section_type, body.diameter_m, body.width_m, body.height_m)
            return StructuralAnalysisResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def apply_scale_transform(self, body: ScaleRequest) -> ScaleResponse:
        """Aplica escala paramétrica à instância (Frente 39)."""
        try:
            res = await self._service.apply_scale_transform(body.instance_id, body.scale_factors, body.pivot)
            return ScaleResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_cam_dxf(self, body: ExportCamDxfRequest) -> ExportCamDxfResponse:
        """Exporta contornos para máquinas CNC e Corte a Laser em DXF (Frente 40)."""
        try:
            res = await self._service.export_cam_dxf(body.parts, body.output_filename)
            return ExportCamDxfResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_camera_path(self, body: CameraPathRequest) -> CameraPathResponse:
        """Gera interpolacao suave Catmull-Rom para sobrevoo de camera (Frente 41)."""
        try:
            res = await self._service.calculate_camera_path(body.waypoints, body.frames_per_segment)
            return CameraPathResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_point_cloud_xyz(self, body: PointCloudExportRequest) -> PointCloudExportResponse:
        """Exporta nuvem de pontos 3D LiDAR em formato ASCII XYZ (Frente 42)."""
        try:
            res = await self._service.export_point_cloud_xyz(body.output_filename)
            return PointCloudExportResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_maintenance_plan(self, body: MaintenancePlanRequest) -> MaintenancePlanResponse:
        """Gera plano normativo de manutencao preventiva NBR 16071-7 (Frente 43)."""
        try:
            res = await self._service.generate_maintenance_plan(body.installation_date_iso, body.environment_type)
            return MaintenancePlanResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def apply_mirror_transform(self, body: MirrorRequest) -> MirrorResponse:
        """Aplica espelhamento e simetria 3D de Householder (Frente 44)."""
        try:
            res = await self._service.apply_mirror_transform(body.instance_id, body.plane_normal, body.plane_point)
            return MirrorResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_qr_tag_svg(self, body: QrTagExportRequest) -> QrTagExportResponse:
        """Gera placa de identificacao patrimonial com QR Code em SVG (Frente 45)."""
        try:
            res = await self._service.export_qr_tag_svg(body.serial_number, body.product_name, body.output_filename)
            return QrTagExportResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def simulate_swing_kinematics(self, body: SwingKinematicsRequest) -> SwingKinematicsResponse:
        """Simula cinematica e seguranca de balanco NBR 16071 (Frente 46)."""
        try:
            res = await self._service.simulate_swing_kinematics(
                body.chain_length_m,
                body.user_mass_kg,
                body.initial_angle_deg,
                body.seat_height_at_rest_m,
                body.damping_ratio,
                body.total_time_s,
                body.fps
            )
            return SwingKinematicsResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_art_pdf(self, body: ArtReportRequest) -> ArtReportResponse:
        """Gera minuta de ART / RRT em PDF vetorial (Frente 47)."""
        try:
            res = await self._service.generate_art_pdf(
                body.professional_name,
                body.crea_cau,
                body.rnp,
                body.contractor,
                body.location,
                body.project_name,
                body.output_filename
            )
            return ArtReportResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def inspect_wall_thickness(self, body: WallThicknessRequest) -> WallThicknessResponse:
        """Inspeciona espessura de paredes de pecas rotomoldadas (Frente 48)."""
        try:
            res = await self._service.inspect_wall_thickness(body.min_thickness_mm, body.max_thickness_mm)
            return WallThicknessResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def optimize_cargo_load(self, body: CargoLoadRequest) -> CargoLoadResponse:
        """Otimiza a cubagem e alocacao 3D de volumes no transporte (Frente 49)."""
        try:
            res = await self._service.optimize_cargo_load(body.packages, body.vehicle_type)
            return CargoLoadResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_technical_sketch(self, body: TechnicalSketchRequest) -> TechnicalSketchResponse:
        """Gera prancha em SVG com traco arquitetonico estilizado e overshoot (Frente 50)."""
        try:
            res = await self._service.generate_technical_sketch(
                body.dihedral_angle_threshold_deg,
                body.overshoot_mm,
                body.output_filename
            )
            return TechnicalSketchResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_spiral_tube(self, body: SpiralTubeRequest) -> SpiralTubeResponse:
        """Gera geometria 3D de toboga espiral helicoidal (Frente 51)."""
        try:
            res = await self._service.generate_spiral_tube(
                body.radius_m,
                body.height_m,
                body.turns,
                body.tube_radius_m,
                body.segments_per_turn,
                body.tube_segments,
                body.is_open_gutter
            )
            return SpiralTubeResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_overturn_stability(self, body: OverturnStabilityRequest) -> OverturnStabilityResponse:
        """Calcula estabilidade ao tombamento sob vento e empuxo (Frente 52)."""
        try:
            res = await self._service.calculate_overturn_stability(
                body.total_mass_kg,
                body.cg_position,
                body.base_support_points,
                body.wind_speed_km_h,
                body.exposed_frontal_area_m2,
                body.lateral_live_load_n,
                body.live_load_height_m
            )
            return OverturnStabilityResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_field_inspection_html(self, body: FieldInspectionRequest) -> FieldInspectionResponse:
        """Exporta checklist de inspecao de campo NBR 16071-7 em HTML5 offline (Frente 53)."""
        try:
            res = await self._service.export_field_inspection_html(
                body.park_name,
                body.inspector_name,
                body.inspection_date,
                None,
                body.output_filename
            )
            return FieldInspectionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_angle_dimension(self, body: AngleDimensionRequest) -> AngleDimensionResponse:
        """Calcula cota angular e arco grafico 3D entre 3 pontos (Frente 54)."""
        try:
            res = await self._service.calculate_angle_dimension(
                body.vertex_point,
                body.point_a,
                body.point_b,
                body.arc_radius_m
            )
            return AngleDimensionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_fastener_torque(self, body: FastenerTorqueRequest) -> FastenerTorqueResponse:
        """Dimensiona fixador e calcula torque normativo NBR 7190 / ISO 898 (Frente 55)."""
        try:
            res = await self._service.calculate_fastener_torque(
                body.timber_thickness_mm,
                body.steel_plate_thickness_mm,
                body.bolt_standard,
                body.material_grade,
                body.friction_factor_k
            )
            return FastenerTorqueResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_hip_roof(self, body: HipRoofRequest) -> HipRoofResponse:
        """Gera geometria 3D de telhado de 4 aguas ou piramidal (Frente 56)."""
        try:
            res = await self._service.generate_hip_roof(
                body.base_width_m,
                body.base_length_m,
                body.base_height_m,
                body.pitch_deg,
                body.overhang_m
            )
            return HipRoofResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def simulate_hic_impact(self, body: HicRequest) -> HicResponse:
        """Simula impacto HIC e piso amortecedor NBR 16071-3 (Frente 57)."""
        try:
            res = await self._service.simulate_hic_impact(
                body.fall_height_m,
                body.surface_type,
                body.installed_thickness_mm
            )
            return HicResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_zebra_label(self, body: ZebraLabelRequest) -> ZebraLabelResponse:
        """Exporta etiqueta termica industrial Zebra ZPL II e SVG (Frente 58)."""
        try:
            res = await self._service.export_zebra_label(
                body.part_name,
                body.part_sku,
                body.dimensions_mm,
                body.lot_batch,
                body.output_zpl_filename,
                body.output_svg_filename
            )
            return ZebraLabelResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_exploded_trails(self, body: ExplodedTrailsRequest) -> ExplodedTrailsResponse:
        """Calcula linhas tracejadas de trajetoria para vista explodida (Frente 59)."""
        try:
            res = await self._service.calculate_exploded_trails(
                body.parts,
                body.dash_size_m,
                body.gap_size_m
            )
            return ExplodedTrailsResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_carbon_footprint(self, body: CarbonFootprintRequest) -> CarbonFootprintResponse:
        """Calcula balanco de carbono e sustentabilidade florestal (Frente 60)."""
        try:
            res = await self._service.calculate_carbon_footprint(
                body.timber_volume_m3,
                body.steel_weight_kg,
                body.plastic_weight_kg,
                body.transport_distance_km
            )
            return CarbonFootprintResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def manage_attribute_dictionary(self, body: AttributeDictionaryRequest) -> AttributeDictionaryResponse:
        """Manipula dicionarios de atributos nativos e componentes dinamicos (Frente 61)."""
        try:
            res = await self._service.manage_attribute_dictionary(
                body.dict_name,
                body.key,
                body.value,
                body.evaluate_formula,
                body.context_vars
            )
            return AttributeDictionaryResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def manage_tag_folder(self, body: TagFolderRequest) -> TagFolderResponse:
        """Cria e gerencia pastas de tags hierarquicas (Frente 62)."""
        try:
            res = await self._service.manage_tag_folder(
                body.folder_id,
                body.name,
                body.parent_id,
                body.visible,
                body.tags_to_add
            )
            return TagFolderResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def configure_edge_styles(self, body: EdgeStylesRequest) -> EdgeStylesResponse:
        """Configura opcoes nativas de estilos de arestas do SketchUp (Frente 63)."""
        try:
            res = await self._service.configure_edge_styles(body.model_dump())
            return EdgeStylesResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_two_point_perspective(self, body: TwoPointPerspectiveRequest) -> TwoPointPerspectiveResponse:
        """Calcula matriz de camera com Perspectiva de Dois Pontos (Frente 64)."""
        try:
            res = await self._service.calculate_two_point_perspective(
                body.eye,
                body.target,
                body.fov_deg,
                body.aspect_ratio
            )
            return TwoPointPerspectiveResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def project_texture_uv(self, body: TextureProjectionRequest) -> TextureProjectionResponse:
        """Calcula coordenadas UV analiticas para projecao planar ou cilindrica (Frente 65)."""
        try:
            res = await self._service.project_texture_uv(
                body.vertices,
                body.projection_type,
                body.plane_normal,
                body.scale_u_m,
                body.scale_v_m,
                body.rotation_deg
            )
            return TextureProjectionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


    async def weld_curve_edges(self, body: CurveWeldRequest) -> CurveResponse:
        """Solda arestas contiguas em curvas SUCurveRef (Frente 66)."""
        try:
            res = await self._service.weld_curve_edges(body.edges, body.tolerance)
            return CurveResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_arc_curve(self, body: CurveArcCreateRequest) -> CurveResponse:
        """Cria arco analitico parametrico SUArcCurveRef (Frente 66)."""
        try:
            res = await self._service.create_arc_curve(
                body.center,
                body.radius,
                body.normal,
                body.start_angle_rad,
                body.end_angle_rad,
                body.num_segments
            )
            return CurveResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_or_reverse_section_plane(self, body: SectionPlaneCreateRequest) -> SUSectionPlaneResponse:
        """Cria ou configura plano de corte SUSectionPlaneRef (Frente 67)."""
        try:
            res = await self._service.create_or_reverse_section_plane(
                body.name,
                body.symbol,
                body.normal,
                body.distance,
                body.is_active
            )
            return SUSectionPlaneResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def slice_geometry_by_plane(self, body: SectionPlaneSliceRequest) -> SUSectionPlaneResponse:
        """Fatia malha 3D gerando contornos e loops de corte transversal (Frente 67)."""
        try:
            res = await self._service.slice_geometry_by_plane(
                body.vertices,
                body.faces,
                body.plane_equation
            )
            return SUSectionPlaneResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def resolve_face_render_style(self, body: FaceStyleResolveRequest) -> FaceStyleResponse:
        """Resolve shaders e propriedades PBR de estilos de faces (Frente 68)."""
        try:
            res = await self._service.resolve_face_render_style(
                body.mode,
                body.material_color,
                body.texture_path,
                body.opacity,
                body.is_back_face
            )
            return FaceStyleResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_glass_pbr_material(self, body: GlassMaterialRequest) -> FaceStyleResponse:
        """Cria material de vidro fisico PBR (Frente 68)."""
        try:
            res = await self._service.create_glass_pbr_material(
                body.name,
                body.color,
                body.opacity,
                body.refraction_index
            )
            return FaceStyleResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_presentation_scene(self, body: SceneCreateRequest) -> SceneAnimationResponse:
        """Cria definicao canonica de cena SUSceneRef (Frente 69)."""
        try:
            res = await self._service.create_presentation_scene(
                body.name,
                body.eye,
                body.target,
                body.up,
                body.fov,
                body.is_orthographic,
                body.transition_time,
                body.delay_time,
                body.include_in_animation
            )
            return SceneAnimationResponse(
                entity_type="SUSceneRef",
                timeline=res,
                status=res["status"]
            )
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_scene_animation_timeline(self, body: SceneAnimationTimelineRequest) -> SceneAnimationResponse:
        """Gera timeline continua de transicao entre cenas (Frente 69)."""
        try:
            res = await self._service.generate_scene_animation_timeline(
                body.scenes,
                body.fps,
                body.loop
            )
            return SceneAnimationResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_shadow_and_sun_info(self, body: ShadowInfoRequest) -> ShadowInfoResponse:
        """Calcula parametros de iluminacao solar e sombreamento SUShadowInfoRef (Frente 70)."""
        try:
            res = await self._service.calculate_shadow_and_sun_info(
                body.year,
                body.month,
                body.day,
                body.hour,
                body.minute,
                body.latitude,
                body.longitude,
                body.tz_offset,
                body.north_angle,
                body.light_intensity,
                body.dark_intensity,
                body.display_shadows,
                body.use_sun_for_shading,
                body.edges_cast_shadows
            )
            return ShadowInfoResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


    async def create_screen_text(self, body: ScreenTextRequest) -> TextResponse:
        try:
            res = await self._service.create_screen_text(
                body.text,
                body.screen_x,
                body.screen_y,
                body.font_name,
                body.font_size_pt,
                body.color_hex,
                body.bold,
                body.italic
            )
            return TextResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_leader_text(self, body: LeaderTextRequest) -> TextResponse:
        try:
            res = await self._service.create_leader_text(
                body.text,
                body.anchor_point,
                body.offset_vector,
                body.arrow_type,
                body.font_name,
                body.font_size_pt,
                body.color_hex
            )
            return TextResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_dimension_linear(self, body: DimensionLinearRequest) -> DimensionLinearResponse:
        try:
            res = await self._service.create_dimension_linear(
                body.start_pt,
                body.end_pt,
                body.offset_distance,
                body.plane_normal,
                body.arrow_type,
                body.unit,
                body.precision,
                body.custom_text
            )
            return DimensionLinearResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_guide_line_infinite(self, body: GuideLineInfiniteRequest) -> InfiniteGuideResponse:
        try:
            res = await self._service.create_guide_line_infinite(
                body.point,
                body.direction,
                body.end_point,
                body.is_infinite,
                body.extent_m
            )
            return InfiniteGuideResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_guide_point(self, body: GuidePointCreateRequest) -> InfiniteGuideResponse:
        try:
            res = await self._service.create_guide_point(body.point)
            return InfiniteGuideResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def intersect_guide_lines(self, body: GuideLineIntersectRequest) -> InfiniteGuideResponse:
        try:
            res = await self._service.intersect_guide_lines(body.line1, body.line2, body.tolerance)
            return InfiniteGuideResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def configure_alpha_material(self, body: AlphaMaterialRequest) -> AlphaTextureResponse:
        try:
            res = await self._service.configure_alpha_material(
                body.name,
                body.texture_path,
                body.alpha_mode,
                body.alpha_threshold,
                body.double_sided
            )
            return AlphaTextureResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_face_me_matrix(self, body: FaceMeRequest) -> AlphaTextureResponse:
        try:
            res = await self._service.calculate_face_me_matrix(
                body.instance_position,
                body.camera_position,
                body.axial_only
            )
            return AlphaTextureResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def resolve_nested_hierarchy_node(self, body: NestedHierarchyResolveRequest) -> NestedHierarchyResponse:
        try:
            res = await self._service.resolve_nested_hierarchy_node(body.node_id, body.path_to_node)
            return NestedHierarchyResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def convert_world_transform_to_local(self, body: WorldToLocalRequest) -> NestedHierarchyResponse:
        try:
            res = await self._service.convert_world_transform_to_local(
                body.desired_world_matrix,
                body.parent_world_matrix
            )
            return NestedHierarchyResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


    async def create_dimension_radial(self, body: DimensionRadialRequest) -> DimensionRadialResponse:
        try:
            res = await self._service.create_dimension_radial(
                body.center,
                body.radius,
                body.normal,
                body.angle_deg,
                body.is_diameter,
                body.leader_length,
                body.unit,
                body.precision
            )
            return DimensionRadialResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def configure_fog_style(self, body: FogStyleRequest) -> FogStyleResponse:
        try:
            res = await self._service.configure_fog_style(
                body.enabled,
                body.start_dist_m,
                body.end_dist_m,
                body.color_hex
            )
            return FogStyleResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_auto_fog_from_bbox(self, body: AutoFogRequest) -> FogStyleResponse:
        try:
            res = await self._service.calculate_auto_fog_from_bbox(
                body.min_point,
                body.max_point,
                body.color_hex
            )
            return FogStyleResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def process_mesh_smoothing(self, body: MeshSmoothingRequest) -> MeshSmoothingResponse:
        try:
            res = await self._service.process_mesh_smoothing(
                body.vertices,
                body.faces,
                body.angle_threshold_deg
            )
            return MeshSmoothingResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_section_hatch_lines(self, body: SectionHatchRequest) -> SectionHatchResponse:
        try:
            res = await self._service.generate_section_hatch_lines(
                body.closed_loop_3d,
                body.pattern,
                body.spacing_m,
                body.angle_deg
            )
            return SectionHatchResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def set_geo_location(self, body: GeoReferenceRequest) -> GeoReferenceResponse:
        try:
            res = await self._service.set_geo_location(
                body.latitude,
                body.longitude,
                body.altitude_m,
                body.north_angle_deg,
                body.city,
                body.country
            )
            return GeoReferenceResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def local_point_to_wgs84(self, body: LocalToGeoRequest) -> GeoReferenceResponse:
        try:
            res = await self._service.local_point_to_wgs84(
                body.local_xyz_m,
                body.origin_lat,
                body.origin_lon,
                body.origin_alt_m,
                body.north_angle_deg
            )
            return GeoReferenceResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def triangulate_face_with_holes(self, body: PolyMeshHolesRequest) -> PolyMeshResponse:
        """Triangula face plana com furos internos SUPolyMeshRef (Frente 81)."""
        try:
            res = await self._service.triangulate_face_with_holes(
                body.outer_loop_3d,
                body.inner_loops_3d
            )
            return PolyMeshResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_align_view(self, body: AlignViewRequest) -> AlignViewResponse:
        """Calcula parâmetros de câmera perpendicular à face (Align View) (Frente 82)."""
        try:
            res = await self._service.calculate_align_view(
                body.face_vertices,
                body.fov_deg,
                body.margin_factor
            )
            return AlignViewResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def configure_background_sky(self, body: BackgroundSkyStyleRequest) -> BackgroundSkyStyleResponse:
        """Configura estilos de céu, solo e horizonte SUStyleRef (Frente 83)."""
        try:
            res = await self._service.configure_background_sky(
                body.sky_enabled,
                body.ground_enabled,
                body.sky_color,
                body.ground_color,
                body.horizon_color,
                body.background_color,
                body.ground_transparency_percent,
                body.show_horizon
            )
            return BackgroundSkyStyleResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_dimension_tolerance(self, body: DimensionToleranceRequest) -> DimensionToleranceResponse:
        """Calcula tolerâncias dimensionais ISO 2768 / NBR 6492 (Frente 84)."""
        try:
            res = await self._service.calculate_dimension_tolerance(
                body.nominal_val,
                body.unit,
                body.tolerance_type,
                body.upper_tol,
                body.lower_tol,
                body.iso_class,
                body.precision
            )
            return DimensionToleranceResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def record_undo_operation(self, body: UndoRedoRecordRequest) -> UndoRedoActionResponse:
        """Registra operação reversível na pilha transacional (Frente 85)."""
        try:
            res = await self._service.record_undo_operation(
                body.name,
                body.action_type,
                body.target_id,
                body.before_state,
                body.after_state
            )
            return UndoRedoActionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def execute_undo(self) -> UndoRedoActionResponse:
        """Desfaz a última operação registrada (Frente 85)."""
        try:
            res = await self._service.execute_undo()
            return UndoRedoActionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def execute_redo(self) -> UndoRedoActionResponse:
        """Refaz a última operação desfeita (Frente 85)."""
        try:
            res = await self._service.execute_redo()
            return UndoRedoActionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def get_undo_redo_history(self) -> UndoRedoStatusResponse:
        """Retorna histórico e profundidade das pilhas de Undo e Redo (Frente 85)."""
        try:
            res = await self._service.get_undo_redo_history()
            return UndoRedoStatusResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def subdivide_quad_mesh(self, body: SubDSubdivisionRequest) -> SubDMeshResponse:
        """Aplica subdivisão Catmull-Clark sobre malha de controle QuadFace (Frente 86)."""
        try:
            res = await self._service.subdivide_quad_mesh(
                body.vertices,
                body.faces,
                body.iterations
            )
            return SubDMeshResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_auto_section_dimensions(self, body: SectionDimensionRequest) -> SectionDimensionResponse:
        """Gera cotas ortogonais e marcas de nível NBR 6492 em cortes (Frente 87)."""
        try:
            res = await self._service.generate_auto_section_dimensions(
                body.cut_loops_3d,
                body.offset_m,
                body.unit,
                body.precision
            )
            return SectionDimensionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_spherical_panorama(self, body: PanoramaSphericalRequest) -> PanoramaSphericalResponse:
        """Calcula cubemap de 6 câmeras e malha de raios equirretangulares 360° (Frente 88)."""
        try:
            res = await self._service.calculate_spherical_panorama(
                body.eye_position,
                body.horizontal_samples,
                body.vertical_samples,
                body.sphere_radius_m
            )
            return PanoramaSphericalResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def detect_component_clashes(self, body: ClashDetectionRequest) -> ClashDetectionResponse:
        """Detecta colisões físicas (Hard Clash) e folgas (Clearance Clash) entre componentes (Frente 89)."""
        try:
            res = await self._service.detect_component_clashes(
                body.components,
                body.clearance_tolerance_m
            )
            return ClashDetectionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_mesh_mass_properties(self, body: MassPropertiesRequest) -> MassPropertiesResponse:
        """Calcula volume, massa, Centro de Gravidade e inércia de malha B-Rep fechada (Frente 90)."""
        try:
            res = await self._service.calculate_mesh_mass_properties(
                body.vertices,
                body.triangles,
                body.material_type,
                body.custom_density_kg_m3
            )
            return MassPropertiesResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def create_solid_shell(self, body: SolidShellRequest) -> SolidShellResponse:
        """Gera casca sólida volumétrica B-Rep a partir de superfícies (Frente 91)."""
        try:
            res = await self._service.create_solid_shell(
                body.vertices,
                body.faces,
                body.thickness_m,
                body.inwards
            )
            return SolidShellResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def configure_spot_light(self, body: PhotometricSpotLightRequest) -> PhotometricSpotLightResponse:
        """Configura parâmetros de holofote fotométrico spot Three.js (Frente 92)."""
        try:
            res = await self._service.configure_spot_light(
                body.position,
                body.target,
                body.lumens,
                body.color_temperature_k,
                body.beam_angle_deg,
                body.penumbra_percent,
                body.max_distance_m,
                body.cast_shadows
            )
            return PhotometricSpotLightResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_pipe_route(self, body: PipingRouteRequest) -> PipingRouteResponse:
        """Roteia tubulação e dutos paramétricos 3D com cotovelos e curvas (Frente 93)."""
        try:
            res = await self._service.generate_pipe_route(
                body.route_points,
                body.outer_diameter_mm,
                body.wall_thickness_mm,
                body.radial_segments,
                body.bend_radius_factor
            )
            return PipingRouteResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_camera_animation_path(self, body: CameraAnimationPathRequest) -> CameraAnimationPathResponse:
        """Gera trajetória cinematográfica contínua de câmera (Orbit ou Flythrough) (Frente 94)."""
        try:
            res = await self._service.generate_camera_animation_path(
                body.mode,
                body.target_point,
                body.radius_m,
                body.height_m,
                body.start_angle_deg,
                body.total_rotation_deg,
                body.waypoints,
                body.duration_seconds,
                body.fps,
                body.fov_deg
            )
            return CameraAnimationPathResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_cnc_cutlist(self, body: CamCutlistRequest) -> CamCutlistResponse:
        """Processa peças e produz tabela industrial de corte CNC com CSV (Frente 95)."""
        try:
            res = await self._service.generate_cnc_cutlist(
                body.parts,
                body.saw_kerf_mm,
                body.trim_margin_mm,
                body.export_csv
            )
            return CamCutlistResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_wall_with_openings(self, body: ArchitecturalWallRequest) -> ArchitecturalWallResponse:
        """Gera parede paramétrica 3D com vãos de portas e janelas (Frente 96)."""
        try:
            res = await self._service.generate_wall_with_openings(
                body.start_pt,
                body.end_pt,
                body.height_m,
                body.thickness_m,
                body.openings
            )
            return ArchitecturalWallResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def unfold_sheet_metal(self, body: SheetMetalUnfoldRequest) -> SheetMetalUnfoldResponse:
        """Calcula o blank planificado e linhas de dobra DIN 6935 (Frente 97)."""
        try:
            res = await self._service.unfold_sheet_metal(
                body.base_length_mm,
                body.base_width_mm,
                body.thickness_mm,
                body.inner_radius_mm,
                body.k_factor,
                body.flanges
            )
            return SheetMetalUnfoldResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_projected_shadow(self, body: ShadowCastingRequest) -> ShadowCastingResponse:
        """Calcula projeção de sombra do oclusor sobre o solo ou superfície (Frente 98)."""
        try:
            res = await self._service.calculate_projected_shadow(
                body.occluder_vertices,
                body.sun_direction,
                body.ground_elevation_z
            )
            return ShadowCastingResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def configure_water_surface(self, body: WaterMaterialConfigRequest) -> WaterMaterialConfigResponse:
        """Configura shader PBR de água, ondas Gerstner e cáusticas (Frente 99)."""
        try:
            res = await self._service.configure_water_surface(
                body.shallow_color_hex,
                body.deep_color_hex,
                body.clarity_percent,
                body.wave_amplitude_m,
                body.wave_wavelength_m,
                body.wave_speed_m_s,
                body.ior,
                body.caustics_intensity,
                body.enable_foam
            )
            return WaterMaterialConfigResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_mesh_lod_chain(self, body: SkpLODChainRequest) -> SkpLODChainResponse:
        """Gera cadeia de 3 níveis de detalhe (LOD0, LOD1, LOD2) para Three.js (Frente 100)."""
        try:
            res = await self._service.generate_mesh_lod_chain(
                body.vertices,
                body.triangles,
                body.lod1_target_ratio,
                body.lod2_target_ratio
            )
            return SkpLODChainResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_stair(self, body: StairGeneratorRequest) -> StairGeneratorResponse:
        """Gera escada paramétrica e dimensionamento ergonômico Blondel NBR 9050 (Frente 101)."""
        try:
            res = await self._service.generate_stair(
                body.total_height_m,
                body.stair_width_m,
                body.stair_type,
                body.origin_xyz,
                body.add_handrail
            )
            return StairGeneratorResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_voronoi_panel(self, body: VoronoiPanelRequest) -> VoronoiPanelResponse:
        """Gera painel decorativo ou estrutural com perfurações Voronoi (Frente 102)."""
        try:
            res = await self._service.generate_voronoi_panel(
                body.width_m,
                body.height_m,
                body.thickness_m,
                body.num_seeds,
                body.seed_random_seed,
                body.cell_inset_ratio
            )
            return VoronoiPanelResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_wind_pressure(self, body: WindPressureRequest) -> WindPressureResponse:
        """Calcula pressão dinâmica e forças estáticas de vento NBR 6123 (Frente 103)."""
        try:
            res = await self._service.calculate_wind_pressure(
                body.basic_speed_v0_m_s,
                body.terrain_category,
                body.building_height_m,
                body.facade_width_m,
                body.facade_length_m,
                body.topographic_s1,
                body.statistical_s3
            )
            return WindPressureResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def configure_atmospheric_sky(self, body: AtmosphericSkyRequest) -> AtmosphericSkyResponse:
        """Configura céu físico Rayleigh/Mie e sol Three.js (Frente 104)."""
        try:
            res = await self._service.configure_atmospheric_sky(
                body.solar_elevation_deg,
                body.solar_azimuth_deg,
                body.turbidity,
                body.rayleigh,
                body.mie_coefficient,
                body.mie_directional_g
            )
            return AtmosphericSkyResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def export_ifc4_bim(self, body: IFC4BimExportRequest) -> IFC4BimExportResponse:
        """Compila modelo no formato texto físico STEP ISO-10303-21 IFC4 LOD 350 (Frente 105)."""
        try:
            res = await self._service.export_ifc4_bim(
                body.project_name,
                body.elements,
                body.author,
                body.organization
            )
            return IFC4BimExportResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # ========================================================================
    # Frentes 106 a 115: Física, Fatiamento 3D, MEP, Conforto, Aço e SINAPI 5D
    # ========================================================================

    async def simulate_rigid_body_physics(self, body: RigidBodyPhysicsRequest) -> RigidBodyPhysicsResponse:
        """Simula dinâmica Newtoniana e colisões de corpos rígidos (Frente 106)."""
        try:
            res = await self._service.simulate_rigid_body_physics(
                body.bodies, body.gravity_z, body.ground_z,
                body.total_time_s, body.time_step_s, body.restitution, body.friction_coeff
            )
            return RigidBodyPhysicsResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def slice_3d_print_fdm(self, body: Slicing3dPrintRequest) -> Slicing3dPrintResponse:
        """Calcula métricas de fatiamento FDM e fatiador planar (Frente 107)."""
        try:
            res = await self._service.slice_3d_print_fdm(
                body.vertices, body.triangles,
                body.layer_height_mm, body.infill_percent, body.print_speed_mm_s
            )
            return Slicing3dPrintResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_retaining_wall_stability(self, body: RetainingWallRequest) -> RetainingWallResponse:
        """Calcula estabilidade ao tombamento/deslizamento de muro de arrimo NBR 11682 (Frente 108)."""
        try:
            res = await self._service.calculate_retaining_wall_stability(
                body.wall_height_m, body.stem_top_thickness_m, body.stem_bottom_thickness_m,
                body.base_width_m, body.base_thickness_m, body.soil_friction_angle_deg,
                body.soil_unit_weight_kn_m3, body.concrete_unit_weight_kn_m3, body.surcharge_kpa
            )
            return RetainingWallResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_hydraulic_piping(self, body: HydraulicPipingRequest) -> HydraulicPipingResponse:
        """Calcula perda de carga contínua/localizada Hazen-Williams NBR 5626 (Frente 109)."""
        try:
            res = await self._service.calculate_hydraulic_piping(
                body.pipe_diameter_dn_mm, body.flow_rate_l_s, body.pipe_roughness_c,
                body.inlet_pressure_mca, body.waypoints, body.fittings
            )
            return HydraulicPipingResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_electrical_conduit(self, body: ElectricalConduitRequest) -> ElectricalConduitResponse:
        """Dimensiona taxa de ocupação e queda de tensão em eletrodutos NBR 5410 (Frente 110)."""
        try:
            res = await self._service.calculate_electrical_conduit(
                body.conduit_nominal_dn_mm, body.circuit_current_amperes, body.cable_gauge_mm2,
                body.cables_count, body.circuit_length_m, body.voltage_v, body.power_factor
            )
            return ElectricalConduitResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_thermal_comfort(self, body: ThermalComfortRequest) -> ThermalComfortResponse:
        """Calcula transmitância U e capacidade Ct de envoltória NBR 15220 (Frente 111)."""
        try:
            res = await self._service.calculate_thermal_comfort(
                body.layers, body.rsi_m2_k_w, body.rse_m2_k_w, body.target_bioclimatic_zone
            )
            return ThermalComfortResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_room_acoustics(self, body: RoomAcousticsRequest) -> RoomAcousticsResponse:
        """Calcula espectro RT60 e absorção acústica de Sabine NBR 10152 (Frente 112)."""
        try:
            res = await self._service.calculate_room_acoustics(
                body.room_width_m, body.room_length_m, body.room_height_m,
                body.surfaces, body.room_type
            )
            return RoomAcousticsResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_daylight_factor(self, body: DaylightFactorRequest) -> DaylightFactorResponse:
        """Calcula Fator de Luz Diurna (FLD %) e iluminância interna NBR 15215 (Frente 113)."""
        try:
            res = await self._service.calculate_daylight_factor(
                body.room_width_m, body.room_depth_m, body.room_height_m,
                body.window_width_m, body.window_height_m, body.window_sill_height_m,
                body.glass_transmittance, body.external_horizontal_lux,
                body.average_internal_reflectance, body.obstruction_angle_deg
            )
            return DaylightFactorResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_steel_profile(self, body: SteelProfileRequest) -> SteelProfileResponse:
        """Gera perfil metálico I/W e calcula propriedades geométricas NBR 8800 (Frente 114)."""
        try:
            res = await self._service.generate_steel_profile(
                body.depth_d_mm, body.flange_width_bf_mm, body.web_thickness_tw_mm,
                body.flange_thickness_tf_mm, body.length_m
            )
            return SteelProfileResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_bim_5d_sinapi_budget(self, body: Bim5dSinapiCostRequest) -> Bim5dSinapiCostResponse:
        """Calcula orçamento analítico BIM 5D, BDI e Curva ABC com base SINAPI (Frente 115)."""
        try:
            res = await self._service.calculate_bim_5d_sinapi_budget(
                body.elements, body.bdi_percent, body.social_charges_percent
            )
            return Bim5dSinapiCostResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # ---------------------------------------------------------
    # Frentes 116 a 145: Métodos do Controller
    # ---------------------------------------------------------
    async def calculate_stormwater_drainage(self, body: StormwaterDrainageRequest) -> StormwaterDrainageResponse:
        try:
            res = await self._service.calculate_stormwater_drainage(**body.model_dump())
            return StormwaterDrainageResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_permeable_pavement(self, body: PermeablePavementRequest) -> PermeablePavementResponse:
        try:
            res = await self._service.calculate_permeable_pavement(**body.model_dump())
            return PermeablePavementResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_sewer_network(self, body: SewerNetworkGravityRequest) -> SewerNetworkGravityResponse:
        try:
            res = await self._service.calculate_sewer_network(**body.model_dump())
            return SewerNetworkGravityResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_detention_basin(self, body: DetentionBasinHydrologyRequest) -> DetentionBasinHydrologyResponse:
        try:
            res = await self._service.calculate_detention_basin(**body.model_dump())
            return DetentionBasinHydrologyResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_earthwork_bruckner(self, body: EarthworkBrucknerRequest) -> EarthworkBrucknerResponse:
        try:
            res = await self._service.calculate_earthwork_bruckner(**body.model_dump())
            return EarthworkBrucknerResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_slope_stability_bishop(self, body: SlopeStabilityBishopRequest) -> SlopeStabilityBishopResponse:
        try:
            res = await self._service.calculate_slope_stability_bishop(**body.model_dump())
            return SlopeStabilityBishopResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_deep_foundations_piles(self, body: DeepFoundationsPilesRequest) -> DeepFoundationsPilesResponse:
        try:
            res = await self._service.calculate_deep_foundations_piles(**body.model_dump())
            return DeepFoundationsPilesResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_shallow_footings(self, body: ShallowFootingsRequest) -> ShallowFootingsResponse:
        try:
            res = await self._service.calculate_shallow_footings(**body.model_dump())
            return ShallowFootingsResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_gabion_wall(self, body: GabionRetainingWallRequest) -> GabionRetainingWallResponse:
        try:
            res = await self._service.calculate_gabion_wall(**body.model_dump())
            return GabionRetainingWallResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_concrete_formwork(self, body: ConcreteFormworkShoringRequest) -> ConcreteFormworkShoringResponse:
        try:
            res = await self._service.calculate_concrete_formwork(**body.model_dump())
            return ConcreteFormworkShoringResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_reinforced_concrete_beam(self, body: ReinforcedConcreteBeamRequest) -> ReinforcedConcreteBeamResponse:
        try:
            res = await self._service.calculate_reinforced_concrete_beam(**body.model_dump())
            return ReinforcedConcreteBeamResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_waffle_slab(self, body: WaffleSlabRequest) -> WaffleSlabResponse:
        try:
            res = await self._service.calculate_waffle_slab(**body.model_dump())
            return WaffleSlabResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_prestressed_concrete(self, body: PrestressedConcreteRequest) -> PrestressedConcreteResponse:
        try:
            res = await self._service.calculate_prestressed_concrete(**body.model_dump())
            return PrestressedConcreteResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_glulam_timber(self, body: GlulamCltTimberRequest) -> GlulamCltTimberResponse:
        try:
            res = await self._service.calculate_glulam_timber(**body.model_dump())
            return GlulamCltTimberResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_space_truss(self, body: SpaceTrussRequest) -> SpaceTrussResponse:
        try:
            res = await self._service.generate_space_truss(**body.model_dump())
            return SpaceTrussResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_fuel_gas_piping(self, body: FuelGasPipingRequest) -> FuelGasPipingResponse:
        try:
            res = await self._service.calculate_fuel_gas_piping(**body.model_dump())
            return FuelGasPipingResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_lightning_spda(self, body: LightningProtectionSpdaRequest) -> LightningProtectionSpdaResponse:
        try:
            res = await self._service.calculate_lightning_spda(**body.model_dump())
            return LightningProtectionSpdaResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_fire_egress(self, body: FireEgressRouteRequest) -> FireEgressRouteResponse:
        try:
            res = await self._service.calculate_fire_egress(**body.model_dump())
            return FireEgressRouteResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_hvac_cooling_load(self, body: HvacThermalLoadRequest) -> HvacThermalLoadResponse:
        try:
            res = await self._service.calculate_hvac_cooling_load(**body.model_dump())
            return HvacThermalLoadResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_photometric_lighting(self, body: PhotometricLumenDesignRequest) -> PhotometricLumenDesignResponse:
        try:
            res = await self._service.calculate_photometric_lighting(**body.model_dump())
            return PhotometricLumenDesignResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_solar_pv(self, body: SolarPhotovoltaicArrayRequest) -> SolarPhotovoltaicArrayResponse:
        try:
            res = await self._service.calculate_solar_pv(**body.model_dump())
            return SolarPhotovoltaicArrayResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_natural_ventilation(self, body: NaturalVentilationRequest) -> NaturalVentilationResponse:
        try:
            res = await self._service.calculate_natural_ventilation(**body.model_dump())
            return NaturalVentilationResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_glazing_fenestration(self, body: GlazingFenestrationRequest) -> GlazingFenestrationResponse:
        try:
            res = await self._service.generate_glazing_fenestration(**body.model_dump())
            return GlazingFenestrationResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_ventilated_facade(self, body: VentilatedFacadeRequest) -> VentilatedFacadeResponse:
        try:
            res = await self._service.calculate_ventilated_facade(**body.model_dump())
            return VentilatedFacadeResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def simulate_wind_cfd_2d(self, body: MiniWindCfd2dRequest) -> MiniWindCfd2dResponse:
        try:
            res = await self._service.simulate_wind_cfd_2d(**body.model_dump())
            return MiniWindCfd2dResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_bim_4d_schedule(self, body: Bim4dGanttScheduleRequest) -> Bim4dGanttScheduleResponse:
        try:
            res = await self._service.generate_bim_4d_schedule(**body.model_dump())
            return Bim4dGanttScheduleResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_bim_7d_cobie(self, body: Bim7dAssetManagementCobieRequest) -> Bim7dAssetManagementCobieResponse:
        try:
            res = await self._service.generate_bim_7d_cobie(**body.model_dump())
            return Bim7dAssetManagementCobieResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_site_logistics(self, body: ConstructionSiteLogisticsRequest) -> ConstructionSiteLogisticsResponse:
        try:
            res = await self._service.calculate_site_logistics(**body.model_dump())
            return ConstructionSiteLogisticsResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def audit_universal_accessibility(self, body: UniversalAccessibilityRequest) -> UniversalAccessibilityResponse:
        try:
            res = await self._service.audit_universal_accessibility(**body.model_dump())
            return UniversalAccessibilityResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def calculate_lca_emissions(self, body: LifeCycleAssessmentRequest) -> LifeCycleAssessmentResponse:
        try:
            res = await self._service.calculate_lca_emissions(**body.model_dump())
            return LifeCycleAssessmentResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # --------------------------------------------------------------------------
    # OPÇÃO A: CONTROLLERS NATIVOS DO SKETCHUP
    # --------------------------------------------------------------------------

    async def position_camera_native(self, body: PositionCameraNativeRequest) -> PositionCameraNativeResponse:
        try:
            res = await self._service.position_camera_native(**body.model_dump())
            return PositionCameraNativeResponse(camera=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def look_around_native(self, body: LookAroundNativeRequest) -> LookAroundNativeResponse:
        try:
            res = await self._service.look_around_native(**body.model_dump())
            return LookAroundNativeResponse(camera=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def walk_step_native(self, body: WalkStepNativeRequest) -> WalkStepNativeResponse:
        try:
            res = await self._service.walk_step_native(**body.model_dump())
            return WalkStepNativeResponse(walk_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def sandbox_smoove(self, body: SandboxSmooveRequest) -> SandboxSmooveResponse:
        try:
            res = await self._service.sandbox_smoove(**body.model_dump())
            return SandboxSmooveResponse(smoove_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def sandbox_stamp(self, body: SandboxStampRequest) -> SandboxStampResponse:
        try:
            res = await self._service.sandbox_stamp(**body.model_dump())
            return SandboxStampResponse(stamp_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def sandbox_drape(self, body: SandboxDrapeRequest) -> SandboxDrapeResponse:
        try:
            res = await self._service.sandbox_drape(**body.model_dump())
            return SandboxDrapeResponse(drape_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def sandbox_flip_edge(self, body: SandboxFlipEdgeRequest) -> SandboxFlipEdgeResponse:
        try:
            res = await self._service.sandbox_flip_edge(**body.model_dump())
            return SandboxFlipEdgeResponse(flip_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def match_photo_calibrate(self, body: MatchPhotoCalibrateRequest) -> MatchPhotoCalibrateResponse:
        try:
            res = await self._service.match_photo_calibrate(**body.model_dump())
            return MatchPhotoCalibrateResponse(calibration=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def watermark_style_configure(self, body: WatermarkStyleConfigureRequest) -> WatermarkStyleConfigureResponse:
        try:
            res = await self._service.watermark_style_configure(**body.model_dump())
            return WatermarkStyleConfigureResponse(watermark_config=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def dynamic_component_interact(self, body: DynamicComponentInteractRequest) -> DynamicComponentInteractResponse:
        try:
            res = await self._service.dynamic_component_interact(**body.model_dump())
            return DynamicComponentInteractResponse(interaction_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def trimble_solid_tools_execute(self, body: TrimbleSolidToolsRequest) -> TrimbleSolidToolsResponse:
        try:
            res = await self._service.trimble_solid_tools_execute(**body.model_dump())
            return TrimbleSolidToolsResponse(operation_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # --------------------------------------------------------------------------
    # OPÇÃO A (PARTE 2): CONTROLLERS NATIVOS DO SKETCHUP
    # --------------------------------------------------------------------------

    async def ifc_classify_component(self, body: IfcClassifyComponentRequest) -> IfcClassifyComponentResponse:
        try:
            res = await self._service.ifc_classify_component(**body.model_dump())
            return IfcClassifyComponentResponse(classification=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def ifc_audit_classifications(self, body: IfcAuditRequest) -> IfcAuditResponse:
        try:
            res = await self._service.ifc_audit_classifications(**body.model_dump())
            return IfcAuditResponse(audit_summary=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_3d_text(self, body: ThreeDTextGenerateRequest) -> ThreeDTextGenerateResponse:
        try:
            res = await self._service.generate_3d_text(**body.model_dump())
            return ThreeDTextGenerateResponse(text_geometry=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def generate_report(self, body: GenerateReportRequest) -> GenerateReportResponse:
        try:
            res = await self._service.generate_report(**body.model_dump())
            return GenerateReportResponse(report_data=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def axes_set_custom(self, body: AxesCustomSetRequest) -> AxesCustomSetResponse:
        try:
            res = await self._service.axes_set_custom(**body.model_dump())
            return AxesCustomSetResponse(axes=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def axes_align_to_face(self, body: AxesAlignFaceRequest) -> AxesAlignFaceResponse:
        try:
            res = await self._service.axes_align_to_face(**body.model_dump())
            return AxesAlignFaceResponse(axes=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def axes_reset(self) -> AxesResetResponse:
        try:
            res = await self._service.axes_reset()
            return AxesResetResponse(axes=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def inspect_entity_edge(self, body: EntityInspectEdgeRequest) -> EntityInspectEdgeResponse:
        try:
            res = await self._service.inspect_entity_edge(**body.model_dump())
            return EntityInspectEdgeResponse(metrics=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def inspect_entity_face(self, body: EntityInspectFaceRequest) -> EntityInspectFaceResponse:
        try:
            res = await self._service.inspect_entity_face(**body.model_dump())
            return EntityInspectFaceResponse(metrics=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def inspect_entity_solid(self, body: EntityInspectSolidRequest) -> EntityInspectSolidResponse:
        try:
            res = await self._service.inspect_entity_solid(**body.model_dump())
            return EntityInspectSolidResponse(metrics=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def component_edit_mode_apply(self, body: ComponentEditModeRequest) -> ComponentEditModeResponse:
        try:
            res = await self._service.component_edit_mode_apply(**body.model_dump())
            return ComponentEditModeResponse(edit_mode_state=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def model_units_configure(self, body: ModelUnitsConfigRequest) -> ModelUnitsConfigResponse:
        try:
            res = await self._service.model_units_configure(**body.model_dump())
            return ModelUnitsConfigResponse(units_config=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def model_units_format(self, body: ModelUnitsFormatRequest) -> ModelUnitsFormatResponse:
        try:
            res = await self._service.model_units_format(**body.model_dump())
            return ModelUnitsFormatResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # --------------------------------------------------------------------------
    # OPÇÃO A (PARTE 3): CONTROLLERS NATIVOS DO SKETCHUP
    # --------------------------------------------------------------------------

    async def texture_pin_transform(self, body: TexturePinTransformRequest) -> TexturePinTransformResponse:
        try:
            res = await self._service.texture_pin_transform(**body.model_dump())
            return TexturePinTransformResponse(mapping=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def color_by_tag_apply(self, body: ColorByTagApplyRequest) -> ColorByTagApplyResponse:
        try:
            res = await self._service.color_by_tag_apply(**body.model_dump())
            return ColorByTagApplyResponse(color_by_tag_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def purge_unused_items(self, body: PurgeUnusedRequest) -> PurgeUnusedResponse:
        try:
            res = await self._service.purge_unused_items(**body.model_dump())
            return PurgeUnusedResponse(purge_result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def make_component_definition(self, body: MakeComponentDefinitionRequest) -> MakeComponentDefinitionResponse:
        try:
            res = await self._service.make_component_definition(**body.model_dump())
            return MakeComponentDefinitionResponse(definition=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def advanced_selection_execute(self, body: AdvancedSelectionRequest) -> AdvancedSelectionResponse:
        try:
            res = await self._service.advanced_selection_execute(**body.model_dump())
            return AdvancedSelectionResponse(**res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def hidden_geometry_configure(self, body: HiddenGeometryConfigRequest) -> HiddenGeometryConfigResponse:
        try:
            res = await self._service.hidden_geometry_configure(**body.model_dump())
            return HiddenGeometryConfigResponse(display_state=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def model_statistics_calculate(self, body: ModelStatisticsRequest) -> ModelStatisticsResponse:
        try:
            res = await self._service.model_statistics_calculate(**body.model_dump())
            return ModelStatisticsResponse(statistics=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # --------------------------------------------------------------------------
    # OPÇÃO A (PARTE 4): CONTROLLERS NATIVOS DO SKETCHUP
    # --------------------------------------------------------------------------

    async def regular_polygon_generate(self, body: RegularPolygonRequest) -> RegularPolygonResponse:
        try:
            res = await self._service.regular_polygon_generate(**body.model_dump())
            return RegularPolygonResponse(polygon=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def freehand_curve_process(self, body: FreehandCurveRequest) -> FreehandCurveResponse:
        try:
            res = await self._service.freehand_curve_process(**body.model_dump())
            return FreehandCurveResponse(curve=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def reverse_orient_faces(self, body: ReverseOrientFacesRequest) -> ReverseOrientFacesResponse:
        try:
            res = await self._service.reverse_orient_faces(**body.model_dump())
            return ReverseOrientFacesResponse(result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def dolly_fov_lens_control(self, body: DollyFovLensRequest) -> DollyFovLensResponse:
        try:
            res = await self._service.dolly_fov_lens_control(**body.model_dump())
            return DollyFovLensResponse(result=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def intersect_faces_compute(self, body: IntersectFacesRequest) -> IntersectFacesResponse:
        try:
            res = await self._service.intersect_faces_compute(**body.model_dump())
            return IntersectFacesResponse(intersection=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def axis_lock_inference(self, body: AxisLockInferenceRequest) -> AxisLockInferenceResponse:
        try:
            res = await self._service.axis_lock_inference(**body.model_dump())
            return AxisLockInferenceResponse(inference=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def ground_sky_style_configure(self, body: GroundSkyStyleRequest) -> GroundSkyStyleResponse:
        try:
            res = await self._service.ground_sky_style_configure(**body.model_dump())
            return GroundSkyStyleResponse(style=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # --------------------------------------------------------------------------
    # OPÇÃO A (PARTE 5): MÉTODOS NATIVOS DO SKETCHUP
    # --------------------------------------------------------------------------

    async def stamp_terrain_apply(self, body: StampTerrainRequest) -> StampTerrainResponse:
        try:
            res = await self._service.stamp_terrain_apply(**body.model_dump())
            return StampTerrainResponse(stamp=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def drape_path_apply(self, body: DrapePathRequest) -> DrapePathResponse:
        try:
            res = await self._service.drape_path_apply(**body.model_dump())
            return DrapePathResponse(drape=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def section_cut_fill_compute(self, body: SectionCutFillRequest) -> SectionCutFillResponse:
        try:
            res = await self._service.section_cut_fill_compute(**body.model_dump())
            return SectionCutFillResponse(cut_fill=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def soft_smooth_edges_process(self, body: SoftSmoothEdgesRequest) -> SoftSmoothEdgesResponse:
        try:
            res = await self._service.soft_smooth_edges_process(**body.model_dump())
            return SoftSmoothEdgesResponse(soft_smooth=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def edge_divide_execute(self, body: EdgeDivideRequest) -> EdgeDivideResponse:
        try:
            res = await self._service.edge_divide_execute(**body.model_dump())
            return EdgeDivideResponse(divide=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def push_pull_create_face_extrude(self, body: PushPullCreateFaceRequest) -> PushPullCreateFaceResponse:
        try:
            res = await self._service.push_pull_create_face_extrude(**body.model_dump())
            return PushPullCreateFaceResponse(extrude=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def bim_ifc_property_set_build(self, body: BimIfcPropertySetRequest) -> BimIfcPropertySetResponse:
        try:
            res = await self._service.bim_ifc_property_set_build(**body.model_dump())
            return BimIfcPropertySetResponse(pset=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    # --------------------------------------------------------------------------
    # OPÇÃO A (PARTE 6): MÉTODOS NATIVOS DO SKETCHUP
    # --------------------------------------------------------------------------

    async def add_detail_sandbox_apply(self, body: AddDetailSandboxRequest) -> AddDetailSandboxResponse:
        try:
            res = await self._service.add_detail_sandbox_apply(**body.model_dump())
            return AddDetailSandboxResponse(detail=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def flip_edge_sandbox_apply(self, body: FlipEdgeSandboxRequest) -> FlipEdgeSandboxResponse:
        try:
            res = await self._service.flip_edge_sandbox_apply(**body.model_dump())
            return FlipEdgeSandboxResponse(flip=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def walk_camera_gravity_step(self, body: WalkCameraGravityRequest) -> WalkCameraGravityResponse:
        try:
            res = await self._service.walk_camera_gravity_step(**body.model_dump())
            return WalkCameraGravityResponse(walk=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def look_around_camera_rotate(self, body: LookAroundCameraRequest) -> LookAroundCameraResponse:
        try:
            res = await self._service.look_around_camera_rotate(**body.model_dump())
            return LookAroundCameraResponse(look_around=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def position_camera_place(self, body: PositionCameraRequest) -> PositionCameraResponse:
        try:
            res = await self._service.position_camera_place(**body.model_dump())
            return PositionCameraResponse(position=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def fog_settings_configure(self, body: FogSettingsRequest) -> FogSettingsResponse:
        try:
            res = await self._service.fog_settings_configure(**body.model_dump())
            return FogSettingsResponse(fog=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def graphic_export_2d_configure(self, body: GraphicExport2DRequest) -> GraphicExport2DResponse:
        try:
            res = await self._service.graphic_export_2d_configure(**body.model_dump())
            return GraphicExport2DResponse(export_2d=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    async def flip_along_axes(self, body: FlipAlongRequest) -> FlipAlongResponse:
        try:
            res = await self._service.flip_along_axes(**body.model_dump())
            return FlipAlongResponse(flip=res)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e




