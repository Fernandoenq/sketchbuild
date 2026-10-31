"""
Entrypoint do backend FastAPI do sketchbuild.

Rodar (de dentro da pasta sketchbuild, OBRIGATORIO Python 3.12
-- ver REVERSE_ENGINEERING_NOTES.md secao 15/17):
    py -3.12 -m uvicorn app.main:app --reload --port 8000

Visualizador 3D (motor ctypes standalone, nao precisa do SketchUp
aberto):
    http://127.0.0.1:8000/                                (frontend Three.js)
    POST http://127.0.0.1:8000/api/v1/scene/open   {"path": "C:/.../arquivo.skp"}

Arquitetura alternativa (Ruby bridge, precisa do SketchUp aberto --
ver README.md):
    GET  http://127.0.0.1:8000/health
    GET  http://127.0.0.1:8000/docs       (Swagger UI automatico)
    GET  http://127.0.0.1:8000/api/v1/models/bridge/ping
    POST http://127.0.0.1:8000/api/v1/models/open        {"path": "C:/.../arquivo.skp"}
    GET  http://127.0.0.1:8000/api/v1/models/current
    POST http://127.0.0.1:8000/api/v1/models/current/close
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.routes import health_router, model_router, recent_files_router, scene_router

app = FastAPI(title=settings.api_title)

register_exception_handlers(app)

app.include_router(health_router.router)
app.include_router(model_router.router, prefix=settings.api_prefix)
app.include_router(scene_router.router, prefix=settings.api_prefix)
app.include_router(recent_files_router.router, prefix=settings.api_prefix)

@app.post("/api/v1/debug-log")
async def client_debug_log(request: Request):
    try:
        data = await request.json()
        print(f"[BROWSER LOG] {data}", flush=True)
    except Exception as e:
        print(f"[BROWSER LOG ERROR] {e}", flush=True)
    return {"status": "ok"}

# Thumbnails reais (PNG) dos arquivos recentes -- ver
# app/repositories/recent_files_repository.py. Pasta criada sob demanda
# pelo repository; garantimos que existe aqui tambem pro StaticFiles
# nao reclamar num start limpo (sem nenhum arquivo aberto ainda).
_THUMBNAILS_DIR = Path(__file__).resolve().parent / "data" / "thumbnails"
_THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/thumbnails", StaticFiles(directory=_THUMBNAILS_DIR), name="thumbnails")

# Frontend Three.js estatico. Montado por ULTIMO: qualquer rota de API
# acima e casada primeiro; isso so serve o que mais ninguem pegou
# (inclusive "/" -- html=True serve frontend/index.html nesse caso).
_FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=_FRONTEND_DIR, html=True), name="frontend")
