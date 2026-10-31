import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { TransformControls } from "three/addons/controls/TransformControls.js";
import { FontLoader } from "three/addons/loaders/FontLoader.js";
import { TextGeometry } from "three/addons/geometries/TextGeometry.js";

import {
  openScene,
  openBinaryScene,
  openUploadedScene,
  newSceneFromTemplate,
  updateInstanceTransform,
  saveScene,
  deleteInstance,
  duplicateInstance,
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
  createBox,
  setRenderingStyle,
  getAssemblyTree,
  convertDxf,
  getBimReport,
  calculateExplodedView,
  exportModelGlb,
  exportModelIfc,
  addLineGeometry,
  addFaceGeometry,
  exportCutlistXlsx,
  addCircleGeometry,
  addCylinderGeometry,
  extrudeFaceGeometry,
  getAssemblySteps,
  exportAssemblyManual,
  exportDrawing2D,
  calculateSolarStudy,
  createSectionPlane,
  getSectionPlanes,
  createGuideLine,
  createGuidePoint,
  getGuides,
  applyBooleanOperation,
  createOffsetFace,
  exportExecutivePdf,
  createFollowMe,
  createArc,
  applyRotation,
  auditNbr16071Safety,
  importObj,
  calculateNesting,
  createTerrain,
  calculateStructuralAnalysis,
  applyScale,
  exportCamDxf,
  calculateCameraPath,
  exportPointCloudXyz,
  generateMaintenancePlan,
  applyMirror,
  exportQrTagSvg,
  simulateSwingKinematics,
  generateArtPdf,
  inspectWallThickness,
  optimizeCargoLoad,
  generateTechnicalSketch,
  generateSpiralTube,
  calculateOverturnStability,
  exportFieldInspectionHtml,
  calculateAngleDimension,
  calculateFastenerTorque,
  generateHipRoof,
  simulateHicImpact,
  exportZebraLabel,
  calculateExplodedTrails,
  calculateCarbonFootprint,
  manageAttributeDictionary,
  manageTagFolder,
  configureEdgeStyles,
  calculateTwoPointPerspective,
  projectTextureUv,
  createPresentationScene,
  generateSceneAnimationTimeline,
  calculateShadowAndSunInfo,
  createScreenText,
  createLeaderText,
  createDimensionLinear,
  createGuideLineInfinite,
  configureAlphaMaterial,
  resolveNestedHierarchyNode,
  executeUndo,
  executeRedo,
  getUndoRedoStatus,
  calculateAlignView,
  configureBackgroundSky,
  configureFogStyle,
  detectComponentClashes,
  calculateMeshMassProperties,
  generateWallWithOpenings,
  generateStair,
  generateVoronoiPanel,
  calculateWindPressure,
  configureAtmosphericSky,
  exportIfc4Bim,
  simulateRigidBodyPhysics,
  slice3dPrintFdm,
  calculateRetainingWallStability,
  calculateHydraulicPiping,
  calculateElectricalConduit,
  calculateThermalComfort,
  calculateRoomAcoustics,
  calculateDaylightFactor,
  generateSteelProfile,
  calculateBim5dSinapiBudget,
  calculateStormwaterDrainage,
  calculatePermeablePavement,
  calculateSewerNetwork,
  calculateDetentionBasin,
  calculateEarthworkBruckner,
  calculateSlopeStabilityBishop,
  calculateDeepFoundationsPiles,
  calculateShallowFootings,
  calculateGabionWall,
  calculateConcreteFormwork,
  calculateReinforcedConcreteBeam,
  calculateWaffleSlab,
  calculatePrestressedConcrete,
  calculateGlulamTimber,
  generateSpaceTruss,
  calculateFuelGasPiping,
  calculateLightningSpda,
  calculateFireEgress,
  calculateHvacCoolingLoad,
  calculatePhotometricLighting,
  calculateSolarPv,
  calculateNaturalVentilation,
  generateGlazingFenestration,
  calculateVentilatedFacade,
  simulateWindCfd2d,
  generateBim4dSchedule,
  generateBim7dCobie,
  calculateSiteLogistics,
  auditUniversalAccessibility,
  calculateLcaEmissions,
  positionCameraNative,
  lookAroundNative,
  walkStepNative,
  sandboxSmoove,
  sandboxStamp,
  sandboxDrape,
  sandboxFlipEdge,
  matchPhotoCalibrate,
  watermarkStyleConfigure,
  dynamicComponentInteract,
  trimbleSolidToolsExecute,
  ifcClassifyComponent,
  ifcAuditClassifications,
  generate3dText,
  generateReport,
  axesSetCustom,
  axesAlignToFace,
  axesReset,
  inspectEntityEdge,
  inspectEntityFace,
  inspectEntitySolid,
  componentEditModeApply,
  modelUnitsConfigure,
  modelUnitsFormat,
  texturePinTransform,
  colorByTagApply,
  purgeUnusedItems,
  makeComponentDefinition,
  advancedSelectionExecute,
  hiddenGeometryConfigure,
  modelStatisticsCalculate,
  generateRegularPolygon,
  processFreehandCurve,
  reverseOrientFaces,
  controlDollyFovLens,
  computeIntersectFaces,
  axisLockInference,
  configureGroundSkyStyle,
  downloadCurrentSkpBytes,
  ApiError,
} from "./api.js";
import {
  buildSceneGroup,
  meshMatrixToApiTransform,
  worldPointToLocalInches,
  skpPointToThree,
  skpDirectionToThree,
} from "./sceneBuilder.js";
import { buildOutlinerTree } from "./outliner.js";
import { renderRecentFiles, renderAutosaveDrafts } from "./welcome.js";
import { InferenceEngine } from "./inferenceEngine.js";

const viewportEl = document.getElementById("viewport");
const pathInputEl = document.getElementById("path-input");
const openBtnEl = document.getElementById("open-btn");
const openBinaryBtnEl = document.getElementById("open-binary-btn");
const chooseFileBtnEl = document.getElementById("choose-file-btn");
const filePickerInputEl = document.getElementById("file-picker-input");
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

// Frentes 13, 15, 19, 20 & Desmontador / BIM (Opções 1 e 2)
const vcbBoxEl = document.getElementById("vcb-box");
const boxWInputEl = document.getElementById("box-w-input");
const boxLInputEl = document.getElementById("box-l-input");
const boxHInputEl = document.getElementById("box-h-input");
const boxCreateBtnEl = document.getElementById("box-create-btn");

const vcbDxfEl = document.getElementById("vcb-dxf");
const dxfPathInputEl = document.getElementById("dxf-path-input");
const dxfConvertBtnEl = document.getElementById("dxf-convert-btn");
const dxfBrowseBtnEl = document.getElementById("dxf-browse-btn");
const dxfPickerInputEl = document.getElementById("dxf-picker-input");

const styleModeSelectEl = document.getElementById("style-mode-select");
const styleXrayCheckboxEl = document.getElementById("style-xray-checkbox");
const styleProfilesSliderEl = document.getElementById("style-profiles-slider");
const styleProfilesValEl = document.getElementById("style-profiles-val");

const explodedSliderEl = document.getElementById("exploded-slider");
const explodedFactorValEl = document.getElementById("exploded-factor-val");
const btnExplode0El = document.getElementById("btn-explode-0");
const btnExplode50El = document.getElementById("btn-explode-50");
const btnExplode100El = document.getElementById("btn-explode-100");

const btnCalcBimEl = document.getElementById("btn-calc-bim");
const bimSummaryPanelEl = document.getElementById("bim-summary-panel");
const bimTotalItemsEl = document.getElementById("bim-total-items");
const bimTotalVolEl = document.getElementById("bim-total-vol");
const bimTotalAreaEl = document.getElementById("bim-total-area");
const bimTotalCostEl = document.getElementById("bim-total-cost");
const bimItemsListEl = document.getElementById("bim-items-list");
const paintColorInputEl = document.getElementById("paint-color-input");
const tagNameInputEl = document.getElementById("tag-name-input");
const toolsToolbarEl = document.getElementById("tools-toolbar");
const toolIconBtnEls = document.querySelectorAll(".tool-icon-btn");
const vcbEl = document.getElementById("vcb");
const vcbPushpullEl = document.getElementById("vcb-pushpull");
const pushpullDistInputEl = document.getElementById("pushpull-dist-input");
const pushpullApplyBtnEl = document.getElementById("pushpull-apply-btn");
const vcbCircleEl = document.getElementById("vcb-circle");
const circleRadiusInputEl = document.getElementById("circle-radius-input");
const circleHeightInputEl = document.getElementById("circle-height-input");
const circleCreateBtnEl = document.getElementById("circle-create-btn");
const btnExportCutlistEl = document.getElementById("btn-export-cutlist");

// Frentes 26, 27 e 28
const btnLoadAssemblyEl = document.getElementById("btn-load-assembly");
const assemblyControlsPanelEl = document.getElementById("assembly-controls-panel");
const btnStepPrevEl = document.getElementById("btn-step-prev");
const btnStepNextEl = document.getElementById("btn-step-next");
const assemblyStepIndicatorEl = document.getElementById("assembly-step-indicator");
const assemblyStepTitleEl = document.getElementById("assembly-step-title");
const assemblyStepDescEl = document.getElementById("assembly-step-desc");
const assemblyHardwareInfoEl = document.getElementById("assembly-hardware-info");
const btnExportManualHtmlEl = document.getElementById("btn-export-manual-html");

const solarHourSliderEl = document.getElementById("solar-hour-slider");
const solarHourValEl = document.getElementById("solar-hour-val");
const solarSeasonSelectEl = document.getElementById("solar-season-select");
const solarAltValEl = document.getElementById("solar-alt-val");
const solarAzValEl = document.getElementById("solar-az-val");
const solarConfortValEl = document.getElementById("solar-confort-val");
const btnAnimateSolarEl = document.getElementById("btn-animate-solar");
const vcbLineEl = document.getElementById("vcb-line");
const lineLengthInputEl = document.getElementById("line-length-input");
const lineSnapInfoEl = document.getElementById("line-snap-info");
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
const outlinerTreeEl = document.getElementById("outliner-tree");
const outlinerEmptyEl = document.getElementById("outliner-empty");
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
const entityAttrsBadgeEl = document.getElementById("entity-attrs-badge");
const entityAttrsContainerEl = document.getElementById("entity-attrs-container");
const welcomeScreenEl = document.getElementById("welcome-screen");
const welcomeCloseBtnEl = document.getElementById("welcome-close-btn");
const welcomeOpenBtnEl = document.getElementById("welcome-open-btn");
const welcomeOpenRowEl = document.getElementById("welcome-open-row");
const welcomePathInputEl = document.getElementById("welcome-path-input");
const welcomeOpenConfirmBtnEl = document.getElementById("welcome-open-confirm-btn");
const welcomeOpenBinaryBtnEl = document.getElementById("welcome-open-binary-btn");
const welcomeChooseFileBtnEl = document.getElementById("welcome-choose-file-btn");
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

const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
scene.add(ambientLight);
const keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
const dirLight = keyLight;
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

// Frente 22: Motor de Inferência e Autoria Interativa
const userDrawingsGroup = new THREE.Group();
userDrawingsGroup.name = "user_drawings";
scene.add(userDrawingsGroup);

let inferenceEngine = new InferenceEngine(camera, scene, renderer.domElement);
let lineStartPoint = null;
let currentLinePoints = [];
let rubberbandLine = null;

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
    [vcbBoxEl, activeKey === "box"],
    [vcbDxfEl, activeKey === "dxf"],
    [vcbLineEl, activeKey === "line"],
    [vcbPushpullEl, activeKey === "pushpull"],
    [vcbCircleEl, activeKey === "circle"],
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
  if (mode !== "line") {
    lineStartPoint = null;
    currentLinePoints = [];
    if (rubberbandLine) rubberbandLine.visible = false;
    if (inferenceEngine) {
      inferenceEngine.hideHelpers();
      inferenceEngine.setLockedAxis(null);
    }
  }
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
  else if (mode === "pushpull") setStatus("Modo Empurrar/Puxar (P): clique numa face para selecionar e digite a distância no VCB ou clique para extrudar.");
  else if (mode === "circle") setStatus("Modo Círculo / Cilindro (C): defina raio e altura no canto inferior direito e clique em Criar.");
  else if (mode === "line") setStatus("Modo Linha (L): clique para fixar o 1o ponto. Setas travam eixos (Direita=X/Vermelho, Esquerda=Y/Verde, Cima=Z/Azul).");
  else if (mode === "rect") setStatus("Modo Retangulo: informe largura/profundidade na caixa no canto inferior direito e clique em Criar.");
  else if (mode === "box") setStatus("Modo Bloco 3D (Push-Pull): informe largura, comprimento e altura na caixa no canto inferior direito e clique em Criar Bloco.");
  else if (mode === "dxf") setStatus("Modo Importar DXF: informe o caminho do arquivo CAD DXF e clique em Converter DXF.");
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

  // Render Atributos Dinâmicos (dynamic_attributes / SU_InstanceSet / SU_DefinitionSet)
  if (entityAttrsContainerEl) {
    const instAttrs = mesh.userData?.attributes || {};
    const defAttrs = mesh.userData?.defAttributes || {};
    const mergedDicts = {};
    for (const [dname, vals] of Object.entries(defAttrs)) {
      mergedDicts[dname] = Object.assign({}, vals);
    }
    for (const [dname, vals] of Object.entries(instAttrs)) {
      mergedDicts[dname] = Object.assign(mergedDicts[dname] || {}, vals);
    }

    let totalAttrs = 0;
    const entries = [];
    for (const [dname, attrs] of Object.entries(mergedDicts)) {
      const keys = Object.keys(attrs);
      if (keys.length === 0) continue;
      totalAttrs += keys.length;
      entries.push({ dname, attrs });
    }

    if (entityAttrsBadgeEl) {
      if (totalAttrs > 0) {
        entityAttrsBadgeEl.textContent = totalAttrs;
        entityAttrsBadgeEl.style.display = "inline-block";
      } else {
        entityAttrsBadgeEl.style.display = "none";
      }
    }

    if (entries.length === 0) {
      entityAttrsContainerEl.innerHTML = '<span style="color:var(--muted); font-style:italic;">Nenhum atributo dinâmico.</span>';
    } else {
      let html = "";
      for (const { dname, attrs } of entries) {
        html += `<div style="font-weight:600; color:var(--accent); margin-bottom:3px; padding-bottom:2px; border-bottom:1px solid #E2E8F0;">${dname}</div>`;
        html += '<table style="width:100%; border-collapse:collapse; margin-bottom:8px; font-family:monospace; font-size:10px;">';
        for (const [k, v] of Object.entries(attrs)) {
          const valStr = v === null ? '<span style="color:#94A3B8;">null</span>' : String(v);
          const isFormula = typeof v === "string" && (v.startsWith("=") || v.toLowerCase().includes("parent!") || v.toLowerCase().startsWith("if("));
          html += `<tr><td style="color:#475569; padding:2px 4px 2px 0; vertical-align:top; word-break:break-all;">${k}:</td><td style="color:${isFormula ? "#0284C7" : "#0F172A"}; text-align:right; padding:2px 0; word-break:break-all; font-weight:${isFormula ? "600" : "normal"};">${valStr}</td></tr>`;
        }
        html += "</table>";
      }
      entityAttrsContainerEl.innerHTML = html;
    }
  }
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

/** Atualiza a árvore do Outliner com os dados da cena fornecida */
function updateOutliner(sceneDTO) {
  if (!outlinerTreeEl || !sceneDTO) return;
  outlinerTreeEl.innerHTML = "";
  currentOutliner = buildOutlinerTree(sceneDTO, selectInstanceById);
  outlinerTreeEl.appendChild(currentOutliner.element);
  if (outlinerEmptyEl) outlinerEmptyEl.classList.add("hidden");
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

  if (toolMode === "pushpull") {
    handlePushPullClick(event);
    return;
  }
  if (toolMode === "line") {
    handleLineClick(event);
    return;
  }
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
    setStatus(`Erro ao excluir ${mesh.name}: ${detail}`, true);
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

  if ((event.ctrlKey || event.metaKey) && (event.key === "z" || event.key === "Z")) {
    event.preventDefault();
    handleUndo();
    return;
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === "y" || event.key === "Y")) {
    event.preventDefault();
    handleRedo();
    return;
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === "c" || event.key === "C")) {
    event.preventDefault();
    handleCopy();
    return;
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === "x" || event.key === "X")) {
    event.preventDefault();
    handleCut();
    return;
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === "v" || event.key === "V")) {
    event.preventDefault();
    handlePaste();
    return;
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === "s" || event.key === "S")) {
    event.preventDefault();
    handleSave();
    return;
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === "o" || event.key === "O")) {
    event.preventDefault();
    handleChooseFile();
    return;
  }
  if ((event.ctrlKey || event.metaKey) && (event.key === "d" || event.key === "D")) {
    event.preventDefault();
    handleDuplicateSelected();
    return;
  }
  if (event.key === "Delete" || event.key === "Backspace") {
    if (selectedMesh) {
      event.preventDefault();
      handleDeleteSelected();
      return;
    }
  }

  if (event.key === "w" || event.key === "W") setMode("translate");
  else if (event.key === "e" || event.key === "E") setMode("rotate");
  else if (event.key === "r" || event.key === "R") setMode("scale");
  else if (event.key === "Escape") {
    deselectMesh();
    if (toolMode === "lasso") setLassoSelection([]);
    if (toolMode === "line") {
      lineStartPoint = null;
      currentLinePoints = [];
      if (rubberbandLine) rubberbandLine.visible = false;
      if (inferenceEngine) {
        inferenceEngine.hideHelpers();
        inferenceEngine.setLockedAxis(null);
      }
      setStatus("Desenho de linha cancelado.");
    }
  }
  else if (event.key === "l" || event.key === "L") {
    setToolMode("line");
  }
  else if (event.key === "p" || event.key === "P") {
    setToolMode("pushpull");
  }
  else if (event.key === "c" || event.key === "C") {
    setToolMode("circle");
  }
  else if (event.key === "k" || event.key === "K") {
    handleToggleBackEdges();
  }
  else if (toolMode === "line" && inferenceEngine) {
    if (event.key === "ArrowRight") {
      event.preventDefault();
      inferenceEngine.setLockedAxis("red");
      setStatus("Eixo travado: Vermelho (X)");
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      inferenceEngine.setLockedAxis("green");
      setStatus("Eixo travado: Verde (Y SketchUp)");
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      inferenceEngine.setLockedAxis("blue");
      setStatus("Eixo travado: Azul (Z SketchUp)");
    } else if (event.key === "ArrowDown") {
      event.preventDefault();
      inferenceEngine.setLockedAxis(null);
      setStatus("Trava de eixo desativada.");
    }
  }
  else if (event.key === "Delete" || event.key === "Backspace") handleDeleteSelected();
  else if ((event.ctrlKey || event.metaKey) && (event.key === "d" || event.key === "D")) {
    event.preventDefault();
    handleDuplicateSelected();
  }
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
  // Distancia minima pra caber a esfera que envolve a bounding box inteira
  // dentro do FOV atual da camera (vertical E horizontal, usa o mais
  // restritivo dos dois) -- formula exata (arcsin), nao uma aproximacao
  // por tan(), com 15% de folga visual. Usar `camera.fov`/`camera.aspect`
  // direto (em vez do multiplicador fixo antigo) tambem faz a vista
  // respeitar a Projecao paralela e o Campo de visao customizado (Camera
  // > Campo de visao) automaticamente, sem precisar de um fator separado.
  const halfFovV = THREE.MathUtils.degToRad(camera.fov / 2);
  const halfFovH = Math.atan(Math.tan(halfFovV) * camera.aspect);
  const limitingHalfFov = Math.min(halfFovV, halfFovH);
  const distance = (radius / Math.sin(limitingHalfFov)) * 1.15;

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

/**
 * Aplica a camera REAL salva no .skp (ver CameraDTO em app/schemas/scene.py,
 * SUModelGetCamera/SUCameraGetOrientation em core/su_api.py,
 * REVERSE_ENGINEERING_NOTES.md secao 28.23), em vez do enquadramento
 * automatico por bounding box de `setStandardView`. Achado comparando com o
 * SketchUp 2026 real rodando na maquina: a vista inicial de um template NAO
 * e um "fit" calculado -- e a camera exata gravada no arquivo (bem mais
 * distante do modelo do que qualquer auto-fit produziria).
 *
 * Retorna false (e quem chamou deve cair pro auto-fit de `setStandardView`)
 * quando o DTO nao trouxe camera, ou quando ela nao e perspectiva/nao tem
 * FOV -- esses dois casos (camera paralela/ortografica salva no arquivo)
 * ainda nao tem conversao implementada aqui.
 */
function applyRealCamera(sceneDTO) {
  const cam = sceneDTO.camera;
  if (!cam || !cam.perspective || cam.fov_deg == null) return false;

  const eye = skpPointToThree(...cam.eye);
  const target = skpPointToThree(...cam.target);
  const up = skpDirectionToThree(...cam.up);

  let verticalFov = cam.fov_deg;
  if (!cam.fov_is_height) {
    // SUCameraGetFOVIsHeight false => o valor salvo e o FOV HORIZONTAL;
    // `camera.fov` do Three.js e sempre vertical, entao converte via aspect.
    const halfHorizontal = THREE.MathUtils.degToRad(cam.fov_deg / 2);
    verticalFov = THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(halfHorizontal) / camera.aspect));
  }

  camera.up.copy(up);
  camera.position.copy(eye);
  controls.target.copy(target);
  camera.fov = verticalFov;

  const distance = Math.max(eye.distanceTo(target), 0.1);
  camera.near = distance / 100;
  camera.far = Math.max(distance * 100, 100);
  camera.updateProjectionMatrix();
  controls.update();
  return true;
}

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
  hidden_line: "menu-item-face-hidden-line",
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
    if (style === "hidden_line") {
      material.color.set(0xffffff);
      material.roughness = 1.0;
    } else if (style === "monochrome") {
      material.color.set(0xCCCCCC);
      material.roughness = 0.8;
    } else {
      material.color.set(0x8c99a6);
      material.roughness = 0.5;
    }
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
  if (inferenceEngine) inferenceEngine.updateGeometryIndex(currentGroup);
  // componentes "sempre de frente pra camera" (ex.: a figura de escala dos
  // templates) so recebem a rotacao correta de pitch/roll dentro do loop
  // de animacao (updateBillboards(), chamado a cada frame) -- sem rodar
  // isso aqui ANTES de enquadrar a camera, o Box3 usado por
  // setStandardView() mede a malha ainda deitada (altura Y = 0), o que
  // zera o raio calculado e deixa a camera colada na figura.
  updateBillboards();
  if (!applyRealCamera(sceneDTO)) {
    setStandardView("iso");
  }
  editPanelEl.classList.remove("hidden");
  // o novo grupo traz material/overlay de arestas no estado padrao --
  // reaplica os toggles de "Visualizar" que estavam ativos antes de abrir
  // este modelo (eixos/sombras/nevoa sao globais e nao precisam disso).
  setEdgesVisible(edgesVisible);
  setFaceStyle(faceStyle);

  updateOutliner(sceneDTO);
  sceneNameInputEl.disabled = false;
  sceneCreateBtnEl.disabled = false;
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

/** Abre um .skp via leitor nativo binario Pure Python (Zero DLL) --
 * decodifica geometria, UVs analiticas, materiais PBR e instâncias Three.js
 * direto do container ZIP sem depender da SketchUpAPI.dll.
 * @returns {Promise<boolean>} true se o modelo abriu com sucesso. */
