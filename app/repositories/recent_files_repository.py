"""
Persistencia dos arquivos recentes (JSON local em app/data/) e das
thumbnails (PNG em app/data/thumbnails/). Unico lugar que toca esses
arquivos -- mesmo padrao do SkpEngineRepository ser o unico lugar que
importa ctypes.

Nao ha banco de verdade aqui de proposito: e um app desktop de usuario
unico (mesma decisao ja tomada pra sessao de edicao -- ver
REVERSE_ENGINEERING_NOTES.md secao 18.4), entao um JSON simples resolve
sem trazer dependencia nova.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

MAX_RECENT_FILES = 10

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_RECENT_FILES_JSON = _DATA_DIR / "recent_files.json"
_THUMBNAILS_DIR = _DATA_DIR / "thumbnails"


class RecentFilesRepository:
    def __init__(self) -> None:
        _DATA_DIR.mkdir(parents=True, exist_ok=True)
        _THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def file_id(file_path: str) -> str:
        """Id estavel derivado do path -- evita problemas de URL com
        espacos/backslashes de caminhos Windows nas rotas de thumbnail."""
        return hashlib.md5(file_path.encode("utf-8")).hexdigest()[:16]

    def list_all(self) -> list[dict]:
        return self._load()

    def register_opened(self, file_path: str) -> str:
        """Registra (ou atualiza) um arquivo na lista de recentes,
        movendo-o pro topo. `last_modified` vem de verdade do disco --
        se o arquivo tiver sumido entre a abertura e a listagem, fica
        None em vez de inventar uma data."""
        entry_id = self.file_id(file_path)
        all_entries = self._load()
        existing_thumbnail = next(
            (e.get("thumbnail_url") for e in all_entries if e["id"] == entry_id),
            None,
        )
        entries = [e for e in all_entries if e["id"] != entry_id]

        try:
            last_modified = datetime.fromtimestamp(
                os.path.getmtime(file_path), tz=timezone.utc
            ).isoformat()
        except OSError:
            last_modified = None

        entries.insert(
            0,
            {
                "id": entry_id,
                "path": file_path,
                "name": os.path.basename(file_path),
                "last_opened": datetime.now(timezone.utc).isoformat(),
                "last_modified": last_modified,
                "thumbnail_url": existing_thumbnail,
            },
        )
        self._save(entries[:MAX_RECENT_FILES])
        return entry_id

    def save_thumbnail(self, file_path: str, image_base64: str) -> str:
        """Decodifica o PNG (snapshot real do canvas Three.js, mandado
        pelo frontend) e grava em disco, associando o arquivo na lista
        de recentes caso ele ja esteja la."""
        entry_id = self.file_id(file_path)
        _, _, raw_b64 = image_base64.partition(",")  # tira "data:image/png;base64,"
        png_bytes = base64.b64decode(raw_b64 or image_base64)
        (_THUMBNAILS_DIR / f"{entry_id}.png").write_bytes(png_bytes)

        thumbnail_url = f"/thumbnails/{entry_id}.png"
        entries = self._load()
        for entry in entries:
            if entry["id"] == entry_id:
                entry["thumbnail_url"] = thumbnail_url
        self._save(entries)
        return thumbnail_url

    # -- leitura/escrita do JSON ------------------------------------------

    def _load(self) -> list[dict]:
        if not _RECENT_FILES_JSON.exists():
            return []
        try:
            return json.loads(_RECENT_FILES_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, entries: list[dict]) -> None:
        _RECENT_FILES_JSON.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
        )
