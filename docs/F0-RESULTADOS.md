# F0: resultados das receitas no SketchUp real

SketchUp 26.2.243, Ruby 3.2.2, unidades internas em polegadas. Script: `ruby_bridge/f0_receitas.rb`.
Dados completos: `docs/f0/f0_resultados.json` (golden para os testes do núcleo de topologia).

## Tabela (V = vértices, E = arestas, F = faces)

| Receita | Resultado no SketchUp |
|---|---|
| r01 linha solta | V2 E1 F0 |
| r02 4 linhas fechando laço | F0; depois de `find_faces`: V4 E4 F1 |
| r03 retângulo (`add_face`) | V4 E4 F1 |
| r04 retângulo + Push/Pull | cubo V8 E12 F6 |
| r05 Push/Pull de volta ao plano | V0 E0 F0 (tudo colapsa; ver nota 1) |
| r06 linha cruzando a face | V6 E7 F2 |
| r07 linhas em T | 3 arestas (a de base é dividida) |
| r08 linhas em X | 2 arestas, **sem** vértice de interseção |
| r09 círculo de 24 lados | só arestas F0; com `add_face`: F1, área 7764,57 in² |
| r10 face dentro de face | F2; a de fora ganha 2 laços (furo); áreas 10000 e 30000 |
| r11 furo vazado por Push/Pull | V16 E24 F10, dois anéis com 2 laços |
| r12 apagar aresta compartilhada | funde as faces: V4 E4 F1 |
| r13 arco + 2 raios | `find_faces` cria 1 face (V14 E14), área 1957,89 |
| r14 Follow Me | V15 E20 F8, 2 arestas soltas |

## Regras que o núcleo precisa reproduzir

1. `add_line` **não** cria face sozinho; só `find_faces` fecha laço.
2. Aresta nova que encosta no meio de outra divide a existente (T). Cruzamento em X **não** divide.
3. Linha que atravessa uma face a divide em duas.
4. Face desenhada dentro de outra vira furo (laço interno) na de fora, e a interna continua existindo.
5. Push/Pull que atravessa o sólido vaza (some o miolo e surgem as paredes do furo).
6. Apagar aresta compartilhada funde as faces e remove vértices colineares.
7. `add_face` com pontos anti-horários pode dar normal -Z; o desenho precisa normalizar a orientação.

## Notas e pontos em aberto

1. r05: o resultado V0 E0 F0 precisa ser confirmado (a receita escolhe a face do topo por `top_face`; se ela escolheu errado, o colapso é de outra face).
2. O leitor `SkpBinaryReader.extract_mesh` lê os 14 `.skp` reais sem erro e as diferenças de faces batem com o Ruby (r03 +1, r04 +6, r06 +2, r10 +2, r11 +10, r14 +8). Os totais absolutos (110 faces no modelo "vazio") incluem a figura humana do modelo padrão do SketchUp, então comparar sempre pela diferença.
3. Ainda não medido: o que `SUEntitiesFill` e `SUEntitiesAddFaces` já fundem, dividem ou soldam.
4. Ainda não validado: abrir no SketchUp real um `.skp` gravado pelo nosso gravador por patch (risco nº 1 do plano).
