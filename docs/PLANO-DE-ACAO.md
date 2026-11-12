# Plano de ação: SketchBuild fiel ao SketchUp (REA do que falta ou não funciona)

Criado em 11/11/2026. Objetivo: fazer o SketchBuild entregar, de forma **verificável**, as funcionalidades do SketchUp
que hoje não existem, existem só de mentira ou não funcionam. "Verificável" quer dizer: cada item só vira "pronto"
quando um oráculo (SketchUp real via Ruby, `SketchUpAPI.dll`, OpenSKP ou o leitor binário) confirma o resultado.

Este documento é o mapa. A execução vai sendo registrada na seção 14 (registro de execução) e a nota
`Projetos/SketchBuild` do Second Brain recebe uma entrada por bloco concluído.

## 0. Regras de trabalho (valem para todos os blocos)

1. **Nunca tocar no backend em uso nem clicar na interface sem o Fernando confirmar.** Testes automáticos rodam em
   processo separado, com porta própria, e só em módulos puros (`core/`, `app/` via chamada direta).
2. **Originais intocados.** Todo `.skp` de entrada é lido; a saída vai para pasta nova. Os modelos da Parkelô ficam
   fora do GitHub (só estatísticas e hashes entram no repositório).
3. **Commits sem assinatura do Claude**, autor só o Fernando. Push direto em `master` do repositório público
   `Fernandoenq/sketchbuild`, depois de cada bloco com testes verdes.
4. **Tripla camada:** documento no repo + entrada na nota SketchBuild do Second Brain + commit/push.
5. **Pontos não definidos** (lacunas do formato, decisões tomadas sem confirmação) viram "assunção pendente" na nota.
6. **Python 3.12** para tudo que usa a DLL (`py -3.12 -I`, com `sys.path.insert`). O ctypes do 3.14 tem regressão.
7. **Nada de dado da Parkelô, nome de cliente ou caminho pessoal em commit.** Conferir com `git diff --cached` antes.
8. **Mentira técnica é bug.** Se um módulo "simula" um recurso sem o oráculo, ele recebe o selo `SIMULADO` na
   auditoria e a interface avisa; não é apresentado como funcionalidade real.

## 1. Estado atual (levantado em 11/11/2026)

- 190 módulos em `core/`, 246 rotas em `scene_router.py`, 54 arquivos `test_*.py`, 187 seções nas notas de REA.
- **Real e conferido contra o SketchUp:** leitura de malha pelo `model.dat`; objetos ocultos (flag `0x07d3`) e poda
  sem SketchUp; inteiro de integridade do cabeçalho; núcleo de topologia F1 a F6 (receitas r01 a r14 em
  `docs/f0/f0_resultados.json`); 36 operações do gravador binário por patch (retângulo, caixa, círculo, cilindro,
  linha, polígono, plano de seção, guias, offset).
- **Existe mas sem oráculo (selo SIMULADO até prova em contrário):** a maior parte das "Frentes" 1 a 145
  (engenharia, BIM 4D/5D/7D, normas ABNT, física, fatiamento, acústica, iluminação, etc.). Os testes delas
  confirmam consistência interna, não fidelidade ao SketchUp.
- **Não existe ou não funciona:** ver seção 2.

## 2. Lacunas conhecidas (o que o REA precisa atacar)

### 2.1 Persistência e formato (maior risco)
| ID | Lacuna | Hoje |
|---|---|---|
| P1 | Gravar a topologia do `/draw` (vértices, arestas, faces com furos) num `.skp` válido | não existe; o desenho vive só na memória |
| P2 | Gravar hierarquia (definições, instâncias, transformações, grupos vs componentes) | só em memória (`Cena`) |
| P3 | Gravar materiais e texturas nas faces novas | parcial, só no gravador por patch |
| P4 | Gravar tags (camadas), cenas, estilos, sombras, câmera | parcial |
| P5 | Recalcular caixa limite, miniaturas, `meta.dat`, contadores | caixa limite e miniaturas ficam velhas |
| P6 | Edição estrutural do `model.dat` (inserir/remover registros TLV sem corromper IDs e tabelas `0x138e`) | só poda; inserção por patch limitada |
| P7 | Compatibilidade com versões antigas (pré-VFF 2021) e com SketchUp 2017 a 2026 | só VFF 2021+ |
| P8 | Arestas e faces ocultas dentro de definições vivas na poda | não removidas |
| P9 | Abrir no SketchUp real o que o gravador gera (risco nº 1 do plano de modelagem) | nunca validado |

### 2.2 Leitura e visualização
| ID | Lacuna |
|---|---|
| L1 | `SkpBinaryReader` e `extract_mesh` não respeitam o flag de oculto; visualizador mostra ocultos |
| L2 | Opção "exibir tudo" e visibilidade efetiva por etiqueta (tags por cena, `0x7150`) |
| L3 | Arestas suaves e lisas (bits `0x08` e `0x10`) no desenho de contorno |
| L4 | Guias, textos, cotas, planos de seção e seção preenchida na leitura |
| L5 | Normais, face de trás, orientação de faces e materiais por face traseira |
| L6 | Performance em modelos de 300 a 900 MB (streaming, LOD, instanciamento GPU, cache em disco) |
| L7 | Estilos (traço, raio-x, monocromático, bordas) e sombras reais |

