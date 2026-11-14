# Relatório da noite do REA (14/11/2026)

Só o projeto pessoal (`sketchup_companion`) foi alterado; **nada no 3D Parkelô**.

## Resultado
| Item | Estado | Onde |
|---|---|---|
| `SketchUp.exe` aberto no REA (133 mil funções, RTTI completa) | feito, após ajustar o limite do Ghidra para 4 h e esperar a análise terminar | `docs/REA-SketchUpExe-ferramentas.md` |
| Inventário das classes de ferramentas, entidades e algoritmos (com endereço) | feito | idem |
| Tipo 0x12 = face | confirmado por leitura (`CFaceFinder`) | idem |
| Regra do Empurrar/Puxar: recusa "cannot be stretched" e "curved or smoothed" | **lida**, semântica exata pendente | idem |
| SDK: `SUEntitiesFill` não divide face nem faz furo | **confirmada** | `docs/REA-DESENHO-EM-FACE.md` |
| SDK: transformação (mover/rotar/escalar/espelho) | **confirmada e implementada** no núcleo | `core/topology/edit.py`, `test_skp_transformar_sdk.py` |
| Fusão coplanar na SDK | inconclusivo | `docs/REA-DESENHO-EM-FACE.md` |

## Implementado no núcleo
Escala negativa (espelho): normal refletida e ordem dos vértices invertida, igual à SDK em 12 casos; fator zero recusado. API e front aceitam fator negativo.

## O que ficou pendente e por quê
- Aprofundar cada ferramenta (Empurrar/Puxar, Mover, Offset, Rotacionar, Escalar, Siga-me, formas, Linha): o método de abrir slot por slot da vtable gasta o contexto sem achar geometria. Retomar pelos textos de regra e pelos `callees` da função de clique (ver método na nota do `.exe`).
- Sem o REA, nenhuma regra de Empurrar/Puxar, Offset, Siga-me nem interseção entrou no núcleo (só regras confirmadas entram).

## Para a próxima sessão
1. Reiniciar o Claude com `CLAUDE_CODE_MCP_TOOL_IDLE_TIMEOUT=0` para o REA abrir o `.exe` sem cortar.
2. Atacar primeiro: Empurrar/Puxar (mensagens "curved or smoothed" e "cannot be stretched"), depois `CFaceFinder`/criação de face ao fechar ciclo e `CEdgeEraseSet`.
