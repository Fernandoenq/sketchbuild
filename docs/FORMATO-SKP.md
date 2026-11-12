# Formato do `model.dat` (VFF 2021+): geometria

Levantado em 11/11/2026 com `tools/skp_inspect.py` sobre as receitas golden de F0 (SketchUp 26.2, `r01` a `r14`).
Tudo aqui foi **observado**, não deduzido de documentação. Onde há dúvida, a seção "Assunções" diz.
Convenções: registro = `tag uint16 + tamanho uint32 + valor`; números little-endian; coordenadas em polegadas.

## 1. Esqueleto (já usado pelo leitor e pela poda)

```
0x01f4 registro_externo            (tamanho + 6 = tamanho do model.dat)
  0x01f5 > 0x03e8 > 0x03e9 u16     PRÓXIMO ID DE ENTIDADE (= maior id usado + 1)  [confirmado em r01..r14]
  0x01f9 > 0x1770 > 0x1771 > 0x157c  definições (cada uma com 0x1388)
  0x01f6 > 0x1388                    raiz do modelo
```

Dentro de cada `0x1388` (entidades), em ordem:
`0x07d0` cabeçalho (id em `0x05dc>0x05de`, flags `0x07d3`), `0x1389` vértices, `0x138a` arestas, `0x138b` faces,
`0x138c` instâncias, `0x139e`, `0x138e` tabela de ids, `0x139b`, `0x139f`, `0x13a0` caixa limite.

## 2. IDs

O id mora em `0x05dc > 0x05de` como inteiro little-endian de **1 a 4 bytes** (tamanho mínimo). Os ids são
consecutivos na ordem de criação (r01: aresta 48880, vértices 48881 e 48882; contador final 48883).
Vértices, arestas, faces e curvas compartilham o mesmo espaço de ids.

## 3. Vértice `0x09c4` (44 bytes de valor, com id de 2 bytes)

```
0x09c4
  0x05dc [8]  > 0x05de [2]  id
  0x09c5 [24]               x, y, z  (3 × float64)
```

## 4. Aresta `0x0bb8` (43 bytes de valor, com ids de 2 bytes)

```
0x0bb8
  0x07d0 [21] > 0x05dc [8] > 0x05de id ; 0x07d3 [1] flags = 0x06 (padrão)
  0x0bb9 [2]  id do vértice inicial
  0x0bba [2]  id do vértice final
  0x0bbb [2]  (só em arestas de curva) id da curva a que pertence   [r09 círculo, r13 arco]
```
Flags `0x07d3`: base `0x06`; `+0x01` oculta, `+0x08` suave, `+0x10` lisa, `+0x20` travada.

## 5. Face `0x0dac`

```
0x0dac
  0x07d0 [21] > id ; 0x07d3 flags = 0x46 (padrão de face)
  0x0dad [32]  plano (A, B, C, D) em float64, com A·x + B·y + C·z + D = 0 e (A,B,C) = normal unitária
  0x0dae       laços
    0x1194     um por laço (o primeiro é o externo, os seguintes são furos)
      0x1195
        0x0fa0 [15]  um por aresta do laço, na ordem do percurso
          0x0fa1 [2] id da aresta
          0x0fa2 [1] 0 = percurso no mesmo sentido da aresta (inicial→final), 1 = sentido contrário
```
O laço externo é anti-horário em torno da normal gravada; os furos, horários (r10: laço externo com flags 1, furo
com flags 0). Os vértices da face não são gravados: saem das arestas.
Exemplos: r03 (retângulo no chão, normal -Z): plano `[0,0,-1,0]`; r04 (tampa em z=50, normal +Z): `[0,0,1,-50]`.

## 6. Tabela `0x138e` (ids dos filhos)

Lista de entradas `tamanho(1 byte) + id`, com os ids das **arestas, faces e instâncias** da entidade (os vértices
**não** entram). Em r10 aparece a instância do modelo base (45059) seguida de arestas e faces.

## 7. Caixa limite `0x13a0` [48]

Seis float64: `mín x, mín y, mín z, máx x, máx y, máx z` da definição **incluindo as instâncias** (no modelo de
exemplo, o boneco do modelo padrão entra na conta).

**Regra conferida em 11/11/2026** (arquivos reais r03, r10 e "Sem nome", salvos pelo SketchUp): em contêiner **sem instâncias** a caixa é exatamente o mín/máx dos vértices (1678 vértices da definição do boneco batem em 1e-6). Com instância, a caixa da raiz **não** é a dos oito cantos da caixa da definição transformados: no exemplo ela fica centrada na origem da instância (meia largura 24,352 em x e y; z igual ao da definição). A regra de instância segue **não decifrada**.

**RESOLVIDO em 12/11/2026 (`core/caixa_instancia.py`, `test_caixa_instancia.py`):** o boneco do arquivo real é um componente que **sempre olha para a câmera** (`SUComponentDefinitionGetBehavior`, `always_face_camera = 1`), e a caixa que a SDK calcula para a instância (`SUDrawingElementGetBoundingBox`) é exatamente o `0x13a0` gravado pelo SketchUp. Regras, conferidas em 25 casos aleatórios contra a SDK e contra os números do arquivo real:
- **instância comum:** caixa dos oito cantos da caixa da definição, transformados (a frase "não é a dos oito cantos" abaixo vale só para componente face-me);
- **face-me:** a caixa local vira `[-R, R]² x [zmin, zmax]` (`R` = maior `hypot(x, y)` entre os **cantos da caixa da definição**, não dos vértices) e entram os oito cantos transformados pela matriz da instância. **Generalizado em 12/11/2026** e conferido contra a SDK com giros em x, y e z e escala uniforme (30 casos aleatórios): com só giro em z dá a antiga fórmula de meia largura `R * (|cos t| + |sen t|)`. No arquivo real: R = 17,60676, t = 33°, meia largura 24,3516.