### 2.3 Modelagem (F2 a F6 e além)
| ID | Lacuna |
|---|---|
| M1 | Plano de desenho qualquer (hoje só o chão); inferência de eixos, paralelas, perpendiculares, pontos médios |
| M2 | Caixa de medidas (VCB) com digitação para todas as ferramentas |
| M3 | Push/Pull com arrasto do mouse, inferência de altura e dupla-clique de repetição |
| M4 | Push/Pull além do lado oposto, colapso parcial, face com furo pousando em face, Ctrl em face com furos |
| M5 | Mover aresta ou vértice de sólido (a face quebrada é triangulada e as arestas ficam suaves) |
| M6 | Rotacionar e Escalar com gizmo, eixo livre, espelho (escala negativa), escala por eixo no front |
| M7 | Offset de face com furos, quinas côncavas, arcos |
| M8 | Siga-me com caminho fechado, perfil fora do caminho, torção mínima (Rotation Minimizing Frames) |
| M9 | Intersect Faces com grupos e contexto (só selecionados, só com o modelo) |
| M10 | Arcos (2 pontos, 3 pontos, setor, fatia), curvas (grupo de arestas "Curve"), Bézier, mão livre suavizada |
| M11 | Suavizar e Amaciar (soften/smooth) com ângulo |
| M12 | Ferramentas de sólido (união, subtração, interseção, aparar, dividir) sobre sólidos reais |
| M13 | Pintar, apagar, selecionar (laço, janela, cruzamento), inverter seleção, selecionar tudo e nenhum |
| M14 | Fita métrica, transferidor, cotas, textos, eixos, planos de seção e seção preenchida no núcleo |
| M15 | Componentes: criar, editar, tornar único, explodir aninhado, substituir, componentes dinâmicos |
| M16 | Caixa de areia (terreno): contornos, escultura, estampar, drapejar, adicionar detalhe, inverter aresta |
| M17 | Edição colaborativa (F0 a F7 já prontas atrás de `AO_VIVO`, push e ensaio pendentes) |
| M18 | Histórico por delta (hoje cópia completa por passo) e histórico persistente |

### 2.4 Interface (itens desabilitados ou ausentes)
Menus sem função hoje: Selecionar tudo, Selecionar nenhum, Inverter seleção, Criar componente, Editar componente,
Importar, Imprimir, Reverter, Salvar como modelo, Salvar uma cópia como, Geometria oculta, Objetos ocultos, Guias,
Guias de cena, Preenchimento de seção, Oclusão ambiental, Materiais fotorrealistas, Norte verdadeiro, Modelo centralizado,
Alfinete de localização, Animação, Cena anterior e próxima, Janela de zoom, Zoom na foto, Adaptar à nova foto,
Editar foto adaptada, Enviar para o LayOut, 3D Warehouse, Trimble Connect, Fazer login, Gerenciar licença, Comentários,
Barras de ferramentas, Buscar no SketchUp, Central de ajuda, Verificar atualização, Entre em contato.
Botões desligados: Arcos e Equidistância ("fora de escopo"), que agora entram pelo núcleo.

| ID | Lacuna |
|---|---|
| U1 | Front de grupos e componentes: criar, entrar, sair, desenhar as instâncias, outliner ligado à `Cena` |
| U2 | Integrar o desenho do núcleo com a cena do SDK (hoje são dois mundos: sessão SDK e sessão do `/draw`) |
| U3 | Desfazer/refazer unificado (núcleo, SDK e gravador binário) |
| U4 | Atalhos de teclado do SketchUp (espaço, L, R, C, P, M, Q, S, E, B, F) e barra de status de medidas |
| U5 | Todos os menus acima: cada item vira "implementar", "adaptar" ou "descartar com justificativa" |
| U6 | Teste real do front no navegador (F2 a F6 só tiveram sintaxe verificada) |
| U7 | Acessibilidade, responsividade, idioma, temas |

### 2.5 Importar e exportar
| ID | Lacuna |
|---|---|
| E1 | Importar: DXF/DWG, OBJ, STL, 3DS, COLLADA, KMZ, imagens, PDF; validar contra arquivos de verdade |
| E2 | Exportar: OBJ, STL, GLB, IFC, DXF, PDF 2D e 3D, imagens, animação, COLLADA, FBX |
| E3 | Salvar cópia, salvar como modelo, reverter ao salvo, autosave consistente entre os motores |
| E4 | LayOut: gerar `.layout` ou ao menos pranchas equivalentes (Frente 185 existe, sem oráculo) |

### 2.6 Qualidade e infraestrutura
| ID | Lacuna |
|---|---|
| Q1 | Auditoria de fidelidade das 145 frentes e dos 190 módulos (selo REAL, PARCIAL, SIMULADO, QUEBRADO) |
| Q2 | Receitas golden para cada operação (F0 tem 14; o alvo é 80 ou mais) rodadas no SketchUp real |
| Q3 | Integração contínua (GitHub Actions) rodando os testes puros; testes de DLL só local |
| Q4 | Fuzz e propriedade nos núcleos (topologia, poda, leitor) e testes de regressão com `.skp` sintético |
| Q5 | Segurança: validação de caminhos, upload, CORS, limites de tamanho, dependências |
| Q6 | Desempenho: perfil, memória, tempo de abertura, cache; metas em seção 11 |
| Q7 | Empacotamento: instalador, scripts de execução, `requirements`, README, versão |
| Q8 | Dívida: ~190 módulos `core/` sem fronteira clara com o app; duplicações entre `core/` e `core/topology` |

## 3. Método de REA (como cada lacuna é atacada)

Para cada lacuna, o ciclo é sempre o mesmo, e o resultado entra em `REVERSE_ENGINEERING_NOTES.md`:

1. **Hipótese** escrita antes de olhar (o que o SketchUp deveria fazer e por quê).
2. **Receita golden** em Ruby (`ruby_bridge/`), rodada no SketchUp real, JSON versionado em `docs/f0/` (ou `docs/golden/`).
3. **Binário:** localizar a função no `SketchUpAPI.dll` e no `SketchUp.exe` com o REA (Ghidra via MCP `rea`), anotar
   com `annotate_native_function`, registrar Evidence ID.
4. **Formato:** diferenciar `.skp` antes e depois da operação (diff estrutural do `model.dat`, árvore TLV), com a
   ferramenta de diff de TLV (a criar, item T1).
