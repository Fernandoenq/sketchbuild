from __future__ import annotations
from typing import Any

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
    material_name: str | None = None


class MaterialDTO(BaseModel):
    """Definição de Material PBR (Frente 2) consumível pelo Three.js."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    color: list[int] = Field(default_factory=lambda: [140, 153, 166])
    opacity: float = 1.0
    has_texture: bool = False
    texture_url: str | None = None
    metalness: float = 0.05
    roughness: float = 0.85
    attributes: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Dicionários de atributos do material (ex: VRayInfo)",
    )


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
    uvs: list[float] = Field(default_factory=list, description="Coordenadas UV analíticas [u, v, ...]")
    material_name: str | None = Field(default=None, description="Nome do material principal da definição")
    face_materials: list[str] = Field(default_factory=list, description="Lista de materiais de cada face")
    always_faces_camera: bool = Field(
        default=False,
        description='Componente "sempre de frente para a camera" (ex.: o '
        "personagem de escala dos templates) -- SUComponentDefinitionGet"
        "Behavior, ver REVERSE_ENGINEERING_NOTES.md secao 25. O frontend "
        "reorienta esse componente em tempo real pra encarar a camera "
        "(so o eixo vertical/yaw) em vez de usar a rotacao estatica da "
        "instancia.",
    )
    attributes: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Dicionários de atributos e componentes dinâmicos (dynamic_attributes)",
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
    attributes: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Dicionários de atributos da instância (dynamic_attributes / SU_InstanceSet)",
    )


class CameraDTO(BaseModel):
    """Camera REAL "atual" do modelo (SUModelGetCamera/SUCameraGetOrientation
    -- ver core/su_api.py get_model_camera() e REVERSE_ENGINEERING_NOTES.md
    secao 28.23). `eye`/`target`/`up` em polegadas, Z-up (mesma convencao
    bruta de `InstanceDTO.transform` -- o frontend converte pra metros/
    Y-up). `fov_deg`/`fov_is_height` vem `null` quando a camera nao esta
    em modo perspectiva (o frontend cai pro enquadramento automatico por
    bounding box nesse caso)."""

    model_config = ConfigDict(from_attributes=True)

    eye: list[float]
    target: list[float]
    up: list[float]
    perspective: bool
    fov_deg: float | None = None
    fov_is_height: bool = True


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
    id: int | None = None
    material_name: str | None = None


class ScenePageDTO(BaseModel):
    """Uma Cena real do modelo (model/scene.h -- a API Ruby chama o
    mesmo objeto de "Page", mesmo dado)."""

    model_config = ConfigDict(from_attributes=True)

    scene_id: str
    name: str
    active: bool
    include_in_animation: bool = True
    use_camera: bool = True


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
    camera: CameraDTO | None = Field(
        default=None,
        description="Camera real salva no arquivo (ver CameraDTO) -- o "
        "frontend usa isso pra posicionar a camera inicial em vez de so "
        "enquadrar pela bounding box, ver REVERSE_ENGINEERING_NOTES.md "
        "secao 28.23.",
    )
    tags: list[TagDTO] = Field(
        default_factory=list,
        description="Lista de etiquetas / camadas (Tags / Layers) presentes no modelo",
    )
    scenes: list[ScenePageDTO] = Field(
        default_factory=list,
        description="Lista de cenas / abas reais do modelo (Pages)",
    )
    materials: dict[str, MaterialDTO] = Field(
        default_factory=dict,
        description="Dicionário de materiais PBR mapeados para Three.js",
    )
    reader_mode: str = Field(
        default="ctypes",
        description="Indica o motor que gerou a cena ('ctypes' ou 'binary_native')",
    )
    model_attributes: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Dicionários de atributos globais do modelo (ModelProperties, etc)",
    )


class SceneAttributesResponse(BaseModel):
    """Resposta de GET /scene/attributes com dicionários de atributos e componentes dinâmicos."""

    model_config = ConfigDict(from_attributes=True)

    model: dict[str, dict[str, Any]] = Field(default_factory=dict)
    definitions: dict[str, dict[str, dict[str, Any]]] = Field(default_factory=dict)
    instances: list[dict[str, Any]] = Field(default_factory=list)
    materials: dict[str, dict[str, dict[str, Any]]] = Field(default_factory=dict)


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
    arquivo que foi aberto. `overwrite_confirmed` confirma explicitamente
    que, se `path` ja existir no disco e for diferente do arquivo aberto
    nesta sessao, pode sobrescrever mesmo assim (ver
    SceneOverwriteConfirmationRequiredError em app/domain/exceptions.py)."""

    path: str | None = Field(default=None, min_length=1)
    overwrite_confirmed: bool = False


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


class ListTagsResponse(BaseModel):
    """Saída de GET /scene/tags."""

    tags: list[TagDTO]


class UpdateCameraRequest(BaseModel):
    """Entrada de PATCH /scene/camera para atualizar a orientação da câmera."""

    eye: list[float] = Field(..., description="Coordenadas [x, y, z] em polegadas")
    target: list[float] = Field(..., description="Coordenadas [x, y, z] em polegadas")
    up: list[float] | None = Field(default=None, description="Vetor unitário [x, y, z]")
    fov_deg: float | None = Field(default=None, description="Campo de visão em graus")


class UpdateCameraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    applied: bool


class SetTagVisibilityRequest(BaseModel):
    """Entrada de PATCH /scene/tags/{name}/visibility -- equivalente real
    do ícone de olho ao lado de cada Etiqueta na Bandeja padrão real."""

    visible: bool


class SetTagVisibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    visible: bool


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


class DuplicateInstanceRequest(BaseModel):
    """Entrada de POST /scene/instances/{instance_id}/duplicate."""

    transform: list[float] | None = Field(
        default=None,
        description="Matriz 4x4 column-major opcional para a nova instância duplicada.",
    )
    offset_delta_cm: list[float] | None = Field(
        default=None,
        description="Deslocamento relativo [dx, dy, dz] em centímetros em relação à instância original.",
    )


class DuplicateInstanceResponse(BaseModel):
    """Saída de POST /scene/instances/{instance_id}/duplicate."""

    model_config = ConfigDict(from_attributes=True)

    instance: InstanceDTO
    duplicated: bool = True


# ============================================================================
# Frentes 13, 15, 19, 20 & Desmontador / Orçamentador BIM (Opções 1 e 2)
# ============================================================================

class CreateBoxRequest(BaseModel):
    """Entrada para criação de Sólido 3D Manifold (Frente 13)."""

    width_m: float = Field(..., gt=0, description="Largura em metros (eixo X)", examples=[1.0])
    length_m: float = Field(..., gt=0, description="Comprimento em metros (eixo Y)", examples=[2.0])
    height_m: float = Field(..., gt=0, description="Altura em metros (eixo Z)", examples=[0.8])
    offset_xyz_cm: list[float] | None = Field(
        default=None,
        description="Deslocamento relativo opcional [dx, dy, dz] em centímetros.",
        examples=[[0.0, 0.0, 0.0]],
    )


class BoxDetailsDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "Box"
    vertex_count: int = 8
    edge_count: int = 12
    face_count: int = 6
    dimensions_m: list[float]
    volume_m3: float


class CreateBoxResponse(BaseModel):
    """Resposta com detalhes do sólido e cena atualizada."""

    model_config = ConfigDict(from_attributes=True)

    box: BoxDetailsDTO
    scene: SceneResponse


class SetStyleRequest(BaseModel):
    """Entrada de configuração de Estilos de Renderização (Frente 19)."""

    mode: str = Field(
        default="textured",
        description="Modo de exibição: textured, shaded, hidden_line, wireframe, monochrome",
        examples=["hidden_line"],
    )
    xray: bool = Field(default=False, description="Modo Raio-X (transparência técnica)")
    profiles_width: int = Field(default=2, ge=1, le=10, description="Largura do traço de contornos/arestas")
    background_rgb: list[int] | None = Field(
        default=None,
        description="Cor de fundo RGB [r, g, b] 0-255",
        examples=[[255, 255, 255]],
    )
    sky_rgb: list[int] | None = Field(
        default=None,
        description="Cor do céu RGB [r, g, b] 0-255",
        examples=[[200, 220, 240]],
    )


class SetStyleResponse(BaseModel):
    """Resposta de alteração de Estilo de Renderização."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    mode: str
    xray: bool
    profiles_width: int
    style_xml_updated: bool = True


class AssemblyTreeNodeDTO(BaseModel):
    """Nó da Árvore Hierárquica do Outliner e Vista Explodida (Frente 15)."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    is_group: bool = False
    definition_id: int | None = None
    definition_name: str | None = None
    parent_def_id: int | None = None
    translation_cm: list[float] | None = None
    matrix_4x4: list[float] | None = None
    children: list[AssemblyTreeNodeDTO] = Field(default_factory=list)


class AssemblyTreeResponse(BaseModel):
    """Resposta de GET /scene/assembly-tree."""

    model_config = ConfigDict(from_attributes=True)

    name: str = "Model Root"
    total_instances: int
    root_nodes_count: int
    children: list[AssemblyTreeNodeDTO]


class ConvertDxfRequest(BaseModel):
    """Entrada para conversão de arquivo DXF para SKP (Frente 20)."""

    dxf_path: str = Field(..., min_length=1, description="Caminho do arquivo DXF no servidor")
    scale_factor: float = Field(default=1.0, gt=0, description="Fator de escala do DXF")


class ConvertDxfResponse(BaseModel):
    """Resposta de conversão DXF -> SKP."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    output_skp_path: str
    entities_converted: int
    faces_count: int
    lines_count: int
    total_area_m2: float


class BimItemDTO(BaseModel):
    """Item analítico do Orçamento BIM / BOM."""

    model_config = ConfigDict(from_attributes=True)

    definition_name: str
    instance_count: int
    unit_volume_m3: float
    total_volume_m3: float
    unit_area_m2: float
    total_area_m2: float
    classification: str | None = None
    material: str | None = None
    unit_price: float = 0.0
    total_price: float = 0.0
    instances: list[str] = Field(default_factory=list)


class BimBomSummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_items_count: int
    total_volume_m3: float
    total_area_m2: float
    estimated_cost: float
    materials_count: int
    currency: str = "BRL"


class BimBomReportResponse(BaseModel):
    """Resposta de GET /scene/bim-report."""

    model_config = ConfigDict(from_attributes=True)

    summary: BimBomSummaryDTO
    items: list[BimItemDTO]


class ExplodedViewRequest(BaseModel):
    """Entrada de cálculo paramétrico de Vista Explodida."""

    expansion_factor: float = Field(default=0.5, ge=0.0, le=5.0, description="Fator de explosão lambda (0.0 = montado, 1.0+ = explodido)")


class ExplodedViewResponse(BaseModel):
    """Matrizes transformadas para cada instância na vista explodida."""

    model_config = ConfigDict(from_attributes=True)

    expansion_factor: float
    instance_transforms: dict[str, list[float]]


# ============================================================================
# Frente 21: Exportador Multi-formato (GLTF/GLB e IFC BIM)
# ============================================================================

class ExportGlbRequest(BaseModel):
    """Entrada de POST /scene/export/glb."""

    path: str = Field(
        ...,
        min_length=1,
        description="Caminho absoluto de destino para o arquivo binário .glb",
        examples=[r"C:\Users\<usuario>\Desktop\modelo.glb"],
    )


class ExportGlbResponse(BaseModel):
    """Resposta de exportação glTF 2.0 Binary (.glb)."""

    model_config = ConfigDict(from_attributes=True)

    saved: bool = True
    path: str
    file_size_bytes: int
    mesh_count: int
    node_count: int
    format: str = "glTF 2.0 Binary (.glb)"


class ExportIfcRequest(BaseModel):
    """Entrada de POST /scene/export/ifc."""

    path: str = Field(
        ...,
        min_length=1,
        description="Caminho absoluto de destino para o arquivo BIM .ifc",
        examples=[r"C:\Users\<usuario>\Desktop\modelo.ifc"],
    )
    project_name: str = Field(
        default="Projeto SketchBuild",
        description="Nome do projeto na estrutura espacial IfcProject",
    )


class ExportIfcResponse(BaseModel):
    """Resposta de exportação IFC4 / IFC2X3 (STEP ISO 10303-21)."""

    model_config = ConfigDict(from_attributes=True)

    saved: bool = True
    path: str
    file_size_bytes: int
    elements_count: int
    format: str = "Industry Foundation Classes (IFC4 STEP)"


# ============================================================================
# Frente 22: Autoria Interativa de Desenho no Canvas WebGL
# ============================================================================

class AddLineGeometryRequest(BaseModel):
    """Entrada para criação de aresta 3D livre via desenho interativo."""

    start_m: list[float] = Field(..., min_length=3, max_length=3, description="Ponto de partida [x, y, z] em metros")
    end_m: list[float] = Field(..., min_length=3, max_length=3, description="Ponto final [x, y, z] em metros")


class AddFaceGeometryRequest(BaseModel):
    """Entrada para criação de face 3D poligonal coplanar via fechamento de polígono."""

    points_m: list[list[float]] = Field(..., min_length=3, description="Lista de 3 ou mais pontos [x, y, z] em metros")


class AddGeometryEntityResponse(BaseModel):
    """Resposta de criação de geometria livre (Aresta ou Face)."""

    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    entity: dict[str, Any]




# ============================================================================
# Frente 23: Integracao Industrial Parkelo e Lista de Corte Excel (.xlsx)
# ============================================================================

class ExportCutlistRequest(BaseModel):
    """Entrada para exportacao da lista de corte e orcamento em Excel."""

    path: str = Field(..., min_length=1, description="Caminho de destino do arquivo .xlsx")


class ExportCutlistResponse(BaseModel):
    """Resposta da exportacao da lista de corte e orcamento."""

    model_config = ConfigDict(from_attributes=True)

    saved: bool = True
    path: str
    file_size_bytes: int
    total_pecas: int
    total_custo_brl: float
    sheets: list[str]


# ============================================================================
# Frente 14: Curvas, Circulos e Cilindros Parametricos
# ============================================================================

class AddCircleGeometryRequest(BaseModel):
    """Entrada para criacao de circulo plano B-Rep."""

    radius_m: float = Field(..., gt=0, description="Raio do circulo em metros")
    center_xyz_m: list[float] = Field(default=[0.0, 0.0, 0.0], min_length=3, max_length=3)
    num_segments: int = Field(default=24, ge=3, le=128)


class AddCylinderGeometryRequest(BaseModel):
    """Entrada para criacao de Cilindro Sólido Manifold."""

    radius_m: float = Field(..., gt=0, description="Raio da base em metros")
    height_m: float = Field(..., gt=0, description="Altura do cilindro em metros")
    center_xyz_m: list[float] = Field(default=[0.0, 0.0, 0.0], min_length=3, max_length=3)
    num_segments: int = Field(default=16, ge=4, le=128)


# ============================================================================
# Frente 24: Ferramenta Push/Pull Interativa no Canvas WebGL
# ============================================================================

class ExtrudeFaceGeometryRequest(BaseModel):
    """Entrada para extrusao de face coplanar existente (Push/Pull)."""

    points_m: list[list[float]] = Field(..., min_length=3, description="Vertices da face a ser extrudada")
    distance_m: float = Field(..., description="Distancia de extrusao ao longo da normal em metros")
    normal: list[float] | None = Field(default=None, min_length=3, max_length=3, description="Vetor normal")

# ============================================================================
# Frente 26: Sequenciador de Montagem e Manual Tecnico 3D
# ============================================================================

class AssemblyStepsResponse(BaseModel):
    """Resposta de GET /scene/assembly-steps."""

    model_config = ConfigDict(from_attributes=True)

    steps: list[dict[str, Any]]
    total_steps: int
    total_instances: int


class ExportAssemblyManualRequest(BaseModel):
    """Entrada para exportacao do manual de montagem em HTML."""

    project_name: str = "Playground Parkelo"
    path: str | None = None


class ExportAssemblyManualResponse(BaseModel):
    """Resposta da exportacao do manual de montagem em HTML."""

    model_config = ConfigDict(from_attributes=True)

    saved: bool = True
    path: str | None = None
    html_content: str


# ============================================================================
# Frente 27: Desenho Tecnico Vetorial 2D (Plantas Baixas e Elevacoes)
# ============================================================================

class ExportDrawing2DRequest(BaseModel):
    """Entrada para exportacao de desenho tecnico 2D vetorial em SVG."""

    path: str = Field(..., min_length=1, description="Caminho de destino .svg")
    view_type: str = Field(default="top", description="Tipo de vista: top (planta), front (elevacao frontal), side (lateral)")
    title: str = Field(default="Prancha Tecnica de Engenharia", description="Titulo do carimbo")
    scale: str = Field(default="1:50", description="Escala arquitetonica")


class ExportDrawing2DResponse(BaseModel):
    """Resposta da exportacao de desenho tecnico 2D vetorial."""

    model_config = ConfigDict(from_attributes=True)

    saved: bool = True
    path: str
    view_type: str
    scale: str
    file_size_bytes: int


# ============================================================================
# Frente 28: Estudo Solar e Sombras Analiticas (Heliodon)
# ============================================================================

class SolarStudyRequest(BaseModel):
    """Entrada para calculo de posicao solar e insolação."""

    day_of_year: int = Field(default=80, ge=1, le=365, description="Dia do ano (1 a 365)")
    hour: float = Field(default=14.0, ge=0.0, le=24.0, description="Hora solar (0.0 a 24.0)")
    latitude: float = Field(default=-23.5505, description="Latitude em graus")
    longitude: float = Field(default=-46.6333, description="Longitude em graus")


class SolarStudyResponse(BaseModel):
    """Resposta do estudo solar com posicao atual e curva horaria."""

    model_config = ConfigDict(from_attributes=True)

    position: dict[str, Any]
    day_curve: dict[str, Any]


# ============================================================================
# Frente 17: Planos e Cortes de Seção (SectionPlane)
# ============================================================================

class SectionPlaneRequest(BaseModel):
    """Entrada para criação de Plano de Corte de Seção."""

    plane_abcd: list[float] = Field(
        default=[0.0, 0.0, 1.0, 0.0],
        description="Equação analítica do plano [a, b, c, d] onde ax + by + cz + d = 0 (d em metros)"
    )
    name: str = Field(default="Corte A-A", description="Nome identificador do corte")
    symbol: str = Field(default="A1", description="Símbolo técnico do corte")


class SectionPlaneResponse(BaseModel):
    """Resposta com dados do Plano de Seção criado/listado."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SectionPlane"
    plane: list[float]
    plane_inches: list[float]
    name: str
    symbol: str


