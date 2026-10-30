from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class OpenModelRequest(BaseModel):
    """Entrada de POST /models/open."""

    path: str = Field(
        ...,
        min_length=1,
        description="Caminho absoluto de um arquivo .skp no disco local do SketchUp.",
        examples=[r"C:\Users\<usuario>\Desktop\modelo.skp"],
    )


class OpenModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    opened: bool
    path: str


class ModelSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    path: str
    guid: str
    faces: int
    edges: int
    groups: int
    component_instances: int
    number_of_definitions: int


class CloseModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    closed: bool


class PingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pong: bool
    sketchup_version: str
    ruby_version: str
    bridge_port: int


class InspectBinaryRequest(BaseModel):
    path: str = Field(
        ...,
        min_length=1,
        description="Caminho absoluto de um arquivo .skp para inspeção binária nativa.",
    )


class InspectBinaryResponse(BaseModel):
    num_vertices: int
    largura_cm: float
    profundidade_cm: float
    altura_cm: float
    min_pt_cm: list[float]
    max_pt_cm: list[float]
    is_empty: bool


class MaterialInfoResponse(BaseModel):
    name: str
    color: list[int]
    opacity: float
    hasTexture: bool
    texturePath: str | None = None
    xScale: float
    yScale: float
    metalness: float
    roughness: float


class ComponentInstanceResponse(BaseModel):
    definition_id: int | None = None
    definition_name: str
    translation_cm: list[float]
    matrix_4x4: list[float]


class ComponentDefinitionResponse(BaseModel):
    id: int
    name: str
    instances_count: int


class HierarchyResponse(BaseModel):
    definitions: list[ComponentDefinitionResponse] = Field(default_factory=list)
    instances: list[ComponentInstanceResponse] = Field(default_factory=list)
    total_definitions: int = 0
    total_instances: int = 0


class ExtractMeshBinaryResponse(BaseModel):
    vertices: list[float]
    normals: list[float]
    uvs: list[float] = Field(default_factory=list)
    indices: list[int]
    materials: dict[str, MaterialInfoResponse] = Field(default_factory=dict)
    face_materials: list[str] = Field(default_factory=list)
    num_faces: int
    num_vertices: int
    bounds: InspectBinaryResponse
    hierarchy: HierarchyResponse | None = None


class HealthResponse(BaseModel):
    status: str
    bridge: PingResponse | None = None
    detail: str | None = None
