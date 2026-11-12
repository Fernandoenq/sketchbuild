"""Schemas das rotas de desenho (F2). Unidade: polegadas, como o núcleo de topologia."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Ponto = tuple[float, float, float]


class DrawRequest(BaseModel):
    ferramenta: Literal["linha", "retangulo", "circulo", "poligono", "arco", "mao_livre"]
    pontos: list[Ponto] | None = None  # linha, mao_livre
    p0: Ponto | None = None  # retangulo
    p1: Ponto | None = None
    centro: Ponto | None = None  # circulo, poligono, arco
    raio: float | None = Field(default=None, gt=0)
    normal: Ponto = (0.0, 0.0, 1.0)
    lados: int | None = Field(default=None, ge=3, le=360)
    circunscrito: bool | None = None
    ang_ini: float | None = None
    ang_fim: float | None = None
    fechar: bool | None = None


class DrawDelta(BaseModel):
    added: dict[str, Any]
    changed: dict[str, Any]
    removed: list[int]


class DrawResponse(BaseModel):
    vertices: DrawDelta
    edges: DrawDelta
    faces: DrawDelta
    counts: dict[str, int]


class DrawStateResponse(BaseModel):
    vertices: dict[str, Any]
    edges: dict[str, Any]
    faces: dict[str, Any]
    pintura: dict[str, list[str | None]] = Field(default_factory=dict)  # face -> [frente, verso]
    materiais: dict[str, dict[str, Any]] = Field(default_factory=dict)
    counts: dict[str, int]
    historico: dict[str, bool] = Field(default_factory=dict)


class PushPullRequest(BaseModel):
    face_id: int
    distancia: float  # polegadas, positivo = na direcao da normal da face
    criar_nova: bool = False  # Ctrl: mantem a face original e cria uma nova


class EditRequest(BaseModel):
    operacao: Literal["mover", "rotacionar", "escalar"]
    vertices: list[int] = Field(default_factory=list)
    arestas: list[int] = Field(default_factory=list)
    faces: list[int] = Field(default_factory=list)
    vetor: Ponto | None = None  # mover (polegadas)
    angulo: float | None = None  # rotacionar (graus)
    eixo: Ponto = (0.0, 0.0, 1.0)
    centro: Ponto | None = None  # rotacionar, escalar (padrao: centro da selecao)
    fator: float | None = Field(default=None, gt=0)  # escalar uniforme
    fatores: Ponto | None = None  # escalar por eixo


class OffsetRequest(BaseModel):
    face_id: int
    distancia: float  # polegadas, negativo = para dentro


class FollowMeRequest(BaseModel):
    face_id: int
    arestas: list[int]


class IntersectRequest(BaseModel):
    faces: list[int] | None = None  # None = todas as faces da definicao ativa


class GroupRequest(BaseModel):
    faces: list[int] = Field(default_factory=list)
    arestas: list[int] = Field(default_factory=list)
    tipo: Literal["grupo", "componente"] = "grupo"
    nome: str | None = None


class InstanceRequest(BaseModel):
    instancia: int
    transformacao: list[float] | None = Field(default=None, min_length=16, max_length=16)


class SceneSummaryResponse(BaseModel):
    ativa: int
    caminho: list[int]
    definicoes: dict[str, Any]
    instancias: dict[str, Any]


class SaveDrawRequest(BaseModel):
    path: str
    sobrescrever: bool = False  # so com confirmacao explicita do usuario


class SaveDrawResponse(BaseModel):
    path: str
    vertices: int
    arestas: int
    faces: int
    bytes: int


class PaintRequest(BaseModel):
    faces: list[int] = Field(min_length=1)
    material: str | None = None  # nome; aplica na frente (ou no verso, se verso=True)
    rgb: tuple[int, int, int] | None = None  # cria/atualiza o material `material`
    alpha: int = Field(default=255, ge=0, le=255)
    verso: bool = False
    limpar: bool = False  # volta ao padrao (frente, ou verso se verso=True)


class PaintResponse(BaseModel):
    pintadas: dict[str, list[str | None]]  # face -> [frente, verso]
    materiais: dict[str, dict[str, Any]]
