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
