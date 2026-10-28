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


class SceneOverwriteConfirmationRequiredError(SceneSessionError):
    """"Salvar"/"Salvar Como" apontou pra um arquivo que JA EXISTE no
    disco e e DIFERENTE do modelo atualmente aberto na sessao -- exige
    confirmacao explicita do usuario (`overwrite_confirmed=true`) antes
    de sobrescrever. Trava adicionada depois de um incidente real
    (28/10/2026): um modelo de template vazio foi salvo por cima de um
    arquivo de producao real de ~170MB, sem nenhum aviso, perdendo o
    conteudo original (sem recuperacao possivel pelo app -- `SUModelSaveToFile`
    sobrescreve direto, nao passa pela Lixeira do Windows)."""

    def __init__(self, existing_path: str, existing_size_bytes: int):
        self.existing_path = existing_path
        self.existing_size_bytes = existing_size_bytes
        super().__init__(
            f'"{existing_path}" ja existe no disco ({existing_size_bytes} bytes) e e '
            "diferente do modelo aberto nesta sessao -- confirme explicitamente "
            "pra sobrescrever"
        )
