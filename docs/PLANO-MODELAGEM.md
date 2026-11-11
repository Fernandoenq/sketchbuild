# Plano: modelagem 3D como no SketchUp

Estado em 11/11/2026. Decisões do Fernando: o primeiro marco é o **ciclo clássico**
(desenhar, a face nasce sozinha, Push/Pull edita o sólido) e o **núcleo de topologia
mora em Python, no backend**.

## 1. Diagnóstico do que existe hoje

O programa "desenha e anexa":

- **Linha** (`frontend/src/main.js`, `commitLineSegment`): desenha o segmento no Three.js e
  envia cada aresta solta para `POST /api/v1/scene/geometry/line`.
- **Faces** só nascem por rota explícita de polígono (`add_polygon_face`). Fechar um laço de
  arestas não cria face.
- **Push/Pull** (`POST /api/v1/scene/geometry/pushpull`, `extrude_face`): recebe os vértices
  do polígono e acrescenta um sólido novo. Não altera a face existente nem arrasta as
  vizinhas.
- **Sem núcleo de topologia:** não divide aresta na interseção, não divide face quando uma
  linha a cruza, não funde coplanares, não cicatriza ao apagar.
- **Desfazer/Refazer de modelagem:** não existe.

## 2. O que a API pública do SketchUp oferece

Conferido nos símbolos exportados da `SketchUpAPI.dll` 2026:

- **Tem:** `SUEntitiesAddFaces/AddEdges/AddCurves/Fill`, `SUEntitiesWeld`, `SUEntitiesErase`,
  `SUEntitiesTransform`, `SUFaceReverse` e as consultas de topologia (`SUFaceGetOuterLoop`,
  `SUEdgeGetFaces`, `SUVertexGetEdges` e similares).
- **Não tem:** Push/Pull, Offset, Follow Me, Intersect Faces, booleanas.

Conclusão: o núcleo de modelagem precisa ser nosso. A DLL serve como **oráculo** de
verificação, não como motor de edição.

## 3. Arquitetura

