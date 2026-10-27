# SketchBuild

Editor/visualizador 3D **standalone** de arquivos `.skp`: lê geometria real
(vértices, normais, árvore de componentes) via `ctypes` contra a C API
pública oficial da Trimble (`SketchUpAPI.dll`) -- sem precisar do SketchUp
Desktop instalado nem aberto -- e renderiza num visualizador web com
Three.js/WebGL.

> Histórico completo de engenharia reversa -- incluindo a investigação de
> crash com WinDbg/`cdb.exe` que revelou a causa raiz real (uma regressão do
> `ctypes` no Python 3.14, não uma limitação da DLL) -- está em
> [`REVERSE_ENGINEERING_NOTES.md`](./REVERSE_ENGINEERING_NOTES.md), seções
> 15-18.

## Visão geral e arquitetura

Sidecar Pattern em três camadas desacopladas:

```
┌──────────────────────┐   HTTP/JSON   ┌────────────────────────┐   ctypes (in-process)   ┌───────────────────┐
│ Frontend (Three.js)   │ ◄───────────► │ Backend (FastAPI)       │ ───────────────────────► │ Core (SketchUpAPI  │
│ frontend/              │               │ route→controller→       │                          │ .dll via ctypes)    │
│ render + OrbitControls │               │ service→repository      │                          │ core/su_api.py      │
└──────────────────────┘               └────────────────────────┘                          └───────────────────┘
```

- **Core** (`core/su_api.py`, `core/su_types.py`, `core/mesh_extractor.py`) --
  binding `ctypes` fino sobre a `SketchUpAPI.dll` oficial (SDK documentado
  publicamente pela Trimble). Abre um `.skp`, triangula cada face via
  `SUMeshHelper` e percorre a árvore `Model → Entities → {Faces,
  ComponentInstances}` recursivamente, devolvendo geometria deduplicada por
  definição + instâncias com matriz 4x4 em espaço de mundo.
- **Backend** (`app/`) -- sidecar FastAPI, camadas `route → controller →
  service → repository`. O `repository` (`app/repositories/
  skp_engine_repository.py`) é o único lugar que importa `core.*`/`ctypes`;
  chama o Core **in-process** (sem socket -- diferente da ponte Ruby
  histórica, ver seção abaixo), despachado numa threadpool pra não bloquear
  o event loop durante o parse.
- **Frontend** (`frontend/`) -- página estática (Three.js via CDN, módulos
  ES), servida pelo próprio FastAPI (`StaticFiles`). `fetch` no endpoint da
  cena, monta uma `BufferGeometry` por definição e um `Mesh` por instância
  (matriz aplicada direto via `Matrix4.fromArray`), com `OrbitControls` pra
  navegação e `TransformControls` pra editar a instância selecionada
  (clique pra selecionar via raycasting, W/E/R trocam mover/girar/escalar).

### Por que isso não era óbvio

A primeira tentativa de chamar `SUModelCreateFromFileWithStatus`/
`SUModelCreateFromBufferWithStatus` via `ctypes` crashava o processo
(`STATUS_ACCESS_VIOLATION`). A investigação inicial (decompilação estática
com Ghidra/REA) concluiu, incorretamente, que o crash estava dentro do
parser interno do formato `.skp` na própria DLL.

A investigação foi refeita com uma ferramenta de runtime (WinDbg/`cdb.exe`),
analisando os crash dumps reais (`!analyze -v`) e reproduzindo o crash ao
vivo. Resultado: o access violation ocorre **inteiramente dentro do próprio
`ctypes`/CPython** (`python314!PyObject_IsInstance`), **antes** da chamada
nativa à DLL ser executada -- nenhum frame da `SketchUpAPI.dll` aparece na
pilha. É uma regressão isolada do `ctypes` no Python 3.14.3. Rodando
exatamente o mesmo código, com os mesmos argumentos, contra a mesma DLL, em
**Python 3.12**: funciona perfeitamente. A `SketchUpAPI.dll` nunca teve
nenhuma limitação real.

## Stack tecnológica

