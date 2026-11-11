"""Poda de ocultos direto no `model.dat` (sem abrir o SketchUp).

Remove de um .skp (VFF 2021+):
  - instâncias (grupos e componentes) ocultas (bit 0x01 da tag 0x07d3);
  - instâncias que estão em tag (camada) invisível;
  - as definições que ficam sem nenhuma instância viva (a "limpeza de não usados").

Estrutura usada (conferida em modelos reais, ver REVERSE_ENGINEERING_NOTES.md §186-187):
  0x01f9 > 0x1770 > 0x1771 > [0x0063, 0x157c (definição) ...]
  0x157c > 0x1388 (entidades) > 0x07d0 (cabeçalho com o ID), 0x1389/0x138a/0x138b (vértices,
          arestas, faces), 0x138c > 0x1964 (instância), 0x138d > 0x1d4c > 0x1964 (instância em
          envoltório), 0x138e (tabela com o ID de cada filho), 0x13a0 (caixa limite)
  0x01f6 > 0x1388: definição raiz do modelo
  0x01f8 > 0x3a98 > 0x3a99: tags; 0x3c8e = 1 quando invisível
Instância 0x1964 > 0x07d0: 0x05dc>0x05de = ID, 0x07d3 = flags, 0x07d2 = ID da tag (ausente = Layer0);
0x1967 = ID da definição (o ID da definição é o do 0x07d0 do seu 0x1388).

O original nunca é alterado: lê de `origem` e grava só em `destino`.
Arestas e faces ocultas dentro das definições não são tocadas (mexem na topologia).
"""
from __future__ import annotations

import mmap
import os
import shutil
import struct
import tempfile
import zipfile
import zlib
from typing import Dict, Iterable, List, Optional, Set, Tuple

Rec = Tuple[int, int, int]  # (tag, tamanho do valor, posição do cabeçalho)

HEADER = struct.Struct("<HI")
HIDDEN_BIT = 0x01


def _parse(m, p: int, end: int) -> List[Rec]:
    out: List[Rec] = []
    while p < end:
        if p + 6 > end:
            raise ValueError(f"registro truncado em {p:#x}")
        t, l = HEADER.unpack_from(m, p)
        if p + 6 + l > end:
            raise ValueError(f"tamanho estoura em {p:#x} (tag {t:#06x})")
        out.append((t, l, p))
        p += 6 + l
    return out


def _try_parse(m, p: int, end: int) -> Optional[List[Rec]]:
    try:
        return _parse(m, p, end)
    except ValueError:
        return None


def _varint(b) -> int:
    return int.from_bytes(bytes(b), "little")


def _eid(m, hdr_rec: Rec) -> Optional[int]:
    """ID da entidade dentro de um 0x07d0 (0x05dc > 0x05de)."""
    t, l, p = hdr_rec
    for a, ll, pp in _parse(m, p + 6, p + 6 + l):
        if a == 0x05DC:
            inner = bytes(m[pp + 6: pp + 6 + ll])
            if inner[:2] == b"\xde\x05":
                n = struct.unpack_from("<I", inner, 2)[0]
                return _varint(inner[6:6 + n])
        if a == 0x05DE:
            return _varint(m[pp + 6: pp + 6 + ll])
    return None


def _find_all(m, p, end, tag, depth=0, limit=8, out=None):
    out = [] if out is None else out
    ks = _try_parse(m, p, end)
    if ks is None:
        return out
    for a, l, q in ks:
        if a == tag:
            out.append((a, l, q))
        if l >= 6 and depth < limit:
            _find_all(m, q + 6, q + 6 + l, tag, depth + 1, limit, out)
    return out


def valor_integridade(crcs: List[int]) -> int:
    """Inteiro que o SketchUp grava nos 4 últimos bytes do cabeçalho VFF e confere ao abrir.

    É um CRC32 encadeado sobre os CRCs das entradas do ZIP, na ordem do ZIP: primeiro as posições
    pares (CRC invertido), depois as ímpares (menos 0x2a quando maior que 0x2a). Se o ZIP muda
    (por exemplo o model.dat podado) e este valor não acompanha, o SketchUp avisa que
    "este modelo falhou nas verificações de integridade do arquivo".
    """
    v = 0
    for i, c in enumerate(crcs):
        if i % 2 == 0:
            v = zlib.crc32(struct.pack("<I", ~c & 0xFFFFFFFF), v)
    for i, c in enumerate(crcs):
        if i % 2 == 1:
            v = zlib.crc32(struct.pack("<I", c - 0x2A if c > 0x2A else c), v)
    return v


