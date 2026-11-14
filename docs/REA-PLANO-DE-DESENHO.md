# Plano de desenho do Retângulo (REA do SketchUp.exe, 14/11/2026)

Pergunta: no SketchUp o retângulo ora nasce deitado, ora em pé, conforme a referência e o mouse. O nosso só nascia no chão (vermelho-verde), nunca usava o azul.

## O que o SketchUp.exe faz (LIDO)

- **Preferência `AutoDrawingPlane`** (string 0x1420c3350; lida no carregamento das preferências em `FUN_140b1df30`, guardada em `DAT_142c4507a`, ev_b9623012…). É a chave do "plano de desenho automático".
- **`FUN_140b383c0`** (ev_c9d7bca9…, único leitor da preferência no código de inferência) devolve o plano de desenho padrão:
  1. Parte do plano de índice 2 (o do chão, eixo azul como normal).
  2. Com `AutoDrawingPlane` ligada e uma vista disponível, pega a **direção da vista** `v` e calcula `|v · normal_k|` para os três planos dos eixos (k = 0, 1, 2).
  3. Fica com o maior (empate: o índice menor, desigualdade estrita para trocar).
  4. **Só vale se o maior for maior que 0,9848 (cos 10°)**: a câmera precisa estar a menos de 10° de um eixo. Senão, volta para o chão.
  Em palavras: olhando de cima, ou numa vista inclinada qualquer, o retângulo nasce no chão. Olhando de frente ou de lado (horizontal, perto de um eixo), nasce em pé, no plano que está de frente para a câmera.
- A barra de status do Retângulo diz **"Arrow Keys = Toggle Lock Drawing Plane."** (0x1420dbb10): as setas travam o plano. **Não li** qual seta é qual plano.
- A ferramenta usa a base comum das formas (`FUN_140cd5450`, movimento do mouse): antes do 1º clique pergunta ao motor de inferência o que está sob o mouse (`FUN_140b356d0`); depois do 1º clique passa o contexto do clique anterior (`FUN_140b35750`). Não li esse motor.

## SUPOSTO (leitura, sem executar o SketchUp)

- Os três planos de `FUN_140b383c0` têm como normais os eixos x, y, z do modelo, na ordem (o índice 2 ser o chão é o que sustenta isso).
- `v` é a direção para onde a câmera olha (e não a posição): com a posição, "perto de um eixo" não faria sentido.
- **Face sob o mouse define o plano do retângulo** (a "referência do objeto" citada por Fernando): é o comportamento observado no SketchUp real, não foi provado no código (a string `FacePlane` existe, mas não foi seguida).

## O que foi implementado (frontend/src/modelagem.js + planoDesenho.js)

| Situação no 1º clique | Plano |
|---|---|
| Mouse sobre uma face | plano da face (normal virada para a câmera) |
| Espaço vazio, câmera a menos de 10° de um eixo | plano vertical perpendicular a esse eixo (azul-vermelho ou azul-verde) |
| Espaço vazio, qualquer outra câmera | chão (como antes) |
| Ponto encaixado (vértice, meio, aresta) | mesma regra do espaço vazio, passando pelo ponto |

Depois do 1º clique o 2º canto fica no plano fixado: pontos encaixados são projetados nele e o resto vem do raio do mouse cruzando o plano. A prévia usa a mesma conta do backend (`cantosRetangulo` = `pontos_retangulo`), e o clique final envia `normal` ao `/api/v1/draw` (o backend já aceitava; conferido: normal (0,1,0) dá laço [(0,0,0), (w,0,0), (w,0,h), (0,0,h)]). Esc e novo retângulo limpam o plano. A barra de status mostra "Retângulo no plano …".

**Não mexi** em Círculo, Polígono, Arcos, Retângulo rotacionado (continuam no chão). **Não implementei** o travamento por setas (falta ler qual seta é qual plano) nem a preferência para desligar o plano automático.

## Testes

`node --test frontend/src/planoDesenho.test.mjs`: 12 testes (limiar de 10°, desempate, câmera de cima/inclinada/horizontal, cantos idênticos aos do núcleo Python, interseção raio-plano, projeção). **A integração na tela (cliques e prévia no navegador) não foi testada**: depende de abrir o app e clicar, e ficou para Fernando validar.
