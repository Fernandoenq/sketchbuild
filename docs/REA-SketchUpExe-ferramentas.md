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

## Empurrar/Puxar: `FUN_1419419d0` é a CÓPIA da face, não a extrusão (14/11, rodada 4)

Lida em ev_2028eec9…. Correção da rodada 3: eu tratava esta função como "a extrusão em si". Ela só **duplica a face e emparelha original com cópia**.
- **LIDA:** cria uma lista com a face e executa uma operação de cópia sobre ela (`FUN_140917890` + `FUN_1409179d0`; retorno 0 = falhou, devolve nulo e o empurrar é recusado). `FUN_1407f40e0(this+0x10, lista)` devolve a lista copiada e a função pega o primeiro item, que precisa ser **face (0x12)**; é a face nova.
- **LIDA:** monta dois mapas ordenados (`std::map`) por ponteiro: `this+0x80` (um tipo de elemento da face original → o equivalente na cópia) e `this+0x90` (aresta original → aresta da cópia). O emparelhamento é **por ordem de iteração**: percorre os elementos da original e da cópia em paralelo e liga o n-ésimo ao n-ésimo. Logo, a cópia preserva a ordem dos elementos do laço.
- **LIDA:** fora do modo "copiar" (3º argumento = 0) e com um objeto de seleção ativo (`modelo+0x310`), os itens são também registrados nele (`FUN_1407b26c0`), o que explica a face/arestas ficarem selecionadas durante o arrasto. Em modo copiar isso é pulado.
- **SUPOSTA:** os mapas servem depois (`FUN_141941350`, `FUN_141942e90`) para costurar original e cópia com as faces laterais e para mover só a cópia na distância digitada. É o mesmo desenho do núcleo (`core/topology/pushpull.py`: laço de cima copiado, laterais ligando os dois laços), então **nada a mudar no núcleo**.

**Ainda falta** a costura/movimento (`FUN_141941350`, `FUN_141942e90`) e o teste de curva/suavizada (`FUN_141933920`, `FUN_141940a70`).

## `FUN_141933920`: conjunto de vértices da seleção — confirma 0x10 e 0x27 (14/11, rodada 5)

Lida em ev_ae46d491…. A função esvazia o conjunto em `this+0x40` e, para cada item da seleção (`this+0x10`), chama `FUN_141933540` para inserir **vértices**:
- item de código **0x12** (face): percorre os elementos da face (enumerador `FUN_140872bb0`) e insere cada um;
- item de código **0x10**: insere `item+0x40` e `item+0x48` (os dois extremos);
- item de código **0x27**: insere o próprio item;
- qualquer outro código é ignorado.

**Conclusões:** 0x12 = face (já confirmado), **0x10 = aresta** (tem dois extremos nos campos +0x40/+0x48), **0x27 = vértice** (entra direto no mesmo conjunto onde entram os extremos da aresta). Isto **corrige** a nota de 13/11 que dizia "0x27 provável contêiner". Selo: **LIDA** (estrutura) e **CONFIRMADA** (os três códigos, por consistência de uso), sem execução do SketchUp.

**Efeito no modo esticar** (junto com `FUN_141948e90`, **SUPOSTA**): o conjunto é o de vértices que a seleção moveria; a recusa "This face cannot be stretched." sai quando **todos** esses vértices já estão sobre a face escolhida (o teste `FUN_1408bc150` só verifica se a face contém o vértice).

**Ainda falta** para o Empurrar/Puxar: `FUN_141941350`, `FUN_141942e90` (costura e movimento) e `FUN_141940a70`. O teste de curva/suavizada continua sem aparecer; pode estar no `CPushPullController` (vtable 0x142781c90) e não na ferramenta.

## `CPushPullController`: as regras de recusa do "esticar" (14/11, rodada 6)

Os textos ficam colados à vtable do controlador (0x142781c90; bytes em ev_cca3508d…, busca em ev_27b61ec1…). **LIDO** (texto exato, endereços 0x142781cxx–0x142781e10):

| # | Mensagem do SketchUp | Condição que ela descreve (SUPOSTA, só pelo texto) |
|---|---|---|
| 1 | "This face cannot be stretched." | nenhum vértice da seleção sai da face (ver `FUN_141948e90`, rodada 3 e 5) |
| 2 | "Cannot move face - face touching at corner must be a triangle." | ao mover uma face, a face vizinha que toca só num canto (por um vértice) precisa ser **triângulo** |
| 3 | "Stretch would result in non-planar face" | esticar deixaria uma face vizinha não plana |
| 4 | "adjacent face has non-parallel edge" | a vizinha tem aresta não paralela à direção do movimento |
| 5 | "adjacent face has holes" | a vizinha tem furos |