class _Instancia:
    __slots__ = ("id", "oculta", "tag", "def_ref")

    def __init__(self, id_, oculta, tag, def_ref):
        self.id, self.oculta, self.tag, self.def_ref = id_, oculta, tag, def_ref


def _instancia(m, rec: Rec) -> _Instancia:
    """`rec` é o 0x1964 ou o 0x1d4c que o envolve."""
    t, l, p = rec
    if t == 0x1D4C:
        inner = _parse(m, p + 6, p + 6 + l)[0]
        t, l, p = inner
    hdr = flags = tag = ref = None
    for a, ll, pp in _parse(m, p + 6, p + 6 + l):
        if a == 0x07D0:
            hdr = (a, ll, pp)
            for a2, l2, p2 in _parse(m, pp + 6, pp + 6 + ll):
                if a2 == 0x07D3 and l2:
                    flags = m[p2 + 6]
                elif a2 == 0x07D2:
                    tag = _varint(m[p2 + 6: p2 + 6 + l2])
        elif a == 0x1967:
            ref = _varint(m[pp + 6: pp + 6 + ll])
    return _Instancia(_eid(m, hdr), bool((flags or 0) & HIDDEN_BIT), tag, ref)


def _slice(m, a: int, b: int):
    return memoryview(m)[a:b]


def _rec(tag: int, parts: List) -> List:
    n = sum(len(x) for x in parts)
    return [HEADER.pack(tag, n)] + parts


def _raw(m, r: Rec) -> List:
    t, l, p = r
    return [_slice(m, p, p + 6 + l)]


def _len(parts: Iterable) -> int:
    return sum(len(x) for x in parts)


