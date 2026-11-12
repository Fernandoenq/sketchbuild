"""B2: grava uma `Topology` (vértices, arestas, faces com furos) na raiz de um `.skp` VFF 2021+.

Parte de um modelo-base (por padrão um modelo vazio salvo pela própria SketchUpAPI, que é pequeno e
sem dados de ninguém), monta os registros do `model.dat` como o SketchUp grava (ver docs/FORMATO-SKP.md),
atualiza o contador de ids, a tabela `0x138e` e a caixa limite, refaz o registro externo `0x01f4` e o
inteiro de integridade do cabeçalho. O arquivo de entrada nunca é alterado.

Limites desta versão (assunções no FORMATO-SKP.md): só a raiz do modelo, sem material, curvas só de círculo e arco
(registro 0x1397, ver FORMATO-SKP.md) e sem instâncias novas.
"""
from __future__ import annotations

import math
import os
import time
import uuid
import shutil
import struct
import tempfile
import zipfile
from typing import Dict, List, Optional, Sequence, Tuple

from core.skp_hidden_pruner import HEADER, _parse, valor_integridade
from core.topology.model import Topology, _cross, _dot, _newell, _norm, _sub, _unit

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


def _cabecalho(id_: int, flags: int, material: Optional[int] = None) -> bytes:
    mat = _rec(0x07D1, _id_bytes(material)) if material is not None else b""
    return _rec(0x07D0, _rec(0x05DC, _rec(0x05DE, _id_bytes(id_))) + mat + _rec(0x07D3, bytes([flags])))


def nome_seguro(nome: str) -> str:
    """Nome do diretório do material no ZIP: o SketchUp troca '/' por '_'."""
    return "".join("_" if c in INVALIDOS else c for c in nome)


INVALIDOS = '/\\:*?"<>|'

_XML_MATERIAL = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>\n'
    '<materialDocument xmlns="http://sketchup.google.com/schemas/sketchup/1.0/material" '
    'xmlns:mat="http://sketchup.google.com/schemas/sketchup/1.0/material">\n'
    '  <mat:material name=%s type="0" workflow="0" colorRed="%d" colorGreen="%d" colorBlue="%d" colorizeType="0" '
    'trans="%s" useTrans="%d" pbrPromoState="%d" hasTexture="0">\n'
    '    <mat:pbrMR xScale="1" yScale="1">\n'
    '      <mat:enable_metalness>0</mat:enable_metalness>\n'
    '      <mat:enable_roughness>0</mat:enable_roughness>\n'
    '      <mat:roughness_texture_invert>0</mat:roughness_texture_invert>\n'
    '      <mat:enable_normal>0</mat:enable_normal>\n'
    '      <mat:enable_occlusion>0</mat:enable_occlusion>\n'
    '      <mat:metallicFactor>1</mat:metallicFactor>\n'
    '      <mat:roughnessFactor>1</mat:roughnessFactor>\n'
    '      <mat:normalMapStyle>1</mat:normalMapStyle>\n'
    '      <mat:normalScale>1</mat:normalScale>\n'
    '      <mat:occlusionStrength>1</mat:occlusionStrength>\n'
    '      <mat:baseColorFactor>4294967295</mat:baseColorFactor>\n'
    '    </mat:pbrMR>\n'
    '  </mat:material>\n'
    '</materialDocument>\n'
)


def xml_material(nome: str, rgb: Tuple[int, int, int], alpha: int = 255) -> bytes:
    """materials/<nome>/material.xml no formato observado em arquivos da SketchUpAPI (docs/FORMATO-SKP.md, seção 7c)."""
    from xml.sax.saxutils import quoteattr
    usa = alpha < 255
    trans = repr(1 - alpha / 255) if usa else "0.5"
    corpo = _XML_MATERIAL % (quoteattr(nome), rgb[0], rgb[1], rgb[2], trans, 1 if usa else 0, 2 if usa else 0)
    return corpo.encode("utf-8")


# Blocos constantes observados em arquivos da SketchUpAPI (docs/FORMATO-SKP.md, seção 7d).
_ATTR_DEFINICAO = bytes.fromhex(
    "dd0580000000b1367a000000b23674000000b3366e000000b03600000000b4361000000053555f446566696e6974696f6e536574"
    "b53642000000b636050000005072696365a43806000000ad3800000000b6360400000053697a65a43806000000ad3800000000"
    "b6360300000055726ca43806000000ad3800000000b7360400000000000000")
