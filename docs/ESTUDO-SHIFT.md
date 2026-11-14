# Estudo: segurar Shift nas ferramentas (SketchUp x SketchBuild)

Data: 14/11/2026. Fonte do comportamento do SketchUp: o que conheço da interface e dos atalhos documentados do SketchUp. NÃO foi
conferido no `SketchUp.exe`: a `SketchUpAPI.dll` (única aberta no REA) não tem a interface de ferramentas, então não há oráculo.
Alvo de REA futuro: strings e tratadores de teclado do `SketchUp.exe` (Shift, ModifierKeys, SU::Tool).

## O que o Shift faz em cada ferramenta do SketchUp

| Ferramenta | Shift | Ctrl | Observação |
|---|---|---|---|
| Linha, Retângulo (rot.), Arco, Pizza, Mão livre* | trava a inferência ativa (eixo, paralela, perpendicular, sobre aresta) enquanto segura | | * mão livre: sem efeito conhecido |
| Retângulo, Círculo, Polígono | trava a inferência de plano | | |
| Selecionar | alterna a entidade (soma se não estava, tira se estava) | soma | Ctrl+Shift tira |
| Apagar | OCULTA a aresta em vez de apagar | suaviza | Ctrl+Shift endurece (desfaz o suavizar) |
| Mover | trava a inferência | alterna cópia | Alt: dobra automática |
| Rotar | trava o plano do transferidor | cópia | |
| Escala | alterna uniforme/não uniforme | escala a partir do centro | |
| Tinta | preenche tudo o que tem o mesmo material | preenche faces vizinhas | Ctrl+Shift: mesmo material só no objeto; Alt amostra |
| Empurrar/Puxar | (sem função conhecida) | cria face nova (mantém a original) | |
| Offset, Siga-me | (sem função conhecida) | | Alt no Offset |
| Fita métrica, Transferidor, Dimensões | trava a inferência | Ctrl alterna criar guia | |
| Órbita | vira Panorâmica | | Zoom: Shift muda para campo de visão |

## Estado no SketchBuild (14/11/2026)

| Ferramenta | Antes | Agora |
|---|---|---|
| Linha, Retângulo rotacionado, Arco 2 pontos, Arco 3 pontos, Bézier | sem inferência de eixo | inferência de eixo no chão (vermelho x, verde y do SketchUp) quando o mouse chega a ~3° do eixo; **Shift trava o eixo inferido** enquanto segura; a prévia fica da cor do eixo |
| Selecionar (núcleo) | Shift soma | Shift alterna, Ctrl soma, Ctrl+Shift tira |
| Apagar (núcleo) | só apaga | Shift oculta (bit 0x01 da aresta, `soften.ocultar`, `POST /draw/soften {ocultar}`), Ctrl suaviza, Ctrl+Shift endurece; aresta oculta some do desenho e da seleção |
| Órbita | Shift+arrastar com o botão do meio já faz Panorâmica pelo `OrbitControls` do three (a conferir) | igual |
| Mover, Rotar, Escala, Tinta, Fita, Transferidor, Dimensões | por formulário/botões, não por mouse | NÃO implementado: sem gesto de mouse para ter o que travar |
| Retângulo, Círculo, Polígono | sem inferência de plano | NÃO implementado (o desenho é sempre no chão) |

## Assunções pendentes
- Tolerância do encaixe no eixo (3°) e a trava só nos eixos x e y do SketchUp no chão; sem eixo azul, sem paralela/perpendicular, sem "sobre aresta".
- Shift só trava se já havia eixo inferido ao apertar (como o SketchUp, que trava a inferência ativa; sem inferência não faz nada).
- Oculto: o bit 0x01 do 0x07d3 foi conferido na leitura de .skp (KMP-0202), mas a regra "Shift+Apagar oculta" e a rota não têm oráculo na SDK; ocultar também deveria esconder faces só com arestas ocultas, o que não foi feito.
- Mostrar geometria oculta (Exibir > Geometria oculta) não existe: arestas ocultas só voltam por desfazer ou pela API.
