// F2 do plano de modelagem (docs/PLANO-MODELAGEM.md): Linha, Retângulo, Círculo,
// Polígono, Arco e Mão livre que desenham no núcleo de topologia do backend
// (POST /api/v1/draw). O backend devolve o delta de vértices/arestas/faces e
// este módulo redesenha a geometria. Plano de desenho: chão (z=0 do SketchUp).
//
// Unidades: o viewport usa metros e o núcleo usa polegadas. Eixos: three (x, y, z)
// equivale a SketchUp (x, -z, y), o mesmo mapeamento do resto do app.

import * as THREE from "three";
import { drawTool, drawState, drawClear, drawPushPull, drawEdit, drawOffset } from "./api.js";

const POL = 39.37007874015748; // polegadas por metro
const PASSO = 0.01; // 1 cm
const SNAP_PX = 12;

const FERRAMENTAS = [
  ["linha", "Linha (modelagem)", '<line x1="5" y1="19" x2="19" y2="5"/><circle cx="5" cy="19" r="1.4" fill="currentColor"/><circle cx="19" cy="5" r="1.4" fill="currentColor"/>'],
  ["retangulo", "Retângulo (modelagem)", '<rect x="5" y="7" width="14" height="10"/>'],
  ["circulo", "Círculo (modelagem)", '<circle cx="12" cy="12" r="8"/>'],
  ["poligono", "Polígono (modelagem)", '<path d="M12 4l7 5-3 9H8L5 9z"/>'],
  ["arco", "Arco (modelagem)", '<path d="M4 18c2-9 14-9 16 0"/>'],
  ["mao_livre", "Mão livre (modelagem)", '<path d="M4 16c3-8 5 4 8-3s5 3 8-4"/>'],
  ["selecionar", "Selecionar face ou aresta (modelagem; Shift soma)", '<path d="M6 3l12 9-5 1.2L16 19l-2.4 1L11 14.5 7 17z"/>'],
  ["pushpull", "Empurrar/Puxar (modelagem)", '<rect x="4" y="10" width="16" height="10"/><path d="M12 2v8M9 5l3-3 3 3"/>'],
];

const DICA = {
  linha: "Linha: clique os pontos. Enter, duplo clique ou Esc termina.",
  retangulo: "Retângulo: clique no primeiro canto e no canto oposto.",
  circulo: "Círculo: clique no centro e depois no raio.",
  poligono: "Polígono: clique no centro e depois num vértice (lados no campo ao lado).",
  arco: "Arco: clique no centro, no início e no fim (anti-horário).",
  mao_livre: "Mão livre: segure o botão e arraste.",
  selecionar: "Selecionar: clique numa face ou aresta (Shift soma). Depois use Mover, Rotar, Esc. ou Offset com o valor no campo ao lado.",
  pushpull: "Empurrar/Puxar: clique numa face, digite a distância (m) no campo e Enter (Ctrl+Enter mantém a face original). Negativo empurra.",
};

const toSku = (p) => [p.x * POL, -p.z * POL, p.y * POL];
const fromSku = ([x, y, z]) => new THREE.Vector3(x / POL, z / POL, -y / POL);

