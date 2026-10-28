import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { TransformControls } from "three/addons/controls/TransformControls.js";
import { FontLoader } from "three/addons/loaders/FontLoader.js";
import { TextGeometry } from "three/addons/geometries/TextGeometry.js";

import {
  openScene,
  newSceneFromTemplate,
  updateInstanceTransform,
  saveScene,
  deleteInstance,
  exportModelObj,
  addRectangle,
  paintInstance,
  paintFace,
  tagInstance,
  listScenePages,
  createScenePage,
  activateScenePage,
  listTags,
  setTagVisibility,
  setInstanceAxes,
  listRecentFiles,
  uploadThumbnail,
  getCurrentSession,
  listAutosaveDrafts,
  recoverAutosaveDraft,
  discardAutosaveDraft,
  ApiError,
} from "./api.js";
import { buildSceneGroup, meshMatrixToApiTransform, worldPointToLocalInches } from "./sceneBuilder.js";
import { buildOutlinerTree } from "./outliner.js";
import { renderRecentFiles, renderAutosaveDrafts } from "./welcome.js";

const viewportEl = document.getElementById("viewport");
const pathInputEl = document.getElementById("path-input");
const openBtnEl = document.getElementById("open-btn");
const statusEl = document.getElementById("status");
const editPanelEl = document.getElementById("edit-panel");
const selectedLabelEl = document.getElementById("selected-label");
const savePathInputEl = document.getElementById("save-path-input");
const saveBtnEl = document.getElementById("save-btn");
const toolbarSaveBtnEl = document.getElementById("toolbar-save-btn");
const exportObjPathInputEl = document.getElementById("export-obj-path-input");
const exportObjBtnEl = document.getElementById("export-obj-btn");
const rectWidthInputEl = document.getElementById("rect-width-input");
const rectHeightInputEl = document.getElementById("rect-height-input");
const rectCreateBtnEl = document.getElementById("rect-create-btn");
const rectAsGroupCheckboxEl = document.getElementById("rect-as-group-checkbox");
const textContentInputEl = document.getElementById("text-content-input");
const paintColorInputEl = document.getElementById("paint-color-input");
const tagNameInputEl = document.getElementById("tag-name-input");
const toolsToolbarEl = document.getElementById("tools-toolbar");
const toolIconBtnEls = document.querySelectorAll(".tool-icon-btn");
const vcbEl = document.getElementById("vcb");
const vcbRectEl = document.getElementById("vcb-rect");
const vcbTagEl = document.getElementById("vcb-tag");
const vcbPaintEl = document.getElementById("vcb-paint");
const vcbTextEl = document.getElementById("vcb-text");
const sceneNameInputEl = document.getElementById("scene-name-input");
const sceneCreateBtnEl = document.getElementById("scene-create-btn");
const scenePagesListEl = document.getElementById("scene-pages-list");
const tagsListEl = document.getElementById("tags-list");
const tagsEmptyEl = document.getElementById("tags-empty");
const menuTopItemEls = document.querySelectorAll(".menu-top-item[data-menu]");
const defaultTrayEl = document.getElementById("default-tray");
const outlinerTreeEl = document.getElementById("outliner-tree");
const viewBtnEls = document.querySelectorAll(".view-btn");
const entityInfoEl = document.getElementById("entity-info");
const entityInfoEmptyEl = document.getElementById("entity-info-empty");
const trayHeaderEls = document.querySelectorAll(".tray-header");
const posXEl = document.getElementById("pos-x");
const posYEl = document.getElementById("pos-y");
const posZEl = document.getElementById("pos-z");
const rotXEl = document.getElementById("rot-x");
const rotYEl = document.getElementById("rot-y");
const rotZEl = document.getElementById("rot-z");
const welcomeScreenEl = document.getElementById("welcome-screen");
const welcomeCloseBtnEl = document.getElementById("welcome-close-btn");
const welcomeOpenBtnEl = document.getElementById("welcome-open-btn");
const welcomeOpenRowEl = document.getElementById("welcome-open-row");
const welcomePathInputEl = document.getElementById("welcome-path-input");
const welcomeOpenConfirmBtnEl = document.getElementById("welcome-open-confirm-btn");
const welcomeRecentGridEl = document.getElementById("welcome-recent-grid");
const welcomeAutosaveSectionEl = document.getElementById("welcome-autosave-section");
const welcomeAutosaveGridEl = document.getElementById("welcome-autosave-grid");
const welcomeTemplateCardEls = document.querySelectorAll(
  ".welcome-template-card[data-template-id]"
);

const scene = new THREE.Scene();

// Fundo "ceu" degrade + chao solido, reproduzindo o estilo padrao do
// SketchUp Desktop (cores reais extraidas via screenshot do SketchUp 2026
// rodando nesta mesma maquina -- ver REVERSE_ENGINEERING_NOTES.md secao
// 25). O ceu e so um degrade em screen-space (THREE.Scene.background com
// um Texture simples nao acompanha a orientacao da camera) -- suficiente
// pros angulos de camera deste visualizador; o chao, esse sim, e uma
// malha 3D de verdade e recebe perspectiva/paralaxe normal ao orbitar.
function createSkyTexture() {
  const canvas = document.createElement("canvas");
  canvas.width = 2;
  canvas.height = 256;
  const ctx = canvas.getContext("2d");
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "#40B3E2");
  gradient.addColorStop(1, "#BFE5F5");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  return new THREE.CanvasTexture(canvas);
}
scene.background = createSkyTexture();

// MeshStandardMaterial (em vez de MeshBasicMaterial) so pra poder receber
// sombra quando "Visualizar > Sombras" estiver ligado -- material Basic
// nunca participa do shadow map do three.js. Mesma cor/aparencia de antes.
const groundPlane = new THREE.Mesh(
  new THREE.PlaneGeometry(4000, 4000),
  new THREE.MeshStandardMaterial({ color: 0xBFBFC6, side: THREE.DoubleSide, roughness: 1, metalness: 0 })
);
groundPlane.rotation.x = -Math.PI / 2; // PlaneGeometry nasce no plano XY -- deita no XZ (chao, Y=0 pra cima)
groundPlane.receiveShadow = true;
scene.add(groundPlane);

const camera = new THREE.PerspectiveCamera(
  50,
  window.innerWidth / window.innerHeight,
  0.01,
  1000
);
camera.position.set(3, 3, 3);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.localClippingEnabled = true; // Ferramentas > Plano de secao (THREE.Plane real)
viewportEl.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

const transformControls = new TransformControls(camera, renderer.domElement);
scene.add(transformControls.getHelper());

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
keyLight.position.set(5, 8, 5);
// Frustum/resolucao fixos do shadow camera -- simplificacao conhecida (nao
// se adapta ao tamanho real de cada modelo carregado, ver REVERSE_ENGINEERING_NOTES.md
// secao 27); cobre bem os modelos de escala domestica/arquitetonica usados nos testes.
keyLight.shadow.mapSize.set(1024, 1024);
keyLight.shadow.camera.left = -20;
keyLight.shadow.camera.right = 20;
keyLight.shadow.camera.top = 20;
keyLight.shadow.camera.bottom = -20;
keyLight.shadow.camera.near = 0.1;
keyLight.shadow.camera.far = 50;
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
fillLight.position.set(-5, 2, -5);
scene.add(fillLight);

// SketchUp real nao mostra grade no visualizador padrao -- so os 3 eixos
// RGB passando pela origem, solidos no sentido positivo e tracejados no
// negativo. Cores: vermelho=X, verde=Z nativo do SketchUp (mapeado pra
// Three.js Z, ver SKP_TO_THREE_UP em sceneBuilder.js), azul=Y (up).
const axisLines = []; // ver setAxesVisible() -- toggle de "Visualizar > Eixos"

function addAxisLine(color, direction, length = 100) {
  const positive = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), direction.clone().multiplyScalar(length)]),
    new THREE.LineBasicMaterial({ color })
  );
  scene.add(positive);
  axisLines.push(positive);

  const negative = new THREE.Line(
    new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), direction.clone().multiplyScalar(-length)]),
    new THREE.LineDashedMaterial({ color, dashSize: 0.3, gapSize: 0.2 })
  );
  negative.computeLineDistances();
  scene.add(negative);
  axisLines.push(negative);
}
addAxisLine(0xCC3333, new THREE.Vector3(1, 0, 0)); // vermelho = X
addAxisLine(0x3333CC, new THREE.Vector3(0, 1, 0)); // azul = Y (up)
addAxisLine(0x339933, new THREE.Vector3(0, 0, 1)); // verde = Z

let currentGroup = null;
let selectedMesh = null;
let suppressNextClick = false;
let currentOutliner = null; // { element, setSelected } -- ver outliner.js

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

/** Modo da ferramenta de clique no viewport -- "select" (padrao: clique
 * seleciona, igual sempre funcionou), "erase" (Ferramentas > Apagar:
 * clique exclui na hora, mesmo SUEntitiesErase de handleDeleteSelected,
 * so sem passar pelo passo de selecionar+clicar Excluir) e "measure"
 * (Ferramentas > Fita metrica: dois cliques medem a distancia real em
 * metros entre os pontos, mostrada na barra de status). Ver
 * REVERSE_ENGINEERING_NOTES.md secao 28 (rodada de Ferramentas). */
let toolMode = "select";
let measureFirstPoint = null;
let protractorPoints = []; // Ferramentas > Transferidor: acumula ate 3 pontos (vertice + 2 lados)
let dimensionFirstPoint = null; // Ferramentas > Dimensoes: acumula 1 ponto antes de criar a cota 3D
let currentSceneDTO = null; // ultima cena aberta/criada -- usado por "Janela > Informacoes do modelo"
let lassoSelection = []; // Ferramentas > Laco: lista de meshes acumulados por cliques sucessivos
let loadedFont = null; // cache da fonte carregada pra "Ferramentas > Texto 3D"
let fontLoadPromise = null;
let axesPoints = []; // Ferramentas > Eixos: acumula 3 cliques (origem, direcao X, direcao Y)
let axesTargetMesh = null; // mesh do 1o clique -- define a instancia/definicao alvo dos outros 2