# ============================================================================
# Frente 18: Linhas de Guia e Pontos de Construção (Tape Measure)
# ============================================================================

class GuideLineRequest(BaseModel):
    """Entrada para criação de Linha de Guia / Trena."""

    start: list[float] = Field(description="Ponto inicial [x, y, z] em metros")
    end: list[float] = Field(description="Ponto final ou vetor de direção [x, y, z] em metros")
    is_infinite: bool = Field(default=False, description="Se a linha de guia é infinita")


class GuidePointRequest(BaseModel):
    """Entrada para criação de Ponto de Construção."""

    position: list[float] = Field(description="Coordenada do ponto [x, y, z] em metros")


class GuidesResponse(BaseModel):
    """Resposta com lista de linhas de guia e pontos de construção da cena."""

    model_config = ConfigDict(from_attributes=True)

    guide_lines: list[dict[str, Any]]
    guide_points: list[dict[str, Any]]


# ============================================================================
# Frente 25: Operações Booleanas de Sólidos (Solid Tools / CSG)
# ============================================================================

class BooleanOperationRequest(BaseModel):
    """Entrada para operação booleana sólida CSG (Furação, Subtração, União)."""

    operation: str = Field(
        default="subtract",
        description="Tipo de operação: subtract (A - B), subtract_hole (furação cilíndrica) ou union (A + B)"
    )
    main_shape: dict[str, Any] = Field(description="Geometria do sólido principal (box ou cylinder)")
    tool_shape: dict[str, Any] = Field(description="Geometria da ferramenta cortante")


class BooleanOperationResponse(BaseModel):
    """Resposta com a malha B-Rep resultante da operação booleana."""

    model_config = ConfigDict(from_attributes=True)

    operation: str
    type: str
    faces_count: int
    faces: list[Any]


# ============================================================================
# Frente 29: Exportador Executivo de Proposta Comercial em PDF Vetorial
# ============================================================================

class ExecutivePdfExportRequest(BaseModel):
    """Entrada para geração da Proposta Executiva e Prancha Técnica em PDF."""

    project_name: str = Field(default="Parque Infantil Parkelô", description="Nome do projeto")
    author: str = Field(default="SketchBuild Engine", description="Nome do engenheiro / autor")
    client_name: str = Field(default="Cliente Final", description="Nome do cliente / município")
    output_filename: str = Field(default="proposta_executiva_parkelo.pdf", description="Nome do arquivo PDF")


class ExecutivePdfExportResponse(BaseModel):
    """Resposta com o status e caminho do PDF compilado."""

    model_config = ConfigDict(from_attributes=True)

    file_path: str
    size_bytes: int
    project_name: str
    pages: int = 1


# ============================================================================
# Frente 30: Ferramenta de Offset / Equidistância 2D/3D (Ferramenta F)
# ============================================================================

class OffsetFaceRequest(BaseModel):
    """Entrada para cálculo de deslocamento paralelo (Offset) de polígonos."""

    points: list[list[float]] = Field(description="Lista de vértices coplanares [[x, y, z], ...]")
    distance: float = Field(default=0.10, description="Distância do deslocamento métrico em metros")
    inside: bool = Field(default=True, description="True para interior, False para exterior")
    create_frame: bool = False


class OffsetFaceResponse(BaseModel):
    """Resposta com a face deslocada ou moldura criada."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str
    distance_m: float
    inside: bool
    face_id: str | None = None
    frame_faces_count: int | None = None


# ============================================================================
# Frentes 31 a 35: Follow Me, Arcos 3D, Rotação, Auditoria NBR 16071 e OBJ
# ============================================================================

class FollowMeRequest(BaseModel):
    """Entrada para extrusão Follow Me ao longo de caminho 3D."""

    path_points: list[list[float]] = Field(description="Sequência de pontos 3D [[x, y, z], ...] do caminho guia")
    profile_type: str = Field(default="circle", description="'circle' para tubos ou 'custom' para perfil poligonal")
    radius: float = Field(default=0.10, description="Raio se perfil for circular")
    profile_points: list[list[float]] | None = Field(default=None, description="Pontos 2D [(u, v), ...] se customizado")
    close_caps: bool = Field(default=True, description="Fechar tampas nas extremidades")


class FollowMeResponse(BaseModel):
    """Resposta da extrusão Follow Me."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "FollowMeExtrusion"
    path_points_count: int
    profile_points_count: int
    faces_count: int


class ArcRequest(BaseModel):
    """Entrada para geração de arco circular 3D."""

    start: list[float] = Field(description="Ponto inicial [x, y, z]")
    end: list[float] = Field(description="Ponto final [x, y, z]")
    sagitta: float = Field(default=0.30, description="Altura da flecha / curvatura em metros")
    num_segments: int = Field(default=12, ge=3, le=64, description="Número de segmentos da curva")


class ArcResponse(BaseModel):
    """Resposta do arco circular 3D gerado."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "Arc"
    points: list[list[float]]
    radius: float
    sagitta: float
    chord_length: float
    segments_count: int


class RotateTransformRequest(BaseModel):
    """Entrada para rotação com transferidor de instância ou geometria."""

    instance_id: str = Field(description="ID da instância a rotacionar")
    pivot: list[float] = Field(default=[0.0, 0.0, 0.0], description="Centro de rotação [cx, cy, cz]")
    axis: list[float] = Field(default=[0.0, 0.0, 1.0], description="Eixo normal de rotação [kx, ky, kz]")
    angle_degrees: float = Field(default=45.0, description="Ângulo de rotação em graus")


class RotateTransformResponse(BaseModel):
    """Resposta da transformação de rotação aplicada."""

    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    angle_degrees: float
    pivot: list[float]
    axis: list[float]
    transform_matrix_16: list[float]


class SafetyAuditResponse(BaseModel):
    """Relatório estruturado de auditoria NBR 16071 para playgrounds."""

    model_config = ConfigDict(from_attributes=True)

    compliant: bool
    safety_score: int
    standard: str
    total_checks: int
    approved_checks: int
    safety_seal: str
    tests: list[dict[str, Any]]


class ImportObjRequest(BaseModel):
    """Entrada para importação de malha 3D Wavefront OBJ."""

    file_path: str = Field(description="Caminho completo do arquivo .obj no disco")
    scale: float = Field(default=1.0, description="Fator de escala de importação")


class ImportObjResponse(BaseModel):
    """Resposta com resumo da importação do arquivo OBJ."""

    model_config = ConfigDict(from_attributes=True)

    success: bool
    imported_vertices: int
    imported_faces: int
    scale: float


# ============================================================================
# Frentes 36 a 40: Nesting 1D/2D, Terrenos, FEA Estrutural, Escala e CAM DXF
# ============================================================================

class NestingRequest(BaseModel):
    """Entrada para otimização de plano de corte de barras e toras."""

    demanded_pieces: list[dict[str, Any]] = Field(description="Lista de peças [{'name': str, 'length_m': float, 'quantity': int}]")
    stock_bar_length_m: float = Field(default=3.00, description="Comprimento comercial da barra bruta em metros")


class NestingResponse(BaseModel):
    """Resposta com o plano de corte otimizado."""

    model_config = ConfigDict(from_attributes=True)

    stock_bar_length_m: float
    total_bars_required: int
    total_pieces_cut: int
    total_stock_used_m: float
    total_net_pieces_m: float
    total_scrap_m: float
    efficiency_percent: float
    scrap_percent: float
    bars: list[dict[str, Any]]


class TerrainRequest(BaseModel):
    """Entrada para geração de terreno paramétrico Sandbox."""

    width_m: float = Field(default=10.0, description="Largura do terreno em metros")
    length_m: float = Field(default=10.0, description="Comprimento do terreno em metros")
    grid_resolution_m: float = Field(default=1.0, description="Resolução da malha em metros")
    slope_x_pct: float = Field(default=0.0, description="Declividade em X (%)")
    slope_y_pct: float = Field(default=5.0, description="Declividade em Y (%)")


class TerrainResponse(BaseModel):
    """Resposta com a malha topográfica gerada."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "TerrainMesh"
    dimensions_m: list[float]
    grid_size: list[int]
    vertex_count: int
    triangle_count: int
    mean_elevation_m: float
    earthwork_cut_m3: float
    earthwork_fill_m3: float


class StructuralAnalysisRequest(BaseModel):
    """Entrada para cálculo estrutural e tensões em vigas de madeira."""

    span_length_m: float = Field(default=2.00, description="Vão livre da viga em metros")
    load_kn_per_m: float = Field(default=2.50, description="Carga distribuída em kN/m")
    section_type: str = Field(default="circular", description="'circular' ou 'rectangular'")
    diameter_m: float = Field(default=0.16, description="Diâmetro se tora circular")
    width_m: float = Field(default=0.08, description="Largura se retangular")
    height_m: float = Field(default=0.16, description="Altura se retangular")


class StructuralAnalysisResponse(BaseModel):
    """Resposta com o laudo de estabilidade estrutural."""

    model_config = ConfigDict(from_attributes=True)

    section_type: str
    span_length_m: float
    applied_load_kn_m: float
    max_bending_moment_kn_m: float
    bending_stress_mpa: float
    admissible_stress_mpa: float
    max_deflection_mm: float
    deflection_limit_mm: float
    safety_factor: float
    deflection_compliant: bool
    stress_compliant: bool
    structural_status: str


class ScaleRequest(BaseModel):
    """Entrada para ferramenta de escala paramétrica."""

    instance_id: str = Field(description="ID da instância a redimensionar")
    scale_factors: list[float] = Field(default=[1.0, 1.0, 1.0], description="Fatores de escala [sx, sy, sz]")
    pivot: list[float] = Field(default=[0.0, 0.0, 0.0], description="Ponto pivô de ancoragem da escala [px, py, pz]")


class ScaleResponse(BaseModel):
    """Resposta da operação de escala."""

    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    scale_factors: list[float]
    pivot: list[float]
    transform_matrix_16: list[float]


class ExportCamDxfRequest(BaseModel):
    """Entrada para exportação DXF para CNC / Corte a Laser."""

    parts: list[dict[str, Any]] = Field(description="Peças com contorno externo e furos em mm")
    output_filename: str = Field(default="pecas_usinagem_cnc.dxf", description="Nome do arquivo DXF")


class ExportCamDxfResponse(BaseModel):
    """Resposta com caminho e dados do arquivo DXF gerado."""

    model_config = ConfigDict(from_attributes=True)

    file_path: str
    size_bytes: int
    parts_count: int


# ============================================================================
# Frentes 41 a 45: Flythrough, Nuvem de Pontos, Manutenção NBR, Mirror e QR Tag
# ============================================================================

class CameraPathRequest(BaseModel):
    """Entrada para interpolação de sobrevoo de câmera."""

    waypoints: list[dict[str, Any]] = Field(description="Lista de câmeras [{'position': [x,y,z], 'target': [x,y,z]}]")
    frames_per_segment: int = Field(default=24, ge=6, le=120, description="Frames por segmento de interpolação")


class CameraPathResponse(BaseModel):
    """Resposta com os keyframes contínuos de câmera."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "FlythroughPath"
    waypoints_count: int
    total_frames: int
    duration_seconds: float
    camera_positions: list[list[float]]
    camera_targets: list[list[float]]


class PointCloudExportRequest(BaseModel):
    """Entrada para exportação de Nuvem de Pontos LiDAR."""

    output_filename: str = Field(default="nuvem_pontos_modelo.xyz", description="Nome do arquivo .xyz")


class PointCloudExportResponse(BaseModel):
    """Resposta com dados do arquivo de nuvem de pontos gerado."""

    model_config = ConfigDict(from_attributes=True)

    file_path: str
    size_bytes: int


class MaintenancePlanRequest(BaseModel):
    """Entrada para geração do cronograma de manutenção preventiva."""

    installation_date_iso: str = Field(default="2026-03-01", description="Data de instalação (AAAA-MM-DD)")
    environment_type: str = Field(default="urban", description="'urban', 'coastal' ou 'rural'")


class MaintenancePlanResponse(BaseModel):
    """Resposta com o plano de manutenção preventiva NBR 16071-7."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "MaintenancePlan"
    installation_date: str
    environment: str
    monitored_components_count: int
    expected_lifespan_years: float
    tasks: list[dict[str, Any]]
    next_urgent_inspection: str


class MirrorRequest(BaseModel):
    """Entrada para espelhamento e simetria 3D."""

    instance_id: str = Field(description="ID da instância a espelhar")
    plane_normal: list[float] = Field(default=[1.0, 0.0, 0.0], description="Vetor normal do plano de espelho")
    plane_point: list[float] = Field(default=[0.0, 0.0, 0.0], description="Ponto do plano de espelho")


class MirrorResponse(BaseModel):
    """Resposta da operação de espelhamento."""

    model_config = ConfigDict(from_attributes=True)

    instance_id: str
    plane_normal: list[float]
    plane_point: list[float]
    transform_matrix_16: list[float]


class QrTagExportRequest(BaseModel):
    """Entrada para emissão de placa/etiqueta técnica de patrimônio com QR Code."""

    serial_number: str = Field(default="PKL-2026-X84", description="Número de série e lote")
    product_name: str = Field(default="Playground Parkelô NBR 16071", description="Nome comercial da peça")
    output_filename: str = Field(default="etiqueta_patrimonio.svg", description="Nome do arquivo SVG")


class QrTagExportResponse(BaseModel):
    """Resposta da geração da placa técnica."""

    model_config = ConfigDict(from_attributes=True)

    file_path: str
    size_bytes: int
    serial_number: str


class SwingKinematicsRequest(BaseModel):
    """Entrada para simulação de cinemática e envelope de segurança de balanço NBR 16071."""

    chain_length_m: float = Field(default=2.20, ge=0.5, le=5.0, description="Comprimento da corrente/tirante em metros")
    user_mass_kg: float = Field(default=50.0, ge=15.0, le=120.0, description="Massa do usuário em kg")
    initial_angle_deg: float = Field(default=45.0, ge=10.0, le=75.0, description="Ângulo de lançamento em graus")
    seat_height_at_rest_m: float = Field(default=0.45, ge=0.2, le=1.0, description="Altura do assento ao solo em repouso em metros")
    damping_ratio: float = Field(default=0.05, ge=0.01, le=0.3, description="Coeficiente de amortecimento aerodinâmico/atrito")
    total_time_s: float = Field(default=4.0, ge=1.0, le=20.0, description="Tempo total de simulação em segundos")
    fps: int = Field(default=24, ge=12, le=60, description="Taxa de amostragem de frames")


class SwingKinematicsResponse(BaseModel):
    """Resposta com cinemática, tração máxima e zona de impacto do balanço."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SwingKinematicsAnalysis"
    chain_length_m: float
    suspension_height_m: float
    user_mass_kg: float
    initial_angle_deg: float
    max_tangential_speed_m_s: float
    max_chain_tension_kn: float
    seat_clearance_at_rest_m: float
    seat_clearance_compliant: bool
    required_impact_zone_length_m: float
    trajectory_points_count: int
    trajectory_points: list[dict[str, Any]]
    safety_status: str


class ArtReportRequest(BaseModel):
    """Entrada para geração de Minuta de ART / RRT em PDF."""

    professional_name: str = Field(default="Eng. Fernando Henrique", description="Nome do Responsável Técnico")
    crea_cau: str = Field(default="CREA-SP 5060708090/D", description="Registro no CREA/CAU")
    rnp: str = Field(default="2619087654", description="Registro Nacional Profissional")
    contractor: str = Field(default="Condomínio Residencial Parque das Árvores", description="Nome do Contratante")
    location: str = Field(default="Av. das Nações Unidas, 14261 - São Paulo/SP", description="Endereço da Instalação")
    project_name: str = Field(default="Playground Modular Parkelô NBR 16071", description="Nome da Obra/Equipamento")
    output_filename: str = Field(default="minuta_art_rrt.pdf", description="Nome do arquivo PDF gerado")


class ArtReportResponse(BaseModel):
    """Resposta da geração da Minuta de ART / RRT."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ArtReportPdf"
    file_path: str
    size_bytes: int
    professional_name: str
    crea_cau: str
    project_name: str
    contractor: str


class WallThicknessRequest(BaseModel):
    """Entrada para inspeção de espessura de parede em peças rotomoldadas."""

    min_thickness_mm: float = Field(default=6.0, ge=1.0, le=30.0, description="Espessura mínima admissível em mm")
    max_thickness_mm: float = Field(default=14.0, ge=3.0, le=50.0, description="Espessura máxima admissível em mm")


class WallThicknessResponse(BaseModel):
    """Resposta da inspeção de espessura de parede."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "WallThicknessInspection"
    samples_count: int
    min_thickness_mm: float
    max_thickness_mm: float
    avg_thickness_mm: float
    specified_range_mm: list[float]
    thin_wall_defects_count: int
    thick_wall_defects_count: int
    thin_wall_defects: list[dict[str, Any]]
    is_compliant: bool
    status: str


class CargoLoadRequest(BaseModel):
    """Entrada para otimização de cubagem e carregamento de carga 3D."""

    packages: list[dict[str, Any]] = Field(description="Lista de pacotes [{'name': str, 'length_m': float, 'width_m': float, 'height_m': float, 'weight_kg': float, 'quantity': int}]")
    vehicle_type: str = Field(default="caminhao_truck", description="'caminhao_toco', 'caminhao_truck' ou 'carreta_bau'")


class CargoLoadResponse(BaseModel):
    """Resposta com o plano de carregamento 3D e cubagem."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "CargoLoadPlan"
    vehicle_type: str
    vehicle_dimensions_m: list[float]
    vehicle_volume_m3: float
    vehicle_max_payload_kg: float
    packed_items_count: int
    unpacked_items_count: int
    total_cargo_weight_kg: float
    total_cargo_volume_m3: float
    volumetric_occupancy_pct: float
    weight_occupancy_pct: float
    center_of_gravity: list[float]
    packed_items: list[dict[str, Any]]
    unpacked_items: list[dict[str, Any]]
    status: str


