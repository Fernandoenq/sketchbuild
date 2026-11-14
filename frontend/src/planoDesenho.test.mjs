// node --test frontend/src/planoDesenho.test.mjs
import test from "node:test";
import assert from "node:assert/strict";
import { planoAutomatico, cantosRetangulo, raioNoPlano, projetarNoPlano, normalParaCamera, nomeDoPlano, COS_PLANO_AUTO } from "./planoDesenho.js";

const perto = (a, b) => a.every((v, i) => Math.abs(v - b[i]) < 1e-9);
const grau = (g) => (g * Math.PI) / 180;

test("o limiar é o cosseno de 10 graus lido no SketchUp.exe", () => {
  assert.ok(Math.abs(COS_PLANO_AUTO - Math.cos(grau(10))) < 1e-4);
});

test("câmera de cima: plano do chão", () => {
  assert.deepEqual(planoAutomatico([0, 0, -1]), [0, 0, 1]);
});

test("câmera inclinada (45 graus): continua no chão", () => {
  assert.deepEqual(planoAutomatico([0, Math.SQRT1_2, -Math.SQRT1_2]), [0, 0, 1]);
});

test("câmera horizontal olhando ao longo de y: plano vertical perpendicular a y", () => {
  assert.deepEqual(planoAutomatico([0, 1, 0]), [0, 1, 0]);
});

test("câmera horizontal olhando ao longo de x: plano vertical perpendicular a x", () => {
  assert.deepEqual(planoAutomatico([-1, 0, 0]), [1, 0, 0]);
});

test("dentro de 10 graus de um eixo vale o eixo; fora, o chão", () => {
  const dentro = [0, Math.cos(grau(9)), -Math.sin(grau(9))];
  const fora = [0, Math.cos(grau(11)), -Math.sin(grau(11))];
  assert.deepEqual(planoAutomatico(dentro), [0, 1, 0]);
  assert.deepEqual(planoAutomatico(fora), [0, 0, 1]);
});

test("a direção não precisa vir normalizada", () => {
  assert.deepEqual(planoAutomatico([0, 7, 0]), [0, 1, 0]);
});

test("cantos iguais aos do núcleo Python (core/topology/draw.py)", () => {
  assert.ok(perto(cantosRetangulo([0, 0, 0], [100, 100, 0], [0, 0, 1])[2], [100, 100, 0]));
  const emY = cantosRetangulo([0, 0, 0], [100, 100, 100], [0, 1, 0]);
  [[0, 0, 0], [100, 0, 0], [100, 0, 100], [0, 0, 100]].forEach((c, i) => assert.ok(perto(emY[i], c), `y#${i}`));
  const emX = cantosRetangulo([0, 0, 0], [100, 100, 100], [1, 0, 0]);
  [[0, 0, 0], [0, 100, 0], [0, 100, 100], [0, 0, 100]].forEach((c, i) => assert.ok(perto(emX[i], c), `x#${i}`));
});

test("retângulo no chão mantém a altura do primeiro canto", () => {
  const c = cantosRetangulo([0, 0, 50], [10, 20, 50], [0, 0, 1]);
  assert.ok(c.every((p) => p[2] === 50));
});

test("raio fura o plano; paralelo e atrás da origem dão null", () => {
  assert.ok(perto(raioNoPlano([0, 0, 10], [0, 0, -1], [0, 0, 0], [0, 0, 1]), [0, 0, 0]));
  assert.equal(raioNoPlano([0, 0, 10], [1, 0, 0], [0, 0, 0], [0, 0, 1]), null);
  assert.equal(raioNoPlano([0, 0, 10], [0, 0, 1], [0, 0, 0], [0, 0, 1]), null);
});

test("projeção ortogonal no plano", () => {
  assert.ok(perto(projetarNoPlano([3, 4, 9], [0, 0, 2], [0, 0, 1]), [3, 4, 2]));
});

test("normal vira para o lado da câmera e o nome do plano", () => {
  assert.deepEqual(normalParaCamera([0, 1, 0], [0, 1, 0]), [-0, -1, -0]);
  assert.deepEqual(normalParaCamera([0, 1, 0], [0, -1, 0]), [0, 1, 0]);
  assert.equal(nomeDoPlano([0, 0, 1]), "vermelho-verde (chão)");
  assert.equal(nomeDoPlano([0, 1, 0]), "vermelho-azul (vertical)");
  assert.equal(nomeDoPlano([1, 0, 0]), "verde-azul (vertical)");
  assert.equal(nomeDoPlano([0.6, 0.8, 0]), "da face");
});
