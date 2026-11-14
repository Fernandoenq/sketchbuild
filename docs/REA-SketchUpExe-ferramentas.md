# REA do SketchUp.exe: inventário das ferramentas (14/11/2026)

Alvo: `C:\Program Files\SketchUp\SketchUp 2026\SketchUp\SketchUp.exe`, sha256 `f211d3d5…33e1`, base `0x140000000`, 133.387 procedimentos, 49.127 strings, Ghidra 12.1.4 (análise de ~40 min; o limite do MCP é 30 min por chamada, então a análise precisa terminar no processo do Ghidra e a chamada seguinte já pega a sessão pronta).

**RTTI está completa**: os nomes das classes vêm do binário (`.?AV…@@`). Endereço = nome da classe (campo `name` do TypeDescriptor); o TypeDescriptor começa 16 bytes antes. COL = (xref do TypeDescriptor) − 12; a vtable começa 8 bytes depois do ponteiro para o COL.

## Classes das ferramentas (endereço do nome RTTI)
| Ferramenta | Classe | Nome RTTI em |
|---|---|---|
| base | `CTool` | 0x142dbcfb0 |
| Empurrar/Puxar | `CPushPullTool` / `CPushPullTool_V2` / `CPushPullController` / `PushPullHelper::Face_PushPullData` | 0x142e0f6d0 / 0x142e0e1b0 / 0x142e4b3c0 / 0x142e4b428 |
| Mover | `CMoveTool`, `CMoveToolHelper`, `CArrayHelper` | 0x142e0f548, 0x142e10800, 0x142e10850 |
| Offset | `COffsetTool` | 0x142e0f610 |
| Rotacionar | `CRotateTool`, `CBaseRotateTool`, `CRotateHelper` | 0x142e0f778, 0x142d7b398, 0x142e0ea28 |
| Escalar | `CScaleTool`, `CStretchHelper` | 0x142df6cb8, 0x142e4b460 |
| Siga-me | `CExtrudeTool` (provável) | 0x142e0e1d8 |
| Retângulo | `CRectangleTool`, `CRectangle3PointTool` | 0x142e0f750, 0x142e0f720 |
| Círculo / Polígono | `CCircleTool`, `CPolyTool` | 0x142e0ed80, 0x142e0ed60 |
| Arcos | `CArcTool`, `CArc3PointTool`, `CArc3PointPieTool`, `CFit3PointArcTool` | 0x142e0ebc0, 0x142df7530, 0x142df7508, 0x142e0ebe0 |
| Linha / mão livre | `CSketchTool`, `CFreehandTool`, `CDivideLineTool` | 0x142e0f7a0, 0x142e0f3c0, 0x142e0eb48 |
| Apagar | `CEraseTool`, `CEraseController` | 0x142e0e278, 0x142e11798 |
| Tinta | `CPaintTool`, `CPaintMatchTool` | 0x142e0e040, 0x142e0e068 |
| Medidas | `CMeasureTool`, `CProtractorTool`, `CDimensionTool`, `CTextTool`, `C3DTextTool`, `CSectionPlaneTool`, `CCoordinateTool` | 0x142e0f408, 0x142e0f6a8, 0x142e0f250, 0x142e0f7c8, 0x142e0e018, 0x142e0f898, 0x142e0e138 |
| Seleção | `CSelectionTool`, `SelectionToolBase`, `LassoSelectionTool` | 0x142e0dcb0, 0x142e0dcd8, 0x142e0e2a0 |
| Sólidos | `CBooleanTool` (+ Union, Difference, Intersect, Trim, Split, SplitP), `COuterShellTool` | 0x142e0ec60 e vizinhos, 0x142e0ec08 |
| Auxiliares | `CTwoPointTool`, `CThreePointTool`, `CFlipTool`, `CAutoFoldHelper`, `CInterferenceDetectionHelper`, `CToolManager` | 0x142e0e188, 0x142d7b370, 0x142d7580, 0x142e4b340, 0x142e107c8, 0x142df3850 |