class _Plano:
    """Plano de poda de um model.dat mapeado em memória."""

    def __init__(self, m, modo: str = "completo"):
        # modo: "identidade" (não remove nada), "instancias" (só instâncias) ou "completo"
        self.modo = modo
        self.m = m
        self.top = _parse(m, 16, len(m))
        self.f9 = next(r for r in self.top if r[0] == 0x01F9)
        f9k = _parse(m, self.f9[2] + 6, self.f9[2] + 6 + self.f9[1])
        self.r1770 = next(r for r in f9k if r[0] == 0x1770)
        k1770 = _parse(m, self.r1770[2] + 6, self.r1770[2] + 6 + self.r1770[1])
        self.r1771 = next(r for r in k1770 if r[0] == 0x1771)
        self.f9_kids, self.k1770 = f9k, k1770
        self.k1771 = _parse(m, self.r1771[2] + 6, self.r1771[2] + 6 + self.r1771[1])
        self.root = next(r for r in self.top if r[0] == 0x01F6)
        self.tags_invisiveis = self._tags_invisiveis()
        self.defs: Dict[int, Rec] = {}
        self.ents: Dict[Optional[int], Rec] = {}  # id da def (None = raiz) -> 0x1388
        self.insts: Dict[Optional[int], List[Tuple[Rec, _Instancia]]] = {}
        for r in self.k1771:
            if r[0] != 0x157C:
                continue
            e = next(x for x in _parse(m, r[2] + 6, r[2] + 6 + r[1]) if x[0] == 0x1388)
            did = self._ents_id(e)
            self.defs[did] = r
            self.ents[did] = e
            self.insts[did] = self._instancias_de(e)
        e = next(x for x in _parse(m, self.root[2] + 6, self.root[2] + 6 + self.root[1]) if x[0] == 0x1388)
        self.ents[None] = e
        self.insts[None] = self._instancias_de(e)

    def _tags_invisiveis(self) -> Set[int]:
        m, out = self.m, set()
        for lo, hi in ((16, self.f9[2]), (self.f9[2] + 6 + self.f9[1], len(m))):
            for _, l, q in _find_all(m, lo, hi, 0x3C8C):
                tid, hidden = None, False
                for a, ll, pp in _parse(m, q + 6, q + 6 + l):
                    if a == 0x05DC:
                        inner = bytes(m[pp + 6: pp + 6 + ll])
                        n = struct.unpack_from("<I", inner, 2)[0]
                        tid = _varint(inner[6:6 + n])
                    elif a == 0x3C8E and ll:
                        hidden = m[pp + 6] == 1
                if hidden and tid is not None:
                    out.add(tid)
        return out

    def _ents_id(self, e: Rec) -> int:
        hdr = next(x for x in _parse(self.m, e[2] + 6, e[2] + 6 + e[1]) if x[0] == 0x07D0)
        return _eid(self.m, hdr)

    def _instancias_de(self, e: Rec) -> List[Tuple[Rec, _Instancia]]:
        m, out = self.m, []
        for a, l, p in _parse(m, e[2] + 6, e[2] + 6 + e[1]):
            if a in (0x138C, 0x138D):
                for r in _parse(m, p + 6, p + 6 + l):
                    out.append((r, _instancia(m, r)))
        return out

    def morta(self, inst: _Instancia) -> bool:
        if self.modo == "identidade":
            return False
        return inst.oculta or (inst.tag is not None and inst.tag in self.tags_invisiveis)

    def vivas(self) -> Set[int]:
        """Definições alcançáveis a partir da raiz por instâncias vivas."""
        vistas: Set[int] = set()
        fila = [None]
        while fila:
            d = fila.pop()
            for _, inst in self.insts[d]:
                if self.morta(inst) or inst.def_ref in vistas or inst.def_ref not in self.defs:
                    continue
                vistas.add(inst.def_ref)
                fila.append(inst.def_ref)
        return vistas

    # -- reescrita -------------------------------------------------------------

    def _ents_parts(self, did: Optional[int]) -> Tuple[List, int]:
        """Partes do 0x1388 sem as instâncias mortas. Devolve (partes do registro, removidas)."""
        m, e = self.m, self.ents[did]
        mortas = {i.id for _, i in self.insts[did] if self.morta(i)}
        if not mortas:
            return _raw(m, e), 0
        filhos: List = []
        for a, l, p in _parse(m, e[2] + 6, e[2] + 6 + e[1]):
            if a in (0x138C, 0x138D):
                keep = [r for r in _parse(m, p + 6, p + 6 + l) if _instancia(m, r).id not in mortas]
                if not keep:
                    continue
                if len(keep) == len(_parse(m, p + 6, p + 6 + l)):
                    filhos += _raw(m, (a, l, p))
                else:
                    corpo: List = []
                    for r in keep:
                        corpo += _raw(m, r)
                    filhos += _rec(a, corpo)
            elif a == 0x138E:
                tab, q, fim = bytearray(), p + 6, p + 6 + l
                while q < fim:
                    n = m[q]
                    if _varint(m[q + 1: q + 1 + n]) not in mortas:
                        tab += m[q: q + 1 + n]
                    q += 1 + n
                filhos += _rec(a, [bytes(tab)])
            else:
                filhos += _raw(m, (a, l, p))
        return _rec(0x1388, filhos), len(mortas)

    def escrever(self, saida) -> Dict[str, int]:
        """Grava o model.dat podado em `saida` (arquivo binário aberto). Devolve o relatório."""
        m = self.m
        vivas = set(self.defs) if self.modo != "completo" else self.vivas()
        rel = {"definicoes_antes": len(self.defs), "definicoes_removidas": 0,
               "instancias_removidas": 0, "instancias_total": sum(len(v) for v in self.insts.values())}

        defs_parts: List = []
        for r in self.k1771:
            if r[0] != 0x157C:
                defs_parts += _raw(m, r)
                continue
            did = self._ents_id(next(x for x in _parse(m, r[2] + 6, r[2] + 6 + r[1]) if x[0] == 0x1388))
            if did not in vivas:
                rel["definicoes_removidas"] += 1
                continue
            ent_parts, n = self._ents_parts(did)
            rel["instancias_removidas"] += n
            if n == 0:
                defs_parts += _raw(m, r)
                continue
            corpo: List = []
            for a, l, p in _parse(m, r[2] + 6, r[2] + 6 + r[1]):
                corpo += ent_parts if a == 0x1388 else _raw(m, (a, l, p))
            defs_parts += _rec(0x157C, corpo)
        p1771 = _rec(0x1771, defs_parts)

        def com_filhos(pai: Rec, kids: List[Rec], troca_tag: int, troca_parts: List) -> List:
            c: List = []
            for k in kids:
                c += troca_parts if k[0] == troca_tag else _raw(m, k)
            return _rec(pai[0], c)

        p1770 = com_filhos(self.r1770, self.k1770, 0x1771, p1771)
        p1f9 = com_filhos(self.f9, self.f9_kids, 0x1770, p1770)

        raiz_parts, n = self._ents_parts(None)
        rel["instancias_removidas"] += n
        rk = _parse(m, self.root[2] + 6, self.root[2] + 6 + self.root[1])
        p1f6 = com_filhos(self.root, rk, 0x1388, raiz_parts)

        corpo_parts: List = []
        for r in self.top:
            corpo_parts += p1f9 if r is self.f9 else p1f6 if r is self.root else _raw(m, r)
        # o registro externo 0x01f4 (6 bytes de cabeçalho + 0x0063 de 10 bytes) cobre o arquivo todo:
        # o tamanho dele precisa acompanhar a poda, senão o SketchUp recusa o arquivo
        externo = m[0:16]
        total = 10 + _len(corpo_parts)
        saida.write(HEADER.pack(HEADER.unpack_from(externo, 0)[0], total) + bytes(externo[6:16]))
        for x in corpo_parts:
            saida.write(x)
        return rel


