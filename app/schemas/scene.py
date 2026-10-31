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
