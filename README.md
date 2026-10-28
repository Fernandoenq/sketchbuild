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
> 15-28.

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
  Visual no padrão **SketchUp Pro Desktop Classic** (cinzas corporativos,
  toolbar superior fixa, *Default Tray* lateral) -- ver seção abaixo.
  Painel **Outliner** (`frontend/src/outliner.js`) mostra a árvore de
  componentes remontada client-side a partir do campo `parent_instance_id`
  de cada instância, com seleção sincronizada nos dois sentidos (árvore ↔
  3D). Painel **Entity Info** mostra/edita posição (X/Y/Z) e rotação
  numéricas da instância selecionada, sincronizado em tempo real com o
  gizmo. Botões de **Vistas Padrão** (Topo/Frente/Lateral/Isométrica na
  toolbar de ícones; as 7 vistas reais -- incluindo Inferior/Posterior/
  Esquerda -- no menu Câmera) reposicionam a câmera instantaneamente com
  base na bounding box do modelo carregado (`setStandardView()` em
  `main.js`).

### Barra de menu real (Arquivo/Editar/Visualizar/Câmera)

`#menu-bar` replica a barra de menu de texto do SketchUp Desktop real
(9 itens: Arquivo, Editar, Visualizar, Câmera, Desenho, Ferramentas,
Janela, Extensões, Ajuda), catalogada via clique real no SketchUp 2026
rodando na máquina (não por suposição -- ver
`REVERSE_ENGINEERING_NOTES.md` seções 26 e 27). Hoje **4 dos 9** menus
têm dropdown funcional:
- **Arquivo**: Novo/Abrir/Salvar/Salvar como/Exportar Modelo 3D (.obj).
- **Editar**: Excluir (equivalente real de Del, ver seção 26); Criar
  grupo (`SUGroupCreate`/`SUEntitiesAddGroup` reais, cria o retângulo
  novo dentro de um Grupo em vez de solto na raiz -- ver seção 28.18).
- **Visualizar**: Eixos/Sombras/Névoa (toggles), Estilo de aresta >
  Bordas (overlay de contorno preto por malha), Estilo de face (5 modos:
  Sombreado com texturas/Sombreado/Monocromático/Grade de linhas/Raios X
  -- muta a `MeshStandardMaterial` compartilhada por toda a cena em vez
  de reconstruir).
- **Câmera**: Exibições padrão (as 7 vistas reais -- antes só 4
  existiam), Projeção paralela/Perspectiva (aproximação de "projeção
  paralela falsa" via FOV estreito + distância compensada, não é uma
  `OrthographicCamera` real), Campo de visão (`window.prompt`).

Dentro de cada dropdown, só os itens implementados ficam clicáveis; o
resto fica `.disabled` (cinza, sem clique) -- igual o SketchUp real faz
com itens indisponíveis no contexto atual, nunca escondidos. Submenus
aninhados (ex.: "Estilo de face >") abrem em flyout no hover, mesma
mecânica CSS do menu de topo.

Os **5 menus restantes** (Desenho, Ferramentas, Janela, Extensões,
Ajuda) também estão catalogados e com dropdown real, com um ou mais
itens funcionais cada (ver `REVERSE_ENGINEERING_NOTES.md` seção 28):
- **Desenho > Formas > Retângulo**: cria geometria nova de verdade (não
  só edita a existente) -- uma face retangular real via
  `SUGeometryInputCreate`/`SUEntitiesFill` da `SketchUpAPI.dll`
  (família de exports públicos confirmada via engenharia reversa, ver
  seção 28.6). Resto do menu (Linhas, Arcos, Retângulo Giratório,
  Círculo, Polígono, Sandbox) continua fora de escopo.
