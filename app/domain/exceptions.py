"""
Excecoes de dominio do sketchbuild. Nao dependem de FastAPI nem
de socket/JSON -- so o controller sabe traduzir isso pra HTTP, e so o
repository sabe traduzir erro de socket/bridge pra isso.
"""

from __future__ import annotations


class SketchBuildError(Exception):
    """Raiz de todas as excecoes de dominio deste app."""


class BridgeUnavailableError(SketchBuildError):
    """Nao foi possivel conectar na Sketchup Bridge.

    Causa tipica: SketchUp fechado, ou aberto mas sem o script
    `ruby_bridge/sketchup_bridge.rb` carregado no Ruby Console.
    """


class BridgeCommandError(SketchBuildError):
    """A bridge respondeu com ok: false (erro do lado Ruby/SketchUp)."""


class InvalidModelPathError(SketchBuildError):
    """Caminho de modelo invalido (nao e .skp, string vazia, etc.)."""


class ModelFileNotFoundError(SketchBuildError):
    """Caminho aponta pra um arquivo que nao existe no disco."""


class SceneParseError(SketchBuildError):
    """Falha dentro do motor ctypes (core/) ao abrir/processar um .skp.

    Causa tipica: SU_RESULT de erro vindo de su_check (core/su_types.py)
    -- ex.: arquivo corrompido, formato nao suportado nesta versao da
    SketchUpAPI.dll. Nao confundir com BridgeCommandError -- esse e do
    caminho antigo (Ruby bridge); este e do parser ctypes standalone
    (ver REVERSE_ENGINEERING_NOTES.md secao 15-17).
    """


class SceneSessionError(SketchBuildError):
    """Erro de sessao de edicao: nenhum modelo aberto, instancia
    inexistente, ou falha ao aplicar transformacao/salvar (ver
    app/repositories/skp_engine_repository.py -- secao 18 das notas)."""
