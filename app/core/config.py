"""
Configuracao central do sidecar. Le variaveis de ambiente com defaults
seguros (os mesmos defaults ja validados manualmente contra a Sketchup
Bridge -- ver REVERSE_ENGINEERING_NOTES.md secao 10).

Nao usa `pydantic-settings` de proposito (nao esta instalado no
ambiente e nao vale a pena adicionar so por isso) -- `BaseModel` com
defaults lidos de `os.getenv` resolve o mesmo problema sem dependencia
nova.
"""

from __future__ import annotations

import os

from pydantic import BaseModel


class Settings(BaseModel):
    # Bridge Ruby/TCP (ver app/infra/bridge_client.py e
    # ruby_bridge/sketchup_bridge.rb -- PORT precisa ser o mesmo valor
    # dos dois lados).
    bridge_host: str = os.getenv("SKETCHUP_BRIDGE_HOST", "127.0.0.1")
    bridge_port: int = int(os.getenv("SKETCHUP_BRIDGE_PORT", "9876"))
    bridge_timeout_seconds: float = float(
        os.getenv("SKETCHUP_BRIDGE_TIMEOUT_SECONDS", "10")
    )
    # Timeout maior para abertura de modelo: arquivos grandes (ex.: o
    # .skp de 178 MB testado em 27/10/2026) levam bem mais que o
    # timeout padrao de leitura/escrita.
    bridge_open_model_timeout_seconds: float = float(
        os.getenv("SKETCHUP_BRIDGE_OPEN_MODEL_TIMEOUT_SECONDS", "120")
    )

    api_prefix: str = "/api/v1"
    api_title: str = "SketchBuild API"


settings = Settings()
