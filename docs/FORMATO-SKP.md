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

**Regra conferida em 11/11/2026** (arquivos reais r03, r10 e "Sem nome", salvos pelo SketchUp): em contêiner **sem instâncias** a caixa é exatamente o mín/máx dos vértices (1678 vértices da definição do boneco batem em 1e-6). Com instância, a caixa da raiz **não** é a dos oito cantos da caixa da definição transformados: no exemplo ela fica centrada na origem da instância (meia largura 24,352 em x e y; z igual ao da definição). A regra de instância segue **não decifrada**. A poda total recalcula a caixa só em contêiner sem instâncias vivas; com instância viva mantém a antiga (só pode ser maior).

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

**Cena** (só lida, ainda não gravada): `0x0207 > 0x6d60 > 0x6d61` (vazio sem cenas) passa a ter um `0x7148` por cena com `0x6f54{0x05dc>0x05de id, 0x6f55 nome, 0x6f56 vazio}`, `0x7149 = 0` (u32), `0x7152 = 1`, `0x7153` vazio, `0x7154` e `0x7155` = -1.0 (double), `0x715c` vazio, `0x7157 = 1`. Uma cena criada só com nome não leva câmera nem estilo; o que cada campo controla (câmera, visibilidade por tag) falta decifrar com cenas reais.

## 7d. Definições, grupos e componentes — decifrado em 11/11/2026

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
