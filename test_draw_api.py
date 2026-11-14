"""F2: camada controller/serviço/repositório do desenho (sem HTTP: httpx não é dependência)."""
import asyncio
import unittest

from fastapi import HTTPException

from app.controllers.draw_controller import DrawController
from app.schemas.draw import DrawRequest, SaveDrawRequest, EditRequest, FollowMeRequest, GroupRequest, InstanceRequest, GroupSolidRequest, IntersectRequest, OffsetRequest, PaintRequest, PushPullRequest, TagRequest, CenaRequest, SoftenRequest, SelecaoRequest, SolidoRequest, GuiaRequest, NotaRequest, PosicionarRequest, ComportamentoRequest


def _tem_pillow():
    try:
        import PIL  # noqa: F401
        return True
    except ImportError:
        return False


def run(c):
    return asyncio.run(c)


class TestDrawController(unittest.TestCase):
    def setUp(self):
        self.c = DrawController()
        run(self.c.limpar())

    def test_retangulo_e_delta(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        self.assertEqual(j.counts, {"vertices": 4, "edges": 4, "faces": 1})
        self.assertEqual(len(j.faces.added), 1)
        self.assertEqual(run(self.c.estado()).counts["faces"], 1)

    def test_circulo_24_lados(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="circulo", centro=(0, 0, 0), raio=50)))
        self.assertEqual(j.counts, {"vertices": 24, "edges": 24, "faces": 1})

    def test_faltando_parametro(self):
        with self.assertRaises(HTTPException) as cm:
            run(self.c.desenhar(DrawRequest(ferramenta="circulo", centro=(0, 0, 0))))
        self.assertEqual(cm.exception.status_code, 422)

    def test_pushpull_cubo(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        r = run(self.c.empurrar(PushPullRequest(face_id=fid, distancia=-50)))
        self.assertEqual(r.counts, {"vertices": 8, "edges": 12, "faces": 6})

    def test_pushpull_invalido(self):
        with self.assertRaises(HTTPException) as cm:
            run(self.c.empurrar(PushPullRequest(face_id=99, distancia=5)))
        self.assertEqual(cm.exception.status_code, 422)

    def test_editar_e_offset(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        r = run(self.c.editar(EditRequest(operacao="mover", faces=[fid], vetor=(5, 0, 0))))
        self.assertEqual(len(r.vertices.changed), 4)
        r = run(self.c.offset(OffsetRequest(face_id=fid, distancia=-10)))
        self.assertEqual(r.counts["faces"], 2)
        with self.assertRaises(HTTPException) as cm:
            run(self.c.editar(EditRequest(operacao="mover", faces=[fid])))
        self.assertEqual(cm.exception.status_code, 422)

    def test_grupo_entrar_sair_explodir(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        g = run(self.c.agrupar(GroupRequest(faces=[fid])))
        self.assertEqual(run(self.c.estado()).counts["faces"], 0)
        run(self.c.entrar(InstanceRequest(instancia=g["instancia"])))
        self.assertEqual(run(self.c.estado()).counts["faces"], 1)
        run(self.c.sair())
        run(self.c.explodir(InstanceRequest(instancia=g["instancia"])))
        self.assertEqual(run(self.c.estado()).counts["faces"], 1)

    def test_combinar_grupos_recusa_o_que_nao_e_solido(self):
        a, b = self._agrupar_quadrado("grupo", 0), self._agrupar_quadrado("grupo", 500)
        with self.assertRaises(HTTPException) as cm:  # dois quadrados soltos não são sólidos
            run(self.c.combinar_grupos(GroupSolidRequest(operacao="uniao", a=a, b=b)))
        self.assertEqual(cm.exception.status_code, 422)
        with self.assertRaises(HTTPException):
            run(self.c.combinar_grupos(GroupSolidRequest(operacao="uniao", a=a, b=999)))
        for op in ("aparar", "dividir"):
            with self.assertRaises(HTTPException) as cm:
                run(self.c.combinar_grupos(GroupSolidRequest(operacao=op, a=a, b=b)))
            self.assertEqual(cm.exception.status_code, 422)

    def _agrupar_quadrado(self, tipo, x0):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(x0, 0, 0), p1=(x0 + 100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        return run(self.c.agrupar(GroupRequest(faces=[fid], tipo=tipo)))["instancia"]

    def test_comportamento_do_componente(self):
        comp = self._agrupar_quadrado("componente", 0)
        run(self.c.entrar(InstanceRequest(instancia=comp)))
        r = run(self.c.comportamento(ComportamentoRequest(face_me=True, snap=2)))
        self.assertEqual(r.definicoes[str(r.ativa)]["comportamento"],
                         {"face_me": True, "corta_abertura": False, "sombra_sol": False, "snap": 2})
        with self.assertRaises(HTTPException):
            run(self.c.comportamento(ComportamentoRequest(definicao=0, face_me=True)))  # raiz
        run(self.c.sair())
        grupo = self._agrupar_quadrado("grupo", 500)
        run(self.c.entrar(InstanceRequest(instancia=grupo)))
        with self.assertRaises(HTTPException):
            run(self.c.comportamento(ComportamentoRequest(face_me=True)))  # grupo não tem comportamento

    def test_salvar_cena_com_grupo(self):
        import os
        import sys
        import tempfile
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        run(self.c.agrupar(GroupRequest(faces=[fid])))
        if sys.version_info[:2] == (3, 12):
            with tempfile.TemporaryDirectory() as tmp:
                r = run(self.c.salvar(SaveDrawRequest(path=os.path.join(tmp, "g.skp"))))
                self.assertEqual((r.faces, r.arestas), (0, 0))  # a geometria esta dentro do grupo, nao na raiz

    def test_intersect_e_followme(self):
        run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        r = run(self.c.intersectar(IntersectRequest()))
        self.assertEqual(r.counts["faces"], 1)
        with self.assertRaises(HTTPException):
            run(self.c.siga_me(FollowMeRequest(face_id=1, arestas=[])))

    def test_desfazer_e_refazer(self):
        run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        self.assertTrue(run(self.c.estado()).historico["pode_desfazer"])
        e = run(self.c.desfazer())
        self.assertEqual(e.counts, {"vertices": 0, "edges": 0, "faces": 0})
        self.assertTrue(e.historico["pode_refazer"])
        e = run(self.c.refazer())
        self.assertEqual(e.counts["faces"], 1)
        with self.assertRaises(HTTPException) as cm:
            run(self.c.refazer())
        self.assertEqual(cm.exception.status_code, 409)
        self.assertEqual(run(self.c.historico())["log"][0]["operacao"], "desenhar:retangulo")

    def test_salvar_desenho(self):
        import os
        import sys
        import tempfile
        run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "d.skp")
            if sys.version_info[:2] == (3, 12):
                r = run(self.c.salvar(SaveDrawRequest(path=p)))
                self.assertEqual((r.faces, r.arestas), (1, 4))
                self.assertTrue(os.path.exists(p))
                with self.assertRaises(HTTPException) as cm:  # nao sobrescreve sem confirmar
                    run(self.c.salvar(SaveDrawRequest(path=p)))
                self.assertEqual(cm.exception.status_code, 409)
            with self.assertRaises(HTTPException) as cm:
                run(self.c.salvar(SaveDrawRequest(path=os.path.join(tmp, "x.txt"))))
            self.assertEqual(cm.exception.status_code, 422)

    def test_pintar_frente_verso_desfazer_e_salvar(self):
        import os
        import sys
        import tempfile
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        r = run(self.c.pintar(PaintRequest(faces=[fid], material="Vermelho", rgb=(255, 0, 0))))
        self.assertEqual(r.pintadas[str(fid)], ["Vermelho", None])
        r = run(self.c.pintar(PaintRequest(faces=[fid], material="Azul", rgb=(0, 0, 255), alpha=128, verso=True)))
        self.assertEqual(r.pintadas[str(fid)], ["Vermelho", "Azul"])
        self.assertEqual(r.materiais["Azul"], {"rgb": [0, 0, 255], "alpha": 128})
        r = run(self.c.pintar(PaintRequest(faces=[fid], limpar=True, verso=True)))
        self.assertEqual(r.pintadas[str(fid)], ["Vermelho", None])
        run(self.c.desfazer())  # volta ao verso azul
        r = run(self.c.pintar(PaintRequest(faces=[fid], material="Azul", verso=True)))
        self.assertEqual(r.pintadas[str(fid)], ["Vermelho", "Azul"])
        if sys.version_info[:2] == (3, 12):
            with tempfile.TemporaryDirectory() as tmp:
                run(self.c.salvar(SaveDrawRequest(path=os.path.join(tmp, "c.skp"))))

    def test_pintar_erros(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(10, 10, 0))))
        fid = int(next(iter(j.faces.added)))
        for body in (PaintRequest(faces=[fid]),  # sem material
                     PaintRequest(faces=[fid], material="Fantasma"),  # nao definido
                     PaintRequest(faces=[999], material="X", rgb=(1, 2, 3)),  # face inexistente
                     PaintRequest(faces=[fid], material="X", rgb=(1, 2, 300))):  # cor invalida
            with self.assertRaises(HTTPException) as cm:
                run(self.c.pintar(body))
            self.assertEqual(cm.exception.status_code, 422)

    def test_rotas_registradas(self):
        from app.main import app
        caminhos = {r.path for r in app.routes}
        self.assertIn("/api/v1/draw", caminhos)
        self.assertIn("/api/v1/draw/state", caminhos)
        self.assertIn("/api/v1/draw/pushpull", caminhos)
        self.assertIn("/api/v1/draw/edit", caminhos)
        self.assertIn("/api/v1/draw/offset", caminhos)
        for r in ("save", "paint", "undo", "redo", "history", "followme", "intersect", "scene", "group", "instance", "explode", "group-solid", "enter", "exit"):
            self.assertIn("/api/v1/draw/" + r, caminhos)

    def _png(self):
        import base64
        import struct
        import zlib
        linhas = b"".join(bytes([0]) + bytes([255, 0, 0]) * 4 for _ in range(4))  # 4x4 todo vermelho

        def bloco(tp, dd):
            return struct.pack(">I", len(dd)) + tp + dd + struct.pack(">I", zlib.crc32(tp + dd) & 0xFFFFFFFF)
        assinatura = bytes([0x89]) + b"PNG" + bytes([13, 10, 26, 10])
        png = (assinatura + bloco(b"IHDR", struct.pack(">IIBBBBB", 4, 4, 8, 2, 0, 0, 0))
               + bloco(b"IDAT", zlib.compress(linhas)) + bloco(b"IEND", b""))
        return base64.b64encode(png).decode()

    def test_pintar_com_textura_e_salvar(self):
        import os
        import tempfile
        import zipfile
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        r = run(self.c.pintar(PaintRequest(faces=[fid], material="Tijolo", textura_base64=self._png(), textura_nome="C:/x/tijolo.png")))
        self.assertEqual(r.pintadas[str(fid)], ["Tijolo", None])
        self.assertEqual(r.materiais["Tijolo"]["rgb"], [128, 128, 128] if not _tem_pillow() else [255, 0, 0])
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "t.skp")
            run(self.c.salvar(SaveDrawRequest(path=p)))
            with open(p, "rb") as fh:
                b = fh.read()
            import io
            z = zipfile.ZipFile(io.BytesIO(b[b.find(b"PK" + bytes([3, 4])):]))
            self.assertIn("materials/Tijolo/tijolo.png", z.namelist())  # so o nome do arquivo, sem a pasta enviada

    def test_textura_invalida(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        for ruim in ("@@@", "aGVsbG8="):  # nao e base64 / base64 de texto
            with self.assertRaises(HTTPException) as cm:
                run(self.c.pintar(PaintRequest(faces=[fid], material="X", textura_base64=ruim)))
            self.assertEqual(cm.exception.status_code, 422)

    def test_tags_e_cenas_no_estado_e_no_desfazer(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        e = run(self.c.marcar(TagRequest(nome="Piso", faces=[fid], arestas=[1])))
        self.assertEqual(e.tags, {"Piso": {"visivel": True}})
        self.assertEqual(e.tag_faces, {str(fid): "Piso"})
        self.assertEqual(e.tag_arestas, {"1": "Piso"})
        e = run(self.c.marcar(TagRequest(nome="Piso", visivel=False)))
        self.assertEqual(e.tags["Piso"]["visivel"], False)
        e = run(self.c.marcar(TagRequest(limpar=True, faces=[fid])))
        self.assertEqual(e.tag_faces, {})
        with self.assertRaises(HTTPException):
            run(self.c.marcar(TagRequest(faces=[fid])))  # sem nome e sem limpar
        e = run(self.c.adicionar_cena(CenaRequest(nome="Vista", olho=(0, -300, 100), alvo=(0, 0, 0))))
        self.assertEqual(e.cenas, [{"nome": "Vista", "descricao": "", "animar": True, "camera": True}])
        with self.assertRaises(HTTPException):
            run(self.c.adicionar_cena(CenaRequest(nome="Vista")))  # repetida
        with self.assertRaises(HTTPException):
            run(self.c.adicionar_cena(CenaRequest(nome="Sem alvo", olho=(1, 2, 3))))
        e = run(self.c.desfazer())
        self.assertEqual(e.cenas, [])  # desfez a cena; as duas tentativas recusadas nao entraram no historico

    def test_selecionar_e_ferramentas_de_arco(self):
        run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(10, 10, 0))))
        run(self.c.desenhar(DrawRequest(ferramenta="arco_3pontos", p0=(20, 0, 0), p1=(25, 5, 0), p2=(30, 0, 0))))
        run(self.c.desenhar(DrawRequest(ferramenta="bezier", pontos=[(40, 0, 0), (45, 10, 0), (50, 0, 0)], lados=4)))
        run(self.c.desenhar(DrawRequest(ferramenta="setor", centro=(70, 0, 0), raio=5, ang_ini=0, ang_fim=90)))
        r = run(self.c.selecionar(SelecaoRequest(acao="tudo")))
        self.assertGreaterEqual(len(r.faces), 2)
        inv = run(self.c.selecionar(SelecaoRequest(acao="inverter", faces=r.faces[:1], arestas=r.edges)))
        self.assertEqual(inv.faces, r.faces[1:])
        self.assertEqual(inv.edges, [])
        j = run(self.c.selecionar(SelecaoRequest(acao="janela", matriz=[1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
                                                 retangulo=[-1, -1, 11, 11])))
        self.assertEqual(len(j.faces), 1)
        for corpo in (SelecaoRequest(acao="tag"), SelecaoRequest(acao="janela"),
                      SelecaoRequest(acao="material", nome="nada")):
            with self.assertRaises(HTTPException):
                run(self.c.selecionar(corpo))
        with self.assertRaises(HTTPException):
            run(self.c.desenhar(DrawRequest(ferramenta="arco_3pontos", p0=(0, 0, 0), p1=(1, 0, 0), p2=(2, 0, 0))))

    def _cubo_api(self, x, y, z, s):
        ids = []
        for p in ([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [(0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)],
                  [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)], [(0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)],
                  [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)], [(1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1)]):
            pts = [(x + i * s, y + j * s, z + k * s) for i, j, k in p]
            antes = set(run(self.c.estado()).faces)
            run(self.c.desenhar(DrawRequest(ferramenta="linha", pontos=pts + [pts[0]])))
            ids += [int(i) for i in set(run(self.c.estado()).faces) - antes]
        return sorted(ids)

    def test_solido_verificar_e_operar(self):
        a = self._cubo_api(0, 0, 0, 10)
        b = self._cubo_api(5, 5, 5, 10)
        self.assertEqual((len(a), len(b)), (6, 6))
        v = run(self.c.solido(SolidoRequest(acao="verificar", a=a)))
        self.assertTrue(v.solido)
        self.assertAlmostEqual(v.volume, 1000.0)
        self.assertFalse(run(self.c.solido(SolidoRequest(acao="verificar", a=a[:5]))).solido)
        r = run(self.c.solido(SolidoRequest(acao="intersecao", a=a, b=b)))
        self.assertAlmostEqual(r.volume, 125.0)
        run(self.c.desfazer())
        self.assertEqual(len(run(self.c.estado()).faces), 12)  # desfazer volta aos dois cubos
        with self.assertRaises(HTTPException):
            run(self.c.solido(SolidoRequest(acao="uniao", a=a)))  # falta o segundo sólido

    def test_solido_coplanar_recusa_e_restaura(self):
        a = self._cubo_api(0, 0, 0, 10)
        b = self._cubo_api(10, 0, 0, 10)  # encosta numa face inteira: coplanares
        antes = run(self.c.estado()).counts
        with self.assertRaises(HTTPException):
            run(self.c.solido(SolidoRequest(acao="uniao", a=a, b=b)))
        self.assertEqual(run(self.c.estado()).counts, antes)

    def test_suavizar_por_angulo_e_por_selecao(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="circulo", centro=(0, 0, 0), raio=50)))
        fid = int(next(iter(j.faces.added)))
        run(self.c.empurrar(PushPullRequest(face_id=fid, distancia=100)))
        e = run(self.c.suavizar(SoftenRequest(angulo=20)))
        self.assertEqual(len(e.suaves), 24)
        self.assertTrue(all(b == 0x18 for b in e.suaves.values()))
        primeira = int(next(iter(e.suaves)))
        e = run(self.c.suavizar(SoftenRequest(arestas=[primeira], limpar=True)))
        self.assertEqual(len(e.suaves), 23)
        with self.assertRaises(HTTPException):
            run(self.c.suavizar(SoftenRequest()))  # sem arestas e sem angulo
        e = run(self.c.desfazer())
        self.assertEqual(len(e.suaves), 24)

    def test_ocultar_arestas_pelo_shift_do_apagar(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(10, 10, 0))))
        eid = int(next(iter(j.edges.added)))
        e = run(self.c.suavizar(SoftenRequest(arestas=[eid], ocultar=True)))
        self.assertEqual(e.suaves[str(eid)] & 1, 1)
        self.assertEqual(len(e.edges), 4)  # ocultar não apaga
        e = run(self.c.desfazer())
        self.assertNotIn(str(eid), e.suaves)
        e = run(self.c.suavizar(SoftenRequest(arestas=[eid], ocultar=True)))
        e = run(self.c.suavizar(SoftenRequest(arestas=[eid], ocultar=False)))
        self.assertNotIn(str(eid), e.suaves)
        with self.assertRaises(HTTPException):
            run(self.c.suavizar(SoftenRequest(ocultar=True)))  # sem arestas

    def test_guias_e_plano_de_secao_na_api(self):
        e = run(self.c.guia(GuiaRequest(tipo="ponto", p=(1, 2, 3))))
        self.assertEqual(len(e.guias), 1)
        e = run(self.c.guia(GuiaRequest(tipo="linha", p=(0, 0, 0), direcao=(0, 0, 1))))
        e = run(self.c.guia(GuiaRequest(tipo="secao", p=(0, 0, 50), direcao=(0, 0, 1))))
        self.assertEqual(list(e.secoes.values()), [[0.0, 0.0, 1.0, -50.0]])
        self.assertEqual(len(e.guias), 2)
        with self.assertRaises(HTTPException):
            run(self.c.guia(GuiaRequest(tipo="linha", p=(0, 0, 0))))  # nem alvo nem direcao
        with self.assertRaises(HTTPException):
            run(self.c.guia(GuiaRequest(tipo="apagar", id=999)))
        gid = int(next(iter(e.guias)))
        e = run(self.c.guia(GuiaRequest(tipo="apagar", id=gid)))
        self.assertEqual(len(e.guias), 1)
        e = run(self.c.desfazer())
        self.assertEqual(len(e.guias), 2)

    def test_texto_com_cor_na_api(self):
        e = run(self.c.nota(NotaRequest(tipo="texto", texto="Colorido", p=(1, 2, 3), cor=(10, 20, 30))))
        self.assertEqual([x["material"] for x in e.textos.values()], ["<auto>"])
        with self.assertRaises(HTTPException):
            run(self.c.nota(NotaRequest(tipo="texto", texto="Outro", p=(1, 2, 3), cor=(1, 1, 1))))  # segunda cor
        e = run(self.c.nota(NotaRequest(tipo="texto", texto="Fonte", p=(1, 2, 3), fonte_nova=("Arial", True, False, 20))))
        self.assertIn(["Arial", True, False, 20], [list(x["fonte_nova"]) for x in e.textos.values() if x.get("fonte_nova")])

    def test_texto_e_cota_na_api(self):
        e = run(self.c.nota(NotaRequest(tipo="texto", texto="Olá", p=(1, 2, 3))))
        self.assertEqual([x["texto"] for x in e.textos.values()], ["Olá"])
        e = run(self.c.nota(NotaRequest(tipo="cota", p=(0, 0, 0), fim=(100, 0, 0))))
        c = next(iter(e.cotas.values()))
        self.assertEqual((c["normal"], c["eixo_x"]), ([0.0, 0.0, 1.0], [1.0, 0.0, 0.0]))
        e = run(self.c.nota(NotaRequest(tipo="cota", p=(0, 0, 0), fim=(0, 0, 80))))  # aresta vertical: normal em y
        self.assertIn([0.0, 1.0, 0.0], [x["normal"] for x in e.cotas.values()])
        with self.assertRaises(HTTPException):
            run(self.c.nota(NotaRequest(tipo="texto", p=(0, 0, 0))))  # sem texto
        with self.assertRaises(HTTPException):
            run(self.c.nota(NotaRequest(tipo="cota", p=(0, 0, 0))))  # sem fim
        with self.assertRaises(HTTPException):
            run(self.c.nota(NotaRequest(tipo="apagar", id=999)))
        tid = int(next(iter(e.textos)))
        e = run(self.c.nota(NotaRequest(tipo="apagar", id=tid)))
        self.assertEqual((len(e.textos), len(e.cotas)), (0, 2))
        cid = int(next(iter(e.cotas)))
        e = run(self.c.nota(NotaRequest(tipo="apagar", id=cid)))
        self.assertEqual(len(e.cotas), 1)
        e = run(self.c.desfazer())
        self.assertEqual(len(e.cotas), 2)

    def test_posicionar_textura_na_api(self):
        j = run(self.c.desenhar(DrawRequest(ferramenta="retangulo", p0=(0, 0, 0), p1=(100, 100, 0))))
        fid = int(next(iter(j.faces.added)))
        with self.assertRaises(HTTPException):  # sem textura na frente
            run(self.c.posicionar(PosicionarRequest(faces=[fid], tamanho=50)))
        run(self.c.pintar(PaintRequest(faces=[fid], material="Tijolo", textura_base64=self._png(), textura_nome="t.png")))
        e = run(self.c.posicionar(PosicionarRequest(faces=[fid], tamanho=50, u0=0.25, v0=0.5)))
        self.assertEqual(e.uv[str(fid)], [50.0, 0.0, 0.0, 50.0, -12.5, -25.0])
        with self.assertRaises(HTTPException):
            run(self.c.posicionar(PosicionarRequest(faces=[fid])))  # sem tamanho nem limpar
        e = run(self.c.posicionar(PosicionarRequest(faces=[fid], limpar=True)))
        self.assertEqual(e.uv, {})
        e = run(self.c.desfazer())
        self.assertIn(str(fid), e.uv)


if __name__ == "__main__":
    unittest.main()