/** Carrega (uma vez, com cache) a fonte publica do CDN do Three.js
 * (mesmo CDN de onde a lib ja vem, ver index.html importmap) pra
 * "Ferramentas > Texto 3D" -- extrusao real de fonte em malha
 * (THREE.TextGeometry), nao e um sprite 2D como "Texto" (28.13). */
function loadFont() {
  if (!fontLoadPromise) {
    fontLoadPromise = new Promise((resolve, reject) => {
      new FontLoader().load(
        "https://cdn.jsdelivr.net/npm/three@0.169.0/examples/fonts/helvetiker_regular.typeface.json",
        (font) => {
          loadedFont = font;
          resolve(font);
        },
        undefined,
        reject
      );
    });
  }
  return fontLoadPromise;
}

/** Grupo dedicado as cotas 3D persistentes criadas por "Ferramentas >
 * Dimensoes" (linha + rotulo de texto) -- separado de currentGroup
 * porque nao vem do DTO/backend, e so anotacao visual local. */
const dimensionsGroup = new THREE.Group();
scene.add(dimensionsGroup);

/** Ferramentas > Laco: como o material e compartilhado por toda a cena
 * (group.userData.sharedMaterial), nao da pra "tingir" so as pecas
 * selecionadas via material -- usa um THREE.BoxHelper real (caixa
 * delimitadora) por peca, sem mexer no material. */
const lassoHelpersGroup = new THREE.Group();
scene.add(lassoHelpersGroup);

function setLassoSelection(meshes) {
  lassoSelection = meshes;
  lassoHelpersGroup.clear();
  meshes.forEach((mesh) => lassoHelpersGroup.add(new THREE.BoxHelper(mesh, 0xffaa00)));
  if (toolMode === "lasso") {
    setStatus(
      meshes.length
        ? `${meshes.length} peca(s) selecionada(s) (Laco). Use "Excluir (Del)" pra excluir todas.`
        : "Modo Laco: va clicando em varias pecas. Esc limpa."
    );
  }
}

/** THREE.Plane real usado por "Ferramentas > Plano de secao" -- corta
 * de verdade a geometria renderizada (WebGL clipping nativo), nao e um
 * efeito falso. Aplicado no material compartilhado de cada cena aberta
 * (ver group.userData.sharedMaterial em sceneBuilder.js). */
let sectionPlane = null;

/** Sincroniza o icone ativo na "Large Tool Set" (#tools-toolbar) e a
 * caixa contextual (#vcb, "Value Control Box") com o toolMode/modo do
 * gizmo atuais -- mesmo padrao visual do SketchUp real: so um icone
 * destacado por vez, so os campos da ferramenta ativa visiveis. */
function syncToolUI(activeKey) {
  toolIconBtnEls.forEach((btn) => btn.classList.toggle("active", btn.dataset.toolMode === activeKey));
  const fields = [
    [vcbRectEl, activeKey === "rect"],
    [vcbTagEl, activeKey === "tag"],
    [vcbPaintEl, activeKey === "paint" || activeKey === "paintFace"],
    [vcbTextEl, activeKey === "text" || activeKey === "text3d"],
  ];
  let any = false;
  fields.forEach(([el, visible]) => {
    el.classList.toggle("visible", visible);
    if (visible) any = true;
  });
  vcbEl.classList.toggle("visible", any);
}

function setToolMode(mode) {
  toolMode = mode;
  measureFirstPoint = null;
  protractorPoints = [];
  dimensionFirstPoint = null;
  axesPoints = [];
  axesTargetMesh = null;
  if (mode !== "lasso") setLassoSelection([]);
  if (mode === "erase") setStatus("Modo Apagar: clique numa peca pra excluir na hora.");
  else if (mode === "measure") setStatus("Modo Fita metrica: clique no primeiro ponto.");
  else if (mode === "protractor") setStatus("Modo Transferidor: clique no vertice do angulo.");
  else if (mode === "section") setStatus("Modo Plano de secao: clique num ponto pra cortar o modelo nessa altura.");
  else if (mode === "dimension") setStatus("Modo Dimensoes: clique no primeiro ponto da cota.");
  else if (mode === "text") setStatus("Modo Texto: escreva o conteudo na caixa no canto inferior direito e clique no viewport pra posicionar.");
  else if (mode === "text3d") setStatus("Modo Texto 3D: escreva o conteudo na caixa no canto inferior direito e clique no viewport (carregando fonte na 1a vez).");
  else if (mode === "lasso") { lassoSelection = []; setStatus("Modo Laco: va clicando em varias pecas (Shift+clique tambem funciona). Esc limpa."); }
  else if (mode === "paint") setStatus("Modo Pintura: escolha a cor na caixa no canto inferior direito e clique numa peca.");
  else if (mode === "paintFace") setStatus("Modo Pintura por face: escolha a cor na caixa no canto inferior direito e clique numa FACE (afeta todas as instancias da mesma peca no arquivo).");
  else if (mode === "tag") setStatus("Modo Etiqueta: escreva o nome na caixa no canto inferior direito e clique numa peca.");
  else if (mode === "axes") setStatus("Modo Eixos: clique na peca pra definir a ORIGEM dos eixos novos.");
  else if (mode === "rect") setStatus("Modo Retangulo: informe largura/profundidade na caixa no canto inferior direito e clique em Criar.");
  else setStatus("Modo Selecionar.");
  syncToolUI(mode);
}

function setMode(mode) {
  toolMode = "select"; // mover/girar/escalar precisam do modo de selecao pra funcionar
  transformControls.setMode(mode);
  syncToolUI(mode);
}

/** Reflete posicao (metros)/rotacao (graus) do mesh selecionado nos campos
 * numericos do painel "Entity Info" -- so leitura, nao dispara eventos. */
function updateEntityInfoDisplay(mesh) {
  if (!mesh) {
    entityInfoEl.classList.add("hidden");
    entityInfoEmptyEl.classList.remove("hidden");
    return;
  }
  entityInfoEl.classList.remove("hidden");
  entityInfoEmptyEl.classList.add("hidden");
  posXEl.value = mesh.position.x.toFixed(3);
  posYEl.value = mesh.position.y.toFixed(3);
  posZEl.value = mesh.position.z.toFixed(3);
  rotXEl.value = THREE.MathUtils.radToDeg(mesh.rotation.x).toFixed(1);
  rotYEl.value = THREE.MathUtils.radToDeg(mesh.rotation.y).toFixed(1);
  rotZEl.value = THREE.MathUtils.radToDeg(mesh.rotation.z).toFixed(1);
}

function selectMesh(mesh) {
  if (selectedMesh === mesh) return;
  selectedMesh = mesh;
  // o mesh foi montado com matrixAutoUpdate=false e matriz composta
  // direto (ver sceneBuilder.js) -- o TransformControls le/escreve via
  // position/quaternion/scale, entao sincronizamos essas propriedades
  // com a matriz atual antes de ligar o controle e voltar a deixar o
  // three.js recalcular a matriz a partir delas.
  mesh.matrixAutoUpdate = true;
  mesh.matrix.decompose(mesh.position, mesh.quaternion, mesh.scale);
  transformControls.attach(mesh);
  selectedLabelEl.textContent = `Selecionado: ${mesh.name}`;
  currentOutliner?.setSelected(mesh.name);
  updateEntityInfoDisplay(mesh);
}

function deselectMesh() {
  transformControls.detach();
  selectedMesh = null;
  selectedLabelEl.textContent = "Nenhuma instancia selecionada.";
  currentOutliner?.setSelected(null);
  updateEntityInfoDisplay(null);
}

/** Seleciona pelo instance_id (vindo de um clique no Outliner) -- nem toda
 * instancia tem Mesh proprio (ex.: "root", definicoes sem geometria), entao
 * so liga o gizmo quando ha malha de verdade pra anexar. */
function selectInstanceById(instanceId) {
  const mesh = currentGroup?.getObjectByName(instanceId);
  if (mesh) {
    selectMesh(mesh);
  } else {
    transformControls.detach();
    selectedMesh = null;
    selectedLabelEl.textContent = `Selecionado: ${instanceId} (sem geometria propria/nao editavel)`;
    currentOutliner?.setSelected(instanceId);
    updateEntityInfoDisplay(null);
  }
}

/** Le os campos numericos do painel e aplica no mesh selecionado -- mesmo
 * caminho do gizmo (updateMatrix + PATCH via applyTransformEdit). */
function applyEntityInfoInputs() {
  if (!selectedMesh) return;
  selectedMesh.position.set(
    parseFloat(posXEl.value) || 0,
    parseFloat(posYEl.value) || 0,
    parseFloat(posZEl.value) || 0
  );
  selectedMesh.rotation.set(
    THREE.MathUtils.degToRad(parseFloat(rotXEl.value) || 0),
    THREE.MathUtils.degToRad(parseFloat(rotYEl.value) || 0),
    THREE.MathUtils.degToRad(parseFloat(rotZEl.value) || 0)
  );
  applyTransformEdit(selectedMesh);
}

[posXEl, posYEl, posZEl, rotXEl, rotYEl, rotZEl].forEach((input) => {
  input.addEventListener("change", applyEntityInfoInputs);
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") input.blur(); // dispara "change" e tira o foco
  });
});

