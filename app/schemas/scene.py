from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OpenSceneRequest(BaseModel):
    """Entrada de POST /scene/open."""

    path: str = Field(
        ...,
        min_length=1,
        description="Caminho absoluto de um arquivo .skp no disco local.",
        examples=[r"C:\Users\<usuario>\Desktop\modelo.skp"],
    )


class NewSceneFromTemplateRequest(BaseModel):
    """Entrada de POST /scene/new. `template_id` e uma das chaves fixas de
    TEMPLATES (ver app/services/scene_service.py) -- os mesmos 6 templates
    reais da Trimble mostrados na secao "Criar novo modelo" da Pagina
    Inicial."""

    template_id: str = Field(..., min_length=1, examples=["simple_meters"])


class FaceRangeDTO(BaseModel):
    """Um intervalo de triangulos (em `indices`, 3 por triangulo) que
    pertence a UMA face real do .skp -- usado pelo frontend pra mapear
    o `faceIndex` que o raycaster do Three.js devolve num clique de
    volta pro `face_id` real, e pintar so aquela face (ver
    "Ferramentas > Pintura" por face, REVERSE_ENGINEERING_NOTES.md
    secao 28.19)."""

    model_config = ConfigDict(from_attributes=True)

    face_id: str
    triangle_start: int
    triangle_count: int


class DefinitionDTO(BaseModel):
    """Geometria de uma definicao (deduplicada -- uma entrada por
    definicao unica, nao por uso/instancia). Arrays planos: 3 floats
    por vertice/normal, 3 indices por triangulo."""

    model_config = ConfigDict(from_attributes=True)

    definition_id: str
    name: str
    vertices: list[float]
    normals: list[float]
    indices: list[int]
    face_ranges: list[FaceRangeDTO] = Field(default_factory=list)
    always_faces_camera: bool = Field(
        default=False,
        description='Componente "sempre de frente para a camera" (ex.: o '
        "personagem de escala dos templates) -- SUComponentDefinitionGet"
        "Behavior, ver REVERSE_ENGINEERING_NOTES.md secao 25. O frontend "
        "reorienta esse componente em tempo real pra encarar a camera "
        "(so o eixo vertical/yaw) em vez de usar a rotacao estatica da "
        "instancia.",
    )


class InstanceDTO(BaseModel):
    """Uma ocorrencia real de uma definicao na arvore (nao deduplicado).
    `transform` e a matriz 4x4 column-major ja composta em espaco de
    mundo -- consumivel direto por `Matrix4.fromArray()` no Three.js.
    `parent_instance_id` preserva a hierarquia original da arvore (null
    pra `inst_root`, a pseudo-instancia sintetica do Entities raiz) --
    usado pelo Outliner do frontend pra remontar a arvore client-side."""

    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    definition_id: str
    transform: list[float]
    parent_instance_id: str | None = None
    tag: str | None = Field(
        default=None,
        description="Nome real da Etiqueta (Tag/Layer) desta instancia "
        "(SUDrawingElementGetLayer/SULayerGetName) -- 'Sem etiquetas' "
        "quando nenhuma foi atribuida explicitamente. `null` so pra "
        "'inst_root' (pseudo-instancia sintetica, nunca tem Etiqueta).",
    )


class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    model_path: str | None = Field(
        default=None,
        description="Caminho de disco do modelo aberto. `null` quando o "
        "modelo foi criado a partir de um template (POST /scene/new) e "
        "ainda nao foi salvo nenhuma vez -- nesse caso o primeiro "
        "POST /scene/save PRECISA informar `path` (equivalente a "
        '"Salvar Como" no SketchUp real).',
    )
    definitions: list[DefinitionDTO]
    instances: list[InstanceDTO]


class UpdateTransformRequest(BaseModel):
    """Entrada de PATCH /scene/instances/{instance_id}/transform."""

    transform: list[float] = Field(
        ...,
        min_length=16,
        max_length=16,
        description="Matriz 4x4 column-major em espaco de MUNDO (mesma "
        "convencao do campo `transform` em InstanceDTO) -- o backend "
        "converte pra local antes de gravar na SketchUpAPI.dll.",
    )


class UpdateTransformResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    applied: bool


