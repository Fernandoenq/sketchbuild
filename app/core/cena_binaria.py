"""
Cena 3D em binario compacto (04/11/2026, otimizacao parte 1).

O DTO da cena ia como JSON: cada ponto repetido 3x por triangulo e escrito
como texto (o projeto com o Scandere dava 221 MB). Aqui:
- pontos iguais (mesma posicao e mesma normal) viram um so, e os indices sao
  remapeados -- a ordem dos triangulos nao muda, entao `face_ranges`
  (pintura por face, cores) continuam valendo;
- posicoes em Float32, normais em Int8 (normalizadas), indices em Uint16/Uint32.

Formato: b"SKB1" + uint32 (tamanho do cabecalho) + cabecalho JSON (o DTO sem
os arrays; cada definicao ganha "bin": {v, n, i: [inicio, quantidade]}) +
preenchimento ate multiplo de 4 + os blocos binarios.

So responde assim quando o navegador pede (cabecalho "X-Cena: bin"); sem
isso, segue o JSON de sempre (rotas do Fernando, testes).
"""

from __future__ import annotations

import json
import struct

import numpy as np
from fastapi import Request
from fastapi.responses import Response

TIPO = "application/x-sketchbuild-cena"


def quer_binario(request: Request) -> bool:
    return request.headers.get("x-cena") == "bin"


def _compactar(vertices, normals, indices):
    v = np.asarray(vertices, dtype=np.float32).reshape(-1, 3)
    n = np.asarray(normals, dtype=np.float32).reshape(-1, 3) if len(normals) == len(vertices) else None
    idx = np.asarray(indices, dtype=np.int64)
    if len(v) == 0:
        return v, n, idx.astype(np.uint32)
    # chave = posicao (1/1000 de polegada) + normal (1/1000)
    chave = np.round(v * 1000).astype(np.int64)
    if n is not None:
        chave = np.hstack([chave, np.round(n * 1000).astype(np.int64)])
    _, primeiro, inverso = np.unique(chave, axis=0, return_index=True, return_inverse=True)
    v2 = v[primeiro]
    n2 = n[primeiro] if n is not None else None
    idx2 = inverso.reshape(-1)[idx]
    return v2, n2, idx2.astype(np.uint16 if len(v2) < 65536 else np.uint32)


def _json_numpy(x):
    """Campos do motor que chegam como numpy (transformacao, caixa...) viram lista/numero."""
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    raise TypeError(f"{type(x).__name__} nao vira JSON")