async function applyTransformEdit(mesh) {
  mesh.updateMatrix();
  const apiTransform = meshMatrixToApiTransform(mesh.matrix);
  try {
    await updateInstanceTransform(mesh.name, apiTransform);
    setStatus(`Transformacao de ${mesh.name} aplicada na sessao (ainda nao salva em disco).`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao aplicar transformacao: ${detail}`, true);
  }
}

transformControls.addEventListener("objectChange", () => {
  if (selectedMesh) updateEntityInfoDisplay(selectedMesh);
});

transformControls.addEventListener("dragging-changed", (event) => {
  controls.enabled = !event.value;
  if (!event.value) {
    suppressNextClick = true;
    setTimeout(() => {
      suppressNextClick = false;
    }, 0);
    if (selectedMesh) applyTransformEdit(selectedMesh);
  }
});

renderer.domElement.addEventListener("click", (event) => {
  if (suppressNextClick) {
    suppressNextClick = false;
    return;
  }
  if (!currentGroup) return;

  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);

  const hits = raycaster.intersectObjects(currentGroup.children, false);

  if (toolMode === "erase") {
    if (hits.length) handleEraseClick(hits[0].object);
    return;
  }
  if (toolMode === "measure") {
    if (hits.length) handleMeasureClick(hits[0].point);
    return;
  }
  if (toolMode === "protractor") {
    if (hits.length) handleProtractorClick(hits[0].point);
    return;
  }
  if (toolMode === "section") {
    if (hits.length) handleSectionClick(hits[0].point);
    return;
  }
  if (toolMode === "dimension") {
    if (hits.length) handleDimensionClick(hits[0].point);
    return;
  }
  if (toolMode === "text") {
    if (hits.length) handleTextClick(hits[0].point);
    return;
  }
  if (toolMode === "text3d") {
    if (hits.length) handleText3DClick(hits[0].point);
    return;
  }
  if (toolMode === "lasso") {
    if (hits.length) handleLassoClick(hits[0].object);
    return;
  }
  if (toolMode === "paint") {
    if (hits.length) handlePaintClick(hits[0].object);
    return;
  }
  if (toolMode === "paintFace") {
    if (hits.length) handlePaintFaceClick(hits[0]);
    return;
  }
  if (toolMode === "tag") {
    if (hits.length) handleTagClick(hits[0].object);
    return;
  }
  if (toolMode === "axes") {
    if (hits.length) handleAxesClick(hits[0]);
    return;
  }

  if (hits.length) {
    selectMesh(hits[0].object);
  } else {
    deselectMesh();
  }
});

/** Ferramentas > Apagar: exclui direto a peca clicada (mesmo caminho real
 * de handleDeleteSelected/SUEntitiesErase), sem precisar selecionar
 * primeiro. Some do viewport e, se era a selecionada, desliga o gizmo. */
async function handleEraseClick(mesh) {
  try {
    await deleteInstance(mesh.name);
    if (selectedMesh === mesh) deselectMesh();
    currentGroup.remove(mesh);
    setStatus(`${mesh.name} excluido (ainda nao salvo em disco). Modo Apagar continua ativo.`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao excluir: ${detail}`, true);
  }
}

/** Ferramentas > Fita metrica: acumula 2 cliques em pontos reais da
 * geometria (espaco de mundo, metros) e mostra a distancia euclidiana
 * na barra de status -- so leitura, nao toca a sessao/backend. */
function handleMeasureClick(worldPoint) {
  if (!measureFirstPoint) {
    measureFirstPoint = worldPoint.clone();
    setStatus("Modo Fita metrica: clique no segundo ponto.");
    return;
  }
  const distance = measureFirstPoint.distanceTo(worldPoint);
  setStatus(`Distancia medida: ${distance.toFixed(3)} m. Clique no proximo primeiro ponto.`);
  measureFirstPoint = null;
}

/** Ferramentas > Transferidor: acumula 3 cliques reais na geometria
 * (vertice do angulo, depois um ponto em cada lado) e calcula o angulo
 * real entre os dois vetores formados -- so leitura, mesma logica real
 * de medicao da Fita metrica, nao toca sessao/backend. */
function handleProtractorClick(worldPoint) {
  protractorPoints.push(worldPoint.clone());
  if (protractorPoints.length === 1) {
    setStatus("Modo Transferidor: clique no primeiro lado do angulo.");
    return;
  }
  if (protractorPoints.length === 2) {
    setStatus("Modo Transferidor: clique no segundo lado do angulo.");
    return;
  }
  const [vertex, side1, side2] = protractorPoints;
  const v1 = side1.clone().sub(vertex);
  const v2 = side2.clone().sub(vertex);
  const angleDeg = THREE.MathUtils.radToDeg(v1.angleTo(v2));
  setStatus(`Angulo medido: ${angleDeg.toFixed(1)}°. Clique no proximo vertice.`);
  protractorPoints = [];
}

window.addEventListener("keydown", (event) => {
  const tag = event.target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA") return; // nao rouba atalho de quem esta digitando

  if (event.key === "w" || event.key === "W") setMode("translate");
  else if (event.key === "e" || event.key === "E") setMode("rotate");
  else if (event.key === "r" || event.key === "R") setMode("scale");
  else if (event.key === "Escape") {
    deselectMesh();
    if (toolMode === "lasso") setLassoSelection([]);
  }
  else if (event.key === "Delete" || event.key === "Backspace") handleDeleteSelected();
});

setMode("translate");

// Direcao (a partir do centro do modelo) + vetor "up" da camera pra cada
// vista padrao. "top" usa up=(0,0,-1) em vez do (0,1,0) default -- quando
// a direcao de visao e paralela ao up, o OrbitControls degenera (gimbal
// lock nas coordenadas esfericas internas); com um up perpendicular a
// vista fica estavel e orbitavel normalmente.
// As 7 vistas padrao reais do menu "Câmera > Exibições padrão" (catalogadas
// via clique no SketchUp 2026 rodando na maquina -- ver
// REVERSE_ENGINEERING_NOTES.md secao 27); antes so 4 estavam disponiveis.
// "alto"/"inferior" usam up perpendicular (0,0,±1) pelo mesmo motivo de
// sempre: direcao de vista paralela ao up padrao degenera o OrbitControls.
const STANDARD_VIEWS = {
  alto: { direction: new THREE.Vector3(0, 1, 0), up: new THREE.Vector3(0, 0, -1) },
  inferior: { direction: new THREE.Vector3(0, -1, 0), up: new THREE.Vector3(0, 0, 1) },
  frontal: { direction: new THREE.Vector3(0, 0, 1), up: new THREE.Vector3(0, 1, 0) },
  posterior: { direction: new THREE.Vector3(0, 0, -1), up: new THREE.Vector3(0, 1, 0) },
  esquerda: { direction: new THREE.Vector3(-1, 0, 0), up: new THREE.Vector3(0, 1, 0) },
  direita: { direction: new THREE.Vector3(1, 0, 0), up: new THREE.Vector3(0, 1, 0) },
  iso: { direction: new THREE.Vector3(1, 0.8, 1), up: new THREE.Vector3(0, 1, 0) },
};

// -- Câmera > Projeção paralela / Perspectiva ------------------------------
// Three.js nao permite trocar o TIPO de uma PerspectiveCamera em tempo real
// sem recriar OrbitControls/raycaster/render target apontando pra outra
// camera -- em vez disso usamos a aproximacao classica de "projecao
// paralela falsa": FOV bem estreito (quase 0) + camera bem afastada do
// alvo, compensando a distancia pra manter o enquadramento do mesmo
// tamanho. Nao e uma Orthographic de verdade (ver REVERSE_ENGINEERING_NOTES.md
// secao 27), mas visualmente equivalente pros angulos deste visualizador.
const PERSPECTIVE_FOV = 50;
const PARALLEL_FOV = 1;
let projectionMode = "perspective";

function projectionDistanceScale() {
  return projectionMode === "parallel"
    ? Math.tan(THREE.MathUtils.degToRad(PERSPECTIVE_FOV / 2)) / Math.tan(THREE.MathUtils.degToRad(PARALLEL_FOV / 2))
    : 1;
}

/** Reposiciona a camera/controls instantaneamente numa vista padrao,
 * centralizada na bounding box do grupo carregado. */
function setStandardView(viewName) {
  if (!currentGroup) return;
  const { direction, up } = STANDARD_VIEWS[viewName];

  const box = new THREE.Box3().setFromObject(currentGroup);
  if (box.isEmpty()) return;

  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const radius = Math.max(size.length() / 2, 0.1);
  const distance = radius * 2.2 * projectionDistanceScale();

  camera.up.copy(up);
  controls.target.copy(center);
  camera.position.copy(center).addScaledVector(direction.clone().normalize(), distance);
  camera.near = radius / 100;
  camera.far = Math.max(radius * 100, distance * 2);
  camera.updateProjectionMatrix();
  controls.update();
}

viewBtnEls.forEach((btn) => {
  btn.addEventListener("click", () => setStandardView(btn.dataset.view));
});

function setProjectionMode(mode) {
  if (mode === projectionMode) return;
  const center = currentGroup
    ? new THREE.Box3().setFromObject(currentGroup).getCenter(new THREE.Vector3())
    : controls.target.clone();
  const dir = camera.position.clone().sub(center).normalize();
  const currentDist = camera.position.distanceTo(center);
  const baseDist = currentDist / projectionDistanceScale(); // despe a escala atual antes de reaplicar a nova

  projectionMode = mode;
  camera.fov = mode === "parallel" ? PARALLEL_FOV : PERSPECTIVE_FOV;
  const newDist = baseDist * projectionDistanceScale();
  camera.position.copy(center).addScaledVector(dir, newDist);
  camera.far = Math.max(camera.far, newDist * 2);
  camera.updateProjectionMatrix();
  controls.update();

  document.getElementById("menu-item-proj-parallel").classList.toggle("is-checked", mode === "parallel");
  document.getElementById("menu-item-proj-perspective").classList.toggle("is-checked", mode === "perspective");
}