## Empurrar/Puxar (em andamento)
- Construtor `CPushPullTool` = `FUN_140ca4370`: guarda a mensagem **"Cannot Push/Pull curved or smoothed surfaces"** (campo +0xF8) e inicia o estado a zero. **LIDA.** Há também a opção `AllowPreselectPushPull` ("Disable pre-pick on Push/Pull Tool").
- vtable de `CPushPullTool` em `0x1420dae38`. Slot 33 (`FUN_140ca4720`) = ativar a ferramenta: rótulo do campo de valor **"Distance"**, pega a seleção e a face pré-selecionada. **LIDA.** Slot 44 (`FUN_140ca4940`) = desenho da dica/inferência (sem regra de geometria).
- `CPushPullController` (vtable em `0x142781c90`) contém as mensagens **"This face cannot be stretched."** e **"Cannot move face…"** (mover face de uma peça que não pode). **LIDA.**
- Classes `PushPullHelper::Face_PushPullData` e `Base_PushPullData`: os dados por face do empurrar/puxar.

Pendente: ler os métodos do controlador (extrusão, fusão, "criar nova" com Ctrl) e achar o que torna uma face "curva ou suavizada".

## Entidades e algoritmos do modelo no .exe (RTTI, nome em)
`CEntity` 0x142db9a68 · `CFace` 0x142de4848 · `CEdge` 0x142de52d8 · `CEdgeUse` 0x142de4828 · `CLoop` 0x142de4a48 · `CVertex` 0x142de5218 · `CCurve` 0x142de39c0 · `CGroup` 0x142de5728 · `CComponent`/`CComponentDefinition`/`CComponentInstance` 0x142de3090/0x142d797d0/0x142de3110 · `CText` 0x142de5370 · `CDimension*` · `CSectionPlane` 0x142de55a0 · `CTexture` 0x142de4f80 · `CEntitySet` 0x142de2e18.

Algoritmos que interessam ao plano:
- **`CFaceFinder`** (0x142de51d0): procura ciclos fechados que viram face quando uma aresta é desenhada (regra "linha fecha ciclo → face").
- **`CEdgeEraseSet`** (0x142de5048): o conjunto de apagar da borracha (fusão, arestas suaves).
- **`CEdgeChain`** (0x142e4b368) e **`CCurveBuilder`** (0x142e0f9a0): cadeias de arestas e construção de curvas (arcos, círculos, mão livre).
- **`CFaceTesselator`/`CFaceToMesh`**: triangulação.
- **`CInterferenceDetectionHelper`**: usado pelo Mover (colisão).

## Empurrar/Puxar: "This face cannot be stretched." (LIDA)
`FUN_141948e90(controlador, resultado)`: só avalia quando **há exatamente uma entidade selecionada** (`+0x18 == 1`), a entidade é do tipo **0x12** (`vtable+0x98`; mesmo código visto no `SUEntitiesErase`) e a ferramenta não está em estado de arrasto (`+0x30 == 0`). Chama `FUN_141933920` (monta o conjunto de entidades vizinhas em `+0x40`) e testa cada vizinha com `FUN_1408bc150(vizinha, entidade)`; **se todas passam**, escreve a mensagem "This face cannot be stretched." Ou seja: a recusa depende do conjunto de vizinhas da face, não da geometria da própria face. Semântica exata de `FUN_1408bc150` ainda não lida.

## Entidade 0x12 = face (LIDA, 14/11/2026)
`CFaceFinder` (vtable em 0x1420ac438; só o slot 4, `FUN_1408b1a60`, tem código próprio) recebe uma entidade, converte para `CEntity`, chama `vtable+0x98` e **só guarda se o código for 0x12**, inserindo-a numa lista ordenada de faces (`+0x98/+0xa0`). Logo **0x12 = `CFace`**, o mesmo código que o `CPushPullController` testa e que aparece nos tipos do `SUEntitiesErase` (REA da DLL, 13/11). 0x10 e 0x27 seguem sem confirmação direta (provável aresta e contêiner).

