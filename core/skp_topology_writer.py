"""B2: grava uma `Topology` (vértices, arestas, faces com furos) na raiz de um `.skp` VFF 2021+.

Parte de um modelo-base (por padrão um modelo vazio salvo pela própria SketchUpAPI, que é pequeno e
sem dados de ninguém), monta os registros do `model.dat` como o SketchUp grava (ver docs/FORMATO-SKP.md),
atualiza o contador de ids, a tabela `0x138e` e a caixa limite, refaz o registro externo `0x01f4` e o
inteiro de integridade do cabeçalho. O arquivo de entrada nunca é alterado.

Limites desta versão (assunções no FORMATO-SKP.md): só a raiz do modelo, sem material, sem curvas
(arestas de círculo e arco saem como arestas comuns) e sem instâncias novas.
"""
from __future__ import annotations

import os
import shutil
import struct
import tempfile
import zipfile
from typing import Dict, List, Optional, Sequence, Tuple

from core.skp_hidden_pruner import HEADER, _parse, valor_integridade
from core.topology.model import Topology, _dot, _newell, _norm, _sub, _unit

FLAGS_ARESTA = 0x06
FLAGS_FACE = 0x46


def _rec(tag: int, valor: bytes) -> bytes:
    return struct.pack("<HI", tag, len(valor)) + valor