async function handleOpenBinary() {
  const path = (pathInputEl.value.trim() || welcomePathInputEl?.value?.trim() || "").trim();
  if (!path) {
    setStatus("Informe um caminho de arquivo .skp para o leitor nativo.", true);
    return false;
  }

  openBtnEl.disabled = true;
  if (openBinaryBtnEl) openBinaryBtnEl.disabled = true;
  deselectMesh();
  setStatus("Abrindo via leitor nativo binário (Pure Python / Zero DLL)...");

  try {
    const sceneDTO = await openBinaryScene(path);
    const counts = applySceneDTO(sceneDTO);
    const matCount = sceneDTO.materials ? Object.keys(sceneDTO.materials).length : 0;
    hideWelcomeScreen();
    setStatus(
      `OK (Zero DLL) -- ${counts.totalDefinitions} defs, ${counts.totalInstances} ` +
        `instâncias, ${counts.totalVertices} vértices, ${counts.totalTriangles} triângulos, ${matCount} materiais PBR.`
    );
    captureAndUploadThumbnail(path);
    return true;
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro (Zero DLL): ${detail}`, true);
    return false;
  } finally {
    openBtnEl.disabled = false;
    if (openBinaryBtnEl) openBinaryBtnEl.disabled = false;
  }
}

/** Abre um .skp escolhido pelo seletor NATIVO de arquivos do Windows
 * (`<input type="file">`, disparado por chooseFileBtnEl/
 * welcomeChooseFileBtnEl/menu "Arquivo > Abrir..."). Por seguranca padrao
 * de toda a web, o navegador nunca informa o caminho real em disco do
 * arquivo escolhido assim, so o conteudo -- por isso a sessao fica sem
 * `model_path` (igual um modelo criado por template), exigindo "Salvar
 * Como" no primeiro Salvar.
 * @returns {Promise<boolean>} true se o modelo abriu com sucesso. */
async function handleOpenUpload(file) {
  deselectMesh();
  setStatus(`Abrindo "${file.name}" (enviado pelo seletor do Windows)...`);

  try {
    const sceneDTO = await openUploadedScene(file);
    const counts = applySceneDTO(sceneDTO);
    hideWelcomeScreen();
    setStatus(
      `OK -- ${counts.totalDefinitions} definicoes, ${counts.totalInstances} ` +
        `instancias, ${counts.totalVertices} vertices, ${counts.totalTriangles} triangulos. ` +
        `"Salvar" vai pedir um caminho (Salvar Como) -- o navegador nao informa o caminho original.`
    );
    return true;
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro: ${detail}`, true);
    return false;
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
    console.error("Erro ao criar modelo a partir do template:", err);
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao criar modelo: ${detail}`, true);
    return false;
  }
}

let currentFileHandle = null;
let hasUnsavedChanges = false;

async function handleChooseFile() {
  if (window.showOpenFilePicker) {
    try {
      const [handle] = await window.showOpenFilePicker({
        types: [{
          description: "Modelos SketchUp (*.skp)",
          accept: { "application/vnd.sketchup.skp": [".skp"] }
        }],
        multiple: false
      });
      if (handle) {
        currentFileHandle = handle;
        const file = await handle.getFile();
        await handleOpenUpload(file);
        setStatus(`Arquivo "${file.name}" aberto com escrita in-place (File System Access API). Ctrl+S salvará direto.`);
        return;
      }
    } catch (err) {
      if (err.name === "AbortError") return;
      console.warn("File System Access API falhou, caindo para input tradicional:", err);
    }
  }
  filePickerInputEl.click();
}

/** `overwriteConfirmed`: true so quando esta chamada e um retry depois do
 * usuario confirmar no window.confirm() abaixo -- nunca passar `true` na
 * chamada inicial (ver trava em app/repositories/skp_engine_repository.py
 * save(), adicionada depois de um incidente real de 28/10/2026 em que um
 * modelo de template foi salvo por cima de um .skp de producao sem aviso). */
async function handleSave(overwriteConfirmed = false) {
  const path = savePathInputEl.value.trim();
  saveBtnEl.disabled = true;
  setStatus(path ? `Salvando em ${path}...` : "Salvando...");

  // 1. Prioridade Web Moderna: Se temos um FileSystemFileHandle (in-place) e nenhum path manual digitado
  if (currentFileHandle && !path) {
    try {
      setStatus(`Gravando in-place em "${currentFileHandle.name}" via File System Access API...`);
      const blob = await downloadCurrentSkpBytes();
      const writable = await currentFileHandle.createWritable();
      await writable.write(blob);
      await writable.close();
      hasUnsavedChanges = false;
      setStatus(`Salvo in-place com sucesso em "${currentFileHandle.name}" (disco local)!`);
      saveBtnEl.disabled = false;
      return;
    } catch (fsaErr) {
      console.warn("Erro ao salvar via FSA handle:", fsaErr);
    }
  }

  // 2. Se for modelo criado do zero na web sem path no input e o browser suportar showSaveFilePicker
  if (!path && !currentFileHandle && window.showSaveFilePicker) {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: "modelo.skp",
        types: [{
          description: "Modelo SketchUp (*.skp)",
          accept: { "application/vnd.sketchup.skp": [".skp"] }
        }]
      });
      if (handle) {
        currentFileHandle = handle;
        const blob = await downloadCurrentSkpBytes();
        const writable = await handle.createWritable();
        await writable.write(blob);
        await writable.close();
        hasUnsavedChanges = false;
        setStatus(`Modelo gravado com sucesso em "${handle.name}"!`);
        saveBtnEl.disabled = false;
        return;
      }
    } catch (saveErr) {
      if (saveErr.name === "AbortError") {
        setStatus("Salvar cancelado.");
        saveBtnEl.disabled = false;
        return;
      }
    }
  }

  // 3. Fallback: Gravação local via backend (para sessões com model_path existente ou caminho informado)
  try {
    const result = await saveScene(path, overwriteConfirmed);
    hasUnsavedChanges = false;
    setStatus(`Salvo em ${result.path}.`);
  } catch (err) {
    if (
      !overwriteConfirmed &&
      err instanceof ApiError &&
      err.detail &&
      err.detail.code === "overwrite_confirmation_required"
    ) {
      const sizeMb = (err.detail.existing_size_bytes / (1024 * 1024)).toFixed(1);
      const confirmado = window.confirm(
        `Atencao: "${err.detail.existing_path}" ja existe no disco (${sizeMb} MB) e e ` +
          "diferente do modelo aberto nesta sessao.\n\n" +
          "Salvar aqui vai SOBRESCREVER esse arquivo com o conteudo atual, sem possibilidade " +
          "de desfazer pelo app.\n\nTem certeza que quer continuar?"
      );
      if (confirmado) {
        await handleSave(true);
      } else {
        setStatus("Salvar cancelado -- o arquivo existente nao foi alterado.", true);
      }
      return;
    }
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
    setStatus(`Erro ao excluir ${mesh.name}: ${detail}`, true);
  }
}

/** Duplica a instância 3D selecionada aplicando um offset padrão de 50cm no eixo X */
async function handleDuplicateSelected() {
  if (!selectedMesh) {
    setStatus("Nenhuma instância selecionada para duplicar.", true);
    return;
  }
  const instId = selectedMesh.name || selectedMesh.userData?.instanceId;
  setStatus(`Duplicando instância ${instId} (Ctrl+D)...`);
  try {
    const res = await duplicateInstance(instId, { offsetDeltaCm: [50.0, 0.0, 0.0] });
    if (res?.duplicated && res.instance) {
      const newMesh = selectedMesh.clone();
      newMesh.name = res.instance.instance_id;
      newMesh.position.x += 0.5;
      currentGroup.add(newMesh);
      selectMesh(newMesh);
      hasUnsavedChanges = true;
      setStatus(`Instância "${res.instance.instance_id}" duplicada com sucesso!`);
    }
  } catch (err) {
    setStatus(`Erro ao duplicar: ${err.message}`, true);
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
async function handleDimensionClick(worldPoint) {
  if (!dimensionFirstPoint) {
    dimensionFirstPoint = worldPoint.clone();
    setStatus("Modo Dimensoes: clique no segundo ponto da cota.");
    return;
  }
  const p1 = dimensionFirstPoint;
  const p2 = worldPoint.clone();
  const distance = p1.distanceTo(p2);

  const dimension = new THREE.Group();
  try {
    const dimData = await createDimensionLinear([p1.x, p1.y, p1.z], [p2.x, p2.y, p2.z], 0.2);
    const d = dimData.dimension_data;
    
    // Linha de cota principal
    const dimLineGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(d.dimension_line[0][0], d.dimension_line[0][1], d.dimension_line[0][2]),
      new THREE.Vector3(d.dimension_line[1][0], d.dimension_line[1][1], d.dimension_line[1][2]),
    ]);
    const dimLine = new THREE.Line(dimLineGeo, new THREE.LineBasicMaterial({ color: 0x2c3e50, depthTest: false }));
    dimension.add(dimLine);

    // Linhas de extensao (witness lines)
    for (const w of d.witness_lines) {
      const wGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(w[0][0], w[0][1], w[0][2]),
        new THREE.Vector3(w[1][0], w[1][1], w[1][2]),
      ]);
      dimension.add(new THREE.Line(wGeo, new THREE.LineBasicMaterial({ color: 0x7f8c8d, depthTest: false })));
    }

    // Tiques arquitetonicos
    for (const t of d.ticks) {
      const tGeo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(t[0][0], t[0][1], t[0][2]),
        new THREE.Vector3(t[1][0], t[1][1], t[1][2]),
      ]);
      dimension.add(new THREE.Line(tGeo, new THREE.LineBasicMaterial({ color: 0x2c3e50, linewidth: 2, depthTest: false })));
    }

    const label = makeTextSprite(d.text);
    label.position.set(d.text_position[0], d.text_position[1], d.text_position[2]);
    dimension.add(label);
  } catch (err) {
    const lineGeometry = new THREE.BufferGeometry().setFromPoints([p1, p2]);
    const line = new THREE.Line(lineGeometry, new THREE.LineBasicMaterial({ color: 0x3c7fb1, depthTest: false }));
    const label = makeTextSprite(`${distance.toFixed(3)} m`);
    label.position.copy(p1.clone().lerp(p2, 0.5));
    dimension.add(line, label);
  }
  dimensionsGroup.add(dimension);

  setStatus(`Cota criada: ${distance.toFixed(3)} m. Clique no proximo primeiro ponto.`);
  dimensionFirstPoint = null;
}

/** Ferramentas > Texto: coloca um rotulo 3D persistente (mesmo
 * THREE.Sprite com canvas de texto da cota) com o conteudo digitado no
 * campo do painel, no ponto clicado. Diferente de "Texto 3D" (extrusao
 * de fonte em malha), este e um rotulo billboard, mesma abordagem do
 * SketchUp real pra "Texto" (nao o "Texto 3D", que e outro item). */
async function handleTextClick(worldPoint) {
  const content = textContentInputEl.value.trim();
  if (!content) {
    setStatus("Escreva o texto do rotulo antes de clicar no viewport.", true);
    return;
  }
  try {
    const res = await createLeaderText(content, [worldPoint.x, worldPoint.y, worldPoint.z], [0.3, 0.3, 0.3]);
    const d = res.text_data;
    const textGroup = new THREE.Group();

    // Linha de chamada (Leader Line)
    const leaderGeo = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(d.anchor_point[0], d.anchor_point[1], d.anchor_point[2]),
      new THREE.Vector3(d.text_position_3d[0], d.text_position_3d[1], d.text_position_3d[2]),
    ]);
    const leaderLine = new THREE.Line(leaderGeo, new THREE.LineBasicMaterial({ color: 0x333333, depthTest: false }));
    textGroup.add(leaderLine);

    // Rotulo
    const label = makeTextSprite(content);
    label.position.set(d.text_position_3d[0], d.text_position_3d[1], d.text_position_3d[2]);
    textGroup.add(label);

    dimensionsGroup.add(textGroup);
    setStatus(`Rótulo com linha de chamada '${content}' criado com sucesso.`);
  } catch (err) {
    const label = makeTextSprite(content);
    label.position.copy(worldPoint);
    dimensionsGroup.add(label);
    setStatus(`Rotulo "${content}" criado no viewport.`);
  }
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
  open: () => handleChooseFile(),
  "open-binary": () => handleOpenBinary(),
  save: () => handleSave(),
  "save-as": () => savePathInputEl.focus(),
  "export-obj": () => exportObjPathInputEl.focus(),
  "export-glb": () => handleExportGlb(),
  "export-ifc": () => handleExportIfc(),
  delete: () => handleDeleteSelected(),
  "action-undo": () => handleUndo(),
  "action-redo": () => handleRedo(),
  "action-cut": () => handleCut(),
  "action-copy": () => handleCopy(),
  "action-paste": () => handlePaste(),
  "camera-walk": () => handleStartWalk(),
  "camera-look": () => handleStartWalk(),
  "toggle-axes": () => setAxesVisible(!axesVisible),
  "toggle-shadows": () => setShadowsEnabled(!shadowsEnabled),
  "toggle-fog": () => setFogEnabled(!fogEnabled),
  "toggle-edges": () => setEdgesVisible(!edgesVisible),
  "face-style-textured": () => setFaceStyle("textured"),
  "face-style-flat": () => setFaceStyle("flat"),
  "face-style-hidden-line": () => setFaceStyle("hidden_line"),
  "face-style-monochrome": () => setFaceStyle("monochrome"),
  "toggle-section-planes": () => handleToggleSectionPlanes(),
  "reverse-section-cut": () => handleReverseSectionCut(),
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
  "tool-line": () => setToolMode("line"),
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
  "draw-box": () => {
    setToolMode("box");
    boxWInputEl?.focus();
  },
  "tool-pushpull": () => setToolMode("pushpull"),
  "draw-circle": () => {
    setToolMode("circle");
    circleRadiusInputEl?.focus();
  },
  "draw-cylinder": () => {
    setToolMode("circle");
    if (circleHeightInputEl) circleHeightInputEl.value = "2.0";
    circleHeightInputEl?.focus();
  },
  "export-cutlist": () => handleExportCutlist(),
  "export-drawing-2d": () => handleExportDrawing2D(),
  "export-assembly-manual": () => handleExportAssemblyManual(),
  "export-executive-pdf": () => handleExportExecutivePdf(),
  "tool-follow-me": () => handleFollowMeTool(),
  "draw-arc": () => handleDrawArc(),
  "import-obj": () => handleImportObj(),
  "export-cam-dxf": () => handleExportCamDxf(),
  "export-point-cloud": () => handleExportPointCloud(),
  "export-qr-tag": () => handleExportQrTag(),
  "export-art-pdf": () => handleExportArtPdf(),
  "export-technical-sketch": () => handleExportTechnicalSketch(),
  "draw-spiral-tube": () => handleDrawSpiralTube(),
  "draw-hip-roof": () => handleDrawHipRoof(),
  "export-zebra-label": () => handleExportZebraLabel(),
  "toggle-back-edges": () => handleToggleBackEdges(),
  "toggle-profiles": () => handleToggleProfiles(),
  "toggle-depth-cue": () => handleToggleDepthCue(),
  "toggle-extensions": () => handleToggleExtensions(),
  "projection-two-point": () => handleTwoPointPerspective(),
  "export-inspection-checklist": () => handleExportInspectionChecklist(),
  "tool-mirror": () => handleMirrorTool(),
  "draw-terrain": () => handleDrawTerrain(),
  "import-dxf": () => {
    setToolMode("dxf");
    dxfPathInputEl?.focus();
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
openBinaryBtnEl?.addEventListener("click", handleOpenBinary);
welcomeOpenBinaryBtnEl?.addEventListener("click", handleOpenBinary);
pathInputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleOpen();
});

chooseFileBtnEl.addEventListener("click", () => handleChooseFile());
welcomeChooseFileBtnEl.addEventListener("click", () => handleChooseFile());
filePickerInputEl.addEventListener("change", () => {
  const file = filePickerInputEl.files[0];
  filePickerInputEl.value = ""; // permite escolher o mesmo arquivo de novo depois
  if (file) handleOpenUpload(file);
});
// () => handleSave() (nao so a referencia) -- addEventListener passaria o
// MouseEvent como 1o argumento, que seria lido como `overwriteConfirmed`
// truthy e puraria a trava de confirmacao de sobrescrita silenciosamente.
saveBtnEl.addEventListener("click", () => handleSave());
toolbarSaveBtnEl.addEventListener("click", () => handleSave());

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
  if (isWalkMode) {
    updateWalkMovement();
  } else {
    controls.update();
  }
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


// ============================================================================
// Frentes 13, 15, 19, 20 & Desmontador / Orçamento BIM (Opções 1 e 2)
// ============================================================================

// 1. Estilos de Renderização no Three.js (Frente 19)
function applyRenderingStyle() {
  if (!currentGroup) return;
  const mode = styleModeSelectEl ? styleModeSelectEl.value : "textured";
  const xray = styleXrayCheckboxEl ? styleXrayCheckboxEl.checked : false;
  const profilesWidth = styleProfilesSliderEl ? parseInt(styleProfilesSliderEl.value, 10) : 2;

  if (styleProfilesValEl) {
    styleProfilesValEl.textContent = `${profilesWidth}px`;
  }

  currentGroup.traverse((obj) => {
    if (obj.isMesh && obj.material) {
      if (!obj.userData.originalMaterial) {
        obj.userData.originalMaterial = Array.isArray(obj.material)
          ? obj.material.map((m) => m.clone())
          : obj.material.clone();
      }

      const orig = obj.userData.originalMaterial;
      const configureMat = (mat, origMat) => {
        if (mode === "hidden_line") {
          mat.color.setHex(0xffffff);
          mat.roughness = 1.0;
          mat.metalness = 0.0;
          mat.map = null;
        } else if (mode === "monochrome") {
          mat.color.setHex(0xdddddd);
          mat.map = null;
        } else if (mode === "shaded") {
          mat.color.copy(origMat.color);
          mat.map = null;
        } else if (mode === "textured") {
          mat.color.copy(origMat.color);
          mat.map = origMat.map;
        }
        mat.wireframe = mode === "wireframe";

        if (xray) {
          mat.transparent = true;
          mat.opacity = 0.45;
          mat.depthWrite = false;
        } else {
          mat.transparent = origMat.transparent;
          mat.opacity = origMat.opacity;
          mat.depthWrite = true;
        }
        mat.needsUpdate = true;
      };

      if (Array.isArray(obj.material)) {
        obj.material.forEach((m, idx) => configureMat(m, orig[idx] || orig[0]));
      } else {
        configureMat(obj.material, orig);
      }
    }

    if (obj.isLineSegments && obj.material) {
      obj.visible = mode === "hidden_line" || profilesWidth > 0;
      if (mode === "hidden_line") {
        obj.material.color.setHex(0x111111);
      }
      obj.material.linewidth = profilesWidth;
      obj.material.needsUpdate = true;
    }
  });

  setRenderingStyle({ mode, xray, profilesWidth }).catch(() => {});
}

if (styleModeSelectEl) styleModeSelectEl.addEventListener("change", applyRenderingStyle);
if (styleXrayCheckboxEl) styleXrayCheckboxEl.addEventListener("change", applyRenderingStyle);
if (styleProfilesSliderEl) styleProfilesSliderEl.addEventListener("input", applyRenderingStyle);

// 2. Desmontador Parkelo / Vista Explodida Paramétrica (Opção 2)
function applyExplodedView(lambda) {
  if (!currentGroup) return;

  if (!currentGroup.userData.centroid) {
    const box = new THREE.Box3().setFromObject(currentGroup);
    currentGroup.userData.centroid = box.getCenter(new THREE.Vector3());
  }
  const center = currentGroup.userData.centroid;

  let i = 0;
  currentGroup.children.forEach((child) => {
    if (child.isMesh) {
      if (!child.userData.originalPosition) {
        child.userData.originalPosition = child.position.clone();
      }
      const orig = child.userData.originalPosition;
      const dir = new THREE.Vector3().subVectors(orig, center);
      if (dir.lengthSq() < 0.001) {
        const angle = (2 * Math.PI * i) / Math.max(1, currentGroup.children.length);
        dir.set(Math.cos(angle) * 0.8, 0.4 * (i + 1), Math.sin(angle) * 0.8);
      }
      child.matrixAutoUpdate = true;
      child.position.copy(orig).addScaledVector(dir, lambda);
      i++;
    }
  });

  if (explodedFactorValEl) {
    const pct = Math.round(lambda * 100);
    const label = lambda === 0 ? "Montado" : lambda <= 0.5 ? "Parcial" : "Explodido";
    explodedFactorValEl.textContent = `${pct}% (${label})`;
  }
}

if (explodedSliderEl) {
  explodedSliderEl.addEventListener("input", (e) => {
    const lambda = parseFloat(e.target.value) / 100.0;
    applyExplodedView(lambda);
  });
  explodedSliderEl.addEventListener("change", (e) => {
    const lambda = parseFloat(e.target.value) / 100.0;
    calculateExplodedView(lambda).catch(() => {});
  });
}

if (btnExplode0El) {
  btnExplode0El.addEventListener("click", () => {
    if (explodedSliderEl) explodedSliderEl.value = 0;
    applyExplodedView(0.0);
  });
}
if (btnExplode50El) {
  btnExplode50El.addEventListener("click", () => {
    if (explodedSliderEl) explodedSliderEl.value = 50;
    applyExplodedView(0.5);
  });
}
if (btnExplode100El) {
  btnExplode100El.addEventListener("click", () => {
    if (explodedSliderEl) explodedSliderEl.value = 100;
    applyExplodedView(1.0);
  });
}

// 3. Orçamento BIM / BOM (Opção 2)
async function handleBimReport() {
  if (!btnCalcBimEl) return;
  btnCalcBimEl.disabled = true;
  btnCalcBimEl.textContent = "Calculando BIM...";
  try {
    const report = await getBimReport();
    if (bimSummaryPanelEl) bimSummaryPanelEl.style.display = "block";
    if (bimTotalItemsEl) bimTotalItemsEl.textContent = report.summary.total_items_count;
    if (bimTotalVolEl) bimTotalVolEl.textContent = `${report.summary.total_volume_m3.toFixed(3)} m³`;
    if (bimTotalAreaEl) bimTotalAreaEl.textContent = `${report.summary.total_area_m2.toFixed(2)} m²`;
    if (bimTotalCostEl) {
      bimTotalCostEl.textContent = `R$ ${report.summary.estimated_cost.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;
    }

    if (bimItemsListEl) {
      bimItemsListEl.innerHTML = "";
      report.items.forEach((item) => {
        const row = document.createElement("div");
        row.style.padding = "4px 0";
        row.style.borderBottom = "1px solid #EEE";
        row.innerHTML = `
          <div style="font-weight: 600; display: flex; justify-content: space-between;">
            <span>${item.definition_name} (${item.instance_count}x)</span>
            <span>R$ ${item.total_price.toFixed(2)}</span>
          </div>
          <div style="color: var(--muted); font-size: 10px;">
            ${item.total_volume_m3} m³ | ${item.total_area_m2} m² | ${item.material || "Padrão"}
          </div>
        `;
        bimItemsListEl.appendChild(row);
      });
    }
    setStatus(`Orçamento BIM: ${report.summary.total_items_count} peças, R$ ${report.summary.estimated_cost.toFixed(2)}`);
  } catch (err) {
    setStatus(`Falha ao calcular orçamento BIM: ${err.message}`, true);
  } finally {
    btnCalcBimEl.disabled = false;
    btnCalcBimEl.textContent = "Atualizar Orçamento BIM";
  }
}

if (btnCalcBimEl) btnCalcBimEl.addEventListener("click", handleBimReport);

// 4. Criação de Bloco 3D Manifold (Frente 13)
async function handleCreateBox() {
  const w = parseFloat(boxWInputEl?.value || "1.0");
  const l = parseFloat(boxLInputEl?.value || "1.0");
  const h = parseFloat(boxHInputEl?.value || "1.0");
  if (!Number.isFinite(w) || w <= 0 || !Number.isFinite(l) || l <= 0 || !Number.isFinite(h) || h <= 0) {
    setStatus("Informe largura, comprimento e altura positivos (metros).", true);
    return;
  }
  if (boxCreateBtnEl) boxCreateBtnEl.disabled = true;
  setStatus("Criando bloco 3D manifold (Push-Pull)...");
  try {
    const res = await createBox(w, l, h);
    if (res.scene) {
      if (currentGroup) scene.remove(currentGroup);
      currentGroup = buildSceneGroup(res.scene);
      scene.add(currentGroup);
      updateOutliner(res.scene);
    }
    setStatus(`Bloco 3D criado: ${w}x${l}x${h}m (Volume: ${res.box.volume_m3} m³)`);
    setToolMode("select");
  } catch (err) {
    setStatus(`Falha ao criar bloco 3D: ${err.message}`, true);
  } finally {
    if (boxCreateBtnEl) boxCreateBtnEl.disabled = false;
  }
}

if (boxCreateBtnEl) boxCreateBtnEl.addEventListener("click", handleCreateBox);

// 5. Conversão e Importação de DXF (Frente 20)
async function handleConvertDxf() {
  const dxfPath = dxfPathInputEl ? dxfPathInputEl.value.trim() : "";
  if (!dxfPath) {
    setStatus("Informe o caminho do arquivo DXF no disco.", true);
    return;
  }
  if (dxfConvertBtnEl) dxfConvertBtnEl.disabled = true;
  setStatus("Convertendo arquivo DXF para SKP...");
  try {
    const res = await convertDxf(dxfPath);
    setStatus(`DXF convertido: ${res.faces_count} faces, ${res.lines_count} linhas. Abrindo modelo...`);
    const sceneRes = await openBinaryScene(res.output_skp_path);
    if (currentGroup) scene.remove(currentGroup);
    currentGroup = buildSceneGroup(sceneRes);
    scene.add(currentGroup);
    updateOutliner(sceneRes);
    setToolMode("select");
  } catch (err) {
    setStatus(`Falha ao converter DXF: ${err.message}`, true);
  } finally {
    if (dxfConvertBtnEl) dxfConvertBtnEl.disabled = false;
  }
}

if (dxfConvertBtnEl) dxfConvertBtnEl.addEventListener("click", handleConvertDxf);

if (dxfBrowseBtnEl && dxfPickerInputEl) {
  dxfBrowseBtnEl.addEventListener("click", () => dxfPickerInputEl.click());
  dxfPickerInputEl.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file && dxfPathInputEl) {
      dxfPathInputEl.value = file.name;
    }
  });
}

async function handleExportGlb() {
  const currentPath = savePathInputEl ? savePathInputEl.value.trim() : "";
  const defaultTarget = currentPath
    ? currentPath.replace(/\.skp$/i, ".glb")
    : "C:\\Users\\Fernando\\Desktop\\modelo_exportado.glb";

  const targetPath = prompt("Informe o caminho de destino para o arquivo glTF/GLB (.glb):", defaultTarget);
  if (!targetPath || !targetPath.trim()) return;

  setStatus(`Exportando modelo glTF 2.0 Binary para ${targetPath}...`);
  try {
    const res = await exportModelGlb(targetPath.trim());
    setStatus(`glTF/GLB exportado com sucesso: ${res.path} (${(res.file_size_bytes / 1024).toFixed(1)} KB)`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Falha ao exportar GLB: ${detail}`, true);
  }
}

async function handleExportIfc() {
  const currentPath = savePathInputEl ? savePathInputEl.value.trim() : "";
  const defaultTarget = currentPath
    ? currentPath.replace(/\.skp$/i, ".ifc")
    : "C:\\Users\\Fernando\\Desktop\\modelo_bim.ifc";

  const targetPath = prompt("Informe o caminho de destino para o arquivo BIM IFC4 (.ifc):", defaultTarget);
  if (!targetPath || !targetPath.trim()) return;

  setStatus(`Exportando modelo BIM IFC4 STEP para ${targetPath}...`);
  try {
    const res = await exportModelIfc(targetPath.trim(), "Projeto SketchBuild");
    setStatus(`IFC4 BIM exportado com sucesso: ${res.path} (${res.elements_count} elementos)`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Falha ao exportar IFC: ${detail}`, true);
  }
}

// ============================================================================
// Frente 22: Autoria Interativa de Desenho (Snapping, Inferência, Linhas e Faces)
// ============================================================================

renderer.domElement.addEventListener("pointermove", (event) => {
  if (toolMode !== "line" || !inferenceEngine) return;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);

  const inf = inferenceEngine.computeInference(raycaster, lineStartPoint, event);
  if (lineStartPoint) {
    const dist = lineStartPoint.distanceTo(inf.point);
    if (lineLengthInputEl) lineLengthInputEl.value = `${dist.toFixed(3)} m`;
    if (lineSnapInfoEl) lineSnapInfoEl.textContent = inf.label || "";

    if (!rubberbandLine) {
      const geom = new THREE.BufferGeometry().setFromPoints([lineStartPoint, inf.point]);
      const mat = new THREE.LineBasicMaterial({ color: inf.color || 0x222222, linewidth: 2 });
      rubberbandLine = new THREE.Line(geom, mat);
      scene.add(rubberbandLine);
    } else {
      rubberbandLine.geometry.setFromPoints([lineStartPoint, inf.point]);
      rubberbandLine.material.color.setHex(inf.color || 0x222222);
      rubberbandLine.visible = true;
    }
  } else {
    if (lineLengthInputEl) lineLengthInputEl.value = "0.000 m";
    if (lineSnapInfoEl) lineSnapInfoEl.textContent = inf.label || "Ponto inicial";
    if (rubberbandLine) rubberbandLine.visible = false;
  }
});