- **Ferramentas**: Mover/Rotar/Escala ligados ao mesmo `setMode()` do
  painel de edição; Selecionar/Apagar/Fita métrica/Virar ao longo de
  (Vermelho/Verde/Azul) também implementados de verdade -- Apagar exclui
  de verdade a peça clicada (mesmo `SUEntitiesErase` de "Editar >
  Excluir"), Fita métrica mede a distância real entre dois pontos
  clicados (metros), Virar espelha a instância aplicando pelo mesmo
  `PATCH /scene/instances/{id}/transform` já existente (não duplica
  lógica, só mais um caminho de UI).
- **Ferramentas > Transferidor**: 3 cliques reais na geometria medem o
  ângulo real entre eles (graus), na barra de status.
- **Ferramentas > Dimensões**: 2 cliques criam uma cota 3D real e
  persistente (linha + rótulo com a distância) no viewport.
- **Ferramentas > Texto**: cria um rótulo 3D real com o conteúdo
  digitado no painel, posicionado no ponto clicado.
- **Ferramentas > Texto 3D**: extrusão real de fonte em malha
  (`THREE.TextGeometry`, carregada do mesmo CDN de onde o Three.js já
  vem) -- diferente de "Texto" (rótulo billboard 2D), produz um mesh
  de verdade com volume/sombreamento.
- **Ferramentas > Laço**: seleção múltipla real (destacada com
  `THREE.BoxHelper` laranja por peça, já que o material é
  compartilhado por toda a cena); "Excluir (Del)" nesse modo exclui de
  verdade todas as peças selecionadas em lote.
- **Ferramentas > Pintura**: aplica uma cor RGBA nova de verdade numa
  instância via `SUMaterialCreate`/`SUMaterialSetColor`/
  `SUDrawingElementSetMaterial` (família de exports públicos
  confirmada via engenharia reversa, ver seção 28.15). Limitação
  documentada: a peça pintada usa um material clonado client-side, por
  isso deixa de responder aos toggles de "Visualizar > Estilo de
  face" (que só mutam o material compartilhado) depois de pintada.
- **Ferramentas > Plano de seção**: `THREE.Plane` + clipping nativo do
  WebGL -- corta de verdade a geometria acima da altura clicada
  (sem "tampa" preenchida, limitação documentada).
- **Ferramentas > Etiqueta**: aplica uma Etiqueta (Tag) real na
  instância clicada via `SULayerCreate`/`SULayerSetName`/
  `SUModelAddLayers`/`SUDrawingElementSetLayer` (família de exports
  públicos confirmada via engenharia reversa, ver seção 28.18 -- nome
  interno da API continua "Layer", nome legado da Trimble, mesmo a UI
  chamando de "Etiqueta"/"Tag"). Só muda metadado, não topologia/malha.
- **Ferramentas > Pintura por face**: pinta uma FACE específica (não a
  peça inteira) via `SUFaceToDrawingElement`/`SUDrawingElementSetMaterial`
  (confirmado via REA que `SUFaceSetFrontMaterial` é um thin wrapper
  desse mesmo caminho, ver seção 28.19). Como a face pertence à
  geometria da DEFINIÇÃO, a mudança no `.skp` afeta todas as instâncias
  que compartilham essa definição -- mesmo comportamento do SketchUp
  real. Limitação documentada: visualmente, só a instância clicada
  nesta sessão reflete a pintura (`THREE.BufferGeometry.groups` +
  array de materiais no mesh específico).
- **Janela > Bandeja padrão**: Informações da entidade/Componentes
  ligados ao colapso das seções do Default Tray já existentes;
  Sombras/Névoa ligados ao MESMO toggle real de "Visualizar >
  Sombras/Névoa" (duplicação de caminho de UI, igual o SketchUp real);
  "Informações do modelo" mostra as contagens reais da cena aberta.
- **Ajuda**: "Sobre o SketchBuild..." mostra uma mensagem informativa
  na barra de status; "Bem-vindo ao SketchUp..." reabre a Página
  Inicial real (mesma tela da Fase 6).
- **Extensões** ficou catalogado sem nenhum item funcional -- lista de
  plugins de terceiros, fora do escopo deste visualizador/editor
  (decisão de escopo confirmada explicitamente por Fernando).

### Design system -- clone visual SketchUp Pro Classic

A UI replica o padrão visual do SketchUp Desktop (tema claro, cinzas
corporativos, ícones lineares, sem dark mode):
- **Top Toolbar** (`#top-toolbar`) fixa no topo, com separadores verticais
  de 1px entre grupos de botões -- ícones SVG inline (sem lib de ícones
  externa) pras 4 vistas padrão + salvar.
- **Default Tray** (`#default-tray`) -- painel direito único com Outliner e
  Entity Info como seções sanfonadas (accordion) independentes, cada uma
  recolhível pelo próprio cabeçalho, igual ao comportamento real do Default
  Tray do SketchUp.
- Paleta de tokens em `:root` (`--bg`, `--panel`, `--toolbar`, `--border`,
  `--accent`, etc.) -- trocar aqui já re-tema o app inteiro.
- Inputs numéricos do Entity Info alinhados à direita, fonte monoespaçada,
  com efeito "afundado" (`box-shadow: inset`) -- padrão denso de inspector
  CAD. `border-radius` unificado em 2px em todos os controles.
- 100% frontend -- nenhuma mudança de contrato de API foi necessária para
  o redesenho visual.

### Página Inicial (Welcome Screen)

Tela modal exibida ao carregar o app, modelada na tela de boas-vindas do
SketchUp Desktop -- com dado **100% real**, nada forjado:
- **Arquivos recentes** -- lista real (`GET /api/v1/recent-files`),
  persistida em `app/data/recent_files.json`. Toda abertura bem-sucedida
  via `/scene/open` registra o arquivo automaticamente
  (`app/controllers/scene_controller.py`). `last_modified` vem de verdade
  do disco; se o arquivo tiver sumido, mostra "Arquivo não encontrado" em
  vez de inventar uma data.
- **Thumbnail real** -- não é um ícone genérico: o frontend tira um
  snapshot de verdade do canvas Three.js (`renderer.domElement.toDataURL()`)
  logo após o modelo carregar e enquadrar na isométrica, e manda pro
  backend (`POST /api/v1/recent-files/thumbnail`) gravar em
  `app/data/thumbnails/{id}.png`, servido via `StaticFiles` em
  `/thumbnails`.
- **Abrir arquivo** -- campo de caminho inline (o app roda no navegador,
  não tem acesso a um seletor de arquivo nativo do SO como o SketchUp
  Desktop; essa limitação é assumida, não escondida).
- **Criar novo modelo** -- grade com os 6 templates reais da Trimble
  (Simples/Visualização/Arquitetura × unidades), **funcional**
  (`POST /api/v1/scene/new`). Não usa `SUModelCreate`: descobriu-se que o
  SketchUp Desktop real também não cria um modelo em branco por API --
  "Criar novo modelo" abre um dos `.skp` de template que a Trimble
  instala junto com o programa. A unidade de cada arquivo (a/b/c/d) foi
  confirmada empiricamente via `SUModelGetUnits` (ver
  `REVERSE_ENGINEERING_NOTES.md` seção 24). O template é aberto via
  buffer (sem vínculo com o caminho real no disco) e a sessão fica sem
  `model_path` até o primeiro "Salvar Como" -- um "Salvar" simples nunca
  sobrescreve o `.skp` original da instalação da Trimble.
- `app/data/` (JSON de recentes + thumbnails) está no `.gitignore` -- guarda
  caminhos absolutos reais do disco e imagens reais dos seus modelos.
- **Fidelidade visual com o SketchUp real** -- eixos corrigidos (o
  `.skp` nativo é Z-up, o Three.js é Y-up; o pipeline inteiro passava as
  coordenadas direto, sem remapear -- achado reproduzindo e corrigindo
  via o personagem de escala plano "Sree", que ficava deitado em vez de
  em pé), o personagem de escala dos templates gira em tempo real pra
  encarar a câmera (`SUComponentDefinitionGetBehavior`, campo "sempre de
  frente para a câmera"), sem grade (só os 3 eixos RGB, como o SketchUp
  real), e fundo em degradê de céu + chão sólido nas cores reais do
  programa. Detalhes completos em `REVERSE_ENGINEERING_NOTES.md` seção
  25.

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
sketchup_companion/
├── core/
│   ├── su_types.py                 # tipos ctypes (SU*Ref, SUTransformation, su_check)
│   ├── su_api.py                   # binding ctypes contra SketchUpAPI.dll
│   └── mesh_extractor.py           # percorre a arvore e monta o DTO (definitions+instances)
├── app/                             # backend FastAPI (camadas)
│   ├── main.py                      # registra routers + serve frontend/ como estatico
│   ├── routes/scene_router.py       # POST /api/v1/scene/open, /scene/new
│   ├── controllers/scene_controller.py
│   ├── services/scene_service.py
│   ├── repositories/skp_engine_repository.py  # unico lugar que chama core/
│   ├── schemas/scene.py             # DefinitionDTO, InstanceDTO, SceneResponse
│   ├── routes/recent_files_router.py       # GET /api/v1/recent-files, POST .../thumbnail
│   ├── repositories/recent_files_repository.py  # JSON local -- Pagina Inicial
│   ├── data/                        # recent_files.json + thumbnails/ (gerado, gitignored)
│   └── routes/model_router.py , ruby_bridge/ , bridge_*.py  # arquitetura alternativa (ver abaixo)
├── frontend/
│   ├── index.html
│   └── src/{main,sceneBuilder,outliner,welcome,api}.js
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
| POST | `/api/v1/scene/new` | Cria um modelo novo a partir de um template real da Trimble (`{template_id}` -- ver seção "Criar novo modelo" acima). `model_path` volta `null` até o primeiro "Salvar Como". |
| PATCH | `/api/v1/scene/instances/{instance_id}/transform` | Aplica uma nova transformação (mundial, column-major) a uma instância da sessão aberta -- só em memória, ainda não grava em disco. |
| POST | `/api/v1/scene/save` | Grava o modelo editado em disco (`path` omitido = sobrescreve o arquivo aberto; exige `path` explícito se o modelo ainda não tiver um -- caso de modelo criado por template). |
| DELETE | `/api/v1/scene/instances/{instance_id}` | Exclui de verdade a instância da sessão aberta (equivalente nativo de "Editar > Excluir"/Del -- ver `REVERSE_ENGINEERING_NOTES.md` seção 26). |
| POST | `/api/v1/scene/export/obj` | Exporta a sessão aberta pra um `.obj` (equivalente parcial de "Arquivo > Exportar > Modelo 3D..." -- só formato OBJ por enquanto, escrito em Python puro já que a `SketchUpAPI.dll` não expõe exportadores nativos -- ver seção 26.4). |
| POST | `/api/v1/scene/geometry/rectangle` | Cria uma face retangular nova no chão da sessão aberta (equivalente real de "Desenho > Formas > Retângulo" -- geometria nova de verdade via `SUGeometryInputCreate`/`SUEntitiesFill`, ver `REVERSE_ENGINEERING_NOTES.md` seção 28.6), opcionalmente dentro de um Grupo novo (`as_group`, equivalente a "Editar > Criar grupo", ver seção 28.18). |
| POST | `/api/v1/scene/instances/{instance_id}/material` | Aplica uma cor RGBA nova de verdade numa instância (equivalente real de "Ferramentas > Pintura" -- `SUMaterialCreate`/`SUMaterialSetColor`/`SUDrawingElementSetMaterial`, ver `REVERSE_ENGINEERING_NOTES.md` seção 28.15). |
| POST | `/api/v1/scene/instances/{instance_id}/tag` | Aplica uma Etiqueta (Tag) real numa instância (equivalente real de "Ferramentas > Etiqueta" -- `SULayerCreate`/`SULayerSetName`/`SUModelAddLayers`/`SUDrawingElementSetLayer`, ver `REVERSE_ENGINEERING_NOTES.md` seção 28.18). |
| POST | `/api/v1/scene/faces/{face_id}/material` | Aplica uma cor RGBA nova numa FACE específica (não a instância inteira) -- `SUFaceToDrawingElement`/`SUDrawingElementSetMaterial`, afeta todas as instâncias que compartilham a mesma definição (ver `REVERSE_ENGINEERING_NOTES.md` seção 28.19). |
| GET | `/api/v1/recent-files` | Lista os `.skp` recentemente abertos por este app (mais recente primeiro) -- alimenta a Página Inicial. |
| POST | `/api/v1/recent-files/thumbnail` | Recebe um PNG real (snapshot do canvas 3D) pra virar a thumbnail de um arquivo na Página Inicial. |
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
    {
      "instance_id": "inst_0",
      "definition_id": "def_...",
      "transform": [ /* 16 floats, column-major */ ],
      "parent_instance_id": "inst_root"
    }
  ]
}
```
`parent_instance_id` preserva a hierarquia original da árvore (`null` só
pra `inst_root`, a pseudo-instância sintética do `Entities` raiz) -- usado
pelo painel Outliner do frontend pra remontar a árvore client-side.
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

### `DELETE /api/v1/scene/instances/{instance_id}`

```jsonc
// Response 200
{ "instance_id": "inst_1", "deleted": true }
```
Equivalente nativo de "Editar > Excluir"/Del: usa `SUComponentInstanceToEntity`
+ `SUEntitiesErase` (SDK público, ver `REVERSE_ENGINEERING_NOTES.md` seção
26.4) -- remove de verdade a instância do `SUModelRef` aberto em memória
(não é só um efeito visual no frontend). Irreversível nesta sessão (ainda
não há desfazer/refazer). Erro: `409` (nenhuma sessão aberta, instância
inexistente, ou é o pseudo-objeto `inst_root`, que não é excluível).

### `POST /api/v1/scene/export/obj`

```jsonc
// Request
{ "path": "C:/.../modelo.obj" }

