"""T1: diferença registro a registro entre dois .skp (VFF 2021+).

Uso:  py -3.12 tools/tlv_diff.py A.skp B.skp [--raiz 0x01f6] [--max 80]

Achata o model.dat de cada arquivo em caminhos (tag/tag[n]/...) com o valor das folhas e mostra o que só existe
em A, só em B ou mudou. Ids e valores variam entre arquivos: o objetivo é ver QUAIS registros novos aparecem
quando uma única coisa muda (ex.: pintar uma face), não comparar byte a byte.
"""
import argparse
import io
import os
import sys
import zipfile
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.skp_hidden_pruner import _parse  # noqa: E402


def carregar_dat(caminho: str) -> bytes:
    b = open(caminho, "rb").read()
    o = b.find(b"PK\x03\x04")
    return zipfile.ZipFile(io.BytesIO(b[o:])).read("model.dat")


def _eh_conteiner(d: bytes, p: int, fim: int) -> bool:
    try:
        itens = _parse(d, p, fim)
    except Exception:
        return False
    return bool(itens) and all(0 < t < 0x7FFF for t, _, _ in itens) and sum(l + 6 for _, l, _ in itens) == fim - p


def achatar(d: bytes, p: int, fim: int, prefixo: str, out: Dict[str, List[str]], prof: int = 0) -> None:
    contagem: Dict[int, int] = {}
    for t, l, q in _parse(d, p, fim):
        n = contagem.get(t, 0)
        contagem[t] = n + 1
        caminho = "%s/%04x" % (prefixo, t)
        v0, v1 = q + 6, q + 6 + l
        if prof < 12 and l >= 6 and _eh_conteiner(d, v0, v1):
            achatar(d, v0, v1, caminho, out, prof + 1)
        else:
            out.setdefault(caminho, []).append(d[v0:v1].hex() if l <= 64 else "(%d bytes) %s..." % (l, d[v0:v0 + 24].hex()))


def diferenca(a: bytes, b: bytes) -> Dict[str, list]:
    fa: Dict[str, List[str]] = {}
    fb: Dict[str, List[str]] = {}
    achatar(a, 6, len(a), "", fa)
    achatar(b, 6, len(b), "", fb)
    so_a = {k: v for k, v in fa.items() if k not in fb}
    so_b = {k: v for k, v in fb.items() if k not in fa}
    mudou = {k: (fa[k], fb[k]) for k in fa if k in fb and (len(fa[k]) != len(fb[k]) or fa[k] != fb[k])}
    return {"so_a": so_a, "so_b": so_b, "mudou": mudou}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--max", type=int, default=80)
    x = ap.parse_args()
    r = diferenca(carregar_dat(x.a), carregar_dat(x.b))
    for rotulo, chave in (("SÓ EM A", "so_a"), ("SÓ EM B", "so_b")):
        print("== %s (%d caminhos)" % (rotulo, len(r[chave])))
        for k, v in list(r[chave].items())[: x.max]:
            print("  %s  x%d  %s" % (k, len(v), v[0]))
    print("== MUDOU (%d caminhos)" % len(r["mudou"]))
    for k, (va, vb) in list(r["mudou"].items())[: x.max]:
        print("  %s\n     A(%d): %s\n     B(%d): %s" % (k, len(va), va[:3], len(vb), vb[:3]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