class TechnicalSketchRequest(BaseModel):
    """Entrada para geração de esboço técnico com traço arquitetônico em SVG."""

    dihedral_angle_threshold_deg: float = Field(default=25.0, ge=5.0, le=80.0, description="Ângulo diedro para filtro de arestas vivas")
    overshoot_mm: float = Field(default=8.0, ge=0.0, le=30.0, description="Extensão das pontas das arestas (nanquim)")
    output_filename: str = Field(default="esboco_tecnico_arquitetura.svg", description="Nome do arquivo SVG gerado")


class TechnicalSketchResponse(BaseModel):
    """Resposta da geração do esboço técnico estilizado."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "TechnicalSketchSvg"
    file_path: str
    size_bytes: int
    sharp_edges_count: int
    overshoot_mm: float


class SpiralTubeRequest(BaseModel):
    """Entrada para geração de tubos e tobogãs helicoidais paramétricos."""

    radius_m: float = Field(default=1.20, ge=0.5, le=5.0, description="Raio da hélice do tobogã em metros")
    height_m: float = Field(default=2.40, ge=1.0, le=10.0, description="Altura total da descida em metros")
    turns: float = Field(default=1.25, ge=0.5, le=4.0, description="Número de voltas da espiral")
    tube_radius_m: float = Field(default=0.38, ge=0.2, le=1.0, description="Raio da seção circular do tubo em metros")
    segments_per_turn: int = Field(default=16, ge=8, le=32, description="Resolução axial da espiral")
    tube_segments: int = Field(default=8, ge=6, le=24, description="Resolução radial da seção circular")
    is_open_gutter: bool = False


class SpiralTubeResponse(BaseModel):
    """Resposta com a geometria e métricas de escorregamento do tobogã espiral."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SpiralTubeGeometry"
    radius_m: float
    height_m: float
    turns: float
    tube_radius_m: float
    is_open_gutter: bool
    path_length_m: float
    average_slope_deg: float
    estimated_exit_speed_m_s: float
    vertices_count: int
    faces_count: int
    vertices: list[list[float]]
    faces: list[list[int]]
    status: str


class OverturnStabilityRequest(BaseModel):
    """Entrada para verificação de estabilidade e tombamento por vento/multidão."""

    total_mass_kg: float = Field(default=850.0, ge=50.0, le=50000.0, description="Massa total da estrutura montada em kg")
    cg_position: list[float] = Field(default=[1.50, 1.20, 1.45], description="Coordenadas [X, Y, Z] do Centro de Gravidade em metros")
    base_support_points: list[list[float]] | None = None
    wind_speed_km_h: float = Field(default=100.0, ge=30.0, le=200.0, description="Velocidade básica do vento NBR 6123 em km/h")
    exposed_frontal_area_m2: float = Field(default=6.50, ge=0.5, le=100.0, description="Área frontal exposta ao vento em m²")
    lateral_live_load_n: float = Field(default=500.0, ge=0.0, le=5000.0, description="Empuxo lateral de multidão no topo em N")
    live_load_height_m: float = Field(default=1.80, ge=0.5, le=5.0, description="Altura de aplicação do empuxo de multidão em metros")


class OverturnStabilityResponse(BaseModel):
    """Resposta do cálculo de tombamento e lastro de sapata."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "OverturnStabilityAnalysis"
    total_mass_kg: float
    center_of_gravity: list[float]
    restoring_arm_m: float
    restoring_moment_kn_m: float
    wind_speed_km_h: float
    wind_pressure_pa: float
    wind_force_kn: float
    overturning_moment_kn_m: float
    safety_factor: float
    required_safety_factor: float
    is_stable: bool
    extra_ballast_kg: float
    extra_concrete_volume_m3: float
    status: str


class FieldInspectionRequest(BaseModel):
    """Entrada para emissão de ficha de inspeção de campo NBR 16071-7."""

    park_name: str = Field(default="Parque Ibirapuera - Área Infantil", description="Nome do parque ou condomínio")
    inspector_name: str = Field(default="Eng. Fernando Henrique", description="Nome do auditor/engenheiro")
    inspection_date: str = Field(default="2026-03-01", description="Data da vistoria")
    output_filename: str = Field(default="ficha_inspecao_nbr16071.html", description="Nome do arquivo HTML")


class FieldInspectionResponse(BaseModel):
    """Resposta com dados da ficha de inspeção de campo gerada."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "FieldInspectionHtml"
    file_path: str
    size_bytes: int
    park_name: str
    inspector_name: str
    inspection_date: str
    items_count: int


class AngleDimensionRequest(BaseModel):
    """Entrada para cálculo e cotagem angular 3D."""

    vertex_point: list[float] = Field(description="Vértice central do ângulo [X, Y, Z]")
    point_a: list[float] = Field(description="Ponto do eixo A [X, Y, Z]")
    point_b: list[float] = Field(description="Ponto do eixo B [X, Y, Z]")
    arc_radius_m: float = Field(default=0.60, ge=0.1, le=5.0, description="Raio do arco de cota gráfica em metros")


class AngleDimensionResponse(BaseModel):
    """Resposta com valor do ângulo, arco gráfico e ponto de texto."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "AngleDimension"
    vertex_point: list[float]
    point_a: list[float]
    point_b: list[float]
    angle_degrees: float
    angle_radians: float
    angle_gms: str
    arc_radius_m: float
    plane_normal: list[float]
    label_position: list[float]
    text_label: str
    arc_points_count: int
    arc_points: list[list[float]]


class FastenerTorqueRequest(BaseModel):
    """Entrada para dimensionamento de fixador e cálculo de torque normativo."""

    timber_thickness_mm: float = Field(default=160.0, ge=20.0, le=600.0, description="Espessura da peça de madeira em mm")
    steel_plate_thickness_mm: float = Field(default=4.75, ge=0.0, le=50.0, description="Espessura da chapa de aço em mm")
    bolt_standard: str = Field(default="1/2_POL", description="'M10', 'M12', 'M16', '1/2_POL' ou '5/8_POL'")
    material_grade: str = Field(default="Inox_304", description="Grau do material ('Inox_304', 'A307_Zincado', 'Grau_5')")
    friction_factor_k: float = Field(default=0.18, ge=0.10, le=0.30, description="Fator de atrito da rosca")


class FastenerTorqueResponse(BaseModel):
    """Resposta com especificação do fixador e torque de aperto."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "FastenerTorqueSpecification"
    bolt_standard: str
    material_grade: str
    nominal_diameter_mm: float
    grip_length_mm: float
    min_required_bolt_length_mm: float
    commercial_bolt_length_mm: float
    recommended_washer: str
    recommended_nut: str
    socket_tool_size_mm: int
    max_wood_crushing_force_kn: float
    pretension_force_kn: float
    recommended_torque_n_m: float
    recommended_torque_kgf_m: float
    safe_clamping_status: str


class HipRoofRequest(BaseModel):
    """Entrada para geração de telhado de quatro águas ou piramidal."""

    base_width_m: float = Field(default=2.40, ge=0.5, le=20.0, description="Largura da base da torre em metros")
    base_length_m: float = Field(default=3.20, ge=0.5, le=30.0, description="Comprimento da base da torre em metros")
    base_height_m: float = Field(default=2.80, ge=0.5, le=10.0, description="Altura do beiral ao solo em metros")
    pitch_deg: float = Field(default=30.0, ge=10.0, le=60.0, description="Inclinação das águas do telhado em graus")
    overhang_m: float = Field(default=0.35, ge=0.0, le=1.5, description="Projeção do beiral em metros")


class HipRoofResponse(BaseModel):
    """Resposta com geometria e quantitativo do telhado de quatro águas."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "HipRoofGeometry"
    base_width_m: float
    base_length_m: float
    base_height_m: float
    pitch_deg: float
    overhang_m: float
    apex_height_m: float
    ridge_length_m: float
    sloped_roof_area_m2: float
    hip_rafter_length_m: float
    vertices_count: int
    faces_count: int
    vertices: list[list[float]]
    faces: list[list[int]]
    roof_type: str


class HicRequest(BaseModel):
    """Entrada para simulação de impacto HIC e piso amortecedor NBR 16071-3."""

    fall_height_m: float = Field(default=1.80, ge=0.3, le=5.0, description="Altura de queda livre em metros")
    surface_type: str = Field(default="areia_lavada", description="'areia_lavada', 'casca_madeira', 'borracha_epdm' ou 'grama_natural'")
    installed_thickness_mm: float = Field(default=300.0, ge=0.0, le=600.0, description="Espessura instalada do piso amortecedor em mm")


class HicResponse(BaseModel):
    """Resposta da simulação de desaceleração de impacto HIC."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "HicImpactAnalysis"
    surface_name: str
    surface_type: str
    fall_height_m: float
    installed_thickness_mm: float
    recommended_thickness_mm: float
    impact_velocity_m_s: float
    impact_duration_ms: float
    peak_deceleration_g: float
    hic_score: float
    critical_fall_height_m: float
    hic_limit: float
    peak_g_limit: float
    is_compliant: bool
    curve_points_count: int
    curve_points: list[dict[str, Any]]
    safety_verdict: str


class ZebraLabelRequest(BaseModel):
    """Entrada para emissão de etiqueta térmica Zebra ZPL II industrial."""

    part_name: str = Field(default="Pilar Eucalipto Citriodora", description="Nome da peça usinada")
    part_sku: str = Field(default="PKL-EUC-16-220", description="SKU / Código de rastreio da peça")
    dimensions_mm: str = Field(default="D160 x L2200 mm", description="Dimensões métricas em milímetros")
    lot_batch: str = Field(default="LOTE-2026-X84", description="Número do lote de autoclave")
    output_zpl_filename: str = Field(default="etiqueta_zebra.zpl", description="Nome do arquivo ZPL")
    output_svg_filename: str = Field(default="etiqueta_zebra.svg", description="Nome do arquivo SVG de preview")


class ZebraLabelResponse(BaseModel):
    """Resposta da emissão da etiqueta industrial Zebra."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ZebraThermalLabel"
    zpl_file_path: str
    svg_file_path: str
    zpl_size_bytes: int
    part_sku: str
    part_name: str
    label_dimensions: str


class ExplodedTrailsRequest(BaseModel):
    """Entrada para cálculo de linhas de trajetória de vista explodida."""

    parts: list[dict[str, Any]] = Field(description="Lista de peças [{'id': str, 'name': str, 'original_pos': [x,y,z], 'exploded_pos': [x,y,z]}]")
    dash_size_m: float = Field(default=0.05, ge=0.01, le=0.5, description="Comprimento do traço da linha em metros")
    gap_size_m: float = Field(default=0.03, ge=0.01, le=0.5, description="Espaçamento do traço em metros")


class ExplodedTrailsResponse(BaseModel):
    """Resposta com as linhas de chamada tracejadas de montagem."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ExplodedViewTrails"
    parts_with_trails_count: int
    total_trail_length_m: float
    dash_size_m: float
    gap_size_m: float
    trails: list[dict[str, Any]]


class CarbonFootprintRequest(BaseModel):
    """Entrada para cálculo de balanço de carbono e sustentabilidade."""

    timber_volume_m3: float = Field(default=2.80, ge=0.1, le=50.0, description="Volume total de madeira tratada em m³")
    steel_weight_kg: float = Field(default=95.0, ge=0.0, le=5000.0, description="Peso de ferragens de aço em kg")
    plastic_weight_kg: float = Field(default=45.0, ge=0.0, le=2000.0, description="Peso de peças plásticas PEAD em kg")
    transport_distance_km: float = Field(default=350.0, ge=0.0, le=5000.0, description="Distância de frete da fábrica ao local em km")


class CarbonFootprintResponse(BaseModel):
    """Resposta com o inventário e selo de carbono da estrutura."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "CarbonFootprintAnalysis"
    timber_volume_m3: float
    co2_sequestered_kg: float
    steel_weight_kg: float
    co2_steel_emissions_kg: float
    plastic_weight_kg: float
    co2_plastic_emissions_kg: float
    transport_distance_km: float
    co2_transport_emissions_kg: float
    total_emissions_kg: float
    net_carbon_balance_kg: float
    is_carbon_negative: bool
    equivalent_trees_planted_years: float
    sustainability_badge: str
    status: str


class AttributeDictionaryRequest(BaseModel):
    """Entrada para manipulação de Dicionários de Atributos e Componentes Dinâmicos."""

    dict_name: str = Field(default="dynamic_attributes", description="Nome do dicionário (ex: dynamic_attributes)")
    key: str = Field(default="_lenx_formula", description="Chave do atributo")
    value: Any = Field(default="=100 * 2", description="Valor ou fórmula paramétrica")
    evaluate_formula: bool = False
    context_vars: dict[str, float] = Field(default_factory=dict, description="Variáveis para avaliação de fórmula")


class AttributeDictionaryResponse(BaseModel):
    """Resposta com dados do atributo e valor avaliado."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "AttributeDictionaryResult"
    dict_name: str
    key: str
    value: Any
    evaluated_result: float | None = None
    status: str


class TagFolderRequest(BaseModel):
    """Entrada para criação e organização de Pastas de Tags."""

    folder_id: str = Field(description="Identificador único da pasta")
    name: str = Field(description="Nome de exibição da pasta de tags")
    parent_id: str | None = Field(default=None, description="ID da pasta pai para aninhamento")
    visible: bool = True
    tags_to_add: list[str] = Field(default_factory=list, description="Lista de tags a mover para esta pasta")


class TagFolderResponse(BaseModel):
    """Resposta com a árvore hierárquica de pastas e visibilidade em cascata."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "TagFolderHierarchy"
    folder_id: str
    name: str
    parent_id: str | None
    visible: bool
    tags_count: int
    tags: list[str]
    tree_summary: dict[str, Any]


class EdgeStylesRequest(BaseModel):
    """Entrada para configuração das opções de renderização de arestas nativas."""

    profiles_enabled: bool = True
    profile_width: int = Field(default=2, ge=1, le=8, description="Espessura das arestas de silhueta (1-8px)")
    depth_cue_enabled: bool = False
    extensions_enabled: bool = False
    extension_length_px: int = Field(default=4, ge=1, le=20)
    endpoints_enabled: bool = False
    endpoint_size_px: int = Field(default=5, ge=1, le=15)
    jitter_enabled: bool = False
    back_edges_enabled: bool = False  # Atalho K


class EdgeStylesResponse(BaseModel):
    """Resposta com as configurações ativas de estilo de arestas."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "EdgeStylesConfiguration"
    settings: dict[str, Any]
    back_edges_shortcut_active: bool
    status: str


class TwoPointPerspectiveRequest(BaseModel):
    """Entrada para enquadramento em Perspectiva de Dois Pontos (sem convergência vertical)."""

    eye: list[float] = Field(description="Posição da câmera [X, Y, Z]")
    target: list[float] = Field(description="Ponto focal observado [X, Y, Z]")
    fov_deg: float = Field(default=35.0, ge=5.0, le=90.0, description="Campo de visão em graus")
    aspect_ratio: float = Field(default=16.0 / 9.0, ge=0.5, le=3.0)


class TwoPointPerspectiveResponse(BaseModel):
    """Resposta com matriz de projeção oblíqua e alvo horizontalizado."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "TwoPointPerspectiveCamera"
    camera_type: str
    original_eye: list[float]
    original_target: list[float]
    corrected_target: list[float]
    original_pitch_deg: float
    lens_shift_y: float
    fov_deg: float
    vertical_lines_parallel: bool
    projection_matrix_16: list[float]


class TextureProjectionRequest(BaseModel):
    """Entrada para projeção analítica de coordenadas UV."""

    vertices: list[list[float]] = Field(description="Lista de vértices 3D [[x,y,z], ...]")
    projection_type: str = Field(default="planar", description="'planar' ou 'cylindrical'")
    plane_normal: list[float] = Field(default=[0.0, 0.0, 1.0], description="Normal do plano projetado")
    scale_u_m: float = Field(default=1.0, ge=0.01, le=50.0, description="Escala horizontal da textura em metros")
    scale_v_m: float = Field(default=1.0, ge=0.01, le=50.0, description="Escala vertical da textura em metros")
    rotation_deg: float = Field(default=0.0, ge=-360.0, le=360.0, description="Rotação angular do mapeamento UV")


class TextureProjectionResponse(BaseModel):
    """Resposta com o buffer de coordenadas UV calculadas."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "TextureProjectionResult"
    projection_type: str
    vertices_count: int
    uv_coordinates: list[list[float]]
    status: str


# ==============================================================================
# FRENTES 66 A 70 - ENGENHARIA REVERSA PURA DO SKETCHUP (CURVAS, CORTES, ESTILOS, CENAS E SOMBRAS)
# ==============================================================================

class CurveWeldRequest(BaseModel):
    """Entrada para soldagem de arestas consecutivas em polilinha/curva SUCurveRef."""

    edges: list[list[list[float]]] = Field(description="Lista de arestas [[[x0,y0,z0], [x1,y1,z1]], ...]")
    tolerance: float = Field(default=0.0001, ge=1e-6, le=0.01)


class CurveArcCreateRequest(BaseModel):
    """Entrada para criação de arco analítico SUArcCurveRef."""

    center: list[float] = Field(default=[0.0, 0.0, 0.0], description="Centro [x, y, z]")
    radius: float = Field(default=1.0, ge=0.001, description="Raio do arco")
    normal: list[float] = Field(default=[0.0, 0.0, 1.0], description="Normal unitária")
    start_angle_rad: float = Field(default=0.0, description="Ângulo inicial em radianos")
    end_angle_rad: float = Field(default=6.283185, description="Ângulo final em radianos")
    num_segments: int = Field(default=24, ge=3, le=360, description="Segmentação do arco")


