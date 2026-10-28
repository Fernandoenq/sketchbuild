// Converte o DTO do backend (definitions + instances, ver
// app/schemas/scene.py / core/mesh_extractor.py) em um THREE.Group
// pronto pra entrar na cena. Nenhuma chamada de rede aqui.

import * as THREE from "three";

// A SketchUpAPI.dll devolve coordenadas em POLEGADAS (unidade interna
// fixa do formato .skp, independente da unidade de exibicao do
// modelo). Convertido pra metros so na malha renderizada -- o DTO
// cru (API) continua em polegadas.
const INCHES_TO_METERS = 0.0254;

// O SketchUp usa Z como eixo vertical (convencao nativa do formato .skp
// -- vermelho=X, verde=Y, azul=Z=up), mas o Three.js usa Y como vertical.
// Essa conversao NUNCA foi feita neste pipeline (achado 27/10/2026,
// comparando com o SketchUp 2026 real rodando na maquina -- ver
// REVERSE_ENGINEERING_NOTES.md secao 25): tudo era renderizado deitado
// de lado. Rotacao fixa de -90 em torno de X remapeia Z-up -> Y-up
// preservando a regra da mao direita (sem espelhar/inverter normais):
// new_x=x, new_y=z, new_z=-y. So e preciso aplicar essa rotacao na
// matriz de MUNDO ja composta (a geometria local de cada definicao fica
// intocada) -- ver uso de `.premultiply()` abaixo.
const SKP_TO_THREE_UP = new THREE.Matrix4().makeRotationX(-Math.PI / 2);
// Inversa (R^-1 = R^T, ja que e uma rotacao pura) -- usada so no caminho
// de edicao/salvamento (meshMatrixToApiTransform), pra devolver a
// transformacao editada de volta pro sistema de eixos nativo do SketchUp
// antes de mandar pro backend.
const THREE_TO_SKP_UP = new THREE.Matrix4().makeRotationX(Math.PI / 2);

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

  // `face_ranges` (ver core/mesh_extractor.py / app/schemas/scene.py
  // FaceRangeDTO) mapeia intervalos de TRIANGULO (indice do Raycaster,
  // "faceIndex") de volta pro `face_id` real da SUFaceRef -- usado por
  // "Ferramentas > Pintura por face" (ver main.js handlePaintFaceClick()
  // e REVERSE_ENGINEERING_NOTES.md secao 28.19). Guardado na geometria
  // (nao no mesh) porque e uma propriedade da malha da DEFINICAO,
  // compartilhada entre todas as instancias dela.
  geometry.userData.faceRanges = definitionDTO.face_ranges || [];

  return geometry;
}

/**
 * Monta um THREE.Group a partir do DTO de /api/v1/scene/open.
 * Uma geometria por definicao (deduplicada), um Mesh por instancia
 * (aplicando a matriz de transformacao em espaco de mundo).
 */
// Material usado em TODAS as malhas da cena (uma unica instancia
// compartilhada) -- ver REVERSE_ENGINEERING_NOTES.md secao 27 ("Estilo de
// face"). Isso permite ao menu Visualizar mudar wireframe/opacidade/cor
// globalmente so mutando essas propriedades, sem precisar reconstruir a
// cena nem percorrer malha por malha.
const EDGE_LINE_MATERIAL = new THREE.LineBasicMaterial({ color: 0x2b2b2b });

