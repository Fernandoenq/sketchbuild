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
