// Converte o DTO do backend (definitions + instances, ver
// app/schemas/scene.py / core/mesh_extractor.py) em um THREE.Group
// pronto pra entrar na cena. Nenhuma chamada de rede aqui.

import * as THREE from "three";

// A SketchUpAPI.dll devolve coordenadas em POLEGADAS (unidade interna
// fixa do formato .skp, independente da unidade de exibicao do
// modelo). Convertido pra metros so na malha renderizada -- o DTO
// cru (API) continua em polegadas.
const INCHES_TO_METERS = 0.0254;

function buildGeometry(definitionDTO) {
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(definitionDTO.vertices.length);
  for (let i = 0; i < definitionDTO.vertices.length; i++) {
    positions[i] = definitionDTO.vertices[i] * INCHES_TO_METERS;
  }
  geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));

  if (definitionDTO.normals && definitionDTO.normals.length === definitionDTO.vertices.length) {
    geometry.setAttribute(
      "normal",
      new THREE.BufferAttribute(new Float32Array(definitionDTO.normals), 3)
    );
  }

  geometry.setIndex(definitionDTO.indices);

  if (!definitionDTO.normals || !definitionDTO.normals.length) {
    geometry.computeVertexNormals();
  }

  return geometry;
}

/**
 * Monta um THREE.Group a partir do DTO de /api/v1/scene/open.
 * Uma geometria por definicao (deduplicada), um Mesh por instancia
 * (aplicando a matriz de transformacao em espaco de mundo).
 */
export function buildSceneGroup(sceneDTO) {
  const group = new THREE.Group();
  group.name = sceneDTO.model_path;

  const geometriesByDefinitionId = new Map();
  for (const definitionDTO of sceneDTO.definitions) {
    if (!definitionDTO.vertices.length) continue; // definicao sem geometria propria (ex.: "root")
    geometriesByDefinitionId.set(definitionDTO.definition_id, buildGeometry(definitionDTO));
  }

  const material = new THREE.MeshStandardMaterial({
    color: 0x8c99a6,
    side: THREE.DoubleSide,
    roughness: 0.85,
    metalness: 0.05,
  });

  for (const instanceDTO of sceneDTO.instances) {
    const geometry = geometriesByDefinitionId.get(instanceDTO.definition_id);
    if (!geometry) continue;

    // transform do backend esta em polegadas (translacao inclusa);
    // a geometria ja foi convertida pra metros, entao escalamos so a
    // translacao da matriz pra manter rotacao/escala intactas.
    const raw = new THREE.Matrix4().fromArray(instanceDTO.transform);
    const position = new THREE.Vector3();
    const quaternion = new THREE.Quaternion();
    const scale = new THREE.Vector3();
    raw.decompose(position, quaternion, scale);
    position.multiplyScalar(INCHES_TO_METERS);
    const world = new THREE.Matrix4().compose(position, quaternion, scale);

    const mesh = new THREE.Mesh(geometry, material);
    mesh.matrixAutoUpdate = false;
    mesh.matrix.copy(world);
    mesh.name = instanceDTO.instance_id;
    group.add(mesh);
  }

  return group;
}

/**
 * Inverso de parte da conversao feita em `buildSceneGroup`: recebe a
 * matriz de mundo de um mesh (em METROS, ja editada pelo gizmo) e
 * devolve o array de 16 floats no formato que a API espera (mesma
 * unidade do SDK -- POLEGADAS na translacao). Rotacao/escala nao mudam
 * de unidade, so a translacao precisa ser revertida.
 */
export function meshMatrixToApiTransform(matrix) {
  const position = new THREE.Vector3();
  const quaternion = new THREE.Quaternion();
  const scale = new THREE.Vector3();
  matrix.decompose(position, quaternion, scale);
  position.multiplyScalar(1 / INCHES_TO_METERS);
  return new THREE.Matrix4().compose(position, quaternion, scale).toArray();
}