class CurveResponse(BaseModel):
    """Resposta com curvas soldadas ou metadados de arco analítico."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUCurveEntity"
    curve_data: dict[str, Any]
    status: str


class SectionPlaneCreateRequest(BaseModel):
    """Entrada para criação/inversão de plano de corte SUSectionPlaneRef."""

    name: str = Field(default="Corte Transversal", description="Nome do corte")
    symbol: str = Field(default="A", max_length=5, description="Símbolo ou letra indicativa")
    normal: list[float] = Field(default=[0.0, 0.0, -1.0], description="Normal do plano (A, B, C)")
    distance: float = Field(default=1.0, description="Distância D do plano")
    is_active: bool = Field(default=True, description="Se o corte está ativo")


class SectionPlaneSliceRequest(BaseModel):
    """Entrada para fatiamento de geometria 3D por plano de corte."""

    vertices: list[list[float]] = Field(description="Vértices da malha [[x,y,z], ...]")
    faces: list[list[int]] = Field(description="Polígonos/triângulos indexados")
    plane_equation: list[float] = Field(description="Equação do plano [A, B, C, D]")


class SUSectionPlaneResponse(BaseModel):
    """Resposta de operações com planos de corte analíticos (Frente 67)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUSectionPlane"
    plane_data: dict[str, Any]
    status: str


class FaceStyleResolveRequest(BaseModel):
    """Entrada para resolução de propriedades visuais por estilo de face."""

    mode: str = Field(default="SHADED_WITH_TEXTURES", description="Modo: WIRE_FRAME, HIDDEN_LINE, SHADED, SHADED_WITH_TEXTURES, MONOCHROME, XRAY")
    material_color: str | None = Field(default=None, description="Cor hexadecimal #RRGGBB")
    texture_path: str | None = Field(default=None, description="URL ou path de textura difusa")
    opacity: float = Field(default=1.0, ge=0.0, le=1.0)
    is_back_face: bool = Field(default=False, description="True se for a face posterior (verso)")


class GlassMaterialRequest(BaseModel):
    """Entrada para geração de material translúcido estilo vidro arquitetônico."""

    name: str = Field(default="Vidro Arquitetônico Transparente")
    color: str = Field(default="#dff9fb")
    opacity: float = Field(default=0.3, ge=0.05, le=0.95)
    refraction_index: float = Field(default=1.52, ge=1.0, le=2.5)


class FaceStyleResponse(BaseModel):
    """Resposta com shaders e propriedades PBR de renderização."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "FaceStyleShader"
    render_properties: dict[str, Any]
    status: str


class SceneCreateRequest(BaseModel):
    """Entrada para criação de cena/página de apresentação SUSceneRef."""

    name: str = Field(description="Nome da cena")
    eye: list[float] = Field(description="Posição da câmera [x, y, z]")
    target: list[float] = Field(description="Ponto focal observado [x, y, z]")
    up: list[float] = Field(default=[0.0, 1.0, 0.0])
    fov: float = Field(default=35.0, ge=5.0, le=90.0)
    is_orthographic: bool = Field(default=False)
    transition_time: float = Field(default=1.5, ge=0.0, le=30.0)
    delay_time: float = Field(default=1.0, ge=0.0, le=30.0)
    include_in_animation: bool = Field(default=True)


class SceneAnimationTimelineRequest(BaseModel):
    """Entrada para interpolação contínua de timeline entre cenas."""

    scenes: list[dict[str, Any]] = Field(description="Lista de cenas SUSceneRef")
    fps: int = Field(default=30, ge=10, le=60)
    loop: bool = Field(default=True)


class SceneAnimationResponse(BaseModel):
    """Resposta com keyframes e timeline interpolada de animação de câmera."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ScenesAnimationTimeline"
    timeline: dict[str, Any]
    status: str


class ShadowInfoRequest(BaseModel):
    """Entrada para cálculo astronômico de vetor solar SUShadowInfoRef."""

    year: int = Field(default=2026, ge=1900, le=2100)
    month: int = Field(default=3, ge=1, le=12)
    day: int = Field(default=21, ge=1, le=31)
    hour: int = Field(default=14, ge=0, le=23)
    minute: int = Field(default=0, ge=0, le=59)
    latitude: float = Field(default=-23.5505, ge=-90.0, le=90.0)
    longitude: float = Field(default=-46.6333, ge=-180.0, le=180.0)
    tz_offset: float = Field(default=-3.0, ge=-12.0, le=14.0)
    north_angle: float = Field(default=0.0, ge=-360.0, le=360.0)
    light_intensity: int = Field(default=80, ge=0, le=100)
    dark_intensity: int = Field(default=45, ge=0, le=100)
    display_shadows: bool = Field(default=True)
    use_sun_for_shading: bool = Field(default=True)
    edges_cast_shadows: bool = Field(default=False)


class ShadowInfoResponse(BaseModel):
    """Resposta com vetor solar e iluminação para Three.js."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUShadowInfo"
    shadow_info: dict[str, Any]
    status: str


# ==============================================================================
# FRENTES 71 A 75 - ENGENHARIA REVERSA PURA DO SKETCHUP (TEXTOS, COTAS, GUIAS, ALFA E HIERARQUIA)
# ==============================================================================

class ScreenTextRequest(BaseModel):
    """Entrada para criação de texto 2D fixado na tela (HUD) SUTextRef."""

    text: str = Field(description="Conteúdo do texto")
    screen_x: float = Field(default=20.0, description="Posição horizontal em pixels")
    screen_y: float = Field(default=20.0, description="Posição vertical em pixels")
    font_name: str = Field(default="Arial")
    font_size_pt: int = Field(default=12, ge=6, le=72)
    color_hex: str = Field(default="#000000")
    bold: bool = Field(default=False)
    italic: bool = Field(default=False)


class LeaderTextRequest(BaseModel):
    """Entrada para criação de texto anotativo com linha de chamada (líder) SUTextRef."""

    text: str = Field(description="Conteúdo da anotação")
    anchor_point: list[float] = Field(description="Ponto 3D ancorado no modelo [x, y, z]")
    offset_vector: list[float] = Field(default=[0.5, 0.5, 0.5], description="Vetor 3D de deslocamento do rótulo")
    arrow_type: str = Field(default="ARROW", description="ARROW, DOT, NONE, SLASH")
    font_name: str = Field(default="Arial")
    font_size_pt: int = Field(default=10, ge=6, le=72)
    color_hex: str = Field(default="#000000")


class TextResponse(BaseModel):
    """Resposta com dados de texto 2D ou rótulo de líder SUTextRef."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUTextRef"
    text_data: dict[str, Any]
    status: str


class DimensionLinearRequest(BaseModel):
    """Entrada para cálculo de cota linear SUDimensionLinearRef."""

    start_pt: list[float] = Field(description="Ponto inicial 3D cotado [x, y, z]")
    end_pt: list[float] = Field(description="Ponto final 3D cotado [x, y, z]")
    offset_distance: float = Field(default=0.2, description="Afastamento perpendicular da linha de cota em metros")
    plane_normal: list[float] | None = Field(default=None, description="Normal do plano de apoio")
    arrow_type: str = Field(default="SLASH", description="SLASH (tique 45°), ARROW, DOT")
    unit: str = Field(default="m", description="m, cm, mm, in")
    precision: int = Field(default=2, ge=0, le=4)
    custom_text: str | None = Field(default=None, description="Texto customizado para sobrepor a distância medida")


class DimensionLinearResponse(BaseModel):
    """Resposta com dados gráficos da cota SUDimensionLinearRef."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUDimensionLinearRef"
    dimension_data: dict[str, Any]
    status: str


class GuideLineInfiniteRequest(BaseModel):
    """Entrada para linha de guia infinita ou finita SUGuideLineRef."""

    point: list[float] = Field(description="Ponto de passagem da guia [x, y, z]")
    direction: list[float] | None = Field(default=None, description="Vetor diretor unitário [dx, dy, dz]")
    end_point: list[float] | None = Field(default=None, description="Ponto final se guia for finita")
    is_infinite: bool = Field(default=True, description="Se a guia se estende ao infinito")
    extent_m: float = Field(default=500.0, ge=1.0, le=10000.0)


class GuidePointCreateRequest(BaseModel):
    """Entrada para ponto de construção auxiliar SUGuidePointRef."""

    point: list[float] = Field(description="Coordenadas 3D do ponto [x, y, z]")


class GuideLineIntersectRequest(BaseModel):
    """Entrada para cálculo de interseção analítica entre duas linhas de guia."""

    line1: dict[str, Any] = Field(description="Dados da primeira linha SUGuideLineRef")
    line2: dict[str, Any] = Field(description="Dados da segunda linha SUGuideLineRef")
    tolerance: float = Field(default=0.001, ge=1e-6, le=0.1)


class InfiniteGuideResponse(BaseModel):
    """Resposta de operações com linhas e pontos de guia."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUGuideEntity"
    guide_data: dict[str, Any]
    status: str


class AlphaMaterialRequest(BaseModel):
    """Entrada para configuração de material com transparência alfa (PNG cutout)."""

    name: str = Field(description="Nome do material")
    texture_path: str = Field(description="Caminho ou URL do arquivo PNG com canal alfa")
    alpha_mode: str = Field(default="MASK", description="'MASK' para alphaTest ou 'BLEND' para transparência suave")
    alpha_threshold: float = Field(default=0.5, ge=0.01, le=0.99)
    double_sided: bool = Field(default=True)


class FaceMeRequest(BaseModel):
    """Entrada para cálculo de matriz billboard de rotação Face-Me."""

    instance_position: list[float] = Field(description="Posição 3D da instância [x, y, z]")
    camera_position: list[float] = Field(description="Posição 3D da câmera [x, y, z]")
    axial_only: bool = Field(default=True, description="True para girar apenas em torno de Z")


class AlphaTextureResponse(BaseModel):
    """Resposta com shader alfa ou matriz de rotação Face-Me."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "AlphaTextureResult"
    result_data: dict[str, Any]
    status: str


class NestedHierarchyResolveRequest(BaseModel):
    """Entrada para resolução de nó aninhado a partir de caminho hierárquico."""

    node_id: str = Field(description="ID do nó folha a inspecionar")
    path_to_node: list[dict[str, Any]] = Field(description="Lista de nós com matrizes locais da raiz até o nó")


class WorldToLocalRequest(BaseModel):
    """Entrada para converter transformação desejada no espaço mundial em matriz local."""

    desired_world_matrix: list[float] = Field(description="Matriz 4x4 column-major desejada no mundo")
    parent_world_matrix: list[float] = Field(description="Matriz 4x4 column-major acumulada dos pais")


class NestedHierarchyResponse(BaseModel):
    """Resposta com matrizes mundiais acumuladas e decomposição afim."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "NestedHierarchyResult"
    hierarchy_data: dict[str, Any]
    status: str


# ==============================================================================
# FRENTES 76 A 80 - ENGENHARIA REVERSA PURA DO SKETCHUP (COTAS RADIAIS, NÉVOA, SMOOTHING, HACHURAS E GEO)
# ==============================================================================

class DimensionRadialRequest(BaseModel):
    """Entrada para cálculo de cota radial ou diamétrica SUDimensionRadialRef."""

    center: list[float] = Field(description="Centro do arco/círculo [x, y, z]")
    radius: float = Field(gt=0.0, description="Raio do arco/círculo em metros")
    normal: list[float] = Field(default=[0.0, 0.0, 1.0], description="Normal do plano do círculo")
    angle_deg: float = Field(default=45.0, description="Ângulo de contato na borda em graus")
    is_diameter: bool = Field(default=False, description="True para cota diamétrica (Ø), False para radial (R)")
    leader_length: float = Field(default=0.3, ge=0.05, le=5.0)
    unit: str = Field(default="m", description="m, cm, mm, in")
    precision: int = Field(default=2, ge=0, le=4)


class DimensionRadialResponse(BaseModel):
    """Resposta com dados gráficos da cota radial/diamétrica SUDimensionRadialRef."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUDimensionRadialRef"
    radial_data: dict[str, Any]
    status: str


class FogStyleRequest(BaseModel):
    """Entrada para configuração de névoa atmosférica de cena SUStyleFog."""

    enabled: bool = Field(default=True)
    start_dist_m: float = Field(default=10.0, ge=0.0)
    end_dist_m: float = Field(default=100.0, ge=0.1)
    color_hex: str = Field(default="#dcdde1")


class AutoFogRequest(BaseModel):
    """Entrada para cálculo automático de névoa baseado na Bounding Box."""

    min_point: list[float] = Field(description="Canto inferior da BBox [min_x, min_y, min_z]")
    max_point: list[float] = Field(description="Canto superior da BBox [max_x, max_y, max_z]")
    color_hex: str = Field(default="#dcdde1")


class FogStyleResponse(BaseModel):
    """Resposta com parâmetros de névoa configurados."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUStyleFog"
    fog_data: dict[str, Any]
    status: str


class MeshSmoothingRequest(BaseModel):
    """Entrada para algoritmo de suavização de arestas Soft & Smooth do SketchUp."""

    vertices: list[list[float]] = Field(description="Vértices da malha [[x,y,z], ...]")
    faces: list[list[int]] = Field(description="Faces indexadas")
    angle_threshold_deg: float = Field(default=35.0, ge=0.0, le=90.0, description="Ângulo limite diedro em graus")


class MeshSmoothingResponse(BaseModel):
    """Resposta com classificação de arestas e normais de vértices ponderadas."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "MeshSmoothingResult"
    smoothing_data: dict[str, Any]
    status: str


class SectionHatchRequest(BaseModel):
    """Entrada para geração de hachuras gráficas normativas NBR 6492 / ISO 128."""

    closed_loop_3d: list[list[float]] = Field(description="Loop de contorno seccionado [[x,y,z], ...]")
    pattern: str = Field(default="WOOD", description="WOOD, CONCRETE, STEEL, SOLID")
    spacing_m: float = Field(default=0.05, ge=0.005, le=1.0)
    angle_deg: float = Field(default=45.0, ge=-180.0, le=180.0)


class SectionHatchResponse(BaseModel):
    """Resposta com segmentos de reta 3D das linhas de hachura."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SectionHatchResult"
    hatch_data: dict[str, Any]
    status: str


class GeoReferenceRequest(BaseModel):
    """Entrada para georreferenciamento do modelo SUGeoReferenceRef."""

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    altitude_m: float = Field(default=0.0)
    north_angle_deg: float = Field(default=0.0, ge=-360.0, le=360.0)
    city: str = Field(default="São Paulo")
    country: str = Field(default="Brasil")


class LocalToGeoRequest(BaseModel):
    """Entrada para conversão de ponto 3D local em coordenadas WGS84."""

    local_xyz_m: list[float] = Field(description="Ponto 3D local [x, y, z] em metros")
    origin_lat: float = Field(ge=-90.0, le=90.0)
    origin_lon: float = Field(ge=-180.0, le=180.0)
    origin_alt_m: float = Field(default=0.0)
    north_angle_deg: float = Field(default=0.0)


class GeoReferenceResponse(BaseModel):
    """Resposta de dados georreferenciados e conversões geodésicas."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUGeoReferenceRef"
    geo_data: dict[str, Any]
    status: str


# ==============================================================================
# FRENTES 81 A 85 - ENGENHARIA REVERSA PURA DO SKETCHUP (POLY MESH, ALIGN VIEW, SKY/GROUND, TOLERÂNCIAS E UNDO/REDO)
# ==============================================================================

class PolyMeshHolesRequest(BaseModel):
    """Entrada para triangulação de face com furos SUPolyMeshRef."""

    outer_loop_3d: list[list[float]] = Field(description="Loop externo [[x,y,z], ...]")
    inner_loops_3d: list[list[list[float]]] | None = Field(default=None, description="Lista de loops internos (furos)")


class PolyMeshResponse(BaseModel):
    """Resposta com malha triangulada e normais SUPolyMeshRef."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUPolyMeshRef"
    mesh_data: dict[str, Any]
    status: str


class AlignViewRequest(BaseModel):
    """Entrada para alinhamento de câmera à face selecionada (Align View)."""

    face_vertices: list[list[float]] = Field(description="Vértices da face plana [[x,y,z], ...]")
    fov_deg: float = Field(default=35.0, ge=5.0, le=90.0)
    margin_factor: float = Field(default=1.25, ge=1.0, le=3.0)


class AlignViewResponse(BaseModel):
    """Resposta com posição e orientação de câmera alinhada à face."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "AlignViewCamera"
    camera_data: dict[str, Any]
    status: str


class BackgroundSkyStyleRequest(BaseModel):
    """Entrada para configuração de estilos de céu, solo e horizonte SUStyleRef."""

    sky_enabled: bool = Field(default=True)
    ground_enabled: bool = Field(default=True)
    sky_color: str = Field(default="#b4d5fe")
    ground_color: str = Field(default="#c2b8a3")
    horizon_color: str = Field(default="#95afc0")
    background_color: str = Field(default="#ffffff")
    ground_transparency_percent: int = Field(default=50, ge=0, le=100)
    show_horizon: bool = Field(default=True)


class BackgroundSkyStyleResponse(BaseModel):
    """Resposta com parâmetros de estilo de fundo WebGL."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SUStyleBackgroundSky"
    style_data: dict[str, Any]
    status: str


class DimensionToleranceRequest(BaseModel):
    """Entrada para cálculo e formatação de tolerâncias dimensionais ISO 2768 / NBR 6492."""

    nominal_val: float = Field(description="Valor nominal da dimensão")
    unit: str = Field(default="mm", description="mm, cm, m, in")
    tolerance_type: str = Field(default="BILATERAL", description="BILATERAL, LIMITS, DEVIATION, ISO_CLASS")
    upper_tol: float = Field(default=0.1, ge=0.0)
    lower_tol: float = Field(default=0.1, ge=0.0)
    iso_class: str = Field(default="m", description="f (fina), m (média), c (grossa), v (muito grossa)")
    precision: int = Field(default=2, ge=0, le=4)