5. **Implementação** mínima que reproduza a receita, com teste contra o golden.
6. **Oráculos de verificação**, em ordem de confiança: (a) SketchUp real; (b) `SketchUpAPI.dll` lendo o arquivo
   gerado; (c) OpenSKP (MIT) em ambiente isolado; (d) nosso leitor. Pelo menos dois concordando.
7. **Registro:** nota REA, tabela de assunções, entrada no Second Brain, commit.

Ferramentas de apoio a criar (bloco T):
- **T1** `tools/tlv_diff.py`: compara dois `model.dat` e imprime a árvore de diferenças por tag.
- **T2** `tools/skp_inspect.py`: dump legível da árvore TLV de qualquer `.skp` (com nomes de tag conhecidos).
- **T3** `tools/oraculo.py`: abre um `.skp` pela DLL (Python 3.12) e devolve contagens e geometria para comparar.
- **T4** `ruby_bridge/golden_*.rb`: receitas golden novas, uma por operação.
- **T5** Banco de receitas: `docs/golden/*.json` com esquema único (entrada, passos, medidas, versão do SketchUp).
- **T6** Gerador de `.skp` sintético mínimo (sem dados de cliente) para testes automatizados.
- **T7** Mapa de tags do `model.dat` (`docs/FORMATO-SKP.md`): cada tag, tipo, onde aparece, quem lê, quem escreve.

## 4. Fases e ordem de execução

A ordem prioriza o que **destrava o resto** e o que **reduz o maior risco** (gravar um `.skp` que o SketchUp abra).

| Fase | Foco | Itens | Saída |
|---|---|---|---|
| A | Fundação de verificação | T1 a T7, Q1 (auditoria), Q3 | Ferramentas de diff e oráculo, tabela de fidelidade |
| B | Persistência da topologia | P1, P5, P6, P9, L1 | Desenho do `/draw` vira `.skp` que a DLL abre |
| C | Hierarquia e materiais | P2, P3, P4, U1, U2 | Grupos e componentes gravados e lidos |
| D | Modelagem robusta | M1 a M11 | Operações novas com golden e testes |
| E | Interface | U3 a U7, menus | Menus e atalhos completos, sem itens mortos |
| F | Terreno, sólidos, dinâmicos | M12, M15, M16 | Solid tools, caixa de areia, componentes dinâmicos |
| G | Importar e exportar | E1 a E4 | Conversores validados contra arquivos reais |
| H | Escala e desempenho | L6, M18, Q6 | Modelos de 900 MB abrem rápido e editam |
| I | Auditoria das frentes | Q1, Q8 | Cada frente com selo e plano de correção |
| J | Colaboração e servidor | M17, servidor 3D | Ao vivo com 2 navegadores ensaiado |

Cada fase termina com: testes verdes, nota REA, entrada no vault, commit/push e uma linha no registro (seção 14).

## 5. Fase A: fundação de verificação

**A1. Mapa de tags (T7 e T2).** Entregar `tools/skp_inspect.py` que imprime a árvore TLV com os nomes de tag que já
conhecemos (`0x01f4`, `0x1388`, `0x07d0`, `0x07d3`, `0x1389` a `0x138b`, `0x138c`, `0x138d`, `0x138e`, `0x13a0`, `0x1964`,
`0x1967`, `0x3a98`, ...). Saída em texto e JSON. Gera `docs/FORMATO-SKP.md` a partir do que o código já lê.
Aceite: roda nos 14 `.skp` de F0 e nos 62 podados sem erro, e a árvore bate com o que o leitor extrai.

**A2. Diff de TLV (T1).** Compara dois `model.dat` ignorando IDs recalculados. Usar nos pares "vazio" e "r03 retângulo",
"r04 cubo", "r09 círculo" para ver exatamente quais registros nascem por entidade.
Aceite: relatório de quais tags e bytes mudam em cada receita, em `docs/FORMATO-SKP.md`.

**A3. Oráculo pela DLL (T3).** `tools/oraculo.py` abre um `.skp` pela `SketchUpAPI.dll` e devolve: contagem de
vértices, arestas, faces, grupos, componentes, definições, materiais, tags, e a lista de faces com área e normal.
Aceite: nos 14 arquivos de F0, os números batem com o JSON golden.

**A4. Receitas golden novas (T4 e T5).** Meta de 60 receitas novas, em blocos:
- Desenho: arco 2/3 pontos, setor, fatia, polígono de N lados, curva Bézier, mão livre; linha sobre face em planos
  inclinados; linha cruzando em X dentro de face; retângulo rotacionado; círculo em plano vertical.
- Push/Pull: face com furo, empurrar além, puxar sobre face coplanar vizinha, Ctrl, face inclinada, extrusão de
  círculo (cilindro com faces suaves), repetição por dupla-clique.
- Move: aresta, vértice, face de sólido, com e sem Ctrl (cópia), ao longo de eixo.
- Rotate e Scale: eixo livre, escala por eixo, espelho, cópia múltipla.
- Offset: furos, quinas côncavas, arco, círculo.
- Follow Me: caminho fechado, perfil fora do caminho, caminho com arco, "Face Perimeter".
- Intersect Faces: com selecionados, com modelo, com grupo, com componente.
- Soften/Smooth: ângulos 20, 40, 60 graus; arestas coplanares.
- Grupos e componentes: criar, aninhar, tornar único, explodir, editar por dentro, transformar, espelhar.
- Materiais: pintar face, pintar grupo, material no verso, textura posicionada.
- Tags, cenas, estilos, sombras, câmera.
- Seção: plano de seção, preenchimento, corte de grupo.
- Sólidos: união, subtração, interseção, aparar, dividir; verificação de "sólido" válido.
- Terreno: de contornos, de grade, escultura, estampar, drapejar, detalhe, inverter aresta.
Aceite: `docs/golden/*.json` com esquema único, scripts Ruby versionados, execução registrada com a versão do SketchUp.
Observação: rodar as receitas exige o SketchUp aberto; o Fernando roda `load` do script e devolve o JSON (um comando
só, como foi feito em F0). Cada lote de 15 receitas é um comando.

