"""
Controller da Pagina Inicial / arquivos recentes. So orquestra o
service -- sem regra de negocio aqui (mesmo padrao do SceneController).
"""

from __future__ import annotations

from app.schemas.recent_files import RecentFileEntry, ThumbnailUploadResponse
from app.services.recent_files_service import RecentFilesService


class RecentFilesController:
    def __init__(self, service: RecentFilesService | None = None):
        self._service = service or RecentFilesService()

    async def list_recent(self) -> list[RecentFileEntry]:
        entries = await self._service.list_recent()
        return [RecentFileEntry.model_validate(e) for e in entries]

    async def upload_thumbnail(
        self, file_path: str, image_base64: str
    ) -> ThumbnailUploadResponse:
        url = await self._service.save_thumbnail(file_path, image_base64)
        return ThumbnailUploadResponse(thumbnail_url=url)