export function buildSceneGroup(sceneDTO) {
  const group = new THREE.Group();
  group.name = sceneDTO.model_path;

  const geometriesByDefinitionId = new Map();
  const definitionsById = new Map();
  for (const definitionDTO of sceneDTO.definitions) {
    definitionsById.set(definitionDTO.definition_id, definitionDTO);
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
    world.premultiply(SKP_TO_THREE_UP);

    const mesh = new THREE.Mesh(geometry, material);
    mesh.name = instanceDTO.instance_id;
    mesh.castShadow = true;
    mesh.receiveShadow = true;

    // Overlay de arestas (Visualizar > Estilo de aresta > Bordas) -- filho
    // do mesh, entao herda a matriz dele (world ou billboard) automaticamente
    // sem logica extra. Comeca invisivel; main.js liga via setEdgesVisible().
    const edgesMesh = new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 25), EDGE_LINE_MATERIAL);
    edgesMesh.visible = false;
    edgesMesh.matrixAutoUpdate = false; // acompanha a matriz identidade local -- so o pai (mesh) se move
    mesh.add(edgesMesh);
    mesh.userData.edgesMesh = edgesMesh;

    const alwaysFacesCamera = definitionsById.get(instanceDTO.definition_id)?.always_faces_camera;
    if (alwaysFacesCamera) {
      // Componente "sempre de frente para a camera" (ex.: o personagem de
      // escala dos templates -- ver SUComponentDefinitionGetBehavior em
      // core/su_api.py). O SketchUp real reorienta esse componente em
      // tempo real (so o "yaw", eixo vertical) pra sempre encarar a
      // camera. Guardamos aqui a posicao/escala fixas (ja remapeadas) e o
      // pitch/roll originais (euler 'YXZ', componentes x/z) extraidos da
      // orientacao gravada no .skp -- so o componente Y (yaw) e
      // recalculado a cada frame em main.js (updateBillboards()). Zerar
      // pitch/roll (em vez de preserva-los) fazia a figura, que e uma
      // geometria plana/sem espessura, sumir de perfil em certas vistas
      // (ex.: vista Frontal com a camera alinhada ao eixo Z).
      world.decompose(position, quaternion, scale);
      mesh.position.copy(position);
      mesh.scale.copy(scale);
      mesh.matrixAutoUpdate = true;
      mesh.rotation.order = "YXZ";
      const baseEuler = new THREE.Euler().setFromQuaternion(quaternion, "YXZ");
      mesh.userData.billboard = true;
      mesh.userData.billboardPitch = baseEuler.x;
      mesh.userData.billboardRoll = baseEuler.z;
    } else {
      mesh.matrixAutoUpdate = false;
      mesh.matrix.copy(world);
    }

    group.add(mesh);
  }

  group.userData.sharedMaterial = material;
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
  const skpWorld = matrix.clone().premultiply(THREE_TO_SKP_UP);
  const position = new THREE.Vector3();
  const quaternion = new THREE.Quaternion();
  const scale = new THREE.Vector3();
  skpWorld.decompose(position, quaternion, scale);
  position.multiplyScalar(1 / INCHES_TO_METERS);
  return new THREE.Matrix4().compose(position, quaternion, scale).toArray();
}

/**
 * Converte um ponto em espaco de MUNDO do Three.js (metros, Y-up -- ex.:
 * um ponto clicado no viewport via Raycaster) pro espaco LOCAL da
 * definicao por tras de `mesh` (polegadas, convencao de eixo nativa do
 * .skp -- o MESMO espaco em que os vertices da geometria e os pontos de
 * `SUAxesCreateCustom` vivem). Usado por "Ferramentas > Eixos" (ver
 * REVERSE_ENGINEERING_NOTES.md secao 28.21): `mesh.matrix` ja e
 * `SKP_TO_THREE_UP @ worldTransformSkp` (ver buildSceneGroup acima), entao
 * invertê-la desfaz os dois passos de uma vez -- nao precisa aplicar
 * THREE_TO_SKP_UP separadamente como em meshMatrixToApiTransform (que
 * converte uma matriz de mundo inteira, nao um ponto relativo a UM mesh
 * especifico).
 */
export function worldPointToLocalInches(mesh, worldPoint) {
  const inverse = new THREE.Matrix4().copy(mesh.matrix).invert();
  const local = worldPoint.clone().applyMatrix4(inverse);
  local.multiplyScalar(1 / INCHES_TO_METERS);
  return [local.x, local.y, local.z];
}