**A5. Auditoria de fidelidade (Q1).** Script `tools/auditar_frentes.py` que percorre os 190 módulos de `core/` e as 246
rotas e preenche uma tabela `docs/AUDITORIA-FUNCIONALIDADES.md` com: nome, linhas, tem teste, usa DLL, usa gravador,
tem oráculo golden, cita "simul", "mock", "placeholder", "stub", "exemplo", "dummy", retorna constantes, selo proposto.
Aceite: tabela completa, ordenada por risco; cada módulo com selo REAL, PARCIAL, SIMULADO ou QUEBRADO, e a regra do
selo escrita no topo do documento.

**A6. CI (Q3).** Workflow `.github/workflows/testes.yml`: instala `requirements.txt` em Python 3.12, roda só os testes
que não precisam da DLL (`test_topology_*`, `test_draw_api`, testes de poda com arquivo sintético, testes de leitor).
Aceite: verde no GitHub, badge no README.

**A7. `.skp` sintético (T6).** Gerar, sem cliente, um `.skp` mínimo e um médio (dezenas de grupos/instâncias, com ocultos)
usando o gravador e o SDK, para testes automatizados da poda, do leitor e do gravador.
Aceite: testes de poda e de leitor deixam de depender de arquivo da Parkelô.

## 6. Fase B: persistência da topologia (o maior risco)

Meta: o desenho do `/draw` vira `.skp` e a `SketchUpAPI.dll` abre e conta as mesmas entidades.

**B1. REA do registro de geometria.** Com T1 e T2, mapear no `model.dat` do SketchUp real, para as receitas r01 a r14:
- registro de vértice (`0x1389` e filhos), aresta (`0x138a`: índices de vértice, flags, material, tag), face (`0x138b`:
  laços, normal, plano, material frente e verso, flags), laço (laço externo e internos), ordem dos registros,
  tabela de IDs dos filhos (`0x138e`), caixa limite (`0x13a0`), contadores globais.
- No `SketchUpAPI.dll`, olhar `SUEntitiesAddFaces`, `SUEntitiesAddEdges`, `SUFaceCreate`, `SUGeometryInputAddVertex`,
  `SUGeometryInputAddFace`, `SUEntitiesFill` e os serializadores que escrevem esses registros.
Aceite: `docs/FORMATO-SKP.md` com a estrutura byte a byte de vértice, aresta e face, validada nos 14 arquivos F0.

**B2. Gravador de topologia (`core/skp_topology_writer.py`).** Serializa uma `Topology` numa definição de um `.skp`
existente (modelo vazio como base): insere registros, atualiza `0x138e`, caixa limite, contadores e o registro externo
`0x01f4`, recalcula o inteiro de integridade do cabeçalho.
Aceite: para r03, r04, r09, r10, r11, r14 geradas pelo núcleo, a DLL abre o arquivo e as contagens batem com o golden.

**B3. Roundtrip.** Núcleo → `.skp` → DLL → núcleo. Comparar vértices (com tolerância), arestas, faces, laços, normais.
Aceite: igualdade estrutural para 50 desenhos aleatórios (propriedade) gerados pelas ferramentas do `/draw`.

**B4. Abrir no SketchUp real.** Lote com 10 arquivos gerados; o Fernando abre cada um e roda `contar_ocultos.rb` e um
script de contagem. Aceite: abre sem aviso de integridade e as contagens batem. Se algum falhar, volta a B1.

**B5. Salvar do `/draw`.** Botão e rota "Salvar desenho" que grava num caminho novo (nunca sobrescreve sem confirmar).
Aceite: ida e volta pela interface (depois do teste manual do Fernando).

**B6. Edição estrutural do `model.dat`.** Inserir e remover registros TLV com atualização de tamanhos em todos os
ancestrais, sem quebrar IDs, tabelas de filhos e `0x01f4`. É a base da B2 e do restante da fase C.
Aceite: inserir e remover N entidades em arquivo real mantém o arquivo abrindo e a árvore idêntica ao esperado.

**B7. Leitor com ocultos (L1 e L2).** `SkpBinaryReader` e `extract_mesh` leem o flag `0x07d3` e a visibilidade efetiva
(instância, etiqueta, herança); parâmetro `mostrar_ocultos`. Interface: Editar > Reexibir > Tudo realmente reexibe o que
estava oculto no arquivo (hoje só reexibe o que o usuário ocultou).
Aceite: contagem de visíveis do leitor igual à do `contar_ocultos.rb` nos 5 modelos de referência.

**B8. Poda completa (P8).** Remover arestas e faces ocultas dentro de definições vivas (hoje só instâncias e
definições mortas), validar nos 62 arquivos e em 3 aberturas no SketchUp real.

## 7. Fase C: hierarquia, materiais e interface de grupos

**C1. REA de definições e instâncias** (`0x01f9`, `0x1770`, `0x1771`, `0x138c`, `0x138d`, `0x1964`, `0x1967`):
transformação (4x4), nome, tipo (grupo versus componente), caminho de definição, `0x138e` aninhada.
**C2. Gravador de hierarquia:** `Cena` → `.skp` com definições e instâncias; ida e volta pela DLL.
**C3. Materiais e texturas:** faces novas com material, textura posicionada, verso; estender `create_textured_material`.
**C4. Tags, cenas e estilos:** gravar e ler; visibilidade por cena (`0x7150`).
**C5. Front de grupos (U1):** criar grupo/componente, entrar/sair (duplo clique e Esc), instâncias desenhadas com a
malha da definição, outliner ligado à `Cena`, "tornar único", explodir aninhado.
**C6. Unificar os dois mundos (U2):** decidir e implementar a ponte entre a `Cena` do núcleo e a sessão SDK/binária:
abrir um `.skp` real dentro da `Cena` (importando a topologia da definição editada) e salvar de volta.
Aceite da fase: abrir um modelo real, entrar num grupo, desenhar, empurrar, sair, salvar, reabrir no SketchUp.