**Gravador (12/11/2026):** `gravar_cena` agora grava `0x13a0` na raiz = união da geometria solta com as instâncias da raiz (`_caixa_com_instancias`; definições aninhadas entram pela caixa das instâncias filhas); a caixa do grupo no arquivo gravado bate com a da SDK. O gravador não grava `always_face_camera`, então as instâncias gravadas são comuns. **Poda (12/11/2026):** a poda "total" agora recalcula o `0x13a0` também com instância viva (vértices que sobram + caixa de cada instância viva, face-me lido de `0x1b5d`; testes em `test_skp_poda_caixa.py` comparam com o mesmo desenho gravado sem a geometria oculta). **Falta:** a `Instancia` do núcleo não guarda `always_face_camera` (vem da definição, seção 7m); definições aninhadas (grupo dentro de grupo) conferidas em 12/11/2026. Texto antigo: a raiz só com instâncias ficava sem `0x13a0` (arquivos feitos pela SDK). Leitura original, mantida para histórico:

**Leitura de 12/11/2026 (`Sem nome.skp` e r10, os dois com a mesma instância do boneco):** a caixa da raiz é a **união** da caixa da geometria solta com a caixa da instância (em r10 o mín vem da instância e o máx, 200, da geometria). A caixa da instância fica **centrada na origem da instância** (-14,433; -24,632) com meia largura 24,352 em x e y e z igual ao da definição; a transformação é só rotação em z (-33°) mais translação, sem escala. A caixa da definição vai de x -7,225 a 17,607 e tem y = 0; a rotação dos oito cantos daria uma caixa bem menor (20,8 x 13,5), e nenhuma combinação simples dos extremos da definição dá 24,352. Hipótese: componente que sempre olha para a câmera (face-me), com caixa simétrica em torno da origem; sem segundo exemplo (outra instância ou outra rotação) não dá para fechar a fórmula, e a SketchUpAPI não grava `0x13a0` em contêiner só com instâncias, então não há oráculo local. O gravador segue sem `0x13a0` nesse caso. A poda total recalcula a caixa só em contêiner sem instâncias vivas; com instância viva mantém a antiga (só pode ser maior).

## 7b. Curva de arco `0x1397` (círculo e arco) — decifrada em 11/11/2026

Lugar: filho de `0x1388`, entre `0x1389` (vértices) e `0x138a` (arestas). Um `0x1397` guarda um `0x4c2c` por curva:

```
0x1397
  0x4c2c
    0x4a38              metadados
      0x05dc > 0x05de   id da curva (mesmo espaço de ids de vértices, arestas e faces)
      0x4a39 [u32]      número de arestas da curva
      0x4a3a [u8]       0 (tipo; só observado 0)
      0x4a3b [id]       id da primeira aresta (na ordem do desenho)
      0x4a3c [id]       id da última aresta
    0x4c2d [128]        16 doubles little-endian (polegadas, radianos)
```

Os 16 doubles de `0x4c2d`, conferidos contra 6 arquivos gerados pela SketchUpAPI com centro, raio, normal e início variados:

| Índices | Conteúdo |
|---|---|
| 0–2 | centro |
| 3–6 | plano A, B, C, D (normal unitária, D = -n·centro) |
| 7–9 | vetor X já multiplicado pelo raio (direção do ponto inicial) |
| 10–12 | vetor Y já multiplicado pelo raio (n × X) |
| 13 | raio |
| 14 | ângulo inicial (0 em todos os casos gerados) |
| 15 | ângulo final (varredura; círculo = 2π) |

Cada aresta membro leva `0x0bbb` = id da curva, depois de `0x0bba`. A tabela `0x138e` não lista curvas.

Validação: `tools/su_curvas.py` (SUEntitiesGetArcCurves) relê raio, centro, normal, eixos e ângulos do que o writer grava (3 testes novos). Observação: a DLL só enumera a curva quando as arestas NÃO têm face; nos arquivos feitos pelo SketchUp real (r09 círculo, r13 arco com raios) ela também devolve zero, então o comportamento bate. O círculo do SketchBuild (com face) grava o registro igual ao do SketchUp.

**Curva simples `0x1396`** (polígono, mão livre; a SketchUpAPI cria com `SUCurveCreateWithEdges`): mesmo lugar, mas só os metadados, sem `0x4c2c` e sem `0x4c2d`:
```
0x1396
  0x4a38  (um por curva)   0x05dc>0x05de id | 0x4a39 u32 nº de arestas | 0x4a3a u8=0 | 0x4a3b 1ª aresta | 0x4a3c última aresta
```
As arestas levam `0x0bbb` = id da curva, igual à curva de arco. Se uma aresta da curva é dividida em T, a curva passa a listar as duas metades, na ordem do percurso (o writer faz isso em `Topology._dividir_na_curva`); se uma aresta some, a curva inteira é ignorada e as arestas saem comuns.

Assunções: (1) ângulo inicial sempre 0 e X = direção do ponto inicial, o que o SketchUp faz nos arquivos gerados pela API; se o Ruby gravar outro X com ângulo inicial diferente, a geometria é a mesma; (2) a posição do id da curva no espaço de ids (aqui, depois das faces) não afeta a leitura pela DLL; (3) vários arcos dentro de um mesmo `0x1397` não foi confirmado em arquivo do SketchUp real.

## 7c. Material de cor na face — decifrado em 11/11/2026

Um material tem duas partes, e a cor mora só na segunda:

1. `model.dat`: `0x01f7 > 0x30d4 > 0x30d5 > 0x32c8` (um por material; `0x01f7` já existe vazio no modelo em branco):
   ```
   0x32c8
     0x05dc > 0x05de   id do material (mesmo espaço de ids da geometria)
     0x32cc            nome em UTF-8 (sem terminador)
     0x32ca [u8]       0 (só observado 0 = cor sólida, sem textura)
     0x32cb [0]        vazio
   ```