class DimensionToleranceResponse(BaseModel):
    """Resposta com limites dimensionais e texto técnico formatado."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "DimensionTolerance"
    tolerance_data: dict[str, Any]
    status: str


class UndoRedoRecordRequest(BaseModel):
    """Entrada para registro de operação atômica na pilha transacional."""

    name: str = Field(description="Nome da operação (ex: 'Mover Viga')")
    action_type: str = Field(description="Tipo de ação (TRANSFORM, ADD, DELETE, PAINT)")
    target_id: str = Field(description="ID da entidade afetada")
    before_state: dict[str, Any] = Field(description="Estado anterior antes da modificação")
    after_state: dict[str, Any] = Field(description="Novo estado após a modificação")


class UndoRedoActionResponse(BaseModel):
    """Resposta ao executar desfazer (undo) ou refazer (redo)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "UndoRedoAction"
    action: str
    operation: dict[str, Any] | None = None
    restore_state: dict[str, Any] | None = None
    can_undo: bool
    can_redo: bool
    next_undo_name: str | None = None
    next_redo_name: str | None = None
    status: str


class UndoRedoStatusResponse(BaseModel):
    """Resposta com o estado atual da pilha de histórico."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "UndoRedoStatus"
    can_undo: bool
    can_redo: bool
    undo_name: str | None = None
    redo_name: str | None = None
    undo_count: int
    redo_count: int
    recent_operations: list[str] = Field(default_factory=list)


class SubDSubdivisionRequest(BaseModel):
    """Entrada para subdivisão de superfície Catmull-Clark / QuadMesh (Frente 86)."""

    vertices: list[list[float]] = Field(description="Vértices da malha de controle [[x, y, z], ...]")
    faces: list[list[int]] = Field(description="Faces de controle poligonais (quads/tris) [[idx, ...], ...]")
    iterations: int = Field(default=1, ge=1, le=3, description="Níveis de subdivisão Catmull-Clark")


class SubDMeshResponse(BaseModel):
    """Resposta da malha orgânica suavizada por Catmull-Clark (Frente 86)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SubDMeshResult"
    iterations: int
    original_vertices_count: int
    original_faces_count: int
    subdivided_vertices_count: int
    subdivided_quad_faces_count: int
    triangles_count: int
    vertices: list[list[float]]
    quad_faces: list[list[int]]
    triangles: list[list[int]]
    status: str


class SectionDimensionRequest(BaseModel):
    """Entrada para geração automática de cotas e níveis em corte de seção (Frente 87)."""

    cut_loops_3d: list[list[list[float]]] = Field(description="Loops fechados 3D gerados pelo corte de seção")
    offset_m: float = Field(default=0.25, ge=0.05, le=5.0, description="Distância de afastamento das linhas de cota")
    unit: str = Field(default="m", description="m, cm, mm, in")
    precision: int = Field(default=2, ge=0, le=4)


class SectionDimensionResponse(BaseModel):
    """Resposta com cotas lineares e marcas de nível NBR 6492 (Frente 87)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SectionDimensionResult"
    dimensions_count: int
    dimensions: list[dict[str, Any]]
    level_marks: list[dict[str, Any]]
    bbox_min: list[float]
    bbox_max: list[float]
    span_horizontal_m: float
    span_vertical_m: float
    status: str


class PanoramaSphericalRequest(BaseModel):
    """Entrada para cálculo de panorama esférico 360° e cubemap (Frente 88)."""

    eye_position: list[float] = Field(description="Posição do observador [x, y, z] em metros")
    horizontal_samples: int = Field(default=16, ge=4, le=64)
    vertical_samples: int = Field(default=8, ge=2, le=32)
    sphere_radius_m: float = Field(default=10.0, ge=1.0, le=100.0)


class PanoramaSphericalResponse(BaseModel):
    """Resposta com cubemap de 6 câmeras e malha de raios equirretangulares (Frente 88)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str
    cubemap: dict[str, Any]
    grid: dict[str, Any]
    status: str


class ClashDetectionRequest(BaseModel):
    """Entrada para auditoria de colisões e interferências entre componentes (Frente 89)."""

    components: list[dict[str, Any]] = Field(description="Lista de componentes [{'id': str, 'name': str, 'bbox_min': [x,y,z], 'bbox_max': [x,y,z]}]")
    clearance_tolerance_m: float = Field(default=0.01, ge=0.0, le=1.0, description="Tolerância de proximidade em metros")


class ClashDetectionResponse(BaseModel):
    """Resposta com relatório de interferências críticas e avisos de folga (Frente 89)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ClashDetectionReport"
    components_analyzed_count: int
    total_clashes_count: int
    hard_clashes_count: int
    clearance_clashes_count: int
    clashes: list[dict[str, Any]]
    status: str


class MassPropertiesRequest(BaseModel):
    """Entrada para cálculo de propriedades físicas, massa e Centro de Gravidade (Frente 90)."""

    vertices: list[list[float]] = Field(description="Vértices da malha B-Rep fechada [[x, y, z], ...]")
    triangles: list[list[int]] = Field(description="Índices dos triângulos com normais externas [[i1, i2, i3], ...]")
    material_type: str = Field(default="madeira_eucalipto", description="madeira_eucalipto, madeira_pinus, aco, aluminio, pead_plastico, concreto, vidro")
    custom_density_kg_m3: float = Field(default=0.0, ge=0.0, description="Densidade personalizada (se > 0 substitui o material)")


class MassPropertiesResponse(BaseModel):
    """Resposta com propriedades físicas completas, massa, CG e inércia (Frente 90)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "MassPropertiesReport"
    material_type: str
    density_kg_m3: float
    volume_m3: float
    surface_area_m2: float
    total_mass_kg: float
    center_of_gravity: list[float]
    dimensions_bbox_m: list[float]
    moments_of_inertia_kg_m2: dict[str, float]
    status: str


class SolidShellRequest(BaseModel):
    """Entrada para espessura e casca sólida B-Rep (Frente 91)."""

    vertices: list[list[float]] = Field(description="Vértices da malha original [[x, y, z], ...]")
    faces: list[list[int]] = Field(description="Faces originais [[i1, i2, ...], ...]")
    thickness_m: float = Field(default=0.05, ge=0.001, le=10.0, description="Espessura da parede sólida em metros")
    inwards: bool = Field(default=False, description="Se verdadeiro, expande para dentro da normal")


class SolidShellResponse(BaseModel):
    """Resposta da casca sólida B-Rep gerada (Frente 91)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SolidShellResult"
    thickness_m: float
    inwards: bool
    original_vertices_count: int
    original_faces_count: int
    total_vertices_count: int
    total_faces_count: int
    boundary_quads_count: int
    triangles_count: int
    vertices: list[list[float]]
    faces: list[list[int]]
    triangles: list[list[int]]
    is_solid_manifold: bool
    status: str


class PhotometricSpotLightRequest(BaseModel):
    """Entrada para parametrização de holofote fotométrico spot (Frente 92)."""

    position: list[float] = Field(description="Posição da luminária [x, y, z]")
    target: list[float] = Field(description="Ponto focal ou alvo [x, y, z]")
    lumens: float = Field(default=1200.0, ge=10.0, le=500000.0, description="Fluxo luminoso em lúmens")
    color_temperature_k: float = Field(default=3000.0, ge=1000.0, le=40000.0, description="Temperatura de cor em Kelvin")
    beam_angle_deg: float = Field(default=45.0, ge=5.0, le=175.0, description="Ângulo de abertura do feixe")
    penumbra_percent: float = Field(default=25.0, ge=0.0, le=100.0)
    max_distance_m: float = Field(default=20.0, ge=0.5, le=500.0)
    cast_shadows: bool = Field(default=True)


class PhotometricSpotLightResponse(BaseModel):
    """Resposta com configuração analítica de holofote fotométrico (Frente 92)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "PhotometricSpotLight"
    position: list[float]
    target: list[float]
    direction: list[float]
    photometrics: dict[str, Any]
    beam_geometry: dict[str, Any]
    three_config: dict[str, Any]
    status: str


class PipingRouteRequest(BaseModel):
    """Entrada para geração de rota de tubulação paramétrica (Frente 93)."""

    route_points: list[list[float]] = Field(description="Pontos de eixo da rota [[x, y, z], ...]")
    outer_diameter_mm: float = Field(default=114.3, ge=10.0, le=2000.0, description="Diâmetro externo nominal em mm")
    wall_thickness_mm: float = Field(default=6.02, ge=0.5, le=100.0)
    radial_segments: int = Field(default=16, ge=6, le=64)
    bend_radius_factor: float = Field(default=1.5, ge=0.5, le=10.0)


class PipingRouteResponse(BaseModel):
    """Resposta da malha de tubulação e conexões/cotovelos gerados (Frente 93)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "PipingRouteResult"
    outer_diameter_mm: float
    wall_thickness_mm: float
    total_length_m: float
    segments_count: int
    fittings_count: int
    fittings: list[dict[str, Any]]
    vertices_count: int
    faces_count: int
    triangles_count: int
    vertices: list[list[float]]
    faces: list[list[int]]
    triangles: list[list[int]]
    status: str


class CameraAnimationPathRequest(BaseModel):
    """Entrada para geração de animação de trajetória de câmera (Frente 94)."""

    mode: str = Field(default="ORBIT", description="'ORBIT' ou 'FLYTHROUGH'")
    target_point: list[float] = Field(description="Ponto focal [x, y, z]")
    radius_m: float = Field(default=10.0, ge=0.5, le=1000.0)
    height_m: float = Field(default=3.5, ge=-100.0, le=1000.0)
    start_angle_deg: float = Field(default=0.0)
    total_rotation_deg: float = Field(default=360.0)
    waypoints: list[list[float]] | None = Field(default=None, description="Waypoints para modo FLYTHROUGH")
    duration_seconds: float = Field(default=10.0, ge=0.5, le=600.0)
    fps: int = Field(default=30, ge=1, le=120)
    fov_deg: float = Field(default=45.0, ge=10.0, le=120.0)


class CameraAnimationPathResponse(BaseModel):
    """Resposta com frames contínuos de animação de câmera (Frente 94)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "CameraAnimationPath"
    mode: str
    duration_seconds: float
    fps: int
    total_frames: int
    radius_m: float | None = None
    waypoints_count: int | None = None
    target: list[float]
    frames: list[dict[str, Any]]
    status: str


class CamCutlistRequest(BaseModel):
    """Entrada para geração de lista de corte industrial CNC (Frente 95)."""

    parts: list[dict[str, Any]] = Field(description="Lista de peças [{'name': str, 'length_mm': float, 'width_mm': float, 'thickness_mm': float, 'quantity': int}]")
    saw_kerf_mm: float = Field(default=4.0, ge=0.5, le=20.0, description="Espessura do disco de serra")
    trim_margin_mm: float = Field(default=15.0, ge=0.0, le=100.0, description="Margem de refilo por borda")
    export_csv: bool = Field(default=True)


class CamCutlistResponse(BaseModel):
    """Resposta com lista de corte CNC, métricas de rendimento e CSV industrial (Frente 95)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "CamCutlistReport"
    saw_kerf_mm: float
    trim_margin_mm: float
    unique_parts_count: int
    total_items_count: int
    total_finished_area_m2: float
    total_raw_area_m2: float
    cutting_yield_percent: float
    parts: list[dict[str, Any]]
    csv_data: str
    status: str


class ArchitecturalWallRequest(BaseModel):
    """Entrada para geração de parede arquitetônica com vãos de portas/janelas (Frente 96)."""

    start_pt: list[float] = Field(description="Ponto inicial do eixo da parede [x, y, z]")
    end_pt: list[float] = Field(description="Ponto final do eixo da parede [x, y, z]")
    height_m: float = Field(default=2.80, ge=0.5, le=50.0, description="Altura total da parede em metros")
    thickness_m: float = Field(default=0.15, ge=0.05, le=2.0, description="Espessura da parede em metros")
    openings: list[dict[str, Any]] | None = Field(default=None, description="Lista de aberturas [{'name': str, 'dist_from_start_m': float, 'width_m': float, 'sill_height_m': float, 'height_m': float}]")


class ArchitecturalWallResponse(BaseModel):
    """Resposta da malha de parede arquitetônica e sólidos B-Rep (Frente 96)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ArchitecturalWallResult"
    wall_length_m: float
    height_m: float
    thickness_m: float
    openings_count: int
    blocks_count: int = 1
    vertices_count: int
    faces_count: int
    triangles_count: int
    vertices: list[list[float]]
    faces: list[list[int]]
    triangles: list[list[int]]
    gross_volume_m3: float = 0.0
    void_volume_m3: float = 0.0
    net_volume_m3: float
    status: str


class SheetMetalUnfoldRequest(BaseModel):
    """Entrada para planificação de chapa dobrada DIN 6935 (Frente 97)."""

    base_length_mm: float = Field(description="Comprimento da base plana em mm")
    base_width_mm: float = Field(description="Largura da base plana em mm")
    thickness_mm: float = Field(default=2.0, ge=0.1, le=50.0)
    inner_radius_mm: float = Field(default=2.0, ge=0.1, le=50.0)
    k_factor: float = Field(default=0.44, ge=0.1, le=0.9)
    flanges: list[dict[str, Any]] | None = Field(default=None, description="Lista de abas [{'edge': 'LEFT'/'RIGHT'/'TOP'/'BOTTOM', 'length_mm': float, 'angle_deg': float}]")


class SheetMetalUnfoldResponse(BaseModel):
    """Resposta com dimensões de blank planificado e linhas de dobra (Frente 97)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SheetMetalUnfoldResult"
    material_thickness_mm: float
    inner_bend_radius_mm: float
    k_factor: float
    base_dimensions_mm: list[float]
    blank_dimensions_mm: list[float]
    blank_area_m2: float
    flanges_count: int
    flanges: list[dict[str, Any]]
    bend_lines: list[dict[str, Any]]
    status: str


class ShadowCastingRequest(BaseModel):
    """Entrada para cálculo de projeção de sombra em superfícies receptoras (Frente 98)."""

    occluder_vertices: list[list[float]] = Field(description="Vértices do sólido oclusor [[x, y, z], ...]")
    sun_direction: list[float] = Field(description="Vetor do sol descendente [sx, sy, sz]")
    ground_elevation_z: float = Field(default=0.0)


class ShadowCastingResponse(BaseModel):
    """Resposta com contorno da sombra projetada e métricas solares (Frente 98)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ProjectedShadowResult"
    ground_elevation_z: float
    sun_direction: list[float]
    solar_zenith_angle_deg: float = 0.0
    projected_vertices_count: int
    projected_points: list[list[float]]
    shadow_throw_length_m: float
    shadow_bbox: list[float] = Field(default_factory=list)
    shadow_bbox_area_m2: float
    status: str


class WaterMaterialConfigRequest(BaseModel):
    """Entrada para configuração de shader PBR de água e ondas de Gerstner (Frente 99)."""

    shallow_color_hex: str = Field(default="#4db5ff")
    deep_color_hex: str = Field(default="#004080")
    clarity_percent: float = Field(default=85.0, ge=0.0, le=100.0)
    wave_amplitude_m: float = Field(default=0.05, ge=0.0, le=5.0)
    wave_wavelength_m: float = Field(default=1.2, ge=0.1, le=100.0)
    wave_speed_m_s: float = Field(default=1.0, ge=0.0, le=50.0)
    ior: float = Field(default=1.333, ge=1.0, le=2.5)
    caustics_intensity: float = Field(default=0.75, ge=0.0, le=2.0)
    enable_foam: bool = Field(default=True)


class WaterMaterialConfigResponse(BaseModel):
    """Resposta com uniformes de água para Three.js (Frente 99)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "PBRWaterMaterialConfig"
    optical_properties: dict[str, Any]
    wave_dynamics: dict[str, Any]
    three_uniforms: dict[str, Any]
    status: str


class SkpLODChainRequest(BaseModel):
    """Entrada para decimação e geração de cadeia de LOD Three.js (Frente 100)."""

    vertices: list[list[float]] = Field(description="Vértices da malha original [[x, y, z], ...]")
    triangles: list[list[int]] = Field(description="Triângulos originais [[i1, i2, i3], ...]")
    lod1_target_ratio: float = Field(default=0.50, ge=0.05, le=0.95)
    lod2_target_ratio: float = Field(default=0.25, ge=0.02, le=0.50)


class SkpLODChainResponse(BaseModel):
    """Resposta com os 3 níveis de detalhe (LOD0, LOD1, LOD2) e distâncias (Frente 100)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SkpLODChainResult"
    original_mesh: dict[str, int]
    lod_levels: list[dict[str, Any]]
    metrics: dict[str, Any]
    status: str


class StairGeneratorRequest(BaseModel):
    """Entrada para geração de escada paramétrica e cálculo de Blondel NBR 9050 (Frente 101)."""

    total_height_m: float = Field(default=2.80, ge=0.3, le=50.0, description="Desnível total a vencer")
    stair_width_m: float = Field(default=1.00, ge=0.5, le=10.0, description="Largura útil da escada")
    stair_type: str = Field(default="STRAIGHT", description="'STRAIGHT', 'L_SHAPE', 'SPIRAL_HELICAL', 'SANTOS_DUMONT'")
    origin_xyz: list[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0])
    add_handrail: bool = Field(default=True)


class StairGeneratorResponse(BaseModel):
    """Resposta com malha 3D de escada e caminho de corrimão (Frente 101)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "StairGeometryResult"
    stair_type: str
    total_height_m: float
    stair_width_m: float
    total_run_length_m: float
    blondel_info: dict[str, Any]
    steps_count: int
    vertices_count: int
    faces_count: int
    triangles_count: int
    vertices: list[list[float]]
    faces: list[list[int]]
    triangles: list[list[int]]
    handrail_path: list[list[float]]
    status: str


class VoronoiPanelRequest(BaseModel):
    """Entrada para geração de painel Voronoi vazado paramétrico (Frente 102)."""

    width_m: float = Field(default=2.0, ge=0.1, le=50.0)
    height_m: float = Field(default=1.0, ge=0.1, le=50.0)
    thickness_m: float = Field(default=0.03, ge=0.005, le=1.0)
    num_seeds: int = Field(default=12, ge=3, le=100)
    seed_random_seed: int = Field(default=42)
    cell_inset_ratio: float = Field(default=0.20, ge=0.05, le=0.80)


class VoronoiPanelResponse(BaseModel):
    """Resposta com células Voronoi e loops vazados (Frente 102)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "VoronoiPanelResult"
    panel_dimensions_m: list[float]
    seeds_count: int
    seeds: list[list[float]]
    cells: list[dict[str, Any]]
    cell_inset_ratio: float
    status: str