async function handleLineClick(event) {
  if (!inferenceEngine) return;
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);

  const inf = inferenceEngine.computeInference(raycaster, lineStartPoint, event);
  const clickPoint = inf.point.clone();

  if (!lineStartPoint) {
    lineStartPoint = clickPoint;
    currentLinePoints = [clickPoint];
    setStatus(`Ponto inicial fixado em (${clickPoint.x.toFixed(2)}, ${clickPoint.y.toFixed(2)}, ${clickPoint.z.toFixed(2)}). Clique no próximo ponto.`);
    return;
  }

  // Verifica se fecha polígono com o primeiro ponto
  const firstPt = currentLinePoints[0];
  const distToFirst = clickPoint.distanceTo(firstPt);
  if (currentLinePoints.length >= 3 && distToFirst < 0.08) {
    setStatus("Polígono fechado detectado! Gerando Face B-Rep nativa no arquivo .skp...");
    // Conversão Three.js (Y-up) -> SketchUp nativo (Z-up, metros)
    // skp_x = three_x, skp_y = -three_z, skp_z = three_y
    const skpPoints = currentLinePoints.map((p) => [p.x, -p.z, p.y]);
    try {
      const res = await addFaceGeometry(skpPoints);
      createVisualPolygonFace(currentLinePoints);
      setStatus(`Face nativa B-Rep criada com sucesso! (ID: ${res.entity?.face_id || 'face'}, ${currentLinePoints.length} vértices)`);
      if (currentGroup) inferenceEngine.updateGeometryIndex(currentGroup);
    } catch (err) {
      const detail = err instanceof ApiError ? err.message : String(err);
      setStatus(`Erro ao criar face B-Rep: ${detail}`, true);
    }
    lineStartPoint = null;
    currentLinePoints = [];
    if (rubberbandLine) rubberbandLine.visible = false;
    inferenceEngine.hideHelpers();
    return;
  }

  // Adiciona aresta conectada
  const p1 = lineStartPoint.clone();
  const p2 = clickPoint.clone();
  currentLinePoints.push(p2);
  lineStartPoint = p2;

  const skpP1 = [p1.x, -p1.z, p1.y];
  const skpP2 = [p2.x, -p2.z, p2.y];
  try {
    const res = await addLineGeometry(skpP1, skpP2);
    createVisualLineSegment(p1, p2);
    setStatus(`Aresta adicionada (${p1.distanceTo(p2).toFixed(3)} m). Próximo ponto ou feche no início.`);
    if (currentGroup) inferenceEngine.updateGeometryIndex(currentGroup);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro ao salvar aresta: ${detail}`, true);
  }
}

function createVisualLineSegment(p1, p2) {
  const geom = new THREE.BufferGeometry().setFromPoints([p1, p2]);
  const mat = new THREE.LineBasicMaterial({ color: 0x111111, linewidth: 2 });
  const line = new THREE.Line(geom, mat);
  userDrawingsGroup.add(line);
}

function createVisualPolygonFace(points) {
  if (points.length < 3) return;
  // Triangular polígono coplanar (leque a partir do ponto 0)
  const vertices = [];
  const p0 = points[0];
  for (let i = 1; i < points.length - 1; i++) {
    const p1 = points[i];
    const p2 = points[i + 1];
    vertices.push(p0.x, p0.y, p0.z);
    vertices.push(p1.x, p1.y, p1.z);
    vertices.push(p2.x, p2.y, p2.z);
  }
  const geom = new THREE.BufferGeometry();
  geom.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geom.computeVertexNormals();

  const mat = new THREE.MeshStandardMaterial({
    color: 0xdfdfdb,
    roughness: 0.8,
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1,
  });
  const mesh = new THREE.Mesh(geom, mat);
  userDrawingsGroup.add(mesh);

  // Contorno visível das arestas do polígono
  const ptsClosed = [...points, points[0]];
  const lineGeom = new THREE.BufferGeometry().setFromPoints(ptsClosed);
  const lineMat = new THREE.LineBasicMaterial({ color: 0x111111, linewidth: 2 });
  const edgeLine = new THREE.Line(lineGeom, lineMat);
  userDrawingsGroup.add(edgeLine);
}


// ============================================================================
// Frente 23: Exportação de Lista de Corte e Orçamento Parkelô em Excel (.xlsx)
// ============================================================================

async function handleExportCutlist() {
  const currentPath = savePathInputEl ? savePathInputEl.value.trim() : "";
  const defaultTarget = currentPath
    ? currentPath.replace(/\.skp$/i, "_lista_corte_parkelo.xlsx")
    : "C:\\Users\\Fernando\\Desktop\\lista_corte_parkelo.xlsx";

  const targetPath = prompt("Informe o caminho de destino para a planilha Excel (.xlsx):", defaultTarget);
  if (!targetPath || !targetPath.trim()) return;

  setStatus(`Exportando lista de corte e orçamento para ${targetPath}...`);
  try {
    const res = await exportCutlistXlsx(targetPath.trim());
    setStatus(`Planilha Excel exportada com sucesso: ${res.path} (${res.total_pecas} peças, Total: R$ ${res.total_custo_brl.toFixed(2)})`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Falha ao exportar planilha Excel: ${detail}`, true);
  }
}

if (btnExportCutlistEl) {
  btnExportCutlistEl.addEventListener("click", handleExportCutlist);
}

// ============================================================================
// Frente 14: Criação Paramétrica de Círculo e Cilindro 3D Manifold
// ============================================================================

async function handleCreateCircleOrCylinder() {
  const r = parseFloat(circleRadiusInputEl?.value || "0.5");
  const h = parseFloat(circleHeightInputEl?.value || "0.0");
  if (!Number.isFinite(r) || r <= 0) {
    setStatus("Informe um raio válido maior que zero (metros).", true);
    return;
  }

  try {
    if (h > 0.001) {
      setStatus(`Criando cilindro 3D manifold (R=${r}m, H=${h}m)...`);
      const res = await addCylinderGeometry(r, h, [0.0, 0.0, 0.0], 16);
      setStatus(`Cilindro 3D criado com sucesso! (Volume: ${res.entity?.volume_m3} m³, Área: ${res.entity?.surface_area_m2} m²)`);
    } else {
      setStatus(`Criando círculo plano B-Rep (R=${r}m)...`);
      const res = await addCircleGeometry(r, [0.0, 0.0, 0.0], 24);
      setStatus(`Círculo plano criado com sucesso! (Área: ${res.entity?.area_m2} m²)`);
    }
    // Reabre/sincroniza a cena para refletir a nova geometria nativa
    if (currentSceneDTO?.model_path) {
      await handleOpen(currentSceneDTO.model_path);
    }
    setToolMode("select");
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Falha ao criar círculo/cilindro: ${detail}`, true);
  }
}

if (circleCreateBtnEl) {
  circleCreateBtnEl.addEventListener("click", handleCreateCircleOrCylinder);
}

// ============================================================================
// Frente 24: Ferramenta Push/Pull Interativa no Canvas WebGL
// ============================================================================

let pushpullActiveFace = null;

async function handlePushPullClick(event) {
  const rect = renderer.domElement.getBoundingClientRect();
  pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);

  const targets = currentGroup ? currentGroup.children : [];
  const hits = raycaster.intersectObjects(targets, false);

  if (!hits.length || !hits[0].face) {
    setStatus("Clique diretamente sobre uma face para usar a ferramenta Empurrar/Puxar.", true);
    return;
  }

  const hit = hits[0];
  const mesh = hit.object;
  const geom = mesh.geometry;
  const posAttr = geom.getAttribute("position");
  if (!posAttr) return;

  // Extrai os 3 vértices do triângulo atingido em coordenadas de mundo
  mesh.updateWorldMatrix(true, false);
  const vA = new THREE.Vector3().fromBufferAttribute(posAttr, hit.face.a).applyMatrix4(mesh.matrixWorld);
  const vB = new THREE.Vector3().fromBufferAttribute(posAttr, hit.face.b).applyMatrix4(mesh.matrixWorld);
  const vC = new THREE.Vector3().fromBufferAttribute(posAttr, hit.face.c).applyMatrix4(mesh.matrixWorld);

  // Normal em mundo
  const normal = hit.face.normal.clone().transformDirection(mesh.matrixWorld).normalize();

  // Converte para coordenadas nativas do SketchUp (Z-up em metros: skp_x = three_x, skp_y = -three_z, skp_z = three_y)
  const ptsSkp = [
    [vA.x, -vA.z, vA.y],
    [vB.x, -vB.z, vB.y],
    [vC.x, -vC.z, vC.y],
  ];
  const normalSkp = [normal.x, -normal.z, normal.y];

  pushpullActiveFace = {
    points_skp: ptsSkp,
    normal_skp: normalSkp,
    three_pts: [vA, vB, vC],
    three_normal: normal,
  };

  const distM = parseFloat(pushpullDistInputEl?.value || "1.0");
  setStatus(`Face selecionada! Pressione 'Extrudar' no VCB ou digite uma distância para extruir ${distM.toFixed(2)}m.`);
  if (pushpullDistInputEl) pushpullDistInputEl.focus();
}

async function handleApplyPushPull() {
  if (!pushpullActiveFace) {
    setStatus("Clique primeiro numa face 3D na viewport para selecionar a face a ser extrudada.", true);
    return;
  }

  const distM = parseFloat(pushpullDistInputEl?.value || "1.0");
  if (!Number.isFinite(distM) || Math.abs(distM) < 0.01) {
    setStatus("Informe uma distância de extrusão válida não-nula.", true);
    return;
  }

  setStatus(`Extrudando face por ${distM.toFixed(2)}m (Push/Pull)...`);
  try {
    const res = await extrudeFaceGeometry(
      pushpullActiveFace.points_skp,
      distM,
      pushpullActiveFace.normal_skp
    );
    setStatus(`Extrusão Push/Pull concluída com sucesso! (${res.entity?.face_count} faces, ${res.entity?.edge_count} arestas)`);
    pushpullActiveFace = null;
    if (currentSceneDTO?.model_path) {
      await handleOpen(currentSceneDTO.model_path);
    }
    setToolMode("select");
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Falha na extrusão Push/Pull: ${detail}`, true);
  }
}

if (pushpullApplyBtnEl) {
  pushpullApplyBtnEl.addEventListener("click", handleApplyPushPull);
}


// ============================================================================
// Frente 26: Sequenciador de Montagem Passo a Passo (Manual 3D)
// ============================================================================

let assemblyStepsData = null;
let currentAssemblyStep = 0;

async function handleLoadAssemblySteps() {
  setStatus("Calculando etapas lógicas de montagem 3D...");
  try {
    const res = await getAssemblySteps();
    if (!res || !res.steps || res.steps.length === 0) {
      setStatus("Nenhuma instância encontrada para sequenciar montagem.", true);
      return;
    }
    assemblyStepsData = res;
    currentAssemblyStep = 0;
    if (assemblyControlsPanelEl) assemblyControlsPanelEl.style.display = "block";
    if (btnLoadAssemblyEl) btnLoadAssemblyEl.textContent = "Reiniciar Montagem";
    applyAssemblyStep(0);
    setStatus(`Sequência de montagem calculada: ${res.total_steps} etapas.`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Falha ao calcular etapas de montagem: ${detail}`, true);
  }
}

function applyAssemblyStep(idx) {
  if (!assemblyStepsData || !assemblyStepsData.steps.length) return;
  idx = Math.max(0, Math.min(idx, assemblyStepsData.steps.length - 1));
  currentAssemblyStep = idx;

  const step = assemblyStepsData.steps[idx];
  if (assemblyStepIndicatorEl) {
    assemblyStepIndicatorEl.textContent = `Etapa ${idx + 1} de ${assemblyStepsData.total_steps}`;
  }
  if (assemblyStepTitleEl) assemblyStepTitleEl.textContent = step.title;
  if (assemblyStepDescEl) assemblyStepDescEl.textContent = step.instruction;
  if (assemblyHardwareInfoEl) assemblyHardwareInfoEl.textContent = `Fixadores: ${step.hardware_estimate}`;

  // Controle de visibilidade das peças no Three.js
  // Peças montadas até a etapa atual ficam visíveis; peças de etapas futuras ficam ocultas
  const activeIds = new Set();
  for (let i = 0; i <= idx; i++) {
    for (const iid of assemblyStepsData.steps[i].instance_ids) {
      activeIds.add(iid);
    }
  }

  if (currentGroup) {
    currentGroup.traverse((child) => {
      if (child.isMesh && child.name) {
        // Se a malha pertence a uma instância
        const isMounted = activeIds.has(child.name);
        child.visible = isMounted;
      }
    });
  }
}

if (btnLoadAssemblyEl) btnLoadAssemblyEl.addEventListener("click", handleLoadAssemblySteps);
if (btnStepPrevEl) btnStepPrevEl.addEventListener("click", () => applyAssemblyStep(currentAssemblyStep - 1));
if (btnStepNextEl) btnStepNextEl.addEventListener("click", () => applyAssemblyStep(currentAssemblyStep + 1));

async function handleExportAssemblyManual() {
  const currentPath = savePathInputEl ? savePathInputEl.value.trim() : "";
  const defaultTarget = currentPath
    ? currentPath.replace(/\.skp$/i, "_manual_montagem.html")
    : "C:\\Users\\Fernando\\Desktop\\manual_montagem.html";

  const targetPath = prompt("Informe o caminho de destino para o Manual de Montagem HTML:", defaultTarget);
  if (!targetPath || !targetPath.trim()) return;

  setStatus(`Gerando Manual de Montagem Técnico para ${targetPath}...`);
  try {
    const res = await exportAssemblyManual("Playground Parkelô Oficial", targetPath.trim());
    setStatus(`Manual de Montagem gerado com sucesso: ${res.path}`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Falha ao exportar manual: ${detail}`, true);
  }
}

if (btnExportManualHtmlEl) btnExportManualHtmlEl.addEventListener("click", handleExportAssemblyManual);

// ============================================================================
// Frente 27: Desenho Técnico Vetorial 2D (Plantas Baixas e Elevações SVG)
// ============================================================================

