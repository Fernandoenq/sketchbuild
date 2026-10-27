import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { TransformControls } from "three/addons/controls/TransformControls.js";

import { openScene, updateInstanceTransform, saveScene, ApiError } from "./api.js";
import { buildSceneGroup, meshMatrixToApiTransform } from "./sceneBuilder.js";

const viewportEl = document.getElementById("viewport");
const pathInputEl = document.getElementById("path-input");
const openBtnEl = document.getElementById("open-btn");
const statusEl = document.getElementById("status");
const editPanelEl = document.getElementById("edit-panel");
const selectedLabelEl = document.getElementById("selected-label");
const modeBtnEls = document.querySelectorAll(".mode-btn");
const savePathInputEl = document.getElementById("save-path-input");
const saveBtnEl = document.getElementById("save-btn");

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x14161a);

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
viewportEl.appendChild(renderer.domElement);

const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;

const transformControls = new TransformControls(camera, renderer.domElement);
scene.add(transformControls.getHelper());

scene.add(new THREE.AmbientLight(0xffffff, 0.6));
const keyLight = new THREE.DirectionalLight(0xffffff, 1.2);
keyLight.position.set(5, 8, 5);
scene.add(keyLight);
const fillLight = new THREE.DirectionalLight(0xffffff, 0.4);
fillLight.position.set(-5, 2, -5);
scene.add(fillLight);

scene.add(new THREE.GridHelper(10, 20, 0x3a3f47, 0x242830));

let currentGroup = null;
let selectedMesh = null;
let suppressNextClick = false;

const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("error", isError);
}

function setMode(mode) {
  transformControls.setMode(mode);
  modeBtnEls.forEach((btn) => btn.classList.toggle("active", btn.dataset.mode === mode));
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
}

function deselectMesh() {
  if (!selectedMesh) return;
  transformControls.detach();
  selectedMesh = null;
  selectedLabelEl.textContent = "Nenhuma instancia selecionada.";
}

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
  if (hits.length) {
    selectMesh(hits[0].object);
  } else {
    deselectMesh();
  }
});

window.addEventListener("keydown", (event) => {
  const tag = event.target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA") return; // nao rouba atalho de quem esta digitando

  if (event.key === "w" || event.key === "W") setMode("translate");
  else if (event.key === "e" || event.key === "E") setMode("rotate");
  else if (event.key === "r" || event.key === "R") setMode("scale");
  else if (event.key === "Escape") deselectMesh();
});

modeBtnEls.forEach((btn) => {
  btn.addEventListener("click", () => setMode(btn.dataset.mode));
});
setMode("translate");

/** Centraliza a camera/controls na bounding box do grupo carregado. */
function frameCameraOn(group) {
  const box = new THREE.Box3().setFromObject(group);
  if (box.isEmpty()) return;

  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());
  const radius = Math.max(size.length() / 2, 0.1);

  controls.target.copy(center);
  const direction = new THREE.Vector3(1, 0.8, 1).normalize();
  camera.position.copy(center).addScaledVector(direction, radius * 2.2);
  camera.near = radius / 100;
  camera.far = radius * 100;
  camera.updateProjectionMatrix();
  controls.update();
}

async function handleOpen() {
  const path = pathInputEl.value.trim();
  if (!path) {
    setStatus("Informe um caminho de arquivo .skp.", true);
    return;
  }

  openBtnEl.disabled = true;
  deselectMesh();
  setStatus("Abrindo e extraindo malha...");

  try {
    const sceneDTO = await openScene(path);

    if (currentGroup) {
      scene.remove(currentGroup);
    }
    currentGroup = buildSceneGroup(sceneDTO);
    scene.add(currentGroup);
    frameCameraOn(currentGroup);
    editPanelEl.classList.remove("hidden");

    const totalVertices = sceneDTO.definitions.reduce(
      (acc, d) => acc + d.vertices.length / 3,
      0
    );
    const totalTriangles = sceneDTO.definitions.reduce(
      (acc, d) => acc + d.indices.length / 3,
      0
    );
    setStatus(
      `OK -- ${sceneDTO.definitions.length} definicoes, ${sceneDTO.instances.length} ` +
        `instancias, ${totalVertices} vertices, ${totalTriangles} triangulos.`
    );
  } catch (err) {
    const detail = err instanceof ApiError ? err.message : String(err);
    setStatus(`Erro: ${detail}`, true);
  } finally {
    openBtnEl.disabled = false;
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

openBtnEl.addEventListener("click", handleOpen);
pathInputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter") handleOpen();
});
saveBtnEl.addEventListener("click", handleSave);

window.addEventListener("resize", () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
});

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}
animate();
