"""A5: auditoria de fidelidade dos módulos de core/ (e das rotas do app).

Uso:  python tools/auditar_frentes.py            (gera docs/AUDITORIA-FUNCIONALIDADES.md e docs/auditoria.json)

O script NÃO decide sozinho que algo é "real": só junta fatos mensuráveis (tamanho, testes que citam
o módulo, rotas que importam o módulo, uso da DLL, palavras de alerta) e aplica a regra de selo abaixo.

Selos (do mais para o menos confiável):
  VALIDADO   conferido contra um oráculo (lista ORACULOS: SketchUp real, SketchUpAPI.dll ou golden)
  TESTADO    tem teste automatizado que cita o módulo, mas o teste só confere consistência interna
  SEM TESTE  é usado pelo app, mas nenhum teste cita o módulo
  ORFAO      nem o app nem os testes usam o módulo (código morto ou ainda não ligado)
Alerta: o módulo cita palavras como simul, mock, placeholder, stub, dummy, fake, exemplo, aproxim.
"""
import ast
import json
import os
import re
import sys
from typing import Dict, List

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Oráculos reais confirmados nesta sessão ou em sessões anteriores (REVERSE_ENGINEERING_NOTES.md, docs/f0)
ORACULOS = {
    "skp_hidden_pruner": "SketchUp real (KMP-0102) + 62 arquivos verificados",
    "skp_topology_writer": "SketchUpAPI.dll (roundtrip, 8 testes) ; B4 no SketchUp real pendente",
    "su_api": "é a própria SketchUpAPI.dll",
    "mesh_extractor": "SketchUpAPI.dll",
    "skp_binary_reader": "diferenças de faces batem com o Ruby nas receitas F0",
}
ORACULOS_PACOTE = {"topology": "receitas golden F0 (r01 a r14)"}

ALERTAS = re.compile(r"simul|mock|placeholder|stub|dummy|fake|exemplo|aproxima|hardcod|fict[ií]cio|demonstra", re.I)


def _lista(pasta: str, ext: str = ".py") -> List[str]:
    out = []
    for dp, _, fs in os.walk(pasta):
        if "__pycache__" in dp:
            continue
        out += [os.path.join(dp, f) for f in fs if f.endswith(ext)]
    return sorted(out)


def _ler(p: str) -> str:
    with open(p, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def auditar() -> List[Dict]:
    core = [p for p in _lista(os.path.join(RAIZ, "core")) if os.path.basename(p) != "__init__.py"]
    testes = {p: _ler(p) for p in _lista(RAIZ) if os.path.basename(p).startswith("test_") and os.path.dirname(p) == RAIZ}
    app = {p: _ler(p) for p in _lista(os.path.join(RAIZ, "app"))}
    rotas = {p: t for p, t in app.items() if os.sep + "routes" + os.sep in p}
    resultado = []
    for p in core:
        rel = os.path.relpath(p, RAIZ).replace(os.sep, "/")
        nome = os.path.splitext(os.path.basename(p))[0]
        pacote = rel.split("/")[1] if rel.count("/") > 1 else ""
        src = _ler(p)
        try:
            arv = ast.parse(src)
            doc = (ast.get_docstring(arv) or "").strip().splitlines()
            doc1 = doc[0] if doc else ""
            funcoes = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(arv))
        except SyntaxError:
            doc1, funcoes = "(erro de sintaxe)", 0
        padrao = re.compile(r"\b%s\b" % re.escape(nome))
        usado_em_testes = sorted(os.path.basename(t) for t, s in testes.items() if padrao.search(s))
        usado_em_app = sorted(os.path.relpath(a, RAIZ).replace(os.sep, "/") for a, s in app.items() if padrao.search(s))
        usado_em_core = sorted(os.path.basename(c) for c in core if c != p and padrao.search(_ler(c)))
        usa_dll = bool(re.search(r"SketchUpAPI|su_api|ctypes", src))
        alertas = sorted({m.group(0).lower() for m in ALERTAS.finditer(src)})
        oraculo = ORACULOS.get(nome) or ORACULOS_PACOTE.get(pacote)
        if oraculo:
            selo = "VALIDADO"
        elif usado_em_testes:
            selo = "TESTADO"
        elif usado_em_app or usado_em_core:
            selo = "SEM TESTE"
        else:
            selo = "ORFAO"
        resultado.append({
            "modulo": rel, "linhas": src.count("\n") + 1, "funcoes": funcoes, "descricao": doc1[:110],
            "selo": selo, "oraculo": oraculo or "", "testes": usado_em_testes, "rotas_ou_app": usado_em_app,
            "usado_por_core": usado_em_core, "usa_dll": usa_dll, "alertas": alertas,
        })
    return resultado