// Response 200
{ "saved": true, "path": "C:/.../modelo.obj" }
```
Reextrai o DTO da sessão aberta na hora (reflete qualquer edição/exclusão
já aplicada) e escreve um `.obj` combinando todas as instâncias em espaço
de mundo (metros, sem UV/textura ainda -- ver `core/obj_exporter.py`).
Erros: `400` (caminho vazio ou não termina em `.obj`), `409` (nenhuma
sessão aberta ou falha ao escrever o arquivo).

### `POST /api/v1/scene/geometry/rectangle`

```jsonc
// Request
{ "width_m": 1.0, "height_m": 1.0, "as_group": false }

// Response 200
{
  "scene": {
    "model_path": "C:/.../arquivo.skp",
    "definitions": [ /* mesmo formato de /scene/open, já com a nova face */ ],
    "instances": [ /* ... */ ]
  }
}
```
Cria uma face retangular real (4 vértices coplanares, dimensões em
metros) centrada na origem, deitada no plano XY (Z=0, chão) --
`SUGeometryInputCreate` → `SUGeometryInputAddVertex` (×4) →
`SULoopInputCreate`/`SULoopInputAddVertexIndex` (×4) →
`SUGeometryInputAddFace` → `SUEntitiesFill(entities, input, true)`,
toda a família de exports públicos da `SketchUpAPI.dll` confirmada via
engenharia reversa (ver `REVERSE_ENGINEERING_NOTES.md` seção 28.6).
Diferente de mover/excluir uma instância, devolve a **cena inteira**
pós-criação em vez de um delta -- o frontend reconstrói a malha "root"
completa a partir da resposta (`applySceneDTO`). Se `as_group: true`,
a face é criada dentro de um `SUGroupRef` novo (`SUGroupCreate` →
`SUGroupSetName` → `SUEntitiesAddGroup`) em vez de direto na raiz --
equivalente real de "Editar > Criar grupo" (ver `REVERSE_ENGINEERING_
NOTES.md` seção 28.18); como Grupos são uma coleção separada de
`SUEntitiesGetInstances`, o `mesh_extractor.py` soma
`get_instances()` + `group_to_instance(g) for g in get_groups()` pra
grupos novos aparecerem no viewer/Outliner. Erros: `400`
(`width_m`/`height_m` ≤ 0), `409` (nenhuma sessão aberta ou falha ao
criar a geometria).

### `POST /api/v1/scene/instances/{instance_id}/material`

```jsonc
// Request
{ "r": 60, "g": 127, "b": 177 }

