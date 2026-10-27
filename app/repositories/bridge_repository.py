"""
Repository da Sketchup Bridge.

Papel desta camada (ver skill backend-architecture): e o UNICO lugar
que fala com a "fonte de dados" -- aqui, em vez de SQLAlchemy/banco, a
fonte de dados e o processo do SketchUp via socket TCP
(app/infra/bridge_client.py). Nenhuma camada acima deste repository
deve importar `socket`, `json` ou `SketchUpBridgeClient` diretamente.

Cada metodo abre uma conexao curta, manda um comando, fecha a conexao.
Isso bate com o que validamos manualmente em 27/10/2026 (ver
REVERSE_ENGINEERING_NOTES.md secao 10.7): conexao por chamada, sem
estado persistente entre requests -- mais simples e mais resiliente a
um SketchUp que reinicia ou a uma bridge que foi recarregada.

Traduz erros de baixo nivel (ConnectionError, BridgeError) para
excecoes de dominio (app/domain/exceptions.py), que e o que o service
e o controller sabem interpretar.
"""

from __future__ import annotations

from app.core.config import settings
from app.domain.exceptions import BridgeCommandError, BridgeUnavailableError
from app.infra.bridge_client import BridgeError, SketchUpBridgeClient


class BridgeRepository:
    def __init__(
        self,
        host: str = settings.bridge_host,
        port: int = settings.bridge_port,
    ):
        self._host = host
        self._port = port

    def _run(self, cmd: str, params: dict | None, timeout: float) -> dict:
        try:
            with SketchUpBridgeClient(
                host=self._host, port=self._port, timeout=timeout
            ) as client:
                return client.request(cmd, params)
        except BridgeError as e:
            raise BridgeCommandError(str(e)) from e
        except (ConnectionError, OSError) as e:
            # Mensagem estavel e "limpa" de proposito -- e o `detail` que
            # chega ate o cliente HTTP via 503 (ver ModelController). Nao
            # deixamos a excecao de socket (ConnectionRefusedError,
            # TimeoutError, etc.) vazar pra fora desta camada.
            raise BridgeUnavailableError(
                "SketchUp Bridge is offline or unavailable. Open SketchUp "
                f"with the bridge script loaded ({self._host}:{self._port}) "
                f"and try again. (socket error: {e.__class__.__name__}: {e})"
            ) from e
        except Exception as e:
            # Defesa extra: qualquer coisa inesperada aqui (ex.: resposta
            # que nao e JSON valido) nunca deve vazar como 500 cru -- vira
            # um erro de dominio explicito, que o controller sabe traduzir.
            raise BridgeCommandError(
                f"unexpected error talking to the Sketchup Bridge: "
                f"{e.__class__.__name__}: {e}"
            ) from e

    def ping(self) -> dict:
        return self._run("ping", None, timeout=settings.bridge_timeout_seconds)

    def open_model(self, file_path: str) -> dict:
        # timeout maior: carregar um .skp grande pode levar bem mais
        # que o timeout usado pros outros comandos (ver core/config.py).
        return self._run(
            "open_model",
            {"path": file_path},
            timeout=settings.bridge_open_model_timeout_seconds,
        )

    def model_summary(self) -> dict:
        return self._run(
            "model_summary", None, timeout=settings.bridge_timeout_seconds
        )

    def close_model(self) -> dict:
        return self._run(
            "close_model", None, timeout=settings.bridge_timeout_seconds
        )