class WindPressureRequest(BaseModel):
    """Entrada para cálculo de vento normativo NBR 6123 (Frente 103)."""

    basic_speed_v0_m_s: float = Field(default=45.0, ge=10.0, le=100.0, description="Velocidade básica V0 em m/s")
    terrain_category: str = Field(default="IV", description="'I', 'II', 'III', 'IV', 'V'")
    building_height_m: float = Field(default=12.0, ge=1.0, le=300.0)
    facade_width_m: float = Field(default=20.0, ge=1.0, le=500.0)
    facade_length_m: float = Field(default=15.0, ge=1.0, le=500.0)
    topographic_s1: float = Field(default=1.0, ge=0.8, le=2.0)
    statistical_s3: float = Field(default=1.0, ge=0.8, le=1.5)


class WindPressureResponse(BaseModel):
    """Resposta com pressão dinâmica e forças de arrasto de vento (Frente 103)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "WindPressureReport"
    parameters: dict[str, Any]
    aerodynamics: dict[str, Any]
    facade_loads: dict[str, Any]
    status: str


class AtmosphericSkyRequest(BaseModel):
    """Entrada para configuração de céu físico Rayleigh/Mie (Frente 104)."""

    solar_elevation_deg: float = Field(default=35.0, ge=-10.0, le=90.0)
    solar_azimuth_deg: float = Field(default=135.0, ge=0.0, le=360.0)
    turbidity: float = Field(default=3.0, ge=1.0, le=20.0)
    rayleigh: float = Field(default=1.2, ge=0.0, le=10.0)
    mie_coefficient: float = Field(default=0.005, ge=0.0, le=0.1)
    mie_directional_g: float = Field(default=0.82, ge=0.0, le=1.0)


class AtmosphericSkyResponse(BaseModel):
    """Resposta com parâmetros de espalhamento e Three.js Sky (Frente 104)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "AtmosphericSkyConfig"
    solar_angles: dict[str, Any]
    sun_position_vector: list[float]
    atmospheric_parameters: dict[str, Any]
    three_sky_uniforms: dict[str, Any]
    status: str


class IFC4BimExportRequest(BaseModel):
    """Entrada para compilação física STEP ISO-10303-21 IFC4 LOD 350 (Frente 105)."""

    project_name: str = Field(default="Projeto Executivo SketchBuild")
    elements: list[dict[str, Any]] = Field(description="Lista de elementos [{'name': str, 'ifc_type': str, 'vertices': [...], 'triangles': [...]}]")
    author: str = Field(default="SketchBuild Engineer")
    organization: str = Field(default="Parkelo & SketchBuild")


class IFC4BimExportResponse(BaseModel):
    """Resposta com o documento STEP IFC4 em texto puro (Frente 105)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "IFC4StepExportResult"
    project_name: str
    elements_count: int
    step_file_size_bytes: int
    ifc_schema: str = "IFC4"
    step_content: str
    status: str


# ============================================================================
# Frentes 106 a 115: Física, Fatiamento 3D, MEP, Conforto, Aço e SINAPI 5D
# ============================================================================

class RigidBodyPhysicsRequest(BaseModel):
    """Entrada para simulação de física de corpos rígidos (Frente 106)."""

    bodies: list[dict[str, Any]] = Field(default_factory=list, description="Lista de corpos [{'id', 'name', 'mass_kg', 'initial_pos', 'initial_vel', 'dimensions'}]")
    gravity_z: float = Field(default=-9.81, description="Aceleração gravitacional em m/s2")
    ground_z: float = Field(default=0.0)
    total_time_s: float = Field(default=2.0, ge=0.1, le=10.0)
    time_step_s: float = Field(default=0.016, ge=0.001, le=0.1)
    restitution: float = Field(default=0.45, ge=0.0, le=1.0)
    friction_coeff: float = Field(default=0.35, ge=0.0, le=1.0)


class RigidBodyPhysicsResponse(BaseModel):
    """Resposta com trajetórias de corpos rígidos (Frente 106)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "RigidBodyPhysicsReport"
    parameters: dict[str, Any]
    bodies_count: int
    final_summary: list[dict[str, Any]]
    trajectories: dict[str, list[dict[str, Any]]]
    status: str


class Slicing3dPrintRequest(BaseModel):
    """Entrada para fatiamento FDM e estimativa de impressão 3D (Frente 107)."""

    vertices: list[list[float]] = Field(description="Vértices 3D da malha")
    triangles: list[list[int]] = Field(description="Triângulos indexados")
    layer_height_mm: float = Field(default=0.20, ge=0.05, le=1.0)
    infill_percent: float = Field(default=20.0, ge=0.0, le=100.0)
    print_speed_mm_s: float = Field(default=50.0, ge=10.0, le=300.0)


class Slicing3dPrintResponse(BaseModel):
    """Resposta com métricas de fatiamento FDM (Frente 107)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "FdmSlicingReport"
    parameters: dict[str, Any]
    dimensions_mm: dict[str, Any]
    slicing_metrics: dict[str, Any]
    layers_sample: list[dict[str, Any]]
    status: str


class RetainingWallRequest(BaseModel):
    """Entrada para dimensionamento de muro de arrimo NBR 11682 (Frente 108)."""

    wall_height_m: float = Field(default=3.0, ge=0.5, le=15.0)
    stem_top_thickness_m: float = Field(default=0.25, ge=0.15, le=2.0)
    stem_bottom_thickness_m: float = Field(default=0.45, ge=0.20, le=3.0)
    base_width_m: float = Field(default=1.80, ge=0.5, le=10.0)
    base_thickness_m: float = Field(default=0.40, ge=0.2, le=2.0)
    soil_friction_angle_deg: float = Field(default=30.0, ge=15.0, le=45.0)
    soil_unit_weight_kn_m3: float = Field(default=18.0, ge=10.0, le=25.0)
    concrete_unit_weight_kn_m3: float = Field(default=25.0, ge=20.0, le=30.0)
    surcharge_kpa: float = Field(default=5.0, ge=0.0, le=50.0)


class RetainingWallResponse(BaseModel):
    """Resposta com fatores de segurança e malha 3D do muro (Frente 108)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "RetainingWallReport"
    parameters: dict[str, Any]
    stability_analysis: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str


class HydraulicPipingRequest(BaseModel):
    """Entrada para cálculo de rede hidráulica NBR 5626 (Frente 109)."""

    pipe_diameter_dn_mm: float = Field(default=25.0, ge=15.0, le=150.0)
    flow_rate_l_s: float = Field(default=0.50, ge=0.01, le=50.0)
    pipe_roughness_c: float = Field(default=140.0, ge=80.0, le=160.0)
    inlet_pressure_mca: float = Field(default=15.0, ge=1.0, le=100.0)
    waypoints: list[list[float]] | None = Field(default=None)
    fittings: list[str] | None = Field(default=None)


class HydraulicPipingResponse(BaseModel):
    """Resposta com perda de carga e pressão residual NBR 5626 (Frente 109)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "HydraulicPipingReport"
    parameters: dict[str, Any]
    hydraulic_results: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str


class ElectricalConduitRequest(BaseModel):
    """Entrada para dimensionamento de eletrodutos NBR 5410 (Frente 110)."""

    conduit_nominal_dn_mm: float = Field(default=25.0, ge=16.0, le=110.0)
    circuit_current_amperes: float = Field(default=16.0, ge=1.0, le=200.0)
    cable_gauge_mm2: float = Field(default=2.5, ge=1.5, le=120.0)
    cables_count: int = Field(default=3, ge=1, le=24)
    circuit_length_m: float = Field(default=18.0, ge=1.0, le=300.0)
    voltage_v: float = Field(default=127.0, ge=100.0, le=500.0)
    power_factor: float = Field(default=0.95, ge=0.5, le=1.0)


class ElectricalConduitResponse(BaseModel):
    """Resposta com taxa de ocupação e queda de tensão NBR 5410 (Frente 110)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ElectricalConduitReport"
    parameters: dict[str, Any]
    conduit_occupancy: dict[str, Any]
    voltage_drop: dict[str, Any]
    diagnostic: dict[str, Any]
    waypoints_3d: list[list[float]]
    status: str


class ThermalComfortRequest(BaseModel):
    """Entrada para avaliação térmica NBR 15220 (Frente 111)."""

    layers: list[dict[str, Any]] | None = Field(default=None)
    rsi_m2_k_w: float = Field(default=0.13)
    rse_m2_k_w: float = Field(default=0.04)
    target_bioclimatic_zone: int = Field(default=3, ge=1, le=8)


class ThermalComfortResponse(BaseModel):
    """Resposta com transmitância térmica U e capacidade Ct NBR 15220 (Frente 111)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "ThermalComfortReport"
    parameters: dict[str, Any]
    thermal_metrics: dict[str, Any]
    layers: list[dict[str, Any]]
    status: str


class RoomAcousticsRequest(BaseModel):
    """Entrada para acústica de salas NBR 10152 (Frente 112)."""

    room_width_m: float = Field(default=6.0, ge=1.0, le=100.0)
    room_length_m: float = Field(default=8.0, ge=1.0, le=100.0)
    room_height_m: float = Field(default=3.0, ge=1.0, le=30.0)
    surfaces: list[dict[str, Any]] | None = Field(default=None)
    room_type: str = Field(default="CLASSROOM")


class RoomAcousticsResponse(BaseModel):
    """Resposta com espectro RT60 e diagnóstico de inteligibilidade (Frente 112)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "RoomAcousticsReport"
    parameters: dict[str, Any]
    acoustic_metrics: dict[str, Any]
    rt60_frequency_spectrum: dict[str, float]
    total_absorption_sabins: list[float]
    status: str


class DaylightFactorRequest(BaseModel):
    """Entrada para cálculo do Fator de Luz Diurna FLD NBR 15215 (Frente 113)."""

    room_width_m: float = Field(default=4.0, ge=1.0, le=50.0)
    room_depth_m: float = Field(default=6.0, ge=1.0, le=50.0)
    room_height_m: float = Field(default=2.80, ge=1.5, le=10.0)
    window_width_m: float = Field(default=2.0, ge=0.5, le=30.0)
    window_height_m: float = Field(default=1.20, ge=0.3, le=5.0)
    window_sill_height_m: float = Field(default=1.0, ge=0.0, le=3.0)
    glass_transmittance: float = Field(default=0.85, ge=0.1, le=1.0)
    external_horizontal_lux: float = Field(default=10000.0, ge=1000.0, le=100000.0)
    average_internal_reflectance: float = Field(default=0.50, ge=0.1, le=0.9)
    obstruction_angle_deg: float = Field(default=15.0, ge=0.0, le=75.0)


class DaylightFactorResponse(BaseModel):
    """Resposta com FLD médio e grelha no plano de trabalho NBR 15215 (Frente 113)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "DaylightFactorReport"
    parameters: dict[str, Any]
    daylight_metrics: dict[str, Any]
    workplane_grid_points: list[dict[str, Any]]
    status: str


class SteelProfileRequest(BaseModel):
    """Entrada para geração de perfil metálico NBR 8800 (Frente 114)."""

    depth_d_mm: float = Field(default=200.0, ge=50.0, le=1200.0)
    flange_width_bf_mm: float = Field(default=100.0, ge=25.0, le=600.0)
    web_thickness_tw_mm: float = Field(default=6.0, ge=1.5, le=50.0)
    flange_thickness_tf_mm: float = Field(default=9.0, ge=2.0, le=80.0)
    length_m: float = Field(default=3.0, ge=0.1, le=20.0)


class SteelProfileResponse(BaseModel):
    """Resposta com propriedades de seção NBR 8800 e B-Rep 3D (Frente 114)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "SteelProfileReport"
    profile_type: str
    nominal_designation: str
    dimensions_mm: dict[str, Any]
    section_properties: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str


class Bim5dSinapiCostRequest(BaseModel):
    """Entrada para orçamento paramétrico 5D com tabela SINAPI (Frente 115)."""

    elements: list[dict[str, Any]] | None = Field(default=None)
    bdi_percent: float = Field(default=24.50, ge=0.0, le=60.0)
    social_charges_percent: float = Field(default=84.0, ge=0.0, le=150.0)


class Bim5dSinapiCostResponse(BaseModel):
    """Resposta com orçamento detalhado, BDI e Curva ABC SINAPI (Frente 115)."""

    model_config = ConfigDict(from_attributes=True)

    entity_type: str = "Bim5dSinapiReport"
    financial_summary: dict[str, Any]
    items_count: int
    abc_classification_summary: dict[str, Any]
    items: list[dict[str, Any]]
    status: str


# ============================================================================
# Frentes 116 a 145: Schemas de Engenharia Civil, Geotecnia, MEP, BIM 4D/7D e Sustentabilidade
# ============================================================================

# 116
class StormwaterDrainageRequest(BaseModel):
    roof_area_m2: float = Field(default=120.0, ge=1.0)
    rainfall_intensity_mm_h: float = Field(default=150.0, ge=10.0)
    gutter_width_m: float = Field(default=0.20, ge=0.05)
    gutter_depth_m: float = Field(default=0.15, ge=0.05)
    gutter_slope_m_m: float = Field(default=0.005, ge=0.001)
    downspout_diameter_mm: float = Field(default=100.0, ge=50.0)
    gutters_count: int = Field(default=2, ge=1)

class StormwaterDrainageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    hydraulic_results: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 117
class PermeablePavementRequest(BaseModel):
    pavement_area_m2: float = Field(default=250.0, ge=1.0)
    design_rainfall_mm: float = Field(default=60.0, ge=1.0)
    surface_type: str = Field(default="INTERLOCKING_CONCRETE_BLOCKS")
    base_thickness_m: float = Field(default=0.25, ge=0.05)
    base_voids_ratio: float = Field(default=0.38, ge=0.1, le=0.6)
    soil_infiltration_rate_mm_h: float = Field(default=15.0, ge=0.1)

class PermeablePavementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    drainage_metrics: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 118
class SewerNetworkGravityRequest(BaseModel):
    pipe_diameter_dn_mm: float = Field(default=150.0, ge=100.0)
    flow_rate_l_s: float = Field(default=2.50, ge=0.01)
    pipe_length_m: float = Field(default=40.0, ge=1.0)
    slope_m_m: float = Field(default=0.008, ge=0.001)
    manning_n: float = Field(default=0.013)

class SewerNetworkGravityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    hydraulic_metrics: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 119
class DetentionBasinHydrologyRequest(BaseModel):
    catchment_area_ha: float = Field(default=5.0, ge=0.1)
    runoff_coefficient: float = Field(default=0.70, ge=0.05, le=1.0)
    design_rainfall_intensity_mm_h: float = Field(default=120.0, ge=10.0)
    allowable_outflow_l_s: float = Field(default=250.0, ge=1.0)
    basin_depth_m: float = Field(default=2.0, ge=0.5)

class DetentionBasinHydrologyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    hydrologic_results: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 120
class EarthworkBrucknerRequest(BaseModel):
    cross_sections: list[dict[str, Any]] | None = Field(default=None)
    bulking_factor: float = Field(default=1.25, ge=1.0, le=2.0)
    compaction_factor: float = Field(default=0.85, ge=0.5, le=1.0)

class EarthworkBrucknerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    earthwork_summary: dict[str, Any]
    bruckner_curve: list[dict[str, Any]]
    status: str

# 121
class SlopeStabilityBishopRequest(BaseModel):
    slope_height_m: float = Field(default=8.0, ge=1.0)
    slope_angle_deg: float = Field(default=35.0, ge=5.0, le=80.0)
    soil_cohesion_kpa: float = Field(default=12.0, ge=0.0)
    soil_friction_angle_deg: float = Field(default=28.0, ge=5.0, le=45.0)
    soil_unit_weight_kn_m3: float = Field(default=19.0, ge=10.0)
    piezometric_ru: float = Field(default=0.15, ge=0.0, le=0.5)

class SlopeStabilityBishopResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    stability_analysis: dict[str, Any]
    failure_arc_points: list[list[float]]
    status: str

# 122
class DeepFoundationsPilesRequest(BaseModel):
    pile_type: str = Field(default="CONTINUOUS_FLIGHT_AUGER")
    pile_diameter_mm: float = Field(default=500.0, ge=200.0)
    pile_length_m: float = Field(default=12.0, ge=2.0)
    spt_profile_n_values: list[int] | None = Field(default=None)
    column_axial_load_kn: float = Field(default=1800.0, ge=10.0)

class DeepFoundationsPilesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    geotechnical_capacity: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 123
class ShallowFootingsRequest(BaseModel):
    column_load_kn: float = Field(default=650.0, ge=10.0)
    soil_allowable_stress_mpa: float = Field(default=0.20, ge=0.05)
    column_dim_a_cm: float = Field(default=20.0, ge=10.0)
    column_dim_b_cm: float = Field(default=40.0, ge=10.0)
    fck_concrete_mpa: float = Field(default=25.0, ge=15.0)

class ShallowFootingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    footing_dimensions: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 124
class GabionRetainingWallRequest(BaseModel):
    wall_height_m: float = Field(default=4.0, ge=1.0)
    tiers_count: int = Field(default=4, ge=1)
    base_width_m: float = Field(default=2.5, ge=0.5)
    top_width_m: float = Field(default=1.0, ge=0.5)
    soil_friction_angle_deg: float = Field(default=30.0, ge=15.0)

class GabionRetainingWallResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    stability_analysis: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 125
class ConcreteFormworkShoringRequest(BaseModel):
    element_type: str = Field(default="COLUMN")
    height_or_span_m: float = Field(default=3.20, ge=0.5)
    pour_rate_v_m_h: float = Field(default=2.50, ge=0.5)
    slump_cm: float = Field(default=12.0, ge=5.0)
    slab_thickness_cm: float = Field(default=15.0, ge=5.0)

class ConcreteFormworkShoringResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    formwork_metrics: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 126
class ReinforcedConcreteBeamRequest(BaseModel):
    section_width_bw_cm: float = Field(default=20.0, ge=10.0)
    section_height_h_cm: float = Field(default=50.0, ge=15.0)
    bending_moment_mk_kn_m: float = Field(default=120.0, ge=1.0)
    shear_force_vk_kn: float = Field(default=85.0, ge=1.0)
    concrete_fck_mpa: float = Field(default=30.0, ge=15.0)

class ReinforcedConcreteBeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    design_results: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 127
class WaffleSlabRequest(BaseModel):
    span_x_m: float = Field(default=8.0, ge=2.0)
    span_y_m: float = Field(default=8.0, ge=2.0)
    rib_spacing_cm: float = Field(default=80.0, ge=40.0)
    rib_width_bw_cm: float = Field(default=12.0, ge=7.0)
    slab_total_height_h_cm: float = Field(default=30.0, ge=15.0)
    topping_thickness_hf_cm: float = Field(default=5.0, ge=4.0)

class WaffleSlabResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    waffle_metrics: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 128
class PrestressedConcreteRequest(BaseModel):
    beam_span_m: float = Field(default=16.0, ge=4.0)
    section_height_h_m: float = Field(default=0.90, ge=0.3)
    section_width_bw_m: float = Field(default=0.35, ge=0.15)
    strands_count: int = Field(default=8, ge=1)
    eccentricity_midspan_m: float = Field(default=0.32, ge=0.0)
    concrete_fck_mpa: float = Field(default=40.0, ge=25.0)

class PrestressedConcreteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    prestress_metrics: dict[str, Any]
    parabolic_tendon_3d: list[list[float]]
    status: str

# 129
class GlulamCltTimberRequest(BaseModel):
    timber_type: str = Field(default="GLULAM_BEAM")
    span_m: float = Field(default=9.0, ge=1.0)
    width_b_cm: float = Field(default=16.0, ge=5.0)
    height_h_cm: float = Field(default=45.0, ge=10.0)
    distributed_load_kn_m: float = Field(default=12.0, ge=0.5)
    fire_resistance_rating_minutes: int = Field(default=60, ge=0)

class GlulamCltTimberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    timber_structural_results: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 130
class SpaceTrussRequest(BaseModel):
    span_x_m: float = Field(default=12.0, ge=4.0)
    span_y_m: float = Field(default=12.0, ge=4.0)
    module_size_m: float = Field(default=2.0, ge=1.0)
    truss_depth_m: float = Field(default=1.20, ge=0.5)
    uniform_load_kn_m2: float = Field(default=1.20, ge=0.2)

class SpaceTrussResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    truss_statistics: dict[str, Any]
    truss_nodes: list[dict[str, Any]]
    status: str

# 131
class FuelGasPipingRequest(BaseModel):
    gas_type: str = Field(default="GLP")
    total_power_kw: float = Field(default=75.0, ge=1.0)
    pipe_length_m: float = Field(default=25.0, ge=1.0)
    inlet_pressure_kpa: float = Field(default=2.80, ge=1.0)
    nominal_diameter_dn_mm: float = Field(default=22.0, ge=10.0)

class FuelGasPipingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    gas_network_results: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 132
class LightningProtectionSpdaRequest(BaseModel):
    building_width_m: float = Field(default=20.0, ge=2.0)
    building_length_m: float = Field(default=30.0, ge=2.0)
    building_height_m: float = Field(default=18.0, ge=2.0)
    protection_level: str = Field(default="LEVEL_III")
    air_terminals_count: int = Field(default=4, ge=1)

class LightningProtectionSpdaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    spda_design: dict[str, Any]
    air_terminals_positions_3d: list[list[float]]
    status: str

# 133
class FireEgressRouteRequest(BaseModel):
    occupancy_type: str = Field(default="OFFICE_D1")
    floor_population_persons: int = Field(default=180, ge=1)
    longest_travel_distance_m: float = Field(default=38.0, ge=1.0)
    has_sprinklers: bool = Field(default=True)
    doors_count: int = Field(default=2, ge=1)

class FireEgressRouteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    egress_metrics: dict[str, Any]
    egress_path_waypoints_3d: list[list[float]]
    status: str

# 134
class HvacThermalLoadRequest(BaseModel):
    floor_area_m2: float = Field(default=80.0, ge=5.0)
    ceiling_height_m: float = Field(default=2.80, ge=2.0)
    occupants_count: int = Field(default=8, ge=1)
    outdoor_temp_c: float = Field(default=34.0, ge=20.0)
    indoor_temp_c: float = Field(default=24.0, ge=16.0)

class HvacThermalLoadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    thermal_load_breakdown: dict[str, Any]
    status: str

# 135
class PhotometricLumenDesignRequest(BaseModel):
    room_length_m: float = Field(default=10.0, ge=2.0)
    room_width_m: float = Field(default=6.0, ge=2.0)
    ceiling_height_m: float = Field(default=3.0, ge=2.0)
    target_lux: float = Field(default=500.0, ge=50.0)
    lamp_lumens: float = Field(default=4000.0, ge=500.0)

class PhotometricLumenDesignResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    lighting_results: dict[str, Any]
    luminaire_positions_3d: list[list[float]]
    status: str

# 136
class SolarPhotovoltaicArrayRequest(BaseModel):
    roof_available_area_m2: float = Field(default=150.0, ge=10.0)
    latitude_deg: float = Field(default=-23.55)
    module_peak_power_w: float = Field(default=550.0, ge=100.0)
    solar_irradiance_kwh_m2_day: float = Field(default=4.80, ge=1.0)

class SolarPhotovoltaicArrayResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    solar_system_metrics: dict[str, Any]
    modules_positions_3d: list[list[float]]
    status: str

# 137
class NaturalVentilationRequest(BaseModel):
    room_volume_m3: float = Field(default=180.0, ge=10.0)
    inlet_opening_area_m2: float = Field(default=2.50, ge=0.1)
    outlet_opening_area_m2: float = Field(default=2.50, ge=0.1)
    vertical_height_difference_m: float = Field(default=4.0, ge=0.5)
    wind_speed_m_s: float = Field(default=3.5, ge=0.1)

class NaturalVentilationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    ventilation_results: dict[str, Any]
    status: str

# 138
class GlazingFenestrationRequest(BaseModel):
    fenestration_type: str = Field(default="CURTAIN_WALL")
    width_m: float = Field(default=3.0, ge=0.5)
    height_m: float = Field(default=2.60, ge=0.5)
    glass_type: str = Field(default="LAMINATED_DOUBLE")
    glass_thickness_mm: float = Field(default=8.0, ge=4.0)

class GlazingFenestrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    fenestration_metrics: dict[str, Any]
    geometry_3d: dict[str, Any]
    status: str

# 139
class VentilatedFacadeRequest(BaseModel):
    facade_height_m: float = Field(default=15.0, ge=2.0)
    facade_width_m: float = Field(default=20.0, ge=2.0)
    air_cavity_depth_cm: float = Field(default=8.0, ge=3.0)
    cladding_material: str = Field(default="PORCELAIN_TILES")

class VentilatedFacadeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    thermal_and_structural_results: dict[str, Any]
    status: str

# 140
class MiniWindCfd2dRequest(BaseModel):
    building_width_m: float = Field(default=12.0, ge=2.0)
    building_depth_m: float = Field(default=12.0, ge=2.0)
    wind_inflow_speed_m_s: float = Field(default=10.0, ge=1.0)
    grid_resolution: str = Field(default="MEDIUM")

class MiniWindCfd2dResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    aerodynamic_results: dict[str, Any]
    streamlines_sample: list[list[dict[str, Any]]]
    status: str

# 141
class Bim4dGanttScheduleRequest(BaseModel):
    project_start_date: str = Field(default="2026-11-01")
    tasks: list[dict[str, Any]] | None = Field(default=None)
    total_budget_brl: float = Field(default=450000.0, ge=1000.0)

class Bim4dGanttScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    schedule_summary: dict[str, Any]
    gantt_tasks: list[dict[str, Any]]
    curve_s_points: list[dict[str, Any]]
    status: str

# 142
class Bim7dAssetManagementCobieRequest(BaseModel):
    facility_name: str = Field(default="Edifício Corporativo SketchBuild")
    assets: list[dict[str, Any]] | None = Field(default=None)

class Bim7dAssetManagementCobieResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    facility_management_summary: dict[str, Any]
    cobie_components: list[dict[str, Any]]
    preventive_tasks: list[dict[str, Any]]
    status: str

# 143
class ConstructionSiteLogisticsRequest(BaseModel):
    site_width_m: float = Field(default=60.0, ge=10.0)
    site_length_m: float = Field(default=80.0, ge=10.0)
    building_footprint_m2: float = Field(default=1200.0, ge=50.0)
    cranes: list[dict[str, Any]] | None = Field(default=None)
    daily_workers_count: int = Field(default=65, ge=1)

class ConstructionSiteLogisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    logistics_results: dict[str, Any]
    status: str

# 144
class UniversalAccessibilityRequest(BaseModel):
    door_clear_width_cm: float = Field(default=85.0, ge=50.0)
    corridor_width_cm: float = Field(default=120.0, ge=80.0)
    ramp_slope_percent: float = Field(default=8.33, ge=1.0)
    ramp_rise_height_cm: float = Field(default=60.0, ge=5.0)
    wheelchair_turn_space_diameter_m: float = Field(default=1.50, ge=0.8)
    has_tactile_paving: bool = Field(default=True)

class UniversalAccessibilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    compliance_checklist: dict[str, Any]
    status: str

# 145
class LifeCycleAssessmentRequest(BaseModel):
    gross_floor_area_m2: float = Field(default=850.0, ge=10.0)
    building_lifespan_years: int = Field(default=50, ge=10)
    materials_inventory: list[dict[str, Any]] | None = Field(default=None)

class LifeCycleAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str
    parameters: dict[str, Any]
    lca_metrics: dict[str, Any]
    materials_breakdown: list[dict[str, Any]]
    status: str


# ==============================================================================
# OPÇÃO A: FERRAMENTAS NATIVAS OFICIAIS DO SKETCHUP
# ==============================================================================

# Walk & Look Around & Position Camera
class PositionCameraNativeRequest(BaseModel):
    eye_x: float = Field(default=0.0)
    eye_y: float = Field(default=-5.0)
    eye_z: float = Field(default=0.0)
    target_x: float = Field(default=0.0)
    target_y: float = Field(default=0.0)
    target_z: float = Field(default=1.0)
    eye_height_m: float = Field(default=1.68, ge=0.1, le=5.0)
    use_eye_height_offset: bool = Field(default=True)

class PositionCameraNativeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_position_camera"
    camera: dict[str, Any]
    status: str = "success"

class LookAroundNativeRequest(BaseModel):
    eye: tuple[float, float, float] = Field(default=(0.0, -5.0, 1.68))
    current_yaw_deg: float = Field(default=0.0)
    current_pitch_deg: float = Field(default=0.0)
    delta_yaw_deg: float = Field(default=5.0)
    delta_pitch_deg: float = Field(default=0.0)
    target_distance_m: float = Field(default=10.0, ge=0.5)

class LookAroundNativeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_look_around"
    camera: dict[str, Any]
    status: str = "success"

class WalkStepNativeRequest(BaseModel):
    current_eye: tuple[float, float, float] = Field(default=(0.0, -5.0, 1.68))
    yaw_deg: float = Field(default=0.0)
    move_forward: float = Field(default=0.5)
    move_strafe: float = Field(default=0.0)
    obstacles_aabb: list[dict[str, Any]] | None = Field(default=None)
    terrain_elevation_z: float | None = Field(default=None)
    eye_height_m: float = Field(default=1.68, ge=0.1, le=5.0)
    enable_collision: bool = Field(default=True)

class WalkStepNativeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_walk_step"
    walk_result: dict[str, Any]
    status: str = "success"

# Sandbox Tools
class SandboxSmooveRequest(BaseModel):
    vertices: list[tuple[float, float, float]] = Field(default_factory=list)
    center_x: float = Field(default=0.0)
    center_y: float = Field(default=0.0)
    radius_m: float = Field(default=5.0, ge=0.1)
    offset_z_m: float = Field(default=1.5)

class SandboxSmooveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_sandbox_smoove"
    smoove_result: dict[str, Any]
    status: str = "success"

class SandboxStampRequest(BaseModel):
    vertices: list[tuple[float, float, float]] = Field(default_factory=list)
    footprint_poly: list[tuple[float, float]] = Field(default_factory=list)
    plateau_elevation_z: float = Field(default=1.0)
    skirt_offset_m: float = Field(default=1.5, ge=0.0)

class SandboxStampResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_sandbox_stamp"
    stamp_result: dict[str, Any]
    status: str = "success"

class SandboxDrapeRequest(BaseModel):
    path_points_2d: list[tuple[float, float]] = Field(default_factory=list)
    triangles: list[list[tuple[float, float, float]]] = Field(default_factory=list)

class SandboxDrapeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_sandbox_drape"
    drape_result: dict[str, Any]
    status: str = "success"

class SandboxFlipEdgeRequest(BaseModel):
    tri_a: list[tuple[float, float, float]]
    tri_b: list[tuple[float, float, float]]

class SandboxFlipEdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_sandbox_flip_edge"
    flip_result: dict[str, Any]
    status: str = "success"

# Match Photo
class MatchPhotoCalibrateRequest(BaseModel):
    image_width_px: int = Field(default=1920, ge=100)
    image_height_px: int = Field(default=1080, ge=100)
    red_line_1: tuple[tuple[float, float], tuple[float, float]]
    red_line_2: tuple[tuple[float, float], tuple[float, float]]
    green_line_1: tuple[tuple[float, float], tuple[float, float]]
    green_line_2: tuple[tuple[float, float], tuple[float, float]]
    origin_screen_px: tuple[float, float] | None = Field(default=None)
    reference_height_m: float = Field(default=3.0, ge=0.1)
    reference_segment_px: tuple[tuple[float, float], tuple[float, float]] | None = Field(default=None)

class MatchPhotoCalibrateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_match_photo"
    calibration: dict[str, Any]
    status: str = "success"

# Watermark Style
class WatermarkStyleConfigureRequest(BaseModel):
    name: str = Field(default="Selo Oficial")
    image_url: str = Field(default="/static/watermarks/parkelo_stamp.png")
    layer: str = Field(default="overlay")  # 'overlay' ou 'background'
    placement: str = Field(default="screen_position")  # 'screen_position', 'tiled', 'stretched'
    anchor: str = Field(default="bottom-right")
    opacity_pct: float = Field(default=85.0, ge=0.0, le=100.0)
    scale_pct: float = Field(default=100.0, ge=10.0, le=500.0)
    lock_aspect_ratio: bool = Field(default=True)
    blend_mode: str = Field(default="normal")
    offset_px: tuple[int, int] = Field(default=(20, 20))

class WatermarkStyleConfigureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_watermark_style"
    watermark_config: dict[str, Any]
    status: str = "success"

# Dynamic Component Interaction
class DynamicComponentInteractRequest(BaseModel):
    instance_id: str = Field(default="inst_1")
    dynamic_attributes: dict[str, Any] = Field(default_factory=dict)
    onclick_formula: str | None = Field(default=None)

class DynamicComponentInteractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_dynamic_component_interact"
    interaction_result: dict[str, Any]
    status: str = "success"

# Trimble Solid Tools
class TrimbleSolidToolsRequest(BaseModel):
    operation: str = Field(default="subtract")  # 'intersect', 'union', 'subtract', 'trim', 'split'
    solid_a: dict[str, Any]
    solid_b: dict[str, Any]

class TrimbleSolidToolsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_trimble_solid_tools"
    operation_result: dict[str, Any]
    status: str = "success"


# ==============================================================================
# OPÇÃO A (PARTE 2): FERRAMENTAS E SUBSISTEMAS NATIVOS ADICIONAIS DO SKETCHUP
# ==============================================================================

# 1. Classificação IFC / BIM
class IfcClassifyComponentRequest(BaseModel):
    instance_id: str = Field(default="inst_1")
    definition_name: str = Field(default="Viga Principal")
    schema_name: str = Field(default="IFC4")
    ifc_class: str = Field(default="IfcBeam")
    predefined_type: str = Field(default="NOTDEFINED")
    description: str = Field(default="")
    tag: str | None = Field(default=None)

class IfcClassifyComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_ifc_classification"
    classification: dict[str, Any]
    status: str = "success"

class IfcAuditRequest(BaseModel):
    instances: list[dict[str, Any]] = Field(default_factory=list)

class IfcAuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_ifc_audit"
    audit_summary: dict[str, Any]
    status: str = "success"

# 2. Texto 3D (3D Text Tool)
class ThreeDTextGenerateRequest(BaseModel):
    text: str = Field(default="SKETCHBUILD")
    font_family: str = Field(default="Arial")
    height_m: float = Field(default=0.30, ge=0.01)
    extrusion_depth_m: float = Field(default=0.05, ge=0.0)
    is_filled: bool = Field(default=True)
    is_extruded: bool = Field(default=True)
    alignment: str = Field(default="left")
    origin_xyz: tuple[float, float, float] = Field(default=(0.0, 0.0, 0.0))

class ThreeDTextGenerateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_3d_text"
    text_geometry: dict[str, Any]
    status: str = "success"

# 3. Gerador de Relatório (Generate Report)
class GenerateReportRequest(BaseModel):
    instances: list[dict[str, Any]] = Field(default_factory=list)
    scope: str = Field(default="entire_model")
    group_by_definition: bool = Field(default=True)
    selected_instance_ids: list[str] | None = Field(default=None)

class GenerateReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_generate_report"
    report_data: dict[str, Any]
    status: str = "success"

# 4. Ferramenta Eixos (Axes Tool)
class AxesCustomSetRequest(BaseModel):
    origin: tuple[float, float, float] = Field(default=(0.0, 0.0, 0.0))
    x_point: tuple[float, float, float] = Field(default=(1.0, 0.0, 0.0))
    y_point: tuple[float, float, float] = Field(default=(0.0, 1.0, 0.0))

class AxesCustomSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_axes_system"
    axes: dict[str, Any]
    status: str = "success"

class AxesAlignFaceRequest(BaseModel):
    face_vertices: list[tuple[float, float, float]] = Field(default_factory=list)

class AxesAlignFaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_axes_system"
    axes: dict[str, Any]
    status: str = "success"

class AxesResetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_axes_system"
    axes: dict[str, Any]
    status: str = "success"

# 5. Inspetor de Métricas da Entidade (Entity Info)
class EntityInspectEdgeRequest(BaseModel):
    v1: tuple[float, float, float]
    v2: tuple[float, float, float]
    is_smooth: bool = Field(default=False)
    is_soft: bool = Field(default=False)
    is_hidden: bool = Field(default=False)
    tag: str = Field(default="Layer0")

class EntityInspectEdgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_entity_info"
    metrics: dict[str, Any]
    status: str = "success"

class EntityInspectFaceRequest(BaseModel):
    vertices: list[tuple[float, float, float]]
    front_material: str | None = Field(default=None)
    back_material: str | None = Field(default=None)
    tag: str = Field(default="Layer0")

class EntityInspectFaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_entity_info"
    metrics: dict[str, Any]
    status: str = "success"

class EntityInspectSolidRequest(BaseModel):
    definition_name: str = Field(default="Componente Sólido")
    instance_name: str = Field(default="inst_1")
    triangles: list[list[tuple[float, float, float]]]
    tag: str = Field(default="Layer0")
    dynamic_attributes: dict[str, Any] | None = Field(default=None)

class EntityInspectSolidResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_entity_info"
    metrics: dict[str, Any]
    status: str = "success"

# 6. Modos de Edição de Componentes (Component Edit Modes)
class ComponentEditModeRequest(BaseModel):
    active_instance_id: str | None = Field(default=None)
    active_definition_name: str | None = Field(default=None)
    all_instances: list[dict[str, Any]] = Field(default_factory=list)
    hide_rest_of_model: bool = Field(default=False)
    hide_similar_components: bool = Field(default=False)
    fade_rest_of_model: bool = Field(default=True)
    fade_similar_components: bool = Field(default=True)
    fade_opacity: float = Field(default=0.25, ge=0.0, le=1.0)

class ComponentEditModeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_component_edit_mode"
    edit_mode_state: dict[str, Any]
    status: str = "success"

# 7. Unidades e Precisão do Modelo (Model Units & Precision)
class ModelUnitsConfigRequest(BaseModel):
    format_type: str = Field(default="DECIMAL")
    unit_length: str = Field(default="METERS")
    precision_digits: int = Field(default=2, ge=0, le=5)
    enable_length_snapping: bool = Field(default=True)
    length_snap_interval_m: float = Field(default=0.01, ge=0.0001)
    enable_angle_snapping: bool = Field(default=True)
    angle_snap_degrees: float = Field(default=15.0, ge=0.1, le=90.0)

class ModelUnitsConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_model_units"
    units_config: dict[str, Any]
    status: str = "success"

class ModelUnitsFormatRequest(BaseModel):
    length_meters: float
    unit: str = Field(default="METERS")
    precision_digits: int = Field(default=2, ge=0, le=5)

class ModelUnitsFormatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_model_units_format"
    formatted_string: str
    length_meters: float
    status: str = "success"


# ==============================================================================
# OPÇÃO A (PARTE 3): FERRAMENTAS E SUBSISTEMAS NATIVOS ADICIONAIS DO SKETCHUP
# ==============================================================================

# 1. Posicionamento de Textura por Pinos (Texture Position Pin Tool)
class TexturePinTransformRequest(BaseModel):
    face_vertices: list[tuple[float, float, float]]
    red_pin_origin: tuple[float, float] = Field(default=(0.0, 0.0))
    green_pin_scale_rot: tuple[float, float] = Field(default=(1.0, 0.0))
    blue_pin_shear: float = Field(default=0.0)
    yellow_pin_distortion: tuple[float, float] | None = Field(default=None)

class TexturePinTransformResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_texture_pin_mapping"
    mapping: dict[str, Any]
    status: str = "success"

# 2. Colorir por Etiqueta (Color by Tag)
class ColorByTagApplyRequest(BaseModel):
    tags: list[dict[str, Any]] = Field(default_factory=list)
    instances: list[dict[str, Any]] = Field(default_factory=list)
    enabled: bool = Field(default=True)

class ColorByTagApplyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_color_by_tag"
    color_by_tag_result: dict[str, Any]
    status: str = "success"

# 3. Eliminar Não Utilizados (Purge Unused)
class PurgeUnusedRequest(BaseModel):
    component_definitions: list[dict[str, Any]] = Field(default_factory=list)
    instances: list[dict[str, Any]] = Field(default_factory=list)
    materials: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[dict[str, Any]] = Field(default_factory=list)

class PurgeUnusedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_purge_unused"
    purge_result: dict[str, Any]
    status: str = "success"

# 4. Criar Componente com Comportamentos (Make Component Behaviors)
class MakeComponentDefinitionRequest(BaseModel):
    definition_name: str = Field(default="Novo Componente")
    description: str = Field(default="")
    glue_to: str = Field(default="NONE")
    cut_opening: bool = Field(default=False)
    always_face_camera: bool = Field(default=False)
    shadows_face_sun: bool = Field(default=False)
    local_origin: tuple[float, float, float] = Field(default=(0.0, 0.0, 0.0))
    opening_loop_2d: list[tuple[float, float]] | None = Field(default=None)

class MakeComponentDefinitionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_make_component"
    definition: dict[str, Any]
    status: str = "success"

# 5. Seleção Avançada (Advanced Selection)
class AdvancedSelectionRequest(BaseModel):
    operation: str = Field(default="invert")  # 'invert', 'by_tag', 'by_material', 'connected'
    all_entity_ids: list[str] = Field(default_factory=list)
    currently_selected_ids: list[str] = Field(default_factory=list)
    target_tag: str | None = Field(default=None)
    target_material: str | None = Field(default=None)
    instances: list[dict[str, Any]] = Field(default_factory=list)
    seed_face_index: int = Field(default=0)
    faces_vertices: list[list[tuple[float, float, float]]] = Field(default_factory=list)

class AdvancedSelectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_advanced_selection"
    operation: str
    selected_ids: list[str] | list[int]
    total_selected: int
    status: str = "success"

# 6. Geometria Oculta e Objetos Ocultos (Hidden Geometry & Objects)
class HiddenGeometryConfigRequest(BaseModel):
    show_hidden_geometry: bool = Field(default=False)
    show_hidden_objects: bool = Field(default=False)
    instances: list[dict[str, Any]] | None = Field(default=None)
    edges: list[dict[str, Any]] | None = Field(default=None)

class HiddenGeometryConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_hidden_geometry"
    display_state: dict[str, Any]
    status: str = "success"

# 7. Estatísticas do Modelo (Model Info Statistics)
class ModelStatisticsRequest(BaseModel):
    edges_count: int = Field(default=0, ge=0)
    faces_count: int = Field(default=0, ge=0)
    component_definitions_count: int = Field(default=0, ge=0)
    component_instances_count: int = Field(default=0, ge=0)
    groups_count: int = Field(default=0, ge=0)
    guide_lines_count: int = Field(default=0, ge=0)
    guide_points_count: int = Field(default=0, ge=0)
    section_planes_count: int = Field(default=0, ge=0)
    dimensions_count: int = Field(default=0, ge=0)
    texts_count: int = Field(default=0, ge=0)
    materials_count: int = Field(default=0, ge=0)
    tags_count: int = Field(default=1, ge=1)
    scenes_count: int = Field(default=0, ge=0)

class ModelStatisticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_model_statistics"
    statistics: dict[str, Any]
    status: str = "success"


# ============================================================================
# Opção A (Parte 4): Ferramentas Oficiais do SketchUp Desktop (Zero DLL)
# ============================================================================

# 1. Polígono Regular Paramétrico (Polygon Tool)
class RegularPolygonRequest(BaseModel):
    sides_count: int = Field(default=6, ge=3, description="Número de lados do polígono")
    radius_m: float = Field(default=1.0, gt=0, description="Raio em metros")
    radius_mode: str = Field(default="CIRCUMSCRIBED", description="Modo do raio: CIRCUMSCRIBED ou INSCRIBED")
    center_xyz: tuple[float, float, float] = Field(default=(0.0, 0.0, 0.0), description="Centro do polígono")
    normal_xyz: tuple[float, float, float] = Field(default=(0.0, 0.0, 1.0), description="Vetor normal do plano")

class RegularPolygonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_regular_polygon"
    polygon: dict[str, Any]
    status: str = "success"

# 2. Ferramenta Mão Livre (Freehand Tool)
class FreehandCurveRequest(BaseModel):
    raw_points_xyz: list[tuple[float, float, float]] = Field(..., min_length=2, description="Pontos brutos da curva desenhada")
    tolerance_m: float = Field(default=0.02, ge=0.0001, description="Tolerância de simplificação Ramer-Douglas-Peucker")
    auto_close: bool = Field(default=False, description="Tentar fechar a curva gerando face plana")
    close_threshold_m: float = Field(default=0.1, ge=0.001, description="Distância máxima entre pontas para fechamento")

class FreehandCurveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_freehand_curve"
    curve: dict[str, Any]
    status: str = "success"

# 3. Inverter Faces e Orientar Faces (Reverse & Orient Faces)
class ReverseOrientFacesRequest(BaseModel):
    mode: str = Field(default="REVERSE", description="Modo: 'REVERSE' ou 'ORIENT'")
    faces: list[dict[str, Any]] = Field(..., description="Lista de dicionários de faces com vértices e normais")
    selected_face_indices: list[int] = Field(default_factory=list, description="Índices das faces a inverter em modo REVERSE")
    reference_face_index: int = Field(default=0, ge=0, description="Índice da face de referência em modo ORIENT")

class ReverseOrientFacesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_reverse_orient_faces"
    result: dict[str, Any]
    status: str = "success"

# 4. Dolly, FOV e Lente Fotográfica (Camera Dolly & Lens Engine)
class DollyFovLensRequest(BaseModel):
    operation: str = Field(default="PARSE_VCB", description="'PARSE_VCB', 'FOV_TO_FOCAL', 'FOCAL_TO_FOV', 'APPLY_DOLLY'")
    vcb_input: str | None = Field(default=None, description="Texto digitado no VCB (ex: '50mm', '35 deg')")
    fov_degrees: float | None = Field(default=None, description="Campo de visão em graus")
    focal_length_mm: float | None = Field(default=None, description="Distância focal em mm (35mm equiv)")
    camera_eye_xyz: tuple[float, float, float] | None = Field(default=None, description="Posição da câmera [x, y, z]")
    camera_target_xyz: tuple[float, float, float] | None = Field(default=None, description="Ponto focal da câmera [x, y, z]")
    dolly_delta_m: float = Field(default=1.0, description="Deslocamento ao longo do eixo de visão em metros")
    dolly_mode: str = Field(default="KEEP_TARGET", description="'KEEP_TARGET' ou 'MOVE_TARGET'")

class DollyFovLensResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_dolly_fov_lens"
    result: dict[str, Any]
    status: str = "success"

# 5. Interseccionar Faces (Intersect Faces)
class IntersectFacesRequest(BaseModel):
    context_mode: str = Field(default="WITH_MODEL", description="'WITH_MODEL' ou 'WITH_SELECTION'")
    faces_set_a: list[dict[str, Any]] = Field(..., description="Conjunto principal de faces com vértices 3D")
    faces_set_b: list[dict[str, Any]] | None = Field(default=None, description="Conjunto secundário para WITH_SELECTION")

class IntersectFacesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_intersect_faces"
    intersection: dict[str, Any]
    status: str = "success"

# 6. Bloqueio de Eixos e Inferência (Axis Lock & Inference Engine)
class AxisLockInferenceRequest(BaseModel):
    arrow_key: str = Field(default="RIGHT", description="'RIGHT' (X), 'LEFT' (Y), 'UP' (Z), 'DOWN' (Ref), 'NONE'")
    cursor_point_xyz: tuple[float, float, float] | None = Field(default=None, description="Posição 3D do cursor")
    origin_point_xyz: tuple[float, float, float] | None = Field(default=(0.0, 0.0, 0.0), description="Origem da linha de inferência")
    custom_direction_xyz: tuple[float, float, float] | None = Field(default=None, description="Direção customizada para seta para baixo")

class AxisLockInferenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_axis_lock_inference"
    inference: dict[str, Any]
    status: str = "success"

# 7. Configurações de Solo e Céu dos Estilos (Ground & Sky Style Settings)
class GroundSkyStyleRequest(BaseModel):
    background_color: str | None = Field(default=None, description="Cor de fundo hex (ex: '#FFFFFF')")
    sky_enabled: bool | None = Field(default=None, description="Habilita cúpula de céu")
    sky_color: str | None = Field(default=None, description="Cor do céu hex (ex: '#C3DDF7')")
    ground_enabled: bool | None = Field(default=None, description="Habilita plano de solo")
    ground_color: str | None = Field(default=None, description="Cor do solo hex (ex: '#C7BEB3')")
    ground_transparency_pct: int | None = Field(default=None, ge=0, le=100, description="Transparência do solo de 0 a 100%")
    show_ground_from_below: bool | None = Field(default=None, description="Exibe plano de solo visto por baixo")

class GroundSkyStyleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_ground_sky_style"
    style: dict[str, Any]
    status: str = "success"

# -----------------------------------------------------------------------------
# OPÇÃO A (PARTE 5): FERRAMENTAS NATIVAS OFICIAIS DO SKETCHUP DESKTOP
# -----------------------------------------------------------------------------

# 1. Carimbo de Terreno (Stamp Tool)
class StampTerrainRequest(BaseModel):
    tin_vertices: list[list[float]] = Field(description="Lista de vértices [x, y, z] da malha TIN")
    tin_triangles: list[list[int]] = Field(description="Lista de triângulos [i0, i1, i2] da malha TIN")
    footprint_polygon: list[list[float]] = Field(description="Polígono da pegada da construção [[x, y], ...]")
    target_elevation: float = Field(default=0.0, description="Cota Z do platô nivelado")
    transition_width: float = Field(default=1.5, ge=0.01, description="Largura do talude/saia de transição em metros")

class StampTerrainResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_stamp_terrain"
    stamp: dict[str, Any]
    status: str = "success"

# 2. Projetar Linhas no Terreno (Drape Tool)
class DrapePathRequest(BaseModel):
    tin_vertices: list[list[float]] = Field(description="Lista de vértices [x, y, z] da malha TIN")
    tin_triangles: list[list[int]] = Field(description="Lista de triângulos da malha TIN")
    path_points_2d: list[list[float]] = Field(description="Pontos 2D [x, y] da polilinha a ser projetada")
    subdivision_steps: int = Field(default=4, ge=1, le=32, description="Passos de subdivisão por segmento")

class DrapePathResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_drape_path"
    drape: dict[str, Any]
    status: str = "success"

# 3. Preenchimento de Seção e Inversão (Section Cut Fill & Flip)
class SectionCutFillRequest(BaseModel):
    solid_vertices: list[list[float]] = Field(description="Vértices do sólido cortado")
    solid_triangles: list[list[int]] = Field(description="Triângulos do sólido cortado")
    plane_coeffs: list[float] = Field(default=[0.0, -1.0, 0.0, 0.0], description="Coeficientes do plano [a, b, c, d]")
    flip_direction: bool = Field(default=False, description="Inverte o sentido de visualização do corte")
    fill_color_hex: str = Field(default="#333333", description="Cor hex da tampa de preenchimento")

class SectionCutFillResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_section_cut_fill"
    cut_fill: dict[str, Any]
    status: str = "success"

# 4. Suavizar / Alisar Arestas (Soft/Smooth Edges)
class SoftSmoothEdgesRequest(BaseModel):
    vertices: list[list[float]] = Field(description="Vértices da malha [x, y, z]")
    triangles: list[list[int]] = Field(description="Triângulos da malha [i0, i1, i2]")
    max_angle_deg: float = Field(default=35.0, ge=0.0, le=180.0, description="Ângulo diedro limite em graus")
    soften_coplanar: bool = Field(default=True, description="Suaviza arestas entre faces coplanares")
    smooth_normals: bool = Field(default=True, description="Gera normais interpoladas para Gouraud shading")

class SoftSmoothEdgesResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_soft_smooth_edges"
    soft_smooth: dict[str, Any]
    status: str = "success"

# 5. Dividir Aresta em N Segmentos (Edge Divide Tool)
class EdgeDivideRequest(BaseModel):
    start_point: list[float] = Field(description="Ponto inicial da aresta [x, y, z]")
    end_point: list[float] = Field(description="Ponto final da aresta [x, y, z]")
    num_segments: int | str = Field(default=4, description="Quantidade de segmentos ou texto do VCB (ex: '6s')")

class EdgeDivideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_edge_divide"
    divide: dict[str, Any]
    status: str = "success"

# 6. Push/Pull com Nova Face Inicial (Ctrl + Push/Pull)
class PushPullCreateFaceRequest(BaseModel):
    face_vertices: list[list[float]] = Field(description="Vértices do polígono plano 3D")
    distance_m: float = Field(description="Distância de extrusão em metros")
    create_new_face: bool = Field(default=True, description="Modificador Ctrl ativo: preserva face base")

class PushPullCreateFaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_push_pull_create_face"
    extrude: dict[str, Any]
    status: str = "success"

# 7. Conjuntos de Propriedades BIM IFC (IFC Property Sets - Psets)
class BimIfcPropertySetRequest(BaseModel):
    instance_id: str = Field(description="ID da instância no modelo")
    ifc_class: str = Field(default="IfcBeam", description="Classe oficial IFC (ex: IfcBeam, IfcWall)")
    pset_name: str = Field(default="Pset_BeamCommon", description="Nome do conjunto de propriedades")
    properties: dict[str, Any] = Field(default_factory=dict, description="Dicionário de propriedades e valores")
    schema_version: str = Field(default="IFC4", description="Versão do schema: IFC2X3 ou IFC4")
    start_step_id: int = Field(default=500, description="ID inicial para linhas STEP")

class BimIfcPropertySetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    entity_type: str = "sketchup_native_bim_ifc_pset"
    pset: dict[str, Any]
    status: str = "success"