def empacotar(dto: dict, extra: dict | None = None) -> bytes:
    blocos: list[bytes] = []
    pos = 0

    def guarda(arr: np.ndarray) -> list:
        nonlocal pos
        dados = arr.tobytes()
        inicio = pos
        blocos.append(dados)
        pos += len(dados)
        if pos % 4:  # alinhamento pros Float32Array/Uint32Array do navegador
            falta = 4 - pos % 4
            blocos.append(b"\0" * falta)
            pos += falta
        return [inicio, int(arr.size)]

    cabecalho = {k: v for k, v in dto.items() if k != "definitions"}
    if extra:
        cabecalho["extra"] = extra
    paleta: list[dict] = []
    paleta_idx: dict = {}
    defs = []
    for d in dto.get("definitions", []):
        vert = d.get("vertices")
        vert = [] if vert is None else vert
        if not len(vert):
            defs.append({k: val for k, val in d.items() if k not in ("_fr", "_compacto")})
            continue
        if d.get("_compacto"):  # veio do cache em disco ja sem pontos repetidos
            v = np.asarray(vert, dtype=np.float32).reshape(-1, 3)
            n = np.asarray(d["normals"], dtype=np.float32).reshape(-1, 3)
            i = np.asarray(d["indices"], dtype=np.uint16 if len(v) < 65536 else np.uint32)
        else:
            nor, ind = d.get("normals"), d.get("indices")
            v, n, i = _compactar(vert, [] if nor is None else nor, [] if ind is None else ind)
        nova = {k: val for k, val in d.items() if k not in ("vertices", "normals", "indices", "face_ranges", "_fr", "_compacto")}
        nova["bin"] = {"v": guarda(v), "i": guarda(i) + [8 * i.itemsize]}
        if n is not None:
            # normal em 1 byte por eixo (-127..127): diferenca invisivel, 4x menor
            nova["bin"]["n8"] = guarda(np.clip(np.round(n * 127), -127, 127).astype(np.int8))
        faces = d.get("face_ranges") or []
        fr = d.get("_fr")
        if fr is not None and len(fr["ini"]):
            # malha vinda do cache em disco: arrays prontos, sem montar lista
            cores, inv = np.unique(fr["cor"], axis=0, return_inverse=True)
            mapa = []
            for c in cores.tolist():
                chave = (tuple(c) if c[0] >= 0 else None, None)
                if chave not in paleta_idx:
                    paleta_idx[chave] = len(paleta)
                    paleta.append({"color": list(chave[0]) if chave[0] else None, "material_name": None})
                mapa.append(paleta_idx[chave])
            ids = fr["ids"]
            nova["bin"]["fs"] = guarda(fr["ini"].astype(np.uint32))
            nova["bin"]["fc"] = guarda(fr["qtd"].astype(np.uint32))
            nova["bin"]["fk"] = guarda(np.asarray(mapa, dtype=np.uint32)[inv.reshape(-1)])
            nova["bin"]["fl"] = guarda((ids & 0xFFFFFFFF).astype(np.uint32))
            nova["bin"]["fh"] = guarda((ids >> np.uint64(32)).astype(np.uint32))
        elif faces:
            # Lista de faces (pode ter centenas de milhares): inicio/qtd de
            # triangulos, cor (indice na paleta) e o id da face (ponteiro).
            chaves = [(tuple(f["color"]) if f.get("color") else None, f.get("material_name")) for f in faces]
            for c in chaves:
                if c not in paleta_idx:
                    paleta_idx[c] = len(paleta)
                    paleta.append({"color": list(c[0]) if c[0] else None, "material_name": c[1]})
            ids = np.array([int(f["face_id"][5:], 16) for f in faces], dtype=np.uint64)
            nova["bin"]["fs"] = guarda(np.array([f["triangle_start"] for f in faces], dtype=np.uint32))
            nova["bin"]["fc"] = guarda(np.array([f["triangle_count"] for f in faces], dtype=np.uint32))
            nova["bin"]["fk"] = guarda(np.array([paleta_idx[c] for c in chaves], dtype=np.uint32))
            nova["bin"]["fl"] = guarda((ids & 0xFFFFFFFF).astype(np.uint32))
            nova["bin"]["fh"] = guarda((ids >> np.uint64(32)).astype(np.uint32))
        defs.append(nova)
    cabecalho["definitions"] = defs
    cabecalho["paleta"] = paleta
    texto = json.dumps(cabecalho, separators=(",", ":"), default=_json_numpy).encode("utf-8")
    texto += b" " * ((4 - (8 + len(texto)) % 4) % 4)
    return b"SKB1" + struct.pack("<I", len(texto)) + texto + b"".join(blocos)


def responder_cena(request: Request, dto, extra: dict | None = None, normal=None):
    """Devolve a cena em binario se o navegador pediu; senao, `normal` (ou o DTO)."""
    if not quer_binario(request) or not isinstance(dto, dict):
        return _listas(dto if normal is None else normal)
    dados = empacotar(dto, extra)
    # Fica guardado na sessao: o F5 seguinte devolve isso sem refazer nada.
    if not any(d.get("reused") for d in dto.get("definitions", [])):
        try:
            from app.repositories.skp_engine_repository import SkpEngineRepository
            repo = SkpEngineRepository()
            if hasattr(repo, "guardar_pacote"):
                repo.guardar_pacote(dados)
        except Exception:
            pass
    return Response(dados, media_type=TIPO, headers={"Cache-Control": "no-store"})


def _listas(x):
    """Resposta em JSON: arrays numpy (motor D) viram listas."""
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, dict):
        return {k: _listas(v) for k, v in x.items() if k not in ("_compacto", "_fr")}
    if isinstance(x, (list, tuple)):
        return [_listas(v) for v in x]
    return x