| Camada | Tecnologia |
|---|---|
| Core/motor | Python 3.12 + `ctypes` (binding direto contra `SketchUpAPI.dll`) |
| SDK nativo | C API pública da Trimble (`SketchUpAPI.dll`, SDK oficial de extensões) |
| Backend | FastAPI (sidecar, camadas route→controller→service→repository) |
| Frontend | Three.js/WebGL (ES modules via CDN, sem build step) |
| Diagnóstico/validação | WinDbg + `cdb.exe` (análise de crash dump e reprodução ao vivo) |

## Requisito de versão do Python

**Python 3.12 é obrigatório** (processo do backend inteiro, não só scripts
avulsos). O Python 3.14.3 tem uma regressão confirmada no módulo `ctypes`
que crasha o processo nesta chamada específica (ver
`REVERSE_ENGINEERING_NOTES.md`, seção 15). O arquivo `.python-version` já
fixa isso para ferramentas como `pyenv`. Ao rodar manualmente no Windows, use
`py -3.12`.

## Estrutura de pastas

```
sketchbuild/
├── core/
│   ├── su_types.py                 # tipos ctypes (SU*Ref, SUTransformation, su_check)
│   ├── su_api.py                   # binding ctypes contra SketchUpAPI.dll
│   └── mesh_extractor.py           # percorre a arvore e monta o DTO (definitions+instances)
├── app/                             # backend FastAPI (camadas)
│   ├── main.py                      # registra routers + serve frontend/ como estatico
│   ├── routes/scene_router.py       # POST /api/v1/scene/open
│   ├── controllers/scene_controller.py
│   ├── services/scene_service.py
│   ├── repositories/skp_engine_repository.py  # unico lugar que chama core/
│   ├── schemas/scene.py             # DefinitionDTO, InstanceDTO, SceneResponse
│   └── routes/model_router.py , ruby_bridge/ , bridge_*.py  # arquitetura alternativa (ver abaixo)
├── frontend/
│   ├── index.html
│   └── src/{main,sceneBuilder,api}.js
├── main.py                          # CLI standalone (sem FastAPI): extrai e resume um .skp
├── crash_analysis/                  # logs do WinDbg (!analyze -v) dos crashes investigados
├── minimal_ctypes_repro*.py , live_crash_test*.py  # scripts da investigacao do bug do ctypes
└── REVERSE_ENGINEERING_NOTES.md     # log completo de engenharia reversa e decisoes
```

## Instalação e execução

### Pré-requisitos
- Python 3.12 (ver seção acima), `pip install -r requirements.txt`.
- SketchUp 2026 instalado (só para ter a `SketchUpAPI.dll` no disco -- **não**
  precisa estar aberto).

### Visualizador web (produto principal)

```bash
py -3.12 -m uvicorn app.main:app --reload --port 8000
```

Abra `http://127.0.0.1:8000/`, informe o caminho absoluto de um `.skp` no
campo e clique em **Abrir**. A cena é extraída pelo Core e renderizada no
Three.js (arraste pra orbitar, scroll pra zoom).

### CLI standalone (sem FastAPI)

```bash
py -3.12 main.py                            # so inicializa e mostra a versao da API
py -3.12 main.py "caminho\para\arquivo.skp"  # abre, resume entidades e extrai a malha
```

Saída esperada:
```
SketchUpAPI carregada. Versao da API: 14.2
Modelo aberto: caminho\para\arquivo.skp
  faces: 0
  edges: 0
  instances: 1
Malha extraida: 2 definicoes, 2 instancias, 9138 vertices, 3046 triangulos
```

## Documentação dos endpoints

| Método | Path | Descrição |
|---|---|---|
| POST | `/api/v1/scene/open` | Abre um `.skp` via motor `ctypes` (standalone), inicia uma sessão de edição e devolve `{model_path, definitions[], instances[]}` -- geometria + matrizes de transformação prontas pro Three.js. |
| PATCH | `/api/v1/scene/instances/{instance_id}/transform` | Aplica uma nova transformação (mundial, column-major) a uma instância da sessão aberta -- só em memória, ainda não grava em disco. |
| POST | `/api/v1/scene/save` | Grava o modelo editado em disco (`path` omitido = sobrescreve o arquivo aberto). |
| GET | `/health` | Saúde do sidecar + ping na ponte Ruby (arquitetura alternativa, ver abaixo). |
| GET, POST | `/api/v1/models/*` | Arquitetura alternativa (Ruby bridge) -- ver seção abaixo. |