## 8. Fase D: modelagem robusta (M1 a M11)

Ordem sugerida, cada item com receita golden (A4) antes do código:
1. **M1/M2 Inferência e VCB:** plano de desenho pela face sob o mouse e pelos eixos; inferência de ponto, ponto médio,
   interseção, paralela, perpendicular; digitação de medidas (`3,5`, `2x4`, `3.2m`, `24s`) em todas as ferramentas.
2. **M3/M4 Push/Pull completo:** arrasto com inferência; regras para face com furo, atravessar, colapso parcial, Ctrl;
   confirmar r05 no SketchUp real (hoje assunção).
3. **M5 Mover aresta/vértice:** triangular a face quebrada, arestas suaves, normais; golden de 8 receitas.
4. **M6 Rotate/Scale/Mirror no front:** gizmo, eixo livre, múltiplas cópias, espelho por escala negativa com inversão
   de laços.
5. **M7 Offset avançado:** furos, quinas côncavas, arco; golden.
6. **M8 Siga-me completo:** caminho fechado, perfil fora do caminho, Rotation Minimizing Frames (o `follow_me_engine.py`
   antigo já usa RMF; comparar com o novo contra r14 e reaproveitar o que for fiel).
7. **M9 Intersect avançado:** contexto de grupo, selecionados, com modelo, coplanares sobrepostas.
8. **M10 Arcos e curvas:** os 4 tipos de arco, curva como grupo de arestas com flag, Bézier, mão livre com RDP.
9. **M11 Soften/Smooth:** flags `0x08`/`0x10` no núcleo; ângulo; efeito no desenho e na malha.
Aceite por item: receita golden passando; sem regressão nos 74 testes atuais; nota REA.

## 9. Fase E: interface

**E-U3** Histórico unificado (núcleo, SDK, gravador binário); delta em vez de cópia completa (M18).
**E-U4** Atalhos do SketchUp e barra de status de medidas; painel "Informações da entidade".
**E-U5** Menus: tabela de decisão item a item (implementar, adaptar, descartar), na ordem:
1. Imediatos e simples: Selecionar tudo/nenhum/inverter, Zoom janela, cena anterior/próxima, Reverter, Salvar cópia,
   Salvar como modelo, Imprimir (PDF), Geometria oculta (mostrar ocultos em tracejado), Objetos ocultos, Guias,
   Guias de cena, Modelo centralizado.
2. Com núcleo: Criar/Editar componente (fase C), Preenchimento de seção, Oclusão ambiental (aproximação em tela),
   Norte verdadeiro, Alfinete de localização, Animação (cenas em sequência), Materiais fotorrealistas (PBR do GLB).
3. Descartar com justificativa (dependem de serviços Trimble): 3D Warehouse, Trimble Connect, login, licença,
   comentários, Central de Ajuda, atualização, contato. Substituir por equivalentes locais quando fizer sentido
   (biblioteca local de componentes, em vez de 3D Warehouse).
**E-U6** Teste do front no navegador: roteiro manual de 40 passos (F2 a F6) e depois automatizado com Playwright
em porta e backend de teste próprios (nunca o backend em uso).
**E-U7** Acessibilidade, responsividade, temas, idioma.

## 10. Fases F a J (resumo operacional)

**F Terreno, sólidos e dinâmicos.** Solid tools reais (união, subtração, interseção, aparar, dividir) sobre o núcleo,
com teste de "sólido válido" (toda aresta em duas faces, volume positivo); caixa de areia (de contornos, de grade,
escultura, estampar, drapejar, detalhe, inverter aresta); componentes dinâmicos (atributos `dynamic_attributes`,
fórmulas, `_hidden_formula` que já aparece nos modelos da Parkelô).
**G Importar e exportar.** Para cada formato: ler arquivos reais de pelo menos 3 origens, comparar contagem e unidades
com o software de origem; exportadores validados em leitores externos (Blender, MeshLab, IfcOpenShell, FreeCAD); PDF 2D
vetorial; imagens em 4K; animação de cenas.
**H Escala e desempenho.** Metas na seção 11. Streaming por definição, LOD, instanciamento, cache em disco (já existe
`cache_malhas.py`), abertura em segundo plano, histórico por delta, limites de memória, perfil com 5 modelos reais.
**I Auditoria das frentes.** Para cada frente classificada SIMULADA na A5: reescrever com oráculo, rebaixar para
"exemplo" na interface ou remover. Prioridade: as que aparecem no menu e as de normas (ABNT), onde erro tem custo.
**J Colaboração e servidor.** Push e ensaio com 2 navegadores da edição colaborativa (F3 a F7); integração com o
servidor 3D (`3d.parkelo.com.br`): login e 2FA já planejados; histórico versionado no bucket. Depende do OK do Fernando.

## 11. Metas mensuráveis

| Métrica | Hoje | Meta |
|---|---|---|
| Receitas golden | 14 | 80 |
| Operações do núcleo com golden | 10 de 14 | 100% das ferramentas do menu "Ferramentas" |
| Roundtrip núcleo → `.skp` → DLL | não existe | 50 de 50 desenhos aleatórios |
| `.skp` gerado aberto no SketchUp real | 0 | 10 de 10 sem aviso |
| Módulos com selo REAL | desconhecido | 100% dos que aparecem no menu |
| Abertura de modelo de 300 MB | travava o PC | menos de 20 s com poda opcional |
| Testes automáticos (sem DLL) no CI | 0 | todos verdes no push |
| Itens de menu mortos | 40 | 0 (cada um implementado, adaptado ou descartado com justificativa) |
| Tempo de desfazer em modelo médio | cópia completa | menos de 100 ms |

## 12. Riscos e mitigação