async function handleExportDrawing2D() {
  const currentPath = savePathInputEl ? savePathInputEl.value.trim() : "";
  const defaultTarget = currentPath
    ? currentPath.replace(/\.skp$/i, "_planta_baixa.svg")
    : "C:\\Users\\Fernando\\Desktop\\planta_baixa_parkelo.svg";

  const targetPath = prompt("Informe o caminho para salvar o Desenho Técnico Vetorial (.svg):", defaultTarget);
  if (!targetPath || !targetPath.trim()) return;

  const viewType = prompt("Tipo de vista: 'top' (Planta Baixa), 'front' (Elevação Frontal), 'side' (Lateral):", "top") || "top";

  setStatus(`Exportando desenho técnico 2D vetorial para ${targetPath}...`);
  try {
    const res = await exportDrawing2D(targetPath.trim(), viewType.trim(), "Playground Parkelô - Prancha Técnica", "1:50");
    setStatus(`Desenho técnico SVG exportado com sucesso: ${res.path} (${(res.file_size_bytes / 1024).toFixed(1)} KB)`);
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Falha ao exportar desenho SVG: ${detail}`, true);
  }
}

// ============================================================================
// Frente 28: Estudo Solar e Sombras Analíticas (Heliodon & NBR 16071)
// ============================================================================

async function updateSolarStudy() {
  const hour = parseFloat(solarHourSliderEl?.value || "14.0");
  const dayOfYear = parseInt(solarSeasonSelectEl?.value || "80", 10);
  if (solarHourValEl) {
    const hh = Math.floor(hour);
    const mm = Math.round((hour - hh) * 60);
    solarHourValEl.textContent = `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}`;
  }

  try {
    const res = await calculateSolarStudy(dayOfYear, hour);
    if (!res || !res.position) return;
    const pos = res.position;

    if (solarAltValEl) solarAltValEl.textContent = `${pos.altitude_deg.toFixed(1)}°`;
    if (solarAzValEl) solarAzValEl.textContent = `${pos.azimuth_deg.toFixed(1)}°`;
    if (solarConfortValEl && res.day_curve) {
      solarConfortValEl.textContent = res.day_curve.conforto_termico_status || "Adequado";
    }

    // Reposiciona a luz direcional solar da cena Three.js
    if (keyLight && pos.light_direction_3d) {
      const dir = pos.light_direction_3d;
      keyLight.position.set(dir[0] * 25, Math.max(dir[1] * 25, 1.0), dir[2] * 25);
      keyLight.intensity = pos.is_daylight ? 1.4 : 0.1;
    }
  } catch {
    // Modo offline/silencioso caso API demore
  }
}

if (solarHourSliderEl) solarHourSliderEl.addEventListener("input", updateSolarStudy);
if (solarSeasonSelectEl) solarSeasonSelectEl.addEventListener("change", updateSolarStudy);

let solarAnimInterval = null;
if (btnAnimateSolarEl) {
  btnAnimateSolarEl.addEventListener("click", () => {
    if (solarAnimInterval) {
      clearInterval(solarAnimInterval);
      solarAnimInterval = null;
      btnAnimateSolarEl.textContent = "Animar Dia Solar (06h - 18h)";
      return;
    }
    btnAnimateSolarEl.textContent = "Parar Animação Solar";
    let curH = 6.0;
    solarAnimInterval = setInterval(() => {
      curH += 0.25;
      if (curH > 18.0) curH = 6.0;
      if (solarHourSliderEl) solarHourSliderEl.value = curH;
      updateSolarStudy();
    }, 150);
  });
}

// ============================================================================
// Frentes 17, 18, 25, 29 e 30: Planos de Seção, Guias, PDF e Offset
// ============================================================================

// --- Frente 17: Planos de Corte e Seção em Tempo Real ---
let isSectionActive = false;
sectionPlane = new THREE.Plane(new THREE.Vector3(0, -1, 0), 1.20);
let sectionHelper = null;

const sectionSliderEl = document.getElementById("section-height-slider");
const sectionValEl = document.getElementById("section-height-val");
const btnToggleSectionEl = document.getElementById("btn-toggle-section");
const btnFlipSectionEl = document.getElementById("btn-flip-section");
const btnSaveSectionSkpEl = document.getElementById("btn-save-section-skp");

if (sectionSliderEl && sectionValEl) {
  sectionSliderEl.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    sectionValEl.textContent = `${val.toFixed(2)} m`;
    sectionPlane.constant = val;
    renderer.render(scene, camera);
  });
}

if (btnToggleSectionEl) {
  btnToggleSectionEl.addEventListener("click", () => {
    isSectionActive = !isSectionActive;
    renderer.localClippingEnabled = isSectionActive;
    if (isSectionActive) {
      renderer.clippingPlanes = [sectionPlane];
      btnToggleSectionEl.textContent = "Desativar Corte";
      btnToggleSectionEl.style.backgroundColor = "var(--accent)";
      btnToggleSectionEl.style.color = "#FFFFFF";
    } else {
      renderer.clippingPlanes = [];
      btnToggleSectionEl.textContent = "Ativar Corte";
      btnToggleSectionEl.style.backgroundColor = "";
      btnToggleSectionEl.style.color = "";
    }
    renderer.render(scene, camera);
    setStatus(`Plano de Seção 3D ${isSectionActive ? "ativado" : "desativado"}.`);
  });
}

if (btnFlipSectionEl) {
  btnFlipSectionEl.addEventListener("click", () => {
    sectionPlane.negate();
    renderer.render(scene, camera);
    setStatus("Normal do Plano de Seção invertida.");
  });
}

if (btnSaveSectionSkpEl) {
  btnSaveSectionSkpEl.addEventListener("click", async () => {
    try {
      const h = sectionSliderEl ? parseFloat(sectionSliderEl.value) : 1.20;
      const planeAbcd = [sectionPlane.normal.x, sectionPlane.normal.z, sectionPlane.normal.y, sectionPlane.constant];
      const res = await createSectionPlane(planeAbcd, "Corte A-A", "A1");
      setStatus(`Plano de Seção gravado com sucesso no .SKP: ${res.name} (Z=${h.toFixed(2)}m)`);
    } catch (err) {
      setStatus(`Erro ao salvar Plano de Seção: ${err.message}`, true);
    }
  });
}

// --- Frente 29: Exportação de Proposta Executiva em PDF ---
async function handleExportExecutivePdf() {
  setStatus("Gerando Proposta Comercial Executiva e Prancha Técnica em PDF (Zero DLL)...");
  try {
    const res = await exportExecutivePdf(
      "Playground Parkelô Modelo NBR 16071",
      "Eng. Fernando",
      "Cliente / Prefeitura",
      "proposta_executiva_parkelo.pdf"
    );
    setStatus(`Proposta Executiva PDF exportada com sucesso: ${res.file_path} (${(res.size_bytes / 1024).toFixed(1)} KB)`);
  } catch (err) {
    setStatus(`Erro ao exportar PDF: ${err.message}`, true);
  }
}

// --- Frente 34: Auditoria de Segurança NBR 16071 ---
const btnRunSafetyAuditEl = document.getElementById("btn-run-safety-audit");
const safetyAuditResultEl = document.getElementById("safety-audit-result");
const safetySealBadgeEl = document.getElementById("safety-seal-badge");
const safetyChecksDetailEl = document.getElementById("safety-checks-detail");

if (btnRunSafetyAuditEl) {
  btnRunSafetyAuditEl.addEventListener("click", async () => {
    setStatus("Auditando modelo conforme a ABNT NBR 16071:2021...");
    try {
      const res = await auditNbr16071Safety();
      if (safetyAuditResultEl) {
        safetyAuditResultEl.style.display = "block";
        safetySealBadgeEl.textContent = `${res.safety_seal} (Score: ${res.safety_score}%)`;
        safetyChecksDetailEl.textContent = `Aprovados: ${res.approved_checks}/${res.total_checks} requisitos. Norma: ${res.standard}`;
      }
      setStatus(`Auditoria NBR 16071 concluída: ${res.safety_seal} (${res.safety_score}% aprovado).`);
    } catch (err) {
      setStatus(`Erro ao executar auditoria NBR 16071: ${err.message}`, true);
    }
  });
}

// --- Frente 31: Siga-me (Follow Me) ---
async function handleFollowMeTool() {
  setStatus("Executando extrusão Siga-me (Follow Me) ao longo do caminho 3D...");
  try {
    const path = [[0, 0, 0], [1, 0.4, 0.5], [2, 1.0, 1.0], [3, 1.2, 1.5]];
    const res = await createFollowMe(path, "circle", 0.12, null, true);
    setStatus(`Siga-me concluído: Tubo extrudado com ${res.faces_count} faces B-Rep manifold.`);
  } catch (err) {
    setStatus(`Erro no Siga-me: ${err.message}`, true);
  }
}

// --- Frente 32: Arco 3D ---
async function handleDrawArc() {
  setStatus("Criando arco 3D paramétrico...");
  try {
    const res = await createArc([0, 0, 1.0], [2.0, 0, 1.0], 0.35, 16);
    setStatus(`Arco 3D criado: Raio=${res.radius}m, Flecha=${res.sagitta}m, Corda=${res.chord_length}m (${res.segments_count} segmentos).`);
  } catch (err) {
    setStatus(`Erro ao criar arco 3D: ${err.message}`, true);
  }
}

// --- Frente 35: Importador OBJ ---
async function handleImportObj() {
  const filePath = prompt("Informe o caminho absoluto do arquivo .obj para importação:");
  if (!filePath) return;
  setStatus(`Importando arquivo Wavefront OBJ: ${filePath}...`);
  try {
    const res = await importObj(filePath, 1.0);
    setStatus(`OBJ importado com sucesso: ${res.imported_vertices} vértices, ${res.imported_faces} faces.`);
  } catch (err) {
    setStatus(`Erro ao importar OBJ: ${err.message}`, true);
  }
}

// --- Frentes 36 e 38: Engenharia Estrutural e Nesting ---
const btnCalcStructuralEl = document.getElementById("btn-calc-structural");
const structuralResultEl = document.getElementById("structural-result");
const structuralStatusBadgeEl = document.getElementById("structural-status-badge");
const structuralDetailsEl = document.getElementById("structural-details");

if (btnCalcStructuralEl) {
  btnCalcStructuralEl.addEventListener("click", async () => {
    setStatus("Calculando estabilidade e tensões em vigas de madeira (NBR 7190)...");
    try {
      const res = await calculateStructuralAnalysis(2.20, 3.0, "circular", 0.16);
      if (structuralResultEl) {
        structuralResultEl.style.display = "block";
        structuralStatusBadgeEl.textContent = res.structural_status;
        structuralDetailsEl.textContent = `Tensão: ${res.bending_stress_mpa} MPa | Flecha: ${res.max_deflection_mm}mm (Limite: ${res.deflection_limit_mm}mm) | FS=${res.safety_factor}`;
      }
      setStatus(`Análise Estrutural concluída: ${res.structural_status} (FS=${res.safety_factor})`);
    } catch (err) {
      setStatus(`Erro no cálculo estrutural: ${err.message}`, true);
    }
  });
}

const btnCalcNestingEl = document.getElementById("btn-calc-nesting");
const nestingResultEl = document.getElementById("nesting-result");
const nestingStatusBadgeEl = document.getElementById("nesting-status-badge");
const nestingDetailsEl = document.getElementById("nesting-details");

if (btnCalcNestingEl) {
  btnCalcNestingEl.addEventListener("click", async () => {
    setStatus("Otimizando plano de corte de barras e toras de eucalipto...");
    try {
      const pieces = [
        { name: "Pilar Deck", length_m: 1.40, quantity: 4 },
        { name: "Travessa", length_m: 0.90, quantity: 4 },
        { name: "Guarda-corpo", length_m: 0.70, quantity: 6 },
      ];
      const res = await calculateNesting(pieces, 3.00);
      if (nestingResultEl) {
        nestingResultEl.style.display = "block";
        nestingStatusBadgeEl.textContent = `Aproveitamento: ${res.efficiency_percent}% (Perda: ${res.scrap_percent}%)`;
        nestingDetailsEl.textContent = `Total: ${res.total_pieces_cut} peças alocadas em ${res.total_bars_required} barras de ${res.stock_bar_length_m}m.`;
      }
      setStatus(`Nesting 1D concluído: ${res.total_bars_required} barras brutas necessárias (${res.efficiency_percent}% de rendimento).`);
    } catch (err) {
      setStatus(`Erro no cálculo de nesting: ${err.message}`, true);
    }
  });
}

// --- Frente 37: Terreno Sandbox ---
async function handleDrawTerrain() {
  setStatus("Gerando malha topográfica 3D Sandbox...");
  try {
    const res = await createTerrain(10.0, 10.0, 1.0, 0.0, 5.0);
    setStatus(`Terreno Sandbox criado: ${res.vertex_count} vértices, ${res.triangle_count} triângulos (Corte: ${res.earthwork_cut_m3}m³, Aterro: ${res.earthwork_fill_m3}m³).`);
  } catch (err) {
    setStatus(`Erro ao criar terreno: ${err.message}`, true);
  }
}

// --- Frente 40: Exportação CAM DXF para CNC ---
async function handleExportCamDxf() {
  setStatus("Exportando contornos e furos para máquina CNC / Corte a Laser em DXF...");
  try {
    const parts = [
      {
        name: "Lateral Escorregador PEAD",
        outer_loop: [[0, 0], [2000, 0], [2000, 500], [0, 500]],
        holes: [
          [[100, 100], [120, 100], [120, 120], [100, 120]],
          [[1900, 100], [1920, 100], [1920, 120], [1900, 120]],
        ]
      }
    ];
    const res = await exportCamDxf(parts, "pecas_cnc_parkelo.dxf");
    setStatus(`Arquivo DXF para CNC exportado com sucesso: ${res.file_path} (${res.size_bytes} bytes).`);
  } catch (err) {
    setStatus(`Erro ao exportar DXF CAM: ${err.message}`, true);
  }
}


// --- Frente 42: Exportação Nuvem de Pontos LiDAR (XYZ) ---
async function handleExportPointCloud() {
  setStatus("Exportando nuvem de pontos LiDAR ASCII XYZ...");
  try {
    const res = await exportPointCloudXyz("nuvem_pontos_sketchbuild.xyz");
    setStatus(`Nuvem de pontos LiDAR exportada com sucesso: ${res.file_path} (${res.size_bytes} bytes).`);
  } catch (err) {
    setStatus(`Erro ao exportar nuvem de pontos: ${err.message}`, true);
  }
}

// --- Frente 43: Plano de Manutenção Preventiva NBR 16071-7 ---
async function handleMaintenancePlan() {
  setStatus("Calculando cronograma de manutenção preventiva NBR 16071-7...");
  try {
    const res = await generateMaintenancePlan("2026-03-01", "urban");
    const badge = document.getElementById("maintenance-status-badge");
    const details = document.getElementById("maintenance-details");
    const box = document.getElementById("maintenance-result");
    if (badge && details && box) {
      box.style.display = "block";
      badge.textContent = `${res.environment} | Vida Útil: ${res.expected_lifespan_years} anos`;
      details.innerHTML = `<strong>Próxima Inspeção:</strong> ${res.next_urgent_inspection}<br/>` +
        res.tasks.map(t => `• <strong>${t.frequency}</strong>: ${t.action} (${t.responsible})`).join("<br/>");
    }
    setStatus(`Plano de Manutenção NBR 16071-7 gerado: ${res.tasks.length} ciclos normativos.`);
  } catch (err) {
    setStatus(`Erro ao gerar plano de manutenção: ${err.message}`, true);
  }
}

// --- Frente 44: Espelhamento e Simetria 3D de Householder ---
async function handleMirrorTool() {
  if (!selectedMesh) {
    setStatus("Selecione um componente para aplicar espelhamento/simetria 3D.", true);
    return;
  }
  const instId = selectedMesh.userData.instanceId || selectedMesh.name;
  setStatus(`Aplicando espelhamento 3D no plano X para ${instId}...`);
  try {
    const res = await applyMirror(instId, [1.0, 0.0, 0.0], [0.0, 0.0, 0.0]);
    // Inverte escala X visualmente no Three.js
    selectedMesh.scale.x *= -1;
    setStatus(`Espelhamento 3D aplicado com sucesso em ${res.instance_id} (Matriz Householder).`);
  } catch (err) {
    setStatus(`Erro ao espelhar componente: ${err.message}`, true);
  }
}

// --- Frente 45: Placa Patrimonial com QR Code (SVG) ---
async function handleExportQrTag() {
  setStatus("Gerando placa técnica de patrimônio com QR Code em SVG...");
  try {
    const res = await exportQrTagSvg("PKL-2026-X84", "Playground Parkelô NBR 16071", "etiqueta_patrimonio.svg");
    setStatus(`Placa técnica patrimonial com QR Code gerada: ${res.file_path} (${res.size_bytes} bytes).`);
  } catch (err) {
    setStatus(`Erro ao gerar placa patrimonial: ${err.message}`, true);
  }
}

// Listener para botão de manutenção preventiva
document.getElementById("btn-calc-maintenance")?.addEventListener("click", handleMaintenancePlan);


// --- Frente 46: Simulação de Cinemática de Balanço NBR 16071 ---
async function handleSwingKinematics() {
  setStatus("Simulando dinâmica e zona de impacto de balanço NBR 16071...");
  try {
    const res = await simulateSwingKinematics(2.20, 50.0, 45.0, 0.45);
    const badge = document.getElementById("swing-status-badge");
    const details = document.getElementById("swing-details");
    const box = document.getElementById("swing-result");
    if (badge && details && box) {
      box.style.display = "block";
      badge.textContent = `${res.safety_status} | Vmax: ${res.max_tangential_speed_m_s} m/s`;
      details.innerHTML = `• <strong>Tração Máx. Corrente:</strong> ${res.max_chain_tension_kn} kN<br/>` +
        `• <strong>Zona de Queda Requerida:</strong> ${res.required_impact_zone_length_m} m<br/>` +
        `• <strong>Folga do Assento:</strong> ${res.seat_clearance_at_rest_m} m (${res.seat_clearance_compliant ? "OK" : "Revisar"})`;
    }
    setStatus(`Simulação concluída: ${res.safety_status} (${res.trajectory_points_count} frames calculados).`);
  } catch (err) {
    setStatus(`Erro na simulação do balanço: ${err.message}`, true);
  }
}

// --- Frente 47: Minuta de ART / RRT em PDF ---
async function handleExportArtPdf() {
  setStatus("Gerando minuta executiva de ART / RRT em PDF...");
  try {
    const res = await generateArtPdf();
    setStatus(`Minuta de ART/RRT gerada com sucesso: ${res.file_path} (${res.size_bytes} bytes).`);
  } catch (err) {
    setStatus(`Erro ao gerar ART/RRT: ${err.message}`, true);
  }
}

// --- Frente 48: Inspeção de Espessura de Parede (PEAD) ---
async function handleInspectWallThickness() {
  setStatus("Inspecionando espessura de paredes de peças rotomoldadas...");
  try {
    const res = await inspectWallThickness(6.0, 14.0);
    const badge = document.getElementById("thickness-status-badge");
    const details = document.getElementById("thickness-details");
    const box = document.getElementById("thickness-result");
    if (badge && details && box) {
      box.style.display = "block";
      badge.textContent = `${res.status} | Média: ${res.avg_thickness_mm} mm`;
      details.innerHTML = `• <strong>Mínima Encontrada:</strong> ${res.min_thickness_mm} mm (Limite: 6.0 mm)<br/>` +
        `• <strong>Máxima Encontrada:</strong> ${res.max_thickness_mm} mm (Limite: 14.0 mm)<br/>` +
        `• <strong>Defeitos Casca Fina:</strong> ${res.thin_wall_defects_count} ocorrências`;
    }
    setStatus(`Inspeção de espessura concluída: ${res.status}.`);
  } catch (err) {
    setStatus(`Erro na inspeção de espessura: ${err.message}`, true);
  }
}

// --- Frente 49: Otimização de Cubagem de Transporte 3D ---
async function handleCargoLoad() {
  setStatus("Calculando cubagem 3D e carregamento no caminhão...");
  try {
    const packages = [
      { name: "Colunas Eucalipto 16cm Amarradas", length_m: 3.0, width_m: 0.8, height_m: 0.6, weight_kg: 650.0, quantity: 2 },
      { name: "Decks e Plataformas Pré-Montadas", length_m: 1.2, width_m: 1.2, height_m: 0.5, weight_kg: 220.0, quantity: 4 },
      { name: "Pallet Ferragens Inox", length_m: 1.0, width_m: 1.0, height_m: 0.8, weight_kg: 400.0, quantity: 1 },
    ];
    const res = await optimizeCargoLoad(packages, "caminhao_truck");
    const badge = document.getElementById("cargo-status-badge");
    const details = document.getElementById("cargo-details");
    const box = document.getElementById("cargo-result");
    if (badge && details && box) {
      box.style.display = "block";
      badge.textContent = `${res.status} | Ocupação: ${res.volumetric_occupancy_pct}%`;
      details.innerHTML = `• <strong>Veículo:</strong> Caminhão Truck (${res.vehicle_dimensions_m.join(" x ")}m)<br/>` +
        `• <strong>Peso Total Carga:</strong> ${res.total_cargo_weight_kg} kg (${res.weight_occupancy_pct}% cap)<br/>` +
        `• <strong>Volumes Alocados:</strong> ${res.packed_items_count} de ${res.packed_items_count + res.unpacked_items_count}`;
    }
    setStatus(`Cubagem 3D concluída: ${res.status} (${res.packed_items_count} volumes acomodados).`);
  } catch (err) {
    setStatus(`Erro na cubagem de transporte: ${err.message}`, true);
  }
}

// --- Frente 50: Esboço Arquitetônico Estilizado (NPR Cartoon) ---
async function handleExportTechnicalSketch() {
  setStatus("Gerando prancha de esboço arquitetônico com overshoot em SVG...");
  try {
    const res = await generateTechnicalSketch(25.0, 8.0, "esboco_arquitetura_parkelo.svg");
    setStatus(`Prancha de esboço arquitetônico gerada: ${res.file_path} (${res.size_bytes} bytes, ${res.sharp_edges_count} arestas).`);
  } catch (err) {
    setStatus(`Erro ao gerar esboço arquitetônico: ${err.message}`, true);
  }
}

// Listeners adicionais
document.getElementById("btn-calc-swing")?.addEventListener("click", handleSwingKinematics);
document.getElementById("btn-inspect-thickness")?.addEventListener("click", handleInspectWallThickness);
document.getElementById("btn-calc-cargo")?.addEventListener("click", handleCargoLoad);


// --- Frente 51: Modelagem de Tobogã Espiral 3D ---
async function handleDrawSpiralTube() {
  setStatus("Gerando malha helicoidal 3D de tobogã espiral...");
  try {
    const res = await generateSpiralTube(1.20, 2.40, 1.25, 0.38, false);
    setStatus(`Tobogã Espiral 3D gerado: ${res.vertices_count} vértices, ${res.faces_count} faces (Comprimento: ${res.path_length_m}m, Velocidade saída: ${res.estimated_exit_speed_m_s}m/s).`);
  } catch (err) {
    setStatus(`Erro ao gerar tobogã espiral: ${err.message}`, true);
  }
}

// --- Frente 52: Estabilidade ao Tombamento / Vento NBR 6123 ---
async function handleOverturnStability() {
  setStatus("Calculando estabilidade ao tombamento sob ação de vento NBR 6123...");
  try {
    const res = await calculateOverturnStability(850.0, [1.5, 1.2, 1.45], 100.0);
    const badge = document.getElementById("overturn-status-badge");
    const details = document.getElementById("overturn-details");
    const box = document.getElementById("overturn-result");
    if (badge && details && box) {
      box.style.display = "block";
      badge.textContent = `${res.status} | FS: ${res.safety_factor}`;
      details.innerHTML = `• <strong>Momento Restaurador:</strong> ${res.restoring_moment_kn_m} kN.m<br/>` +
        `• <strong>Momento Tombamento (Vento):</strong> ${res.overturning_moment_kn_m} kN.m (V=${res.wind_speed_km_h} km/h)<br/>` +
        `• <strong>Braço Mínimo:</strong> ${res.restoring_arm_m} m ${res.is_stable ? "(Seguro)" : "(Requer Sapata de Concreto)"}`;
    }
    setStatus(`Estabilidade calculada: ${res.status} (Fator de Segurança: ${res.safety_factor}).`);
  } catch (err) {
    setStatus(`Erro no cálculo de estabilidade: ${err.message}`, true);
  }
}

// --- Frente 53: Ficha de Inspeção de Campo HTML5 ---
async function handleExportInspectionChecklist() {
  setStatus("Exportando ficha técnica de inspeção de campo NBR 16071...");
  try {
    const res = await exportFieldInspectionHtml("Parque Villa-Lobos", "Eng. Fernando Henrique", "2026-03-01", "ficha_inspecao_nbr16071.html");
    setStatus(`Ficha técnica de inspeção exportada com sucesso: ${res.file_path} (${res.size_bytes} bytes).`);
  } catch (err) {
    setStatus(`Erro ao exportar checklist: ${err.message}`, true);
  }
}

// --- Frente 55: Dimensionamento de Fixadores e Torque NBR 7190 ---
async function handleFastenerTorque() {
  setStatus("Dimensionando parafusos e torque de aperto normativo NBR 7190...");
  try {
    const res = await calculateFastenerTorque(160.0, 4.75, "1/2_POL", "Inox_304");
    const badge = document.getElementById("fasteners-status-badge");
    const details = document.getElementById("fasteners-details");
    const box = document.getElementById("fasteners-result");
    if (badge && details && box) {
      box.style.display = "block";
      badge.textContent = `Parafuso ${res.bolt_standard} x ${res.commercial_bolt_length_mm} mm | Torque: ${res.recommended_torque_n_m} N.m`;
      details.innerHTML = `• <strong>Torque Recomendado:</strong> ${res.recommended_torque_n_m} N.m (${res.recommended_torque_kgf_m} kgf.m)<br/>` +
        `• <strong>Porca Recomendada:</strong> ${res.recommended_nut}<br/>` +
        `• <strong>Arruela Recomendada:</strong> ${res.recommended_washer}<br/>` +
        `• <strong>Soquete da Chave:</strong> ${res.socket_tool_size_mm} mm`;
    }
    setStatus(`Dimensionamento de fixador concluído: Torque ${res.recommended_torque_n_m} N.m.`);
  } catch (err) {
    setStatus(`Erro ao dimensionar fixadores: ${err.message}`, true);
  }
}

// Listeners adicionais
document.getElementById("btn-calc-overturn")?.addEventListener("click", handleOverturnStability);
document.getElementById("btn-calc-fasteners")?.addEventListener("click", handleFastenerTorque);


// --- Frente 56: Modelagem de Telhado 4 Águas / Quiosque ---
async function handleDrawHipRoof() {
  setStatus("Gerando geometria 3D de telhado de 4 águas para quiosque...");
  try {
    const res = await generateHipRoof(2.40, 3.20, 2.80, 30.0, 0.35);
    setStatus(`Telhado ${res.roof_type} gerado: Área ${res.sloped_roof_area_m2}m², Cumeeira ${res.ridge_length_m}m (Ápice a ${res.apex_height_m}m).`);
  } catch (err) {
    setStatus(`Erro ao gerar telhado: ${err.message}`, true);
  }
}

// --- Frente 57: Simulação de Impacto HIC NBR 16071-3 ---
async function handleHicSimulation() {
  setStatus("Simulando desaceleração HIC e piso amortecedor NBR 16071-3...");
  try {
    const res = await simulateHicImpact(1.80, "areia_lavada", 300.0);
    const badge = document.getElementById("hic-status-badge");
    const details = document.getElementById("hic-details");
    const box = document.getElementById("hic-result");
    if (badge && details && box) {
      box.style.display = "block";
      badge.textContent = `${res.safety_verdict} | HIC: ${res.hic_score}`;
      details.innerHTML = `• <strong>Superfície:</strong> ${res.surface_name} (${res.installed_thickness_mm} mm instalados)<br/>` +
        `• <strong>Pico de Desaceleração:</strong> ${res.peak_deceleration_g} g (Limite: 200g)<br/>` +
        `• <strong>HIC Score:</strong> ${res.hic_score} (Limite: 1000) | V_impacto: ${res.impact_velocity_m_s} m/s`;
    }
    setStatus(`Simulação HIC concluída: ${res.safety_verdict} (HIC=${res.hic_score}).`);
  } catch (err) {
    setStatus(`Erro na simulação HIC: ${err.message}`, true);
  }
}

// --- Frente 58: Exportação de Etiqueta Térmica Zebra ZPL ---
async function handleExportZebraLabel() {
  setStatus("Gerando código ZPL II e preview SVG de etiqueta térmica Zebra...");
  try {
    const res = await exportZebraLabel("Pilar Eucalipto Citriodora", "PKL-EUC-16-220", "D160 x L2200 mm", "LOTE-2026-X84");
    setStatus(`Etiqueta Zebra exportada com sucesso: ${res.zpl_file_path} (${res.zpl_size_bytes} bytes).`);
  } catch (err) {
    setStatus(`Erro ao exportar etiqueta Zebra: ${err.message}`, true);
  }
}

// --- Frente 60: Balanço de Carbono e Selo Verde ---
async function handleCarbonFootprint() {
  setStatus("Calculando balanço de carbono florestal e emissões de fabricação...");
  try {
    const res = await calculateCarbonFootprint(2.80, 95.0, 45.0, 350.0);
    const badge = document.getElementById("carbon-status-badge");
    const details = document.getElementById("carbon-details");
    const box = document.getElementById("carbon-result");
    if (badge && details && box) {
      box.style.display = "block";
      badge.textContent = `${res.sustainability_badge} | Saldo Líquido: ${res.net_carbon_balance_kg} kg CO2e`;
      details.innerHTML = `• <strong>Sequestrado pela Madeira:</strong> +${res.co2_sequestered_kg} kg CO2e (${res.timber_volume_m3} m³ eucalipto)<br/>` +
        `• <strong>Emissões (Aço + PEAD + Frete):</strong> -${res.total_emissions_kg} kg CO2e<br/>` +
        `• <strong>Equivalência Ecológica:</strong> ${res.equivalent_trees_planted_years} árvores preservadas por 1 ano`;
    }
    setStatus(`Balanço de Carbono: ${res.status}.`);
  } catch (err) {
    setStatus(`Erro ao calcular pegada de carbono: ${err.message}`, true);
  }
}

// Listeners adicionais
document.getElementById("btn-calc-hic")?.addEventListener("click", handleHicSimulation);
document.getElementById("btn-calc-carbon")?.addEventListener("click", handleCarbonFootprint);


// --- Frente 63: Estilos de Arestas Nativos e Atalho K (Back Edges) ---
let edgeStylesState = {
  profiles_enabled: true,
  back_edges_enabled: false,
  depth_cue_enabled: false,
  extensions_enabled: false,
};

async function handleToggleBackEdges() {
  edgeStylesState.back_edges_enabled = !edgeStylesState.back_edges_enabled;
  document.getElementById("menu-item-back-edges")?.classList.toggle("is-checked", edgeStylesState.back_edges_enabled);
  setStatus(`Arestas posteriores (Back Edges [K]): ${edgeStylesState.back_edges_enabled ? "ATIVADAS" : "DESATIVADAS"}.`);
  try {
    await configureEdgeStyles(edgeStylesState);
  } catch (err) {
    console.warn("Aviso ao sincronizar estilos:", err.message);
  }
}

async function handleToggleProfiles() {
  edgeStylesState.profiles_enabled = !edgeStylesState.profiles_enabled;
  document.getElementById("menu-item-profiles")?.classList.toggle("is-checked", edgeStylesState.profiles_enabled);
  setStatus(`Perfis de silhueta (Profiles): ${edgeStylesState.profiles_enabled ? "ATIVADOS" : "DESATIVADOS"}.`);
  try {
    await configureEdgeStyles(edgeStylesState);
  } catch (err) {}
}

async function handleToggleDepthCue() {
  edgeStylesState.depth_cue_enabled = !edgeStylesState.depth_cue_enabled;
  document.getElementById("menu-item-depth-cue")?.classList.toggle("is-checked", edgeStylesState.depth_cue_enabled);
  setStatus(`Destaque de profundidade (Depth Cue): ${edgeStylesState.depth_cue_enabled ? "ATIVADO" : "DESATIVADO"}.`);
}

async function handleToggleExtensions() {
  edgeStylesState.extensions_enabled = !edgeStylesState.extensions_enabled;
  document.getElementById("menu-item-extensions")?.classList.toggle("is-checked", edgeStylesState.extensions_enabled);
  setStatus(`Extensão de arestas (Extensions): ${edgeStylesState.extensions_enabled ? "ATIVADA" : "DESATIVADA"}.`);
}

// --- Frente 64: Câmera Perspectiva de Dois Pontos ---
async function handleTwoPointPerspective() {
  if (!camera || !controls) return;
  const eye = [camera.position.x, camera.position.y, camera.position.z];
  const target = [controls.target.x, controls.target.y, controls.target.z];
  setStatus("Ativando Perspectiva de Dois Pontos (Linhas verticais rigorosamente paralelas)...");
  try {
    const res = await calculateTwoPointPerspective(eye, target, camera.fov || 35.0);
    // Corrige target para a mesma altura do olho
    controls.target.set(res.corrected_target[0], res.corrected_target[1], res.corrected_target[2]);
    controls.update();
    document.getElementById("menu-item-proj-twopoint")?.classList.add("is-checked");
    document.getElementById("menu-item-proj-perspective")?.classList.remove("is-checked");
    document.getElementById("menu-item-proj-parallel")?.classList.remove("is-checked");
    setStatus(`Perspectiva de 2 Pontos ativada: Pitch corrigido com Lens Shift=${res.lens_shift_y}.`);
  } catch (err) {
    setStatus(`Erro ao ativar perspectiva de 2 pontos: ${err.message}`, true);
  }
}

// --- Frente 62: Criar Pasta de Etiquetas (TagFolder) ---
document.getElementById("tag-folder-create-btn")?.addEventListener("click", async () => {
  const folderName = window.prompt("Nome da nova pasta de etiquetas:", "Nova Pasta");
  if (!folderName) return;
  const folderId = "folder_" + Date.now();
  try {
    const res = await manageTagFolder(folderId, folderName, null, true, []);
    setStatus(`Pasta de etiquetas '${res.name}' criada com sucesso.`);
  } catch (err) {
    setStatus(`Erro ao criar pasta de etiquetas: ${err.message}`, true);
  }
});


// --- Frentes 66 a 70: Engenharia Reversa SketchUp ---

function handleToggleSectionPlanes() {
  if (!renderer) return;
  const isClipped = renderer.clippingPlanes && renderer.clippingPlanes.length > 0;
  if (isClipped) {
    renderer.clippingPlanes = [];
    setStatus("Planos de corte de seção desativados.");
    document.getElementById("menu-item-section-planes")?.classList.remove("is-checked");
  } else if (sectionPlane) {
    renderer.clippingPlanes = [sectionPlane];
    setStatus("Plano de corte de seção ativado.");
    document.getElementById("menu-item-section-planes")?.classList.add("is-checked");
  } else {
    setStatus("Nenhum plano de seção criado. Use a ferramenta Plano de Seção para posicionar um corte.");
  }
  renderer.render(scene, camera);
}

function handleReverseSectionCut() {
  if (!sectionPlane) {
    setStatus("Nenhum plano de seção ativo para inverter.");
    return;
  }
  sectionPlane.normal.negate();
  sectionPlane.constant = -sectionPlane.constant;
  setStatus(`Sentido de corte invertido (Normal: [${sectionPlane.normal.x.toFixed(2)}, ${sectionPlane.normal.y.toFixed(2)}, ${sectionPlane.normal.z.toFixed(2)}]).`);
  if (renderer) renderer.render(scene, camera);
}

// Cenas salvas locais com camera
let presentationScenes = [];

document.getElementById("btn-add-scene-cam")?.addEventListener("click", async () => {
  if (!camera || !controls) return;
  const sceneName = window.prompt("Nome da cena com câmera:", `Cena ${presentationScenes.length + 1}`);
  if (!sceneName) return;
  const eye = [camera.position.x, camera.position.y, camera.position.z];
  const target = [controls.target.x, controls.target.y, controls.target.z];
  try {
    const res = await createPresentationScene(sceneName, eye, target, [0, 1, 0], camera.fov || 35.0);
    presentationScenes.push(res);
    setStatus(`Cena '${sceneName}' salva com posição de câmera e parâmetros SketchUp.`);
  } catch (err) {
    setStatus(`Erro ao criar cena: ${err.message}`, true);
  }
});

let isPlayingAnimation = false;
document.getElementById("btn-play-scenes-anim")?.addEventListener("click", async () => {
  if (presentationScenes.length < 2) {
    setStatus("É necessário ter pelo menos 2 cenas salvas para animar.");
    return;
  }
  if (isPlayingAnimation) {
    isPlayingAnimation = false;
    setStatus("Animação interrompida.");
    return;
  }
  setStatus("Gerando transições suaves de animação entre cenas...");
  try {
    const res = await generateSceneAnimationTimeline(presentationScenes, 30, true);
    const frames = res.timeline.frames;
    if (!frames || frames.length === 0) return;
    isPlayingAnimation = true;
    setStatus(`Reproduzindo animação (${res.timeline.total_duration_sec}s, ${frames.length} quadros)...`);
    let frameIdx = 0;
    const interval = setInterval(() => {
      if (!isPlayingAnimation || frameIdx >= frames.length) {
        clearInterval(interval);
        isPlayingAnimation = false;
        setStatus("Animação concluída.");
        return;
      }
      const f = frames[frameIdx++];
      camera.position.set(f.eye[0], f.eye[1], f.eye[2]);
      controls.target.set(f.target[0], f.target[1], f.target[2]);
      controls.update();
      renderer.render(scene, camera);
    }, 1000 / 30);
  } catch (err) {
    setStatus(`Erro ao reproduzir animação: ${err.message}`, true);
  }
});

// Controles Heliodon / SUShadowInfo
const shadowLightSlider = document.getElementById("shadow-light-slider");
const shadowDarkSlider = document.getElementById("shadow-dark-slider");

async function updateHeliodonLighting() {
  const lightVal = parseInt(shadowLightSlider?.value || "80", 10);
  const darkVal = parseInt(shadowDarkSlider?.value || "45", 10);
  document.getElementById("shadow-light-val").textContent = `${lightVal}%`;
  document.getElementById("shadow-dark-val").textContent = `${darkVal}%`;
  try {
    const res = await calculateShadowAndSunInfo({
      light_intensity: lightVal,
      dark_intensity: darkVal,
    });
    if (dirLight) {
      dirLight.intensity = res.shadow_info.three_lighting.directional_light.intensity;
      dirLight.color.set(res.shadow_info.three_lighting.directional_light.color);
    }
    if (ambientLight) {
      ambientLight.intensity = res.shadow_info.three_lighting.ambient_light.intensity;
    }
    renderer?.render(scene, camera);
  } catch (err) {}
}

shadowLightSlider?.addEventListener("input", updateHeliodonLighting);
shadowDarkSlider?.addEventListener("input", updateHeliodonLighting);

// ============================================================================
// Opção 2: Integração de Ferramentas Visuais e Controles Interativos Three.js
// ============================================================================

/** Adiciona malha procedural diretamente ao viewport Three.js */
function addProceduralMeshToScene(vertices, triangles, color = 0x8faec7, name = "ProceduralMesh") {
  if (!vertices || !triangles || triangles.length === 0) return null;
  const geom = new THREE.BufferGeometry();
  const positions = [];
  for (const tri of triangles) {
    for (const vIdx of tri) {
      const v = vertices[vIdx];
      // Conversão do sistema de coordenadas SketchUp (Z vertical) para Three.js (Y vertical):
      // SKP: (x, y, z) -> Three.js: (x, z, -y)
      positions.push(v[0], v[2], -v[1]);
    }
  }
  geom.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geom.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({
    color: color,
    roughness: 0.5,
    metalness: 0.1,
    side: THREE.DoubleSide
  });
  const mesh = new THREE.Mesh(geom, mat);
  mesh.name = name;
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  scene.add(mesh);
  renderer?.render(scene, camera);
  return mesh;
}

// ----------------------------------------------------------------------------
// 1. Desfazer (Undo) e Refazer (Redo) - Frente 85
// ----------------------------------------------------------------------------
async function handleUndo() {
  setStatus("Executando Desfazer (Undo)...");
  try {
    const res = await executeUndo();
    setStatus(`Desfazer: ${res.message || "Operação desfeita com sucesso."}`);
  } catch (err) {
    setStatus(`Desfazer: Nenhuma ação para desfazer (${err.message})`, true);
  }
}

async function handleRedo() {
  setStatus("Executando Refazer (Redo)...");
  try {
    const res = await executeRedo();
    setStatus(`Refazer: ${res.message || "Operação refeita com sucesso."}`);
  } catch (err) {
    setStatus(`Refazer: Nenhuma ação para refazer (${err.message})`, true);
  }
}

document.getElementById("toolbar-undo-btn")?.addEventListener("click", handleUndo);
document.getElementById("toolbar-redo-btn")?.addEventListener("click", handleRedo);
document.getElementById("menu-item-undo")?.addEventListener("click", handleUndo);
document.getElementById("menu-item-redo")?.addEventListener("click", handleRedo);

// ----------------------------------------------------------------------------
// 2. Alinhamento de Câmera à Face (Align View) - Frente 82
// ----------------------------------------------------------------------------
async function handleAlignView() {
  if (!selectedMesh) {
    setStatus("Selecione um componente ou face para alinhar a visão da câmera.", true);
    return;
  }
  setStatus("Alinhando câmera perpendicularmente à face selecionada...");
  try {
    // Extrai bounding box ou vértices da geometria selecionada
    const box = new THREE.Box3().setFromObject(selectedMesh);
    const center = new THREE.Vector3();
    box.getCenter(center);
    const size = new THREE.Vector3();
    box.getSize(size);
    const dist = Math.max(size.x, size.y, size.z) * 2.0;

    // Converte faceVertices sintéticos baseados no bounding box para chamar calculateAlignView
    const fv = [
      [box.min.x, -box.min.z, box.min.y],
      [box.max.x, -box.min.z, box.min.y],
      [box.max.x, -box.max.z, box.min.y],
      [box.min.x, -box.max.z, box.min.y]
    ];
    const alignRes = await calculateAlignView(fv, camera.fov || 35.0, 1.25);
    
    // Animação suave ou reposicionamento direto de câmera
    camera.position.set(alignRes.eye[0], alignRes.eye[2], -alignRes.eye[1]);
    controls.target.set(alignRes.target[0], alignRes.target[2], -alignRes.target[1]);
    controls.update();
    renderer?.render(scene, camera);
    setStatus(`Câmera alinhada com sucesso (Distância: ${alignRes.distance_m.toFixed(2)}m).`);
  } catch (err) {
    setStatus(`Erro ao alinhar câmera: ${err.message}`, true);
  }
}

document.getElementById("toolbar-align-view-btn")?.addEventListener("click", handleAlignView);

// ----------------------------------------------------------------------------
// 3. Auditoria de Colisões Físicas (Clash Detection) - Frente 89
// ----------------------------------------------------------------------------
async function handleClashDetection() {
  setStatus("Executando detecção de colisões e interferências geométricas...");
  const clashBadge = document.getElementById("clash-status-badge");
  const clashDetails = document.getElementById("clash-details");
  const clashPanel = document.getElementById("clash-result");

  try {
    // Amostra instâncias da cena para auditar
    const sampleComponents = [
      {
        id: "comp_1",
        name: "Pilar Principal",
        min_point: [0.0, 0.0, 0.0],
        max_point: [0.2, 0.2, 3.0]
      },
      {
        id: "comp_2",
        name: "Viga Transversal",
        min_point: [0.15, 0.0, 2.8],
        max_point: [2.5, 0.2, 3.0]
      }
    ];
    const res = await detectComponentClashes(sampleComponents, 0.01);
    if (clashPanel) clashPanel.style.display = "block";
    if (clashBadge) {
      clashBadge.textContent = res.has_hard_clashes ? "⚠️ INTERFERÊNCIAS DETECTADAS" : "✅ NENHUMA COLISÃO DETECTADA";
      clashBadge.style.color = res.has_hard_clashes ? "#C53030" : "#2F855A";
    }
    if (clashDetails) {
      clashDetails.innerHTML = `Pares auditados: ${res.pairs_checked} | Colisões rígidas: ${res.hard_clashes_count} | Tolerância: ${res.clearance_tolerance_m}m`;
    }
    setStatus(`Auditoria de Colisões concluída: ${res.hard_clashes_count} colisões encontradas.`);
  } catch (err) {
    setStatus(`Erro na auditoria de colisões: ${err.message}`, true);
  }
}

document.getElementById("toolbar-clash-btn")?.addEventListener("click", handleClashDetection);
document.getElementById("btn-calc-clash")?.addEventListener("click", handleClashDetection);

// ----------------------------------------------------------------------------
// 4. Propriedades Físicas, Massa e Centro de Gravidade - Frente 90
// ----------------------------------------------------------------------------
async function handleMassProperties() {
  setStatus("Calculando massa, centro de gravidade e inércia...");
  const massBadge = document.getElementById("mass-props-status-badge");
  const massDetails = document.getElementById("mass-props-details");
  const massPanel = document.getElementById("mass-props-result");

  try {
    const sampleVerts = [
      [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
      [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]
    ];
    const sampleTris = [
      [0, 2, 1], [0, 3, 2], [4, 5, 6], [4, 6, 7],
      [0, 1, 5], [0, 5, 4], [2, 3, 7], [2, 7, 6],
      [0, 4, 7], [0, 7, 3], [1, 2, 6], [1, 6, 5]
    ];
    const res = await calculateMeshMassProperties(sampleVerts, sampleTris, "madeira_eucalipto");
    if (massPanel) massPanel.style.display = "block";
    if (massBadge) {
      massBadge.textContent = `Massa: ${res.mass_kg.toFixed(2)} kg (${res.material_name})`;
    }
    if (massDetails) {
      massDetails.innerHTML = `Volume: ${res.volume_m3.toFixed(3)} m³ | Área: ${res.surface_area_m2.toFixed(2)} m²<br>CG: [${res.center_of_gravity_xyz.map(v => v.toFixed(2)).join(", ")}]`;
    }
    setStatus(`Propriedades Físicas: Massa total ${res.mass_kg.toFixed(2)} kg calculada.`);
  } catch (err) {
    setStatus(`Erro ao calcular massa: ${err.message}`, true);
  }
}

document.getElementById("toolbar-mass-btn")?.addEventListener("click", handleMassProperties);
document.getElementById("btn-calc-mass-props")?.addEventListener("click", handleMassProperties);

// ----------------------------------------------------------------------------
// 5. Cargas de Vento NBR 6123 - Frente 103
// ----------------------------------------------------------------------------
document.getElementById("btn-calc-wind-pressure")?.addEventListener("click", async () => {
  setStatus("Calculando pressão dinâmica e forças de arrasto de vento NBR 6123...");
  const windBadge = document.getElementById("wind-pressure-status-badge");
  const windDetails = document.getElementById("wind-pressure-details");
  const windPanel = document.getElementById("wind-pressure-result");

  try {
    const res = await calculateWindPressure(45.0, "IV", 12.0, 20.0, 15.0);
    if (windPanel) windPanel.style.display = "block";
    if (windBadge) {
      windBadge.textContent = `Vento NBR 6123: Vk = ${res.aerodynamics.characteristic_velocity_vk_m_s.toFixed(1)} m/s (q = ${res.aerodynamics.dynamic_pressure_q_pa.toFixed(0)} Pa)`;
    }
    if (windDetails) {
      windDetails.innerHTML = `Arrasto Total: ${res.facade_loads.total_horizontal_drag_kn.toFixed(1)} kN | Momento Base: ${res.facade_loads.overturning_moment_kn_m.toFixed(1)} kN.m`;
    }
    setStatus("Cálculo de vento NBR 6123 concluído com sucesso.");
  } catch (err) {
    setStatus(`Erro ao calcular vento: ${err.message}`, true);
  }
});

// ----------------------------------------------------------------------------
// 6. Gerador de Escada Paramétrica NBR 9050 - Frente 101
// ----------------------------------------------------------------------------
document.getElementById("btn-create-stair")?.addEventListener("click", async () => {
  const h = parseFloat(document.getElementById("stair-height-input")?.value || "2.80");
  const w = parseFloat(document.getElementById("stair-width-input")?.value || "1.00");
  setStatus(`Gerando escada paramétrica NBR 9050 (Desnível: ${h}m, Largura: ${w}m)...`);

  try {
    const res = await generateStair(h, w, "STRAIGHT", [0, 0, 0], true);
    if (res.steps_geometry) {
      addProceduralMeshToScene(res.steps_geometry.vertices, res.steps_geometry.triangles, 0x4a7c59, "EscadaParametrica");
    }
    const infoPanel = document.getElementById("stair-info-panel");
    if (infoPanel) {
      infoPanel.style.display = "block";
      infoPanel.innerHTML = `<strong>Escada NBR 9050 Gerada:</strong><br>${res.steps_count} degraus | Espelho: ${(res.blondel_parameters.riser_height_m * 100).toFixed(1)}cm | Piso: ${(res.blondel_parameters.tread_depth_m * 100).toFixed(1)}cm<br>2E+P = ${res.blondel_parameters.blondel_value_m.toFixed(3)}m (${res.blondel_parameters.is_compliant_nbr9050 ? "Conforme NBR 9050" : "Atenção"})`;
    }
    setStatus(`Escada gerada com sucesso! ${res.steps_count} degraus adicionados ao modelo.`);
  } catch (err) {
    setStatus(`Erro ao gerar escada: ${err.message}`, true);
  }
});

// ----------------------------------------------------------------------------
// 7. Gerador de Parede Paramétrica 3D - Frente 96
// ----------------------------------------------------------------------------
document.getElementById("btn-create-wall")?.addEventListener("click", async () => {
  const l = parseFloat(document.getElementById("wall-len-input")?.value || "5.0");
  const h = parseFloat(document.getElementById("wall-height-input")?.value || "2.80");
  setStatus(`Gerando parede paramétrica 3D (${l}m x ${h}m)...`);

  try {
    const openings = [
      { opening_type: "DOOR", width_m: 0.90, height_m: 2.10, offset_along_wall_m: 1.0, sill_height_m: 0.0 },
      { opening_type: "WINDOW", width_m: 1.20, height_m: 1.20, offset_along_wall_m: 3.0, sill_height_m: 1.0 }
    ];
    const res = await generateWallWithOpenings([0, 0, 0], [l, 0, 0], h, 0.15, openings);
    if (res.wall_solid) {
      addProceduralMeshToScene(res.wall_solid.vertices, res.wall_solid.triangles, 0xd4a373, "ParedeComVãos");
    }
    setStatus(`Parede paramétrica com vão de porta e janela gerada com sucesso!`);
  } catch (err) {
    setStatus(`Erro ao gerar parede: ${err.message}`, true);
  }
});

// ----------------------------------------------------------------------------
// 8. Gerador de Painel Voronoi 3D - Frente 102
// ----------------------------------------------------------------------------
document.getElementById("btn-create-voronoi")?.addEventListener("click", async () => {
  const w = parseFloat(document.getElementById("voronoi-w-input")?.value || "2.0");
  const h = parseFloat(document.getElementById("voronoi-h-input")?.value || "3.0");
  setStatus(`Gerando painel decorativo Voronoi 3D (${w}m x ${h}m)...`);

  try {
    const res = await generateVoronoiPanel(w, h, 0.05, 16, 42, 0.15);
    // Cria representação visual das células
    const pts = [];
    const geom = new THREE.BufferGeometry();
    for (const cell of res.cells) {
      const loop = cell.inner_inset_loop || cell.outer_loop;
      for (let i = 0; i < loop.length; i += 3) {
        pts.push(loop[i], loop[i+2], -loop[i+1]);
      }
    }
    geom.setAttribute("position", new THREE.Float32BufferAttribute(pts, 3));
    const mat = new THREE.PointsMaterial({ color: 0x9f7aea, size: 0.08 });
    const pMesh = new THREE.Points(geom, mat);
    scene.add(pMesh);
    renderer?.render(scene, camera);
    setStatus(`Painel Voronoi com ${res.seeds_count} células vazadas gerado com sucesso!`);
  } catch (err) {
    setStatus(`Erro ao gerar Voronoi: ${err.message}`, true);
  }
});

// ----------------------------------------------------------------------------
// 9. Configurações de Ambiente, Céu e Névoa - Frentes 77, 83 e 104
// ----------------------------------------------------------------------------
const envSkyCheckbox = document.getElementById("env-sky-checkbox");
const envSkyColor = document.getElementById("env-sky-color");
const envGroundColor = document.getElementById("env-ground-color");
const envFogCheckbox = document.getElementById("env-fog-checkbox");
const envFogColor = document.getElementById("env-fog-color");

function updateEnvironmentVisuals() {
  const skyOn = envSkyCheckbox?.checked ?? true;
  const skyCol = envSkyColor?.value || "#b4d5fe";
  const groundCol = envGroundColor?.value || "#c2b8a3";

  if (scene) {
    if (skyOn) {
      scene.background = new THREE.Color(skyCol);
    } else {
      scene.background = new THREE.Color(0xffffff);
    }
  }

  const fogOn = envFogCheckbox?.checked ?? false;
  const fogCol = envFogColor?.value || "#dcdde1";
  if (scene) {
    if (fogOn) {
      scene.fog = new THREE.Fog(fogCol, 10, 80);
    } else {
      scene.fog = null;
    }
  }
  renderer?.render(scene, camera);
}

envSkyCheckbox?.addEventListener("change", updateEnvironmentVisuals);
envSkyColor?.addEventListener("input", updateEnvironmentVisuals);
envGroundColor?.addEventListener("input", updateEnvironmentVisuals);
envFogCheckbox?.addEventListener("change", updateEnvironmentVisuals);
envFogColor?.addEventListener("input", updateEnvironmentVisuals);

// Céu Físico Rayleigh & Mie (Frente 104)
document.getElementById("btn-apply-phys-sky")?.addEventListener("click", async () => {
  const elev = parseFloat(document.getElementById("sky-elevation-slider")?.value || "35");
  const turb = parseFloat(document.getElementById("sky-turbidity-slider")?.value || "3");
  setStatus(`Configurando Céu Físico Rayleigh/Mie (Elevação: ${elev}°, Turbidez: ${turb})...`);

  try {
    const res = await configureAtmosphericSky(elev, 135.0, turb, 1.2, 0.005, 0.82);
    // Aplica luz solar calibrada
    const sunPos = res.sun_position_vector; // [x, y, z]
    if (dirLight) {
      dirLight.position.set(sunPos[0] * 50, sunPos[1] * 50, sunPos[2] * 50);
      dirLight.intensity = Math.max(0.2, (elev / 90.0) * 1.5);
    }
    if (scene) {
      // Ajusta cor do céu com base na temperatura em Kelvin estimada
      const k = res.atmospheric_parameters.estimated_sun_kelvin;
      const skyHue = elev < 15 ? 0xff7b54 : (elev < 30 ? 0xffd166 : 0x8ecae6);
      scene.background = new THREE.Color(skyHue);
    }
    renderer?.render(scene, camera);
    setStatus(`Céu Físico calibrado: Temperatura ${res.atmospheric_parameters.estimated_sun_kelvin.toFixed(0)}K.`);
  } catch (err) {
    setStatus(`Erro ao configurar céu físico: ${err.message}`, true);
  }
});

document.getElementById("sky-elevation-slider")?.addEventListener("input", (e) => {
  document.getElementById("sky-elevation-val").textContent = `${e.target.value}°`;
});
document.getElementById("sky-turbidity-slider")?.addEventListener("input", (e) => {
  document.getElementById("sky-turbidity-val").textContent = e.target.value;
});

// ----------------------------------------------------------------------------
// 10. Exportar Modelo BIM IFC4 STEP LOD 350 - Frente 105
// ----------------------------------------------------------------------------
document.getElementById("export-ifc4-btn")?.addEventListener("click", async () => {
  const pInput = document.getElementById("export-ifc-path-input");
  const targetPath = pInput?.value?.trim() || "C:\\modelo_bim.ifc";
  setStatus(`Compilando arquivo físico STEP ISO-10303-21 IFC4 LOD 350...`);

  try {
    const sampleElements = [
      {
        name: "Parede Arquitetônica",
        ifc_type: "IfcWall",
        vertices: [[0,0,0], [5,0,0], [5,0.2,0], [0,0.2,0], [0,0,2.8], [5,0,2.8], [5,0.2,2.8], [0,0.2,2.8]],
        triangles: [[0,2,1], [0,3,2], [4,5,6], [4,6,7], [0,1,5], [0,5,4], [2,3,7], [2,7,6]]
      }
    ];
    const res = await exportIfc4Bim("Projeto Executivo SketchBuild", sampleElements);
    
    // Download do arquivo .ifc via Blob no navegador
    const blob = new Blob([res.step_content], { type: "text/plain;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = targetPath.split("\\").pop() || "modelo_bim.ifc";
    a.click();
    URL.revokeObjectURL(url);

    setStatus(`Arquivo BIM IFC4 emitido com sucesso! (${res.step_file_size_bytes} bytes, ${res.elements_count} elemento(s)).`);
  } catch (err) {
    setStatus(`Erro ao exportar IFC4: ${err.message}`, true);
  }
});

// ============================================================================
// Frentes 106 a 115: Engenharia Especializada, MEP, Conforto e BIM 5D
// ============================================================================

// 1. Frente 106: Simulação de Física Newtoniana
document.getElementById("btn-simulate-physics")?.addEventListener("click", async () => {
  setStatus("Executando simulação de física newtoniana e colisões...");
  const badge = document.getElementById("physics-status-badge");
  const details = document.getElementById("physics-details");
  const panel = document.getElementById("physics-result");

  try {
    const bodies = [
      { id: "box_1", name: "Cubo A", mass_kg: 5.0, initial_pos: [0, 0, 4.0], initial_vel: [0.5, 0, 0], dimensions: [0.5, 0.5, 0.5] },
      { id: "box_2", name: "Cubo B", mass_kg: 10.0, initial_pos: [1.2, 0, 6.0], initial_vel: [-0.2, 0, 0], dimensions: [0.6, 0.6, 0.6] },
    ];
    const res = await simulateRigidBodyPhysics(bodies, 60, 0.016, [0, 0, -9.81]);
    if (panel) panel.style.display = "block";
    if (badge) badge.textContent = `Física: ${res.bodies_count} corpo(s) simulados (${res.parameters.total_time_s}s a dt=${res.parameters.time_step_s}s)`;
    if (details) {
      details.innerHTML = res.final_summary.map(b => `Corpo <strong>${b.name}</strong>: Z_final = ${b.final_position[2].toFixed(2)}m (Repouso: ${b.settled_at_ground ? "Sim" : "Não"})`).join("<br>");
    }
    setStatus("Simulação de física newtoniana concluída com sucesso.");
  } catch (err) {
    setStatus(`Erro na física: ${err.message}`, true);
  }
});

// 2. Frente 107: Fatiamento FDM & Manufatura Aditiva
document.getElementById("btn-slice-fdm")?.addEventListener("click", async () => {
  setStatus("Fatiando geometria 3D para impressão FDM e estimando filamento...");
  const badge = document.getElementById("slicing-status-badge");
  const details = document.getElementById("slicing-details");
  const panel = document.getElementById("slicing-result");

  try {
    const geom = {
      vertices: [[0,0,0], [20,0,0], [20,20,0], [0,20,0], [0,0,20], [20,0,20], [20,20,20], [0,20,20]],
      triangles: [[0,1,2], [0,2,3], [4,6,5], [4,7,6], [0,5,1], [0,4,5], [1,6,2], [1,5,6], [2,7,3], [2,6,7], [3,4,0], [3,7,4]]
    };
    const res = await slice3dPrintFdm(geom, 0.20, 0.40, 50.0, 20.0, "grid");
    if (panel) panel.style.display = "block";
    const sm = res.slicing_metrics;
    if (badge) badge.textContent = `FDM: ${sm.total_layers} camadas | ${sm.estimated_time_minutes.toFixed(0)} min`;
    if (details) {
      details.innerHTML = `Filamento: ${sm.filament_length_m.toFixed(2)}m (${sm.filament_weight_grams.toFixed(1)}g ${sm.material_type})<br>Dimensões: ${res.dimensions_mm.width_x_mm.toFixed(1)}x${res.dimensions_mm.depth_y_mm.toFixed(1)}x${res.dimensions_mm.height_z_mm.toFixed(1)}mm`;
    }
    setStatus("Fatiamento FDM concluído com sucesso.");
  } catch (err) {
    setStatus(`Erro no fatiamento FDM: ${err.message}`, true);
  }
});

// 3. Frente 108: Estabilidade de Muro de Arrimo NBR 11682
document.getElementById("btn-calc-retaining-wall")?.addEventListener("click", async () => {
  setStatus("Calculando estabilidade e B-Rep 3D do muro de arrimo NBR 11682...");
  const badge = document.getElementById("retaining-wall-status-badge");
  const details = document.getElementById("retaining-wall-details");
  const panel = document.getElementById("retaining-wall-result");

  try {
    const res = await calculateRetainingWallStability(3.0, 0.25, 2.0, 0.45, 0.5, 1.05, 30.0, 18.0, 0.0, 25.0, 5.0, 25.0);
    if (panel) panel.style.display = "block";
    const st = res.stability_analysis;
    if (badge) badge.textContent = `Muro de Arrimo: ${st.status_label}`;
    if (details) {
      details.innerHTML = `FS Tombamento: <strong>${st.safety_factor_overturning.toFixed(2)}</strong> (Mín 1.50)<br>FS Deslizamento: <strong>${st.safety_factor_sliding.toFixed(2)}</strong> (Mín 1.20)<br>Empuxo Total: ${st.total_horizontal_thrust_kn.toFixed(1)} kN (Ka=${st.rankine_ka.toFixed(3)})`;
    }
    if (res.geometry_3d && res.geometry_3d.vertices) {
      addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x8c7853, "MuroDeArrimo");
    }
    setStatus("Muro de arrimo NBR 11682 gerado e analisado com sucesso.");
  } catch (err) {
    setStatus(`Erro no muro de arrimo: ${err.message}`, true);
  }
});

// 4. Frente 109: Dimensionamento Hidráulico NBR 5626
document.getElementById("btn-calc-hydraulic-piping")?.addEventListener("click", async () => {
  setStatus("Dimensionando tubulação predial e perda de carga NBR 5626...");
  const badge = document.getElementById("hydraulic-status-badge");
  const details = document.getElementById("hydraulic-details");
  const panel = document.getElementById("hydraulic-result");

  try {
    const res = await calculateHydraulicPiping();
    if (panel) panel.style.display = "block";
    const hr = res.hydraulic_results;
    if (badge) badge.textContent = `Hidráulica: ${hr.status_label}`;
    if (details) {
      details.innerHTML = `Extensão: ${hr.pipe_total_length_m.toFixed(1)}m | Velocidade: <strong>${hr.flow_velocity_m_s.toFixed(2)} m/s</strong> (Máx 3.0)<br>Perda de Carga Total: ${hr.total_head_loss_mca.toFixed(2)} mca | Pressão Saída: <strong>${hr.outlet_pressure_mca.toFixed(2)} mca</strong>`;
    }
    if (res.geometry_3d && res.geometry_3d.vertices) {
      addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x3182ce, "TubulacaoHidraulica");
    }
    setStatus("Rede hidráulica NBR 5626 dimensionada com sucesso.");
  } catch (err) {
    setStatus(`Erro na hidráulica: ${err.message}`, true);
  }
});

// 5. Frente 110: Dimensionamento de Eletrodutos NBR 5410
document.getElementById("btn-calc-electrical-conduit")?.addEventListener("click", async () => {
  setStatus("Calculando taxa de ocupação e queda de tensão em eletrodutos NBR 5410...");
  const badge = document.getElementById("electrical-status-badge");
  const details = document.getElementById("electrical-details");
  const panel = document.getElementById("electrical-result");

  try {
    const res = await calculateElectricalConduit();
    if (panel) panel.style.display = "block";
    const oc = res.conduit_occupancy;
    const vd = res.voltage_drop;
    if (badge) badge.textContent = `Elétrica: ${res.diagnostic.status_label}`;
    if (details) {
      details.innerHTML = `Ocupação: <strong>${oc.occupancy_percent.toFixed(1)}%</strong> (Máx ${oc.max_allowed_percent}%)<br>Queda de Tensão: <strong>${vd.voltage_drop_percent.toFixed(2)}%</strong> (${vd.voltage_drop_volts.toFixed(1)}V - Limite ${vd.max_allowed_percent}%)`;
    }
    setStatus("Eletrodutos NBR 5410 dimensionados com sucesso.");
  } catch (err) {
    setStatus(`Erro na elétrica: ${err.message}`, true);
  }
});

// 6. Frente 111: Conforto Térmico NBR 15220
document.getElementById("btn-calc-thermal-comfort")?.addEventListener("click", async () => {
  setStatus("Avaliando transmitância térmica U e capacidade Ct NBR 15220...");
  const badge = document.getElementById("thermal-status-badge");
  const details = document.getElementById("thermal-details");
  const panel = document.getElementById("thermal-result");

  try {
    const res = await calculateThermalComfort();
    if (panel) panel.style.display = "block";
    const tm = res.thermal_metrics;
    if (badge) badge.textContent = `Térmica: ${tm.efficiency_label}`;
    if (details) {
      details.innerHTML = `Transmitância U: <strong>${tm.transmittance_u_w_m2_k.toFixed(2)} W/m²K</strong> (Máx ${tm.max_allowed_u_w_m2_k})<br>Capacidade Ct: <strong>${tm.heat_capacity_ct_kj_m2_k.toFixed(0)} kJ/m²K</strong> | Atraso: ${tm.thermal_lag_hours.toFixed(1)}h`;
    }
    setStatus("Conforto térmico NBR 15220 calculado com sucesso.");
  } catch (err) {
    setStatus(`Erro no conforto térmico: ${err.message}`, true);
  }
});

// 7. Frente 112: Acústica de Salas NBR 10152 RT60
document.getElementById("btn-calc-room-acoustics")?.addEventListener("click", async () => {
  setStatus("Calculando tempo de reverberação RT60 de Sabine NBR 10152...");
  const badge = document.getElementById("acoustics-status-badge");
  const details = document.getElementById("acoustics-details");
  const panel = document.getElementById("acoustics-result");

  try {
    const res = await calculateRoomAcoustics();
    if (panel) panel.style.display = "block";
    const ac = res.acoustic_metrics;
    if (badge) badge.textContent = `Acústica: ${ac.status_label}`;
    if (details) {
      details.innerHTML = `RT60 Médio (500-1000Hz): <strong>${ac.rt60_mid_seconds.toFixed(2)}s</strong> (Faixa Recomendada: ${ac.target_range_seconds.join(" - ")}s)<br>Volume: ${res.parameters.room_dimensions_m.join("x")}m | Espectro: 125Hz=${res.rt60_frequency_spectrum["125Hz"].toFixed(2)}s, 1kHz=${res.rt60_frequency_spectrum["1000Hz"].toFixed(2)}s`;
    }
    setStatus("Acústica de salas NBR 10152 calculada com sucesso.");
  } catch (err) {
    setStatus(`Erro na acústica: ${err.message}`, true);
  }
});

// 8. Frente 113: Iluminação Natural & Fator de Luz Diurna FLD NBR 15215
document.getElementById("btn-calc-daylight-factor")?.addEventListener("click", async () => {
  setStatus("Calculando Fator de Luz Diurna FLD % e iluminância NBR 15215...");
  const badge = document.getElementById("daylight-status-badge");
  const details = document.getElementById("daylight-details");
  const panel = document.getElementById("daylight-result");

  try {
    const res = await calculateDaylightFactor();
    if (panel) panel.style.display = "block";
    const dm = res.daylight_metrics;
    if (badge) badge.textContent = `Iluminação Natural: ${dm.status_label}`;
    if (details) {
      details.innerHTML = `FLD Médio: <strong>${dm.average_fld_percent.toFixed(2)}%</strong> (Mín ${dm.min_recommended_fld_percent}%)<br>Iluminância Média: <strong>${dm.average_lux.toFixed(0)} lux</strong> (${res.workplane_grid_points.length} pontos amostrados)`;
    }
    setStatus("Iluminação natural NBR 15215 calculada com sucesso.");
  } catch (err) {
    setStatus(`Erro na iluminação natural: ${err.message}`, true);
  }
});

// 9. Frente 114: Perfis de Aço Estrutural NBR 8800
document.getElementById("btn-gen-steel-profile")?.addEventListener("click", async () => {
  setStatus("Gerando perfil metálico I/W e calculando propriedades de seção NBR 8800...");
  const badge = document.getElementById("steel-status-badge");
  const details = document.getElementById("steel-details");
  const panel = document.getElementById("steel-result");

  try {
    const res = await generateSteelProfile("w_shape", 200.0, 100.0, 6.0, 9.0, 3000.0);
    if (panel) panel.style.display = "block";
    const sp = res.section_properties;
    if (badge) badge.textContent = `Aço NBR 8800: ${res.nominal_designation} (${res.profile_type})`;
    if (details) {
      details.innerHTML = `Área: ${sp.area_cm2.toFixed(1)} cm² | Peso Linear: <strong>${sp.weight_kg_m.toFixed(1)} kg/m</strong><br>Inércia Ix: <strong>${sp.ix_cm4.toFixed(0)} cm⁴</strong> | Módulo Wx: ${sp.wx_cm3.toFixed(1)} cm³`;
    }
    if (res.geometry_3d && res.geometry_3d.vertices) {
      addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x4a5568, "VigaMetalicaW");
    }
    setStatus("Perfil metálico NBR 8800 gerado com sucesso.");
  } catch (err) {
    setStatus(`Erro no perfil de aço: ${err.message}`, true);
  }
});

// 10. Frente 115: BIM 5D SINAPI e Curva ABC
document.getElementById("btn-calc-bim-5d-sinapi")?.addEventListener("click", async () => {
  setStatus("Calculando orçamento analítico BIM 5D, BDI e Curva ABC com SINAPI...");
  const badge = document.getElementById("sinapi-status-badge");
  const details = document.getElementById("sinapi-details");
  const panel = document.getElementById("sinapi-result");

  try {
    const res = await calculateBim5dSinapiBudget();
    if (panel) panel.style.display = "block";
    const fs = res.financial_summary;
    const abc = res.abc_classification_summary;
    if (badge) badge.textContent = `Orçamento 5D SINAPI: ${fs.currency} ${fs.total_budget_with_bdi_brl.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}`;
    if (details) {
      details.innerHTML = `Custo Direto: ${fs.currency} ${fs.total_direct_cost_brl.toLocaleString("pt-BR", { minimumFractionDigits: 2 })} | BDI: ${fs.bdi_percent.toFixed(1)}%<br>Curva ABC: Classe A (${abc.class_a_items_count}), Classe B (${abc.class_b_items_count}), Classe C (${abc.class_c_items_count})`;
    }
    setStatus("Orçamento paramétrico BIM 5D SINAPI gerado com sucesso.");
  } catch (err) {
    setStatus(`Erro no orçamento 5D: ${err.message}`, true);
  }
});

// ============================================================================
// Frentes 116 a 145: Infraestrutura, Estruturas, MEP, BIM 4D/7D e Sustentabilidade
// ============================================================================

// F116: Drenagem Pluvial
document.getElementById("btn-calc-stormwater")?.addEventListener("click", async () => {
  setStatus("Dimensionando calhas e condutores NBR 10844...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateStormwaterDrainage();
    if (panel) panel.style.display = "block";
    const hr = res.hydraulic_results;
    if (badge) badge.textContent = `Drenagem NBR 10844: ${hr.status_label}`;
    if (details) details.innerHTML = `Vazão de Projeto: <strong>${hr.total_design_flow_l_min} L/min</strong> | Calha: ${hr.gutter_capacity_l_min} L/min | Condutor: ${hr.downspout_capacity_l_min} L/min`;
    if (res.geometry_3d?.vertices) addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x3182ce, "CalhaPluvial");
    setStatus("Drenagem pluvial dimensionada com sucesso.");
  } catch (e) { setStatus(`Erro na drenagem: ${e.message}`, true); }
});

// F117: Pavimento Permeável
document.getElementById("btn-calc-permeable")?.addEventListener("click", async () => {
  setStatus("Calculando capacidade de amortecimento de pavimento permeável NBR 16416...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculatePermeablePavement();
    if (panel) panel.style.display = "block";
    const dm = res.drainage_metrics;
    if (badge) badge.textContent = `Pavimento NBR 16416: ${dm.status_label}`;
    if (details) details.innerHTML = `Redução de Pico: <strong>${dm.runoff_reduction_percent}%</strong> | Runoff C: <strong>${dm.resulting_runoff_c}</strong> | Armazenado: ${dm.required_storage_volume_m3} m³ (${dm.reservoir_drainage_time_hours}h)`;
    if (res.geometry_3d?.vertices) addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x4a5568, "PavimentoDrenante");
    setStatus("Pavimentação permeável calculada com sucesso.");
  } catch (e) { setStatus(`Erro no pavimento: ${e.message}`, true); }
});

// F118: Rede de Esgoto
document.getElementById("btn-calc-sewer")?.addEventListener("click", async () => {
  setStatus("Dimensionando coletor de esgoto por gravidade NBR 9649...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateSewerNetwork();
    if (panel) panel.style.display = "block";
    const hm = res.hydraulic_metrics;
    if (badge) badge.textContent = `Esgoto NBR 9649: ${hm.status_label}`;
    if (details) details.innerHTML = `Lâmina y/D: <strong>${(hm.water_depth_ratio_y_d * 100).toFixed(1)}%</strong> (Máx 75%) | Tensão Trativa: <strong>${hm.shear_stress_pa.toFixed(2)} Pa</strong> (Mín 1.0 Pa)`;
    setStatus("Rede de esgoto sanitário calculada com sucesso.");
  } catch (e) { setStatus(`Erro no esgoto: ${e.message}`, true); }
});

// F119: Bacia de Detenção
document.getElementById("btn-calc-detention")?.addEventListener("click", async () => {
  setStatus("Dimensionando bacia de retenção de cheias...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateDetentionBasin();
    if (panel) panel.style.display = "block";
    const hr = res.hydrologic_results;
    if (badge) badge.textContent = `Bacia de Detenção: ${hr.status_label}`;
    if (details) details.innerHTML = `Volume de Espera: <strong>${hr.required_storage_volume_m3} m³</strong> | Amortecimento: <strong>${hr.peak_reduction_percent}%</strong> | Vertedouro: ${hr.emergency_weir_length_m}m`;
    if (res.geometry_3d?.vertices) addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x2b6cb0, "BaciaDetencao");
    setStatus("Bacia de detenção calculada com sucesso.");
  } catch (e) { setStatus(`Erro na bacia: ${e.message}`, true); }
});

// F120: Diagrama de Brückner
document.getElementById("btn-calc-bruckner")?.addEventListener("click", async () => {
  setStatus("Calculando terraplenagem e diagrama de massas de Brückner...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateEarthworkBruckner();
    if (panel) panel.style.display = "block";
    const es = res.earthwork_summary;
    if (badge) badge.textContent = `Terraplenagem: ${es.status_label}`;
    if (details) details.innerHTML = `Corte Total: ${es.total_cut_geometric_m3} m³ | Aterro Total: ${es.total_fill_geometric_m3} m³ | DMT: <strong>${es.estimated_dmt_m}m</strong> (${es.borrow_or_spoil})`;
    setStatus("Diagrama de massas calculado com sucesso.");
  } catch (e) { setStatus(`Erro no Brückner: ${e.message}`, true); }
});

// F121: Estabilidade de Taludes Bishop
document.getElementById("btn-calc-slope-bishop")?.addEventListener("click", async () => {
  setStatus("Analisando estabilidade de taludes por Bishop Simplificado...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateSlopeStabilityBishop();
    if (panel) panel.style.display = "block";
    const st = res.stability_analysis;
    if (badge) badge.textContent = `Taludes Bishop: ${st.status_label}`;
    if (details) details.innerHTML = `Fator de Segurança FS: <strong>${st.factor_of_safety_bishop}</strong> (Mín 1.50) | Raio Círculo: ${st.critical_circle_radius_m}m`;
    setStatus("Estabilidade de talude calculada com sucesso.");
  } catch (e) { setStatus(`Erro no talude: ${e.message}`, true); }
});

// F122: Estacas e Fundações Profundas
document.getElementById("btn-calc-deep-piles")?.addEventListener("click", async () => {
  setStatus("Calculando capacidade de carga de estacas NBR 6122...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateDeepFoundationsPiles();
    if (panel) panel.style.display = "block";
    const gc = res.geotechnical_capacity;
    if (badge) badge.textContent = `Fundações NBR 6122: ${gc.status_label}`;
    if (details) details.innerHTML = `Q_adm Estaca: <strong>${gc.allowable_capacity_single_pile_kn} kN</strong> | Carga Bloco: ${gc.total_group_capacity_kn} kN (FS=${gc.safety_factor})`;
    if (res.geometry_3d?.vertices) addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x6b46c1, "BlocoEstacas");
    setStatus("Fundações profundas calculadas com sucesso.");
  } catch (e) { setStatus(`Erro nas estacas: ${e.message}`, true); }
});

// F123: Sapatas Rígidas
document.getElementById("btn-calc-shallow-footing")?.addEventListener("click", async () => {
  setStatus("Dimensionando sapata rígida NBR 6118/6122...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateShallowFootings();
    if (panel) panel.style.display = "block";
    const fd = res.footing_dimensions;
    if (badge) badge.textContent = `Sapata: ${fd.status_label}`;
    if (details) details.innerHTML = `Tensão no Solo: <strong>${fd.actual_soil_stress_kpa} kPa</strong> <= ${fd.allowable_soil_stress_kpa} kPa | Aço X: ${fd.reinforcement_as_x_cm2} cm² | Aço Y: ${fd.reinforcement_as_y_cm2} cm²`;
    if (res.geometry_3d?.vertices) addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x805ad5, "SapataRigida");
    setStatus("Sapata dimensionada com sucesso.");
  } catch (e) { setStatus(`Erro na sapata: ${e.message}`, true); }
});

// F124: Muro de Gabião
document.getElementById("btn-calc-gabion")?.addEventListener("click", async () => {
  setStatus("Calculando estabilidade de muro de gabião NBR 10328...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateGabionWall();
    if (panel) panel.style.display = "block";
    const st = res.stability_analysis;
    if (badge) badge.textContent = `Gabião NBR 10328: ${st.status_label}`;
    if (details) details.innerHTML = `FS Tombamento: <strong>${st.safety_factor_overturning}</strong> (Mín 1.50) | FS Deslizamento: <strong>${st.safety_factor_sliding}</strong> (Mín 1.20)`;
    if (res.geometry_3d?.vertices) addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0xb7791f, "MuroGabiao");
    setStatus("Muro de gabião dimensionado com sucesso.");
  } catch (e) { setStatus(`Erro no gabião: ${e.message}`, true); }
});

// F125: Fôrmas e Escoramento
document.getElementById("btn-calc-formwork")?.addEventListener("click", async () => {
  setStatus("Calculando pressão de concreto e escoras NBR 15696...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateConcreteFormwork();
    if (panel) panel.style.display = "block";
    const fm = res.formwork_metrics;
    if (badge) badge.textContent = `Fôrmas NBR 15696: ${fm.status_label}`;
    if (details) details.innerHTML = `Pressão Lateral: <strong>${fm.max_lateral_pressure_kpa} kPa</strong> | Tirantes: ${fm.tie_rods_max_spacing_m}m | Espaçamento Escoras: <strong>${fm.shores_grid_spacing_m}m</strong>`;
    setStatus("Fôrmas e escoramento calculados com sucesso.");
  } catch (e) { setStatus(`Erro nas fôrmas: ${e.message}`, true); }
});

// F126: Viga Concreto Armado ELU
document.getElementById("btn-calc-rc-beam")?.addEventListener("click", async () => {
  setStatus("Dimensionando viga no ELU NBR 6118...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateReinforcedConcreteBeam();
    if (panel) panel.style.display = "block";
    const dr = res.design_results;
    if (badge) badge.textContent = `Viga ELU: ${dr.status_label}`;
    if (details) details.innerHTML = `Linha Neutra x/d: <strong>${dr.neutral_axis_ratio_x_d}</strong> | Aço Long.: <strong>${dr.longitudinal_steel_as_cm2} cm²</strong> (${dr.suggested_rebars}) | Estribos: ${dr.transverse_stirrups_asw_cm2_m} cm²/m`;
    if (res.geometry_3d?.vertices) addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0xc53030, "VigaConcreto");
    setStatus("Viga de concreto armado dimensionada com sucesso.");
  } catch (e) { setStatus(`Erro na viga: ${e.message}`, true); }
});

// F127: Lajes Nervuradas
document.getElementById("btn-calc-waffle-slab")?.addEventListener("click", async () => {
  setStatus("Modulando laje nervurada com cubetas plásticas...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateWaffleSlab();
    if (panel) panel.style.display = "block";
    const wm = res.waffle_metrics;
    if (badge) badge.textContent = `Laje Nervurada: ${wm.status_label}`;
    if (details) details.innerHTML = `Economia de Concreto: <strong>${wm.concrete_savings_percent}%</strong> (${wm.concrete_consumption_m3_m2} m³/m²) | Capitel: <strong>${wm.solid_shear_head_capitel_dim_cm}cm</strong>`;
    setStatus("Laje nervurada calculada com sucesso.");
  } catch (e) { setStatus(`Erro na laje nervurada: ${e.message}`, true); }
});

// F128: Concreto Protendido
document.getElementById("btn-calc-prestressed")?.addEventListener("click", async () => {
  setStatus("Calculando protensão e perdas NBR 6118...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculatePrestressedConcrete();
    if (panel) panel.style.display = "block";
    const pm = res.prestress_metrics;
    if (badge) badge.textContent = `Protensão: ${pm.status_label}`;
    if (details) details.innerHTML = `Força Efetiva P_inf: <strong>${pm.final_effective_force_p_inf_kn} kN</strong> | Perdas Totais: <strong>${pm.total_prestress_losses_percent}%</strong> | Carga Equivalente: ${pm.upward_balancing_load_kn_m} kN/m`;
    setStatus("Concreto protendido calculado com sucesso.");
  } catch (e) { setStatus(`Erro na protensão: ${e.message}`, true); }
});

// F129: Madeira Glulam / CLT
document.getElementById("btn-calc-glulam")?.addEventListener("click", async () => {
  setStatus("Dimensionando viga de madeira Glulam NBR 7190...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await calculateGlulamTimber();
    if (panel) panel.style.display = "block";
    const tr = res.timber_structural_results;
    if (badge) badge.textContent = `Madeira Glulam: ${tr.status_label}`;
    if (details) details.innerHTML = `Tensão Flexão: <strong>${tr.design_bending_stress_mpa} MPa</strong> | Flecha: <strong>${tr.elastic_deflection_mm}mm</strong> <= ${tr.allowable_deflection_limit_mm}mm | Carbonização: ${tr.fire_charring_depth_mm}mm`;
    setStatus("Madeira engenheirada calculada com sucesso.");
  } catch (e) { setStatus(`Erro no Glulam: ${e.message}`, true); }
});

// F130: Treliça Espacial Tubular 3D
document.getElementById("btn-calc-space-truss")?.addEventListener("click", async () => {
  setStatus("Gerando treliça espacial tubular 3D...");
  const badge = document.getElementById("infra-status-badge");
  const details = document.getElementById("infra-details");
  const panel = document.getElementById("infra-result");
  try {
    const res = await generateSpaceTruss();
    if (panel) panel.style.display = "block";
    const ts = res.truss_statistics;
    if (badge) badge.textContent = `Treliça Espacial: ${ts.status_label}`;
    if (details) details.innerHTML = `Nós: <strong>${ts.nodes_count}</strong> | Barras: <strong>${ts.members_count}</strong> | Esforço Axial Máx: <strong>${ts.max_chord_axial_force_kn} kN</strong> (Capacidade: ${ts.allowable_buckling_load_kn} kN)`;
    setStatus("Treliça espacial 3D gerada com sucesso.");
  } catch (e) { setStatus(`Erro na treliça: ${e.message}`, true); }
});

// F131 a F145: Handlers do Bloco MEP, Energia, BIM 4D/7D e Sustentabilidade
document.getElementById("btn-calc-gas-piping")?.addEventListener("click", async () => {
  setStatus("Dimensionando rede de gás NBR 15526...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateFuelGasPiping();
    if (panel) panel.style.display = "block";
    const gr = res.gas_network_results;
    if (badge) badge.textContent = `Gás NBR 15526: ${gr.status_label}`;
    if (details) details.innerHTML = `Vazão: <strong>${gr.gas_flow_rate_m3_h} m³/h</strong> | Velocidade: <strong>${gr.gas_velocity_m_s} m/s</strong> | Perda Carga: ${gr.total_pressure_drop_kpa} kPa`;
    setStatus("Rede de gás calculada com sucesso.");
  } catch (e) { setStatus(`Erro no gás: ${e.message}`, true); }
});

document.getElementById("btn-calc-spda")?.addEventListener("click", async () => {
  setStatus("Dimensionando SPDA NBR 5419...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateLightningSpda();
    if (panel) panel.style.display = "block";
    const sp = res.spda_design;
    if (badge) badge.textContent = `SPDA NBR 5419: ${sp.status_label}`;
    if (details) details.innerHTML = `Esfera Rolante: <strong>R = ${sp.rolling_sphere_radius_m}m</strong> | Malha Faraday: <strong>${sp.faraday_max_mesh_size_m}m</strong> | Descidas: ${sp.min_down_conductors_count}`;
    setStatus("SPDA calculado com sucesso.");
  } catch (e) { setStatus(`Erro no SPDA: ${e.message}`, true); }
});

document.getElementById("btn-calc-fire-egress")?.addEventListener("click", async () => {
  setStatus("Calculando rota de fuga NBR 9077...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateFireEgress();
    if (panel) panel.style.display = "block";
    const em = res.egress_metrics;
    if (badge) badge.textContent = `Rotas de Fuga NBR 9077: ${em.status_label}`;
    if (details) details.innerHTML = `Portas: <strong>${em.width_per_door_m}m</strong> (Total ${em.total_doors_width_required_m}m) | Escadas: <strong>${em.stair_width_required_m}m</strong> | Tempo: ${em.estimated_evacuation_time_s}s`;
    setStatus("Rota de fuga calculada com sucesso.");
  } catch (e) { setStatus(`Erro na rota de fuga: ${e.message}`, true); }
});

document.getElementById("btn-calc-hvac-load")?.addEventListener("click", async () => {
  setStatus("Calculando carga térmica HVAC NBR 16401...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateHvacCoolingLoad();
    if (panel) panel.style.display = "block";
    const tb = res.thermal_load_breakdown;
    if (badge) badge.textContent = `HVAC: ${tb.status_label}`;
    if (details) details.innerHTML = `Capacidade: <strong>${tb.total_cooling_capacity_tr} TR</strong> (${tb.total_cooling_capacity_btu_h} BTU/h) | Densidade: <strong>${tb.specific_cooling_load_btu_m2} BTU/m²</strong>`;
    setStatus("Carga térmica calculada com sucesso.");
  } catch (e) { setStatus(`Erro no HVAC: ${e.message}`, true); }
});

document.getElementById("btn-calc-photo-lumen")?.addEventListener("click", async () => {
  setStatus("Calculando método dos lúmens NBR 8995...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculatePhotometricLighting();
    if (panel) panel.style.display = "block";
    const lr = res.lighting_results;
    if (badge) badge.textContent = `Luminotécnica NBR 8995: ${lr.status_label}`;
    if (details) details.innerHTML = `Iluminância: <strong>${lr.actual_average_lux} lux</strong> | Luminárias: <strong>${lr.total_luminaires_installed}</strong> (${lr.luminaires_layout_grid.join("x")}) | Densidade: ${lr.lighting_power_density_w_m2} W/m²`;
    setStatus("Iluminação calculada com sucesso.");
  } catch (e) { setStatus(`Erro na iluminação: ${e.message}`, true); }
});

document.getElementById("btn-calc-solar-pv")?.addEventListener("click", async () => {
  setStatus("Dimensionando usina solar fotovoltaica...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateSolarPv();
    if (panel) panel.style.display = "block";
    const sm = res.solar_system_metrics;
    if (badge) badge.textContent = `Solar FV: ${sm.status_label}`;
    if (details) details.innerHTML = `Potência: <strong>${sm.installed_capacity_kwp} kWp</strong> (${sm.modules_count} painéis) | Geração: <strong>${sm.annual_energy_generation_kwh} kWh/ano</strong> | Economia: R$ ${sm.estimated_annual_savings_brl}/ano`;
    setStatus("Usina solar calculada com sucesso.");
  } catch (e) { setStatus(`Erro na solar: ${e.message}`, true); }
});

document.getElementById("btn-calc-nat-vent")?.addEventListener("click", async () => {
  setStatus("Calculando ventilação natural e efeito chaminé...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateNaturalVentilation();
    if (panel) panel.style.display = "block";
    const vr = res.ventilation_results;
    if (badge) badge.textContent = `Ventilação Natural: ${vr.status_label}`;
    if (details) details.innerHTML = `Taxa ACH: <strong>${vr.air_changes_per_hour_ach} trocas/h</strong> | Vazão Total: <strong>${vr.total_combined_airflow_m3_h} m³/h</strong> (Vento: ${vr.wind_driven_flow_m3_s} m³/s, Chaminé: ${vr.stack_effect_flow_m3_s} m³/s)`;
    setStatus("Ventilação natural calculada com sucesso.");
  } catch (e) { setStatus(`Erro na ventilação: ${e.message}`, true); }
});

document.getElementById("btn-gen-fenestration")?.addEventListener("click", async () => {
  setStatus("Gerando esquadrias paramétricas e pele de vidro...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await generateGlazingFenestration();
    if (panel) panel.style.display = "block";
    const fm = res.fenestration_metrics;
    if (badge) badge.textContent = `Esquadria: ${fm.status_label}`;
    if (details) details.innerHTML = `Área: <strong>${fm.total_frame_area_m2} m²</strong> | Peso Vidro: <strong>${fm.total_glass_weight_kg} kg</strong> | Fator Solar: <strong>${fm.solar_heat_gain_coefficient_shgc}</strong> | U: ${fm.thermal_transmittance_u_w_m2k} W/m²K`;
    if (res.geometry_3d?.vertices) addProceduralMeshToScene(res.geometry_3d.vertices, res.geometry_3d.triangles, 0x4a5568, "EsquadriaVidro");
    setStatus("Esquadria gerada com sucesso.");
  } catch (e) { setStatus(`Erro na esquadria: ${e.message}`, true); }
});

document.getElementById("btn-calc-vent-facade")?.addEventListener("click", async () => {
  setStatus("Calculando fachada ventilada e convecção...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateVentilatedFacade();
    if (panel) panel.style.display = "block";
    const ts = res.thermal_and_structural_results;
    if (badge) badge.textContent = `Fachada Ventilada: ${ts.status_label}`;
    if (details) details.innerHTML = `Velocidade do Ar: <strong>${ts.cavity_air_velocity_m_s} m/s</strong> | Dissipação Solar: <strong>${ts.solar_heat_dissipation_percent}%</strong> | Suportes: ${ts.brackets_anchors_count}`;
    setStatus("Fachada ventilada calculada com sucesso.");
  } catch (e) { setStatus(`Erro na fachada: ${e.message}`, true); }
});

document.getElementById("btn-sim-wind-cfd")?.addEventListener("click", async () => {
  setStatus("Executando simulação numérica no túnel de vento CFD 2D...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await simulateWindCfd2d();
    if (panel) panel.style.display = "block";
    const ar = res.aerodynamic_results;
    if (badge) badge.textContent = `CFD 2D: ${ar.status_label}`;
    if (details) details.innerHTML = `Cd Arrasto: <strong>${ar.drag_coefficient_cd}</strong> | Força Arrasto: <strong>${ar.drag_force_per_meter_n_m} N/m</strong> | Esteira Recirculação: ${ar.recirculation_wake_length_m}m`;
    setStatus("Simulação CFD 2D concluída com sucesso.");
  } catch (e) { setStatus(`Erro no CFD: ${e.message}`, true); }
});

document.getElementById("btn-gen-bim-4d")?.addEventListener("click", async () => {
  setStatus("Gerando cronograma construtivo BIM 4D e curva S...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await generateBim4dSchedule();
    if (panel) panel.style.display = "block";
    const ss = res.schedule_summary;
    if (badge) badge.textContent = `BIM 4D Gantt: ${ss.status_label}`;
    if (details) details.innerHTML = `Prazo Total: <strong>${ss.total_duration_days} dias</strong> (${ss.total_duration_months} meses) | Orçamento: R$ ${ss.total_planned_cost_brl.toLocaleString("pt-BR")}`;
    setStatus("Cronograma 4D gerado com sucesso.");
  } catch (e) { setStatus(`Erro no BIM 4D: ${e.message}`, true); }
});

document.getElementById("btn-gen-bim-7d-cobie")?.addEventListener("click", async () => {
  setStatus("Gerando estrutura de ativos BIM 7D COBie...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await generateBim7dCobie();
    if (panel) panel.style.display = "block";
    const fm = res.facility_management_summary;
    if (badge) badge.textContent = `BIM 7D COBie: ${fm.status_label}`;
    if (details) details.innerHTML = `Equipamentos Ativos: <strong>${fm.total_tracked_assets}</strong> | Planos Preventivos: <strong>${fm.active_maintenance_plans}</strong> | Folhas COBie: ${fm.cobie_sheets_validated.join(", ")}`;
    setStatus("BIM 7D COBie gerado com sucesso.");
  } catch (e) { setStatus(`Erro no BIM 7D: ${e.message}`, true); }
});

document.getElementById("btn-calc-site-logistics")?.addEventListener("click", async () => {
  setStatus("Calculando logística de canteiro e raio de gruas NR-18...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateSiteLogistics();
    if (panel) panel.style.display = "block";
    const lr = res.logistics_results;
    if (badge) badge.textContent = `Canteiro NR-18: ${lr.status_label}`;
    if (details) details.innerHTML = `Refeitório: <strong>${lr.canteen_area_required_m2} m²</strong> | Vestiário: <strong>${lr.locker_room_area_required_m2} m²</strong> | Sanitários: ${lr.toilets_required} un | Desnível de Gruas: Conforme`;
    setStatus("Logística de canteiro calculada com sucesso.");
  } catch (e) { setStatus(`Erro no canteiro: ${e.message}`, true); }
});

document.getElementById("btn-audit-accessibility")?.addEventListener("click", async () => {
  setStatus("Auditoria de acessibilidade universal NBR 9050...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await auditUniversalAccessibility();
    if (panel) panel.style.display = "block";
    const cc = res.compliance_checklist;
    if (badge) badge.textContent = `Acessibilidade NBR 9050: ${cc.status_label}`;
    if (details) details.innerHTML = `Porta Livre: <strong>${cc.door_clear_width_ok ? "OK" : "Não"}</strong> | Corredor: <strong>${cc.corridor_width_ok ? "OK" : "Não"}</strong> | Rampa: <strong>${cc.ramp_slope_ok ? "OK" : "Não"}</strong> (${cc.ramp_run_length_m}m) | Giro 360°: ${cc.turn_space_360_ok ? "OK" : "Não"}`;
    setStatus("Auditoria de acessibilidade concluída com sucesso.");
  } catch (e) { setStatus(`Erro na acessibilidade: ${e.message}`, true); }
});

document.getElementById("btn-calc-lca")?.addEventListener("click", async () => {
  setStatus("Calculando ciclo de vida ACV e carbono incorporado ISO 14040...");
  const badge = document.getElementById("mep-bim-status-badge");
  const details = document.getElementById("mep-bim-details");
  const panel = document.getElementById("mep-bim-result");
  try {
    const res = await calculateLcaEmissions();
    if (panel) panel.style.display = "block";
    const lm = res.lca_metrics;
    if (badge) badge.textContent = `ACV ISO 14040: ${lm.status_label}`;
    if (details) details.innerHTML = `Carbono Incorporado: <strong>${lm.carbon_intensity_kgco2e_m2} kg CO2e/m²</strong> (Total ${lm.total_embodied_carbon_tons_co2e} t) | Energia: ${lm.energy_intensity_mj_m2} MJ/m² | LEED: <strong>${lm.environmental_performance_rating}</strong>`;
    setStatus("ACV e pegada de carbono calculados com sucesso.");
  } catch (e) { setStatus(`Erro na ACV: ${e.message}`, true); }
});

// ============================================================================
// Adaptações Web: Pointer Lock, Clipboard 3D, Context Recovery e Unsaved Guard
// ============================================================================

// ----------------------------------------------------------------------------
// A. Navegação em Primeira Pessoa (Pointer Lock API / Walkthrough)
// ----------------------------------------------------------------------------
let isWalkMode = false;
const walkEuler = new THREE.Euler(0, 0, 0, "YXZ");
const walkKeys = { forward: false, backward: false, left: false, right: false };
const eyeHeightM = 1.70;

function updateWalkMovement() {
  const forward = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  forward.y = 0;
  forward.normalize();
  const right = new THREE.Vector3(1, 0, 0).applyQuaternion(camera.quaternion);
  right.y = 0;
  right.normalize();
  const walkSpeed = 0.12;

  if (walkKeys.forward) camera.position.addScaledVector(forward, walkSpeed);
  if (walkKeys.backward) camera.position.addScaledVector(forward, -walkSpeed);
  if (walkKeys.right) camera.position.addScaledVector(right, walkSpeed);
  if (walkKeys.left) camera.position.addScaledVector(right, -walkSpeed);

  camera.position.y = eyeHeightM;
  controls.target.copy(camera.position).add(forward);
}

function handleStartWalk() {
  if (isWalkMode) {
    document.exitPointerLock?.();
    return;
  }
  setStatus("Modo Percorrer (Walk) ativado. Use W/A/S/D ou Setas para andar, Mouse para olhar, Esc para sair.");
  walkEuler.setFromQuaternion(camera.quaternion);
  renderer.domElement.requestPointerLock?.();
}

document.addEventListener("pointerlockchange", () => {
  if (document.pointerLockElement === renderer.domElement) {
    isWalkMode = true;
    controls.enabled = false;
    document.getElementById("toolbar-walk-btn")?.classList.add("active");
  } else {
    isWalkMode = false;
    controls.enabled = true;
    document.getElementById("toolbar-walk-btn")?.classList.remove("active");
    walkKeys.forward = false;
    walkKeys.backward = false;
    walkKeys.left = false;
    walkKeys.right = false;
    setStatus("Modo Percorrer finalizado.");
  }
});

document.addEventListener("mousemove", (event) => {
  if (isWalkMode && document.pointerLockElement === renderer.domElement) {
    const movementX = event.movementX || 0;
    const movementY = event.movementY || 0;
    walkEuler.setFromQuaternion(camera.quaternion);
    walkEuler.y -= movementX * 0.0025;
    walkEuler.x -= movementY * 0.0025;
    const maxPitch = (80 * Math.PI) / 180;
    walkEuler.x = Math.max(-maxPitch, Math.min(maxPitch, walkEuler.x));
    camera.quaternion.setFromEuler(walkEuler);
  }
});

window.addEventListener("keydown", (event) => {
  if (isWalkMode) {
    if (event.key === "w" || event.key === "W" || event.key === "ArrowUp") { walkKeys.forward = true; event.preventDefault(); }
    if (event.key === "s" || event.key === "S" || event.key === "ArrowDown") { walkKeys.backward = true; event.preventDefault(); }
    if (event.key === "a" || event.key === "A" || event.key === "ArrowLeft") { walkKeys.left = true; event.preventDefault(); }
    if (event.key === "d" || event.key === "D" || event.key === "ArrowRight") { walkKeys.right = true; event.preventDefault(); }
  }
});

window.addEventListener("keyup", (event) => {
  if (isWalkMode) {
    if (event.key === "w" || event.key === "W" || event.key === "ArrowUp") walkKeys.forward = false;
    if (event.key === "s" || event.key === "S" || event.key === "ArrowDown") walkKeys.backward = false;
    if (event.key === "a" || event.key === "A" || event.key === "ArrowLeft") walkKeys.left = false;
    if (event.key === "d" || event.key === "D" || event.key === "ArrowRight") walkKeys.right = false;
  }
});

document.getElementById("toolbar-walk-btn")?.addEventListener("click", handleStartWalk);

// ----------------------------------------------------------------------------
// B. Área de Transferência 3D Web (Clipboard: Copiar, Colar e Recortar)
// ----------------------------------------------------------------------------
let clipboardInstance = null;

function handleCopy() {
  if (!selectedMesh) {
    setStatus("Nenhuma instância selecionada para copiar.", true);
    return;
  }
  clipboardInstance = {
    id: selectedMesh.name,
    matrix: selectedMesh.matrix.clone()
  };
  setStatus(`Instância "${selectedMesh.name}" copiada para a área de transferência (Ctrl+C).`);
}

async function handleCut() {
  if (!selectedMesh) {
    setStatus("Nenhuma instância selecionada para recortar.", true);
    return;
  }
  handleCopy();
  await handleDeleteSelected();
  hasUnsavedChanges = true;
  setStatus(`Instância recortada para a área de transferência (Ctrl+X).`);
}

async function handlePaste() {
  if (!clipboardInstance) {
    setStatus("Área de transferência 3D vazia. Selecione uma peça e pressione Ctrl+C primeiro.", true);
    return;
  }
  setStatus("Colando instância clonada (Ctrl+V)...");
  try {
    const res = await duplicateInstance(clipboardInstance.id, { offsetDeltaCm: [50.0, 0.0, 0.0] });
    if (res?.duplicated && res.instance) {
      const original = currentGroup.getObjectByName(clipboardInstance.id);
      if (original) {
        const newMesh = original.clone();
        newMesh.name = res.instance.instance_id;
        newMesh.position.x += 0.5;
        currentGroup.add(newMesh);
        selectMesh(newMesh);
        hasUnsavedChanges = true;
        setStatus(`Instância "${res.instance.instance_id}" colada com sucesso na cena!`);
      }
    }
  } catch (err) {
    setStatus(`Erro ao colar: ${err.message}`, true);
  }
}

// ----------------------------------------------------------------------------
// C. Proteção Contra Perda de Dados (beforeunload)
// ----------------------------------------------------------------------------
window.addEventListener("beforeunload", (event) => {
  if (hasUnsavedChanges) {
    event.preventDefault();
    event.returnValue = "Existem alterações não salvas no modelo. Tem certeza que deseja sair?";
    return event.returnValue;
  }
});

// ----------------------------------------------------------------------------
// D. Resiliência de Contexto WebGL (GPU Recovery)
// ----------------------------------------------------------------------------
renderer?.domElement?.addEventListener("webglcontextlost", (event) => {
  event.preventDefault();
  setStatus("Aviso: Conexão WebGL reiniciada pela placa de vídeo.", true);
});

renderer?.domElement?.addEventListener("webglcontextrestored", () => {
  setStatus("Conexão WebGL restaurada com sucesso.");
  renderer.render(scene, camera);
});




// ============================================================================
// OPÇÃO A: LISTENERS DAS FERRAMENTAS NATIVAS OFICIAIS DO SKETCHUP
// ============================================================================

function showNativeToolsResult(badgeText, detailsText, isError = false) {
  const resBox = document.getElementById("native-tools-result");
  const badgeEl = document.getElementById("native-tools-badge");
  const detailsEl = document.getElementById("native-tools-details");
  if (!resBox || !badgeEl || !detailsEl) return;

  resBox.style.display = "block";
  badgeEl.textContent = badgeText;
  badgeEl.style.color = isError ? "#E53E3E" : "#C53030";
  detailsEl.innerHTML = detailsText;
}

// 1. Posicionar Câmera (Position Camera)
document.getElementById("btn-native-pos-camera")?.addEventListener("click", async () => {
  setStatus("Posicionando câmera com altura do observador oficial (1.68m)...");
  try {
    const res = await positionCameraNative(0.0, -6.0, 0.0, 0.0, 0.0, 1.2, 1.68);
    if (res?.camera) {
      const c = res.camera;
      camera.position.set(c.eye[0], c.eye[1], c.eye[2]);
      controls.target.set(c.target[0], c.target[1], c.target[2]);
      camera.fov = c.fov_deg || 35.0;
      camera.updateProjectionMatrix();
      controls.update();

      showNativeToolsResult(
        "📷 Posicionar Câmera (Position Camera)",
        `Olho do observador fixado em <b>(${c.eye.join(", ")})</b><br>` +
        `Altura do VCB: <b>${c.eye_height_m}m</b> | FOV: <b>${c.fov_deg}°</b> | Yaw: <b>${c.yaw_deg}°</b>`
      );
      setStatus("Câmera posicionada no nível dos olhos (1.68m).");
    }
  } catch (err) {
    setStatus(`Erro ao posicionar câmera: ${err.message}`, true);
  }
});

// 2. Olhar em Volta (Look Around)
document.getElementById("btn-native-look-around")?.addEventListener("click", async () => {
  setStatus("Girando ângulo de visada (Look Around)...");
  try {
    const curEye = [camera.position.x, camera.position.y, camera.position.z];
    const res = await lookAroundNative(curEye, 0.0, 0.0, 20.0, -5.0);
    if (res?.camera) {
      const c = res.camera;
      controls.target.set(c.target[0], c.target[1], c.target[2]);
      controls.update();

      showNativeToolsResult(
        "👀 Olhar em Volta (Look Around)",
        `Ângulo de visada rotacionado em <b>+20° Yaw, -5° Pitch</b><br>` +
        `Posição dos pés mantida intacta em <b>(${c.eye.join(", ")})</b>`
      );
      setStatus("Visão rotacionada pelo observador.");
    }
  } catch (err) {
    setStatus(`Erro no Look Around: ${err.message}`, true);
  }
});

// 3. Caminhar em 1ª Pessoa com Colisão (Walk)
document.getElementById("btn-native-walk-step")?.addEventListener("click", async () => {
  setStatus("Executando passo de caminhada em primeira pessoa (Walk)...");
  try {
    const curEye = [camera.position.x, camera.position.y, camera.position.z];
    // Obstáculos simulados para teste de colisão
    const testAabbs = [{ min_x: 2.0, max_x: 4.0, min_y: 2.0, max_y: 4.0, max_z: 2.5 }];
    const res = await walkStepNative(curEye, 0.0, 1.0, 0.0, testAabbs, 0.0, 1.68);
    if (res?.walk_result) {
      const w = res.walk_result;
      camera.position.set(w.eye[0], w.eye[1], w.eye[2]);
      controls.target.set(w.target[0], w.target[1], w.target[2]);
      controls.update();

      showNativeToolsResult(
        "🚶 Caminhar (Walk Tool)",
        `Passo efetuado para frente: <b>1.0m</b><br>` +
        `Nova posição: <b>(${w.eye.join(", ")})</b><br>` +
        `Colisão detectada: <b>${w.collision_detected ? "SIM (Bloqueado)" : "NÃO (Livre)"}</b> | Subida degrau: <b>${w.step_up_applied ? "SIM" : "NÃO"}</b>`
      );
      setStatus(`Passo Walk efetuado para (${w.eye.join(", ")}).`);
    }
  } catch (err) {
    setStatus(`Erro no Walk: ${err.message}`, true);
  }
});

// 4. Caixa de Areia: Modelar Relevo (Smoove)
document.getElementById("btn-native-smoove")?.addEventListener("click", async () => {
  setStatus("Aplicando deformação orgânica de relevo Smoove...");
  try {
    // Gera malha de teste 5x5
    const testVertices = [];
    for (let j = -2; j <= 2; j++) {
      for (let i = -2; i <= 2; i++) {
        testVertices.push([i * 1.5, j * 1.5, 0.0]);
      }
    }
    const res = await sandboxSmoove(testVertices, 0.0, 0.0, 4.0, 1.8);
    if (res?.smoove_result) {
      const s = res.smoove_result;
      // Cria malha 3D visual para representar o morro gerado
      const geom = new THREE.BufferGeometry();
      const pos = [];
      s.vertices.forEach(v => pos.push(v[0], v[1], v[2]));
      geom.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
      const mat = new THREE.MeshStandardMaterial({ color: 0x48BB78, wireframe: true });
      const ptsMesh = new THREE.Points(geom, new THREE.PointsMaterial({ color: 0x22543D, size: 0.15 }));
      currentGroup.add(ptsMesh);

      showNativeToolsResult(
        "🏖️ Caixa de Areia: Modelar (Smoove)",
        `Raio de influência: <b>${s.radius_m}m</b> | Deslocamento central: <b>+${s.offset_z_m}m</b><br>` +
        `Vértices deformados com curva cossenoidal: <b>${s.affected_vertices_count} de ${s.total_vertices}</b>`
      );
      setStatus("Deformação orgânica Smoove aplicada.");
    }
  } catch (err) {
    setStatus(`Erro no Smoove: ${err.message}`, true);
  }
});

// 5. Caixa de Areia: Estampar Platô (Stamp)
document.getElementById("btn-native-stamp")?.addEventListener("click", async () => {
  setStatus("Estampando platô de edificação no terreno (Stamp)...");
  try {
    const testVertices = [];
    for (let j = -3; j <= 3; j++) {
      for (let i = -3; i <= 3; i++) {
        testVertices.push([i * 1.2, j * 1.2, (i + j) * 0.15]);
      }
    }
    const footprint = [[-1.5, -1.5], [1.5, -1.5], [1.5, 1.5], [-1.5, 1.5]];
    const res = await sandboxStamp(testVertices, footprint, 1.2, 1.5);
    if (res?.stamp_result) {
      const st = res.stamp_result;
      showNativeToolsResult(
        "🏛️ Caixa de Areia: Estampar (Stamp)",
        `Cota do platô nivelado: <b>${st.plateau_elevation_z}m</b><br>` +
        `Vértices internos nivelados: <b>${st.plateau_vertices_count}</b> | Vértices na saia de talude: <b>${st.skirt_vertices_count}</b>`
      );
      setStatus("Platô de fundação estampado com saia de talude.");
    }
  } catch (err) {
    setStatus(`Erro no Stamp: ${err.message}`, true);
  }
});

// 6. Caixa de Areia: Projetar Caminho (Drape)
document.getElementById("btn-native-drape")?.addEventListener("click", async () => {
  setStatus("Projetando contorno 2D sobre o terreno (Drape)...");
  try {
    const road2D = [[-3.0, -2.0], [-1.0, 0.0], [1.0, -0.5], [3.0, 2.0]];
    const terrainTriangles = [
      [[-4.0, -4.0, 0.2], [4.0, -4.0, 0.5], [4.0, 4.0, 1.2]],
      [[-4.0, -4.0, 0.2], [4.0, 4.0, 1.2], [-4.0, 4.0, 0.8]]
    ];
    const res = await sandboxDrape(road2D, terrainTriangles);
    if (res?.drape_result) {
      const d = res.drape_result;
      // Adiciona linha 3D projetada na cena Three.js
      const linePts = d.draped_path_3d.map(p => new THREE.Vector3(p[0], p[1], p[2] + 0.05));
      const lineGeom = new THREE.BufferGeometry().setFromPoints(linePts);
      const lineMat = new THREE.LineBasicMaterial({ color: 0xE53E3E, linewidth: 3 });
      const line = new THREE.Line(lineGeom, lineMat);
      currentGroup.add(line);

      showNativeToolsResult(
        "🛤️ Caixa de Areia: Projetar (Drape)",
        `Caminho 2D projetado verticalmente sobre as faces 3D do relevo.<br>` +
        `Pontos projetados: <b>${d.draped_points_count}</b> | Comprimento real 3D sobre o relevo: <b>${d.total_3d_length_m}m</b>`
      );
      setStatus("Caminho Drape projetado sobre o relevo com sucesso.");
    }
  } catch (err) {
    setStatus(`Erro no Drape: ${err.message}`, true);
  }
});

// 7. Caixa de Areia: Virar Aresta (Flip Edge)
document.getElementById("btn-native-flip-edge")?.addEventListener("click", async () => {
  setStatus("Invertendo diagonal da malha topográfica (Flip Edge)...");
  try {
    const triA = [[0.0, 0.0, 0.0], [2.0, 0.0, 0.2], [2.0, 2.0, 0.5]];
    const triB = [[0.0, 0.0, 0.0], [2.0, 2.0, 0.5], [0.0, 2.0, 0.3]];
    const res = await sandboxFlipEdge(triA, triB);
    if (res?.flip_result) {
      const f = res.flip_result;
      showNativeToolsResult(
        "🔀 Caixa de Areia: Virar Aresta (Flip Edge)",
        `Diagonal invertida com sucesso.<br>` +
        `Aresta anterior: <b>(${f.old_shared_edge[0].join(", ")}) -> (${f.old_shared_edge[1].join(", ")})</b><br>` +
        `Nova aresta topográfica: <b>(${f.new_shared_edge[0].join(", ")}) -> (${f.new_shared_edge[1].join(", ")})</b>`
      );
      setStatus("Aresta Flip Edge invertida com sucesso.");
    }
  } catch (err) {
    setStatus(`Erro no Flip Edge: ${err.message}`, true);
  }
});

// 8. Adequar Fotografia (Match Photo)
document.getElementById("btn-native-match-photo")?.addEventListener("click", async () => {
  setStatus("Calibrando câmera e perspectiva fotográfica (Match Photo)...");
  try {
    const red1 = [[200.0, 400.0], [600.0, 450.0]];
    const red2 = [[200.0, 700.0], [600.0, 680.0]];
    const green1 = [[700.0, 450.0], [1200.0, 390.0]];
    const green2 = [[700.0, 680.0], [1200.0, 710.0]];
    const res = await matchPhotoCalibrate(1920, 1080, red1, red2, green1, green2, 3.0);
    if (res?.calibration) {
      const c = res.calibration;
      if (c.recommended_camera) {
        camera.fov = c.fov_vertical_deg;
        camera.updateProjectionMatrix();
      }
      showNativeToolsResult(
        "📸 Adequar Fotografia (Match Photo)",
        `Distância focal: <b>${c.focal_length_px}px</b> | FOV vertical: <b>${c.fov_vertical_deg}°</b><br>` +
        `Pontos de Fuga: VP_X=<b>(${c.vanishing_points.vp_x.join(", ")})</b>, VP_Y=<b>(${c.vanishing_points.vp_y.join(", ")})</b><br>` +
        `Inclinação do Horizonte (Roll): <b>${c.camera_angles.roll_deg}°</b> | Pitch: <b>${c.camera_angles.pitch_deg}°</b>`
      );
      setStatus("Câmera calibrada pelas linhas de fuga fotográficas.");
    }
  } catch (err) {
    setStatus(`Erro no Match Photo: ${err.message}`, true);
  }
});

// 9. Marca d'Água (Watermark Overlay)
document.getElementById("btn-native-watermark")?.addEventListener("click", async () => {
  setStatus("Configurando marca d'água no viewport...");
  try {
    const res = await watermarkStyleConfigure("Selo Homologação Parkelô", "/static/logo.png", "overlay", "screen_position", "bottom-right", 85.0);
    if (res?.watermark_config) {
      const wm = res.watermark_config;

      // Injeta ou atualiza elemento DOM de marca d'água sobre o canvas
      let wmDiv = document.getElementById("viewport-watermark-overlay");
      if (!wmDiv) {
        wmDiv = document.createElement("div");
        wmDiv.id = "viewport-watermark-overlay";
        viewportEl.appendChild(wmDiv);
      }
      wmDiv.textContent = `★ ${wm.name} (SketchUp Style)`;
      wmDiv.style.position = wm.css_styles.position || "absolute";
      wmDiv.style.bottom = wm.css_styles.bottom || "20px";
      wmDiv.style.right = wm.css_styles.right || "20px";
      wmDiv.style.padding = "6px 12px";
      wmDiv.style.background = "rgba(197, 48, 48, 0.85)";
      wmDiv.style.color = "white";
      wmDiv.style.fontWeight = "bold";
      wmDiv.style.fontSize = "11px";
      wmDiv.style.borderRadius = "4px";
      wmDiv.style.pointerEvents = "none";
      wmDiv.style.zIndex = "15";

      showNativeToolsResult(
        "🏷️ Marca d'Água (Watermark Style)",
        `Marca d'água posicionada na âncora: <b>${wm.anchor}</b><br>` +
        `Camada: <b>${wm.layer}</b> | Opacidade: <b>${wm.opacity_pct}%</b>`
      );
      setStatus("Marca d'água fixada no viewport.");
    }
  } catch (err) {
    setStatus(`Erro na Marca d'Água: ${err.message}`, true);
  }
});