## Método que funcionou e o que não rende
- **Rende:** partir de uma *string de regra* (mensagem de erro, rótulo "Distance", nome de opção), pegar o `xrefs` e decompilar a função que a usa. Foi assim que saíram o rótulo do campo de valor e a regra "cannot be stretched".
- **Não rende:** abrir um a um os slots da vtable de uma ferramenta. A maioria é getter/stub de 1 a 5 linhas (ex.: `FUN_140ca5500`), e cada chamada ao REA devolve ~8 KB de texto, o que esgota o contexto antes de achar a lógica de geometria. Próxima vez: usar `procedure_callees` da função de clique, ou `search_strings` por mensagens específicas de cada ferramenta (cursores `cursor_pushpull*`, "Distance", "Length", "Angle", textos de barra de status).

## Limite do MCP e como destravar
O MCP corta chamada sem resposta por **30 min** (`CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT`, padrão 1800 s) e a análise do `.exe` leva ~40 min. Contornei esperando o processo do Ghidra terminar (a sessão ficou pronta às 03:49). Para as próximas aberturas: reiniciar o Claude com `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT=0` (ou `"timeout"` no servidor `rea` do `.claude.json`) e `REA_GHIDRA_DISABLED_ANALYZERS` para pular os analisadores mais caros. A sessão atual só dura enquanto o processo do REA ficar vivo; o Windows não persiste a análise.

## Empurrar/Puxar: a mensagem "curved or smoothed" (14/11, rodada 2)

- **LIDA** (ev_b896d782…, ev_bf94ebee…): a string "Cannot Push/Pull curved or smoothed surfaces" (0x1420db090) tem uma única referência, em `FUN_140ca4370` (0x140ca4370), que é o **construtor** de `CPushPullTool` (grava a vtable, zera ~0x30 campos e guarda a mensagem num membro, `this+0xf8`, via `FUN_1406bfb10`).
- Conclusão: a mensagem é só texto guardado na criação. O teste de "curva/suavizada" fica em outro método, que lê esse membro. Nenhuma regra geométrica foi extraída; nada entra no núcleo.
- Próximo passo: achar os leitores do campo `this+0xf8` (métodos de `CPushPullTool` na vtable) e decompilar o que chama `FUN_1408bc150`. Fazer na próxima sessão, com `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT=0`.

## Empurrar/Puxar: o caminho do mouse até a recusa (14/11, rodada 3)

Vtable de `CPushPullTool` (0x1420dae38) lida em bytes (ev_259e633b…). Slots com código próprio da ferramenta ficam em 0x140ca4600–0x140ca7a70; o resto aponta para a classe-base (0x140b0…).

**LIDA** — `FUN_140ca6220` (slot 15, movimento do mouse; ev_92751936…):
- Só começa o empurrar quando já há uma face escolhida (`this+0x80`) e o botão está apertado, e o mouse andou **3 pixels ou mais** em x ou y (`|dx| < 3 && |dy| < 3` não faz nada).
- Escreve "Push/Pull" na barra de status (`FUN_1407b1610`, código 0x2e).
- Chama `FUN_141943ae0(this+0x198, face, +0x138, modo==2)` para criar os dados do empurrar. Se devolve nulo: se a mensagem de recusa está preenchida, mostra-a (`FUN_140b4b880`); senão volta ao estado inicial. Se devolve algo, entra no estado "puxando" (`this+0x98 = 1`) e atualiza a distância (`FUN_140ca50c0`, `FUN_140ca5780`).
- `this+0x318` (int) guarda o modo; `== 1` e `== 2` mudam os parâmetros de `FUN_141943ae0` (provável: Ctrl cria cópia e modo "esticar").