def rigor_dos_testes() -> Dict[str, int]:
    """Conta asserts frouxos (limites, tipo de entidade, presença) contra asserts de valor exato nos test_frentes_*.py."""
    frouxos = re.compile(r"assertGreater|assertLess|assertTrue|assertIn|assertIsNotNone|assertIsInstance|entity_type")
    exatos = re.compile(r"assertAlmostEqual|assertEqual\(")
    f = e = 0
    for p in _lista(RAIZ):
        if os.path.basename(p).startswith("test_frentes_") and os.path.dirname(p) == RAIZ:
            for ln in _ler(p).splitlines():
                if "assertEqual" in ln and "entity_type" in ln:
                    f += 1
                elif frouxos.search(ln):
                    f += 1
                elif exatos.search(ln):
                    e += 1
    return {"frouxos": f, "exatos": e}


def gerar(resultado: List[Dict]) -> str:
    por_selo: Dict[str, int] = {}
    for r in resultado:
        por_selo[r["selo"]] = por_selo.get(r["selo"], 0) + 1
    total_linhas = sum(r["linhas"] for r in resultado)
    L: List[str] = []
    L.append("# Auditoria de funcionalidades (gerada por `tools/auditar_frentes.py`)")
    L.append("")
    L.append("Arquivo gerado. Não editar à mão: rode `python tools/auditar_frentes.py`. Regra dos selos no cabeçalho do script.")
    L.append("")
    L.append("## Resumo")
    L.append("")
    L.append("| Selo | Módulos | Significado |")
    L.append("|---|---|---|")
    sig = {
        "VALIDADO": "conferido contra o SketchUp real, a SketchUpAPI.dll ou golden",
        "TESTADO": "teste automatizado cita o módulo, mas só confere consistência interna (sem oráculo)",
        "SEM TESTE": "usado pelo app ou por outro módulo, nenhum teste o cita",
        "ORFAO": "nem o app, nem outros módulos, nem testes o usam",
    }
    for s in ("VALIDADO", "TESTADO", "SEM TESTE", "ORFAO"):
        L.append("| %s | %d | %s |" % (s, por_selo.get(s, 0), sig[s]))
    L.append("")
    L.append("Total: %d módulos em `core/`, %d linhas. Módulos com palavra de alerta (simul, mock, placeholder, etc.): %d." % (
        len(resultado), total_linhas, sum(1 for r in resultado if r["alertas"])))
    L.append("")
    r = rigor_dos_testes()
    L.append("Rigor dos testes das frentes (`test_frentes_*.py`): %d asserts frouxos (limite mínimo, tipo de entidade, presença) contra %d de valor exato." % (r["frouxos"], r["exatos"]))
    L.append("")
    L.append("**Leitura honesta:** só VALIDADO tem prova de fidelidade ao SketchUp. TESTADO significa que o código faz o que o")
    L.append("próprio teste espera, o que não prova que o resultado bate com o SketchUp ou com a norma citada.")
    L.append("")
    for selo in ("ORFAO", "SEM TESTE", "TESTADO", "VALIDADO"):
        itens = sorted((r for r in resultado if r["selo"] == selo), key=lambda r: (-len(r["alertas"]), -r["linhas"]))
        if not itens:
            continue
        L.append("## %s (%d)" % (selo, len(itens)))
        L.append("")
        L.append("| Módulo | Linhas | Descrição | Testes | App/rotas | DLL | Alertas |")
        L.append("|---|---|---|---|---|---|---|")
        for r in itens:
            L.append("| `%s` | %d | %s | %s | %s | %s | %s |" % (
                r["modulo"], r["linhas"], r["descricao"].replace("|", "/") or "-",
                ", ".join(r["testes"][:3]) + ("..." if len(r["testes"]) > 3 else "") or "-",
                str(len(r["rotas_ou_app"])) if r["rotas_ou_app"] else "-",
                "sim" if r["usa_dll"] else "-", ", ".join(r["alertas"]) or "-"))
        L.append("")
    return "\n".join(L)


def main() -> int:
    res = auditar()
    with open(os.path.join(RAIZ, "docs", "AUDITORIA-FUNCIONALIDADES.md"), "w", encoding="utf-8") as fh:
        fh.write(gerar(res))
    with open(os.path.join(RAIZ, "docs", "auditoria.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=1)
    c: Dict[str, int] = {}
    for r in res:
        c[r["selo"]] = c.get(r["selo"], 0) + 1
    print("auditados %d módulos: %s" % (len(res), c))
    return 0


if __name__ == "__main__":
    sys.exit(main())
