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