**LIDA** — `FUN_141943ae0` (cria os dados; ev_27a0e66f…):
- O dono da face (`face+0x18`, chamado por `vtable+0x98`) só pode ter tipo **2, 4 ou 0x4b**; qualquer outro devolve nulo e a ferramenta não age. Os rótulos desses três códigos não foram confirmados (candidatos: modelo, grupo, definição de componente).
- Se `param_4 == 0` (empurrar normal): `FUN_1419435a0` monta os dados e `FUN_141940a70` os prepara.
- Se `param_4 != 0` (modo esticar): chama `FUN_141948e90`, que devolve a mensagem de recusa.

**LIDA** — `FUN_141948e90` (modo esticar; ev_a5e33d00…): exige que a seleção tenha **exatamente 1 item** (`+0x18 == 1`) e que ele seja **face (0x12)**; `FUN_141933920` reúne um conjunto de itens relacionados (`+0x40`) e, para cada um, `FUN_1408bc150(item, face)` testa se a face **pertence** àquele item (percorre a lista dele e compara; é só um teste de pertencimento, ev_e54c3a03… e ev_8fca44e0…). Se nenhum item falha no teste, o texto "This face cannot be stretched." é gravado. A interpretação exata (por que a mensagem sai quando todos passam) ainda é **SUPOSTA**; não foi usada.

**O que isto muda no núcleo:** nada ainda. Resultado útil: o limiar de 3 px é regra de interface do SketchUp (a interface web já usa distância em unidades, não pixels) e o teste "curva/suavizada" **não está** no caminho do mouse — fica em `FUN_141933920`/`FUN_1419435a0`/`FUN_141940a70`, que são os próximos alvos.

## Empurrar/Puxar: montagem dos dados — `FUN_1419435a0` (14/11, rodada 3)

Lida em ev_72f90c94…. Ordem das etapas (**LIDA**, nomes de função são endereços, sem rótulo):
1. `FUN_141940810()` devolve **dois bits de opção**: bit 0 (habilita o caminho completo) e bit 1 (modo "copiar", o mesmo que o Ctrl faz no SketchUp; **SUPOSTA** pelo uso: vira o 3º argumento de `FUN_1419419d0`).
2. Percorre as **arestas da face** (`FUN_140871e20`); para cada aresta ainda sem dono (`+0x50 == 0`) desfaz vínculos nos dois vértices (`FUN_1408b61a0` / `FUN_140815e80`) e chama `FUN_1408bd080`. Ou seja: prepara as arestas da face antes de extrudar.
3. `FUN_1419424e0` e `FUN_1419419d0(this, face, copiar)` criam a geometria nova (devolve a face/solido novo; nulo = falhou e o empurrar é recusado); `FUN_141941350` e `FUN_1407dd570` ligam o resultado à face original.
4. Sem copiar: guarda a face em `this+0x68` e a marca (`FUN_140875760`). Com copiar: marca (valor 6, `FUN_1407dd3b0`) a face nova e as listas em `this+0x80` e `this+0x90`, roda `FUN_141942e90` e zera `this+0x68`.
5. Limpeza final: para cada vértice da geometria nova, olha as arestas ligadas dois a dois. Quando duas delas têm o mesmo campo `+0x28` (índice 5 do vetor; candidato: mesma reta ou mesma curva), chama o método virtual `+0x20` nas duas e **desconta 2 do número de arestas do vértice**; quando sobram menos de 3, chama `FUN_1407f6940` (provável: apagar o vértice/aresta redundante). **SUPOSTA**: é a fusão de arestas colineares depois do empurrar.

**O que ainda falta:** `FUN_1419419d0` (a extrusão em si), `FUN_141940a70` e `FUN_141933920`. Nada disto foi levado ao núcleo: o núcleo já faz o empurrar de face plana (`core/topology/pushpull.py`), e esta leitura só aponta onde o SketchUp limpa arestas colineares, regra que o núcleo ainda não replica.