def _id_bytes(n: int) -> bytes:
    """Inteiro little-endian com o tamanho mínimo (1 a 4 bytes)."""
    if n < 0 or n >= 1 << 32:
        raise ValueError(f"id fora do intervalo: {n}")
    w = max(1, (n.bit_length() + 7) // 8)
    return n.to_bytes(w, "little")


def _cabecalho(id_: int, flags: int) -> bytes:
    return _rec(0x07D0, _rec(0x05DC, _rec(0x05DE, _id_bytes(id_))) + _rec(0x07D3, bytes([flags])))


def _so_id(id_: int) -> bytes:
    return _rec(0x05DC, _rec(0x05DE, _id_bytes(id_)))


def _lacos_orientados(t: Topology, fid: int) -> Tuple[List[List[int]], Tuple[float, float, float, float]]:
    """Laços na ordem e no sentido que o SketchUp grava: externo anti-horário em torno da normal, furos horários."""
    f = t.faces[fid]
    n = _unit(f.normal)
    lacos = []
    for k, lp in enumerate(f.loops()):
        sentido = _dot(_newell([t.verts[v] for v in lp]), n)
        quer_positivo = k == 0
        lacos.append(list(lp) if (sentido > 0) == quer_positivo else list(reversed(lp)))
    p0 = t.verts[f.outer[0]]
    return lacos, (n[0], n[1], n[2], -_dot(n, p0))


def montar_entidades(t: Topology, primeiro_id: int) -> Tuple[Dict[str, bytes], int, Tuple[Optional[tuple], Optional[tuple]]]:
    """Registros 0x1389 (vértices), 0x138a (arestas), 0x138b (faces), tabela 0x138e e próximo id livre."""
    prox = primeiro_id
    vid: Dict[int, int] = {}
    eid: Dict[int, int] = {}
    fid_: Dict[int, int] = {}
    for v in sorted(t.verts):
        vid[v] = prox
        prox += 1
    for e in sorted(t.edges):
        eid[e] = prox
        prox += 1
    for f in sorted(t.faces):
        fid_[f] = prox
        prox += 1

    verts = b"".join(
        _rec(0x09C4, _so_id(vid[v]) + _rec(0x09C5, struct.pack("<3d", *t.verts[v]))) for v in sorted(t.verts)
    )
    arestas = b""
    for e in sorted(t.edges):
        a, b = t.edges[e]
        arestas += _rec(
            0x0BB8,
            _cabecalho(eid[e], FLAGS_ARESTA)
            + _rec(0x0BB9, _id_bytes(vid[a]))
            + _rec(0x0BBA, _id_bytes(vid[b])),
        )
    faces = b""
    for f in sorted(t.faces):
        lacos, plano = _lacos_orientados(t, f)
        corpo = b""
        for lp in lacos:
            itens = b""
            for i, v in enumerate(lp):
                w = lp[(i + 1) % len(lp)]
                e = t.edge_between(v, w)
                if e is None:
                    raise ValueError(f"a face {f} usa a aresta {v}-{w}, que não existe na topologia")
                sentido = 0 if t.edges[e] == (v, w) else 1
                itens += _rec(0x0FA0, _rec(0x0FA1, _id_bytes(eid[e])) + _rec(0x0FA2, bytes([sentido])))
            corpo += _rec(0x1194, _rec(0x1195, itens))
        faces += _rec(
            0x0DAC,
            _cabecalho(fid_[f], FLAGS_FACE) + _rec(0x0DAD, struct.pack("<4d", *plano)) + _rec(0x0DAE, corpo),
        )
    tabela = b"".join(bytes([len(_id_bytes(i))]) + _id_bytes(i) for i in list(eid.values()) + list(fid_.values()))
    pts = list(t.verts.values())
    caixa = None
    if pts:
        caixa = (tuple(min(p[k] for p in pts) for k in range(3)), tuple(max(p[k] for p in pts) for k in range(3)))
    return {"vertices": verts, "arestas": arestas, "faces": faces, "tabela": tabela}, prox, caixa


def _base_vazia(destino: str) -> None:
    """Modelo vazio salvo pela SketchUpAPI (Python 3.12)."""
    from core.su_api import SketchUpAPI

    api = SketchUpAPI()
    api.initialize()
    try:
        m = api.create_blank_model()
        try:
            m.save(destino)
        finally:
            m.close()
    finally:
        api.terminate()


def _ler_contador(m: bytes, rec_5f1: Tuple[int, int, int]) -> int:
    t, l, p = rec_5f1
    for a, ll, pp in _parse(m, p + 6, p + 6 + l):
        if a == 0x03E8:
            for b, lb, pb in _parse(m, pp + 6, pp + 6 + ll):
                if b == 0x03E9:
                    return int.from_bytes(m[pb + 6:pb + 6 + lb], "little")
    raise ValueError("contador de ids (0x01f5) não encontrado")


def gravar_topologia(t: Topology, destino: str, base: Optional[str] = None) -> Dict[str, int]:
    """Grava `t` na raiz de um modelo-base e salva em `destino` (que não pode ser o próprio `base`)."""
    with tempfile.TemporaryDirectory(prefix="skp_topo_") as tmp:
        if base is None:
            base = os.path.join(tmp, "base.skp")
            _base_vazia(base)
        if os.path.abspath(base) == os.path.abspath(destino):
            raise ValueError("base e destino não podem ser o mesmo arquivo")
        with open(base, "rb") as fh:
            cab = fh.read(4096)
        off = cab.find(b"PK\x03\x04")
        if off < 0:
            raise ValueError("a base não é um .skp VFF (sem ZIP)")
        prefixo = cab[:off]
        zin = zipfile.ZipFile(base)
        dat = zin.read("model.dat")

        ext = _parse(dat, 0, len(dat))
        if len(ext) != 1 or ext[0][0] != 0x01F4:
            raise ValueError("model.dat sem registro externo 0x01f4")
        filhos = _parse(dat, 6, len(dat))
        raiz = next(((a, l, p) for a, l, p in filhos if a == 0x01F6), None)
        cont = next(((a, l, p) for a, l, p in filhos if a == 0x01F5), None)
        if raiz is None or cont is None:
            raise ValueError("raiz do modelo (0x01f6) ou contador (0x01f5) não encontrados")
        ents = _parse(dat, raiz[2] + 6, raiz[2] + 6 + raiz[1])
        e1388 = next(((a, l, p) for a, l, p in ents if a == 0x1388), None)
        if e1388 is None:
            raise ValueError("entidades da raiz (0x1388) não encontradas")
        sub = _parse(dat, e1388[2] + 6, e1388[2] + 6 + e1388[1])
        if any(a in (0x1389, 0x138A, 0x138B, 0x138C, 0x138E, 0x13A0) for a, _, _ in sub):
            raise ValueError("a base já tem geometria na raiz; use um modelo vazio")

        primeiro = _ler_contador(dat, cont)
        reg, prox, caixa = montar_entidades(t, primeiro)

        novas = [(a, dat[p:p + 6 + l]) for a, l, p in sub]
        # ordem observada em r10: 07d0, 1389, 138a, 138b, 139e, 138e, 139b, 139f, 13a0
        corpo = b""
        geometria = b""
        if t.verts:
            geometria += _rec(0x1389, reg["vertices"])
        if t.edges:
            geometria += _rec(0x138A, reg["arestas"])
        if t.faces:
            geometria += _rec(0x138B, reg["faces"])
        for a, bruto in novas:
            if a == 0x139B and (t.edges or t.faces):
                corpo += _rec(0x138E, reg["tabela"])
            if a == 0x139F:
                bruto = _rec(0x139F, bytes([1])) if (t.edges or t.faces) else bruto
            corpo += bruto
            if a == 0x07D0:
                corpo += geometria
        if caixa:
            corpo += _rec(0x13A0, struct.pack("<6d", *caixa[0], *caixa[1]))
        n1388 = _rec(0x1388, corpo)

        raiz_corpo = b""
        for a, l, p in ents:
            raiz_corpo += n1388 if a == 0x1388 else dat[p:p + 6 + l]
        n_raiz = _rec(0x01F6, raiz_corpo)

        contador = _rec(0x01F5, _rec(0x03E8, _rec(0x03E9, _id_bytes(prox))))
        externo = b""
        for a, l, p in filhos:
            if a == 0x01F6:
                externo += n_raiz
            elif a == 0x01F5:
                externo += contador
            else:
                externo += dat[p:p + 6 + l]
        novo_dat = _rec(0x01F4, externo)

        zip_tmp = os.path.join(tmp, "novo.zip")
        with zipfile.ZipFile(zip_tmp, "w", allowZip64=True) as zout:
            for info in zin.infolist():
                if info.filename == "model.dat":
                    zi = zipfile.ZipInfo("model.dat", date_time=info.date_time)
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, novo_dat)
                else:
                    zout.writestr(info, zin.read(info.filename), compress_type=zipfile.ZIP_DEFLATED)
        zin.close()
        with zipfile.ZipFile(zip_tmp) as zchk:
            integ = valor_integridade([i.CRC for i in zchk.infolist()])
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        with open(destino, "wb") as out, open(zip_tmp, "rb") as zf:
            out.write(prefixo[:-4] + struct.pack("<I", integ))
            shutil.copyfileobj(zf, out)
    return {"vertices": len(t.verts), "arestas": len(t.edges), "faces": len(t.faces), "proximo_id": prox,
            "bytes": os.path.getsize(destino)}
