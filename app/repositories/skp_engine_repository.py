"""
Repository do motor ctypes (Core).

Papel desta camada (ver skill backend-architecture): e o UNICO lugar
que fala com a "fonte de dados" -- aqui, a fonte de dados e a
SketchUpAPI.dll via ctypes (core/su_api.py, core/mesh_extractor.py).
Nenhuma camada acima deste repository deve importar `ctypes` ou
`core.*` diretamente.

Diferente do BridgeRepository (conexao nova a cada chamada, sem
estado), a edicao exige que o modelo fique ABERTO entre requests:
abrir -> mover um gizmo no frontend -> aplicar a transformacao -> salvar,
tudo na mesma sessao. Por isso existe `_SESSION`, um singleton em nivel
de modulo (nao por instancia de SkpEngineRepository -- o controller cria
uma instancia nova por request, ver app/controllers/scene_controller.py).
Aceitavel aqui porque o produto e uma ferramenta desktop de usuario
unico, sem concorrencia real entre sessoes.

REQUER Python 3.12 no processo que roda este backend -- ver
REVERSE_ENGINEERING_NOTES.md secao 15 (regressao do ctypes no Python
3.14).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.exceptions import SceneParseError, SceneSessionError
from core.mesh_extractor import extract_scene_with_registry, invert_affine4, matmul4
from core.su_api import SketchUpAPI, SketchUpModel


@dataclass
class _Session:
    api: SketchUpAPI
    model: SketchUpModel
    model_path: str
    registry: dict = field(default_factory=dict)  # instance_id -> {"ref", "parent_world"}

    def close(self) -> None:
        self.model.close()
        self.api.terminate()


_SESSION: _Session | None = None


class SkpEngineRepository:
    def open(self, file_path: str) -> dict:
        global _SESSION

        if _SESSION is not None:
            _SESSION.close()
            _SESSION = None

        api = SketchUpAPI()
        api.initialize()
        try:
            model = api.open_model(file_path)
        except RuntimeError as e:
            api.terminate()
            raise SceneParseError(f"falha ao abrir o .skp: {e}") from e

        try:
            dto, registry = extract_scene_with_registry(api, model)
        except RuntimeError as e:
            model.close()
            api.terminate()
            raise SceneParseError(f"falha ao processar o .skp: {e}") from e

        _SESSION = _Session(api=api, model=model, model_path=file_path, registry=registry)
        dto["model_path"] = file_path
        return dto

    def set_instance_transform(self, instance_id: str, new_world_transform: list[float]) -> None:
        session = self._require_session()
        entry = session.registry.get(instance_id)
        if entry is None or entry["ref"] is None:
            raise SceneSessionError(
                f"instancia {instance_id!r} nao encontrada na sessao atual "
                "(ou e o pseudo-objeto 'inst_root', que nao e editavel)"
            )

        # SUComponentInstanceSetTransform espera a transformacao LOCAL
        # (relativa ao pai imediato), nao a mundial usada no DTO -- ver
        # nota no topo de core/mesh_extractor.py.
        parent_world = entry["parent_world"]
        local = matmul4(invert_affine4(parent_world), new_world_transform)

        try:
            session.api.set_instance_transform(entry["ref"], local)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao aplicar a transformacao: {e}") from e

        # a propria matriz mundial que acabamos de aplicar vira o novo
        # parent_world de qualquer instancia aninhada dentro dela --
        # nesta fase (edicao so de instancias de topo) isso nao e
        # recalculado em cascata; ver pendencia na secao 18 das notas.

    def save(self, path: str | None) -> str:
        session = self._require_session()
        target_path = path or session.model_path
        try:
            session.model.save(target_path)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao salvar o .skp: {e}") from e
        return target_path

    def close(self) -> None:
        global _SESSION
        if _SESSION is not None:
            _SESSION.close()
            _SESSION = None

    def _require_session(self) -> _Session:
        if _SESSION is None:
            raise SceneSessionError(
                "nenhum modelo aberto nesta sessao -- chame POST /api/v1/scene/open primeiro"
            )
        return _SESSION