_ATTR_INSTANCIA = bytes.fromhex(
    "dd056b000000b13665000000b2365f000000b33659000000b03600000000b4360e00000053555f496e7374616e6365536574"
    "b5362f000000b636050000004f776e6572a43806000000ad3800000000b63606000000537461747573a43806000000ad380000"
    "0000b7360400000000000000")
_T_1B58 = bytes.fromhex(
    "581b30000000591b04000000000000005a1b04000000000000005b1b01000000005c1b01000000005d1b01000000005e1b0100000000")
_T_1585 = bytes.fromhex(
    "8515130100001c250d0100001d2507010000bc3401010000bd341800000000000000000000000000000000000000000000000000f03f"
    "be3418000000000000000000000000000000000000000000000000000040bf34180000000000000000000000000000000000f03f00"
    "00000000000000c034080000000000000000000000c134080000000000000000000000c2340100000001c434080000000000000000"
    "003e40c33408000000000000000000f03fc534080000000000000000000000c6340100000001c7340100000000c8340000000"
    "0c934080000000000000000000000ca340100000000cb3408000000000000000000f03fcc34080000000000000000000000cd3408"
    "0000000000000000000000ce340100000000")


def _cabecalho_attr(id_: int, attr: bytes) -> bytes:
    """Cabeçalho de entidade com dicionário de atributos (definição e instância de componente)."""
    return _rec(0x07D0, _rec(0x05DC, _rec(0x05DE, _id_bytes(id_)) + attr) + _rec(0x07D3, bytes([FLAGS_ARESTA])))


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


def _curvas_validas(t: Topology) -> Dict[int, dict]:
    """Curvas cujas arestas ainda existem e continuam encadeadas (divisão/exclusão invalida a curva)."""
    out = {}
    for cid, c in getattr(t, "curvas", {}).items():
        arestas = c["arestas"]
        if not arestas or any(e not in t.edges for e in arestas):
            continue
        out[cid] = c
    return out


def _carga_curva(c: dict) -> bytes:
    """16 doubles de 0x4c2d: centro, plano (A,B,C,D), X·r, Y·r, raio, ângulo inicial, ângulo final (rad)."""
    cx = c["centro"]
    n = _unit(c["normal"])
    r = float(c["raio"])
    x = _unit(_sub(c["inicio"], cx))
    y = _unit(_cross(n, x))
    varredura = math.radians(c["ang_fim"] - c["ang_ini"])
    return struct.pack("<16d", *cx, *n, -_dot(n, cx), *(r * k for k in x), *(r * k for k in y), r, 0.0, varredura)


def montar_entidades(t: Topology, primeiro_id: int, mid_externo: Optional[Dict[str, int]] = None
                     ) -> Tuple[Dict[str, bytes], int, Tuple[Optional[tuple], Optional[tuple]]]:
    """Registros 0x1389 (vértices), 0x138a (arestas), 0x138b (faces), tabela 0x138e e próximo id livre.

    `mid_externo`: ids de material já alocados para o modelo todo (cena com várias definições); sem ele, os
    materiais usados por esta topologia são alocados aqui e devolvidos em reg["materiais"]."""
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

    curvas = _curvas_validas(t)
    cid_: Dict[int, int] = {}
    for c in sorted(curvas):
        cid_[c] = prox
        prox += 1
    usados = sorted({n for f in t.faces.values() for n in (f.frente, f.verso) if n})
    if mid_externo is None:
        for n in usados:
            if n not in getattr(t, "materiais", {}):
                raise ValueError(f"material {n!r} usado numa face mas não definido em Topology.materiais")
        mid: Dict[str, int] = {}
        for n in usados:
            mid[n] = prox
            prox += 1
    else:
        mid = mid_externo
        usados = []
    curva_da_aresta = {e: cid_[c] for c, d in curvas.items() for e in d["arestas"]}

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
            + _rec(0x0BBA, _id_bytes(vid[b]))
            + (_rec(0x0BBB, _id_bytes(curva_da_aresta[e])) if e in curva_da_aresta else b""),
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
        fc = t.faces[f]
        faces += _rec(
            0x0DAC,
            _cabecalho(fid_[f], FLAGS_FACE, mid[fc.frente] if fc.frente else None)
            + (_rec(0x0DAF, _id_bytes(mid[fc.verso])) if fc.verso else b"")
            + _rec(0x0DAD, struct.pack("<4d", *plano)) + _rec(0x0DAE, corpo),
        )
    reg_materiais = b"".join(
        _rec(0x32C8, _so_id(mid[n]) + _rec(0x32CC, n.encode("utf-8")) + _rec(0x32CA, bytes([0])) + _rec(0x32CB, b""))
        for n in usados
    )
    reg_curvas = b""
    reg_simples = b""
    for c in sorted(curvas):
        d = curvas[c]
        meta = (_so_id(cid_[c]) + _rec(0x4A39, struct.pack("<I", len(d["arestas"]))) + _rec(0x4A3A, bytes([0]))
                + _rec(0x4A3B, _id_bytes(eid[d["arestas"][0]])) + _rec(0x4A3C, _id_bytes(eid[d["arestas"][-1]])))
        if d.get("tipo", "arco") == "simples":
            reg_simples += _rec(0x4A38, meta)
        else:
            reg_curvas += _rec(0x4C2C, _rec(0x4A38, meta) + _rec(0x4C2D, _carga_curva(d)))
    tabela = b"".join(bytes([len(_id_bytes(i))]) + _id_bytes(i) for i in list(eid.values()) + list(fid_.values()))
    pts = list(t.verts.values())
    caixa = None
    if pts:
        caixa = (tuple(min(p[k] for p in pts) for k in range(3)), tuple(max(p[k] for p in pts) for k in range(3)))
    return {"vertices": verts, "arestas": arestas, "faces": faces, "tabela": tabela, "curvas": reg_curvas,
            "simples": reg_simples, "materiais": reg_materiais}, prox, caixa