2. ZIP: entrada `materials/<nome>/material.xml` (antes de `materials/Layer_Layer0`). O XML leva `colorRed/Green/Blue`, `trans` (= 1 - alpha/255; 0.5 quando opaco), `useTrans` (1 se alpha < 255) e `pbrPromoState` (0 opaco, 2 com alpha). O resto do XML é fixo (bloco `mat:pbrMR` padrão). Barra e outros caracteres inválidos no nome viram `_` no nome da entrada.

Na face: frente = `0x07d1 [id]` dentro de `0x07d0` (entre `0x05dc` e `0x07d3`); verso = `0x0daf [id]` direto no registro da face, antes de `0x0dad`. O inteiro de integridade do cabeçalho precisa ser refeito porque entram entradas novas no ZIP (o writer já faz).

Como foi descoberto: `tools/tlv_diff.py` entre arquivos gerados pela SketchUpAPI (sem material, vermelho, azul, vermelho+verso verde). Pintar pela API sem `SUModelAddMaterials` NÃO grava a cor: o material sai como `_auto_` sem XML.

Validação: a SketchUpAPI relê cor da frente, cor e alpha do verso (`test_material_frente_e_verso_com_alpha`).

Assunções: (1) nomes não ASCII entram no ZIP em UTF-8 com o flag de nome UTF-8 do Python; o SketchUp grava os bytes crus sem o flag, não testado no SketchUp real; (2) material com textura (`hasTexture=1`, imagem no ZIP) não decifrado; (3) o flag de face 0x46 (Ruby) contra 0x06 (API) segue sem efeito conhecido.

## 7e. Material com textura (imagem) — decifrado em 12/11/2026

Oráculo: `tools/gerar_textura_api.py` gera pela SketchUpAPI `cor.skp` (face azul lisa) e `textura.skp` (mesma face com um PNG 8x8), comparados com `tools/tlv_diff.py`. A diferença é mínima:

- `model.dat`: o `0x32c8` do material ganha só um filho `0x32cd` (u32 = 90; igual ao `cd_tag` do código antigo `create_textured_material`). Nada muda na face: a projeção padrão da imagem não grava UV.
- ZIP: `materials/<nome>/<imagem>` com o arquivo original e `material.xml` com `type="1"`, `hasTexture="1"`, `colorRed/Green/Blue` = cor média da imagem e um bloco `<mat:texture textureFilename xScale yScale avgColor>` com `<mat:images><mat:image id="1" path="./<imagem>" file_name="<imagem>"/>`. `avgColor` = ARGB da cor média (0xFF7F007F para o xadrez azul/vermelho).
- O SketchUp grava em `textureFilename` o caminho absoluto de onde a imagem veio; o gravador escreve só o nome do arquivo.
- Conferido pela DLL: `SUMaterialGetType` = 1 (texturizado) no arquivo do gravador.
- **Assunções pendentes:** significado do valor 90 em `0x32cd`; unidade de `xScale`/`yScale` (gravamos o que o usuário passa, o oráculo usou 1,0); textura posicionada (UV por face) não gravada; falta abrir `~/sketchup_gerados/textura/meu.skp` no SketchUp real.

## 7f. Tags (camadas) e cenas — decifrado em 12/11/2026

Oráculo: `tools/gerar_tags_api.py` (base, tag visível, tag desligada, cena), comparado com `tools/tlv_diff.py`.

**Tag** — tudo mais é igual ao modelo vazio; muda só:

```
0x01f8 > 0x3a98 > 0x3a99 > 0x3c8c (um por tag; a Layer0 já vem, id 4)
  0x05dc > 0x05de   id da tag (mesmo contador dos demais ids)
  0x3c8d            nome (utf-8)
  0x3c8e            1 byte: 1 = tag DESLIGADA (oculta), 0 = visível
  0x3c8f > 0x32c8   material da tag: id = id da tag + 1, 0x32cc = "Layer_<nome>", 0x32ca = 1, 0x32cb vazio
  0x3c90            u32 = 0
```

- ZIP: `materials/Layer_<nome>/material.xml` com cor 0,0,0 e `pbrPromoState="0"` (a Layer0 do modelo vazio é 255,84,84 e promo 2).
- Entidade em tag: `0x07d2` (id da tag) no cabeçalho `0x07d0`, entre `0x07d1` (material) e `0x07d3` (flags).
- O gravador (`core/topology/tag.py`, `Face.tag`) grava só as tags usadas por alguma face, em ordem alfabética, cada uma com dois ids.
- Aresta (`0x0bb8`), grupo e componente (`0x1964`) usam o mesmo `0x07d2` no `0x07d0`; conferido pela DLL (`SUDrawingElementGetLayer`) em face, aresta solta e grupo. No núcleo: `Face.tag`, `Topology.etags` (propagada ao dividir/limpar arestas) e `Instancia.tag`.
- **Assunções pendentes:** a tag de aresta de borda de face não é herdada quando a face muda de forma (Push/Pull cria arestas novas sem tag); visibilidade por cena não gravada.

**Cena** — gravada pelo `gravar_cena` (`Cena.adicionar_cena`), conferida pela DLL (nome, descrição, "incluir na animação", olho e alvo da câmera). Oráculo: `tools/gerar_cenas_api.py` (7 variações). Achados:
- Uma cena criada pela SDK só tem nome/descrição e o flag `0x7152`; `SUSceneSetCamera` não grava `0x714a` e `SUSceneAddLayer` não deixa rastro. Por isso a câmera da cena é gravada como nas cenas reais (arquivo do Fernando com 4 cenas): `0x7149` (u32; 1 com câmera) + `0x714a > 0x34bc` (mesma estrutura da câmera do modelo, `0x01fa > 0x34bc`: `0x34bd` olho, `0x34be` alvo, `0x34bf` cima ortogonalizado, demais campos copiados do modelo base).
- Cena real tem muito mais: `0x714d` (estilo/opções de renderização, `0x733c` com ~70 campos), `0x714e` (sombras: data, hora, latitude, longitude, cidade), `0x715b`, `0x714f` (plano de seção), `0x7158` (miniatura em `scene_thumbnails/`). Nada disso é gravado.
- **Assunções pendentes:** `0x7149` = 1 com câmera (bits dos "usar ..." não decifrados; o valor real observado foi 0x3ff com tudo ligado); `0x34c3` (muda com a câmera, função desconhecida) fica o do modelo base; visibilidade de tags por cena e estilo por cena não gravados; miniatura ausente (o SketchUp a recria ao salvar).