/** "Câmera > Campo de visão..." -- dialogo nativo do navegador (window.prompt),
 * igual aos dialogos "..." do SketchUp real. ATENCAO: prompts bloqueiam a
 * automacao via Claude in Chrome (ver guidelines de testes) -- esse item nao
 * foi clicado nos testes automatizados por esse motivo, so os demais. */
function handleFieldOfView() {
  const current = Math.round(camera.fov);
  const input = window.prompt("Campo de visão (graus, 1-150):", String(current));
  if (input === null) return;
  const fov = parseFloat(input);
  if (!Number.isFinite(fov) || fov <= 0 || fov >= 150) {
    setStatus("Campo de visão inválido.", true);
    return;
  }
  projectionMode = "perspective";
  document.getElementById("menu-item-proj-perspective").classList.add("is-checked");
  document.getElementById("menu-item-proj-parallel").classList.remove("is-checked");
  camera.fov = fov;
  camera.updateProjectionMatrix();
}

// -- Visualizar > Eixos / Sombras / Névoa / Estilo de aresta / Estilo de face --
// Catalogados via clique real no SketchUp 2026 (ver REVERSE_ENGINEERING_NOTES.md
// secao 27). Cada toggle muta estado global (luzes/fog/materia-prima
// compartilhada) em vez de reconstruir a cena.
let axesVisible = true;
let shadowsEnabled = false;
let fogEnabled = false;
let edgesVisible = false;
let faceStyle = "textured"; // textured | flat | monochrome | wireframe | xray

function setAxesVisible(visible) {
  axesVisible = visible;
  axisLines.forEach((line) => (line.visible = visible));
  document.getElementById("menu-item-axes").classList.toggle("is-checked", visible);
}

function setShadowsEnabled(enabled) {
  shadowsEnabled = enabled;
  renderer.shadowMap.enabled = enabled;
  keyLight.castShadow = enabled;
  document.getElementById("menu-item-shadows").classList.toggle("is-checked", enabled);
  // mesmo toggle, acessivel tambem via Janela > Bandeja padrao > Sombras
  document.getElementById("menu-item-tray-shadows")?.classList.toggle("is-checked", enabled);
}

function setFogEnabled(enabled) {
  fogEnabled = enabled;
  scene.fog = enabled ? new THREE.Fog(0xBFE5F5, 10, 200) : null;
  document.getElementById("menu-item-fog").classList.toggle("is-checked", enabled);
  // mesmo toggle, acessivel tambem via Janela > Bandeja padrao > Névoa
  document.getElementById("menu-item-tray-fog")?.classList.toggle("is-checked", enabled);
}

function setEdgesVisible(visible) {
  edgesVisible = visible;
  if (currentGroup) {
    for (const mesh of currentGroup.children) {
      if (mesh.userData.edgesMesh) mesh.userData.edgesMesh.visible = visible;
    }
  }
  document.getElementById("menu-item-edges").classList.toggle("is-checked", visible);
}

const FACE_STYLE_MENU_IDS = {
  textured: "menu-item-face-textured",
  flat: "menu-item-face-flat",
  monochrome: "menu-item-face-monochrome",
  wireframe: "menu-item-face-wireframe",
  xray: "menu-item-face-xray",
};

/** Muta a MeshStandardMaterial compartilhada por todas as malhas da cena
 * (ver group.userData.sharedMaterial em sceneBuilder.js) -- so 5 dos 8
 * estilos reais do SketchUp sao implementaveis sem texturas/materiais por
 * face (que este visualizador nao tem, ver REVERSE_ENGINEERING_NOTES.md
 * secao 27); os demais ficam desabilitados no menu. */
function setFaceStyle(style) {
  faceStyle = style;
  const material = currentGroup?.userData.sharedMaterial;
  if (material) {
    material.wireframe = style === "wireframe";
    material.transparent = style === "xray";
    material.opacity = style === "xray" ? 0.3 : 1;
    material.depthWrite = style !== "xray";
    material.color.set(style === "monochrome" ? 0xCCCCCC : 0x8c99a6);
    material.needsUpdate = true;
  }
  for (const [key, id] of Object.entries(FACE_STYLE_MENU_IDS)) {
    document.getElementById(id).classList.toggle("is-checked", key === style);
  }
}

/** Abas sanfonadas do Default Tray -- cada secao recolhe/expande
 * independente, igual ao comportamento real do Default Tray do SketchUp. */
trayHeaderEls.forEach((header) => {
  header.addEventListener("click", () => {
    document.getElementById(header.dataset.section).classList.toggle("collapsed");
  });
});

/** Tira um snapshot real do canvas (forca um render sincrono antes, ja
 * que o WebGLRenderer nao usa preserveDrawingBuffer) e manda pro backend
 * virar a thumbnail do arquivo na Pagina Inicial. Best-effort -- uma
 * falha aqui nunca deve incomodar quem so queria abrir o modelo. */
async function captureAndUploadThumbnail(path) {
  try {
    renderer.render(scene, camera);
    const dataUrl = renderer.domElement.toDataURL("image/png");
    await uploadThumbnail(path, dataUrl);
  } catch {
    // thumbnail e cosmetico -- ignora silenciosamente
  }
}

/** Monta a cena Three.js/Outliner a partir de um SceneDTO (vindo de
 * /scene/open ou /scene/new) -- compartilhado pelos dois fluxos de
 * abertura. Retorna as contagens pra compor a mensagem de status. */
function applySceneDTO(sceneDTO) {
  currentSceneDTO = sceneDTO; // usado por "Janela > Informacoes do modelo"
  if (currentGroup) {
    scene.remove(currentGroup);
  }
  // cotas 3D (Ferramentas > Dimensoes) e plano de secao referem-se ao
  // modelo anterior -- limpos ao trocar de cena
  dimensionsGroup.clear();
  sectionPlane = null;
  setLassoSelection([]);
  currentGroup = buildSceneGroup(sceneDTO);
  scene.add(currentGroup);
  setStandardView("iso");
  editPanelEl.classList.remove("hidden");
  // o novo grupo traz material/overlay de arestas no estado padrao --
  // reaplica os toggles de "Visualizar" que estavam ativos antes de abrir
  // este modelo (eixos/sombras/nevoa sao globais e nao precisam disso).
  setEdgesVisible(edgesVisible);
  setFaceStyle(faceStyle);

  outlinerTreeEl.innerHTML = "";
  currentOutliner = buildOutlinerTree(sceneDTO, selectInstanceById);
  outlinerTreeEl.appendChild(currentOutliner.element);
  defaultTrayEl.classList.remove("hidden");
  refreshScenePages();
  refreshTags();

  return {
    totalDefinitions: sceneDTO.definitions.length,
    totalInstances: sceneDTO.instances.length,
    totalVertices: sceneDTO.definitions.reduce((acc, d) => acc + d.vertices.length / 3, 0),
    totalTriangles: sceneDTO.definitions.reduce((acc, d) => acc + d.indices.length / 3, 0),
  };
}

/** @returns {Promise<boolean>} true se o modelo abriu com sucesso. */
async function handleOpen() {
  const path = pathInputEl.value.trim();
  if (!path) {
    setStatus("Informe um caminho de arquivo .skp.", true);
    return false;
  }

  openBtnEl.disabled = true;
  deselectMesh();
  setStatus("Abrindo e extraindo malha...");

  try {
    const sceneDTO = await openScene(path);
    const counts = applySceneDTO(sceneDTO);
    setStatus(
      `OK -- ${counts.totalDefinitions} definicoes, ${counts.totalInstances} ` +
        `instancias, ${counts.totalVertices} vertices, ${counts.totalTriangles} triangulos.`
    );
    captureAndUploadThumbnail(path);
    return true;
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro: ${detail}`, true);
    return false;
  } finally {
    openBtnEl.disabled = false;
  }
}

/** Cria um modelo novo a partir de um template real da Trimble (cards da
 * secao "Criar novo modelo"). Nao ha thumbnail/caminho pra registrar em
 * "Arquivos recentes" ainda -- so depois de um "Salvar Como".
 * @returns {Promise<boolean>} true se o template abriu com sucesso. */
async function handleNewFromTemplate(templateId) {
  deselectMesh();
  setStatus("Criando novo modelo a partir do template...");

  try {
    const sceneDTO = await newSceneFromTemplate(templateId);
    const counts = applySceneDTO(sceneDTO);
    savePathInputEl.value = ""; // forca "Salvar Como" -- ainda nao ha arquivo no disco
    setStatus(
      `Novo modelo criado a partir do template -- ${counts.totalVertices} vertices, ` +
        `${counts.totalTriangles} triangulos. Use "Salvar Como" para escolher onde gravar.`
    );
    return true;
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao criar modelo: ${detail}`, true);
    return false;
  }
}