- Um **núcleo de topologia único** em Python (`core/topology/`): vértices, arestas, faces,
  laços externos e internos, tolerância numérica (SketchUp usa cerca de 0,001").
- O núcleo opera só na **definição em edição**, nunca no modelo inteiro (modelos grandes têm
  milhões de vértices).
- O navegador mostra uma pré-visualização leve (elástico, contorno da extrusão) e envia a
  **operação final**. A resposta devolve apenas o que mudou (entidades criadas, alteradas e
  removidas), não a cena toda.
- Persistência: o núcleo é serializado pelo gravador binário existente
  (`core/skp_binary_writer.py`). A leitura de volta passa pelo leitor e pela DLL.
- Inferência de pontos continua em `frontend/src/inferenceEngine.js`.

## 4. Fases

| Fase | Entrega | Pronto quando |
|---|---|---|
| F0 Fundação | Receitas de referência rodadas no SketchUp real (Ruby) e medição do que `SUEntitiesFill` já resolve | Tabela de V/E/F e áreas para cada receita, versionada |
| F1 Topologia | Grafo, divisão de aresta na interseção, laço fechado vira face, face com furo, apagar com cicatrização | Testes de 2D batendo com as receitas |
| F2 Desenho | Linha, Retângulo, Círculo, Polígono, Arco, Mão livre sobre o núcleo | Os mesmos desenhos no navegador geram V/E/F iguais ao SketchUp |
| F3 Push/Pull | Move a face, arrasta paredes vizinhas, trata furos, vaza o sólido, Ctrl cria face nova | Volumes e contagens iguais às receitas |
| F4 Edição | Selecionar aresta e face, Mover/Rotacionar/Escalar geometria solta, Offset | Operações sem corromper o grafo |
| F5 Grupos/Componentes | Criar a partir da seleção, editar por dentro, Intersect Faces, Follow Me | Hierarquia preservada ao salvar |
| F6 Histórico | Desfazer e refazer com log de operações | Sequência de N operações desfeita e refeita bate com o estado original |

### F0 em detalhe
1. Escolher 10 a 15 receitas (retângulo; retângulo mais Push/Pull; linha cruzando face;
   duas linhas em T e em X; círculo; face com furo; Push/Pull empurrando para dentro até
   vazar; apagar aresta compartilhada).
2. Rodar cada uma no SketchUp 2026 pela ponte Ruby (`ruby_bridge/`) e gravar contagem de
   vértices, arestas e faces, áreas e volumes em JSON.
3. Testar `SUEntitiesFill` e `SUEntitiesAddFaces` contra as receitas: o que a DLL já funde,
   divide e solda sozinha.
4. Definir o formato do grafo e a API do núcleo.

## 5. Critério de aceitação

1. O `.skp` gerado **abre no SketchUp 2026 real** e a leitura via Ruby bate com a contagem
   do núcleo.
2. A leitura pela `SketchUpAPI.dll` confere (oráculo automático).
3. Opcional: leitura pelo OpenSKP (https://github.com/iamahsanmehmood/openskp, MIT) como
   segundo oráculo independente, em ambiente isolado e sem depender do Windows.

## 6. Riscos

- O gravador por patch no `model.dat` só foi validado pela DLL, nunca abrindo no SketchUp
  de verdade. É o primeiro item a verificar na F0.
- Dois motores (DLL no Windows e Zero DLL): o núcleo novo passa a ser o caminho único de
  modelagem.
- Tolerância numérica e geometria degenerada (arestas quase coincidentes) exigem testes
  próprios.

## 7. Referência externa: OpenSKP

Toolkit de leitura, escrita e conversão de `.skp`, sem núcleo de modelagem. Mapeia as mesmas
tags do `model.dat` que nós (confirmação independente). Seu escritor produz só o formato
legado MFC, costurando entidades num arquivo em branco gerado pelo SDK. Útil como oráculo e
como referência de guias, cotas, grupos e formato legado. Licença MIT: se algum trecho for
reaproveitado, manter o aviso de copyright.

## Status F2 (11/11/2026)
Núcleo pronto: `core/topology/draw.py` (linha, retângulo, círculo 24 lados, polígono inscrito/circunscrito, arco, mão livre) devolve o delta de V/E/F. Rotas `POST /api/v1/draw`, `GET /api/v1/draw/state`, `DELETE /api/v1/draw` (estado em memória). Testes `test_topology_draw.py` batem com r01, r02, r03, r09, r10, r13 e r06; `test_draw_api.py` cobre as camadas.
Pendente: ligar o front (ferramentas do canvas chamando `/draw`), gravar a topologia no `.skp` (gravador), e conferir a regra de linha que cruza uma face vinda de fora (a API do SketchUp não divide em X; o app gráfico divide).

**Pendente (anotado 11/11/2026):** o front da F2 (`frontend/src/modelagem.js`) só teve a sintaxe verificada. Falta testar no navegador: reiniciar o backend, abrir o app, usar cada botão e conferir contagens, prévia, encaixe e recarga da página.

## Status F3 (11/11/2026)
`core/topology/pushpull.py`: `empurrar(topologia, face, distancia, criar_nova)`. Modo mover (face de sólido com vizinhas perpendiculares: paredes esticam, colapso total some, r05) e modo extrusar (face solta mantém a base, r04; face em furo pousa na face de baixo e vaza, r11). Rota `POST /api/v1/draw/pushpull`; botão Empurrar/Puxar no front (clicar na face, digitar a distância em metros, Enter; Ctrl+Enter mantém a original). Testes `test_topology_pushpull.py` batem com r04, r05 e r11 e conferem normais para fora.
Limites: empurrar além do lado oposto do sólido dá erro (não suportado); colapso parcial dá erro; face com furo que pousa em outra face não é tratada; sem arrasto com o mouse (só campo de distância). Front da F3 não testado no navegador (mesmo pendente da F2).

## Status F4 (11/11/2026)
core/topology/edit.py: mover, rotacionar, escalar (atômicos: se uma face deixa de ser plana ou dois vértices colidem, tudo volta e dá erro) e offset (negativo para dentro, positivo para fora; o laço novo vira face e furo da original). Rotas POST /api/v1/draw/edit e /api/v1/draw/offset. Front: ferramenta Selecionar (face ou aresta, Shift soma), campo de valor e botões Mover (dx,dy,dz em m), Rotar (graus), Esc. (fator ou três) e Offset (m). Testes test_topology_edit.py (11) cobrem mover, esticar a face do topo, desfazer ao quebrar a planaridade, rotação com normais para fora, escala, offset em retângulo e círculo.
Limites: mover só uma aresta ou vértice de sólido é recusado (precisaria triangular a face); escala negativa (espelho) recusada; offset de face com furos só está coberto de forma básica; rotação em eixo livre existe na API mas o front só gira em Z. Front da F4 sem teste no navegador (mesma pendência das F2 e F3).