def _tabela(ids: Sequence[int]) -> bytes:
    return b"".join(bytes([len(_id_bytes(i))]) + _id_bytes(i) for i in ids)


def _ids_da_tabela(tabela: bytes) -> List[int]:
    out, i = [], 0
    while i < len(tabela):
        n = tabela[i]
        out.append(int.from_bytes(tabela[i + 1:i + 1 + n], "little"))
        i += 1 + n
    return out


def _nome_de_grupo(usados: set, base: str = "Group") -> str:
    n, nome = 0, base
    while nome in usados:
        n += 1
        nome = f"{base}{n}"
    usados.add(nome)
    return nome


def _montar_cena(cena, prox: int, mid: Dict[str, int]):
    """Definições (0x157c) e instâncias da cena. Devolve (bytes das definições, instâncias da raiz, prox).

    Instâncias da raiz: (componentes 0x138c, grupos 0x138d, ids) para entrar em 0x1388 da raiz."""
    did: Dict[int, int] = {}
    for d in sorted(k for k in cena.defs if k != 0):
        did[d] = prox
        prox += 1
    iid: Dict[int, int] = {}
    for i in sorted(cena.instancias):
        iid[i] = prox
        prox += 1
    nomes_usados: set = set()
    nome_def: Dict[int, str] = {}
    for d in sorted(did):
        gr = any(x.definicao == d and x.tipo == "grupo" for x in cena.instancias.values())
        nome_def[d] = _nome_de_grupo(nomes_usados) if gr else cena.nomes.get(d, f"Componente{d}")

    def instancias_de(pai: int):
        comp, grup, ids = b"", b"", []
        for i in sorted(x for x, v in cena.instancias.items() if v.pai == pai):
            v = cena.instancias[i]
            if len(v.transformacao) != 16:
                raise ValueError("transformação 4x4 inválida")
            m = v.transformacao
            carga = struct.pack("<13d", m[0], m[4], m[8], m[1], m[5], m[9], m[2], m[6], m[10], m[12], m[13], m[14], 1.0)
            grupo = v.tipo == "grupo"
            corpo = (_cabecalho(iid[i], FLAGS_ARESTA) if grupo else _cabecalho_attr(iid[i], _ATTR_INSTANCIA))
            corpo += _rec(0x1965, v.nome.encode("utf-8") if grupo else b"") + _rec(0x1966, carga)
            corpo += _rec(0x1967, _id_bytes(did[v.definicao])) + _rec(0x1968, uuid.uuid4().bytes)
            if grupo:
                grup += _rec(0x1D4C, _rec(0x1964, corpo))
            else:
                comp += _rec(0x1964, corpo)
            ids.append(iid[i])
        return comp, grup, ids

    # a SketchUpAPI só carrega a instância se a definição dela já veio antes: filhos antes dos pais
    ordem: List[int] = []

    def visita(d: int) -> None:
        if d in ordem:
            return
        for x in sorted(cena.instancias.values(), key=lambda v: v.id):
            if x.pai == d and x.definicao != d:
                visita(x.definicao)
        ordem.append(d)

    for d in sorted(did):
        visita(d)
    defs = b""
    for d in ordem:
        topo = cena.defs[d]
        reg, prox, _ = montar_entidades(topo, prox, mid)
        comp, grup, ids = instancias_de(d)
        grupo = any(x.definicao == d and x.tipo == "grupo" for x in cena.instancias.values())
        corpo = _cabecalho(did[d], FLAGS_ARESTA) if grupo else _cabecalho_attr(did[d], _ATTR_DEFINICAO)
        if topo.verts:
            corpo += _rec(0x1389, reg["vertices"])
        if reg["simples"]:
            corpo += _rec(0x1396, reg["simples"])
        if reg["curvas"]:
            corpo += _rec(0x1397, reg["curvas"])
        if topo.edges:
            corpo += _rec(0x138A, reg["arestas"])
        if topo.faces:
            corpo += _rec(0x138B, reg["faces"])
        if comp:
            corpo += _rec(0x138C, comp)
        if grup:
            corpo += _rec(0x138D, grup)
        corpo += _rec(0x139E, b"") + _rec(0x138E, reg["tabela"] + _tabela(ids))
        corpo += _rec(0x139B, _rec(0x639F, _rec(0x63A0, b""))) + _rec(0x139F, bytes([0]))
        cauda = (_rec(0x157D, uuid.uuid4().bytes) + _rec(0x157E, nome_def[d].encode("utf-8"))
                 + _rec(0x157F, b"Group" if grupo else b"") + _rec(0x1580, b"") + _rec(0x1582, bytes([0]))
                 + _rec(0x1583, struct.pack("<I", 1 if grupo else 0)) + _rec(0x1581, struct.pack("<I", int(time.time())))
                 + _T_1B58 + _T_1585)
        defs += _rec(0x157C, _rec(0x1388, corpo) + cauda)
    return defs, instancias_de(0), prox