export function iniciarModelagem({ scene, camera, renderer, getToolMode, setToolMode, setStatus }) {
  const grupo = new THREE.Group();
  grupo.name = "modelagem";
  scene.add(grupo);
  const previa = new THREE.Line(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({ color: 0x2255cc }));
  previa.visible = false;
  previa.renderOrder = 6;
  previa.frustumCulled = false;
  scene.add(previa);

  const estado = { vertices: new Map(), edges: new Map(), faces: new Map() };
  let ferramenta = null;
  let pontos = []; // pontos já fixados da ação em andamento (coordenadas three)
  let livre = null; // trilha da mão livre
  let lados = 6;
  let selecionada = null; // id da face escolhida no Empurrar/Puxar
  let campoDist = null;
  const sel = { faces: new Set(), edges: new Set() };
  let campoValor = null;
  const chao = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
  const ray = new THREE.Raycaster();

  // -- barra de ferramentas --------------------------------------------------
  const barra = document.getElementById("tools-toolbar");
  const botoes = new Map();
  if (barra) {
    const g = document.createElement("div");
    g.className = "toolbar-group";
    g.title = "Modelagem sobre o núcleo de topologia (F2)";
    for (const [id, titulo, svg] of FERRAMENTAS) {
      const b = document.createElement("button");
      b.className = "toolbar-btn tool-icon-btn";
      b.title = titulo;
      b.setAttribute("aria-label", titulo);
      b.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor">${svg}</svg>`;
      b.addEventListener("click", () => ativar(id));
      botoes.set(id, b);
      g.appendChild(b);
    }
    const n = document.createElement("input");
    n.type = "number";
    n.min = "3";
    n.max = "64";
    n.value = String(lados);
    n.title = "Lados do polígono";
    n.style.cssText = "width:44px;margin-left:4px";
    n.addEventListener("change", () => {
      lados = Math.max(3, Math.min(64, parseInt(n.value, 10) || 6));
    });
    g.appendChild(n);
    const dist = document.createElement("input");
    dist.type = "number";
    dist.step = "0.01";
    dist.placeholder = "dist. m";
    dist.title = "Distância do Empurrar/Puxar em metros (negativo empurra)";
    dist.style.cssText = "width:70px;margin-left:4px";
    dist.addEventListener("keydown", async (e) => {
      if (e.key !== "Enter") return;
      e.stopPropagation();
      const m = parseFloat(dist.value);
      if (!Number.isFinite(m) || m === 0) return setStatus("Informe uma distância diferente de zero.", true);
      if (selecionada == null) return setStatus("Clique antes numa face com a ferramenta Empurrar/Puxar.", true);
      try {
        const r = await drawPushPull(Number(selecionada), m * POL, e.ctrlKey);
        aplicar(r);
        selecionada = null;
        dist.value = "";
        setStatus(`${r.counts.vertices} vértices, ${r.counts.edges} arestas, ${r.counts.faces} faces.`);
      } catch (err) {
        setStatus(`Erro no Empurrar/Puxar: ${err?.message ?? err}`, true);
      }
    });
    g.appendChild(dist);
    campoDist = dist;
    const valor = document.createElement("input");
    valor.type = "text";
    valor.placeholder = "valor";
    valor.title = "Mover: dx,dy,dz em metros | Rotar: graus | Esc.: fator (ou fx,fy,fz) | Offset: metros (negativo para dentro)";
    valor.style.cssText = "width:90px;margin-left:4px";
    campoValor = valor;
    g.appendChild(valor);
    for (const [rotulo, op] of [["Mover", "mover"], ["Rotar", "rotacionar"], ["Esc.", "escalar"], ["Offset", "offset"]]) {
      const b = document.createElement("button");
      b.className = "toolbar-btn";
      b.textContent = rotulo;
      b.title = rotulo + " a seleção com o valor do campo";
      b.addEventListener("click", () => aplicarEdicao(op));
      g.appendChild(b);
    }
    const l = document.createElement("button");
    l.className = "toolbar-btn";
    l.textContent = "Limpar";
    l.title = "Zera o desenho do núcleo de topologia";
    l.addEventListener("click", async () => {
      try {
        await drawClear();
      } catch (err) {
        setStatus(`Erro ao zerar: ${err?.message ?? err}`, true);
        return;
      }
      estado.vertices.clear();
      estado.edges.clear();
      estado.faces.clear();
      redesenhar();
      setStatus("Desenho de modelagem zerado.");
    });
    g.appendChild(l);
    barra.appendChild(g);
  }

  async function aplicarEdicao(op) {
    const bruto = (campoValor?.value ?? "").trim();
    if (!sel.faces.size && !sel.edges.size) return setStatus("Selecione faces ou arestas antes (ferramenta Selecionar).", true);
    const nums = bruto.split(/[;,\s]+/).filter(Boolean).map((x) => Number.parseFloat(x));
    const corpo = { operacao: op, faces: [...sel.faces].map(Number), arestas: [...sel.edges].map(Number) };
    try {
      let r;
      if (op === "mover") {
        if (nums.length !== 3 || nums.some((n) => !Number.isFinite(n))) return setStatus("Mover: informe dx,dy,dz em metros.", true);
        // viewport (x, y, z) -> SketchUp (x, -z, y), em polegadas
        r = await drawEdit({ ...corpo, vetor: [nums[0] * POL, -nums[2] * POL, nums[1] * POL] });
      } else if (op === "rotacionar") {
        if (nums.length !== 1 || !Number.isFinite(nums[0])) return setStatus("Rotar: informe o ângulo em graus.", true);
        r = await drawEdit({ ...corpo, angulo: nums[0] });
      } else if (op === "escalar") {
        if (![1, 3].includes(nums.length) || nums.some((n) => !Number.isFinite(n) || n <= 0)) return setStatus("Esc.: informe um fator positivo (ou três).", true);
        r = await drawEdit(nums.length === 1 ? { ...corpo, fator: nums[0] } : { ...corpo, fatores: [nums[0], nums[2], nums[1]] });
      } else {
        if (sel.faces.size !== 1 || nums.length !== 1 || !Number.isFinite(nums[0])) return setStatus("Offset: escolha uma face e informe a distância em metros.", true);
        r = await drawOffset(Number([...sel.faces][0]), nums[0] * POL);
      }
      sel.faces.clear();
      sel.edges.clear();
      aplicar(r);
      setStatus(r.counts.vertices + " vértices, " + r.counts.edges + " arestas, " + r.counts.faces + " faces.");
    } catch (err) {
      setStatus("Erro na edição: " + (err?.message ?? err), true);
    }
  }

  function ativar(id) {
    ferramenta = id;
    selecionada = null;
    if (id !== "selecionar") {
      sel.faces.clear();
      sel.edges.clear();
      redesenhar();
    }
    terminar();
    setToolMode("modelar");
    setStatus(DICA[id]);
    sincronizar();
  }

  function sincronizar() {
    const viva = getToolMode() === "modelar";
    if (!viva && (pontos.length || livre)) terminar();
    for (const [id, b] of botoes) b.classList.toggle("active", viva && id === ferramenta);
  }
  setInterval(sincronizar, 300);

  // -- ponto sob o mouse (chão + encaixe em vértices existentes) -------------
  function pontoDe(event) {
    const r = renderer.domElement.getBoundingClientRect();
    const nx = ((event.clientX - r.left) / r.width) * 2 - 1;
    const ny = -((event.clientY - r.top) / r.height) * 2 + 1;
    ray.setFromCamera({ x: nx, y: ny }, camera);
    let melhor = null;
    let dist = SNAP_PX;
    for (const v of estado.vertices.values()) {
      const w = fromSku(v);
      const s = w.clone().project(camera);
      const d = Math.hypot(((s.x - nx) * r.width) / 2, ((s.y - ny) * r.height) / 2);
      if (d < dist) {
        dist = d;
        melhor = w;
      }
    }
    if (melhor) return melhor;
    const alvo = new THREE.Vector3();
    if (!ray.ray.intersectPlane(chao, alvo)) return null;
    alvo.x = Math.round(alvo.x / PASSO) * PASSO;
    alvo.z = Math.round(alvo.z / PASSO) * PASSO;
    alvo.y = 0;
    return alvo;
  }

  // -- envio e redesenho ------------------------------------------------------
  async function enviar(corpo) {
    try {
      const r = await drawTool(corpo);
      aplicar(r);
      const c = r.counts;
      setStatus(`${c.vertices} vértices, ${c.edges} arestas, ${c.faces} faces.`);
    } catch (err) {
      setStatus(`Erro ao desenhar: ${err?.message ?? err}`, true);
    }
  }

  function aplicar(delta) {
    for (const [k, mapa] of [["vertices", estado.vertices], ["edges", estado.edges], ["faces", estado.faces]]) {
      const d = delta[k];
      for (const id of d.removed) {
        mapa.delete(String(id));
        sel.faces.delete(String(id));
      }
      for (const [id, v] of Object.entries({ ...d.added, ...d.changed })) mapa.set(id, v);
    }
    redesenhar();
  }

  // face no delta: [outer, holes] (tupla do Python); no estado completo: {outer, holes}
  const lacos = (f) => (Array.isArray(f) ? [f[0], ...f[1]] : [f.outer, ...f.holes]);

  function triangular(f) {
    const faltando = lacos(f).some((lp) => lp.some((id) => !estado.vertices.has(String(id))));
    if (faltando) return null;
    const [externo, ...furos] = lacos(f).map((lp) => lp.map((id) => fromSku(estado.vertices.get(String(id)))));
    if (externo.length < 3) return null;
    const n = new THREE.Vector3();
    for (let i = 0; i < externo.length; i++) {
      const a = externo[i];
      const b = externo[(i + 1) % externo.length];
      n.x += (a.y - b.y) * (a.z + b.z);
      n.y += (a.z - b.z) * (a.x + b.x);
      n.z += (a.x - b.x) * (a.y + b.y);
    }
    n.normalize();
    const u = Math.abs(n.y) < 0.9 ? new THREE.Vector3(0, 1, 0).cross(n).normalize() : new THREE.Vector3(1, 0, 0);
    const v = n.clone().cross(u);
    const p2 = (p) => new THREE.Vector2(p.dot(u), p.dot(v));
    const tri = THREE.ShapeUtils.triangulateShape(externo.map(p2), furos.map((h) => h.map(p2)));
    const todos = [...externo, ...furos.flat()];
    const pos = [];
    for (const t of tri) for (const i of t) pos.push(todos[i].x, todos[i].y, todos[i].z);
    return pos;
  }

  function redesenhar() {
    grupo.children.slice().forEach((o) => {
      o.geometry?.dispose();
      grupo.remove(o);
    });
    const seg = [];
    for (const [a, b] of estado.edges.values()) {
      const pa = estado.vertices.get(String(a));
      const pb = estado.vertices.get(String(b));
      if (!pa || !pb) continue;
      seg.push(fromSku(pa), fromSku(pb));
    }
    if (seg.length) {
      const l = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(seg), new THREE.LineBasicMaterial({ color: 0x111111 }));
      l.renderOrder = 5;
      l.frustumCulled = false;
      grupo.add(l);
    }
    const destaque = [];
    for (const id of sel.edges) {
      const e = estado.edges.get(id);
      if (!e) continue;
      destaque.push(fromSku(estado.vertices.get(String(e[0]))), fromSku(estado.vertices.get(String(e[1]))));
    }
    if (destaque.length) {
      const h = new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(destaque), new THREE.LineBasicMaterial({ color: 0xff7700 }));
      h.renderOrder = 7;
      h.frustumCulled = false;
      grupo.add(h);
    }
    for (const [id, f] of estado.faces) {
      const pos = triangular(f);
      if (!pos || !pos.length) continue;
      const g = new THREE.BufferGeometry();
      g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
      g.computeVertexNormals();
      const escolhida = id === String(selecionada) || sel.faces.has(id);
      const m = new THREE.Mesh(
        g,
        new THREE.MeshStandardMaterial({
          color: escolhida ? 0x6fa8ff : 0xdfdfdb,
          roughness: 0.8,
          side: THREE.DoubleSide,
          polygonOffset: true,
          polygonOffsetFactor: 1,
          polygonOffsetUnits: 1,
        })
      );
      m.frustumCulled = false;
      m.userData.fid = id;
      grupo.add(m);
    }
  }

  // -- geometria da prévia (espelha as regras do backend) ---------------------
  const arcoPontos = (c, r, a0, a1, n) =>
    Array.from({ length: n + 1 }, (_, i) => {
      const a = a0 + ((a1 - a0) * i) / n;
      return new THREE.Vector3(c.x + r * Math.cos(a), 0, c.z - r * Math.sin(a));
    });
  const angulo = (c, p) => Math.atan2(-(p.z - c.z), p.x - c.x); // anti-horário visto de cima (eixo y do SketchUp)
  const graus = (r) => (r * 180) / Math.PI;

  function previaPontos(p) {
    const [a, b] = pontos;
    if (ferramenta === "linha") return [...pontos, p];
    if (ferramenta === "retangulo") return [a, new THREE.Vector3(p.x, 0, a.z), p, new THREE.Vector3(a.x, 0, p.z), a];
    if (ferramenta === "circulo") return arcoPontos(a, a.distanceTo(p), 0, Math.PI * 2, 24);
    if (ferramenta === "poligono") return arcoPontos(a, a.distanceTo(p), 0, Math.PI * 2, lados);
    if (ferramenta === "arco") {
      if (pontos.length === 1) return [a, p];
      const ini = angulo(a, b);
      let fim = angulo(a, p);
      if (fim <= ini) fim += Math.PI * 2;
      return [a, ...arcoPontos(a, a.distanceTo(b), ini, fim, 12), a];
    }
    return null;
  }

  function mostrarPrevia(pts) {
    previa.geometry.dispose();
    previa.geometry = new THREE.BufferGeometry().setFromPoints(pts);
    previa.visible = true;
  }

  function mover(event) {
    if (getToolMode() !== "modelar" || !ferramenta) return;
    const p = pontoDe(event);
    if (!p) return;
    if (ferramenta === "mao_livre") {
      if (livre) {
        if (livre[livre.length - 1].distanceTo(p) >= 0.02) livre.push(p);
        if (livre.length > 1) mostrarPrevia(livre);
      }
      return;
    }
    if (!pontos.length) return;
    const pts = previaPontos(p);
    if (pts) mostrarPrevia(pts);
  }

  function escolherFace(event) {
    const r = renderer.domElement.getBoundingClientRect();
    ray.setFromCamera({ x: ((event.clientX - r.left) / r.width) * 2 - 1, y: -((event.clientY - r.top) / r.height) * 2 + 1 }, camera);
    const hit = ray.intersectObjects(grupo.children.filter((o) => o.isMesh), false)[0];
    selecionada = hit ? hit.object.userData.fid : null;
    redesenhar();
    if (selecionada != null) {
      setStatus(`Face ${selecionada} escolhida. Digite a distância (m) no campo e Enter.`);
      campoDist?.focus();
    } else {
      setStatus("Nenhuma face sob o clique.");
    }
  }

  function arestaSob(event) {
    const r = renderer.domElement.getBoundingClientRect();
    const px = event.clientX - r.left;
    const py = event.clientY - r.top;
    const tela = (v) => {
      const s = fromSku(v).project(camera);
      return [((s.x + 1) / 2) * r.width, ((1 - s.y) / 2) * r.height];
    };
    let melhor = null;
    let dist = 8;
    for (const [id, [a, b]] of estado.edges) {
      const [ax, ay] = tela(estado.vertices.get(String(a)));
      const [bx, by] = tela(estado.vertices.get(String(b)));
      const dx = bx - ax;
      const dy = by - ay;
      const q = dx * dx + dy * dy;
      const u = q ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / q)) : 0;
      const d = Math.hypot(px - (ax + u * dx), py - (ay + u * dy));
      if (d < dist) {
        dist = d;
        melhor = id;
      }
    }
    return melhor;
  }

  function selecionarClique(event) {
    const r = renderer.domElement.getBoundingClientRect();
    ray.setFromCamera({ x: ((event.clientX - r.left) / r.width) * 2 - 1, y: -((event.clientY - r.top) / r.height) * 2 + 1 }, camera);
    const aresta = arestaSob(event);
    const hit = ray.intersectObjects(grupo.children.filter((o) => o.isMesh), false)[0];
    if (!event.shiftKey) {
      sel.faces.clear();
      sel.edges.clear();
    }
    if (aresta != null) {
      if (sel.edges.has(aresta)) sel.edges.delete(aresta);
      else sel.edges.add(aresta);
    } else if (hit) {
      const id = hit.object.userData.fid;
      if (sel.faces.has(id)) sel.faces.delete(id);
      else sel.faces.add(id);
    }
    redesenhar();
    setStatus("Seleção: " + sel.faces.size + " face(s), " + sel.edges.size + " aresta(s).");
  }

  async function clicar(event) {
    if (ferramenta === "selecionar") return selecionarClique(event);
    if (ferramenta === "pushpull") return escolherFace(event);
    const p = pontoDe(event);
    if (!p) return;
    if (ferramenta === "linha") {
      if (pontos.length) await enviar({ ferramenta: "linha", pontos: [toSku(pontos[pontos.length - 1]), toSku(p)] });
      pontos.push(p);
      return;
    }
    pontos.push(p);
    const [a, b, c] = pontos;
    if (ferramenta === "retangulo" && pontos.length === 2) {
      await enviar({ ferramenta: "retangulo", p0: toSku(a), p1: toSku(b) });
      terminar();
    } else if ((ferramenta === "circulo" || ferramenta === "poligono") && pontos.length === 2) {
      const raio = a.distanceTo(b) * POL;
      if (raio > 0) {
        await enviar(
          ferramenta === "circulo" ? { ferramenta, centro: toSku(a), raio } : { ferramenta, centro: toSku(a), raio, lados }
        );
      }
      terminar();
    } else if (ferramenta === "arco" && pontos.length === 3) {
      const ini = graus(angulo(a, b));
      let fim = graus(angulo(a, c));
      if (fim <= ini) fim += 360;
      await enviar({
        ferramenta: "arco",
        centro: toSku(a),
        raio: a.distanceTo(b) * POL,
        ang_ini: ini,
        ang_fim: fim,
        lados: Math.max(3, Math.ceil((fim - ini) / 7.5)),
      });
      terminar();
    }
  }

  function terminar() {
    pontos = [];
    livre = null;
    previa.visible = false;
  }

  const el = renderer.domElement;
  // fase de captura: com a modelagem ativa, o clique não chega à seleção do app
  el.addEventListener(
    "pointerdown",
    (e) => {
      if (getToolMode() !== "modelar" || e.button !== 0) return;
      if (ferramenta === "mao_livre") {
        const p = pontoDe(e);
        if (p) livre = [p];
      }
    },
    true
  );
  el.addEventListener(
    "pointerup",
    async (e) => {
      if (getToolMode() !== "modelar" || e.button !== 0) return;
      if (ferramenta === "mao_livre") {
        const trilha = livre;
        terminar();
        if (trilha && trilha.length >= 2) await enviar({ ferramenta: "mao_livre", pontos: trilha.map(toSku) });
        return;
      }
      await clicar(e);
    },
    true
  );
  el.addEventListener(
    "click",
    (e) => {
      if (getToolMode() === "modelar") e.stopImmediatePropagation();
    },
    true
  );
  el.addEventListener(
    "dblclick",
    () => {
      if (getToolMode() === "modelar" && ferramenta === "linha") terminar();
    },
    true
  );
  el.addEventListener("pointermove", mover);
  window.addEventListener("keydown", (e) => {
    if (getToolMode() !== "modelar") return;
    if (e.key === "Escape" || e.key === "Enter") terminar();
  });

  // reaproveita o desenho que o backend ainda guarda (F5 na página)
  drawState()
    .then((s) => {
      for (const [k, mapa] of [["vertices", estado.vertices], ["edges", estado.edges], ["faces", estado.faces]]) {
        for (const [id, v] of Object.entries(s[k])) mapa.set(id, v);
      }
      redesenhar();
    })
    .catch(() => {});

  return { ativar, estado };
}