1. **Gravar `.skp` que o SketchUp rejeita.** Mitigar com B1 antes de B2, diff de TLV, integridade do cabeçalho já
   resolvida, e B4 em lotes pequenos; nunca sobrescrever original.
2. **Formato muda entre versões.** Testar com 2 versões do SketchUp (25 e 26 já disponíveis); isolar o que muda.
3. **Escopo infinito das frentes.** A auditoria (A5) congela o escopo: só o que tem oráculo ou aparece no menu entra.
4. **Dois mundos (SDK e núcleo).** C6 define a ponte; até lá, o `/draw` fica rotulado "modelagem (beta)" na interface.
5. **Regressão por ctypes 3.14.** Tudo da DLL em 3.12; CI cobre só os módulos puros.
6. **Dados de cliente vazando.** Regra 7 e checagem de `git diff --cached`; `.gitignore` de `*.skp` fora de `docs/`.
7. **Backend compartilhado.** Regra 1; testes só em processo próprio.
8. **Cansaço de contexto.** Cada bloco termina com nota REA e vault, para qualquer sessão retomar do registro.

## 13. Critérios de pronto (valem para qualquer item)

1. Hipótese, receita golden (quando couber) e resultado registrados.
2. Implementação com testes automáticos que falham sem a correção.
3. Pelo menos dois oráculos concordando (ou o SketchUp real, quando a operação existir nele).
4. Nenhum teste existente quebrado (`py -3.12 -m unittest` nos módulos puros).
5. Nota em `REVERSE_ENGINEERING_NOTES.md` e/ou `docs/FORMATO-SKP.md`; entrada na nota SketchBuild; commit publicado.
6. Assunções listadas como pendentes, nunca escondidas.

## 14. Registro de execução

(Preenchido a cada bloco concluído: data, bloco, resultado, commit.)

| Data | Bloco | Resultado | Commit |
|---|---|---|---|
| 11/11/2026 | Plano criado | este documento | (ver git log) |
| 11/11/2026 | B1, B2, B3 (parte), B5 | REA do registro de vértice, aresta e face (docs/FORMATO-SKP.md); `core/skp_topology_writer.py` grava a topologia numa base vazia; 8 testes de roundtrip contra a SketchUpAPI.dll (10 de 10 amostras B4 conferem pela DLL); rota `POST /draw/save` e botão Salvar .skp (nunca sobrescreve sem confirmar) | a97d743 e seguinte (locais, sem push) |
| 11/11/2026 | A1 (parcial) | `tools/skp_inspect.py` imprime a árvore TLV de qualquer .skp | a97d743 |
| 11/11/2026 | B4 (preparação) | `tools/gerar_amostras_b4.py` gera 10 arquivos em ~/sketchup_gerados; `ruby_bridge/conferir_gerados.rb` confere no SketchUp real. FALTA o Fernando rodar | (ver git log) |
| 11/11/2026 | A5 (auditoria) | `tools/auditar_frentes.py` gera `docs/AUDITORIA-FUNCIONALIDADES.md`: 198 módulos, 13 VALIDADO, 164 TESTADO, 20 SEM TESTE, 1 ORFAO | commit local |
| 11/11/2026 | B6 (curvas) | REA do `0x1397/0x4c2d` (16 doubles) decifrado com arquivos da SketchUpAPI; writer grava círculo e arco como curva; `tools/su_curvas.py`; 3 testes novos (11 no total no writer); seção 7b do FORMATO-SKP.md | commit local |
| 11/11/2026 | C1 (material de cor) + T1 | REA: material = `0x32c8` em `0x01f7>0x30d4>0x30d5` + `materials/<nome>/material.xml` no ZIP; face usa `0x07d1` (frente) e `0x0daf` (verso). `tools/tlv_diff.py`. Writer grava materiais; 3 testes novos (13 no writer) | commit local |
| 11/11/2026 | C2 (pintar no app) | `core/topology/material.py`, rota `POST /draw/paint` (frente, verso, limpar, desfazer), `/draw/state` devolve `pintura` e `materiais`; front: seletor de cor + Pintar/Verso, face colorida na tela. 2 testes novos na camada da API. Front sem teste no navegador | commit local |
| 11/11/2026 | A1 a A6 (hierarquia) | REA de definições `0x157c` e instâncias `0x1964` (seção 7d); `gravar_cena` grava raiz, grupos, componentes (várias instâncias, rotação, escala), aninhados e material dentro da definição; o Salvar .skp deixou de recusar grupos. Achado: definições precisam vir filhos antes dos pais. 15 testes no writer, 14 na API | commit local |
| 11/11/2026 | B7 a B9 (curvas) | curva simples `0x1396` decifrada e gravada (polígono, mão livre); arco dividido em T continua curva; `gerar_amostras_b4.py` agora gera 16 arquivos (curva, material, grupo, componente 3x, aninhado) e o `conferir_gerados.rb` confere curvas, grupos, componentes e cores. As 16 amostras conferem pela DLL | commit local |
| 11/11/2026 | C1 a C3 (ocultos) | `podar_skp(..., "total")` poda arestas e faces ocultas (aresta oculta de face viva fica; vértice órfão, curva quebrada e ids da `0x138e` saem junto); `verificar_skp` conta `arestas_ocultas` e `faces_ocultas`; "Remover ocultos" do app usa o modo total e o resumo mostra faces e arestas. Oráculo: `tools/gerar_ocultos_api.py` (SketchUpAPI esconde faces e arestas). 5 testes novos | commit local |
| 11/11/2026 | D (auditoria) | Testes exatos para 16 módulos antes sem teste; falsos aprovados corrigidos (carga, espessura de parede, classificação de montagem); suíte 380 passando; 4 módulos de exportação ainda sem teste | commit local |

- **Front (12/11/2026):** tag desligada some da vista 3D (`tagOculta` em `modelagem.js`). Assunção pendente: paredes e arestas novas do Push/Pull não herdam tag nem material da face de origem (sem oráculo na SketchUpAPI).