// Response 200
{ "instance_id": "inst_1", "painted": true, "color": [60, 127, 177] }
```
Aplica um material novo com cor RGBA real na instância --
`SUMaterialCreate` → `SUMaterialSetColor` →
`SUComponentInstanceToDrawingElement` (passthrough, mesmo padrão de
`SUComponentInstanceToEntity` já usado em "Editar > Excluir") →
`SUDrawingElementSetMaterial`, família de exports públicos confirmada
via engenharia reversa (ver `REVERSE_ENGINEERING_NOTES.md` seção
28.15). Diferente de `geometry/rectangle`, NÃO devolve a cena inteira
-- só muda aparência, não topologia/malha, então o frontend aplica a
cor direto no mesh correspondente sem round-trip. Erros: `400`
(componente de cor fora de 0-255), `409` (nenhuma sessão aberta ou
instância não encontrada).

### `POST /api/v1/scene/instances/{instance_id}/tag`

```jsonc
// Request
{ "name": "Estrutura" }

// Response 200
{ "instance_id": "inst_2", "tag_name": "Estrutura" }
```
Aplica uma Etiqueta (Tag) real na instância --
`SULayerCreate` → `SULayerSetName` → `SUModelAddLayers` (cria/reusa
uma `SULayerRef` em cache por nome na sessão, pra não duplicar a
mesma etiqueta a cada clique) →
`SUComponentInstanceToDrawingElement` (mesmo passthrough já usado em
Pintura/Excluir) → `SUDrawingElementSetLayer`, família de exports
públicos confirmada via engenharia reversa (ver
`REVERSE_ENGINEERING_NOTES.md` seção 28.18 -- a API interna chama
isso de "Layer", nome legado da Trimble, mesmo a UI chamando de
"Etiqueta"/"Tag"). Só muda metadado, não topologia/malha -- NÃO
devolve a cena inteira. Erros: `400` (nome vazio/só espaço), `409`
(nenhuma sessão aberta ou instância não encontrada).

### `POST /api/v1/scene/faces/{face_id}/material`

```jsonc
// Request
{ "r": 60, "g": 127, "b": 177 }