**Cena, formato do registro mínimo (SDK):** `0x0207 > 0x6d60 > 0x6d61` (vazio sem cenas) passa a ter um `0x7148` por cena com `0x6f54{0x05dc>0x05de id, 0x6f55 nome, 0x6f56 vazio}`, `0x7149 = 0` (u32), `0x7152 = 1`, `0x7153` vazio, `0x7154` e `0x7155` = -1.0 (double), `0x715c` vazio, `0x7157 = 1`. Uma cena criada só com nome não leva câmera nem estilo; o que cada campo controla (câmera, visibilidade por tag) falta decifrar com cenas reais.

## 7g. Bits de `0x07d3` (flags de entidade) — decifrado em 12/11/2026

Oráculo: `tools/gerar_flags_api.py` muda uma propriedade por vez pela SketchUpAPI e lê o byte `0x07d3` do cabeçalho da face e das arestas.

| Bit | Significado | Evidência |
|---|---|---|
| `0x01` | oculta (hidden) | face e aresta: 0x06 -> 0x07 |
| `0x02` | projeta sombra | desligar: 0x06 -> 0x04 |
| `0x04` | recebe sombra | desligar (face): 0x06 -> 0x02 |
| `0x08` | aresta suave (soft) | `SUEdgeSetSoft`: 0x06 -> 0x0e |
| `0x10` | aresta lisa (smooth) | `SUEdgeSetSmooth`: 0x06 -> 0x16 |
| `0x40` | **desconhecido** | só aparece nos arquivos salvos pelo SketchUp (faces 0x46), nunca nos da SDK |

O padrão da SDK é 0x06 (projeta e recebe sombra). O gravador usa 0x06 nas arestas (`| eflags`) e 0x46 nas faces. Núcleo: `Topology.eflags` (herdada na divisão em T, na limpeza de vértice e ao agrupar/explodir) e `core/topology/soften.py` (`definir`, `limpar`, `por_angulo`). Conferido pela DLL (`SUEdgeGetSoft`). **Bit 0x40 (12/11/2026):** aparece em todas as faces salvas pelo SketchUp e nunca nas da SDK; o gravador já grava 0x46 nas faces, igual ao original, e nenhuma função da SDK lê esse bit, então fica sem efeito observável e sem nome (provável marca de face/geometria viva). **Pendente:** sombra de face/aresta não tem controle no núcleo; efeito de suave+lisa na malha (normais) não implementado no leitor.

## 7h. Guias e plano de seção — decifrado em 12/11/2026

Oráculo: `tools/gerar_anotacoes_api.py` (base, ponto de guia, linha infinita, linha finita, plano de seção). Cada um entra em `0x1388` **depois das faces/instâncias e antes de `0x139e`**, e o id também entra na tabela `0x138e` (diferente dos vértices):

```
0x1392 > 0x426c   ponto de guia
  0x4268 > 0x07d0   cabeçalho (id, flags 0x06)
  0x426d            posição (3 doubles)
  0x426e            3 doubles = 0 (função desconhecida)
  0x426f            1 byte = 0
0x1391 > 0x4269   linha de guia
  0x4268 > 0x07d0   cabeçalho
  0x426a            8 doubles: início (3), direção unitária (3), t mín, t máx
                    infinita: -1e30 e 1e30; finita: 0 e o comprimento
  0x426b            2 bytes = ff ff (função desconhecida)
0x1393 > 0x445c   plano de seção
  0x07d0            cabeçalho direto (sem 0x4268)
  0x445d            plano A, B, C, D de A x + B y + C z + D = 0 (4 doubles)
  0x445e, 0x445f    vazios
```

Núcleo: `Topology.guias`, `Topology.secoes` e `core/topology/guias.py` (`guia_ponto`, `guia_linha`, `plano_secao`, `apagar`); rota `POST /draw/guide`. Conferido pela DLL (`SUEntitiesGetNumGuidePoints/GuideLines/SectionPlanes` = 1/2/1).
**Pendente:** `0x426e` e `0x426b`; cor, texto e visibilidade da guia; plano de seção ativo/inativo e nome (`0x445e`/`0x445f` vazios); **texto e cotas**: `SUTextSetPoint` derruba a DLL (violação de acesso) e um texto sem ponto falha ao salvar (`SU_ERROR_SERIALIZATION`), então o REA de texto/cota precisa de arquivos reais do SketchUp; guias sem caixa limite (a DLL não grava `0x13a0` com guias).

## 7i. Lacunas que a SketchUpAPI desta instalação não deixa decifrar (12/11/2026)

