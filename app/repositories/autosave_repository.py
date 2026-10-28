"""
Persistencia dos rascunhos de autosave (JSON local + .skp real em
app/data/autosave/) -- mesmo padrao do RecentFilesRepository: sem banco
de verdade de proposito, app desktop de usuario unico.

So cuida do MANIFESTO (id -> {original_path, nome, timestamp}) e do
arquivo .skp do rascunho em si; quem decide QUANDO gravar um rascunho
novo (a cada edicao real) e o SkpEngineRepository, unico lugar que tem
acesso a sessao ctypes aberta (ver skp_engine_repository.py _autosave()).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_AUTOSAVE_DIR = _DATA_DIR / "autosave"
_MANIFEST_JSON = _AUTOSAVE_DIR / "manifest.json"


class AutosaveRepository:
    def __init__(self) -> None:
        _AUTOSAVE_DIR.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def draft_id_for(original_path: str) -> str:
        """Mesmo esquema de id do RecentFilesRepository -- um rascunho
        por arquivo original (sobrescrito a cada autosave, nao acumula
        historico)."""
        return hashlib.md5(original_path.encode("utf-8")).hexdigest()[:16]

    def draft_file_path(self, original_path: str) -> str:
        return str(_AUTOSAVE_DIR / f"{self.draft_id_for(original_path)}.skp")

    def record_autosave(self, original_path: str) -> None:
        """Chamado DEPOIS de gravar o .skp do rascunho em disco de
        verdade (ver skp_engine_repository.py _autosave()) -- so
        atualiza o manifesto."""
        draft_id = self.draft_id_for(original_path)
        entries = self._load()
        entries = [e for e in entries if e["id"] != draft_id]
        entries.insert(
            0,
            {
                "id": draft_id,
                "original_path": original_path,
                "name": os.path.basename(original_path),
                "saved_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        self._save(entries)

    def list_drafts(self) -> list[dict]:
        """So devolve entradas cujo arquivo de rascunho ainda existe de
        verdade no disco -- uma entrada orfa (arquivo apagado por fora)
        nunca e oferecida pra recuperacao."""
        return [e for e in self._load() if (_AUTOSAVE_DIR / f"{e['id']}.skp").exists()]

    def get_entry(self, draft_id: str) -> dict | None:
        return next((e for e in self._load() if e["id"] == draft_id), None)

    def discard(self, original_path: str) -> None:
        self.discard_by_id(self.draft_id_for(original_path))

    def discard_by_id(self, draft_id: str) -> None:
        entries = [e for e in self._load() if e["id"] != draft_id]
        self._save(entries)
        draft_file = _AUTOSAVE_DIR / f"{draft_id}.skp"
        try:
            draft_file.unlink(missing_ok=True)
        except OSError:
            pass  # best-effort -- nunca quebra o fluxo principal por causa disso

    # -- leitura/escrita do JSON ------------------------------------------

    def _load(self) -> list[dict]:
        if not _MANIFEST_JSON.exists():
            return []
        try:
            return json.loads(_MANIFEST_JSON.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self, entries: list[dict]) -> None:
        _MANIFEST_JSON.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
        )