def _com_definicoes(dat: bytes, rec: Tuple[int, int, int], novas: bytes) -> bytes:
    """Acrescenta registros 0x157c em 0x01f9 > 0x1770 > 0x1771 (lista de definições do modelo)."""
    a, l, p = rec
    n1 = _parse(dat, p + 6, p + 6 + l)
    saida = b""
    achou = False
    for t, ll, q in n1:
        if t != 0x1770:
            saida += dat[q:q + 6 + ll]
            continue
        n2 = _parse(dat, q + 6, q + 6 + ll)
        interno = b""
        for t2, l2, q2 in n2:
            if t2 == 0x1771:
                interno += _rec(0x1771, dat[q2 + 6:q2 + 6 + l2] + novas)
                achou = True
            else:
                interno += dat[q2:q2 + 6 + l2]
        saida += _rec(0x1770, interno)
    if not achou:
        raise ValueError("estrutura inesperada em 0x01f9 (esperado 0x1770 > 0x1771)")
    return _rec(0x01F9, saida)


MODELO_VAZIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "modelos", "base_vazia.skp")


def _base_vazia(destino: str) -> None:
    """Modelo vazio: a cópia guardada em core/modelos (salva pela SketchUpAPI, sem dado de ninguém) ou,
    se ela sumir, um modelo novo salvo pela SketchUpAPI (Python 3.12)."""
    if os.path.exists(MODELO_VAZIO):
        shutil.copyfile(MODELO_VAZIO, destino)
        return
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


def _com_materiais(dat: bytes, rec: Tuple[int, int, int], novos: bytes) -> bytes:
    """Acrescenta registros 0x32c8 em 0x01f7 > 0x30d4 > 0x30d5 (lista de materiais do modelo)."""
    a, l, p = rec
    nivel1 = _parse(dat, p + 6, p + 6 + l)
    if len(nivel1) != 1 or nivel1[0][0] != 0x30D4:
        raise ValueError("estrutura inesperada em 0x01f7 (esperado 0x30d4)")
    _, l2, p2 = nivel1[0]
    nivel2 = _parse(dat, p2 + 6, p2 + 6 + l2)
    if len(nivel2) != 1 or nivel2[0][0] != 0x30D5:
        raise ValueError("estrutura inesperada em 0x30d4 (esperado 0x30d5)")
    _, l3, p3 = nivel2[0]
    return _rec(0x01F7, _rec(0x30D4, _rec(0x30D5, dat[p3 + 6:p3 + 6 + l3] + novos)))


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
    return _escrever(t, destino, base, None)


def gravar_cena(cena, destino: str, base: Optional[str] = None) -> Dict[str, int]:
    """Grava a cena inteira (raiz + definições + grupos e componentes com transformação)."""
    return _escrever(cena.defs[0], destino, base, cena)


