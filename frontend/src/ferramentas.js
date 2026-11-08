// Ferramentas da arquiteta (04/11/2026, pedido do usuário): as funcoes do
// SketchUp que mais aparecem nos cursos e blogs de arquitetura e que ainda
// faltavam aqui. Tudo roda no navegador; o que precisa ficar (cenas,
// etiquetas, sol) vai no ambiente do projeto e e salvo junto.
//
//   Planta     vista de cima sem perspectiva (a "planta" que a arquiteta entrega)
//   Cenas      grava vistas e passa de uma pra outra (com "Tocar", tipo slide)
//   Etiqueta   texto com seta preso num ponto do 3D
//   Foto 4K    imagem 3840 x 2160 pra proposta
//   Camadas    liga/desliga brinquedos, muros, cenario e etiquetas
//   Sol        sombra real pela data, hora e cidade
//   Lista      os brinquedos do projeto (clicar seleciona, olho esconde)
//   Corte      corta o projeto na altura ou no comprimento
//   Estilo     normal, traco, raio-x, monocromatico
//   Passeio    anda dentro do parque na altura de uma crianca ou adulto

import * as THREE from "three";

const CIDADES = {
  "Sousa-PB": [-6.76, -38.23],
  "João Pessoa-PB": [-7.12, -34.86],
  "Campina Grande-PB": [-7.23, -35.88],
  "Patos-PB": [-7.02, -37.28],
  "Princesa Isabel-PB": [-7.74, -37.99],
  "São Paulo-SP": [-23.55, -46.63],
};

