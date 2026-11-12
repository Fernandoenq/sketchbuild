"""Sessão de desenho em memória (F2): um núcleo de topologia por execução do backend."""
from __future__ import annotations

import math
import base64
import binascii
import io
import os

from core.skp_topology_writer import gravar_cena
from core.topology import Topology
from core.topology.cena import Cena
from core.topology.historico import Historico
from core.topology.intersect import intersectar
from core.topology.sweep import siga_me
from core.topology.draw import desenhar
from core.topology.edit import escalar, mover, offset, rotacionar, vertices_da_selecao
from core.topology.material import definir_material, matriz_uv, pintar, posicionar_textura
from core.topology.pushpull import empurrar
from core.topology import cotas, guias, soften
from core.topology import texto as _texto
from core.topology.tag import atribuir, atribuir_arestas, definir_tag

MAX_TEXTURA = 8 * 1024 * 1024  # bytes da imagem
_ASSINATURA_PNG = bytes([0x89]) + b"PNG" + bytes([13, 10, 26, 10])
_ASSINATURA_JPEG = bytes([0xFF, 0xD8, 0xFF])


def _textura(b64: str, nome: str | None, escala, rgb) -> tuple[dict, tuple[int, int, int]]:
    """Decodifica a imagem enviada. Devolve (textura para o gravador, cor média). A cor média vem do Pillow quando
    existe; sem ele usa `rgb` (ou cinza)."""
    try:
        dados = base64.b64decode(b64, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("textura: base64 inválido") from e
    if not dados or len(dados) > MAX_TEXTURA:
        raise ValueError(f"textura: tamanho inválido (máximo {MAX_TEXTURA // (1024 * 1024)} MB)")
    if not (dados.startswith(_ASSINATURA_PNG) or dados.startswith(_ASSINATURA_JPEG)):
        raise ValueError("textura: só PNG ou JPEG")
    media = tuple(rgb) if rgb is not None else (128, 128, 128)
    try:
        from PIL import Image
        with Image.open(io.BytesIO(dados)) as im:
            media = tuple(int(c) for c in im.convert("RGB").resize((1, 1), Image.BOX).getpixel((0, 0)))
    except ImportError:
        pass
    except Exception as e:  # imagem corrompida
        raise ValueError("textura: imagem ilegível") from e
    ext = ".png" if dados.startswith(_ASSINATURA_PNG) else ".jpg"
    arq = os.path.basename((nome or "").replace(chr(92), "/")) or ("textura" + ext)
    if not arq.lower().endswith((".png", ".jpg", ".jpeg")):
        arq += ext
    return {"nome": arq, "bytes": dados, "escala": (float(escala[0]), float(escala[1]))}, media


_CENA = Cena()
_HIST = Historico(_CENA)


def _normal_da_cota(d) -> tuple:
    """Normal do plano da cota: o `z` do mundo menos a parte paralela à direção (aresta vertical: usa o `y`)."""
    n = math.sqrt(sum(c * c for c in d))
    u = tuple(c / n for c in d)
    for base in ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)):
        k = sum(base[i] * u[i] for i in range(3))
        v = tuple(base[i] - k * u[i] for i in range(3))
        if math.sqrt(sum(c * c for c in v)) > 1e-6:
            return v
    raise ValueError("cota: direção inválida")


def _topo() -> Topology:
    return _CENA.topo

_OBRIGATORIOS = {
    "linha": ("pontos",),
    "retangulo": ("p0", "p1"),
    "circulo": ("centro", "raio"),
    "poligono": ("centro", "raio"),
    "arco": ("centro", "raio", "ang_ini", "ang_fim"),
    "mao_livre": ("pontos",),
}


def _chave(delta: dict) -> dict:
    """JSON só aceita chave de texto; ids do núcleo são inteiros."""
    out = {}
    for k, v in delta.items():
        out[k] = {
            "added": {str(i): _lista(x) for i, x in v["added"].items()},
            "changed": {str(i): _lista(x) for i, x in v["changed"].items()},
            "removed": list(v["removed"]),
        }
    return out


def _lista(x):
    if isinstance(x, tuple):
        return [_lista(i) for i in x]
    return x


