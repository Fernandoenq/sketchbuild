// Plano de desenho das formas (Retângulo): regras lidas no SketchUp.exe, ver docs/REA-PLANO-DE-DESENHO.md.
// Tudo em coordenadas do SketchUp (x, y, z), vetores como [x, y, z]; o módulo não depende do three.

// FUN_140b383c0: com a preferência AutoDrawingPlane ligada, o plano é o do chão (eixo z) a não ser que a direção da câmera
// esteja a menos de 10° de um eixo; aí vale o plano perpendicular a esse eixo. 0,9848 é cos(10°).
export const COS_PLANO_AUTO = 0.9848;

const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const soma = (a, k, v) => [a[0] + k * v[0], a[1] + k * v[1], a[2] + k * v[2]];
const unit = (v) => {
  const n = Math.hypot(v[0], v[1], v[2]);
  return n > 0 ? [v[0] / n, v[1] / n, v[2] / n] : [0, 0, 1];
};

/** Normal do plano de desenho em espaço vazio, a partir da direção da câmera (olhando para a cena). */
export function planoAutomatico(direcaoCamera) {
  const d = unit(direcaoCamera).map(Math.abs);
  // mesmo desempate do SketchUp: o eixo 1 só vence o 0, e o 2 só vence os dois, com desigualdade estrita
  let eixo = 0;
  let maior = d[0];
  if (maior < d[1]) {
    eixo = 1;
    maior = d[1];
  }
  if (maior < d[2]) {
    eixo = 2;
    maior = d[2];
  }
  const escolhido = maior > COS_PLANO_AUTO ? eixo : 2;
  const n = [0, 0, 0];
  n[escolhido] = 1;
  return n;
}

/** Mesma regra do backend (core/topology/draw.py `eixos`): X = Z x normal, Y = normal x X. */
export function eixosPlano(normal) {
  const n = unit(normal);
  const x = Math.abs(n[0]) < 1e-9 && Math.abs(n[1]) < 1e-9 ? [1, 0, 0] : unit(cross([0, 0, 1], n));
  return [x, cross(n, x)];
}

/** Os quatro cantos do retângulo de p0 a p1 no plano da normal (mesma conta de `pontos_retangulo`). */
export function cantosRetangulo(p0, p1, normal) {
  const [x, y] = eixosPlano(normal);
  const d = sub(p1, p0);
  const a = dot(d, x);
  const b = dot(d, y);
  const q = soma(p0, a, x);
  return [p0, q, soma(q, b, y), soma(p0, b, y)];
}

/** Ponto onde o raio (origem, direção) fura o plano (ponto `o`, normal `n`); null se paralelo ou atrás da origem. */
export function raioNoPlano(origem, direcao, o, n) {
  const dn = dot(direcao, n);
  if (Math.abs(dn) < 1e-9) return null;
  const t = dot(sub(o, origem), n) / dn;
  return t > 0 ? soma(origem, t, direcao) : null;
}

/** Projeção ortogonal de p no plano (ponto `o`, normal `n`). */
export function projetarNoPlano(p, o, n) {
  const u = unit(n);
  return soma(p, -dot(sub(p, o), u), u);
}

/** Vira a normal para o lado da câmera (a direção da câmera aponta para a cena, então n.direção < 0). */
export function normalParaCamera(n, direcaoCamera) {
  return dot(n, direcaoCamera) > 0 ? [-n[0], -n[1], -n[2]] : n;
}

/** Nome do plano para a barra de status. */
export function nomeDoPlano(n) {
  const [x, y, z] = n.map(Math.abs);
  if (z > 0.999) return "vermelho-verde (chão)";
  if (y > 0.999) return "vermelho-azul (vertical)";
  if (x > 0.999) return "verde-azul (vertical)";
  return "da face";
}
