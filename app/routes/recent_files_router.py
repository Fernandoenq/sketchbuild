"""
Rotas da Pagina Inicial / arquivos recentes. So roteamento -- declara
path, metodo, schema de entrada/saida, e delega pro controller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.controllers.recent_files_controller import RecentFilesController
from app.schemas.recent_files import (
    RecentFileEntry,
    ThumbnailUploadRequest,
    ThumbnailUploadResponse,
)

router = APIRouter(prefix="/recent-files", tags=["recent-files"])


def get_controller() -> RecentFilesController:
    return RecentFilesController()


@router.get(
    "",
    response_model=list[RecentFileEntry],
    summary="Lista os .skp recentemente abertos por este app (mais recente primeiro)",
)
async def list_recent_files(
    controller: RecentFilesController = Depends(get_controller),
) -> list[RecentFileEntry]:
    return await controller.list_recent()


@router.post(
    "/thumbnail",
    response_model=ThumbnailUploadResponse,
    summary="Recebe um snapshot real (PNG) do canvas 3D logo apos abrir um modelo, para usar como thumbnail na Pagina Inicial",
)
async def upload_thumbnail(
    body: ThumbnailUploadRequest,
    controller: RecentFilesController = Depends(get_controller),
) -> ThumbnailUploadResponse:
    return await controller.upload_thumbnail(body.path, body.image_base64)