**O que isto entrega:** o "esticar" (mover uma face arrastando as vizinhas, que é o que o Empurrar/Puxar faz numa face inclinada de uma peça) tem **três recusas geométricas** (2, 3, 4, 5 são variantes) e todas giram em torno de **faces vizinhas planas, sem furos, com arestas paralelas ao movimento, ou triângulos nos cantos**. São a especificação dos testes de pré-condição que o núcleo precisaria ter se um dia implementar esse modo. **A mensagem "curved or smoothed" é outra**, da ferramenta (construtor), para arestas/faces suavizadas.

**Núcleo:** o núcleo só faz o empurrar de face plana por normal (sem arrastar vizinhas), então **nada foi implementado**. Quando for implementar o modo esticar, usar esta tabela como lista de casos de teste de recusa. Falta ler qual função emite cada mensagem (as referências cruzadas partem do código de `FUN_141933920` em diante) para provar a condição exata de cada uma.

## `FUN_141947ce0`: o teste da face vizinha no "esticar" (14/11, rodada 7)

A mensagem "Stretch would result in non-planar face" (0x142781dc0) tem uma só referência, em **`FUN_141947ce0`** (ev_8757492a…, decompilada em ev_628e138a…). Ela emite três das cinco recusas: "non-planar", "non-parallel edge" e "face touching at corner must be a triangle". Parâmetros: `(this, saída_de_mensagem, face_vizinha, direção_do_movimento[3])`. **LIDA** (estrutura do código; os nomes M/F abaixo são meus):

1. **Passa direto (sem mensagem)** se `FUN_1406e4d40(normal_da_vizinha, direção)` for verdadeiro (relação entre a normal e a direção do movimento; candidato: normal perpendicular à direção, ou seja, a vizinha só desliza no próprio plano) ou se a vizinha tem **2 ou mais laços** e `FUN_141949030` falha (o ramo dos furos está em `FUN_141949030`, não aqui).
2. **Triângulo (3 vértices) passa direto**: `FUN_14087a870(laço) == 3` não entra no teste.
3. Para os outros polígonos, divide os vértices da vizinha em **M** (`FUN_141949160` verdadeiro: vértice que se move com a face) e **F** (os que ficam).
4. Casos, com `n` = nº de vértices:
   - **M = n** (todos se movem): passa.
   - **F = n** (nenhum se move; a vizinha só toca num canto): se tem **4 vértices**, faz um teste de paralelogramo (as duas arestas do canto, com `|dot(aresta, direção)| < tolerância` e mesmo tipo `+0x38`, e as pontas deslocadas pelo vetor da aresta batendo uma com a outra, dentro de `DAT_142c40108`); se falha, ou se não tem 4 vértices: **"Cannot move face - face touching at corner must be a triangle."**
   - **F < 3 e M > 0** (sobram só 1 ou 2 vértices fixos): **"Stretch would result in non-planar face"**.
   - **F ≥ 3 e M > 0**: precisa que a direção definida pelos vértices que se movem (`FUN_14193d030`) seja **paralela** à definida pelos fixos (`FUN_14193d050`, `FUN_1406e4c80`); senão: **"adjacent face has non-parallel edge"**.

**SUPOSTA (leitura, sem executar):** com 3 ou mais vértices fixos o plano da vizinha está travado, então só vale mover os outros ao longo de uma direção paralela a uma aresta dela; com menos de 3 fixos, o plano deixa de ser determinado e o SketchUp recusa por não-planaridade. A tolerância é a constante global `DAT_142c40108` (valor não lido ainda).

**Para o núcleo (futuro modo esticar):** os testes de recusa são puramente geométricos (contagens de vértices fixos/móveis, paralelismo com a direção, triângulo no canto) e podem ser escritos como funções puras com casos de teste vindos das 5 mensagens. Antes de implementar: ler o valor de `DAT_142c40108`, o que `FUN_141949160` considera "vértice que se move" e `FUN_141949030` (furos).

## Tolerância, "vértice que se move" e furos (14/11, rodada 8)

