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
from core.mesh_extractor import extract_scene, extract_scene_with_registry, invert_affine4, matmul4
from core.obj_exporter import write_obj
from core.su_api import SketchUpAPI, SketchUpModel


@dataclass
class _Session:
    api: SketchUpAPI
    model: SketchUpModel
    model_path: str | None  # None = modelo novo (via template), ainda sem arquivo no disco
    registry: dict = field(default_factory=dict)  # instance_id -> {"ref", "parent_world"}
    tags: dict = field(default_factory=dict)  # nome da etiqueta -> SULayerRef (cache pra reusar a MESMA etiqueta entre cliques, nao criar uma nova a cada vez)
    faces: dict = field(default_factory=dict)  # face_id -> SUFaceRef (usado por paint_face())

    def close(self) -> None:
        self.model.close()
        self.api.terminate()


_SESSION: _Session | None = None


class SkpEngineRepository:
    def open(self, file_path: str) -> dict:
        dto = self._open_and_extract(
            lambda api: api.open_model(file_path), "falha ao abrir o .skp", file_path
        )
        return dto

    def open_new_from_template(self, template_path: str) -> dict:
        """Abre um template real da Trimble via buffer (SUModelCreateFromBuffer
        WithStatus -- ver core/su_api.py open_model_from_buffer), do mesmo jeito
        que o SketchUp de verdade cria um documento novo: com conteudo do
        template, mas SEM vinculo com o arquivo de template no disco.
        `model_path` fica None na sessao -- o primeiro `save()` exige um
        `path` explicito, nunca sobrescrevendo o .skp original da Trimble."""
        return self._open_and_extract(
            lambda api: api.open_model_from_buffer(template_path),
            "falha ao abrir o template .skp",
            None,
        )

    def _open_and_extract(self, opener, open_error_prefix: str, session_path: str | None) -> dict:
        global _SESSION

        if _SESSION is not None:
            _SESSION.close()
            _SESSION = None

        api = SketchUpAPI()
        api.initialize()
        try:
            model = opener(api)
        except RuntimeError as e:
            api.terminate()
            raise SceneParseError(f"{open_error_prefix}: {e}") from e

        try:
            dto, registry, faces_registry = extract_scene_with_registry(api, model)
        except RuntimeError as e:
            model.close()
            api.terminate()
            raise SceneParseError(f"falha ao processar o .skp: {e}") from e

        _SESSION = _Session(
            api=api, model=model, model_path=session_path, registry=registry, faces=faces_registry
        )
        dto["model_path"] = session_path
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
        if not target_path:
            raise SceneSessionError(
                "este modelo foi criado a partir de um template e ainda nao "
                "tem um arquivo associado -- informe um `path` (equivalente "
                'a "Salvar Como")'
            )
        try:
            session.model.save(target_path)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao salvar o .skp: {e}") from e
        # depois do 1o save de um modelo novo, "Salvar" simples passa a
        # sobrescrever o caminho escolhido aqui -- nunca mais o template.
        session.model_path = target_path
        return target_path

    def delete_instance(self, instance_id: str) -> None:
        """Equivalente nativo do "Editar > Excluir"/Del -- ver
        core/su_api.py erase_instance() e REVERSE_ENGINEERING_NOTES.md
        secao 26."""
        session = self._require_session()
        entry = session.registry.get(instance_id)
        if entry is None or entry["ref"] is None or entry["parent_entities"] is None:
            raise SceneSessionError(
                f"instancia {instance_id!r} nao encontrada na sessao atual "
                "(ou e o pseudo-objeto 'inst_root', que nao e excluivel)"
            )
        try:
            session.api.erase_instance(entry["parent_entities"], entry["ref"])
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao excluir a instancia: {e}") from e
        del session.registry[instance_id]

    def paint_instance(self, instance_id: str, r: int, g: int, b: int) -> None:
        """Equivalente real de "Ferramentas > Pintura": aplica uma cor
        RGBA nova de verdade na instancia (ver core/su_api.py
        paint_instance() e REVERSE_ENGINEERING_NOTES.md secao 28). Ao
        contrario de add_rectangle (geometria nova), isto NAO precisa
        reextrair a cena inteira -- so afeta a aparencia da instancia,
        nao a topologia/malha, entao o frontend aplica a cor direto no
        seu proprio mesh sem round-trip de dados."""
        session = self._require_session()
        entry = session.registry.get(instance_id)
        if entry is None or entry["ref"] is None:
            raise SceneSessionError(
                f"instancia {instance_id!r} nao encontrada na sessao atual "
                "(ou e o pseudo-objeto 'inst_root', que nao e pintavel)"
            )
        try:
            session.api.paint_instance(entry["ref"], r, g, b)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao pintar a instancia: {e}") from e

    def paint_face(self, face_id: str, r: int, g: int, b: int) -> None:
        """Equivalente real de pintar uma FACE especifica (nao a
        instancia inteira) -- ver core/su_api.py paint_face() e
        REVERSE_ENGINEERING_NOTES.md secao 28.19. A face pertence a
        geometria da DEFINICAO, entao a mudanca fica gravada pra TODAS
        as instancias que compartilham essa definicao (mesmo
        comportamento real do SketchUp)."""
        session = self._require_session()
        face = session.faces.get(face_id)
        if face is None:
            raise SceneSessionError(
                f"face {face_id!r} nao encontrada na sessao atual"
            )
        try:
            session.api.paint_face(face, r, g, b)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao pintar a face: {e}") from e

    def add_rectangle(self, width_m: float, height_m: float, as_group: bool = False) -> dict:
        """Equivalente real de "Desenho > Formas > Retângulo": cria uma
        face retangular nova no chao (plano XY, Z=0 -- mesma convencao
        Z-up do .skp, ver core/sceneBuilder.js SKP_TO_THREE_UP),
        centrada na origem. Por padrao vai direto na Entities raiz do
        modelo aberto; com `as_group=True` (equivalente real de "Editar >
        Criar grupo", ver REVERSE_ENGINEERING_NOTES.md secao 28.17) a
        face nasce DENTRO de um Grupo novo real (SUGroupCreate +
        SUEntitiesAddGroup) em vez de solta na raiz -- demonstra criacao
        de geometria agrupada com o mesmo fluxo ja validado de add_face().
        Reextrai e devolve o DTO inteiro -- diferente de excluir/mover
        uma instancia, geometria nova nao tem como ser aplicada
        incrementalmente no frontend, o Three.js precisa da malha "root"
        inteira de novo (a face nova entra ali, ver core/mesh_extractor.py
        _collect_definition pro "root")."""
        session = self._require_session()
        INCHES_PER_METER = 1 / 0.0254
        half_w = (width_m * INCHES_PER_METER) / 2
        half_h = (height_m * INCHES_PER_METER) / 2
        points = [
            (-half_w, -half_h, 0.0),
            (half_w, -half_h, 0.0),
            (half_w, half_h, 0.0),
            (-half_w, half_h, 0.0),
        ]
        try:
            if as_group:
                group = session.api.create_group(session.model.get_entities(), "Grupo")
                target_entities = session.api.get_group_entities(group)
            else:
                target_entities = session.model.get_entities()
            session.api.add_face(target_entities, points)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao criar o retângulo: {e}") from e

        dto, registry, faces_registry = extract_scene_with_registry(session.api, session.model)
        session.registry = registry
        session.faces = faces_registry
        dto["model_path"] = session.model_path
        return dto

    def tag_instance(self, instance_id: str, tag_name: str) -> None:
        """Equivalente real de "Ferramentas > Etiqueta": aplica uma
        Etiqueta (Tag) real na instancia -- a API interna ainda chama
        isso de "Layer" (nome legado da Trimble), ver core/su_api.py
        create_tag()/set_instance_tag() e REVERSE_ENGINEERING_NOTES.md
        secao 28.17. Reusa a MESMA etiqueta (SULayerRef) se o mesmo nome
        ja foi usado nesta sessao (session.tags), em vez de criar uma
        Layer nova a cada clique -- mesmo objeto real do modelo."""
        session = self._require_session()
        entry = session.registry.get(instance_id)
        if entry is None or entry["ref"] is None:
            raise SceneSessionError(
                f"instancia {instance_id!r} nao encontrada na sessao atual "
                "(ou e o pseudo-objeto 'inst_root', que nao e etiquetavel)"
            )
        try:
            layer = session.tags.get(tag_name)
            if layer is None:
                layer = session.api.create_tag(session.model.raw_ref, tag_name)
                session.tags[tag_name] = layer
            session.api.set_instance_tag(entry["ref"], layer)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao aplicar a etiqueta: {e}") from e

    def list_scenes(self) -> list[dict]:
        """Equivalente real de "Janela > Bandeja padrao > Cenas" -- lista
        TODAS as cenas reais do modelo aberto (inclusive as que ja
        vinham salvas no .skp antes desta sessao, nao so as criadas
        agora) via SUModelGetScenes/SUModelGetNumScenes (ver
        core/su_api.py e REVERSE_ENGINEERING_NOTES.md secao 28.20).
        `scene_id` e derivado do ponteiro bruto do Ref, nao persiste
        entre sessoes diferentes (mesmo padrao de face_id)."""
        session = self._require_session()
        scenes = session.api.get_scenes(session.model.raw_ref)
        active = session.api.get_active_scene(session.model.raw_ref)
        active_id = f"scene_{active.ptr or 0:x}" if active is not None else None
        result = []
        for scene in scenes:
            scene_id = f"scene_{scene.ptr or 0:x}"
            result.append(
                {
                    "scene_id": scene_id,
                    "name": session.api.get_scene_name(scene) or scene_id,
                    "active": scene_id == active_id,
                }
            )
        return result

    def create_scene(self, name: str) -> dict:
        """Cria uma Cena real nova a partir do estado atual -- equivalente
        real de "Janela > Bandeja padrao > Cenas > +". NAO captura
        camera/estilo visual (ver core/su_api.py create_scene() --
        limitacao documentada, este projeto nao tem binding de
        SUCameraRef)."""
        session = self._require_session()
        try:
            scene = session.api.create_scene(session.model.raw_ref, name)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao criar a cena: {e}") from e
        return {"scene_id": f"scene_{scene.ptr or 0:x}", "name": name}

    def activate_scene(self, scene_id: str) -> None:
        """Equivalente real de clicar numa aba de Cena -- SUSceneActivate
        (ver core/su_api.py). Nao move a camera do viewer nesta sessao
        (limitacao documentada, mesma de create_scene())."""
        session = self._require_session()
        target = None
        for scene in session.api.get_scenes(session.model.raw_ref):
            if f"scene_{scene.ptr or 0:x}" == scene_id:
                target = scene
                break
        if target is None:
            raise SceneSessionError(f"cena {scene_id!r} nao encontrada na sessao atual")
        try:
            session.api.activate_scene(session.model.raw_ref, target)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao ativar a cena: {e}") from e

    def export_obj(self, file_path: str) -> str:
        """Equivalente parcial do "Arquivo > Exportar > Modelo 3D..." --
        so formato OBJ por enquanto (ver core/obj_exporter.py e
        REVERSE_ENGINEERING_NOTES.md secao 26). Reextrai o DTO na hora
        (reflete qualquer edicao/exclusao ja aplicada na sessao)."""
        session = self._require_session()
        dto = extract_scene(session.api, session.model)
        try:
            write_obj(dto, file_path)
        except OSError as e:
            raise SceneSessionError(f"falha ao escrever o .obj: {e}") from e
        return file_path

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