export function iniciarFerramentas(ctx) {
  const { sb } = ctx;
  const esp = () => ctx.getEspaco();

  // ---------- barra ----------
  const barra = document.createElement("div");
  barra.className = "toolbar-group pk-cen-grupo pk-fer-grupo";
  // Icones em traco, no mesmo padrao da faixa de cima (svg 24x24 do toolbar-btn).
  const BOTOES = [
    ["planta", "Planta 2D (vista de cima)", '<rect x="4" y="4" width="16" height="16" /><path d="M4 12h9M13 4v16M13 15h7" />'],
    ["cenas", "Cenas: grava vistas e apresenta", '<rect x="3" y="7" width="13" height="10" rx="1.5" /><path d="M16 11l5-3v8l-5-3" />'],
    ["etiqueta", "Etiqueta com seta", '<path d="M3 12V5h7l10 10-7 7z" /><circle cx="7.5" cy="8.5" r="1.3" />'],
    ["foto", "Foto em alta (4K)", '<path d="M4 8h3l2-3h6l2 3h3v11H4z" /><circle cx="12" cy="13" r="3.5" />'],
    ["camadas", "Camadas", '<path d="M12 4l9 5-9 5-9-5z" /><path d="M3 14l9 5 9-5" />'],
    ["sol", "Sol e sombra real", '<circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" />'],
    ["lista", "Lista do projeto", '<path d="M9 6h11M9 12h11M9 18h11" /><circle cx="4.5" cy="6" r="1" /><circle cx="4.5" cy="12" r="1" /><circle cx="4.5" cy="18" r="1" />'],
    ["corte", "Corte", '<path d="M3 12h18" stroke-dasharray="3 2" /><path d="M6 5l6 7 6-7M6 19l6-7 6 7" />'],
    ["estilo", "Estilo de visualização", '<path d="M4 20l4-1 11-11-3-3L5 16z" /><path d="M14 7l3 3" />'],
    ["passeio", "Passeio (andar dentro do parque)", '<circle cx="13" cy="4.5" r="1.8" /><path d="M10 21l2-6 3 3v3M12 15l1-6 4 3M13 9l-4 2-1 4" />'],
  ];
  for (const [id, titulo, icone] of BOTOES) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "toolbar-btn pk-fer-btn";
    b.dataset.fer = id;
    b.title = titulo;
    b.setAttribute("aria-label", titulo);
    b.innerHTML = `<svg viewBox="0 0 24 24">${icone}</svg>`;
    barra.append(b);
  }
  (document.getElementById("top-toolbar") || document.body).appendChild(barra);

  const caixa = document.createElement("div");
  caixa.className = "pk-cen-caixa pk-fer-caixa";
  caixa.hidden = true;
  document.body.appendChild(caixa);
  let aberta = null;

  function abrir(id, ...conteudo) {
    if (id !== "etiqueta" && modoEtiqueta) pararEtiqueta();
    aberta = id;
    const handle = document.createElement("div");
    handle.className = "pk-cen-drag-handle";
    handle.title = "Clique e arraste para reposicionar a janela";
    const topo = document.createElement("div");
    topo.className = "pk-fer-topo";
    const t = document.createElement("b");
    t.textContent = BOTOES.find((x) => x[0] === id)?.[1] || "";
    const x = Object.assign(document.createElement("button"), { type: "button", className: "pk-fer-x", textContent: "×", title: "Fechar" });
    x.onclick = fechar;
    topo.append(t, x);
    caixa.replaceChildren(handle, topo, ...conteudo);
    caixa.hidden = false;
    barra.querySelectorAll(".pk-fer-btn").forEach((b) => b.classList.toggle("active", b.dataset.fer === id));
  }
  function fechar() {
    aberta = null;
    caixa.hidden = true;
    barra.querySelectorAll(".pk-fer-btn").forEach((b) => b.classList.remove("active"));
    if (modoEtiqueta) pararEtiqueta();
  }
  const el = (tag, props = {}, ...filhos) => {
    const e = Object.assign(document.createElement(tag), props);
    e.append(...filhos);
    return e;
  };
  const botao = (texto, onclick, extra = "") => el("button", { type: "button", className: `pk-fer-acao ${extra}`, textContent: texto, onclick });
  const dica = (texto) => el("p", { className: "pk-cen-mat-nome", textContent: texto });

  barra.addEventListener("click", (e) => {
    const b = e.target.closest(".pk-fer-btn");
    if (!b) return;
    const id = b.dataset.fer;
    if (aberta === id) return fechar();
    ({ planta, cenas, etiqueta, foto, camadas, sol, lista, corte, estilo, passeio })[id]();
  });

  // ---------- 1. Planta 2D ----------
  let emPlanta = false;
  function planta() {
    emPlanta = !emPlanta;
    sb.setProjectionMode(emPlanta ? "parallel" : "perspective");
    sb.setStandardView(emPlanta ? "alto" : "iso");
    barra.querySelector('[data-fer="planta"]').classList.toggle("active", emPlanta);
    sb.setStatus(emPlanta ? "Planta 2D: vista de cima sem perspectiva. Clique de novo pra voltar ao 3D." : "Vista 3D de volta.");
  }

  // ---------- 2. Cenas ----------
  function cenasDoProjeto() {
    const e = esp();
    if (!e) return null;
    e.cenas = Array.isArray(e.cenas) ? e.cenas : [];
    return e.cenas;
  }
  function vistaAtual(nome) {
    const c = sb.camera, t = sb.controls.target;
    return { nome, pos: c.position.toArray().map((v) => +v.toFixed(3)), alvo: t.toArray().map((v) => +v.toFixed(3)), up: c.up.toArray() };
  }
  let animando = null;
  function irPara(cena, ms = 1400) {
    return new Promise((fim) => {
      cancelAnimationFrame(animando);
      const c = sb.camera, ctl = sb.controls;
      const p0 = c.position.clone(), a0 = ctl.target.clone();
      const p1 = new THREE.Vector3(...cena.pos), a1 = new THREE.Vector3(...cena.alvo);
      c.up.set(...(cena.up || [0, 1, 0]));
      const t0 = performance.now();
      const passo = (agora) => {
        const k = Math.min((agora - t0) / ms, 1);
        const s = k * k * (3 - 2 * k); // suave no comeco e no fim
        c.position.lerpVectors(p0, p1, s);
        ctl.target.lerpVectors(a0, a1, s);
        ctl.update();
        if (k < 1) animando = requestAnimationFrame(passo);
        else fim();
      };
      animando = requestAnimationFrame(passo);
    });
  }
  let tocando = false;
  async function tocar() {
    const lista = cenasDoProjeto() || [];
    if (!lista.length) return sb.setStatus("Grave pelo menos uma cena primeiro.", true);
    tocando = !tocando;
    while (tocando) {
      for (const cena of lista) {
        if (!tocando) break;
        sb.setStatus(`▶ ${cena.nome}`);
        await irPara(cena, 2200);
        await new Promise((r) => setTimeout(r, 1800));
      }
    }
    sb.setStatus("Apresentação das cenas parada.");
    if (aberta === "cenas") cenas();
  }
  function cenas() {
    const lista = cenasDoProjeto();
    if (!lista) return sb.setStatus("Crie o espaço primeiro (Novo espaço).", true);
    const ul = el("div", { className: "pk-fer-lista" });
    lista.forEach((c, i) => {
      const linha = el("div", { className: "pk-fer-linha" },
        botao(c.nome, () => irPara(c), "pk-fer-nome"),
        botao("✎", () => {
          const n = prompt("Nome da cena:", c.nome);
          if (n && n.trim()) { c.nome = n.trim().slice(0, 40); ctx.guardar(); cenas(); }
        }, "pk-fer-mini"),
        botao("×", () => { lista.splice(i, 1); ctx.guardar(); cenas(); }, "pk-fer-mini perigo"));
      ul.append(linha);
    });
    abrir("cenas",
      dica("Ajeite a câmera e grave. \"Tocar\" passa pelas cenas sozinho, como slides."),
      ul,
      el("div", { className: "pk-cen-acoes" },
        botao("+ Gravar esta vista", () => {
          lista.push(vistaAtual(`Cena ${lista.length + 1}`));
          ctx.guardar();
          cenas();
        }),
        botao(tocando ? "■ Parar" : "▶ Tocar", tocar, "primario")));
  }

  // ---------- 3. Etiquetas ----------
  const grupoEtiquetas = new THREE.Group();
  grupoEtiquetas.name = "etiquetas-sketchbuild";
  sb.scene.add(grupoEtiquetas);
  function sprite(texto) {
    const c = document.createElement("canvas");
    const g = c.getContext("2d");
    g.font = "700 30px Poppins, system-ui, sans-serif";
    const w = Math.min(Math.ceil(g.measureText(texto).width) + 44, 1000);
    c.width = w; c.height = 60;
    g.font = "700 30px Poppins, system-ui, sans-serif";
    g.fillStyle = "#ffffff";
    g.strokeStyle = "#0B3D91";
    g.lineWidth = 4;
    g.beginPath(); g.roundRect(3, 3, w - 6, 54, 14); g.fill(); g.stroke();
    g.fillStyle = "#0B3D91";
    g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText(texto, w / 2, 32);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    const sp = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, depthTest: false, sizeAttenuation: false }));
    sp.scale.set(0.0006 * w, 0.036, 1);
    sp.center.set(0.5, 0);
    sp.renderOrder = 1001;
    return sp;
  }
  function desenharEtiquetas() {
    grupoEtiquetas.clear();
    for (const [i, d] of (esp()?.etiquetas || []).entries()) {
      const p = new THREE.Vector3(d.x, d.y, d.z);
      const topo = p.clone().add(new THREE.Vector3(0, d.alt ?? 0.9, 0));
      const linha = new THREE.Line(new THREE.BufferGeometry().setFromPoints([p, topo]),
        new THREE.LineBasicMaterial({ color: 0x0b3d91, depthTest: false }));
      linha.renderOrder = 1000;
      const ponta = new THREE.Mesh(new THREE.SphereGeometry(0.05, 12, 8), new THREE.MeshBasicMaterial({ color: 0x0b3d91, depthTest: false }));
      ponta.position.copy(p);
      ponta.renderOrder = 1000;
      const s = sprite(d.texto);
      s.position.copy(topo);
      s.userData.etiqueta = i;
      grupoEtiquetas.add(linha, ponta, s);
    }
  }
  let modoEtiqueta = false;
  const raio = new THREE.Raycaster();
  function pontoClicado(e) {
    const r = sb.canvas.getBoundingClientRect();
    raio.setFromCamera(new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1), sb.camera);
    const alvos = [];
    sb.scene.traverse((o) => { if (o.isMesh && o.visible && !o.userData.ignorarClique) alvos.push(o); });
    const hit = raio.intersectObjects(alvos, false).find((h) => !grupoEtiquetas.children.includes(h.object));
    return hit?.point || null;
  }
  function aoClicarEtiqueta(e) {
    if (!modoEtiqueta || e.target !== sb.canvas || e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();
    const p = pontoClicado(e);
    if (!p) return;
    const texto = prompt("Texto da etiqueta:", "");
    if (!texto || !texto.trim()) return;
    const e2 = esp();
    e2.etiquetas = Array.isArray(e2.etiquetas) ? e2.etiquetas : [];
    e2.etiquetas.push({ x: +p.x.toFixed(3), y: +p.y.toFixed(3), z: +p.z.toFixed(3), texto: texto.trim().slice(0, 60) });
    ctx.guardar();
    desenharEtiquetas();
    etiqueta(true);
  }
  window.addEventListener("pointerdown", (e) => { if (modoEtiqueta && e.target === sb.canvas && e.button === 0) e.stopPropagation(); }, true);
  window.addEventListener("click", aoClicarEtiqueta, true);
  function pararEtiqueta() {
    modoEtiqueta = false;
    sb.canvas.style.cursor = "";
  }
  function etiqueta(manter) {
    if (!esp()) return sb.setStatus("Crie o espaço primeiro (Novo espaço).", true);
    modoEtiqueta = true;
    sb.canvas.style.cursor = "crosshair";
    const lista = el("div", { className: "pk-fer-lista" });
    (esp().etiquetas || []).forEach((d, i) => lista.append(el("div", { className: "pk-fer-linha" },
      el("span", { className: "pk-fer-nome", textContent: d.texto }),
      botao("✎", () => { const n = prompt("Texto:", d.texto); if (n && n.trim()) { d.texto = n.trim().slice(0, 60); ctx.guardar(); desenharEtiquetas(); etiqueta(true); } }, "pk-fer-mini"),
      botao("×", () => { esp().etiquetas.splice(i, 1); ctx.guardar(); desenharEtiquetas(); etiqueta(true); }, "pk-fer-mini perigo"))));
    abrir("etiqueta", dica("Clique no ponto do 3D onde vai a seta e escreva o texto. Feche aqui pra parar."), lista);
    if (!manter) sb.setStatus("Etiqueta: clique no ponto do 3D.");
  }

  // ---------- 4. Foto 4K ----------
  function foto() {
    const r = sb.renderer;
    const tam = r.getSize(new THREE.Vector2());
    const ratio = r.getPixelRatio();
    const cam = sb.camera;
    const aspecto = cam.aspect;
    try {
      r.setPixelRatio(1);
      r.setSize(3840, 2160, false);
      cam.aspect = 3840 / 2160;
      cam.updateProjectionMatrix();
      const url = sb.snapshotPNG(["marcador-sketchbuild"]);
      const a = document.createElement("a");
      a.href = url;
      a.download = `projeto-sketchbuild-4k-${new Date().toISOString().slice(0, 10)}.png`;
      a.click();
      sb.setStatus("Foto 4K baixada (3840 × 2160).");
    } finally {
      r.setPixelRatio(ratio);
      r.setSize(tam.x, tam.y, false);
      cam.aspect = aspecto;
      cam.updateProjectionMatrix();
    }
  }

  // ---------- 5. Camadas ----------
  const camadasVis = { brinquedos: true, muros: true, cenario: true, etiquetas: true };
  function aplicarCamadas() {
    const g = sb.getGroup();
    if (g) g.visible = camadasVis.brinquedos;
    const amb = sb.scene.getObjectByName("ambiente-sketchbuild");
    for (const o of amb?.children || []) {
      if (o.userData.muro) o.visible = camadasVis.muros;
      else if (!["entorno"].includes(o.name) && !o.isLineSegments && !(o.isMesh && o.geometry?.type === "PlaneGeometry")) o.visible = camadasVis.cenario;
    }
    grupoEtiquetas.visible = camadasVis.etiquetas;
  }
  function camadas() {
    const nomes = { brinquedos: "Objetos 3D / Componentes", muros: "Muros e Paredes", cenario: "Cenário (árvores, pessoas, muretas)", etiquetas: "Etiquetas" };
    const itens = Object.entries(nomes).map(([k, n]) => {
      const cb = el("input", { type: "checkbox", checked: camadasVis[k], onchange: () => { camadasVis[k] = cb.checked; aplicarCamadas(); } });
      return el("label", { className: "pk-fer-check" }, cb, ` ${n}`);
    });
    abrir("camadas", dica("Desmarque pra esconder (só na tela, nada é apagado)."), ...itens);
  }

  // ---------- 6. Sol ----------
  // Posicao do sol (formula da NOAA, simplificada): azimute e elevacao pela
  // data, hora local (Brasil, UTC-3) e latitude/longitude.
  function posicaoSol(data, hora, lat, lon) {
    const dia = Math.floor((data - new Date(data.getFullYear(), 0, 0)) / 864e5);
    const g = (2 * Math.PI / 365) * (dia - 1 + (hora - 12) / 24);
    const eqt = 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g) - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
    const decl = 0.006918 - 0.399912 * Math.cos(g) + 0.070257 * Math.sin(g) - 0.006758 * Math.cos(2 * g) + 0.000907 * Math.sin(2 * g);
    const tst = hora * 60 + eqt + 4 * lon - 60 * -3;
    const ha = THREE.MathUtils.degToRad(tst / 4 - 180);
    const la = THREE.MathUtils.degToRad(lat);
    const cosZen = Math.sin(la) * Math.sin(decl) + Math.cos(la) * Math.cos(decl) * Math.cos(ha);
    const zen = Math.acos(Math.min(Math.max(cosZen, -1), 1));
    let az = Math.acos(Math.min(Math.max((Math.sin(la) * Math.cos(zen) - Math.sin(decl)) / (Math.cos(la) * Math.sin(zen)), -1), 1));
    az = ha > 0 ? az + Math.PI : Math.PI - az; // a partir do norte, sentido horario
    return { elevacao: Math.PI / 2 - zen, azimute: az };
  }
  function aplicarSol() {
    const s = esp()?.sol;
    if (!s?.ligado) return;
    const [lat, lon] = CIDADES[s.cidade] || CIDADES["Sousa-PB"];
    const [h, m] = (s.hora || "15:00").split(":").map(Number);
    const { elevacao, azimute } = posicaoSol(new Date(`${s.data}T12:00:00`), h + m / 60, lat, lon);
    const luz = sb.keyLight;
    const r = 40;
    // norte = -Z na cena (fundo do espaco), leste = +X
    luz.position.set(Math.sin(azimute) * Math.cos(elevacao) * r, Math.max(Math.sin(elevacao), 0.02) * r, -Math.cos(azimute) * Math.cos(elevacao) * r);
    luz.target.position.set(0, 0, 0);
    luz.target.updateMatrixWorld();
    luz.intensity = elevacao > 0 ? 1.6 : 0.05;
    const e = esp();
    const meia = Math.max(e.w || 20, e.l || 20) / 2 + 6;
    Object.assign(luz.shadow.camera, { left: -meia, right: meia, top: meia, bottom: -meia, far: 120 });
    luz.shadow.camera.updateProjectionMatrix();
    luz.shadow.mapSize.set(2048, 2048);
    luz.shadow.map?.dispose();
    luz.shadow.map = null;
    sb.setShadowsEnabled(true);
    sb.scene.traverse((o) => { if (o.isMesh && !o.isSprite) { o.castShadow = o.name !== "entorno"; o.receiveShadow = true; } });
    return elevacao;
  }
  function sol() {
    const e = esp();
    if (!e) return sb.setStatus("Crie o espaço primeiro (Novo espaço).", true);
    e.sol = { ligado: false, cidade: "Sousa-PB", data: new Date().toISOString().slice(0, 10), hora: "15:00", ...(e.sol || {}) };
    const s = e.sol;
    const cidade = el("select", { onchange: () => { s.cidade = cidade.value; mudou(); } },
      ...Object.keys(CIDADES).map((c) => el("option", { value: c, textContent: c, selected: c === s.cidade })));
    const data = el("input", { type: "date", value: s.data, onchange: () => { s.data = data.value; mudou(); } });
    const hora = el("input", { type: "range", min: "5", max: "18.5", step: "0.25", value: String(horaNum(s.hora)), oninput: () => { s.hora = horaTxt(+hora.value); rot.textContent = s.hora; mudou(); } });
    const rot = el("b", { textContent: s.hora });
    const liga = el("input", { type: "checkbox", checked: s.ligado, onchange: () => { s.ligado = liga.checked; if (!s.ligado) { sb.setShadowsEnabled(false); sb.keyLight.position.set(5, 8, 5); sb.keyLight.intensity = 1.2; } mudou(); } });
    function mudou() {
      const elev = aplicarSol();
      if (s.ligado && elev !== undefined && elev <= 0) sb.setStatus("Nesse horário o sol já se pôs.");
      ctx.guardar();
    }
    abrir("sol",
      el("label", { className: "pk-fer-check" }, liga, " Sombra real ligada"),
      el("label", { className: "pk-fer-campo" }, "Cidade ", cidade),
      el("label", { className: "pk-fer-campo" }, "Data ", data),
      el("label", { className: "pk-fer-campo" }, "Hora ", rot, hora),
      dica("Mostra onde bate sombra no parquinho na hora de uso."));
  }
  const horaNum = (t) => { const [h, m] = String(t).split(":").map(Number); return h + (m || 0) / 60; };
  const horaTxt = (n) => `${String(Math.floor(n)).padStart(2, "0")}:${String(Math.round((n % 1) * 60)).padStart(2, "0")}`;

  // ---------- 7. Lista do projeto ----------
  function lista() {
    const itens = ctx.brinquedos();
    const ul = el("div", { className: "pk-fer-lista" });
    if (!itens.length) ul.append(dica("Nenhum brinquedo ainda."));
    for (const b of itens) {
      const malhas = ctx.malhasDe(b.id);
      const visivel = malhas.every((m) => m.visible);
      ul.append(el("div", { className: "pk-fer-linha" },
        botao(b.nome, () => { if (malhas[0]) sb.selectMesh(malhas[0]); }, "pk-fer-nome"),
        botao(visivel ? "👁" : "◌", () => { malhas.forEach((m) => (m.visible = !visivel)); lista(); }, "pk-fer-mini")));
    }
    abrir("lista", dica("Clique no nome pra selecionar. O olho esconde só na tela."), ul);
  }

  // ---------- 8. Corte ----------
  const plano = new THREE.Plane(new THREE.Vector3(0, -1, 0), 100);
  function corte() {
    const r = sb.renderer;
    const tipo = el("select", {}, el("option", { value: "altura", textContent: "Na altura (de cima)" }), el("option", { value: "comprimento", textContent: "No comprimento (de lado)" }));
    const faixa = el("input", { type: "range", min: "0", max: "100", value: "100" });
    const rot = el("b", { textContent: "sem corte" });
    function aplicar() {
      const v = +faixa.value / 100;
      if (v >= 1) { r.clippingPlanes = []; rot.textContent = "sem corte"; return; }
      const caixa = new THREE.Box3().setFromObject(sb.getGroup() || sb.scene);
      if (tipo.value === "altura") {
        const h = caixa.min.y + (caixa.max.y - caixa.min.y) * v;
        plano.normal.set(0, -1, 0); plano.constant = h;
        rot.textContent = `${h.toFixed(2).replace(".", ",")} m de altura`;
      } else {
        const z = caixa.min.z + (caixa.max.z - caixa.min.z) * v;
        plano.normal.set(0, 0, -1); plano.constant = z;
        rot.textContent = "corte no comprimento";
      }
      r.clippingPlanes = [plano];
    }
    faixa.oninput = aplicar;
    tipo.onchange = aplicar;
    abrir("corte",
      el("label", { className: "pk-fer-campo" }, "Tipo ", tipo),
      el("label", { className: "pk-fer-campo" }, rot, faixa),
      el("div", { className: "pk-cen-acoes" }, botao("Tirar o corte", () => { faixa.value = "100"; aplicar(); })));
  }

  // ---------- 9. Estilo ----------
  let estiloAtual = "normal";
  function aplicarEstilo(nome) {
    estiloAtual = nome;
    const g = sb.getGroup();
    g?.traverse((o) => {
      if (!o.isMesh) return;
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) {
        if (!m) continue;
        m.userData.orig ??= { cor: m.color?.clone(), transparent: m.transparent, opacity: m.opacity, depthWrite: m.depthWrite };
        const o0 = m.userData.orig;
        m.transparent = nome === "raio-x" ? true : o0.transparent;
        m.opacity = nome === "raio-x" ? 0.3 : o0.opacity;
        m.depthWrite = nome === "raio-x" ? false : o0.depthWrite;
        if (m.color && o0.cor) m.color.copy(nome === "traco" ? new THREE.Color(0xffffff) : nome === "mono" ? new THREE.Color(0xc9ced6) : o0.cor);
        m.needsUpdate = true;
      }
      const tem = o.children.find((c) => c.userData.contorno);
      if (nome === "traco" && !tem) {
        const l = new THREE.LineSegments(new THREE.EdgesGeometry(o.geometry, 30), new THREE.LineBasicMaterial({ color: 0x222222 }));
        l.userData.contorno = true;
        l.raycast = () => {};
        o.add(l);
      }
      if (tem) tem.visible = nome === "traco";
    });
  }
  function estilo() {
    const op = (v, n) => botao(n, () => { aplicarEstilo(v); estilo(); }, v === estiloAtual ? "primario" : "");
    abrir("estilo", el("div", { className: "pk-fer-grade" },
      op("normal", "Normal"), op("traco", "Traço (croqui)"), op("raio-x", "Raio-X"), op("mono", "Monocromático")),
      dica("Muda só a tela e a foto; as cores do projeto continuam salvas."));
  }

  // ---------- 10. Passeio ----------
  function passeio() {
    const altura = (h) => () => {
      fechar();
      const c = sb.camera;
      c.position.y = h;
      sb.controls.target.y = h;
      sb.controls.update();
      sb.startWalk();
    };
    abrir("passeio",
      dica("W/A/S/D ou setas pra andar, o mouse olha em volta, Esc sai."),
      el("div", { className: "pk-cen-acoes" }, botao("Criança (1,10 m)", altura(1.1)), botao("Adulto (1,65 m)", altura(1.65), "primario")));
  }

  // projeto aberto/trocado: desenha o que veio salvo nele
  let ultimo = null;
  setInterval(() => {
    const e = esp();
    const chave = e ? `${JSON.stringify(e.etiquetas || [])}|${JSON.stringify(e.sol || {})}` : "";
    if (e === ultimo?.e && chave === ultimo?.chave) return;
    const trocou = e !== ultimo?.e;
    ultimo = { e, chave };
    desenharEtiquetas();
    if (trocou) {
      if (e?.sol?.ligado) aplicarSol();
      aplicarCamadas();
      if (estiloAtual !== "normal") aplicarEstilo(estiloAtual);
    }
  }, 800);
  window.addEventListener("sb:scene", () => setTimeout(() => {
    aplicarCamadas();
    if (estiloAtual !== "normal") aplicarEstilo(estiloAtual);
    if (esp()?.sol?.ligado) aplicarSol();
  }, 50));
}
