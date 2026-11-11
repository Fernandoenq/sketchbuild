"""T2: dump legível da árvore TLV do model.dat de um .skp (VFF 2021+).

Uso:
  py -3.12 -I tools/skp_inspect.py ARQUIVO.skp [--profundidade N] [--json SAIDA.json] [--tag 0x138b]

Cada registro é (tag uint16, tamanho uint32, valor). O valor é tratado como contêiner quando
cabe inteiro em registros bem formados com tags plausíveis; senão é folha e aparece em hex.
Os nomes de tag são os que o REA já confirmou (ver docs/FORMATO-SKP.md); o resto sai como 0xNNNN.
"""
import argparse
import json
import mmap
import os
import struct
import sys
import tempfile
import zipfile
from typing import Any, Dict, List, Optional, Tuple

HEADER = struct.Struct("<HI")
TAG_MAX = 0x7FFF

NOMES = {
    0x01F4: "registro_externo",
    0x01F6: "raiz_do_modelo",
    0x01F8: "tags",
    0x01F9: "definicoes",
    0x0063: "contador_de_definicoes?",
    0x05DC: "id_envoltorio",
    0x05DE: "id_da_entidade",
    0x07D0: "cabecalho_da_entidade",
    0x07D2: "id_da_tag",
    0x07D3: "flags(bit0=oculto)",
    0x1388: "entidades",
    0x1389: "vertices",
    0x138A: "arestas",
    0x138B: "faces",
    0x138C: "instancias",
    0x138D: "instancias_envolvidas",
    0x138E: "tabela_de_ids_dos_filhos",
    0x13A0: "caixa_limite",
    0x157C: "definicao",
    0x1770: "definicoes_lista",
    0x1771: "definicoes_itens",
    0x1964: "instancia",
    0x1967: "id_da_definicao",
    0x1D4C: "envoltorio_de_instancia",
    0x3A98: "tag_lista",
    0x3A99: "tag",
    0x3C8E: "tag_invisivel",
    0x7148: "camadas_por_cena",
    0x7150: "camada_oculta_na_cena",
}


def tentar(m, p: int, fim: int) -> Optional[List[Tuple[int, int, int]]]:
    out = []
    while p < fim:
        if p + 6 > fim:
            return None
        t, n = HEADER.unpack_from(m, p)
        if t == 0 or t > TAG_MAX or p + 6 + n > fim:
            return None
        out.append((t, n, p))
        p += 6 + n
    return out or None


def valor(m, p: int, n: int) -> Dict[str, Any]:
    b = bytes(m[p:p + n])
    d: Dict[str, Any] = {"hex": b[:48].hex() + ("..." if n > 48 else "")}
    if n == 1:
        d["u8"] = b[0]
    elif n == 2:
        d["u16"] = struct.unpack("<H", b)[0]
    elif n == 4:
        d["u32"] = struct.unpack("<I", b)[0]
        d["f32"] = round(struct.unpack("<f", b)[0], 6)
    elif n == 8:
        d["f64"] = round(struct.unpack("<d", b)[0], 9)
    elif n and n % 8 == 0 and n <= 96:
        d["f64s"] = [round(x, 6) for x in struct.unpack("<%dd" % (n // 8), b)]
    return d


def arvore(m, p: int, fim: int, prof: int, max_prof: int, so_tag: Optional[int], dentro: bool = False) -> List[Dict[str, Any]]:
    saida: List[Dict[str, Any]] = []
    filhos = tentar(m, p, fim)
    if filhos is None:
        return saida
    for t, n, q in filhos:
        no: Dict[str, Any] = {"tag": "0x%04x" % t, "nome": NOMES.get(t, ""), "tamanho": n, "posicao": q}
        sub = tentar(m, q + 6, q + 6 + n) if n >= 6 else None
        mostrar = so_tag is None or dentro or t == so_tag
        if sub is not None and prof < max_prof:
            no["filhos"] = arvore(m, q + 6, q + 6 + n, prof + 1, max_prof, so_tag, dentro or t == so_tag)
        elif sub is not None:
            no["filhos"] = "... (%d registros)" % len(sub)
        else:
            no.update(valor(m, q + 6, n))
        if mostrar or isinstance(no.get("filhos"), list) and no["filhos"]:
            saida.append(no)
    return saida


def carregar(caminho: str):
    with open(caminho, "rb") as fh:
        cab = fh.read(4096)
    off = cab.find(b"PK\x03\x04")
    if off < 0:
        raise ValueError("não é um .skp VFF (sem ZIP)")
    tmp = tempfile.mkdtemp(prefix="skp_inspect_")
    with zipfile.ZipFile(caminho) as z:
        dat = z.extract("model.dat", tmp)
        entradas = [(i.filename, i.file_size, i.CRC) for i in z.infolist()]
    return dat, off, cab[:off], entradas


def imprimir(nos: List[Dict[str, Any]], nivel: int = 0, out=sys.stdout) -> None:
    for no in nos:
        extra = ""
        for k in ("u8", "u16", "u32", "f32", "f64", "f64s"):
            if k in no:
                extra += " %s=%s" % (k, no[k])
        if "hex" in no and "u8" not in no and "u16" not in no and "u32" not in no:
            extra += " hex=%s" % no["hex"]
        nome = (" " + no["nome"]) if no["nome"] else ""
        out.write("%s%s%s [%d]%s\n" % ("  " * nivel, no["tag"], nome, no["tamanho"], extra))
        if isinstance(no.get("filhos"), list):
            imprimir(no["filhos"], nivel + 1, out)
        elif isinstance(no.get("filhos"), str):
            out.write("%s  %s\n" % ("  " * nivel, no["filhos"]))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("arquivo")
    ap.add_argument("--profundidade", type=int, default=6)
    ap.add_argument("--json", dest="saida_json")
    ap.add_argument("--tag", help="só mostra o ramo que passa por esta tag (ex.: 0x138b)")
    a = ap.parse_args(argv)
    dat, off, prefixo, entradas = carregar(a.arquivo)
    so_tag = int(a.tag, 0) if a.tag else None
    with open(dat, "rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as m:
        nos = arvore(m, 0, len(m), 0, a.profundidade, so_tag)
        print("# prefixo: %d bytes | model.dat: %d bytes | entradas do zip: %d" % (off, len(m), len(entradas)))
        imprimir(nos)
        if a.saida_json:
            with open(a.saida_json, "w", encoding="utf-8") as out:
                json.dump({"prefixo": off, "arvore": nos}, out, ensure_ascii=False, indent=1)
    os.remove(dat)
    return 0


if __name__ == "__main__":
    sys.exit(main())
