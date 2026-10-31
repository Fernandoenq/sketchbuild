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