class DrawRepository:
    def desenhar(self, ferramenta: str, **params) -> dict:
        faltam = [c for c in _OBRIGATORIOS[ferramenta] if params.get(c) is None]
        if faltam:
            raise ValueError(f"{ferramenta}: faltam {', '.join(faltam)}")
        params = {k: v for k, v in params.items() if v is not None}
        res = _chave(_HIST.executar("desenhar:" + ferramenta, params, lambda: desenhar(_topo(), ferramenta, **params)))
        res["counts"] = _topo().counts()
        return res

    def empurrar(self, face_id: int, distancia: float, criar_nova: bool = False) -> dict:
        res = _chave(_HIST.executar("pushpull", {"face": face_id, "distancia": distancia}, lambda: empurrar(_topo(), face_id, distancia, criar_nova)))
        res["counts"] = _topo().counts()
        return res

    def editar(self, operacao: str, vertices, arestas, faces, vetor=None, angulo=None,
               eixo=(0.0, 0.0, 1.0), centro=None, fator=None, fatores=None) -> dict:
        ids = vertices_da_selecao(_topo(), vertices, arestas, faces)
        if operacao == "mover":
            if vetor is None:
                raise ValueError("mover: falta o vetor")
            delta = _HIST.executar("mover", {"vetor": vetor}, lambda: mover(_topo(), ids, vetor))
        elif operacao == "rotacionar":
            if angulo is None:
                raise ValueError("rotacionar: falta o angulo")
            delta = _HIST.executar("rotacionar", {"angulo": angulo}, lambda: rotacionar(_topo(), ids, angulo, eixo, centro))
        else:
            if fator is None and fatores is None:
                raise ValueError("escalar: falta o fator")
            delta = _HIST.executar("escalar", {"fator": fator}, lambda: escalar(_topo(), ids, fatores if fatores is not None else fator, centro))
        res = _chave(delta)
        res["counts"] = _topo().counts()
        return res

    def offset(self, face_id: int, distancia: float) -> dict:
        res = _chave(_HIST.executar("offset", {"face": face_id, "distancia": distancia}, lambda: offset(_topo(), face_id, distancia)))
        res["counts"] = _topo().counts()
        return res

    def siga_me(self, face_id: int, arestas: list[int]) -> dict:
        res = _chave(_HIST.executar("followme", {"face": face_id}, lambda: siga_me(_topo(), face_id, arestas)))
        res["counts"] = _topo().counts()
        return res

    def intersectar(self, faces) -> dict:
        res = _chave(_HIST.executar("intersect", {}, lambda: intersectar(_topo(), faces)))
        res["counts"] = _topo().counts()
        return res

    def agrupar(self, tipo: str, faces, arestas, nome) -> dict:
        criar = _CENA.criar_grupo if tipo == "grupo" else _CENA.criar_componente
        iid = _HIST.executar(tipo, {"nome": nome}, lambda: criar(faces, arestas, nome))
        return {"instancia": iid, **self.cena()}

    def instanciar(self, instancia: int, transformacao) -> dict:
        iid = _HIST.executar("instanciar", {"instancia": instancia}, lambda: _CENA.instanciar(instancia, transformacao))
        return {"instancia": iid, **self.cena()}

    def explodir(self, instancia: int) -> dict:
        _HIST.executar("explodir", {"instancia": instancia}, lambda: _CENA.explodir(instancia))
        return self.cena()

    def entrar(self, instancia: int) -> dict:
        _CENA.entrar(instancia)
        return self.cena()

    def sair(self) -> dict:
        _CENA.sair()
        return self.cena()

    def cena(self) -> dict:
        r = _CENA.resumo()
        return {
            "ativa": r["ativa"],
            "caminho": r["caminho"],
            "definicoes": {str(k): v for k, v in r["definicoes"].items()},
            "instancias": {str(k): v for k, v in r["instancias"].items()},
        }

    def salvar(self, caminho: str, sobrescrever: bool = False) -> dict:
        """Grava o desenho (raiz, grupos e componentes) num .skp novo. Nunca sobrescreve sem confirmacao."""
        if not caminho.lower().endswith(".skp"):
            raise ValueError("o caminho precisa terminar em .skp")
        if os.path.exists(caminho) and not sobrescrever:
            raise FileExistsError(caminho)
        return {"path": caminho, **self._relatorio(gravar_cena(_CENA, caminho))}

    @staticmethod
    def _relatorio(r: dict) -> dict:
        return {"vertices": r["vertices"], "arestas": r["arestas"], "faces": r["faces"], "bytes": r["bytes"]}

    def pintar(self, faces, material=None, rgb=None, alpha=255, verso=False, limpar=False,
               textura_base64=None, textura_nome=None, escala=(1.0, 1.0)) -> dict:
        if not material and not limpar:
            raise ValueError("pintar: informe o material (ou limpar)")

        def acao():
            if textura_base64:
                if not material:
                    raise ValueError("pintar: textura sem nome de material")
                tex, media = _textura(textura_base64, textura_nome, escala, rgb)
                definir_material(_topo(), material, media, alpha, tex)
            elif rgb is not None:
                if not material:
                    raise ValueError("pintar: rgb sem nome de material")
                definir_material(_topo(), material, rgb, alpha)
            return pintar(_topo(), faces,
                          frente=None if verso else material, verso=material if verso else None,
                          limpar_frente=limpar and not verso, limpar_verso=limpar and verso)

        res = _HIST.executar("pintar", {"faces": list(faces), "material": material}, acao)
        return {"pintadas": {str(k): list(v) for k, v in res.items()},
                "materiais": {n: {"rgb": list(m["rgb"]), "alpha": m["alpha"]} for n, m in _topo().materiais.items()}}

    def marcar(self, nome=None, visivel=None, faces=(), arestas=(), limpar=False) -> dict:
        if limpar and nome:
            raise ValueError("tag: `limpar` nao combina com `nome` (limpar tira da tag)")
        if not limpar and not nome:
            raise ValueError("tag: informe o nome (ou limpar)")

        def acao():
            if nome and (visivel is not None or nome not in _topo().tags):
                definir_tag(_topo(), nome, True if visivel is None else visivel)
            alvo = None if limpar else nome
            if faces:
                atribuir(_topo(), faces, alvo)
            if arestas:
                atribuir_arestas(_topo(), arestas, alvo)
            return {}

        _HIST.executar("tag", {"nome": nome, "faces": list(faces), "arestas": list(arestas)}, acao)
        return self.estado()

    def guia(self, tipo, p=None, alvo=None, direcao=None, id=None) -> dict:
        def acao():
            if tipo == "apagar":
                if id is None:
                    raise ValueError("guia: informe o id a apagar")
                guias.apagar(_topo(), id)
            elif p is None:
                raise ValueError("guia: informe p")
            elif tipo == "ponto":
                guias.guia_ponto(_topo(), p)
            elif tipo == "linha":
                guias.guia_linha(_topo(), p, alvo, direcao)
            else:
                if direcao is None:
                    raise ValueError("plano de secao: informe a normal em `direcao`")
                guias.plano_secao(_topo(), direcao, p)
            return {}

        _HIST.executar("guia", {"tipo": tipo}, acao)
        return self.estado()

    def nota(self, tipo, texto=None, p=None, fim=None, normal=None, eixo_x=None, desloc=(0.0, 0.0), seta=0,
             tipo_chamada=0, vetor=None, id=None, cor=None, fonte_nova=None, alinhamento_h=None, tela=(0.5, 0.5), texto_3d=False, fonte=None) -> dict:
        def acao():
            if tipo == "apagar":
                if id is None:
                    raise ValueError("nota: informe o id a apagar")
                if id in _topo().textos:
                    _texto.apagar_texto(_topo(), id)
                else:
                    cotas.apagar_cota(_topo(), id)
            elif tipo == "texto":
                if p is None or not texto:
                    raise ValueError("texto: informe o texto e o ponto p")
                _texto.texto_livre(_topo(), texto, p, tipo_chamada, vetor, seta, 2 if fonte is None else fonte, cor=cor, fonte_nova=fonte_nova, tela=tela)
            else:
                if p is None or fim is None:
                    raise ValueError("cota: informe o ponto inicial p e o ponto final fim")
                direcao = tuple(fim[i] - p[i] for i in range(3))
                n = normal or _normal_da_cota(direcao)
                cotas.cota_linear(_topo(), p, fim, n, eixo_x or direcao, texto or "", seta, desloc, alinhamento_h=alinhamento_h, texto_3d=texto_3d, fonte=fonte)
            return {}

        _HIST.executar("nota", {"tipo": tipo}, acao)
        return self.estado()

    def comportamento(self, definicao=None, **flags) -> dict:
        alvo = _CENA.ativa if definicao is None else definicao
        _HIST.executar("comportamento", {"definicao": alvo}, lambda: _CENA.definir_comportamento(alvo, **flags))
        return self.cena()

    def posicionar(self, faces, tamanho=None, u0=0.0, v0=0.0, graus=0.0, limpar=False) -> dict:
        if not limpar and tamanho is None:
            raise ValueError("posicionar: informe o tamanho (ou limpar)")

        def acao():
            posicionar_textura(_topo(), faces, None if limpar else matriz_uv(tamanho, u0, v0, graus))
            return {}

        _HIST.executar("posicionar", {"faces": list(faces)}, acao)
        return self.estado()

    def suavizar(self, arestas=(), angulo=None, suave=True, lisa=True, limpar=False) -> dict:
        if not arestas and angulo is None:
            raise ValueError("suavizar: informe arestas ou angulo")
        if limpar and angulo is not None:
            raise ValueError("suavizar: limpar nao combina com angulo")

        def acao():
            if limpar:
                soften.limpar(_topo(), arestas)
            elif angulo is not None:
                soften.por_angulo(_topo(), angulo, arestas or None)
            else:
                soften.definir(_topo(), arestas, suave, lisa)
            return {}

        _HIST.executar("suavizar", {"arestas": list(arestas), "angulo": angulo}, acao)
        return self.estado()

    def adicionar_cena(self, nome, descricao="", animar=True, olho=None, alvo=None, cima=(0.0, 0.0, 1.0)) -> dict:
        if (olho is None) != (alvo is None):
            raise ValueError("cena: informe olho e alvo juntos")
        camera = None if olho is None else {"olho": olho, "alvo": alvo, "cima": cima}
        def acao():
            _CENA.adicionar_cena(nome, descricao, animar, camera)
            return {}

        _HIST.executar("cena", {"nome": nome}, acao)
        return self.estado()

    def desfazer(self) -> dict:
        _HIST.desfazer()
        return self.estado()

    def refazer(self) -> dict:
        _HIST.refazer()
        return self.estado()

    def historico(self) -> dict:
        return _HIST.resumo()

    def estado(self) -> dict:
        return {
            "vertices": {str(i): list(p) for i, p in _topo().verts.items()},
            "edges": {str(i): list(e) for i, e in _topo().edges.items()},
            "faces": {str(i): {"outer": f.outer, "holes": f.holes, "normal": list(f.normal)}
                      for i, f in _topo().faces.items()},
            "pintura": {str(i): [f.frente, f.verso] for i, f in _topo().faces.items() if f.frente or f.verso},
            "materiais": {n: {"rgb": list(m["rgb"]), "alpha": m["alpha"]} for n, m in _topo().materiais.items()},
            "tags": {n: dict(m) for n, m in _topo().tags.items()},
            "tag_faces": {str(i): f.tag for i, f in _topo().faces.items() if f.tag},
            "tag_arestas": {str(e): n for e, n in _topo().etags.items()},
            "suaves": {str(e): b for e, b in _topo().eflags.items()},
            "guias": {str(i): {k: (list(v) if isinstance(v, tuple) else v) for k, v in g.items()} for i, g in _topo().guias.items()},
            "secoes": {str(i): list(pl) for i, pl in _topo().secoes.items()},
            "textos": {str(i): {k: (list(v) if isinstance(v, tuple) else v) for k, v in x.items()} for i, x in _topo().textos.items()},
            "cotas": {str(i): {k: (list(v) if isinstance(v, tuple) else v) for k, v in x.items()} for i, x in _topo().cotas.items()},
            "uv": {str(i): list(f.uv) for i, f in _topo().faces.items() if f.uv},
            "cenas": [{"nome": c["nome"], "descricao": c["descricao"], "animar": c["animar"], "camera": c["camera"] is not None}
                      for c in _CENA.cenas],
            "counts": _topo().counts(),
            "historico": {k: v for k, v in _HIST.resumo().items() if k.startswith("pode")},
        }

    def limpar(self) -> None:
        global _CENA, _HIST
        _CENA = Cena()
        _HIST = Historico(_CENA)