- **Tolerância `DAT_142c40108` = 0,001** (bytes `fca9f1d24d62503f` em 0x142c40108, ev_b0c67a50…, decodificados como double little-endian). **CONFIRMADA** como valor lido. É a mesma usada nos testes de igualdade de ponto (`FUN_1406e7aa0(a, b, tol)`) e de perpendicularidade (`|dot| < tol`) do `FUN_141947ce0`. Unidade: a interna do SketchUp (polegadas); o núcleo trabalha em outra unidade, então a conversão é obrigatória antes de usar o 0,001.
- **`FUN_141949160(this, vértice)` = "este vértice se move?"** (ev_db7ba869…). **LIDA:** percorre os itens da seleção (`this+0x10`); devolve 1 se o próprio vértice é um dos itens, **ou** se algum item é **face (0x12)** que contém o vértice (teste de pertencimento `FUN_1408bc150`). Ou seja: M = vértices selecionados + vértices das faces selecionadas. Fecha a dúvida das rodadas 3 e 7.
- **`FUN_141949030` = teste de furos** (ev_fe61e01f…, emite "adjacent face has holes"). **LIDA:** percorre os laços da face vizinha; para cada laço com a marca `+0x38 == 0` (SUPOSTA: laço interno, não o externo), percorre os vértices e exige que `FUN_1408b8940(vértice) < 2` para todos. Se algum vértice de um laço interno tem contagem ≥ 2, devolve 0 e grava a mensagem "adjacent face has holes". Ou seja, **um furo na vizinha só é aceito se o contorno dele não for compartilhado com outras arestas/faces** (o sentido exato de `FUN_1408b8940`, provavelmente nº de arestas ou faces ligadas ao vértice, **não foi lido**). Chamada na entrada de `FUN_141947ce0` quando a vizinha tem 2 ou mais laços. O destino da mensagem (4º argumento) não ficou claro no decompilado; tratar como SUPOSTA a ligação mensagem→chamador.

**Estado:** das cinco recusas do esticar, todas têm agora o ponto de código e as constantes conhecidas, menos o sentido de `FUN_1408b8940` e de `FUN_1406e4d40` (relação normal×direção). Isso é o que falta para escrever o modo esticar como funções puras com testes.

## Primitivas do esticar fechadas (14/11, rodada 9)

Três funções pequenas, lidas por inteiro. Selo **CONFIRMADA** (o código é a própria definição; sem execução do SketchUp):

| Função | Definição lida | Evidence |
|---|---|---|
| `FUN_1406e4d40(a, b)` | `abs(a·b) < 0,001` → vetores **perpendiculares** (produto escalar quase zero) | ev_fcbb3ef9… |
| `FUN_1406e4c80(a, b)` | `a == b` **ou** `a == -b`, componente a componente, com folga 0,001 → vetores **paralelos ou antiparalelos** (supõe unitários) | ev_021245c1… |
| `FUN_1408b8940(vértice)` | tamanho de um anel circular ligado em `vértice+0x58` (conta os nós seguindo `+0x48` até voltar à cabeça; 0 se o ponteiro é nulo) | ev_add4b840… |

**Efeitos nas regras do esticar:**
- Passo 1 de `FUN_141947ce0`: a vizinha **passa direto quando a normal dela é perpendicular à direção do movimento** (a face só desliza no próprio plano). Fecha o ponto que estava em aberto.
- "adjacent face has non-parallel edge": a comparação final é "paralelo ou antiparalelo" (sinal não importa).
- Furos: a regra vira "todo vértice de laço interno da vizinha pertence a **menos de 2** elementos do anel `+0x58`". **SUPOSTA** a leitura de que o anel `+0x58` é o das "ocorrências do vértice em laços de faces" (então um furo só vale se seu contorno não é usado por outra face). O anel em si não foi identificado.

**Ainda não lido** para fechar o modo esticar: `FUN_14193d030` e `FUN_14193d050` (o vetor de direção que sai dos vértices móveis e dos fixos), o movimento em si (`FUN_141941350`, `FUN_141942e90`) e a identidade do anel `+0x58`.

**Decisão sobre o núcleo:** não implementei o modo esticar. Sem o movimento e sem os dois vetores acima, qualquer código seria invenção, e a regra do projeto é só entrar o que está confirmado. As três primitivas acima são triviais e ficam documentadas para quando o resto estiver lido.

## `FUN_14193d050`/`FUN_14193d030`: o teste "cadeia reta" do esticar (14/11, rodada 10)

Lidas por inteiro (ev_f885d5b3…, ev_a68f81e6…). **LIDA:**
- Os baldes M (vértices que se movem) e F (fixos) de `FUN_141947ce0` são **cadeias ordenadas de arestas** (vetor em `cadeia+0x8`, quantidade em `+0x14`, marca de validade em `+0x1c`; sem a marca, o teste falha).
- `FUN_14193d050(cadeia, i0, i1, saída)` anda pelas arestas de `i0` a `i1`: pega a direção da primeira aresta (`FUN_1406eb3c0`, vetor entre os dois extremos, respeitando o sentido de percurso, que inverte conforme a aresta seguinte compartilha o extremo certo; `FUN_1408bda20` decide qual extremo) e exige que **cada aresta seguinte tenha a mesma direção** (`FUN_1406ecac0`). Qualquer divergência devolve 0.
- `FUN_14193d030(cadeia, saída)` = `d050(cadeia, 0, n-1, saída)`: a cadeia **inteira**.

