"""
Cache em disco da malha (triangulos) de cada definicao grande (04/11/2026,
otimizacao parte 2).

Triangular as faces e o que mais pesa ao abrir um projeto (o Scandere: 448
mil faces, ~14 s). A malha de uma peca nao muda entre um projeto e outro,
entao fica guardada em <SKETCHBUILD_DATA>/cache_malhas/<chave>.npz e, na
proxima vez, so as faces sao listadas (rapido) pra refazer os ids da pintura
por face.

Chave: nome da definicao + numero de faces + os pontos da primeira e da
ultima face (uma peca editada muda a chave e e refeita).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

PASTA = Path(os.getenv("SKETCHBUILD_DATA", Path(__file__).resolve().parents[1] / "app" / "data")) / "cache_malhas"
MINIMO_FACES = 2000  # peca pequena triangula rapido: nao vale gravar


def chave(api, nome: str, faces: list) -> str:
    h = hashlib.sha1(f"v2|{nome}|{len(faces)}".encode("utf-8"))  # v2: malha ja compactada
    for face in (faces[0], faces[-1]):
        malha = api.build_face_mesh(face)
        h.update(np.asarray(malha["vertices"], dtype=np.float32).tobytes())
    return h.hexdigest()


def ler(k: str, faces: list) -> tuple[dict, dict] | None:
    """Devolve (malha no formato do _build_definition_mesh, registro de faces)."""
    arq = PASTA / f"{k}.npz"
    if not arq.is_file():
        return None
    try:
        z = np.load(arq)
        pos, ini, qtd, cor = z["pos"], z["ini"], z["qtd"], z["cor"]
        registro: dict = {}
        ranges = []
        for p, a, b, c in zip(pos.tolist(), ini.tolist(), qtd.tolist(), cor.tolist()):
            face = faces[p]
            fid = f"face_{face.ptr or 0:x}"
            registro[fid] = face
            ranges.append({"face_id": fid, "triangle_start": a, "triangle_count": b, "color": None if c[0] < 0 else c})
        malha = {
            "vertices": z["v"].tolist(),
            "normals": z["n"].tolist(),
            "indices": z["i"].tolist(),
            "face_ranges": ranges,
            # atalhos pro empacotador binario (app/core/cena_binaria.py)
            "_compacto": True,
            "_fr": {
                "ini": ini, "qtd": qtd, "cor": cor,
                "ids": np.array([faces[p].ptr or 0 for p in pos.tolist()], dtype=np.uint64),
            },
        }
        return malha, registro
    except (OSError, ValueError, KeyError, IndexError):
        return None


def gravar(k: str, malha: dict, faces: list) -> None:
    """Melhor esforco: falha aqui nunca quebra a abertura do projeto."""
    try:
        posicao = {f"face_{f.ptr or 0:x}": i for i, f in enumerate(faces)}
        fr = malha["face_ranges"]
        PASTA.mkdir(parents=True, exist_ok=True)
        tmp = PASTA / f"{k}.tmp.npz"
        # Junta os pontos repetidos AQUI (uma vez so): o Scandere cai de 1,2 M
        # pra ~300 mil pontos; a ordem dos triangulos nao muda.
        from app.core.cena_binaria import _compactar
        v, n, i = _compactar(malha["vertices"], malha["normals"], malha["indices"])
        if n is None:
            n = np.zeros_like(v)
        np.savez(
            tmp,
            v=v,
            n=n,
            i=i.astype(np.uint32),
            pos=np.array([posicao[r["face_id"]] for r in fr], dtype=np.uint32),
            ini=np.array([r["triangle_start"] for r in fr], dtype=np.uint32),
            qtd=np.array([r["triangle_count"] for r in fr], dtype=np.uint32),
            cor=np.array([r["color"] if r.get("color") else [-1, -1, -1] for r in fr], dtype=np.int16).reshape(-1, 3),
        )
        os.replace(tmp, PASTA / f"{k}.npz")
    except (OSError, ValueError, KeyError):
        pass
