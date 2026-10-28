from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RecentFileEntry(BaseModel):
    """Uma entrada na lista "Arquivos recentes" da Pagina Inicial --
    dado real: path/name/last_modified vem do disco, last_opened e o
    momento em que o usuario abriu pelo app, thumbnail_url (quando
    presente) e um snapshot real do canvas Three.js tirado logo apos a
    abertura (nao e um placeholder)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    path: str
    name: str
    last_opened: str
    last_modified: str | None = None
    thumbnail_url: str | None = None


class ThumbnailUploadRequest(BaseModel):
    """Entrada de POST /recent-files/thumbnail -- o frontend manda o
    path do arquivo que acabou de ser aberto + um PNG (data URL ou
    base64 puro) tirado do canvas Three.js logo apos o enquadramento
    isometrico inicial (ver setStandardView("iso") em main.js)."""

    path: str = Field(..., min_length=1)
    image_base64: str = Field(..., min_length=1)


class ThumbnailUploadResponse(BaseModel):
    thumbnail_url: str