def _escrever(t: Topology, destino: str, base: Optional[str], cena) -> Dict[str, int]:
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
        with zipfile.ZipFile(base) as zin:  # lê tudo e solta o arquivo (no Windows ele travaria a limpeza em caso de erro)
            entradas = [(info, zin.read(info.filename)) for info in zin.infolist()]
        dat = next(c for i, c in entradas if i.filename == "model.dat")

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
        mid_global: Optional[Dict[str, int]] = None
        todas = [t] if cena is None else [cena.defs[k] for k in sorted(cena.defs)]
        if cena is not None:
            definidos: Dict[str, dict] = {}
            for tp in todas:
                definidos.update(getattr(tp, "materiais", {}))
            nomes = sorted({n for tp in todas for f in tp.faces.values() for n in (f.frente, f.verso) if n})
            for n in nomes:
                if n not in definidos:
                    raise ValueError(f"material {n!r} usado numa face mas não definido")
            mid_global = {}
            primeiro_geo = primeiro
            for n in nomes:
                mid_global[n] = primeiro_geo
                primeiro_geo += 1
            reg, prox, caixa = montar_entidades(t, primeiro_geo, mid_global)
            reg["materiais"] = b"".join(
                _rec(0x32C8, _so_id(mid_global[n]) + _rec(0x32CC, n.encode("utf-8")) + _rec(0x32CA, bytes([0])) + _rec(0x32CB, b""))
                for n in nomes)
            defs_bytes, (inst_comp, inst_grup, inst_ids), prox = _montar_cena(cena, prox, mid_global)
            todos_materiais = definidos
        else:
            reg, prox, caixa = montar_entidades(t, primeiro)
            defs_bytes, inst_comp, inst_grup, inst_ids = b"", b"", b"", []
            todos_materiais = getattr(t, "materiais", {})

        novas = [(a, dat[p:p + 6 + l]) for a, l, p in sub]
        # ordem observada em r10: 07d0, 1389, 138a, 138b, 139e, 138e, 139b, 139f, 13a0
        corpo = b""
        geometria = b""
        if t.verts:
            geometria += _rec(0x1389, reg["vertices"])
        if reg["simples"]:
            geometria += _rec(0x1396, reg["simples"])
        if reg["curvas"]:
            geometria += _rec(0x1397, reg["curvas"])
        if t.edges:
            geometria += _rec(0x138A, reg["arestas"])
        if t.faces:
            geometria += _rec(0x138B, reg["faces"])
        if inst_comp:
            geometria += _rec(0x138C, inst_comp)
        if inst_grup:
            geometria += _rec(0x138D, inst_grup)
        for a, bruto in novas:
            if a == 0x139B and (t.edges or t.faces or inst_ids):
                corpo += _rec(0x138E, reg["tabela"] + _tabela(inst_ids))
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
            elif a == 0x01F9 and defs_bytes:
                externo += _com_definicoes(dat, (a, l, p), defs_bytes)
            elif a == 0x01F7 and reg["materiais"]:
                externo += _com_materiais(dat, (a, l, p), reg["materiais"])
            else:
                externo += dat[p:p + 6 + l]
        novo_dat = _rec(0x01F4, externo)

        usados = {n for tp in todas for f in tp.faces.values() for n in (f.frente, f.verso) if n}
        inseridos = not usados
        zip_tmp = os.path.join(tmp, "novo.zip")
        with zipfile.ZipFile(zip_tmp, "w", allowZip64=True) as zout:
            for info, conteudo in entradas:
                if info.filename == "model.dat":
                    zi = zipfile.ZipInfo("model.dat", date_time=info.date_time)
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zout.writestr(zi, novo_dat)
                else:
                    if not inseridos and info.filename.startswith("materials/"):
                        for nome, m in sorted(todos_materiais.items()):
                            if nome in usados:
                                zout.writestr(f"materials/{nome_seguro(nome)}/material.xml",
                                              xml_material(nome, tuple(m["rgb"]), m.get("alpha", 255)),
                                              compress_type=zipfile.ZIP_DEFLATED)
                        inseridos = True
                    zout.writestr(info, conteudo, compress_type=zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(zip_tmp) as zchk:
            integ = valor_integridade([i.CRC for i in zchk.infolist()])
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        with open(destino, "wb") as out, open(zip_tmp, "rb") as zf:
            out.write(prefixo[:-4] + struct.pack("<I", integ))
            shutil.copyfileobj(zf, out)
    return {"vertices": len(t.verts), "arestas": len(t.edges), "faces": len(t.faces), "proximo_id": prox,
            "bytes": os.path.getsize(destino),
            "definicoes": 0 if cena is None else len(cena.defs) - 1,
            "instancias": 0 if cena is None else len(cena.instancias)}