async function handleSave() {
  const path = savePathInputEl.value.trim();
  saveBtnEl.disabled = true;
  setStatus(path ? `Salvando em ${path}...` : "Salvando (sobrescrevendo o arquivo aberto)...");

  try {
    const result = await saveScene(path);
    setStatus(`Salvo em ${result.path}.`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao salvar: ${detail}`, true);
  } finally {
    saveBtnEl.disabled = false;
  }
}

/** Equivalente a "Editar > Excluir"/Del: apaga de verdade a instancia
 * selecionada na SketchUpAPI.dll (ver core/su_api.py erase_instance) e
 * remove o mesh da cena Three.js. Irreversivel nesta sessao (ainda nao
 * ha pilha de desfazer/refazer -- ver REVERSE_ENGINEERING_NOTES.md
 * secao 26). O Outliner nao e reconstruido aqui (fica com a entrada
 * obsoleta ate o proximo Abrir) -- limitacao conhecida. */
async function handleDeleteSelected() {
  // Ferramentas > Laco: se ha uma selecao multipla ativa, exclui todas
  // de verdade em lote (mesmo deleteInstance/SUEntitiesErase, uma
  // chamada por peca) -- nao e so um highlight cosmetico.
  if (toolMode === "lasso" && lassoSelection.length) {
    const meshes = [...lassoSelection];
    let deletedCount = 0;
    for (const mesh of meshes) {
      try {
        await deleteInstance(mesh.name);
        currentGroup.remove(mesh);
        deletedCount++;
      } catch (err) {
        const detail = err instanceof ApiError ? err.message : String(err);
        setStatus(`Erro ao excluir ${mesh.name}: ${detail}`, true);
      }
    }
    setLassoSelection([]);
    setStatus(`${deletedCount} peca(s) excluida(s) em lote (ainda nao salvo em disco).`);
    return;
  }

  if (!selectedMesh) {
    setStatus("Nenhuma instancia selecionada para excluir.", true);
    return;
  }
  const mesh = selectedMesh;
  try {
    await deleteInstance(mesh.name);
    deselectMesh();
    currentGroup.remove(mesh);
    setStatus(`${mesh.name} excluido (ainda nao salvo em disco).`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao excluir: ${detail}`, true);
  }
}

/** Ferramentas > Plano de secao: cria um THREE.Plane real (clipping
 * nativo do WebGL via renderer.localClippingEnabled) na altura (Y) do
 * ponto clicado, cortando de verdade a geometria acima dele -- nao e
 * um efeito visual falso, usa o pipeline de clipping real do Three.js.
 * Aplicado no material compartilhado da cena aberta. */
function handleSectionClick(worldPoint) {
  const material = currentGroup?.userData.sharedMaterial;
  if (!material) {
    setStatus("Nenhum modelo aberto.", true);
    return;
  }
  sectionPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), worldPoint.y);
  material.clippingPlanes = [sectionPlane];
  setStatus(`Plano de secao criado em Y=${worldPoint.y.toFixed(3)}m. Clique em outro ponto pra mover, ou use "Remover plano de secao".`);
}

/** Ferramentas > Plano de secao > Remover plano de secao. */
function handleSectionClear() {
  const material = currentGroup?.userData.sharedMaterial;
  if (material) material.clippingPlanes = [];
  sectionPlane = null;
  setStatus("Plano de secao removido.");
}

/** Cria uma textura de texto simples (canvas 2D) pra usar num
 * THREE.Sprite -- usado pelo rotulo de distancia das Dimensoes. */
function makeTextSprite(text) {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 64;
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = "rgba(255,255,255,0.9)";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#3C7FB1";
  ctx.lineWidth = 3;
  ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);
  ctx.fillStyle = "#1A1A1A";
  ctx.font = "bold 28px monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, canvas.width / 2, canvas.height / 2);
  const texture = new THREE.CanvasTexture(canvas);
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture, depthTest: false }));
  sprite.scale.set(0.6, 0.15, 1);
  return sprite;
}

/** Ferramentas > Dimensoes: dois cliques criam uma cota 3D PERSISTENTE
 * de verdade (linha real + rotulo de texto com a distancia real) na
 * cena -- diferente da Fita metrica (so leitura/status), esta fica
 * visivel no viewport ate "Editar > Excluir" ser usado nela ou o
 * modelo ser reaberto. */
function handleDimensionClick(worldPoint) {
  if (!dimensionFirstPoint) {
    dimensionFirstPoint = worldPoint.clone();
    setStatus("Modo Dimensoes: clique no segundo ponto da cota.");
    return;
  }
  const p1 = dimensionFirstPoint;
  const p2 = worldPoint.clone();
  const distance = p1.distanceTo(p2);

  const lineGeometry = new THREE.BufferGeometry().setFromPoints([p1, p2]);
  const line = new THREE.Line(lineGeometry, new THREE.LineBasicMaterial({ color: 0x3c7fb1, depthTest: false }));
  const label = makeTextSprite(`${distance.toFixed(3)} m`);
  label.position.copy(p1.clone().lerp(p2, 0.5));

  const dimension = new THREE.Group();
  dimension.add(line, label);
  dimensionsGroup.add(dimension);

  setStatus(`Cota criada: ${distance.toFixed(3)} m. Clique no proximo primeiro ponto.`);
  dimensionFirstPoint = null;
}

/** Ferramentas > Texto: coloca um rotulo 3D persistente (mesmo
 * THREE.Sprite com canvas de texto da cota) com o conteudo digitado no
 * campo do painel, no ponto clicado. Diferente de "Texto 3D" (extrusao
 * de fonte em malha), este e um rotulo billboard, mesma abordagem do
 * SketchUp real pra "Texto" (nao o "Texto 3D", que e outro item). */
function handleTextClick(worldPoint) {
  const content = textContentInputEl.value.trim();
  if (!content) {
    setStatus("Escreva o texto do rotulo antes de clicar no viewport.", true);
    return;
  }
  const label = makeTextSprite(content);
  label.position.copy(worldPoint);
  dimensionsGroup.add(label);
  setStatus(`Rotulo "${content}" criado no viewport.`);
  setToolMode("select");
}

/** Ferramentas > Laco: alterna a peca clicada dentro/fora da selecao
 * multipla acumulada (lassoSelection). Nao e so cosmetico -- "Excluir
 * (Del)" exclui de verdade todas as pecas selecionadas em lote (ver
 * handleDeleteSelected). */
function handleLassoClick(mesh) {
  const idx = lassoSelection.indexOf(mesh);
  const next = idx === -1 ? [...lassoSelection, mesh] : lassoSelection.filter((m) => m !== mesh);
  setLassoSelection(next);
}

/** Ferramentas > Pintura: aplica uma cor RGBA nova de verdade na
 * instancia (SUMaterialCreate/SUMaterialSetColor/SUDrawingElementSet
 * Material -- ver core/su_api.py paint_instance() e REVERSE_ENGINEERING_
 * NOTES.md secao 28). LIMITACAO HONESTA: como todas as malhas da cena
 * compartilham a mesma MeshStandardMaterial (group.userData.sharedMaterial,
 * ver sceneBuilder.js) por performance, nao da pra tingir so uma peca sem
 * "destacar" ela desse material compartilhado -- esta funcao clona o
 * material pra essa instancia especifica. A partir daí, essa peca para de
 * responder aos toggles de "Visualizar > Estilo de face" (setFaceStyle so
 * muta o material COMPARTILHADO, nunca os clones), o que e um trade-off
 * aceito, nao escondido. */
function handleArmPaint() {
  setToolMode("paint");
}