- **Push/Pull (12/11/2026):** paredes novas herdam o material da frente da face puxada (assunção, sem oráculo; verso igual à frente); tag não é herdada (não há tag ativa no núcleo).

- **Texto, cota e UV no app (12/11/2026):** rotas `POST /api/v1/draw/note` (texto livre, cota linear, apagar) e `POST /api/v1/draw/uv` (posicionar ou limpar a textura da frente); o estado devolve `textos`, `cotas` e `uv`. Front: botões Cotar, Texto e Posicionar textura (um campo de texto serve ao rótulo e ao tamanho do ladrilho em polegadas); cotas aparecem em azul e a marca do texto é uma cruz. Normal da cota escolhida pelo backend (z do mundo menos a parte paralela à direção; aresta vertical usa y). Só `node --check` no front, sem navegador.

- **M10 Arcos e curvas (12/11/2026):** `desenhar` ganhou `arco_3pontos`, `arco_corda` (corda + flecha), `setor`, `fatia`, `bezier` (de Casteljau, grau livre) e `tolerancia` na `mao_livre` (Ramer-Douglas-Peucker); rota `/api/v1/draw` aceita as novas ferramentas. 7 testes em `test_topology_arcos.py`, suíte em 471. Assunções pendentes: a normal do arco por 3 pontos é a do triângulo (o arco corre sempre anti-horário em torno dela); a flecha positiva fica à esquerda de p0→p1 visto da normal; Bézier vira curva simples `0x1396` (a SDK não tem curva Bézier, sem oráculo); front ainda sem botões para as novas ferramentas.

- **M7 Offset robusto (12/11/2026):** o offset recusa (`ValueError`, sem alterar o modelo) quando alguma aresta do laço novo encolhe até sumir ou inverte, isto é, quando a distância passa da espessura da face; antes o quadrado de 10 com −6 devolvia um laço invertido e o L de espessura 20 aceitava −11 e −30. Quinas côncavas e furos já funcionavam. 3 testes novos, suíte em 474. Assunções pendentes: o SketchUp real pode, em vez de recusar, remover só a aresta colapsada e seguir com as vizinhas (sem oráculo, não reproduzido); offset de arco como arco não feito (o laço vira polígono de arestas).

- **M11 Soften/Smooth (12/11/2026):** as flags `0x08`/`0x10` e o suavizar por ângulo já existiam, mas sem teste próprio e sem efeito na malha. Agora `soften.normais_suaves` calcula, por vértice, a normal lisa de cada grupo de faces ligadas por aresta lisa (`0x10`, compartilhada por 2 faces) e `/api/v1/draw/state` devolve `normais_suaves` (face → vértice → normal). 4 testes novos em `test_topology_soften.py`, suíte em 478. Assunções pendentes: média ponderada pela área (o SketchUp pode ponderar por ângulo do vértice); sem inversão de faces com enrolamento oposto; só `0x10` gera normal lisa (`0x08` sozinho só esconde a linha); o front ainda não usa `normais_suaves` no sombreamento.

- **M13 Seleção (12/11/2026):** novo `core/topology/selecao.py` e rota `POST /api/v1/draw/select` (fora do histórico, não altera o modelo): `tudo`, `inverter`, `arestas_das_faces` (duplo clique), `faces_das_arestas`, `conectados` (triplo clique), `tag`, `material`, `janela` (só o que cabe inteiro) e `cruzamento` (o que toca, inclusive retângulo dentro da face), com projeção por matriz 4x4. `drawSelect` em `api.js`. 7 testes do núcleo e 1 de API (que também cobre as ferramentas do M10 pela rota), suíte em 486. Assunções pendentes: laço (mão livre) não feito; vértice atrás da câmera tira a aresta e a face da seleção; seleção em grupos/componentes (só a raiz/contexto atual); o front ainda usa a seleção própria e não chama a rota.

- **M12 Ferramentas de sólido (12/11/2026):** novo `core/topology/solido.py` e rota `POST /api/v1/draw/solid` (`drawSolid` em `api.js`): `verificar` (sólido válido = toda aresta em 2 faces, orientação consistente, volume > 0; volume por divergência, cavidades subtraem), `uniao`, `subtracao` (A menos B) e `intersecao`. Método: Intersect Faces corta um sólido pelo outro, cada pedaço de face é classificado dentro/fora do outro por lançamento de raio e ficam os pedaços certos (na subtração, as faces de B dentro de A são invertidas). Dois cubos de 10 com deslocamento (5,5,5): união 1875, subtração 875, interseção 125; sólido dentro de outro vira casca com cavidade (936). Correção no núcleo achada no caminho: `Topology._register_face` não dividia uma face quando o laço novo encostava no contorno por um trecho contínuo (só aceitava furo); agora `_dividir_por_percurso` troca o contorno pelo resto e a face nova herda tag, pintura e UV. Suíte em 499. Assunções pendentes: faces coplanares sobrepostas entre os dois sólidos recusam com erro (o SketchUp real as une; sem oráculo) e o histórico restaura o modelo; as normais das faces de B invertidas seguem a convenção do núcleo, não uma orientação global para fora; aparar e dividir (do plano) não feitos; sem botões no front.