Tentativas com falha, para ninguém repetir sem outra fonte:
- **Textura posicionada (UV):** RESOLVIDO em 12/11/2026, ver a seção 7j. O crash era a ordem dos campos de `SUMaterialInput` (o material vai por último, offset 0x68), descoberta lendo a DLL no REA.
- **Texto:** RESOLVIDO em 12/11/2026 (seção 7l). Dois erros meus: `SUTextSetPoint(texto, ponto, caminho_de_instância)` tem 3 parâmetros (o terceiro é opcional) e o texto novo nasce sem fonte, então o `.skp` não serializava; a fonte vem de `SUModelGetFonts` + `SUTextSetFont`. (Histórico do beco sem saída: a chamada crashava com endereço 0x6, depois salvava com `SU_ERROR_SERIALIZATION`.)
- **Cota linear:** RESOLVIDO em 12/11/2026 (seção 7k). O crash era a assinatura: `SUDimensionLinearCreate(dim*, ponto_ini*, caminho, ponto_fim*, caminho)`, com os caminhos de instância opcionais.
- `0x1399` = contêiner de cotas (ver 7k); a dúvida abaixo é histórica. O arquivo real do Fernando que tem `0x1399` (registro desconhecido com materiais referenciados, `0x5bcc`/`0x59d8`/`0x5208`) pode ser texto/cota/imagem; sem rótulo não dá para afirmar.
Tentativa de gerar esses arquivos no SketchUp 2026 real, sem ninguém na frente (12/11/2026): `SketchUp.exe -RubyStartup script.rb` abre o programa mas o script não roda (nenhum log, nenhum arquivo em 5 minutos); a instância foi fechada. Para usar o SketchUp real é preciso abri-lo à mão e carregar o script pelo Console Ruby, como em `ruby_bridge/f0_receitas.rb`. O script pronto está em `ruby_bridge/gerar_anotacoes_reais.rb` (texto, cota, textura posicionada, instâncias a 0/90/33° e grupo).
Próxima fonte possível: arquivos reais do SketchUp com texto, cota e textura posicionada, comparados com a mesma cena sem o elemento.

 Definições, grupos e componentes — decifrado em 11/11/2026

Amostras geradas pela SketchUpAPI (grupo, componente, 2 instâncias, rotação, escala, espelho, aninhado) e comparadas com `tools/tlv_diff.py`.

**Definição** (grupo e componente usam o mesmo registro): `0x01f9 > 0x1770 > 0x1771 > 0x157c`, um por definição.
```
0x157c
  0x1388                     entidades da definição: 07d0, 1389, 1397?, 138a, 138b, 138c?, 138d?, 139e, 138e, 139b, 139f
  0x157d [16]                GUID aleatório
  0x157e                     nome (componente: nome dele; grupo: "Group", "Group1", ...)
  0x157f                     "Group" se for grupo, vazio se componente
  0x1580 [0]   0x1582 [u8=0]
  0x1583 [u32]               1 = grupo, 0 = componente
  0x1581 [u32]               carimbo de tempo Unix (segundos) da criação
  0x1b58 [48]                bloco constante          0x1585 [275]  bloco constante (câmera/eixos padrão), independe da geometria
```
Dentro de `0x1388` da definição: `0x139f` = 0 e SEM `0x13a0` (caixa limite), mesmo com geometria; `0x139e` vazio e `0x139b > 0x639f > 0x63a0` iguais aos da raiz; a tabela `0x138e` lista arestas, faces e ids das instâncias filhas. O cabeçalho `0x07d0` do componente leva o dicionário de atributos `SU_DefinitionSet` (Price, Size, Url) em `0x05dc > 0x05dd`; o do grupo é só id + flags.

**Instância** `0x1964`:
```
0x1964
  0x07d0                     cabeçalho (componente: com atributos SU_InstanceSet Owner/Status; grupo: só id + flags)
  0x1965                     nome da instância (grupo: o nome dado; componente: vazio)
  0x1966 [104]               13 doubles: matriz 3x3 por linhas (m[r][c]) + translação (3) + 1.0
  0x1967 [id]                id da definição
  0x1968 [16]                GUID aleatório
```
Onde ficam: componentes em `0x138c > 0x1964`; grupos em `0x138d > 0x1d4c > 0x1964`. Esses contêineres entram em `0x1388` da raiz (ou da definição pai) depois de `0x138b` e antes de `0x139e`. A matriz do SketchUp vem em ordem de colunas (m[0..15]); o registro guarda por linhas: `[m0,m4,m8, m1,m5,m9, m2,m6,m10, m12,m13,m14, 1]`. Escala e espelho entram direto na matriz 3x3.

**Ordem das definições na lista:** filhos antes dos pais. Se uma definição aparecer antes da definição que ela instancia, a SketchUpAPI carrega o modelo mas não enxerga o grupo aninhado (foi o bug da primeira versão). A raiz continua sem `0x13a0` quando só tem instâncias; com geometria solta, a caixa cobre só a geometria (assunção).

Validação (`test_grupo_e_componente_com_transformacao`, `test_grupo_aninhado_e_material_na_definicao`): a DLL relê nome do grupo, faces dentro do grupo, 3 instâncias com as matrizes de rotação, translação e escala idênticas, nome da definição, grupo aninhado e a cor do material dentro da definição; `verificar_skp` sem referências quebradas.

Assunções: (1) vários grupos num mesmo `0x138d` (cada um num `0x1d4c`) e várias instâncias num `0x138c` foram vistos na API mas não em arquivo do SketchUp real; (2) o carimbo `0x1581` e os GUIDs podem ser validados pelo SketchUp, não testado; (3) bbox da raiz com instâncias; (4) tag/camada da instância não escrita (padrão); (5) espelho: o SketchUp pode ajustar a orientação das faces, só a matriz foi conferida.

## 8. O que ainda não está mapeado (próximos passos do REA)

| Tópico | Estado |
|---|---|
| Material de cor, frente e verso | decifrado na seção 7c |
| Material com textura (imagem) | não decifrado |
| Curva de arco (`0x1397`, `0x0bbb`) | decifrado na seção 7b e gravado pelo writer |
| Curva simples (`0x1396`, polígono/mão livre): só `0x4a38`, sem `0x4c2d` | observado, ainda não gravado |
| Arestas suaves e lisas, na face e na aresta | flags conhecidas, efeito na malha não verificado |
| Grupos e componentes novos (`0x1964`, `0x138d`, `0x1967`) | decifrado na seção 7d e gravado |
| Guias, textos, cotas, planos de seção | gravador por patch já escreve alguns, sem receita golden |
| Laços da face em definições (mesmo layout, mas com `0x138e` própria) | não testado |
| Tamanho do id quando passa de 65535 (3 bytes) | só observado em modelos grandes |

## 9. Assunções pendentes