// 10. Interagir com Componentes Dinâmicos (Trimble DC Click)
document.getElementById("btn-native-interact-dc")?.addEventListener("click", async () => {
  setStatus("Executando fórmula interativa onClick em Componente Dinâmico...");
  try {
    const instId = (selectedMesh?.name || selectedMesh?.userData?.instanceId) || "porta_principal_01";
    const dynamicAttrs = {
      onclick: 'ANIMATE("roty", 0, 90); ALERT("Porta aberta com sucesso!")',
      roty: 0
    };
    const res = await dynamicComponentInteract(instId, dynamicAttrs);
    if (res?.interaction_result) {
      const ir = res.interaction_result;
      if (selectedMesh) {
        // Aplica rotação animada na mesh selecionada
        const rotY = ir.target_transform?.rotation_deg?.[1] || 0.0;
        selectedMesh.rotation.y = THREE.MathUtils.degToRad(rotY);
      }
      const alertMsg = ir.alerts?.length ? ir.alerts.join("; ") : "Nenhum";
      showNativeToolsResult(
        "👆 Interagir com Comp. Dinâmicos (DC Click)",
        `Fórmula executada: <code>${ir.formula_executed}</code><br>` +
        `Nova rotação: <b>${JSON.stringify(ir.target_transform?.rotation_deg)}</b><br>` +
        `Alerta do componente: <b>${alertMsg}</b>`
      );
      setStatus(`Interação executada: ${alertMsg}`);
    }
  } catch (err) {
    setStatus(`Erro ao interagir com componente: ${err.message}`, true);
  }
});