def podar_skp(origem: str, destino: str, modo: str = "completo") -> Dict[str, int]:
    """Gera `destino` sem as partes ocultas de `origem` (que não é alterado)."""
    if os.path.abspath(origem) == os.path.abspath(destino):
        raise ValueError("origem e destino não podem ser o mesmo arquivo")
    with open(origem, "rb") as fh:
        head = fh.read(4096)
    off = head.find(b"PK\x03\x04")
    if off < 0:
        raise ValueError("não é um .skp VFF (sem ZIP)")
    with tempfile.TemporaryDirectory(prefix="skp_poda_") as tmp:
        with open(origem, "rb") as fh:
            prefixo = fh.read(off)
        zin = zipfile.ZipFile(origem)  # o zipfile acha o início do ZIP após o prefixo
        if struct.unpack("<I", prefixo[-4:])[0] != valor_integridade([i.CRC for i in zin.infolist()]):
            zin.close()
            raise ValueError("cabeçalho de integridade do original não bate com o cálculo conhecido "
                             "(formato fora do padrão VFF 2021+); arquivo ignorado")
        dat_in = zin.extract("model.dat", tmp)
        dat_out = os.path.join(tmp, "model_novo.dat")
        with open(dat_in, "rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as m:
            plano = _Plano(m, modo)
            with open(dat_out, "wb") as out:
                rel = plano.escrever(out)
        os.remove(dat_in)
        zip_tmp = os.path.join(tmp, "novo.zip")
        with zipfile.ZipFile(zip_tmp, "w", allowZip64=True) as zout:
            for info in zin.infolist():
                if info.filename == "model.dat":
                    continue
                zout.writestr(info, zin.read(info.filename), compress_type=zipfile.ZIP_DEFLATED)
            zinfo = zipfile.ZipInfo("model.dat", date_time=zin.getinfo("model.dat").date_time)
            zinfo.compress_type = zipfile.ZIP_DEFLATED
            with open(dat_out, "rb") as fh, zout.open(zinfo, "w", force_zip64=True) as w:
                shutil.copyfileobj(fh, w, 8 * 1024 * 1024)
        zin.close()
        with zipfile.ZipFile(zip_tmp) as zchk:
            integridade = valor_integridade([i.CRC for i in zchk.infolist()])
        prefixo = prefixo[:-4] + struct.pack("<I", integridade)
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        with open(destino, "wb") as out, open(zip_tmp, "rb") as zf:
            out.write(prefixo)
            shutil.copyfileobj(zf, out, 8 * 1024 * 1024)
    rel["bytes_antes"] = os.path.getsize(origem)
    rel["bytes_depois"] = os.path.getsize(destino)
    return rel


def verificar_skp(caminho: str) -> Dict[str, int]:
    """Confere um .skp gerado: ZIP íntegro, cabeçalho de integridade, zero ocultos, sem referências quebradas."""
    with open(caminho, "rb") as fh:
        head = fh.read(4096)
    off = head.find(b"PK")
    with zipfile.ZipFile(caminho) as z:
        if z.testzip() is not None:
            raise ValueError("ZIP corrompido")
        if struct.unpack("<I", head[off - 4:off])[0] != valor_integridade([i.CRC for i in z.infolist()]):
            raise ValueError("cabeçalho de integridade não confere")
        with tempfile.TemporaryDirectory(prefix="skp_verif_") as tmp:
            dat = z.extract("model.dat", tmp)
            with open(dat, "rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as m:
                if HEADER.unpack_from(m, 0)[1] + 6 != len(m):
                    raise ValueError("tamanho do registro externo do model.dat não confere")
                p = _Plano(m)
                todas = [i for v in p.insts.values() for _, i in v]
                rel = {
                    "definicoes": len(p.defs),
                    "instancias": len(todas),
                    "ocultas": sum(1 for i in todas if p.morta(i)),
                    "refs_quebradas": sum(1 for i in todas if i.def_ref not in p.defs),
                }
                del p
    return rel


def podar_pasta(origem: str, destino: str) -> Dict[str, dict]:
    """Poda todos os .skp de `origem` para `destino` (do menor para o maior); pula os já prontos."""
    import json
    import time

    os.makedirs(destino, exist_ok=True)
    resumo_path = os.path.join(destino, "_resumo.json")
    resumo: Dict[str, dict] = {}
    if os.path.exists(resumo_path):
        with open(resumo_path, encoding="utf-8") as fh:
            resumo = json.load(fh)
    arquivos = sorted((f for f in os.listdir(origem) if f.lower().endswith(".skp")),
                      key=lambda f: os.path.getsize(os.path.join(origem, f)))
    for n, f in enumerate(arquivos, 1):
        saida = os.path.join(destino, f)
        if resumo.get(f, {}).get("ok") and os.path.exists(saida):
            continue
        t0 = time.time()
        print(f"[{n}/{len(arquivos)}] {f} ...", flush=True)
        try:
            rel = podar_skp(os.path.join(origem, f), saida)
            rel["verificacao"] = verificar_skp(saida)
            if rel["verificacao"]["ocultas"] or rel["verificacao"]["refs_quebradas"]:
                raise ValueError(f"verificação falhou: {rel['verificacao']}")
            rel["ok"] = True
            rel["segundos"] = round(time.time() - t0)
            print(f"    ok: {rel['bytes_antes'] // 2**20} MB -> {rel['bytes_depois'] // 2**20} MB, "
                  f"{rel['definicoes_removidas']} defs e {rel['instancias_removidas']} instâncias removidas "
                  f"({rel['segundos']}s)", flush=True)
        except Exception as exc:  # noqa: BLE001 - segue para o próximo arquivo
            if os.path.exists(saida):
                os.remove(saida)
            rel = {"ok": False, "erro": f"{type(exc).__name__}: {exc}"}
            print(f"    PULADO: {rel['erro']}", flush=True)
        resumo[f] = rel
        with open(resumo_path, "w", encoding="utf-8") as fh:
            json.dump(resumo, fh, indent=1, ensure_ascii=False)
    return resumo


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 3:
        sys.exit("uso: python -m core.skp_hidden_pruner ORIGEM.skp DESTINO.skp  (ou ORIGEM_DIR DESTINO_DIR)")
    if os.path.isdir(sys.argv[1]):
        podar_pasta(sys.argv[1], sys.argv[2])
    else:
        print(json.dumps(podar_skp(sys.argv[1], sys.argv[2]), indent=2))
