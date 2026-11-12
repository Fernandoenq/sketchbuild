"""Schemas das rotas de desenho (F2). Unidade: polegadas, como o núcleo de topologia."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Ponto = tuple[float, float, float]


class DrawRequest(BaseModel):
    ferramenta: Literal["linha", "retangulo", "circulo", "poligono", "arco", "mao_livre",
                      "arco_3pontos", "arco_corda", "setor", "fatia", "bezier"]
    pontos: list[Ponto] | None = None  # linha, mao_livre
    p0: Ponto | None = None  # retangulo
    p1: Ponto | None = None
    p2: Ponto | None = None  # arco_3pontos
    flecha: float | None = None  # arco_corda
    tolerancia: float | None = Field(default=None, ge=0)  # mao_livre (RDP)
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
    tags: dict[str, dict[str, Any]] = Field(default_factory=dict)  # nome -> {visivel}
    tag_faces: dict[str, str] = Field(default_factory=dict)  # face -> tag
    tag_arestas: dict[str, str] = Field(default_factory=dict)  # aresta -> tag
    suaves: dict[str, int] = Field(default_factory=dict)  # aresta -> bits (0x08 suave, 0x10 lisa)
    normais_suaves: dict[str, dict[str, list[float]]] = Field(default_factory=dict)  # face -> vértice -> normal lisa
    guias: dict[str, dict[str, Any]] = Field(default_factory=dict)
    secoes: dict[str, list[float]] = Field(default_factory=dict)
    textos: dict[str, dict[str, Any]] = Field(default_factory=dict)
    cotas: dict[str, dict[str, Any]] = Field(default_factory=dict)
    uv: dict[str, list[float]] = Field(default_factory=dict)  # face -> matriz de posicionamento da textura
    cenas: list[dict[str, Any]] = Field(default_factory=list)
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
    textura_base64: str | None = None  # imagem (PNG/JPEG) do material; precisa de `material`
    textura_nome: str | None = None  # nome do arquivo gravado no .skp (ex.: tijolo.png)
    escala: tuple[float, float] = (1.0, 1.0)  # xScale/yScale da textura (unidade do SketchUp, nao validada)


class TagRequest(BaseModel):
    nome: str | None = None  # None com `limpar` devolve as entidades a Layer0
    visivel: bool | None = None  # cria a tag (ou muda a visibilidade se ja existe)
    faces: list[int] = Field(default_factory=list)
    arestas: list[int] = Field(default_factory=list)
    limpar: bool = False  # tira as entidades da tag (volta a Layer0)


class SoftenRequest(BaseModel):
    arestas: list[int] = Field(default_factory=list)  # vazio com `angulo` = o modelo todo
    angulo: float | None = Field(default=None, ge=0, le=180)  # suaviza arestas entre faces com ate esse angulo
    suave: bool = True
    lisa: bool = True
    limpar: bool = False  # tira suave e lisa das arestas dadas


class SelecaoRequest(BaseModel):
    acao: Literal["tudo", "inverter", "arestas_das_faces", "faces_das_arestas", "conectados", "tag", "material",
                  "janela", "cruzamento"]
    faces: list[int] = Field(default_factory=list)  # seleção atual (inverter, conectados, ...)
    arestas: list[int] = Field(default_factory=list)
    nome: str | None = None  # tag ou material
    matriz: list[float] | None = Field(default=None, min_length=16, max_length=16)  # projeção 4x4, linha a linha
    retangulo: list[float] | None = Field(default=None, min_length=4, max_length=4)  # x0, y0, x1, y1 na tela


class SelecaoResponse(BaseModel):
    faces: list[int]
    edges: list[int]
    vertices: list[int]


class GuiaRequest(BaseModel):
    tipo: str = Field(pattern="^(ponto|linha|secao|apagar)$")
    p: tuple[float, float, float] | None = None  # ponto da guia, inicio da linha ou ponto do plano de secao
    alvo: tuple[float, float, float] | None = None  # linha finita ate este ponto
    direcao: tuple[float, float, float] | None = None  # linha infinita nesta direcao; plano de secao: a normal
    id: int | None = None  # tipo=apagar


class NotaRequest(BaseModel):
    tipo: str = Field(pattern="^(texto|cota|apagar)$")
    texto: str | None = None  # texto livre (obrigatorio); na cota vazio = o SketchUp mostra a medida
    p: tuple[float, float, float] | None = None  # texto: ponto; cota: ponto inicial
    fim: tuple[float, float, float] | None = None  # cota: ponto final
    normal: tuple[float, float, float] | None = None  # cota: normal do plano (padrao: escolhida pela direcao)
    eixo_x: tuple[float, float, float] | None = None  # cota: eixo X do plano (padrao: direcao da cota)
    desloc: tuple[float, float] = (0.0, 0.0)  # cota: deslocamento do texto no plano
    fonte: int | None = Field(default=None, ge=0, le=255)  # cota: id de fonte do modelo (2 ou 3)
    texto_3d: bool = False  # cota: texto 3D (SUDimensionSetText3D)
    alinhamento_h: int | None = Field(default=None, ge=0, le=2)  # cota: alinhamento horizontal do texto (0, 1, 2); sobrescreve desloc[0]
    seta: int = Field(default=0, ge=0)
    tipo_chamada: int = Field(default=0, ge=0, le=2)  # texto: tipo da linha de chamada
    vetor: tuple[float, float, float] | None = None  # texto: vetor da linha de chamada
    cor: tuple[int, int, int] | tuple[int, int, int, int] | None = None  # texto: cor rgb[a] 0-255 (uma so por modelo)
    tela: tuple[float, float] = (0.5, 0.5)  # texto: posicao na tela 0-1 (so com tipo_chamada 0)
    fonte_nova: tuple[str, bool, bool, int] | None = None  # texto: (nome, negrito, italico, pontos 1-1000)
    id: int | None = None  # tipo=apagar (texto ou cota)


class ComportamentoRequest(BaseModel):
    definicao: int | None = None  # None = a definicao ativa (componente em que se entrou)
    face_me: bool = False
    corta_abertura: bool = False
    sombra_sol: bool = False
    snap: int = Field(default=0, ge=0, le=4)  # 0 nenhum, 1 qualquer, 2 horizontal, 3 vertical, 4 inclinado


class PosicionarRequest(BaseModel):
    faces: list[int] = Field(min_length=1)
    tamanho: float | None = Field(default=None, gt=0)  # polegadas por repeticao da textura; None com `limpar`
    u0: float = 0.0
    v0: float = 0.0
    graus: float = 0.0
    limpar: bool = False


class CenaRequest(BaseModel):
    nome: str = Field(min_length=1)
    descricao: str = ""
    animar: bool = True
    olho: tuple[float, float, float] | None = None  # camera da cena (precisa de alvo)
    alvo: tuple[float, float, float] | None = None
    cima: tuple[float, float, float] = (0.0, 0.0, 1.0)


class PaintResponse(BaseModel):
    pintadas: dict[str, list[str | None]]  # face -> [frente, verso]
    materiais: dict[str, dict[str, Any]]
