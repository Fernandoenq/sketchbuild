# REA/SDK: desenho sobre geometria existente (14/11/2026)

Oráculo: `tools/conferir_desenho_em_face_sdk.py` (SketchUpAPI, `SUEntitiesFill` com `SUGeometryInput`, um passo por desenho).

## Medido na SDK (CONFIRMADA)
| Caso | Resultado |
|---|---|
| Face 10x10 + linha de borda a borda (pontos novos) | 1 face, 5 arestas: a face **não é partida** |
| Face + linha solta no meio / canto a canto / cruzando duas arestas | 1 face, 5 arestas: nada é dividido |
| Face + retângulo dentro | **2 faces**, 8 arestas: a face grande continua inteira **sem furo**, a nova se sobrepõe |
| Face + retângulo encostado numa borda / meio fora | 2 faces, 8 arestas: sobreposição, sem recorte |
| Face + círculo de 12 lados dentro | 2 faces, 16 arestas: sobreposição, sem furo |
| `weld=False` | igual ao `weld=True` nos casos medidos |

## Conclusão
`SUEntitiesFill` só **acrescenta** geometria. Quem divide a aresta, parte a face, cria o furo e funde coplanares é a **lógica de interseção da ferramenta** (no `SketchUp.exe` ou no núcleo interno da DLL). A SDK exporta apenas `SUEntitiesTransform`, `SUEntitiesTransformMultiple`, `SUEntitiesWeld` e `SUModelMergeCoplanarFaces`; **não exporta** Intersect, PushPull, Offset nem Follow Me.

Consequência para o plano: as regras de "linha divide face", "retângulo/círculo em face cria furo" e Push/Pull/Offset só saem de REA do `SketchUp.exe` (e de arquivos feitos no SketchUp real). Até lá, o que o núcleo faz nesses casos é **SUPOSTA**.

Próximo oráculo possível na SDK: `SUEntitiesWeld` e `SUModelMergeCoplanarFaces` (o que fundem), e `SUEntitiesTransform` (mover/rotar/escalar).