class SaveSceneRequest(BaseModel):
    """Entrada de POST /scene/save. `path` vazio/omitido sobrescreve o
    arquivo que foi aberto."""

    path: str | None = Field(default=None, min_length=1)


class SaveSceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    saved: bool
    path: str


class DeleteInstanceResponse(BaseModel):
    """Saida de DELETE /scene/instances/{instance_id} -- equivalente
    nativo de "Editar > Excluir"/Del (ver REVERSE_ENGINEERING_NOTES.md
    secao 26)."""

    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    deleted: bool


class PaintInstanceRequest(BaseModel):
    """Entrada de POST /scene/instances/{instance_id}/material --
    equivalente real de "Ferramentas > Pintura" (ver
    REVERSE_ENGINEERING_NOTES.md secao 28: SUMaterialCreate/
    SUMaterialSetColor/SUDrawingElementSetMaterial)."""

    r: int = Field(..., ge=0, le=255, examples=[255])
    g: int = Field(..., ge=0, le=255, examples=[0])
    b: int = Field(..., ge=0, le=255, examples=[0])


class PaintInstanceResponse(BaseModel):
    """Nao devolve a cena inteira -- pintura so muda aparencia, nao
    topologia/malha, ver app/repositories/skp_engine_repository.py
    paint_instance()."""

    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    painted: bool
    color: list[int]


class PaintFaceRequest(BaseModel):
    """Entrada de POST /scene/faces/{face_id}/material -- equivalente
    real de pintar UMA face especifica (nao a instancia inteira) no
    SketchUp (ver REVERSE_ENGINEERING_NOTES.md secao 28.19:
    SUFaceSetFrontMaterial/SUFaceToDrawingElement). A face pertence a
    geometria da DEFINICAO, entao a mudanca fica gravada pra TODAS as
    instancias que compartilham essa definicao."""

    r: int = Field(..., ge=0, le=255, examples=[255])
    g: int = Field(..., ge=0, le=255, examples=[0])
    b: int = Field(..., ge=0, le=255, examples=[0])


class PaintFaceResponse(BaseModel):
    """Nao devolve a cena inteira -- pintura so muda aparencia, nao
    topologia/malha, ver app/repositories/skp_engine_repository.py
    paint_face()."""

    model_config = ConfigDict(from_attributes=True)

    face_id: str
    painted: bool
    color: list[int]


class TagInstanceRequest(BaseModel):
    """Entrada de POST /scene/instances/{instance_id}/tag -- equivalente
    real de "Ferramentas > Etiqueta" (a API interna ainda chama isso de
    "Layer", nome legado da Trimble -- ver REVERSE_ENGINEERING_NOTES.md
    seção 28.17)."""

    name: str = Field(..., min_length=1, examples=["Etiqueta 1"])


class TagInstanceResponse(BaseModel):
    """Não devolve a cena inteira -- etiquetar só muda metadado, não
    topologia/malha, ver app/repositories/skp_engine_repository.py
    tag_instance()."""

    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    tag_name: str