1. A ordem dos registros dentro de `0x1388` (vértices, arestas, faces, instâncias) é exigida pelo SketchUp?
   O gravador mantém a ordem observada.
2. `0x07d3 = 0x46` na face: bit `0x40` desconhecido (presente em todas as faces observadas).
3. O contador `0x03e9` precisa ser maior que qualquer id; se isso for violado o SketchUp pode recusar ou reaproveitar ids.
4. A caixa limite precisa ser recalculada; um valor velho provavelmente só afeta o zoom, não a abertura (a confirmar).

## 7j. Textura posicionada (UV) por face `0x2710` — decifrada em 12/11/2026

Oráculo: `tools/gerar_uv_api.py` (SketchUpAPI, `SUGeometryInputFaceSetFrontMaterial` com `SUMaterialInput` = `num_uv_coords`, `uv_coords[4]`, `vertex_indices[4]`, `material`; 112 bytes, material por último). Comparação com `tools/tlv_diff.py` entre a face com textura padrão e com UV: a face sem posicionamento não tem `0x2710`.

Lugar: dentro do cabeçalho da face, `0x07d0 > 0x05dc > 0x05dd > 0x36b1 > 0x36b2 > 0x2710`:

```
0x2710
  0x36b0               vazio
  0x2711               frente
    0x2713
      0x2714 [u32]     1 (frente posicionada)
      0x2715 [72]      matriz 3x3 em f64, por linhas
      0x2716 [24]      3 x f64 = 0 (significado desconhecido; sempre 0 nos casos testados)
      0x2717           vazio
  0x2712               verso (sem posicionamento)
    0x2713
      0x2714 [u32]     0
      0x2715 [72]      identidade
      0x2716 [24]      zeros
      0x2717           vazio
```

**Matriz** `M` (linhas `[a b 0] [c d 0] [tx ty 1]`): `[u v 1] * M = [x y 1]`, isto é, leva a coordenada de textura ao plano da face. Conferido em quatro casos num quadrado de 100 pol no plano z=0 (normal +z), com UV nos cantos (0,0), (100,0), (100,100), (0,100):

| UV nos cantos | `M` |
|---|---|
| (0,0) (2,0) (2,2) (0,2) | `diag(50, 50, 1)`; 50 = tamanho do ladrilho em polegadas |
| mesmo com 4 em vez de 2 | `diag(25, 25, 1)` |
| deslocado (0,25; 0,5) | `diag(50, 50, 1)` com `tx = -12,5` e `ty = -25` (`-u0 * 50`, `-v0 * 50`) |
| (0,0) (0,2) (-2,2) (-2,0) | `[[0,-50,0],[50,0,0],[0,0,1]]` (`u = -y/50`, `v = x/50`) |

**Pendente:** eixos x/y do plano em face inclinada (aqui sempre x e y do mundo); UV com perspectiva (4 pontos que não formam transformação afim; a SketchUpAPI só aceita o par de cantos); `0x2716`; textura posicionada no verso; textura posicionada no verso.

**Gravador (12/11/2026):** `core/skp_topology_writer.py` (`_bloco_uv`) grava o bloco; núcleo: `Face.uv`, `core/topology/material.py` (`matriz_uv`, `posicionar_textura`). `uv` só vai ao arquivo se a frente tem material; limpar a frente tira o `uv`; Push/Pull e divisão de face levam o `uv`; explodir grupo descarta (o plano mudaria de lugar). Testes em `test_skp_uv.py` conferem os números dos quatro casos da SDK.

## 7k. Cota linear `0x1399 > 0x5bcc` — decifrada em 12/11/2026

Oráculo: `tools/gerar_cotas_api.py` (uma cota por modelo e uma mudança por variação, comparadas com `tools/tlv_diff.py`). O gravador reproduz o registro **byte a byte** nos 9 casos (`test_skp_cotas.py`). Lugar: filho de `0x1388`, depois das guias e antes de `0x139e`; um `0x5bcc` por cota; o id da cota entra na tabela `0x138e`.

```
0x1399
  0x5bcc
    0x59d8
      0x07d0 (cabeçalho: id da cota, flags 0x06)
      0x59d9 [texto UTF-8]  vazio = o SketchUp mostra a medida
      0x59db [u8]           texto 3D (`SUDimensionSetText3D`): 0 ou 1
      0x59dc [u32]          tipo de seta (SUDimensionSetArrowType: 0, 1, 2 gravados como 0, 1, 2)
    0x5bcd                  ponto inicial
      0x5208
        0x5209 [u32]        1
        0x520a [3 x f64]    posição
        0x520b > 0x53fc > 0x53fe   vazio (caminho de instância)
        0x520c > 0x53fc > 0x53fe   vazio
    0x5bce                  ponto final (mesma forma)
    0x5bcf [3 x f64]        normal do plano da cota (padrão 0,0,1)
    0x5bd0 [3 x f64]        eixo X (padrão 1,0,0)
    0x5bd1 [u32]            0
    0x5bd3 [f64]            deslocamento x do texto no plano da cota (0 = padrão)
    0x5bd2 [f64]            deslocamento y do texto (distância da linha de cota)
    0x5bd4 [u32]            alinhamento vertical (padrão 1; `SetVerticalAlignment(1)` gravou 0)
```

`SUDimensionLinearSetPosition(50, 25, 5)` com início em (0,0,0) gravou `0x5bd3 = 50` e `0x5bd2 = 25` (o z some: é a posição projetada no plano da cota). `SetHorizontalAlignment(1)` gravou `0x5bd3 = -1.0` (alinhamento horizontal mora no mesmo campo, como sentinela quando não há posição). **Texto 3D e fonte da cota (12/11/2026):** `SUDimensionSetText3D(true)` grava 1 em `0x59db`; `SUDimensionSetFont(fonte)` acrescenta `0x59da` (u8 = id da fonte: 2 ou 3 no modelo em branco) entre `0x59d9` e `0x59db` (sem a chamada o registro não existe). `cota_linear(texto_3d=, fonte=)` e `POST /note` reproduzem os 4 casos byte a byte. Sobraram sem função na SDK: `0x5bd1`, `0x59dc` já é a seta; `SUDimensionSetStyle` precisa de um `SUDimensionStyleRef` que a DLL não cria.