async function handlePaintClick(mesh) {
  const hex = paintColorInputEl.value; // "#rrggbb"
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  try {
    await paintInstance(mesh.name, r, g, b);
    // Se a peca ja tinha faces pintadas individualmente (array de
    // materiais + geometry.groups, ver applyFacePaintColor()), pintar a
    // instancia inteira agora substitui tudo por um unico material --
    // mesma semantica de "pintar por cima" do SketchUp real. Limitacao
    // conhecida: geometry.groups fica na geometria COMPARTILHADA da
    // definicao -- se outra instancia da MESMA definicao tambem tiver
    // faces pintadas nesta sessao, o visual dela reverte junto (dado
    // real no .skp nao e afetado, so o reflexo client-side).
    const baseMaterial = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
    mesh.geometry.clearGroups();
    delete mesh.userData.paintedFaces;
    mesh.material = baseMaterial.clone();
    mesh.material.color.setRGB(r / 255, g / 255, b / 255);
    mesh.material.needsUpdate = true;
    setStatus(`${mesh.name} pintado (#${hex.slice(1)}). Modo Pintura continua ativo.`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao pintar: ${detail}`, true);
  }
}

/** Ferramentas > Pintura por face: pinta uma FACE especifica (nao a peca
 * inteira) -- diferente de handlePaintClick(), a mudanca no backend fica
 * gravada na geometria da DEFINICAO (SUFaceSetFrontMaterial, ver
 * core/su_api.py paint_face() e REVERSE_ENGINEERING_NOTES.md secao
 * 28.19), afetando TODAS as instancias que compartilham essa definicao
 * no .skp -- mesmo comportamento do SketchUp real. Visualmente, so a
 * peca clicada nesta sessao reflete a mudanca (limitacao documentada,
 * mesmo trade-off ja aceito em handlePaintClick/handleArmPaint): o
 * frontend usa `THREE.BufferGeometry.groups` (ver applyFacePaintColor())
 * pra dar uma segunda material so no intervalo de triangulos daquela
 * face, sem reconstruir a malha inteira nem clonar a geometria. */
function handleArmPaintFace() {
  setToolMode("paintFace");
}

/** Mapeia o `faceIndex` (indice de TRIANGULO) que o Raycaster devolve de
 * volta pro `face_id` real via `geometry.userData.faceRanges` (ver
 * sceneBuilder.js buildGeometry()). */
function resolveFaceId(geometry, faceIndex) {
  const ranges = geometry.userData.faceRanges || [];
  for (const range of ranges) {
    if (faceIndex >= range.triangle_start && faceIndex < range.triangle_start + range.triangle_count) {
      return range;
    }
  }
  return null;
}

/** Aplica a cor numa face especifica do mesh via `geometry.groups` +
 * array de materiais -- ver nota em handleArmPaintFace(). Suporta pintar
 * varias faces diferentes da MESMA peca ao longo da sessao
 * (mesh.userData.paintedFaces acumula os intervalos ja pintados e
 * reconstroi os grupos do zero a cada chamada). */
function applyFacePaintColor(mesh, range, r, g, b) {
  const geometry = mesh.geometry;
  if (!mesh.userData.paintedFaces) mesh.userData.paintedFaces = new Map();

  const baseMaterial = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
  const faceMaterial = baseMaterial.clone();
  faceMaterial.color.setRGB(r / 255, g / 255, b / 255);
  faceMaterial.needsUpdate = true;
  mesh.userData.paintedFaces.set(range.face_id, {
    triangleStart: range.triangle_start,
    triangleCount: range.triangle_count,
    material: faceMaterial,
  });

  const totalTriangles = geometry.index.count / 3;
  const sorted = [...mesh.userData.paintedFaces.values()].sort((a, b2) => a.triangleStart - b2.triangleStart);
  const materials = [baseMaterial];
  geometry.clearGroups();
  let cursor = 0;
  for (const painted of sorted) {
    if (painted.triangleStart > cursor) {
      geometry.addGroup(cursor * 3, (painted.triangleStart - cursor) * 3, 0);
    }
    materials.push(painted.material);
    geometry.addGroup(painted.triangleStart * 3, painted.triangleCount * 3, materials.length - 1);
    cursor = painted.triangleStart + painted.triangleCount;
  }
  if (cursor < totalTriangles) {
    geometry.addGroup(cursor * 3, (totalTriangles - cursor) * 3, 0);
  }
  mesh.material = materials;
}

async function handlePaintFaceClick(hit) {
  const mesh = hit.object;
  if (hit.faceIndex === undefined || hit.faceIndex === null) {
    setStatus("Nao foi possivel identificar a face clicada.", true);
    return;
  }
  const range = resolveFaceId(mesh.geometry, hit.faceIndex);
  if (!range) {
    setStatus("Face clicada nao encontrada no DTO (geometria sem face_ranges).", true);
    return;
  }
  const hex = paintColorInputEl.value; // "#rrggbb"
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  try {
    await paintFace(range.face_id, r, g, b);
    applyFacePaintColor(mesh, range, r, g, b);
    setStatus(
      `Face de ${mesh.name} pintada (#${hex.slice(1)}) -- muda todas as instancias dessa peca no arquivo. Modo Pintura por face continua ativo.`
    );
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao pintar a face: ${detail}`, true);
  }
}

/** Ferramentas > Etiqueta: aplica uma Etiqueta (Tag) real na instancia
 * clicada -- a API interna ainda chama isso de "Layer" (nome legado da
 * Trimble, ver REVERSE_ENGINEERING_NOTES.md secao 28.17). Reusa a MESMA
 * etiqueta no backend se o mesmo nome for digitado de novo (cache por
 * sessao em session.tags, ver skp_engine_repository.py). */
function handleArmTag() {
  // Nao valida o nome aqui de proposito -- o campo "Etiqueta" so fica
  // visivel na VCB DEPOIS de armar o modo (ver syncToolUI()), entao
  // exigir nome antes impediria o usuario de digitar. handleTagClick()
  // ja valida no momento do clique na peca.
  setToolMode("tag");
}

async function handleTagClick(mesh) {
  const name = tagNameInputEl.value.trim();
  if (!name) {
    setStatus("Escreva o nome da etiqueta antes de clicar numa peça.", true);
    return;
  }
  try {
    await tagInstance(mesh.name, name);
    // reflete o novo `tag` no DTO em memoria (sem reabrir o modelo) pra
    // "Janela > Bandeja padrao > Etiquetas" ja reconhecer esta instancia
    // na proxima vez que a visibilidade dessa etiqueta for alternada.
    const inst = currentSceneDTO?.instances.find((i) => i.instance_id === mesh.name);
    if (inst) inst.tag = name;
    await refreshTags();
    setStatus(`${mesh.name} etiquetado como "${name}". Modo Etiqueta continua ativo.`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao etiquetar: ${detail}`, true);
  }
}

/** Ferramentas > Eixos: 3 cliques reais na geometria (origem, ponto na
 * direcao X, ponto no plano XY) redefinem o sistema de eixos LOCAL da
 * definicao por tras da peca clicada no 1o clique -- SUAxesCreateCustom/
 * SUComponentDefinitionSetAxes (ver core/su_api.py e
 * REVERSE_ENGINEERING_NOTES.md secao 28.21). Os 2 cliques seguintes
 * usam SEMPRE o `mesh.matrix` do 1o clique pra converter o ponto (pode
 * cair em qualquer peca da cena, so o PONTO importa -- mesma UX do
 * SketchUp real, que deixa clicar em qualquer superficie pra definir
 * direcao). Muda metadado da DEFINICAO (afeta todas as instancias que a
 * compartilham, mesma semantica de Etiqueta/Pintura por face) -- nao
 * move a geometria nem a peca visivelmente nesta sessao. */
function handleAxesClick(hit) {
  if (axesPoints.length === 0) {
    axesTargetMesh = hit.object;
    axesPoints.push(hit.point.clone());
    setStatus("Modo Eixos: clique no ponto que define a direção do eixo X (vermelho).");
    return;
  }
  axesPoints.push(hit.point.clone());
  if (axesPoints.length === 2) {
    setStatus("Modo Eixos: clique no ponto que define o plano do eixo Y (verde).");
    return;
  }
  applyCustomAxes();
}

async function applyCustomAxes() {
  const mesh = axesTargetMesh;
  const [originWorld, xWorld, yWorld] = axesPoints;
  const origin = worldPointToLocalInches(mesh, originWorld);
  const xPoint = worldPointToLocalInches(mesh, xWorld);
  const yPoint = worldPointToLocalInches(mesh, yWorld);
  try {
    await setInstanceAxes(mesh.name, origin, xPoint, yPoint);
    setStatus(
      `Eixos de ${mesh.name} redefinidos (afeta todas as instâncias dessa peça no arquivo). ` +
        "Modo Eixos continua ativo -- clique na próxima origem."
    );
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao redefinir eixos: ${detail}`, true);
  } finally {
    axesPoints = [];
    axesTargetMesh = null;
  }
}

/** Janela > Bandeja padrao > Cenas: lista/cria/ativa Cenas reais do
 * modelo aberto (SUSceneCreate/SUModelAddScenes/SUModelSetActiveScene,
 * ver core/su_api.py e REVERSE_ENGINEERING_NOTES.md secao 28.20). Limitacao
 * documentada: nao captura/restaura camera (este projeto nao tem
 * binding de SUCameraRef) -- "Ativar" muda a cena ativa real do
 * modelo (persistida ao salvar), mas nao move a camera do viewer. */
function renderScenePages(pages) {
  scenePagesListEl.innerHTML = "";
  if (!pages.length) {
    const empty = document.createElement("div");
    empty.style.cssText = "font-size: 11px; color: var(--muted);";
    empty.textContent = "Nenhuma cena neste modelo ainda.";
    scenePagesListEl.appendChild(empty);
    return;
  }
  for (const page of pages) {
    const row = document.createElement("div");
    row.className = "row";
    row.style.cssText = "margin-top: 4px; align-items: center; justify-content: space-between;";

    const label = document.createElement("span");
    label.style.cssText = "font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;";
    label.textContent = page.active ? `${page.name} (ativa)` : page.name;
    row.appendChild(label);

    if (!page.active) {
      const activateBtn = document.createElement("button");
      activateBtn.className = "panel-btn";
      activateBtn.textContent = "Ativar";
      activateBtn.addEventListener("click", () => handleActivateScene(page.scene_id));
      row.appendChild(activateBtn);
    }
    scenePagesListEl.appendChild(row);
  }
}

async function refreshScenePages() {
  try {
    const { pages } = await listScenePages();
    renderScenePages(pages);
  } catch {
    // painel de Cenas e cosmetico -- nao interrompe a abertura do modelo
  }
}

/** "Janela > Bandeja padrao > Etiquetas" -- lista real (nao so as criadas
 * nesta sessao via Ferramentas > Etiqueta), com checkbox de visibilidade
 * real (SULayerSetVisibility, ver REVERSE_ENGINEERING_NOTES.md secao
 * 28.22). Mesmo padrao de renderScenePages() (lista fina inline, sem
 * modulo separado -- so Outliner/Welcome justificam um arquivo proprio,
 * por terem arvore/cards mais complexos). */
function renderTags(tags) {
  tagsListEl.innerHTML = "";
  tagsEmptyEl.classList.toggle("hidden", tags.length > 0);
  for (const tag of tags) {
    const row = document.createElement("div");
    row.className = "row";
    row.style.cssText = "margin-top: 4px; align-items: center; gap: 6px;";

    const visibilityCheckbox = document.createElement("input");
    visibilityCheckbox.type = "checkbox";
    visibilityCheckbox.checked = tag.visible;
    visibilityCheckbox.title = "Visibilidade real da Etiqueta (SULayerSetVisibility)";
    visibilityCheckbox.addEventListener("change", () =>
      handleToggleTagVisibility(tag.name, visibilityCheckbox.checked)
    );
    row.appendChild(visibilityCheckbox);

    const label = document.createElement("span");
    label.style.cssText = "font-size: 12px; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;";
    label.textContent = tag.is_default ? `${tag.name} (padrão)` : tag.name;
    row.appendChild(label);

    tagsListEl.appendChild(row);
  }
}

async function refreshTags() {
  try {
    const tags = await listTags();
    renderTags(tags);
  } catch {
    // painel de Etiquetas e cosmetico -- nao interrompe a abertura do modelo
  }
}

/** Aplica a visibilidade real na DLL (persiste se "Salvar" rodar depois)
 * E reflete na cena 3D client-side -- toda instancia cujo `tag` real
 * (campo novo do DTO, ver core/mesh_extractor.py) bate com a etiqueta
 * alternada tem o mesh escondido/reexibido, sem precisar reabrir o
 * modelo nem reextrair a malha inteira. */
async function handleToggleTagVisibility(tagName, visible) {
  try {
    await setTagVisibility(tagName, visible);
    if (currentGroup && currentSceneDTO) {
      for (const inst of currentSceneDTO.instances) {
        if (inst.tag !== tagName) continue;
        const mesh = currentGroup.getObjectByName(inst.instance_id);
        if (mesh) mesh.visible = visible;
      }
    }
    setStatus(`Etiqueta "${tagName}" ${visible ? "exibida" : "ocultada"}.`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao alternar a etiqueta: ${detail}`, true);
    await refreshTags(); // reverte o checkbox pro estado real
  }
}