**Regra resultante do esticar** (leitura; o passo da comparação de direção usa `FUN_1406e4c80`, paralelo ou antiparalelo, já confirmado):
> Numa vizinha com vértices que se movem e **pelo menos 3 fixos**: **(a)** todas as arestas da cadeia M têm a mesma direção (M é um segmento reto); **(b)** as arestas **internas** de F (índices 1 a F-2, sem a primeira e a última) têm a mesma direção (F é reto no miolo); **(c)** as duas direções são paralelas ou antiparalelas. Se alguma falha: "adjacent face has non-parallel edge".

Interpretação geométrica (**SUPOSTA**): é a condição para a vizinha continuar plana quando um lado dela é arrastado, esticando-se como um trapézio/paralelogramo: o lado que anda e o lado oposto que fica precisam ser paralelos.

**Falta** para escrever o esticar: o movimento em si (`FUN_141941350`, `FUN_141942e90`) e `FUN_1408bda20` / `FUN_1406ecac0` (igualdade de direção e escolha do extremo), além da identidade do anel `+0x58`.

## Paredes e limpeza do Empurrar/Puxar: `FUN_141941350` e `FUN_141942e90` (14/11, rodada 11)

Lidas em ev_75fdd928… e ev_1d07b659…. **LIDA:**
- **`FUN_141941350(this, face_original, face_copia)` cria as paredes.** Guarda a normal da face (`+0x40`) e, para cada aresta da original, monta uma lista (aresta, marca). A marca é zerada quando alguma face vizinha dessa aresta tem **normal perpendicular à da face puxada** (`FUN_1406e4d40`, folga 0,001). Depois, para cada aresta: se a vizinha **não** é perpendicular (ou se é modo copiar, `this+0x149 != 0`), chama `FUN_141942080` (o tratamento de esticar a vizinha; devolve não-zero em falha e interrompe). Se nada falhou, numa 2ª passada cria **três objetos de 0x58 bytes por aresta** (`FUN_140869850`: ligações aresta→laço, com o vértice original, a aresta compartilhada e o vértice da cópia) e marca `this+0x14b = 1`. É a montagem do laço [a, b, b', a'] de cada parede.
- **`FUN_141942e90(this, face)` limpa depois.** Junta, sem repetir, os itens do enumerador de arestas da face e, para cada um com `+0x58 == 0` (sem anel de uso), chama `FUN_1407ba210` (apagar; **SUPOSTA** a identificação). Antes, `FUN_1407f6940` limpa a seleção.

**Reinterpretação (SUPOSTA, mais coerente com todas as leituras):** o anel em `+0x58` é a lista de **usos de face da aresta** (cada nó liga uma face, ver `FUN_1408bc150`, que procura a face no anel). Então `FUN_1408b8940(aresta)` = **quantas faces usam a aresta**; "adjacent face has holes" = existe laço interno cuja aresta é usada por 2 ou mais faces; e a limpeza final apaga as **arestas que ficaram sem nenhuma face**. As "cadeias" M/F do esticar seriam cadeias de arestas (têm extremos em `+0x40/+0x48`). "This face cannot be stretched." = todas as arestas em volta dos vértices da seleção já pertencem só àquela face (face isolada, nada para esticar).

## Implementado no núcleo (a partir da leitura)

`core/topology/pushpull.py`: a regra "todas as vizinhas perpendiculares → a face desliza (mover); senão extrusa" já existia, mas usava a folga **1e-6**. O SketchUp usa **|n·n| < 0,001** nesse mesmo teste (`FUN_1406e4d40`, **CONFIRMADA**, ver rodada 9). Troquei por `_TOL_PERPENDICULAR = 1e-3`. Dois testes novos em `test_topology_pushpull.py`: inclinação de 5e-4 na parede ainda desliza (8 vértices, 12 arestas, 6 faces); 2e-3 vira extrusão (12/20/10). Suíte `test_topology*`: 131 testes OK.

**Não implementado, de propósito:** o modo esticar (vizinha inclinada arrastada), porque falta `FUN_141942080` (o tratamento em si) e o movimento dos vértices. A limpeza de arestas sem face e a fusão de colineares também ficam fora até o núcleo mostrar que precisa delas (o golden `r05` já passa).
