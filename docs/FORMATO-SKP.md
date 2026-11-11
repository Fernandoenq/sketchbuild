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

Assunções: (1) ângulo inicial sempre 0 e X = direção do ponto inicial, o que o SketchUp faz nos arquivos gerados pela API; se o Ruby gravar outro X com ângulo inicial diferente, a geometria é a mesma; (2) a posição do id da curva no espaço de ids (aqui, depois das faces) não afeta a leitura pela DLL; (3) vários arcos dentro de um mesmo `0x1397` não foi confirmado em arquivo do SketchUp real.

## 8. O que ainda não está mapeado (próximos passos do REA)

| Tópico | Estado |
|---|---|
| Material frontal e do verso na face | não observado (receitas sem material) |
| Curva de arco (`0x1397`, `0x0bbb`) | decifrado na seção 7b e gravado pelo writer |
| Curva simples (`0x1396`, polígono/mão livre): só `0x4a38`, sem `0x4c2d` | observado, ainda não gravado |
| Arestas suaves e lisas, na face e na aresta | flags conhecidas, efeito na malha não verificado |
| Grupos e componentes novos (`0x1964`, `0x138d`, `0x1967`) | só leitura |
| Guias, textos, cotas, planos de seção | gravador por patch já escreve alguns, sem receita golden |
| Laços da face em definições (mesmo layout, mas com `0x138e` própria) | não testado |
| Tamanho do id quando passa de 65535 (3 bytes) | só observado em modelos grandes |

## 9. Assunções pendentes

1. A ordem dos registros dentro de `0x1388` (vértices, arestas, faces, instâncias) é exigida pelo SketchUp?
   O gravador mantém a ordem observada.
2. `0x07d3 = 0x46` na face: bit `0x40` desconhecido (presente em todas as faces observadas).
3. O contador `0x03e9` precisa ser maior que qualquer id; se isso for violado o SketchUp pode recusar ou reaproveitar ids.
4. A caixa limite precisa ser recalculada; um valor velho provavelmente só afeta o zoom, não a abertura (a confirmar).