async function handleCreateScene() {
  const name = sceneNameInputEl.value.trim();
  if (!name) {
    setStatus("Escreva o nome da cena antes de criar.", true);
    return;
  }
  try {
    await createScenePage(name);
    sceneNameInputEl.value = "";
    await refreshScenePages();
    setStatus(`Cena "${name}" criada.`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao criar cena: ${detail}`, true);
  }
}

async function handleActivateScene(sceneId) {
  try {
    await activateScenePage(sceneId);
    await refreshScenePages();
    setStatus("Cena ativada (nao move a camera do viewer -- ver limitacao documentada).");
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao ativar cena: ${detail}`, true);
  }
}

/** Ferramentas > Texto 3D: extrusao REAL de fonte em malha (THREE.Font/
 * TextGeometry, carregada do mesmo CDN de onde a lib ja vem -- ver
 * loadFont()), diferente do rotulo billboard 2D de "Texto" (28.13).
 * Malha de verdade com volume, adicionada ao dimensionsGroup. */
function handleArmText3D() {
  const content = textContentInputEl.value.trim();
  if (!content) {
    setStatus("Escreva o texto antes de clicar no viewport.", true);
    return;
  }
  setToolMode("text3d");
}

async function handleText3DClick(worldPoint) {
  const content = textContentInputEl.value.trim();
  if (!content) {
    setStatus("Escreva o texto antes de clicar no viewport.", true);
    return;
  }
  setStatus("Carregando fonte...");
  try {
    const font = loadedFont || (await loadFont());
    const geometry = new TextGeometry(content, {
      font,
      size: 0.1,
      depth: 0.02,
      curveSegments: 4,
    });
    geometry.computeBoundingBox();
    geometry.center();
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0x3c7fb1 }));
    mesh.position.copy(worldPoint);
    dimensionsGroup.add(mesh);
    setStatus(`Texto 3D "${content}" criado no viewport.`);
  } catch (err) {
    setStatus(`Erro ao carregar fonte: ${err}`, true);
  }
  setToolMode("select");
}

/** Ferramentas > Virar ao longo de: espelha a peca selecionada no eixo
 * escolhido (nega a escala nesse eixo) e aplica pelo MESMO caminho real
 * de transformacao ja existente (applyTransformEdit -> PATCH
 * /scene/instances/{id}/transform -> SUComponentInstanceSetTransform).
 * Mapeamento Vermelho/Verde/Azul (eixos nativos do SketchUp, X/Y/Z com Z
 * pra cima) pros eixos do Three.js (Y pra cima, ver SKP_TO_THREE_UP em
 * sceneBuilder.js): Vermelho->X, Verde->Z, Azul->Y. */
const FLIP_AXIS_THREE = { red: "x", green: "z", blue: "y" };

function handleFlip(skpAxis) {
  if (!selectedMesh) {
    setStatus("Nenhuma instancia selecionada para virar.", true);
    return;
  }
  const axis = FLIP_AXIS_THREE[skpAxis];
  selectedMesh.scale[axis] *= -1;
  applyTransformEdit(selectedMesh);
  updateEntityInfoDisplay(selectedMesh);
}

async function handleExportObj() {
  const path = exportObjPathInputEl.value.trim();
  if (!path) {
    setStatus("Informe um caminho de destino terminando em .obj.", true);
    return;
  }
  exportObjBtnEl.disabled = true;
  setStatus(`Exportando para ${path}...`);
  try {
    const result = await exportModelObj(path);
    setStatus(`Exportado para ${result.path}.`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao exportar: ${detail}`, true);
  } finally {
    exportObjBtnEl.disabled = false;
  }
}

/** Equivalente real de "Desenho > Formas > Retângulo" -- cria uma face
 * nova de verdade na Entities raiz via SUEntitiesFill (ver core/su_api.py
 * add_face() e REVERSE_ENGINEERING_NOTES.md secao 28), centrada na
 * origem, deitada no chao. Reusa applySceneDTO() porque geometria nova
 * (diferente de mover/excluir uma instancia) muda a malha "root" inteira
 * -- precisa reconstruir a cena a partir do DTO completo que o backend
 * devolve, nao da pra aplicar incrementalmente no Three.js. */
async function handleAddRectangle() {
  const width = parseFloat(rectWidthInputEl.value);
  const height = parseFloat(rectHeightInputEl.value);
  if (!Number.isFinite(width) || width <= 0 || !Number.isFinite(height) || height <= 0) {
    setStatus("Informe largura e profundidade positivas (metros).", true);
    return;
  }
  const asGroup = rectAsGroupCheckboxEl.checked;
  rectCreateBtnEl.disabled = true;
  setStatus("Criando retângulo...");
  try {
    const result = await addRectangle(width, height, asGroup);
    applySceneDTO(result.scene);
    setStatus(
      `Retângulo ${width}x${height}m criado${asGroup ? " dentro de um grupo novo" : ""} (ainda não salvo em disco).`
    );
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao criar retângulo: ${detail}`, true);
  } finally {
    rectCreateBtnEl.disabled = false;
  }
}

exportObjBtnEl.addEventListener("click", handleExportObj);
rectCreateBtnEl.addEventListener("click", handleAddRectangle);
sceneCreateBtnEl.addEventListener("click", handleCreateScene);

// -- Barra de menu real (Arquivo/Editar) -----------------------------------
// Catalogada via clique real no SketchUp 2026 rodando na maquina (ver
// REVERSE_ENGINEERING_NOTES.md secao 26). Os itens com `data-action` ligam
// nos MESMOS fluxos ja existentes (nao duplicam logica); os demais ficam
// `.disabled` (sem handler), igual o SketchUp real faz com itens
// indisponiveis -- nunca escondidos, so inativos.
const MENU_ACTIONS = {
  new: () => welcomeScreenEl.classList.remove("hidden"),
  open: () => pathInputEl.focus(),
  save: () => handleSave(),
  "save-as": () => savePathInputEl.focus(),
  "export-obj": () => exportObjPathInputEl.focus(),
  delete: () => handleDeleteSelected(),
  "toggle-axes": () => setAxesVisible(!axesVisible),
  "toggle-shadows": () => setShadowsEnabled(!shadowsEnabled),
  "toggle-fog": () => setFogEnabled(!fogEnabled),
  "toggle-edges": () => setEdgesVisible(!edgesVisible),
  "face-style-textured": () => setFaceStyle("textured"),
  "face-style-flat": () => setFaceStyle("flat"),
  "face-style-monochrome": () => setFaceStyle("monochrome"),
  "face-style-wireframe": () => setFaceStyle("wireframe"),
  "face-style-xray": () => setFaceStyle("xray"),
  "view-alto": () => setStandardView("alto"),
  "view-inferior": () => setStandardView("inferior"),
  "view-frontal": () => setStandardView("frontal"),
  "view-posterior": () => setStandardView("posterior"),
  "view-esquerda": () => setStandardView("esquerda"),
  "view-direita": () => setStandardView("direita"),
  "view-iso": () => setStandardView("iso"),
  "projection-parallel": () => setProjectionMode("parallel"),
  "projection-perspective": () => setProjectionMode("perspective"),
  "field-of-view": () => handleFieldOfView(),
  "tool-translate": () => setMode("translate"),
  "tool-rotate": () => setMode("rotate"),
  "tool-scale": () => setMode("scale"),
  "tool-select": () => setToolMode("select"),
  "tool-erase": () => setToolMode("erase"),
  "tool-measure": () => setToolMode("measure"),
  "flip-red": () => handleFlip("red"),
  "flip-green": () => handleFlip("green"),
  "flip-blue": () => handleFlip("blue"),
  "tool-protractor": () => setToolMode("protractor"),
  "tool-section": () => setToolMode("section"),
  "section-clear": () => handleSectionClear(),
  "tool-dimension": () => setToolMode("dimension"),
  "tool-text": () => setToolMode("text"),
  "tool-rect": () => setToolMode("rect"),
  "tool-lasso": () => setToolMode("lasso"),
  "tool-text3d": () => handleArmText3D(),
  "tool-paint": () => handleArmPaint(),
  "tool-paint-face": () => handleArmPaintFace(),
  "tool-tag": () => handleArmTag(),
  "tool-axes": () => setToolMode("axes"),
  "toggle-tray-scenes": () => toggleTraySection("tray-scenes", "menu-item-tray-scenes"),
  "toggle-tray-tags": () => toggleTraySection("tray-tags", "menu-item-tray-tags"),
  "rect-as-group": () => {
    rectAsGroupCheckboxEl.checked = true;
    setToolMode("rect");
    rectWidthInputEl.focus();
  },
  "model-info": () => handleModelInfo(),
  welcome: () => handleWelcome(),
  "toggle-tray-entity-info": () => toggleTraySection("tray-entity-info", "menu-item-tray-entity-info"),
  "toggle-tray-outliner": () => toggleTraySection("tray-outliner", "menu-item-tray-outliner"),
  about: () => handleAbout(),
  "draw-rectangle": () => {
    setToolMode("rect");
    rectWidthInputEl.focus();
  },
};

