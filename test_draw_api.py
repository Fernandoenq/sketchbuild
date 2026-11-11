"""F2: camada controller/serviço/repositório do desenho (sem HTTP: httpx não é dependência)."""
import asyncio
import unittest

from fastapi import HTTPException

from app.controllers.draw_controller import DrawController
from app.schemas.draw import DrawRequest, EditRequest, OffsetRequest, PushPullRequest


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

    def test_rotas_registradas(self):
        from app.main import app
        caminhos = {r.path for r in app.routes}
        self.assertIn("/api/v1/draw", caminhos)
        self.assertIn("/api/v1/draw/state", caminhos)
        self.assertIn("/api/v1/draw/pushpull", caminhos)
        self.assertIn("/api/v1/draw/edit", caminhos)
        self.assertIn("/api/v1/draw/offset", caminhos)


if __name__ == "__main__":
    unittest.main()
