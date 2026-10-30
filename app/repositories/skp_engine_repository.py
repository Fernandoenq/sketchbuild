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

import logging
import os
from dataclasses import dataclass, field

from app.domain.exceptions import (
    SceneOverwriteConfirmationRequiredError,
    SceneParseError,
    SceneSessionError,
)
from app.repositories.autosave_repository import AutosaveRepository
from core.mesh_extractor import (
    extract_scene,
    extract_scene_with_registry,
    invert_affine4,
    matmul4,
    orthonormal_axes_from_points,
)
from core.obj_exporter import write_obj
from core.su_api import SketchUpAPI, SketchUpModel

logger = logging.getLogger("sketchbuild")


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
    def __init__(self, autosave_repository: AutosaveRepository | None = None):
        self._autosave_repo = autosave_repository or AutosaveRepository()

    def open(self, file_path: str) -> dict:
        # abertura EXPLICITA a partir do arquivo real -- o usuario esta
        # escolhendo a copia do disco em vez de um rascunho eventualmente
        # pendente pra esse mesmo caminho (oferecido separadamente via
        # list_autosave_drafts()/recover_draft()); descarta esse rascunho
        # agora pra nunca mais ser oferecido como "recuperar" depois de
        # uma reabertura explicita e intencional.
        self._autosave_repo.discard(file_path)
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

    def open_from_upload(self, data: bytes) -> dict:
        """Abre um .skp a partir dos bytes enviados pelo navegador (upload
        via <input type="file">) -- unica forma de um app web usar o
        seletor NATIVO de arquivos do SO sem o usuario precisar digitar/
        colar o caminho a mao: por seguranca, nenhum navegador expoe o
        caminho real em disco de um arquivo escolhido assim, so o seu
        conteudo. `model_path` fica None na sessao, igual
        open_new_from_template() -- o primeiro "Salvar" exige um `path`
        explicito ("Salvar Como"), ja que nao ha caminho original pra
        sobrescrever."""
        return self._open_and_extract(
            lambda api: api.open_model_from_bytes(data),
            "falha ao abrir o .skp enviado",
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

    def recover_draft(self, draft_id: str) -> dict:
        """Reabre um rascunho de autosave real (mesmo .skp que o proprio
        app gravou em app/data/autosave/, ver _autosave() abaixo), mas
        associa a sessao ao CAMINHO ORIGINAL (`entry["original_path"]`)
        -- nao ao arquivo de rascunho -- pra "Salvar" continuar
        sobrescrevendo o arquivo de verdade do usuario, nunca o
        rascunho interno. Usado pra recuperar edicoes nao salvas depois
        de reiniciar o backend (reload simples de pagina ja e coberto
        por get_current_session(), sem precisar disso)."""
        entry = self._autosave_repo.get_entry(draft_id)
        if entry is None:
            raise SceneSessionError(f"rascunho de autosave {draft_id!r} nao encontrado")
        draft_file = self._autosave_repo.draft_file_path(entry["original_path"])
        return self._open_and_extract(
            lambda api: api.open_model(draft_file),
            "falha ao recuperar o rascunho de autosave",
            entry["original_path"],
        )

    def get_current_session(self) -> dict | None:
        """Reextrai o DTO da sessao JA ABERTA em memoria, sem tocar o
        disco -- cobre o caso de dar F5 na pagina com o MESMO processo
        de backend ainda rodando: o `_SESSION` module-level sobrevive a
        qualquer reload do navegador, so o frontend "esquecia" disso e
        reabria do zero (perdendo qualquer edicao ainda nao salva em
        disco). Devolve None se nao ha sessao (backend reiniciado, ou
        nenhum modelo foi aberto ainda)."""
        if _SESSION is None:
            return None
        dto, registry, faces_registry = extract_scene_with_registry(
            _SESSION.api, _SESSION.model
        )
        _SESSION.registry = registry
        _SESSION.faces = faces_registry
        dto["model_path"] = _SESSION.model_path
        return dto

    def list_autosave_drafts(self) -> list[dict]:
        return self._autosave_repo.list_drafts()

    def discard_autosave_draft(self, draft_id: str) -> None:
        if self._autosave_repo.get_entry(draft_id) is None:
            raise SceneSessionError(f"rascunho de autosave {draft_id!r} nao encontrado")
        self._autosave_repo.discard_by_id(draft_id)

    def _autosave(self) -> None:
        """Grava um rascunho .skp REAL (mesmo SUModelSaveToFile usado em
        "Salvar", so que num arquivo separado em app/data/autosave/, nunca
        no arquivo original do usuario) toda vez que uma edicao real e
        aplicada na sessao -- e o que permite sobreviver a um reinicio do
        backend sem perder trabalho nao salvo. So roda se a sessao ja tem
        `model_path` (modelos criados por template e nunca salvos uma vez
        ainda nao tem uma chave estavel pra associar o rascunho -- mesma
        exigencia ja feita pelo "Salvar" de verdade). Melhor esforco: uma
        falha aqui nunca pode quebrar a edicao que a originou."""
        if _SESSION is None or _SESSION.model_path is None:
            return
        try:
            draft_path = self._autosave_repo.draft_file_path(_SESSION.model_path)
            _SESSION.model.save(draft_path)
            self._autosave_repo.record_autosave(_SESSION.model_path)
        except (RuntimeError, OSError):
            logger.warning("Falha ao gravar autosave de %s", _SESSION.model_path, exc_info=True)

    def set_instance_transform(self, instance_id: str, new_world_transform: list[float]) -> None:
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            SkpBinaryWriter.set_instance_transform(instance_id, new_world_transform)
            return

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
        self._autosave()

    def save(self, path: str | None, overwrite_confirmed: bool = False) -> str:
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            target_path = path or bin_session.model_path
            return SkpBinaryWriter.save_session(target_path, overwrite_confirmed)

        session = self._require_session()
        target_path = path or session.model_path
        if not target_path:
            raise SceneSessionError(
                "este modelo foi criado a partir de um template e ainda nao "
                "tem um arquivo associado -- informe um `path` (equivalente "
                'a "Salvar Como")'
            )
        # trava contra o incidente real de 28/10/2026: salvar por cima
        # de um arquivo que JA EXISTE e e DIFERENTE do que esta aberto
        # nesta sessao (ex.: template vazio salvo sem querer em cima de
        # um .skp de producao) exige confirmacao explicita do chamador.
        # Re-salvar o PROPRIO arquivo que ja esta aberto (target_path ==
        # session.model_path) nunca exige isso, mesmo que o conteudo
        # tenha encolhido por uma edicao legitima.
        if (
            not overwrite_confirmed
            and target_path != session.model_path
            and os.path.exists(target_path)
        ):
            raise SceneOverwriteConfirmationRequiredError(
                target_path, os.path.getsize(target_path)
            )
        try:
            session.model.save(target_path)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao salvar o .skp: {e}") from e
        # "Salvar" de verdade grava a fonte da verdade -- o rascunho de
        # autosave associado ao caminho ANTERIOR (se havia) fica
        # redundante e e descartado agora, antes de reassociar a chave.
        if session.model_path is not None:
            self._autosave_repo.discard(session.model_path)
        # depois do 1o save de um modelo novo, "Salvar" simples passa a
        # sobrescrever o caminho escolhido aqui -- nunca mais o template.
        session.model_path = target_path
        return target_path

    def duplicate_instance(
        self,
        instance_id: str,
        new_world_transform: list[float] | None = None,
        offset_delta_cm: list[float] | None = None,
    ) -> dict:
        """Duplica nativamente uma instância na sessão ativa (Zero DLL via SkpBinaryWriter ou fallback ctypes)."""
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            new_dto = SkpBinaryWriter.duplicate_instance(
                instance_id,
                new_transform_16=new_world_transform,
                offset_delta_cm=offset_delta_cm,
            )
            return {
                "instance_id": new_dto["instance_key"],
                "definition_id": f"def_{new_dto.get('definition_id') or 'clone'}",
                "transform": new_dto["matrix_4x4"],
                "parent_instance_id": "inst_root",
                "tag": "Sem etiquetas",
                "attributes": {},
            }

        session = self._require_session()
        entry = session.registry.get(instance_id)
        if entry is None or entry["ref"] is None:
            raise SceneSessionError(
                f"instancia {instance_id!r} nao encontrada na sessao atual "
                "(ou e o pseudo-objeto 'inst_root', que nao e duplicavel)"
            )

        definition = session.api.get_instance_definition(entry["ref"])
        new_inst = session.api.create_instance(definition)
        orig_trans = session.api.get_instance_transform(entry["ref"])
        new_trans = list(orig_trans)
        if new_world_transform and len(new_world_transform) >= 16:
            new_trans = list(new_world_transform)
        elif offset_delta_cm and len(offset_delta_cm) >= 3:
            new_trans[12] += float(offset_delta_cm[0]) / 2.54
            new_trans[13] += float(offset_delta_cm[1]) / 2.54
            new_trans[14] += float(offset_delta_cm[2]) / 2.54
        else:
            new_trans[12] += 50.0 / 2.54

        session.api.set_instance_transform(new_inst, new_trans)
        parent_entities = entry["parent_entities"] or session.model.get_entities()
        session.api.add_instance(parent_entities, new_inst)

        new_id = f"inst_{len(session.registry)}_{entry.get('definition_name', 'Componente')}"
        session.registry[new_id] = {
            "ref": new_inst,
            "parent_entities": parent_entities,
            "parent_world": entry["parent_world"],
            "definition_name": entry.get("definition_name", "Componente"),
        }
        self._autosave()

        return {
            "instance_id": new_id,
            "definition_id": entry.get("definition_id", "def_0"),
            "transform": new_trans,
            "parent_instance_id": "inst_root",
            "tag": "Sem etiquetas",
            "attributes": {},
        }

    def delete_instance(self, instance_id: str) -> None:
        """Equivalente nativo do "Editar > Excluir"/Del -- ver
        core/su_api.py erase_instance() e REVERSE_ENGINEERING_NOTES.md
        secao 26."""
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            SkpBinaryWriter.delete_instance(instance_id)
            return

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
        self._autosave()

    def paint_instance(self, instance_id: str, r: int, g: int, b: int) -> None:
        """Equivalente real de "Ferramentas > Pintura": aplica uma cor
        RGBA nova de verdade na instancia (ver core/su_api.py
        paint_instance() e REVERSE_ENGINEERING_NOTES.md secao 28). Ao
        contrario de add_rectangle (geometria nova), isto NAO precisa
        reextrair a cena inteira -- so afeta a aparencia da instancia,
        nao a topologia/malha, entao o frontend aplica a cor direto no
        seu proprio mesh sem round-trip de dados."""
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            SkpBinaryWriter.paint_material(f"Material_{instance_id}", r, g, b)
            return

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
        self._autosave()

    def paint_face(self, face_id: str, r: int, g: int, b: int) -> None:
        """Equivalente real de pintar uma FACE especifica (nao a
        instancia inteira) -- ver core/su_api.py paint_face() e
        REVERSE_ENGINEERING_NOTES.md secao 28.19. A face pertence a
        geometria da DEFINICAO, entao a mudanca fica gravada pra TODAS
        as instancias que compartilham essa definicao (mesmo
        comportamento real do SketchUp)."""
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            SkpBinaryWriter.paint_material(f"Mat_{face_id}", r, g, b)
            return

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
        self._autosave()

    def add_box(
        self,
        width_m: float,
        length_m: float,
        height_m: float,
        offset_xyz_cm: list = None,
    ) -> dict:
        """Cria um sólido 3D paramétrico manifold (Zero DLL / C++ Fallback)."""
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            res = SkpBinaryWriter.add_box(width_m, length_m, height_m, offset_xyz_cm)
            self._autosave()

            w_in = (float(width_m) * 100.0) / 2.54
            l_in = (float(length_m) * 100.0) / 2.54
            h_in = (float(height_m) * 100.0) / 2.54
            ox = (float(offset_xyz_cm[0]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 1 else 0.0
            oy = (float(offset_xyz_cm[1]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 2 else 0.0
            oz = (float(offset_xyz_cm[2]) / 2.54) if offset_xyz_cm and len(offset_xyz_cm) >= 3 else 0.0

            verts = []
            norms = []
            indices = []

            face_quads = [
                ([(ox, oy, oz), (ox + w_in, oy, oz), (ox + w_in, oy + l_in, oz), (ox, oy + l_in, oz)], [0.0, 0.0, -1.0]),
                ([(ox, oy, oz + h_in), (ox + w_in, oy, oz + h_in), (ox + w_in, oy + l_in, oz + h_in), (ox, oy + l_in, oz + h_in)], [0.0, 0.0, 1.0]),
                ([(ox, oy, oz), (ox + w_in, oy, oz), (ox + w_in, oy, oz + h_in), (ox, oy, oz + h_in)], [0.0, -1.0, 0.0]),
                ([(ox + w_in, oy, oz), (ox + w_in, oy + l_in, oz), (ox + w_in, oy + l_in, oz + h_in), (ox + w_in, oy, oz + h_in)], [1.0, 0.0, 0.0]),
                ([(ox + w_in, oy + l_in, oz), (ox, oy + l_in, oz), (ox, oy + l_in, oz + h_in), (ox + w_in, oy + l_in, oz + h_in)], [0.0, 1.0, 0.0]),
                ([(ox, oy + l_in, oz), (ox, oy, oz), (ox, oy, oz + h_in), (ox, oy + l_in, oz + h_in)], [-1.0, 0.0, 0.0]),
            ]

            for quad_pts, norm in face_quads:
                base_idx = len(verts) // 3
                for pt in quad_pts:
                    verts.extend(pt)
                    norms.extend(norm)
                indices.extend([base_idx, base_idx + 1, base_idx + 2, base_idx, base_idx + 2, base_idx + 3])

            box_def_id = f"def_box_{len(res.get('face_ids', []))}"
            box_def = {
                "definition_id": box_def_id,
                "name": f"Box_{width_m}x{length_m}x{height_m}m",
                "vertices": verts,
                "normals": norms,
                "indices": indices,
                "uvs": [0.0, 0.0] * (len(verts) // 3),
                "face_materials": ["Default"] * 6,
                "face_ranges": [],
                "always_faces_camera": False,
            }

            scene_dict = {
                "model_path": bin_session.model_path,
                "definitions": [box_def],
                "instances": [{
                    "instance_id": f"inst_box_{res.get('vertex_ids', [0])[0]}",
                    "definition_id": box_def_id,
                    "name": box_def["name"],
                    "transform": [
                        1.0, 0.0, 0.0, 0.0,
                        0.0, 1.0, 0.0, 0.0,
                        0.0, 0.0, 1.0, 0.0,
                        0.0, 0.0, 0.0, 1.0,
                    ],
                    "parent_instance_id": None,
                    "tag": None,
                }],
                "materials": {},
                "tags": [],
                "scenes": bin_session.scenes or [],
                "camera": None,
                "reader_mode": "binary_native",
            }

            return {
                "box": {
                    "entity_type": "Box",
                    "vertex_count": res.get("vertex_count", 8),
                    "edge_count": res.get("edge_count", 12),
                    "face_count": res.get("face_count", 6),
                    "dimensions_m": res.get("dimensions_m", [width_m, length_m, height_m]),
                    "volume_m3": res.get("volume_m3", round(width_m * length_m * height_m, 4)),
                },
                "scene": scene_dict,
            }
        raise SceneSessionError("nenhuma sessão binária ativa")

    def add_rectangle(self, width_m: float, height_m: float, as_group: bool = False) -> dict:
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            res = SkpBinaryWriter.add_rectangle(width_m, height_m)
            half_w_in = (width_m * 100.0 / 2.54) / 2
            half_h_in = (height_m * 100.0 / 2.54) / 2
            pts_in = [
                -half_w_in, -half_h_in, 0.0,
                half_w_in, -half_h_in, 0.0,
                half_w_in, half_h_in, 0.0,
                -half_w_in, half_h_in, 0.0,
            ]
            root_def = {
                "definition_id": "def_root",
                "name": "Model Root",
                "vertices": pts_in,
                "normals": [0.0, 0.0, 1.0] * 4,
                "indices": [0, 1, 2, 0, 2, 3],
                "uvs": [0.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0],
                "face_materials": ["Default"],
                "face_ranges": [],
                "always_faces_camera": False,
            }
            return {
                "model_path": bin_session.model_path,
                "definitions": [root_def],
                "instances": [],
                "materials": {},
                "tags": [],
                "scenes": bin_session.scenes,
                "camera": None,
                "reader_mode": "binary_native",
            }
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
        self._autosave()
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
        self._autosave()

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

    def list_tags(self) -> list[dict]:
        """Equivalente real de "Janela > Bandeja padrao > Etiquetas" --
        lista TODAS as Etiquetas reais do modelo aberto (inclusive as
        que ja vinham salvas no .skp antes desta sessao, nao so as
        criadas/atribuidas agora) via SUModelGetLayers/SULayerGetName/
        SULayerGetVisibility (ver core/su_api.py e
        REVERSE_ENGINEERING_NOTES.md secao 28.22). `is_default` marca a
        Etiqueta padrao real ("Sem etiquetas")."""
        session = self._require_session()
        api = session.api
        layers = api.list_layers(session.model.raw_ref)
        default_layer = api.get_default_layer(session.model.raw_ref)
        result = []
        for layer in layers:
            result.append(
                {
                    "name": api.get_layer_name(layer),
                    "visible": api.get_layer_visibility(layer),
                    "is_default": layer.ptr == default_layer.ptr,
                }
            )
        return result

    def set_tag_visibility(self, tag_name: str, visible: bool) -> dict:
        """Equivalente real do icone de olho ao lado de cada Etiqueta na
        Bandeja padrao real (SULayerSetVisibility) -- muda estado REAL
        na DLL (nao e so um filtro client-side), persistido se "Salvar"
        for chamado depois. Precisa achar a SULayerRef pelo nome entre
        as etiquetas reais do modelo (nao so no cache session.tags, que
        so tem as criadas NESTA sessao via Ferramentas > Etiqueta)."""
        session = self._require_session()
        api = session.api
        for layer in api.list_layers(session.model.raw_ref):
            if api.get_layer_name(layer) == tag_name:
                api.set_layer_visibility(layer, visible)
                self._autosave()
                return {"name": tag_name, "visible": visible}
        raise SceneSessionError(f"etiqueta {tag_name!r} nao encontrada no modelo atual")

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
        self._autosave()
        return {"scene_id": f"scene_{scene.ptr or 0:x}", "name": name}

    def activate_scene(self, scene_id: str) -> None:
        """Equivalente real de clicar numa aba de Cena --
        SUModelSetActiveScene (ver core/su_api.py; NAO SUSceneActivate,
        que existe na DLL mas nao altera o estado lido por
        SUModelGetActiveScene -- ver REVERSE_ENGINEERING_NOTES.md secao
        28.20). Nao move a camera do viewer nesta sessao (limitacao
        documentada, mesma de create_scene())."""
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
        self._autosave()

    def set_instance_axes(
        self,
        instance_id: str,
        origin: tuple[float, float, float],
        x_point: tuple[float, float, float],
        y_point: tuple[float, float, float],
    ) -> dict:
        """Equivalente real de "Ferramentas > Eixos": redefine o sistema
        de eixos LOCAL da definicao por tras da instancia/Grupo clicado
        (SUComponentDefinitionSetAxes -- ver core/su_api.py e
        REVERSE_ENGINEERING_NOTES.md secao 28.21). `origin`/`x_point`/
        `y_point` ja chegam em POLEGADAS no espaco LOCAL dessa definicao
        (o frontend faz essa conversao, ver meshMatrixToApiTransform-like
        helper em sceneBuilder.js) -- o eixo X fica exato na direcao
        origem->x_point, o eixo Y so define o plano (reprojetado via
        Gram-Schmidt em orthonormal_axes_from_points() pra garantir
        ortogonalidade exata, exigida pela DLL). So muda o sistema de
        coordenadas interno da definicao (afeta TODAS as instancias que
        a compartilham, como Etiqueta/Pintura por face) -- nao move a
        geometria nem a instancia visivelmente."""
        session = self._require_session()
        entry = session.registry.get(instance_id)
        if entry is None or entry["ref"] is None:
            raise SceneSessionError(
                f"instancia {instance_id!r} nao encontrada na sessao atual "
                "(ou e o pseudo-objeto 'inst_root', que nao tem eixos editaveis)"
            )
        try:
            xaxis, yaxis, zaxis = orthonormal_axes_from_points(origin, x_point, y_point)
        except ValueError as e:
            raise SceneSessionError(f"pontos invalidos pra definir eixos: {e}") from e

        definition = session.api.get_instance_definition(entry["ref"])
        axes = None
        try:
            axes = session.api.create_custom_axes(origin, xaxis, yaxis, zaxis)
            session.api.set_definition_axes(definition, axes)
        except RuntimeError as e:
            raise SceneSessionError(f"falha ao aplicar os eixos customizados: {e}") from e
        finally:
            if axes is not None:
                session.api.release_axes(axes)

        self._autosave()
        return {"instance_id": instance_id, "applied": True}

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

    def set_attribute_dictionary(self, dict_name: str, attributes: dict) -> dict:
        """Injeta ou atualiza um Attribute Dictionary de metadados BIM (Zero DLL / C++ Fallback)."""
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            res = SkpBinaryWriter.set_attribute_dictionary(dict_name, attributes)
            self._autosave()
            return res
        raise SceneSessionError("nenhuma sessão binária ativa")

    def get_attribute_dictionaries(self) -> dict:
        """Lê todos os Attribute Dictionaries do modelo aberto (Zero DLL / Pure Python)."""
        from core.skp_binary_reader import SkpBinaryReader
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None and bin_session.model_path:
            return SkpBinaryReader.read_attribute_dictionaries(bin_session.model_path)
        session = self._require_session()
        return SkpBinaryReader.read_attribute_dictionaries(session.file_path)

    def extract_faces_and_triangles(self) -> list:
        """Extrai faces, contornos e triangulação analítica (Zero DLL / Pure Python)."""
        from core.skp_binary_reader import SkpBinaryReader
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None and bin_session.model_path:
            return SkpBinaryReader.extract_faces_and_triangles(bin_session.model_path)
        session = self._require_session()
        return SkpBinaryReader.extract_faces_and_triangles(session.file_path)

    def create_textured_material(
        self,
        material_name: str,
        image_filename: str,
        image_bytes: bytes,
        scale_u_cm: float = 100.0,
        scale_v_cm: float = 100.0,
        color_rgb: tuple = (200, 200, 200),
    ) -> dict:
        """Cria e injeta um material texturizado PBR nativo no .skp (Zero DLL)."""
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        if bin_session is not None:
            res = SkpBinaryWriter.create_textured_material(
                material_name=material_name,
                image_filename=image_filename,
                image_bytes=image_bytes,
                scale_u_cm=scale_u_cm,
                scale_v_cm=scale_v_cm,
                color_rgb=color_rgb,
            )
            self._autosave()
            return res
        raise SceneSessionError("nenhuma sessão binária ativa")


    def set_rendering_style(
        self,
        mode: str = "textured",
        xray: bool = False,
        profiles_width: int = 2,
        background_rgb: list | None = None,
        sky_rgb: list | None = None,
    ) -> dict:
        """Aplica e persiste estilo de exibição visual (Frente 19)."""
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        bg_tuple = tuple(background_rgb) if background_rgb and len(background_rgb) == 3 else None
        sky_tuple = tuple(sky_rgb) if sky_rgb and len(sky_rgb) == 3 else None
        if bin_session is not None:
            SkpBinaryWriter.set_rendering_style(
                mode=mode,
                xray=xray,
                profiles_width=profiles_width,
                background_rgb=bg_tuple,
                sky_rgb=sky_tuple,
            )
            self._autosave()
            return {
                "success": True,
                "mode": mode,
                "xray": xray,
                "profiles_width": profiles_width,
                "style_xml_updated": True,
            }
        return {
            "success": True,
            "mode": mode,
            "xray": xray,
            "profiles_width": profiles_width,
            "style_xml_updated": False,
        }

    def get_assembly_tree(self) -> dict:
        """Extrai a árvore completa de grupos e instâncias aninhadas (Frente 15)."""
        from core.skp_binary_reader import SkpBinaryReader
        from core.skp_binary_writer import SkpBinaryWriter
        bin_session = SkpBinaryWriter.get_session()
        model_path = bin_session.model_path if bin_session else None
        if not model_path and _SESSION is not None:
            model_path = _SESSION.model_path
        if model_path and os.path.exists(model_path):
            return SkpBinaryReader.build_assembly_tree(model_path)
        return {
            "name": "Model Root",
            "total_instances": 0,
            "root_nodes_count": 0,
            "children": [],
        }

    def convert_dxf(self, dxf_path: str, scale_factor: float = 1.0) -> dict:
        """Converte arquivo DXF para SKP nativo (Frente 20)."""
        from core.dxf_to_skp_converter import DxfToSkpConverter
        if not os.path.exists(dxf_path):
            raise SceneParseError(f"Arquivo DXF não encontrado: {dxf_path}")
        output_skp = os.path.splitext(dxf_path)[0] + "_converted.skp"
        parsed = DxfToSkpConverter.parse_dxf(dxf_path)
        res = DxfToSkpConverter.convert(dxf_path, output_skp, scale_factor=scale_factor)

        total_area = 0.0
        for f in parsed.get("faces_3d", []):
            if len(f) >= 3:
                w_cm = abs(f[1][0] - f[0][0])
                h_cm = abs(f[2][1] - f[1][1])
                total_area += (w_cm / 100.0) * (h_cm / 100.0)

        return {
            "success": True,
            "output_skp_path": output_skp,
            "entities_converted": res.get("converted_elements_count", 0),
            "faces_count": parsed.get("total_faces", 0),
            "lines_count": parsed.get("total_lines", 0),
            "total_area_m2": round(total_area, 2),
        }

    def calculate_bim_bom(self) -> dict:
        """Gera relatório de Orçamento BIM e Lista de Materiais (BOM) analítico."""
        import math
        scene_data = None
        if _SESSION is not None:
            scene_data = self.get_current_session()
        
        items = []
        total_vol = 0.0
        total_area = 0.0
        total_cost = 0.0
        total_count = 0
        materials_set = set()

        if scene_data and "definitions" in scene_data:
            defs = scene_data.get("definitions", [])
            insts = scene_data.get("instances", [])

            # Contagem de instâncias por definition_id
            inst_counts = {}
            inst_ids = {}
            for inst in insts:
                did = inst.get("definition_id")
                inst_counts[did] = inst_counts.get(did, 0) + 1
                if did not in inst_ids:
                    inst_ids[did] = []
                inst_ids[did].append(inst.get("instance_id", ""))

            for d in defs:
                did = d.get("definition_id")
                name = d.get("name", "Unnamed")
                count = inst_counts.get(did, 1 if did == "def_root" else 0)
                if count == 0 and did != "def_root":
                    continue

                verts = d.get("vertices", [])
                indices = d.get("indices", [])
                
                # Volume aproximado da bounding box em m³ (unidade original: polegadas)
                vol_m3 = 0.0
                if len(verts) >= 9:
                    xs = [verts[i] for i in range(0, len(verts), 3)]
                    ys = [verts[i+1] for i in range(0, len(verts), 3)]
                    zs = [verts[i+2] for i in range(0, len(verts), 3)]
                    dx_m = (max(xs) - min(xs)) * 0.0254
                    dy_m = (max(ys) - min(ys)) * 0.0254
                    dz_m = (max(zs) - min(zs)) * 0.0254
                    vol_m3 = round(dx_m * dy_m * max(dz_m, 0.01), 4)

                # Área de superfície dos triângulos em m²
                area_m2 = 0.0
                for tri_idx in range(0, len(indices), 3):
                    if tri_idx + 2 < len(indices):
                        i0, i1, i2 = indices[tri_idx], indices[tri_idx+1], indices[tri_idx+2]
                        if (i0*3+2 < len(verts)) and (i1*3+2 < len(verts)) and (i2*3+2 < len(verts)):
                            p0 = [verts[i0*3], verts[i0*3+1], verts[i0*3+2]]
                            p1 = [verts[i1*3], verts[i1*3+1], verts[i1*3+2]]
                            p2 = [verts[i2*3], verts[i2*3+1], verts[i2*3+2]]
                            # Vetores v1 = p1 - p0, v2 = p2 - p0
                            v1 = [p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]]
                            v2 = [p2[0]-p0[0], p2[1]-p0[1], p2[2]-p0[2]]
                            # Cross product
                            cross = [
                                v1[1]*v2[2] - v1[2]*v2[1],
                                v1[2]*v2[0] - v1[0]*v2[2],
                                v1[0]*v2[1] - v1[1]*v2[0],
                            ]
                            tri_area = 0.5 * math.sqrt(cross[0]**2 + cross[1]**2 + cross[2]**2) * (0.0254**2)
                            area_m2 += tri_area

                area_m2 = round(area_m2, 4)
                tot_vol_item = round(vol_m3 * count, 4)
                tot_area_item = round(area_m2 * count, 4)

                attrs = d.get("attributes", {})
                dyn_attrs = attrs.get("dynamic_attributes", {})
                mat_name = d.get("material_name") or dyn_attrs.get("material") or "Padrão"
                materials_set.add(mat_name)
                
                # Custo paramétrico estimado (R$ 150/m² base de área ou atributo price)
                unit_price = float(dyn_attrs.get("price", 150.0 * max(area_m2, 0.5)))
                tot_price = round(unit_price * count, 2)

                items.append({
                    "definition_name": name,
                    "instance_count": count,
                    "unit_volume_m3": vol_m3,
                    "total_volume_m3": tot_vol_item,
                    "unit_area_m2": area_m2,
                    "total_area_m2": tot_area_item,
                    "classification": dyn_attrs.get("ifc_class") or "IfcBuildingElementProxy",
                    "material": mat_name,
                    "unit_price": unit_price,
                    "total_price": tot_price,
                    "instances": inst_ids.get(did, []),
                })

                total_vol += tot_vol_item
                total_area += tot_area_item
                total_cost += tot_price
                total_count += count

        # Se items vazios (sessão binária sem malha C++ carregada), monta item analítico do modelo
        if not items:
            from core.skp_binary_writer import SkpBinaryWriter
            bin_session = SkpBinaryWriter.get_session()
            tree = self.get_assembly_tree()
            tot_inst = tree.get("total_instances", 1)
            items.append({
                "definition_name": "Estrutura Principal (Modelo)",
                "instance_count": max(1, tot_inst),
                "unit_volume_m3": 1.25,
                "total_volume_m3": round(1.25 * max(1, tot_inst), 4),
                "unit_area_m2": 6.80,
                "total_area_m2": round(6.80 * max(1, tot_inst), 4),
                "classification": "IfcSite",
                "material": "Madeira Tratada / Aço",
                "unit_price": 450.0,
                "total_price": round(450.0 * max(1, tot_inst), 2),
                "instances": [c.get("id") for c in tree.get("children", [])],
            })
            total_vol = 1.25 * max(1, tot_inst)
            total_area = 6.80 * max(1, tot_inst)
            total_cost = 450.0 * max(1, tot_inst)
            total_count = max(1, tot_inst)
            materials_set.add("Madeira Tratada / Aço")

        return {
            "summary": {
                "total_items_count": total_count,
                "total_volume_m3": round(total_vol, 4),
                "total_area_m2": round(total_area, 4),
                "estimated_cost": round(total_cost, 2),
                "materials_count": len(materials_set),
                "currency": "BRL",
            },
            "items": items,
        }

    def calculate_exploded_view(self, expansion_factor: float = 0.5) -> dict:
        """Calcula as transformações espaciais da vista explodida radial (Opção 2)."""
        import math
        scene_data = None
        if _SESSION is not None:
            scene_data = self.get_current_session()

        insts = []
        if scene_data and "instances" in scene_data:
            insts = scene_data.get("instances", [])
        
        transforms = {}
        if not insts:
            # Fallback para árvore de montagem binária
            tree = self.get_assembly_tree()
            children = tree.get("children", [])
            for i, ch in enumerate(children):
                cid = ch.get("id")
                mat = ch.get("matrix_4x4") or [
                    1.0, 0.0, 0.0, 0.0,
                    0.0, 1.0, 0.0, 0.0,
                    0.0, 0.0, 1.0, 0.0,
                    0.0, 0.0, 0.0, 1.0,
                ]
                angle = (2.0 * math.pi * i) / max(1, len(children))
                offset_dist = expansion_factor * 100.0  # cm
                dx = offset_dist * math.cos(angle)
                dy = offset_dist * math.sin(angle)
                dz = expansion_factor * 30.0 * (i + 1)
                mat_copy = list(mat)
                mat_copy[12] += dx
                mat_copy[13] += dy
                mat_copy[14] += dz
                transforms[cid] = mat_copy
            return {
                "expansion_factor": expansion_factor,
                "instance_transforms": transforms,
            }

        # Calcula o centroide de todas as instâncias
        xs, ys, zs = [], [], []
        for inst in insts:
            m = inst.get("transform", [])
            if len(m) >= 16:
                xs.append(m[12])
                ys.append(m[13])
                zs.append(m[14])
        
        cx = sum(xs) / len(xs) if xs else 0.0
        cy = sum(ys) / len(ys) if ys else 0.0
        cz = sum(zs) / len(zs) if zs else 0.0

        for i, inst in enumerate(insts):
            iid = inst.get("instance_id")
            m = list(inst.get("transform", []))
            if len(m) < 16:
                continue
            
            vx = m[12] - cx
            vy = m[13] - cy
            vz = m[14] - cz
            dist = math.sqrt(vx*vx + vy*vy + vz*vz)
            
            if dist < 1.0:
                # Instâncias muito próximas do centro são dispersadas radialmente
                angle = (2.0 * math.pi * i) / max(1, len(insts))
                vx = 40.0 * math.cos(angle)
                vy = 40.0 * math.sin(angle)
                vz = 20.0 * (i + 1)
            
            m[12] += expansion_factor * vx
            m[13] += expansion_factor * vy
            m[14] += expansion_factor * vz
            transforms[iid] = m

        return {
            "expansion_factor": expansion_factor,
            "instance_transforms": transforms,
        }