/** "Janela > Bandeja padrão > Informações da entidade/Componentes" --
 * equivalente real de mostrar/ocultar um painel da Bandeja padrao (ver
 * REVERSE_ENGINEERING_NOTES.md secao 27). Reusa o mesmo mecanismo de
 * colapso ja ligado ao clique no cabecalho da secao -- so sincroniza a
 * marca de selecao (✓) do item de menu com o estado atual. */
function toggleTraySection(sectionId, menuItemId) {
  const section = document.getElementById(sectionId);
  section.classList.toggle("collapsed");
  document.getElementById(menuItemId).classList.toggle("is-checked", !section.classList.contains("collapsed"));
}

/** "Ajuda > Sobre o SketchBuild..." -- usa a barra de status em vez de um
 * dialogo nativo (window.alert bloquearia a automacao do navegador do
 * mesmo jeito que window.prompt, ver handleFieldOfView()). */
function handleAbout() {
  setStatus(
    "SketchBuild -- visualizador/editor 3D standalone de arquivos .skp " +
      "(ctypes + SketchUpAPI.dll real + Three.js/FastAPI). Projeto de Fernando Filho."
  );
}

/** "Janela > Informacoes do modelo" -- mostra as contagens reais da
 * cena aberta (mesmos dados ja calculados em applySceneDTO/handleOpen,
 * so reexibidos sob demanda). */
function handleModelInfo() {
  if (!currentSceneDTO) {
    setStatus("Nenhum modelo aberto.", true);
    return;
  }
  const totalVertices = currentSceneDTO.definitions.reduce((acc, d) => acc + d.vertices.length / 3, 0);
  const totalTriangles = currentSceneDTO.definitions.reduce((acc, d) => acc + d.indices.length / 3, 0);
  setStatus(
    `Informacoes do modelo -- ${currentSceneDTO.definitions.length} definicoes, ` +
      `${currentSceneDTO.instances.length} instancias, ${totalVertices} vertices, ` +
      `${totalTriangles} triangulos.`
  );
}

/** "Ajuda > Bem-vindo ao SketchUp..." -- reabre a mesma Pagina Inicial
 * real da Fase 6 (nao e um dialogo separado, e a tela de boas-vindas
 * de verdade, igual o SketchUp real reabre via esse item de menu). */
function handleWelcome() {
  welcomeScreenEl.classList.remove("hidden");
}

function closeAllMenus() {
  menuTopItemEls.forEach((item) => item.classList.remove("open"));
}

menuTopItemEls.forEach((item) => {
  item.addEventListener("click", (event) => {
    const actionItem = event.target.closest(".menu-dropdown-item");
    if (actionItem) {
      if (!actionItem.classList.contains("disabled") && actionItem.dataset.action) {
        MENU_ACTIONS[actionItem.dataset.action]?.();
      }
      closeAllMenus();
      return;
    }
    const wasOpen = item.classList.contains("open");
    closeAllMenus();
    if (!wasOpen) item.classList.add("open");
  });
});

document.addEventListener("click", (event) => {
  if (!event.target.closest(".menu-top-item")) closeAllMenus();
});

// -- "Large Tool Set" (icones) -- reusa os mesmos MENU_ACTIONS ja ligados
// no menu "Ferramentas"/"Desenho"/"Editar"; so outra forma de disparar a
// mesma funcao (ver index.html #tools-toolbar).
toolsToolbarEl.querySelectorAll(".toolbar-btn[data-action]").forEach((btn) => {
  btn.addEventListener("click", () => {
    if (btn.classList.contains("disabled") || btn.disabled) return;
    MENU_ACTIONS[btn.dataset.action]?.();
  });
});

openBtnEl.addEventListener("click", handleOpen);
pathInputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleOpen();
});
saveBtnEl.addEventListener("click", handleSave);
toolbarSaveBtnEl.addEventListener("click", handleSave);

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

/** Gira cada mesh "sempre de frente para a camera" (ver sceneBuilder.js
 * / mesh.userData.billboard) so no eixo vertical (yaw), igual ao
 * comportamento real do SketchUp pro personagem de escala. O mesh
 * selecionado fica de fora -- enquanto o gizmo esta anexado, quem manda
 * na rotacao e o TransformControls, nao esse loop. +Z local e a frente
 * do componente (a geometria plana do "Sree" fica no plano Z=0 local). */
function updateBillboards() {
  if (!currentGroup) return;
  for (const mesh of currentGroup.children) {
    if (!mesh.userData.billboard || mesh === selectedMesh) continue;
    const yaw = Math.atan2(camera.position.x - mesh.position.x, camera.position.z - mesh.position.z);
    // 'YXZ' preserva o pitch/roll originais do .skp (mesh.userData.billboardPitch/Roll,
    // ver sceneBuilder.js) -- so o Y (yaw) e recalculado pra encarar a camera.
    mesh.rotation.set(mesh.userData.billboardPitch, yaw, mesh.userData.billboardRoll);
  }
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  updateBillboards();
  renderer.render(scene, camera);
}
animate();

// -- Pagina Inicial (tela de boas-vindas, estilo SketchUp Desktop) --------
// Dados 100% reais: a lista vem de GET /api/v1/recent-files, que o backend
// popula sozinho toda vez que /scene/open tem sucesso (ver
// app/controllers/scene_controller.py); as thumbnails sao snapshots reais
// do canvas (ver captureAndUploadThumbnail acima), nao placeholders.

function hideWelcomeScreen() {
  welcomeScreenEl.classList.add("hidden");
}

/** Abre um caminho a partir da Pagina Inicial (card de recente ou campo de
 * "Abrir arquivo") -- reusa o mesmo handleOpen() do painel principal. */
async function openFromWelcomeScreen(path) {
  pathInputEl.value = path;
  const opened = await handleOpen();
  if (opened) hideWelcomeScreen();
}

async function loadRecentFilesIntoWelcomeScreen() {
  try {
    const entries = await listRecentFiles();
    renderRecentFiles(welcomeRecentGridEl, entries, openFromWelcomeScreen);
  } catch {
    renderRecentFiles(welcomeRecentGridEl, [], openFromWelcomeScreen);
  }
}

/** Reabre um rascunho de autosave (ver "Persistencia de sessao" no
 * README.md) -- a sessao volta associada ao arquivo ORIGINAL, "Salvar"
 * continua sobrescrevendo o arquivo de verdade do usuario. */
async function handleRecoverDraft(draftId) {
  setStatus("Recuperando sessao nao salva...");
  try {
    const sceneDTO = await recoverAutosaveDraft(draftId);
    const counts = applySceneDTO(sceneDTO);
    hideWelcomeScreen();
    setStatus(
      `Sessao recuperada -- ${counts.totalDefinitions} definicoes, ${counts.totalInstances} ` +
        `instancias. As edicoes nao salvas foram restauradas; "Salvar" sobrescreve o arquivo original.`
    );
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao recuperar sessao: ${detail}`, true);
  }
}

/** Descarta um rascunho de autosave sem recuperar e atualiza a grade. */
async function handleDiscardDraft(draftId) {
  try {
    await discardAutosaveDraft(draftId);
    setStatus("Rascunho descartado.");
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao descartar rascunho: ${detail}`, true);
  }
  loadAutosaveDraftsIntoWelcomeScreen();
}

async function loadAutosaveDraftsIntoWelcomeScreen() {
  try {
    const drafts = await listAutosaveDrafts();
    welcomeAutosaveSectionEl.style.display = drafts.length ? "" : "none";
    renderAutosaveDrafts(welcomeAutosaveGridEl, drafts, handleRecoverDraft, handleDiscardDraft);
  } catch {
    welcomeAutosaveSectionEl.style.display = "none";
  }
}

/** Ponto de entrada do app: tenta reconectar numa sessao JA ABERTA em
 * memoria no backend (cobre F5 na pagina sem perder edicoes nao salvas,
 * ver README.md "Persistencia de sessao") antes de mostrar a Pagina
 * Inicial. So quando nao ha sessao em memoria (backend reiniciado, ou
 * primeira abertura desta execucao) e que a Pagina Inicial aparece,
 * junto com qualquer rascunho de autosave pendente oferecido pra
 * recuperacao. */
async function boot() {
  try {
    const sceneDTO = await getCurrentSession();
    if (sceneDTO) {
      const counts = applySceneDTO(sceneDTO);
      hideWelcomeScreen();
      setStatus(
        `Sessao restaurada (reload da pagina) -- ${counts.totalDefinitions} definicoes, ` +
          `${counts.totalInstances} instancias. Nenhuma edicao foi perdida.`
      );
      return;
    }
  } catch {
    // backend inacessivel/erro inesperado -- segue pro fluxo normal da
    // Pagina Inicial em vez de travar o boot do app
  }
  loadRecentFilesIntoWelcomeScreen();
  loadAutosaveDraftsIntoWelcomeScreen();
}

/** Cria o modelo a partir do template clicado e fecha a Pagina Inicial
 * (reusa handleNewFromTemplate, mesmo padrao de openFromWelcomeScreen). */
async function newModelFromWelcomeScreen(templateId) {
  const created = await handleNewFromTemplate(templateId);
  if (created) hideWelcomeScreen();
}

welcomeTemplateCardEls.forEach((card) => {
  card.addEventListener("click", () => newModelFromWelcomeScreen(card.dataset.templateId));
});

welcomeCloseBtnEl.addEventListener("click", hideWelcomeScreen);

welcomeOpenBtnEl.addEventListener("click", () => {
  welcomeOpenRowEl.classList.toggle("visible");
  if (welcomeOpenRowEl.classList.contains("visible")) welcomePathInputEl.focus();
});

welcomeOpenConfirmBtnEl.addEventListener("click", () => {
  openFromWelcomeScreen(welcomePathInputEl.value.trim());
});
welcomePathInputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") openFromWelcomeScreen(welcomePathInputEl.value.trim());
});

boot();