- **M12, faces coplanares (12/11/2026):** novo `solido.combinar(ta, faces_a, tb, faces_b, op)` opera entre sólidos de dois modelos (dois grupos) e aceita sólidos que se encostam ou coincidem em faces inteiras, o que um único `Topology` não representa (ele funde coplanares). Regra para uma face de A que coincide com uma de B (as duas existem): mesmo sentido, união e interseção ficam com a de A e a subtração larga as duas; sentidos opostos (encostados), união e interseção largam as duas e a subtração fica com a de A. Encostados: união de dois cubos de 10 vira caixa de 2000 com 10 faces; subtração devolve A; interseção é vazia. Cubo menor numa parte da face e cubo que passa da borda fecham sozinhos, porque as faces laterais do outro sólido cortam a face coplanar e deixam pedaços idênticos. Mudanças de apoio: `intersectar` agora também usa as arestas que já existiam sobre o corte para dividir faces; `combinar` divide em T as arestas com vértice do outro sólido no meio. 7 testes novos, suíte em 506. Assunções pendentes: sobreposição coplanar que não vire pedaços idênticos (furo no meio de uma face coplanar) ainda recusa com erro; `combinar` ainda não está ligado à `Cena` (grupos com matriz de instância) nem à rota `/draw/solid`, que opera dentro de um modelo só.

- **M11 conferido por REA (12/11/2026):** a regra das normais lisas que eu tinha posto (peso por área, sem inversão) estava ERRADA e foi substituída pela da DLL. Evidência no REA da `SketchUpAPI.dll`: `SUMeshHelperGetNormals` (0x18001d0d4) só copia um array; o mesh é montado em `FUN_180259350`, que pega a normal de cada vértice em `FUN_1801b72d0` → `FUN_1802137b0`, uma tabela de normais por vértice que vira a normal para o lado da face (`dot(normal_da_face, n) < 0` inverte). Os pesos foram achados pelo oráculo `tools/conferir_normais_sdk.py` (SDK de verdade, `SUEdgeSetSmooth` + `SUMeshHelper`): só o bit lisa (`SUEdgeSetSmooth`) liga as faces, `SUEdgeSetSoft` sozinho não muda nada; peso = ângulo do canto da face no vértice; a primeira face do grupo (menor id) é a referência, e uma face que percorre a aresta lisa no mesmo sentido da referência entra com a normal invertida e peso 360° menos o ângulo. `soften.normais_suaves` reescrita e conferida contra a SDK em 9 casos (cantos de 45, 90 e 135 graus, enrolamento consistente e oposto, duas e três faces), erro menor que 1e-6 (`test_skp_normais_sdk.py`). Suíte em 511. Pendência: faces com furo (só o contorno externo entra) e grupos com mais de três faces não foram comparados com a SDK.

- **M12 volume conferido pela SDK (12/11/2026):** o oráculo `SUComponentInstanceComputeVolume` (`tools/conferir_volume_sdk.py`) desmentiu a minha regra de volume. Regra da SDK: cada casca conexa tem as faces unificadas a partir da primeira e conta com o sinal do sentido dela; o resultado é o valor absoluto da soma (cubo todo invertido dá 1000; cavidade com sentido oposto dá 936; casca interna com o MESMO sentido soma e dá 1064; cubo aberto devolve erro 9). Eu subtraía qualquer casca aninhada, o que daria 936 no caso do 1064. `solido.volume` reescrito e conferido contra a SDK em 7 configurações (`test_skp_volume_sdk.py`). Defeito achado por isso: a subtração não invertia as faces de B dentro de A (caíam em `manter` antes de `virar`), e o volume antigo escondia o erro; corrigido, com teste de que as duas cascas ficam com sentidos opostos. Suíte em 514. Continuam SEM oráculo (a DLL não tem função equivalente): união, subtração e interseção em si, offset, seleção, Bézier e RDP; só o volume do resultado é conferível.

- **M10 arcos conferidos pela SDK (12/11/2026):** oráculo `tools/conferir_arco_sdk.py` sobre `SUArcCurveCreate(centro, início, fim, normal, nº de arestas)` (assinatura lida no REA em 0xf9d9; `SUEntitiesAddArcCurves` adiciona). Os vértices do arco por 3 pontos e do arco por corda e flecha batem com os da SDK (até 1e-7) em 6 planos (XY, deslocado, normal -y, inclinado 111, varreduras de 90, 120, 150 e 270 graus) com 6 e 12 segmentos (`test_skp_arco_sdk.py`, suíte em 517). Achado: a SDK sempre usa o próprio ponto inicial como eixo X e ângulo inicial 0 (xaxis = vetor do início, em radianos); os meus ângulos são relativos a `eixos(normal)` e só os vértices são comparáveis. Continuam SEM oráculo, por não existirem na DLL: arco por 3 pontos como operação, arco por corda e flecha, setor, fatia, Bézier e RDP; o que se conferiu foi a geometria do arco gerado, não a interface. A normal do triângulo e o lado da flecha seguem sendo convenção minha.
- **M11 ampliado contra a SDK (12/11/2026):** as pendências do M11 foram comparadas com a SketchUpAPI (`gerar_geral` em `tools/conferir_normais_sdk.py`, 11 configurações novas em `test_skp_normais_sdk.py`, erro < 1e-6). Resultados: (1) anel de 3, 4 e 5 faces em volta do vértice bate; faces de enrolamento invertido no anel batem; (2) canto côncavo de 270° ligado a uma parede bate nos dois lados; (3) face com furo e "chaminé" de paredes nas arestas do furo divergia, pois o núcleo só olhava o contorno externo; agora `normais_suaves` percorre também os furos (furo orientado ao contrário do externo, ângulo do canto medido do lado do material) e bate; (4) DIVERGÊNCIA nova achada: anel FECHADO de 6 faces ou mais em volta do vértice NÃO é suavizado pela SDK (pirâmides de 6, 7 e 8 lados, alturas 5 e 2), enquanto anel aberto (até 11 faces testadas) e anel fechado até 5 faces são; o núcleo agora pula esse caso. Causa não localizada na DLL (o cache de normais, `FUN_1801ceea0`, não foi decompilado): é regra EMPÍRICA, registrada como assunção pendente; (5) empate de produto escalar zero na virada da normal: a SDK mantém a normal, o núcleo agora usa tolerância -1e-9. Regra "primeira face = menor id" continua não distinguida de "ordem de criação" (nos testes coincidem). Suíte em 518.