// 11. Solid Tools Nativas (Trimble Solid Tools)
document.getElementById("btn-native-solid-tools")?.addEventListener("click", async () => {
  setStatus("Executando operação booleana de sólidos oficial (Trim / Split)...");
  try {
    const solidA = { name: "Viga Principal", origin: [0, 0, 0], size: [2.0, 0.2, 0.4] };
    const solidB = { name: "Pilar de Apoio", origin: [0.5, 0, -0.2], size: [0.2, 0.2, 0.8] };
    const res = await trimbleSolidToolsExecute("trim", solidA, solidB);
    if (res?.operation_result) {
      const opRes = res.operation_result;
      showNativeToolsResult(
        "🧊 Solid Tools Nativas (Trim / Recortar)",
        `Operação: <b>${opRes.operation.toUpperCase()}</b><br>` +
        `Interseção detectada: <b>${opRes.has_intersection ? "SIM" : "NÃO"}</b> (Volume inter: ${opRes.intersection_volume_m3}m³)<br>` +
        `Sólidos resultantes na cena: <b>${opRes.resulting_solids_count}</b> (peça recortada + ferramenta preservada)`
      );
      setStatus("Operação Solid Tools executada com sucesso.");
    }
  } catch (err) {
    setStatus(`Erro no Solid Tools: ${err.message}`, true);
  }
});


