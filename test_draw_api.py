"""F2: camada controller/serviço/repositório do desenho (sem HTTP: httpx não é dependência)."""
import asyncio
import unittest

from fastapi import HTTPException

from app.controllers.draw_controller import DrawController
from app.schemas.draw import DrawRequest, SaveDrawRequest, EditRequest, FollowMeRequest, GroupRequest, InstanceRequest, IntersectRequest, OffsetRequest, PaintRequest, PushPullRequest


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
        for r in ("save", "paint", "undo", "redo", "history", "followme", "intersect", "scene", "group", "instance", "explode", "enter", "exit"):
            self.assertIn("/api/v1/draw/" + r, caminhos)


if __name__ == "__main__":
    unittest.main()