**Alinhamento horizontal (12/11/2026, `SUDimensionLinearSetHorizontalAlignment`):** valores 0, 1 e 2 gravam em `0x5bd3` 0.0, -1.0 e +1.0 (3 e 4 são recusados pela SDK); é o mesmo campo do x do deslocamento, então vale o que for posto por último (posição depois do alinhamento: x = posição; alinhamento depois da posição: x = sentinela e o y fica). `cota_linear(alinhamento_h=)` e `POST /note` reproduzem os 6 casos byte a byte. **Deslocamento × ponto inicial (12/11/2026):** não há relação: `SUDimensionLinearSetPosition(x, y, z)` grava `x` em `0x5bd3` e `y` em `0x5bd2` crus (o `z` some), seja qual for o início (fora da origem em x, y e z), a direção da cota, o início oblíquo, a normal em y ou o eixo X em y; 8 casos byte a byte em `test_skp_cotas.py`. O que o SketchUp real faz ao arrastar o texto (projetar no plano da cota) é da interface, não do formato. **Pendente:** cota angular/raio/diâmetro, estilo e fonte da cota, caixa limite com cota (a raiz sem geometria não gravou `0x13a0`), exposição no app.

## 7l. Texto livre `0x1398 > 0x55f0` — decifrado em 12/11/2026

Oráculo: `tools/gerar_texto_api.py` (um texto por modelo e uma mudança por variação). O gravador reproduz o registro **byte a byte** nos 8 casos (`test_skp_texto.py`). Lugar: filho de `0x1388`, depois das guias e antes das cotas (`0x1399`); o id entra na tabela `0x138e`.

```
0x1398
  0x55f0
    0x07d0 (cabeçalho: id do texto, flags 0x06; com cor, ganha 0x07d1 com o id de um material "_auto_")
    0x55f1 [UTF-8]        o texto
    0x55ff                vazio
    0x55f2 [f64]          0,5   (posição de tela? padrão, sem teste)
    0x55f3 [f64]          0,5
    0x55f4 > 0x5208       ponto (0x5209 u32 = 1; 0x520a 3 x f64; 0x520b e 0x520c vazios, como na cota)
    0x55f5 [3 x f64]      vetor da linha de chamada (SUTextSetLeaderVector)
    0x55f6 [u8]           1    (padrão, sem teste)
    0x55f7 [3 x f64]      0,0,1 (padrão, sem teste)
    0x55f8 [u8]           0    (padrão, sem teste)
    0x55f9 [u8]           id da fonte (2 = primeira fonte do modelo em branco, 3 = segunda)
    0x55fa [u32]          tipo de seta (SUTextSetArrowType)
    0x55fb [u32]          1    (padrão, sem teste)
    0x55fc [u8]           1    (padrão, sem teste)
    0x55fd [u32]          tipo da linha de chamada (SUTextSetLeaderType: 0, 1, 2)
    0x55fe [u32]          0    (padrão, sem teste)
```

**Cor** (`SUTextSetColor`) — decifrada em 12/11/2026: a SDK cria o material automático no fim da lista `0x01f7 > 0x30d4 > 0x30d5` (`0x32c8`: `0x05dc > 0x05de` id, `0x32cc` = `_auto_`, `0x32ca` = 0, `0x32cb` vazio) e a cor vai só no `materials/_auto_/material.xml` (nome `<auto>`, `colorRed/Green/Blue`). O material toma o id livre seguinte e o texto, o seguinte (material `0x12`, texto `0x13` no modelo em branco); o id do material entra em `0x07d1` do cabeçalho do texto. Gravador: `texto_livre(..., cor=(r,g,b[,a]))`, material `<auto>` em `Topology.materiais`; o `0x1398`, o `0x32c8` e o XML saem byte a byte iguais aos da SDK (`test_skp_texto.py`); `POST /note` aceita `cor`. **Assunção pendente:** só uma cor de texto por modelo (com duas, o nome do segundo material automático não foi observado; o núcleo recusa). **Posição na tela (12/11/2026):** `SUTextSetScreenPosition(texto, x, y)` (x e y de 0 a 1; só com linha de chamada tipo 0, senão a SDK devolve erro) grava `x` em `0x55f2` e `y` em `0x55f3` (padrão 0.5, 0.5); `texto_livre(tela=)` e `POST /note` reproduzem os 3 casos byte a byte. Os outros campos "padrão" (`0x55f6`, `f7`, `f8`, `fb`, `fc`, `fe`) seguem sem variação na SDK.

**Fonte nova** (`SUModelAddFont(modelo, entrada, saída)`, assinatura lida no pseudocódigo: entrada = versão 1, nome, dois bytes, pontos, flag e tamanho no mundo) — decifrada em 12/11/2026: o modelo só serializa a fonte se algum texto a usa; ela vira um registro no fim da lista `0x01fd > 0x4e20 > 0x4e21`: `0x5014 { 0x05dc>0x05de id, 0x5015 nome UTF-8, 0x5016 negrito u8, 0x5017 itálico u8 (conferidos por `SUFontGetBold/Italic`), 0x5018 pontos u32, 0x5019 u8 = 0 (tamanho no mundo desligado), 0x501a f64 = 0.0 }` e o id dela vai em `0x55f9` do texto. As duas fontes do modelo em branco (ids 2 e 3) têm `0x501a` = 1.0. A fonte toma o id livre antes do material de cor, **independente da ordem de criação** (conferido pondo a cor antes da fonte na SDK: arquivo com os mesmos ids). Gravador: `texto_livre(..., fonte_nova=(nome, negrito, itálico, pontos))`, fontes iguais compartilham o registro; `POST /note` aceita `fonte_nova`; `0x1398` e a lista de fontes saem byte a byte iguais aos da SDK em 6 casos (`test_skp_texto.py`). **Pendente:** tamanho no mundo (`0x5019`/`0x501a` com `SUFontInput` flag ligada) sem teste; campos "padrão, sem teste" acima segunda cor de texto; caixa limite com texto; exposição no app.