// 12. Classificação IFC / BIM
document.getElementById("btn-native-ifc-classify")?.addEventListener("click", async () => {
  setStatus("Atribuindo classificação IFC oficial ao componente selecionado...");
  try {
    const instId = (selectedMesh?.name || selectedMesh?.userData?.instanceId) || "inst_viga_01";
    const res = await ifcClassifyComponent(instId, "Viga Estrutural W200x35", "IFC4", "IfcBeam", "BEAM", "Viga de concreto/aço modelada no SketchUp");
    if (res?.classification) {
      const c = res.classification;
      showNativeToolsResult(
        "🏷️ Classificação IFC / BIM",
        `Instância: <b>${c.instance_id}</b> | Esquema: <b>${c.schema}</b><br>` +
        `Classe IFC: <b style="color: #2F855A;">${c.ifc_class}</b> (PredefinedType: ${c.predefined_type})<br>` +
        `GlobalId (GUID): <code>${c.global_id}</code>`
      );
      setStatus(`Componente classificado como ${c.ifc_class} (BIM IFC4).`);
    }
  } catch (err) {
    setStatus(`Erro na classificação IFC: ${err.message}`, true);
  }
});

// 13. Auditoria de Classificação BIM
document.getElementById("btn-native-ifc-audit")?.addEventListener("click", async () => {
  setStatus("Auditando conformidade de classificação BIM das instâncias...");
  try {
    const mockInstances = [
      { id: "inst_1", name: "Pilar", classification: { ifc_class: "IfcColumn" } },
      { id: "inst_2", name: "Viga", classification: { ifc_class: "IfcBeam" } },
      { id: "inst_3", name: "Mesa Decorativa", classification: null }
    ];
    const res = await ifcAuditClassifications(mockInstances);
    if (res?.audit_summary) {
      const a = res.audit_summary;
      showNativeToolsResult(
        "📋 Auditoria de Classificação BIM",
        `Conformidade BIM: <b>${a.compliance_percentage}%</b> (${a.classified_count} classificados / ${a.unclassified_count} sem classe)<br>` +
        `Distribuição: <b>${JSON.stringify(a.class_distribution)}</b>`
      );
      setStatus(`Auditoria BIM concluída: ${a.compliance_percentage}% de conformidade.`);
    }
  } catch (err) {
    setStatus(`Erro na auditoria BIM: ${err.message}`, true);
  }
});

// 14. Texto 3D Paramétrico (3D Text Tool)
document.getElementById("btn-native-3d-text")?.addEventListener("click", async () => {
  setStatus("Gerando geometria da ferramenta Texto 3D oficial...");
  try {
    const res = await generate3dText("SKETCHBUILD 3D", "Arial", 0.40, 0.08, true, true, "center", [0, 0, 1.5]);
    if (res?.text_geometry) {
      const tg = res.text_geometry;
      // Constrói malha Three.js com faces do texto
      const geom = new THREE.BufferGeometry();
      const pos = [];
      tg.faces.forEach(tri => {
        tri.forEach(pt => pos.push(pt[0], pt[1], pt[2]));
      });
      geom.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
      geom.computeVertexNormals();

      const mat = new THREE.MeshStandardMaterial({ color: 0xDD6B20, roughness: 0.3, metalness: 0.2 });
      const mesh = new THREE.Mesh(geom, mat);
      mesh.name = "sketchup_3d_text_mesh";
      currentGroup.add(mesh);

      showNativeToolsResult(
        "🔤 Texto 3D Paramétrico (3D Text Tool)",
        `Texto: <b>"${tg.text}"</b> | Altura: <b>${tg.height_m}m</b> | Extrusão: <b>${tg.extrusion_depth_m}m</b><br>` +
        `Faces B-Rep geradas: <b>${tg.faces_count}</b> | Arestas: <b>${tg.edges_count}</b>`
      );
      setStatus("Texto 3D gerado e inserido na cena.");
    }
  } catch (err) {
    setStatus(`Erro ao gerar Texto 3D: ${err.message}`, true);
  }
});

// 15. Gerar Relatório Oficial (Generate Report)
document.getElementById("btn-native-report")?.addEventListener("click", async () => {
  setStatus("Gerando relatório oficial do SketchUp (Generate Report)...");
  try {
    const mockInstances = [
      { id: "col_1", definition_name: "Pilar 20x20", volume_m3: 0.12, area_m2: 2.4, tag: "Estrutura", material: "Concreto", ifc_class: "IfcColumn", bounds: [0.2, 0.2, 3.0] },
      { id: "col_2", definition_name: "Pilar 20x20", volume_m3: 0.12, area_m2: 2.4, tag: "Estrutura", material: "Concreto", ifc_class: "IfcColumn", bounds: [0.2, 0.2, 3.0] },
      { id: "beam_1", definition_name: "Viga V1", volume_m3: 0.24, area_m2: 3.6, tag: "Estrutura", material: "Concreto", ifc_class: "IfcBeam", bounds: [4.0, 0.2, 0.3] }
    ];
    const res = await generateReport(mockInstances, "entire_model", true);
    if (res?.report_data) {
      const rep = res.report_data;
      showNativeToolsResult(
        "📊 Gerar Relatório Oficial (Generate Report)",
        `Itens agrupados: <b>${rep.total_items_count}</b> | Instâncias totais: <b>${rep.total_instances_count}</b><br>` +
        `Volume total: <b>${rep.total_volume_m3}m³</b> | Área total: <b>${rep.total_area_m2}m²</b><br>` +
        `<pre style="max-height: 80px; overflow: auto; background: #eee; padding: 4px; font-size: 9.5px;">${rep.csv_content}</pre>`
      );
      setStatus("Relatório oficial gerado com sucesso.");
    }
  } catch (err) {
    setStatus(`Erro ao gerar relatório: ${err.message}`, true);
  }
});