### `POST /api/v1/scene/open`

```jsonc
// Request
{ "path": "C:/.../arquivo.skp" }

// Response 200
{
  "model_path": "C:/.../arquivo.skp",
  "definitions": [
    { "definition_id": "def_...", "name": "...", "vertices": [...], "normals": [...], "indices": [...] }
  ],
  "instances": [
    { "instance_id": "inst_0", "definition_id": "def_...", "transform": [ /* 16 floats, column-major */ ] }
  ]
}
```
Erros: `400` (caminho inválido/não é `.skp`/não existe), `502` (falha do
motor `ctypes` ao processar o arquivo -- ver `SceneParseError`). Abrir um
novo arquivo fecha a sessão de edição anterior, se houver.

### `PATCH /api/v1/scene/instances/{instance_id}/transform`

```jsonc
// Request
{ "transform": [ /* 16 floats, column-major, espaco de MUNDO -- mesma convencao do campo transform do DTO */ ] }

// Response 200
{ "instance_id": "inst_1", "applied": true }
```
O backend converte mundo→local (relativo ao pai imediato) antes de chamar
`SUComponentInstanceSetTransform` -- ver `REVERSE_ENGINEERING_NOTES.md`
seção 18.2. Erro: `409` (nenhuma sessão aberta, instância não encontrada, ou
falha ao aplicar -- ver `SceneSessionError`).

### `POST /api/v1/scene/save`

```jsonc
// Request
{ "path": null }  // ou um caminho absoluto -- null/omitido sobrescreve o arquivo aberto

// Response 200
{ "saved": true, "path": "C:/.../arquivo.skp" }
```
Erro: `409` (nenhuma sessão aberta ou falha ao salvar).

## API em código (sem HTTP)

```python
from core.su_api import SketchUpAPI
from core.mesh_extractor import extract_scene

api = SketchUpAPI()
with api:  # SUInitialize()/SUTerminate() automáticos
    with api.open_model("arquivo.skp") as modelo:
        scene = extract_scene(api, modelo)  # {"definitions": [...], "instances": [...]}
```

## Pendências conhecidas

- Edição de instâncias aninhadas: se uma instância editada tiver filhas
  aninhadas na árvore, o `parent_world` delas não é recalculado em cascata
  depois da edição nesta fase -- só edição de instâncias sem filhos
  aninhados editados na mesma sessão é garantidamente correta (ver
  `REVERSE_ENGINEERING_NOTES.md` seção 18.2/18.7).
- O bug do `ctypes` no Python 3.14 ainda não foi relatado upstream
  (`python/cpython`) -- falta isolar um repro público mínimo que não dependa
  da `SketchUpAPI.dll` (o repro feito só com `ctypes.CFUNCTYPE`, sem a DLL
  real, não reproduziu o crash).
- `main.py` (CLI) continua usando `extract_scene()` sem sessão de edição --
  a edição só existe via API/frontend por enquanto.
- Sessão de edição é um singleton em nível de módulo (sem suporte a
  múltiplos usuários/sessões concorrentes) -- aceitável porque é uma
  ferramenta desktop de usuário único.

## Arquitetura alternativa (histórico de design) -- Sidecar Python + Ruby Bridge

Antes de confirmar que o parser `ctypes` standalone funciona, o projeto
passou por uma fase em que a estratégia era evitar `ctypes` por completo e
automatizar o SketchUp através de um bridge Ruby rodando *dentro* do
processo gráfico já aberto (`ruby_bridge/sketchup_bridge.rb`, TCP
`127.0.0.1:9876`) exposto pelos endpoints `/api/v1/models/*` deste mesmo
backend. Essa arquitetura continua no repositório, funcionando, e é útil
para casos de uso diferentes (ex.: automação de uma sessão do SketchUp já em
uso por um usuário) -- mas **não é mais necessária só para ler um `.skp`**,
que é o que o Core deste README já faz sozinho, sem o SketchUp aberto.
Detalhes da arquitetura do sidecar, protocolo, endpoints e decisões
continuam documentados em `REVERSE_ENGINEERING_NOTES.md`, seções 10-12.