**Ordem de ids texto × cota (resolvida em 12/11/2026, `tools/gerar_texto_cota_api.py`):** a SDK numera pela ordem de **inclusão nas entidades**, não de criação (criar texto antes mas incluir a cota primeiro dá cota = 0x12, texto = 0x13). O gravador numera na ordem de criação no núcleo (que no app é a de inclusão) e a tabela 0x138e fica em ordem crescente de id; conferido byte a byte (`0x1398`, `0x1399`, `0x138e`) nas duas ordens.

**Ids de guias, seções, cotas e textos (resolvido em 12/11/2026, `tools/gerar_ordem_guias_api.py`):** todos entram numa só sequência pela ordem de inclusão nas entidades (ponto de guia, linha de guia e plano de seção misturados; conferido nas ordens psl, slp, lps, spl). O gravador numera os quatro tipos pela ordem de criação do núcleo. Detalhe de ponto flutuante: a direção unitária da linha de guia sai de `c * (1/n)`, não de `c / n` (1 ulp de diferença, só aparecia na comparação byte a byte). **Ids da geometria (decisão, 12/11/2026):** num retângulo feito pela SDK os ids saem 0x12 aresta, 0x13 e 0x14 vértices, 0x15 aresta, 0x16 vértice, 0x17 aresta, 0x18 vértice, 0x19 aresta, 0x1a face (cada aresta antes dos vértices novos dela, na ordem em que a SDK a cria). Isso é consequência do histórico de criação, não uma regra do formato: o SketchUp numera na ordem em que cria cada entidade e o `SUGeometryInput` tem a sua ordem própria, então não há ids canônicos para comparar. O gravador numera vértices, arestas e faces em blocos; o arquivo abre na DLL e o primeiro id livre é o mesmo. Não vale reproduzir a intercalação sem um arquivo do SketchUp real com histórico conhecido.

## 7m. Comportamento do componente `0x157c > 0x1b58` — decifrado em 12/11/2026

Oráculo: `tools/gerar_comportamento_api.py` (`SUComponentDefinitionSetBehavior`) + diff de `tools/tlv_diff.py` entre `base.skp` e uma variação por vez.

```
0x1b58 [reg]  comportamento (cauda da definição, antes de 0x1585)
  0x1b59 [u32]  tipo do snap menos 1 (0 se sem snap): 0 qualquer, 1 horizontal, 2 vertical, 3 inclinado
  0x1b5a [u32]  0    (nunca mudou nas 8 variações; sem teste)
  0x1b5b [u8]   snap ligado (1 se `SUSnapTo` ≠ nenhum)
  0x1b5c [u8]   cortar abertura (cuts_opening)
  0x1b5d [u8]   sempre de frente para a câmera (always_face_camera)
  0x1b5e [u8]   sombra segue o sol (shadows_face_sun)
```

- Núcleo: `Cena.definir_comportamento(definicao, face_me, corta_abertura, sombra_sol)`; só componentes (grupo e raiz dão erro).
- Gravador: `_comportamento(...)` reproduz byte a byte o registro da SDK nos quatro casos; com `face_me` a caixa `0x13a0` da raiz usa a fórmula face-me (seção 7).
- **Pendências:** `0x1b5a` nunca variou; API `POST /api/v1/draw/behavior` e botões Agrupar/Componente/Entrar/Sair/Comportamento no front (Comportamento age no componente em que se entrou; `node --check`, sem teste em navegador); caixa face-me conferida com giros em x/y/z e escala uniforme (escala não uniforme e espelhamento em x ou z também conferidos, 72 casos).

## 7n. Pendências que dependem de insumo externo (12/11/2026)

- **Herança de cor no Push/Pull:** a SDK não tem PushPull; o único oráculo seria um arquivo salvo pelo SketchUp real com uma extrusão de face pintada. Os `.skp` disponíveis na máquina são do projeto Parkelô, vetados por instrução, e os arquivos reais já usados (r03, r04, r10, "Sem nome") não têm essa operação. Segue como assunção (paredes herdam a frente da face puxada); trocar assim que houver um arquivo real.
- **Teste do front no navegador:** a extensão do Chrome não estava conectada (`tabs_context_mcp` falhou); um servidor isolado na porta 8765 subiu e respondeu 200, e foi encerrado. Verificação feita só com `node --check` e testes de API.
- **Cota radial/diâmetro (`SUDimensionRadialCreate(saida, curva)`):** tentativa de 12/11/2026 com `tools/gerar_cota_radial_api.py` falhou: access violation (leitura em 0x15) mesmo com o arco incluído nas entidades e relido por `SUEntitiesGetArcCurves`. Pelo pseudocódigo (`FUN_1800bb200`) ela confere que a curva é de arco (senão devolve 0x12), lê o objeto do arco em `curva + 0x20` e copia raio/ângulos; a causa do crash não foi achada (hipóteses não testadas: precisa de modelo com estilo/unidades carregados, ou de o arco ser um círculo completo). **Segunda tentativa (círculo completo, 24 lados): o mesmo crash.** A DLL não exporta criação de cota angular nem de diâmetro (`SUDimensionAngularCreate` e `SUDimensionDiameterCreate` não existem; só `SUDimensionLinearCreate` e `SUDimensionRadialCreate`), então não há oráculo da SDK para angular e diâmetro. Fica sem oráculo local: só um `.skp` salvo pelo SketchUp real com essas cotas resolveria. Não repetir a mesma chamada sem outra hipótese.
- **`0x1b5a`:** nunca variou nas 8 variações do `SUComponentBehavior` (snap, corta abertura, face-me, sombra); gravado 0.

