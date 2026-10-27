"""
Cliente Python para a Sketchup Bridge (ruby_bridge/sketchup_bridge.rb).

Fala com o servidor TCP que roda DENTRO do processo do SketchUp (via
Ruby oficial). Protocolo: uma linha de texto = um objeto JSON,
terminada em "\n". Ver o cabecalho de sketchup_bridge.rb para o
protocolo completo, e REVERSE_ENGINEERING_NOTES.md secao 10 para a
decisao de arquitetura.

Camada: infra (app/infra). Usado exclusivamente pelo repository
(app/repositories/bridge_repository.py) -- nenhuma camada acima dele
deve importar socket/json diretamente.

Uso direto (fora do FastAPI, ex. scripts de teste manual):
    from app.infra.bridge_client import SketchUpBridgeClient

    with SketchUpBridgeClient() as bridge:
        print(bridge.ping())
        bridge.open_model("C:/caminho/modelo.skp")
        print(bridge.model_summary())
"""

from __future__ import annotations

import itertools
import json
import socket
from typing import Any


class BridgeError(RuntimeError):
    """Erro reportado pelo lado Ruby (ok: false na resposta)."""


class SketchUpBridgeClient:
    DEFAULT_HOST = "127.0.0.1"
    DEFAULT_PORT = 9876  # deve bater com PORT em sketchup_bridge.rb

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = 5.0,
    ):
        self._host = host
        self._port = port
        self._timeout = timeout
        self._sock: socket.socket | None = None
        self._recv_buffer = b""
        self._id_counter = itertools.count(1)

    # -- ciclo de vida ---------------------------------------------------

    def connect(self) -> None:
        if self._sock is not None:
            return
        sock = socket.create_connection(
            (self._host, self._port), timeout=self._timeout
        )
        sock.settimeout(self._timeout)
        self._sock = sock

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None
                self._recv_buffer = b""

    def __enter__(self) -> "SketchUpBridgeClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # -- protocolo ---------------------------------------------------------

    def request(self, cmd: str, params: dict | None = None) -> Any:
        """Envia um comando e espera a resposta correspondente (por id).

        Lanca BridgeError se o lado Ruby responder ok=false, ou
        ConnectionError/OSError se a conexao cair/der timeout.
        """
        if self._sock is None:
            raise ConnectionError(
                "nao conectado -- chame connect() ou use 'with SketchUpBridgeClient() as c:'"
            )

        req_id = next(self._id_counter)
        payload = {"id": req_id, "cmd": cmd, "params": params or {}}
        line = json.dumps(payload) + "\n"
        self._sock.sendall(line.encode("utf-8"))

        while True:
            response = self._read_one_line_json()
            if response.get("id") == req_id:
                break
            # resposta de outro id (nao deveria acontecer num client
            # simples request/response sequencial, mas nao travamos nisso)

        if not response.get("ok", False):
            raise BridgeError(response.get("error", "erro desconhecido na bridge"))
        return response.get("result")

    def _read_one_line_json(self) -> dict:
        while b"\n" not in self._recv_buffer:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("conexao com a Sketchup Bridge foi fechada")
            self._recv_buffer += chunk

        line, self._recv_buffer = self._recv_buffer.split(b"\n", 1)
        return json.loads(line.decode("utf-8"))

    # -- comandos de conveniencia -------------------------------------------

    def ping(self) -> dict:
        return self.request("ping")

    def open_model(self, file_path: str) -> dict:
        return self.request("open_model", {"path": file_path})

    def model_summary(self) -> dict:
        return self.request("model_summary")

    def close_model(self) -> dict:
        return self.request("close_model")