// Response 200
{ "face_id": "face_251f610e7a0", "painted": true, "color": [60, 127, 177] }
```
Aplica um material novo com cor RGBA real numa FACE específica (não na
instância inteira) -- `SUMaterialCreate` → `SUMaterialSetColor` →
`SUFaceToDrawingElement` (passthrough, confirmado via REA que
`SUFaceSetFrontMaterial` é um thin wrapper exatamente desse caminho) →
`SUDrawingElementSetMaterial`, família de exports públicos confirmada
via engenharia reversa (ver `REVERSE_ENGINEERING_NOTES.md` seção
28.19). `face_id` vem de `DefinitionDTO.face_ranges` (devolvido por
`/scene/open`/`/scene/new`/etc. -- cada entrada tem `{face_id,
triangle_start, triangle_count}`, mapeando o `faceIndex` que o
`Raycaster` do Three.js devolve num clique de volta pro `face_id`
real). Como a face pertence à geometria da DEFINIÇÃO (não da
instância), a mudança fica gravada no `.skp` pra TODAS as instâncias
que compartilham essa definição. Não devolve a cena inteira. Erros:
`400` (componente de cor fora de 0-255), `409` (nenhuma sessão aberta
ou face não encontrada).

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
- Outliner mostra só o nome da **definição**, não um nome de instância
  individual (`SUComponentInstanceGetName` ainda não foi verificado via
  assembly) -- e não tem busca/filtro.
- Entity Info não tem campo de escala (fora do escopo pedido na Fase 4).

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