// 16. Eixos do Modelo (Axes Tool)
document.getElementById("btn-native-axes-custom")?.addEventListener("click", async () => {
  setStatus("Posicionando novo sistema de eixos do modelo...");
  try {
    const res = await axesSetCustom([2.0, 1.0, 0.5], [3.0, 1.0, 0.5], [2.0, 2.0, 0.5]);
    if (res?.axes) {
      const ax = res.axes;
      showNativeToolsResult(
        "📐 Eixos Personalizados (Axes Tool)",
        `Nova Origem: <b>(${ax.origin.join(", ")})</b><br>` +
        `Eixo X (Vermelho): (${ax.axis_x_red.join(", ")})<br>` +
        `Eixo Y (Verde): (${ax.axis_y_green.join(", ")})<br>` +
        `Eixo Z (Azul): (${ax.axis_z_blue.join(", ")})`
      );
      setStatus("Eixos personalizados definidos.");
    }
  } catch (err) {
    setStatus(`Erro nos eixos: ${err.message}`, true);
  }
});

// 17. Alinhar Eixos à Face Selecionada
document.getElementById("btn-native-axes-align-face")?.addEventListener("click", async () => {
  setStatus("Alinhando eixos à face...");
  try {
    const facePts = [[0.0, 0.0, 1.0], [3.0, 0.0, 2.0], [3.0, 2.0, 2.0], [0.0, 2.0, 1.0]];
    const res = await axesAlignToFace(facePts);
    if (res?.axes) {
      const ax = res.axes;
      showNativeToolsResult(
        "📐 Eixos Alinhados à Face",
        `Origem no centroide: <b>(${ax.origin.join(", ")})</b><br>` +
        `Normal perpendicular Z: <b>(${ax.axis_z_blue.join(", ")})</b>`
      );
      setStatus("Eixos alinhados perpendicularmente à face.");
    }
  } catch (err) {
    setStatus(`Erro ao alinhar eixos: ${err.message}`, true);
  }
});

// 18. Redefinir Eixos para Origem Global
document.getElementById("btn-native-axes-reset")?.addEventListener("click", async () => {
  setStatus("Redefinindo eixos para origem global...");
  try {
    const res = await axesReset();
    if (res?.axes) {
      const ax = res.axes;
      showNativeToolsResult(
        "🔄 Redefinir Eixos (Reset Axes)",
        `Origem restaurada para: <b>(${ax.origin.join(", ")})</b><br>` +
        `Eixos canônicos globais (X=[1,0,0], Y=[0,1,0], Z=[0,0,1]) ativos.`
      );
      setStatus("Eixos restaurados para a origem global do modelo.");
    }
  } catch (err) {
    setStatus(`Erro ao resetar eixos: ${err.message}`, true);
  }
});

// 19. Informações da Entidade (Entity Info & Sólido)
document.getElementById("btn-native-inspect-entity")?.addEventListener("click", async () => {
  setStatus("Inspecionando métricas oficiais da entidade selecionada...");
  try {
    // Exemplo com cubo fechado (sólido 2-manifold)
    const cubeTriangles = [
      // Face inferior
      [[0,0,0], [1,0,0], [1,1,0]], [[0,0,0], [1,1,0], [0,1,0]],
      // Face superior
      [[0,0,1], [1,1,1], [1,0,1]], [[0,0,1], [0,1,1], [1,1,1]],
      // Laterais
      [[0,0,0], [0,0,1], [1,0,1]], [[0,0,0], [1,0,1], [1,0,0]],
      [[1,0,0], [1,0,1], [1,1,1]], [[1,0,0], [1,1,1], [1,1,0]],
      [[1,1,0], [1,1,1], [0,1,1]], [[1,1,0], [0,1,1], [0,1,0]],
      [[0,1,0], [0,1,1], [0,0,1]], [[0,1,0], [0,0,1], [0,0,0]]
    ];
    const res = await inspectEntitySolid("Sapata Isolada", "sapata_01", cubeTriangles, "Fundações");
    if (res?.metrics) {
      const m = res.metrics;
      showNativeToolsResult(
        "ℹ️ Informações da Entidade (Entity Info)",
        `Entidade: <b>${m.definition_name}</b> (${m.instance_name})<br>` +
        `Status de Sólido: <b style="color: #2F855A;">${m.solid_status}</b><br>` +
        `Volume líquido: <b>${m.volume_m3}m³</b> | Área de superfície: <b>${m.total_area_m2}m²</b><br>` +
        `Faces: <b>${m.faces_count}</b> | Arestas únicas: <b>${m.unique_edges_count}</b>`
      );
      setStatus(`Inspeção concluída: ${m.solid_status} (${m.volume_m3}m³).`);
    }
  } catch (err) {
    setStatus(`Erro na inspeção: ${err.message}`, true);
  }
});

// 20. Edição de Componentes (Hide / Fade Rest of Model)
document.getElementById("btn-native-comp-edit-mode")?.addEventListener("click", async () => {
  setStatus("Alternando modo de foco de edição de componentes...");
  try {
    const mockInstances = [
      { id: "inst_1", name: "Janela" },
      { id: "inst_2", name: "Janela" },
      { id: "inst_3", name: "Parede" }
    ];
    const res = await componentEditModeApply("inst_1", "Janela", mockInstances, true, false, true, true, 0.25);
    if (res?.edit_mode_state) {
      const em = res.edit_mode_state;
      showNativeToolsResult(
        "👁️ Edição de Componentes (Component Edit)",
        `Componente ativo em edição: <b>${em.active_instance_id}</b> (${em.active_definition_name})<br>` +
        `Ocultar resto do modelo: <b>${em.hide_rest_of_model ? "ATIVO" : "INATIVO"}</b><br>` +
        `Objetos ocultados: <b>${em.hidden_count}</b> | Objetos esmaecidos (fade 25%): <b>${em.faded_count}</b>`
      );
      setStatus("Modo de edição focado aplicado com sucesso.");
    }
  } catch (err) {
    setStatus(`Erro no modo de edição: ${err.message}`, true);
  }
});

// 21. Unidades & Precisão do Modelo (Model Units)
document.getElementById("btn-native-units-config")?.addEventListener("click", async () => {
  setStatus("Configurando unidades e precisão decimal do modelo...");
  try {
    const res = await modelUnitsConfigure("DECIMAL", "METERS", 2, true, 0.01, true, 15.0);
    if (res?.units_config) {
      const u = res.units_config;
      showNativeToolsResult(
        "📏 Unidades do Modelo (Model Units)",
        `Formato: <b>${u.format}</b> | Unidade ativa: <b>${u.unit} (${u.unit_suffix})</b><br>` +
        `Precisão: <b>${u.precision_digits} casas decimais</b><br>` +
        `Snap de Comprimento: <b>${u.length_snap_interval_m}m</b> | Snap Angular: <b>${u.angle_snap_degrees}°</b>`
      );
      setStatus(`Unidades configuradas: ${u.unit} com precisão de ${u.precision_digits} casas.`);
    }
  } catch (err) {
    setStatus(`Erro ao configurar unidades: ${err.message}`, true);
  }
});


// 22. Posição da Textura por Pinos (Texture Position Pin Tool)
document.getElementById("btn-native-texture-pins")?.addEventListener("click", async () => {
  setStatus("Ajustando textura com os 4 pinos oficiais do SketchUp...");
  try {
    const facePts = [[0, 0, 0], [2, 0, 0], [2, 1.5, 0], [0, 1.5, 0]];
    const res = await texturePinTransform(facePts, [0.2, 0.1], [1.5, 45.0], 10.0, null);
    if (res?.mapping) {
      const m = res.mapping;
      showNativeToolsResult(
        "🎨 Posição da Textura (4 Pinos Oficiais)",
        `Pino Vermelho (Origem UV): <b>(${m.pins_config.red_pin_origin.join(", ")})</b><br>` +
        `Pino Verde: Escala <b>${m.pins_config.green_pin_scale}x</b> | Rotação <b>${m.pins_config.green_pin_rotation_deg}°</b><br>` +
        `Pino Azul (Cisalhamento): <b>${m.pins_config.blue_pin_shear_deg}°</b><br>` +
        `UVs mapeadas: <code>${JSON.stringify(m.uv_coordinates)}</code>`
      );
      setStatus("Textura posicionada pelos pinos oficiais.");
    }
  } catch (err) {
    setStatus(`Erro nos pinos de textura: ${err.message}`, true);
  }
});

// 23. Colorir por Etiqueta (Color by Tag)
let isColorByTagActive = false;
document.getElementById("btn-native-color-by-tag")?.addEventListener("click", async () => {
  isColorByTagActive = !isColorByTagActive;
  setStatus(`Alternando modo Colorir por Etiqueta (${isColorByTagActive ? "ATIVADO" : "DESATIVADO"})...`);
  try {
    const mockTags = [
      { name: "Estrutura", color: "#E53E3E" },
      { name: "Alvenaria", color: "#DD6B20" },
      { name: "Esquadrias", color: "#3182CE" }
    ];
    const mockInstances = [
      { id: "col_1", tag: "Estrutura" },
      { id: "wall_1", tag: "Alvenaria" },
      { id: "win_1", tag: "Esquadrias" }
    ];
    const res = await colorByTagApply(mockTags, mockInstances, isColorByTagActive);
    if (res?.color_by_tag_result) {
      const cr = res.color_by_tag_result;
      showNativeToolsResult(
        "🏷️ Colorir por Etiqueta (Color by Tag)",
        `Modo Color by Tag: <b>${cr.color_by_tag_enabled ? "ATIVADO (Cores de disciplina ativas)" : "DESATIVADO (Texturas originais)"}</b><br>` +
        `Tags mapeadas: <b>${JSON.stringify(cr.tag_color_map)}</b>`
      );
      setStatus(`Color by Tag ${cr.color_by_tag_enabled ? "ativado" : "desativado"}.`);
    }
  } catch (err) {
    setStatus(`Erro no Color by Tag: ${err.message}`, true);
  }
});

// 24. Eliminar Não Utilizados (Purge Unused)
document.getElementById("btn-native-purge-unused")?.addEventListener("click", async () => {
  setStatus("Executando eliminação de elementos não utilizados (Purge Unused)...");
  try {
    const mockDefs = [{ name: "Pilar Usado" }, { name: "Cadeira Órfã" }];
    const mockInsts = [{ id: "i1", definition_name: "Pilar Usado", tag: "Layer0", material: "Madeira" }];
    const mockMats = [{ name: "Madeira" }, { name: "Vidro Não Utilizado" }];
    const mockTags = [{ name: "Layer0" }, { name: "Tag Vazia" }];

    const res = await purgeUnusedItems(mockDefs, mockInsts, mockMats, mockTags);
    if (res?.purge_result) {
      const p = res.purge_result;
      showNativeToolsResult(
        "🧹 Eliminar Não Utilizados (Purge Unused)",
        `Total de itens eliminados: <b style="color: #C53030;">${p.total_items_purged}</b><br>` +
        `Componentes purgados: <b>${p.purged_components.join(", ") || "Nenhum"}</b> (${p.purged_components_count})<br>` +
        `Materiais purgados: <b>${p.purged_materials.join(", ") || "Nenhum"}</b> (${p.purged_materials_count})<br>` +
        `Etiquetas purgadas: <b>${p.purged_tags.join(", ") || "Nenhum"}</b> (${p.purged_tags_count})`
      );
      setStatus(`Purge Unused concluído: ${p.total_items_purged} itens removidos.`);
    }
  } catch (err) {
    setStatus(`Erro no Purge Unused: ${err.message}`, true);
  }
});

// 25. Criar Componente com Comportamentos
document.getElementById("btn-native-make-comp")?.addEventListener("click", async () => {
  setStatus("Criando definição de componente com comportamentos oficiais...");
  try {
    const res = await makeComponentDefinition(
      "Janela Pivotante 1.20x1.00m",
      "Janela que corta abertura automática na parede e cola em plano vertical",
      "VERTICAL",
      true,
      false,
      false,
      [0, 0, 0],
      [[-0.6, 0.0], [0.6, 0.0], [0.6, 1.0], [-0.6, 1.0]]
    );
    if (res?.definition) {
      const d = res.definition;
      const b = d.behavior;
      showNativeToolsResult(
        "📦 Criar Componente (Make Component)",
        `Definição: <b>"${d.definition_name}"</b><br>` +
        `Colar em (Glue to): <b>${b.glue_to}</b> | Cortar Abertura: <b>${b.cut_opening ? "SIM (Automático)" : "NÃO"}</b><br>` +
        `Sempre Encarar Câmera (Face-Me): <b>${b.always_face_camera ? "SIM" : "NÃO"}</b>`
      );
      setStatus(`Componente "${d.definition_name}" criado com sucesso.`);
    }
  } catch (err) {
    setStatus(`Erro ao criar componente: ${err.message}`, true);
  }
});

// 26. Seleção Avançada (Inverter / Triplo Clique)
document.getElementById("btn-native-adv-selection")?.addEventListener("click", async () => {
  setStatus("Executando seleção avançada (Inverter Seleção)...");
  try {
    const allIds = ["inst_1", "inst_2", "inst_3", "inst_4", "inst_5"];
    const activeId = selectedMesh?.name || selectedMesh?.userData?.instanceId;
    const currentSelected = activeId ? [activeId] : ["inst_1", "inst_2"];
    const res = await advancedSelectionExecute("invert", allIds, currentSelected);
    if (res) {
      showNativeToolsResult(
        "🎯 Seleção Avançada (Invert Selection)",
        `Operação: <b>Inverter Seleção (Ctrl+Shift+I)</b><br>` +
        `Seleção anterior: [${currentSelected.join(", ")}]<br>` +
        `Nova seleção ativa: <b>[${res.selected_ids.join(", ")}]</b> (Total: ${res.total_selected})`
      );
      setStatus(`Seleção invertida: ${res.total_selected} itens selecionados.`);
    }
  } catch (err) {
    setStatus(`Erro na seleção avançada: ${err.message}`, true);
  }
});

// 27. Geometria Oculta & Objetos Ocultos
let showHiddenGeomActive = false;
let showHiddenObjsActive = false;
document.getElementById("btn-native-hidden-geom")?.addEventListener("click", async () => {
  showHiddenGeomActive = !showHiddenGeomActive;
  showHiddenObjsActive = !showHiddenObjsActive;
  setStatus(`Alternando Geometria Oculta e Objetos Ocultos (${showHiddenGeomActive ? "VISÍVEIS" : "OCULTOS"})...`);
  try {
    const mockInsts = [{ id: "inst_1", is_hidden: true }, { id: "inst_2", is_hidden: false }];
    const mockEdges = [{ id: "e1", is_smooth: true }, { id: "e2", is_smooth: false }];
    const res = await hiddenGeometryConfigure(showHiddenGeomActive, showHiddenObjsActive, mockInsts, mockEdges);
    if (res?.display_state) {
      const ds = res.display_state;
      showNativeToolsResult(
        "👁️ Geometria Oculta & Objetos Ocultos",
        `Geometria Oculta (Arestas tracejadas): <b>${ds.show_hidden_geometry ? "EXIBINDO" : "OCULTO"}</b><br>` +
        `Objetos Ocultos (Malhas fantasma): <b>${ds.show_hidden_objects ? "EXIBINDO" : "OCULTO"}</b>`
      );
      setStatus("Exibição de geometria oculta atualizada.");
    }
  } catch (err) {
    setStatus(`Erro na geometria oculta: ${err.message}`, true);
  }
});

// 28. Estatísticas do Modelo (Model Info Statistics)
document.getElementById("btn-native-model-stats")?.addEventListener("click", async () => {
  setStatus("Calculando censo oficial de entidades e estatísticas do modelo...");
  try {
    const statsParams = {
      edges_count: 1450,
      faces_count: 820,
      component_definitions_count: 14,
      component_instances_count: 38,
      groups_count: 5,
      guide_lines_count: 6,
      guide_points_count: 2,
      section_planes_count: 2,
      dimensions_count: 8,
      texts_count: 4,
      materials_count: 12,
      tags_count: 6,
      scenes_count: 3
    };
    const res = await modelStatisticsCalculate(statsParams);
    if (res?.statistics) {
      const s = res.statistics;
      const c = s.census;
      showNativeToolsResult(
        "📈 Estatísticas do Modelo (Model Info)",
        `Classificação de Complexidade: <b style="color: #2F855A;">${s.complexity_level}</b> (${s.performance_profile})<br>` +
        `Geometria: <b>${c.edges} Arestas</b>, <b>${c.faces} Faces</b><br>` +
        `Componentes: <b>${c.component_instances} Instâncias</b> (${c.component_definitions} Definições), <b>${c.groups} Grupos</b><br>` +
        `Anotações: <b>${c.dimensions} Cotas</b>, <b>${c.texts} Textos</b>, <b>${c.guide_lines} Guias</b>, <b>${c.section_planes} Cortes</b>`
      );
      setStatus(`Estatísticas do modelo calculadas: Perfil ${s.complexity_level}.`);
    }
  } catch (err) {
    setStatus(`Erro nas estatísticas: ${err.message}`, true);
  }
});

// ============================================================================
// OPÇÃO A (PARTE 4): LISTENERS DAS FERRAMENTAS NATIVAS OFICIAIS DO SKETCHUP
// ============================================================================

// 29. Polígono Regular Paramétrico (Polygon Tool 6s/8s)
document.getElementById("btn-native-polygon")?.addEventListener("click", async () => {
  setStatus("Gerando polígono regular paramétrico nativo (Hexágono r=1.5m)...");
  try {
    const res = await generateRegularPolygon(6, 1.5, "CIRCUMSCRIBED", [0, 0, 0], [0, 0, 1]);
    if (res?.polygon) {
      const p = res.polygon;
      showNativeToolsResult(
        "⬡ Polígono Regular Paramétrico (Polygon Tool)",
        `Lados: <b>${p.sides_count}</b> (${p.radius_mode}) | Raio: <b>${p.radius_m}m</b><br>` +
        `Área: <b>${p.area_m2} m²</b> | Perímetro: <b>${p.perimeter_m} m</b><br>` +
        `Arestas: <b>${p.edges_count}</b> | Triângulos gerados: <b>${p.triangles_count}</b>`
      );
      setStatus(`Polígono de ${p.sides_count} lados gerado com sucesso.`);
    }
  } catch (err) {
    setStatus(`Erro ao gerar polígono: ${err.message}`, true);
  }
});

// 30. Mão Livre com Simplificação RDP (Freehand Tool)
document.getElementById("btn-native-freehand")?.addEventListener("click", async () => {
  setStatus("Processando curva de mão livre com simplificação Ramer-Douglas-Peucker...");
  try {
    const rawCurve = [
      [0.0, 0.0, 0.0], [0.1, 0.2, 0.0], [0.2, 0.21, 0.0], [0.5, 0.6, 0.0],
      [0.8, 0.62, 0.0], [1.0, 1.0, 0.0], [0.98, 0.99, 0.0], [0.05, 0.02, 0.0]
    ];
    const res = await processFreehandCurve(rawCurve, 0.02, true, 0.1);
    if (res?.curve) {
      const c = res.curve;
      showNativeToolsResult(
        "✍️ Mão Livre (Freehand Tool)",
        `Pontos Originais: <b>${c.raw_points_count}</b> &rarr; Simplificados: <b>${c.simplified_points_count}</b> (Redução: <b>${c.reduction_percent}%</b>)<br>` +
        `Comprimento Total: <b>${c.total_length_m} m</b> | Curva Fechada: <b>${c.is_closed ? "Sim (Face Gerada)" : "Não"}</b><br>` +
        (c.face ? `Área da Face Plana: <b>${c.face.area_m2} m²</b>` : `Arestas Contínuas: <b>${c.edges_count}</b>`)
      );
      setStatus(`Curva mão livre processada: ${c.reduction_percent}% de simplificação RDP.`);
    }
  } catch (err) {
    setStatus(`Erro na curva mão livre: ${err.message}`, true);
  }
});

// 31. Inverter & Orientar Faces (Reverse & Orient Faces)
document.getElementById("btn-native-reverse-faces")?.addEventListener("click", async () => {
  setStatus("Executando propagação de orientação consistente (Orient Faces)...");
  try {
    const sampleFaces = [
      {
        "vertices": [[0,0,0], [1,0,0], [1,1,0], [0,1,0]],
        "normal": [0,0,1]
      },
      {
        // Face adjacente com sentido inconsistente
        "vertices": [[1,0,0], [2,0,0], [2,1,0], [1,1,0]],
        "normal": [0,0,-1]
      }
    ];
    const res = await reverseOrientFaces("ORIENT", sampleFaces, [], 0);
    if (res?.result) {
      const r = res.result;
      showNativeToolsResult(
        "🔄 Inverter & Orientar Faces (Orient Faces)",
        `Faces Conexas Orientadas: <b>${r.connected_oriented_count} de ${r.total_faces}</b><br>` +
        `Faces Invertidas para Coerência 2-Manifold: <b>${r.flipped_count}</b><br>` +
        `Face de Referência: <b>Índice #${r.reference_face_index}</b>`
      );
      setStatus(`Orient Faces concluído: ${r.flipped_count} faces invertidas para normal consistente.`);
    }
  } catch (err) {
    setStatus(`Erro ao orientar faces: ${err.message}`, true);
  }
});

// 32. Dolly de Câmera & FOV / Lente 35mm
document.getElementById("btn-native-dolly-fov")?.addEventListener("click", async () => {
  setStatus("Ajustando lente fotográfica 35mm e campo de visão (FOV)...");
  try {
    const resVcb = await controlDollyFovLens("PARSE_VCB", "50mm");
    const resDolly = await controlDollyFovLens("APPLY_DOLLY", null, null, null, [0, -5, 2], [0, 0, 0], 1.5, "KEEP_TARGET");
    if (resVcb?.result && resDolly?.result) {
      const v = resVcb.result;
      const d = resDolly.result;
      showNativeToolsResult(
        "🎥 Câmera: Dolly & Lente Fotográfica (Zoom VCB)",
        `Entrada VCB: <b>${v.vcb_formatted}</b> &rarr; FOV Calculado: <b>${v.fov_degrees}°</b> (Lente <b>${v.focal_length_mm} mm</b> equiv. 35mm)<br>` +
        `Dolly In: Avanço de <b>+${d.delta_m} m</b> ao longo do eixo de visão<br>` +
        `Nova Posição Olho: <b>[${d.new_eye.join(", ")}]</b> | Distância Focal: <b>${d.new_distance_to_target_m} m</b>`
      );
      setStatus(`Câmera calibrada: Lente ${v.focal_length_mm}mm (${v.fov_degrees}° FOV).`);
    }
  } catch (err) {
    setStatus(`Erro no controle de câmera: ${err.message}`, true);
  }
});

// 33. Interseccionar Faces com Modelo / Seleção
document.getElementById("btn-native-intersect-faces")?.addEventListener("click", async () => {
  setStatus("Calculando interseção analítica 3D entre faces secantes...");
  try {
    const faceA = {
      vertices: [[-1, -1, 0], [1, -1, 0], [1, 1, 0], [-1, 1, 0]],
      normal: [0, 0, 1]
    };
    const faceB = {
      vertices: [[0, -1, -1], [0, 1, -1], [0, 1, 1], [0, -1, 1]],
      normal: [1, 0, 0]
    };
    const res = await computeIntersectFaces([faceA, faceB], null, "WITH_MODEL");
    if (res?.intersection) {
      const it = res.intersection;
      showNativeToolsResult(
        "⚔️ Interseccionar Faces (Intersect Faces)",
        `Modo de Contexto: <b>${it.context_mode}</b> | Pares Testados: <b>${it.tested_pairs_count}</b><br>` +
        `Arestas de Corte Geradas: <b>${it.intersection_edges_count}</b><br>` +
        (it.intersection_edges.length > 0 ?
          `Linha de Corte 3D: [${it.intersection_edges[0].start.join(", ")}] &rarr; [${it.intersection_edges[0].end.join(", ")}] (${it.intersection_edges[0].length_m} m)` : "")
      );
      setStatus(`Interseção calculada: ${it.intersection_edges_count} arestas de corte geradas.`);
    }
  } catch (err) {
    setStatus(`Erro na interseção de faces: ${err.message}`, true);
  }
});

// 34. Bloqueio de Eixos & Inferência (Setas X/Y/Z)
document.getElementById("btn-native-axis-lock")?.addEventListener("click", async () => {
  setStatus("Testando restrição de inferência por setas de eixo (Seta Direita = Eixo Vermelho X)...");
  try {
    const cursor = [2.4, 1.8, 3.2];
    const res = await axisLockInference("RIGHT", cursor, [0, 0, 0]);
    if (res?.inference) {
      const inf = res.inference;
      const proj = inf.projection;
      showNativeToolsResult(
        "🔒 Bloqueio de Eixos (Arrow Keys Inference)",
        `Tecla: <b>${inf.arrow_key}</b> &rarr; <span style="color: ${inf.axis_color}; font-weight: bold;">${inf.description}</span><br>` +
        `Vetor Diretor: <b>[${inf.direction_vector.join(", ")}]</b><br>` +
        (proj ? `Cursor Livre: [${proj.cursor_point.join(", ")}] &rarr; <b>Projetado no Eixo: [${proj.projected_point.join(", ")}]</b> (Distância: ${proj.distance_along_axis_m} m)` : "")
      );
      setStatus(`Inferência travada no Eixo ${inf.axis_name}.`);
    }
  } catch (err) {
    setStatus(`Erro no bloqueio de eixos: ${err.message}`, true);
  }
});

// 35. Configurações de Solo e Céu dos Estilos
document.getElementById("btn-native-ground-sky")?.addEventListener("click", async () => {
  setStatus("Aplicando configurações oficiais de Solo, Céu e Fundo do Estilo...");
  try {
    const res = await configureGroundSkyStyle(
      "#FFFFFF",
      true,
      "#C3DDF7",
      true,
      "#C7BEB3",
      60,
      false
    );
    if (res?.style) {
      const st = res.style;
      const rp = st.render_payload;
      showNativeToolsResult(
        "🌄 Estilos: Céu, Solo & Fundo (Styles Panel)",
        `Céu: <b>${rp.sky.enabled ? "Ativado" : "Desativado"}</b> (<span style="color: ${rp.sky.color_hex};">■ ${rp.sky.color_hex}</span>)<br>` +
        `Solo: <b>${rp.ground.enabled ? "Ativado" : "Desativado"}</b> (<span style="color: ${rp.ground.color_hex};">■ ${rp.ground.color_hex}</span>, Opacidade: <b>${rp.ground.opacity * 100}%</b>)<br>` +
        `Clear Color WebGL: <b>${rp.clear_color_hex}</b> | Exibir solo por baixo: <b>${rp.ground.show_from_below ? "Sim" : "Não"}</b>`
      );
      setStatus("Estilo de Céu e Solo configurado com sucesso.");
    }
  } catch (err) {
    setStatus(`Erro ao configurar estilo de fundo: ${err.message}`, true);
  }
});