class TagDTO(BaseModel):
    """Uma Etiqueta (Tag/Layer) real do modelo -- ver
    REVERSE_ENGINEERING_NOTES.md seção 28.22 (SUModelGetLayers/
    SULayerGetName/SULayerGetVisibility). `is_default` marca a Etiqueta
    padrão real do modelo ("Sem etiquetas"), que nenhuma instância
    atribuída explicitamente usa mas toda instância sem Etiqueta
    pertence a ela."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    visible: bool
    is_default: bool = False


class ListTagsResponse(BaseModel):
    """Saída de GET /scene/tags."""

    tags: list[TagDTO]


class SetTagVisibilityRequest(BaseModel):
    """Entrada de PATCH /scene/tags/{name}/visibility -- equivalente real
    do ícone de olho ao lado de cada Etiqueta na Bandeja padrão real."""

    visible: bool


class SetTagVisibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    visible: bool


class ScenePageDTO(BaseModel):
    """Uma Cena real do modelo (model/scene.h -- a API Ruby chama o
    mesmo objeto de "Page", mesmo dado). Nome prefixado "Page" aqui só
    pra não colidir com `SceneResponse` (o DTO da cena 3D inteira, termo
    já sobrecarregado neste arquivo)."""

    model_config = ConfigDict(from_attributes=True)

    scene_id: str
    name: str
    active: bool


class ListScenePagesResponse(BaseModel):
    """Saída de GET /scene/pages -- TODAS as cenas reais do modelo
    aberto (inclusive as que já vinham salvas no .skp antes desta
    sessão)."""

    model_config = ConfigDict(from_attributes=True)

    pages: list[ScenePageDTO]


class CreateScenePageRequest(BaseModel):
    """Entrada de POST /scene/pages -- equivalente real de "Janela >
    Bandeja padrão > Cenas > +" (ver REVERSE_ENGINEERING_NOTES.md seção
    28.20: SUSceneCreate/SUSceneSetName/SUModelAddScenes). NÃO captura
    câmera/estilo visual (limitação documentada, este projeto não tem
    binding de SUCameraRef)."""

    name: str = Field(..., min_length=1, examples=["Cena 1"])


class CreateScenePageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scene_id: str
    name: str


class ActivateScenePageResponse(BaseModel):
    """Saída de POST /scene/pages/{scene_id}/activate -- SUModelSetActiveScene
    real (ver core/su_api.py). Não move a câmera do viewer nesta sessão
    (mesma limitação de CreateScenePageRequest)."""

    model_config = ConfigDict(from_attributes=True)

    scene_id: str
    activated: bool


class SetInstanceAxesRequest(BaseModel):
    """Entrada de POST /scene/instances/{instance_id}/axes -- equivalente
    real de "Ferramentas > Eixos" (ver REVERSE_ENGINEERING_NOTES.md seção
    28.21: SUAxesCreateCustom/SUComponentDefinitionSetAxes). Os 3 pontos
    já chegam em POLEGADAS no espaço LOCAL da definição por trás da
    instância clicada (mesma convenção de unidade do resto da API) --
    o frontend faz essa conversão antes de mandar. `origin`/`x_point`/
    `y_point` não podem ser colineares (backend valida e recusa com 400)."""

    origin: list[float] = Field(..., min_length=3, max_length=3)
    x_point: list[float] = Field(..., min_length=3, max_length=3)
    y_point: list[float] = Field(..., min_length=3, max_length=3)


class SetInstanceAxesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    applied: bool


class ExportModelRequest(BaseModel):
    """Entrada de POST /scene/export/obj -- equivalente parcial de
    "Arquivo > Exportar > Modelo 3D..." (so formato OBJ por enquanto)."""

    path: str = Field(
        ...,
        min_length=1,
        description="Caminho absoluto de destino, terminando em .obj.",
        examples=[r"C:\Users\<usuario>\Desktop\modelo.obj"],
    )


class ExportModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    saved: bool
    path: str


class AddRectangleRequest(BaseModel):
    """Entrada de POST /scene/geometry/rectangle -- equivalente real de
    "Desenho > Formas > Retângulo" (ver REVERSE_ENGINEERING_NOTES.md
    secao 28). Dimensões em METROS (mesma unidade exibida no frontend);
    o retângulo nasce centrado na origem, deitado no chão (plano XY,
    Z=0)."""

    width_m: float = Field(..., gt=0, examples=[1.0])
    height_m: float = Field(..., gt=0, examples=[1.0])
    as_group: bool = Field(
        default=False,
        description="Quando true, a face nasce dentro de um Grupo novo "
        'real (equivalente a "Editar > Criar grupo") em vez de solta na '
        "Entities raiz -- ver REVERSE_ENGINEERING_NOTES.md seção 28.17.",
    )


class AutosaveDraftDTO(BaseModel):
    """Um rascunho de autosave real (.skp gravado em app/data/autosave/
    a cada edicao, ver app/repositories/skp_engine_repository.py
    _autosave()) oferecido pra recuperacao na Pagina Inicial quando o
    backend reinicia com edicoes nao salvas pendentes."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    original_path: str
    name: str
    saved_at: str


class ListAutosaveDraftsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    drafts: list[AutosaveDraftDTO]


class DiscardAutosaveDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    discarded: bool


class AddRectangleResponse(BaseModel):
    """A cena inteira pós-criação -- diferente de excluir/mover uma
    instância, geometria nova precisa que o frontend reconstrua a malha
    "root" (ver app/repositories/skp_engine_repository.py add_rectangle)."""

    model_config = ConfigDict(from_attributes=True)

    scene: SceneResponse
