// Motor de Inferência e Snapping do SketchUp para Three.js (Frente 22 Aprimorada)
//
// Implementa:
// 1. Snap a Vértices (Extremidade / Endpoint - Marcador Verde)
// 2. Snap a Fechamento de Polígono (Fechar Face - Ponto Verde preenchido)
// 3. Snap a Ponto Médio de Arestas (Midpoint - Marcador Ciano)
// 4. Snap a Arestas Existentes (On Edge - Marcador Quadrado Vermelho)
// 5. Snap a Faces e Superfícies 3D Existentes (On Face - Ponto na Malha)
// 6. Inferência de Eixos Cartesianos com Projeção 3D Exata:
//    - Eixo Vermelho: X do SketchUp/Three.js (#ff2222)
//    - Eixo Verde: Y do SketchUp (Z do Three.js #22aa22)
//    - Eixo Azul: Z do SketchUp (Y vertical do Three.js #2244ff) com plano vertical de projeção
// 7. Trava manual de eixo via Setas do teclado (Direita=Vermelho, Esquerda=Verde, Cima=Azul, Baixo=Livre)

import * as THREE from "three";

export class InferenceEngine {
  constructor(camera, scene, domElement) {
    this.camera = camera;
    this.scene = scene;
    this.domElement = domElement;

    this.snapRadiusPx = 14;
    this.axisThresholdRad = 0.087; // ~5 graus
    this.lockedAxis = null; // "red", "green", "blue" ou null

    this.verticesCache = [];
    this.midpointsCache = [];
    this.edgesCache = [];
    this.meshTargets = [];

    // Plano horizontal do chão (Z=0 no SketchUp / Y=0 no Three.js)
    this.groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

    // Helpers Visuais
    this._initVisualHelpers();
  }

  _initVisualHelpers() {
    this.helperGroup = new THREE.Group();
    this.helperGroup.name = "inference_helpers";

    // 1. Marcador de Snap (esfera iluminada com depthTest=false para ficar sempre visível)
    const snapGeom = new THREE.SphereGeometry(0.045, 12, 12);
    this.snapMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ff00,
      depthTest: false,
      transparent: true,
      opacity: 0.95,
    });
    this.snapMarker = new THREE.Mesh(snapGeom, this.snapMaterial);
    this.snapMarker.visible = false;
    this.snapMarker.renderOrder = 999;
    this.helperGroup.add(this.snapMarker);

    // 2. Linha Guia Tracejada do Eixo Inferido
    const guideGeom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-100, 0, 0),
      new THREE.Vector3(100, 0, 0),
    ]);
    this.guideMaterial = new THREE.LineDashedMaterial({
      color: 0xff0000,
      dashSize: 0.2,
      gapSize: 0.12,
      depthTest: false,
    });
    this.guideLine = new THREE.Line(guideGeom, this.guideMaterial);
    this.guideLine.computeLineDistances();
    this.guideLine.visible = false;
    this.guideLine.renderOrder = 998;
    this.helperGroup.add(this.guideLine);

    this.scene.add(this.helperGroup);
  }

  /**
   * Atualiza o índice espacial de vértices, pontos médios e arestas dos grupos da cena
   * @param {THREE.Group|Array<THREE.Group>} groups
   */
  updateGeometryIndex(groups) {
    this.verticesCache = [];
    this.midpointsCache = [];
    this.edgesCache = [];
    this.meshTargets = [];

    if (!groups) return;
    const groupList = Array.isArray(groups) ? groups : [groups];

    const tempV = new THREE.Vector3();
    const tempV2 = new THREE.Vector3();

    for (const group of groupList) {
      if (!group) continue;
      group.traverse((obj) => {
        // Coleta malhas para raycasting de faces (On Face)
        if (obj.isMesh && obj.visible) {
          this.meshTargets.push(obj);
        }

        // Processa malhas trianguladas
        if (obj.isMesh && obj.geometry) {
          const geom = obj.geometry;
          const posAttr = geom.getAttribute("position");
          if (!posAttr) return;

          obj.updateWorldMatrix(true, false);
          const matrixWorld = obj.matrixWorld;

          const objVerts = [];
          for (let i = 0; i < posAttr.count; i++) {
            tempV.fromBufferAttribute(posAttr, i).applyMatrix4(matrixWorld);
            const vClone = tempV.clone();
            this.verticesCache.push(vClone);
            objVerts.push(vClone);
          }

          // Arestas e pontos médios
          const indices = geom.index ? geom.index.array : null;
          if (indices) {
            for (let i = 0; i < indices.length; i += 3) {
              const i0 = indices[i];
              const i1 = indices[i + 1];
              const i2 = indices[i + 2];
              const pairs = [[i0, i1], [i1, i2], [i2, i0]];
              for (const [a, b] of pairs) {
                if (objVerts[a] && objVerts[b]) {
                  this.edgesCache.push({ p1: objVerts[a], p2: objVerts[b] });
                  this.midpointsCache.push(
                    new THREE.Vector3().addVectors(objVerts[a], objVerts[b]).multiplyScalar(0.5)
                  );
                }
              }
            }
          }
        }

        // Processa linhas desenhadas pelo usuário (Line / LineSegments)
        if (obj.isLine && obj.geometry) {
          const geom = obj.geometry;
          const posAttr = geom.getAttribute("position");
          if (!posAttr) return;

          obj.updateWorldMatrix(true, false);
          const matrixWorld = obj.matrixWorld;

          const lineVerts = [];
          for (let i = 0; i < posAttr.count; i++) {
            tempV.fromBufferAttribute(posAttr, i).applyMatrix4(matrixWorld);
            const vClone = tempV.clone();
            this.verticesCache.push(vClone);
            lineVerts.push(vClone);
          }

          for (let i = 0; i < lineVerts.length - 1; i++) {
            const p1 = lineVerts[i];
            const p2 = lineVerts[i + 1];
            this.edgesCache.push({ p1, p2 });
            this.midpointsCache.push(
              new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5)
            );
          }
        }
      });
    }
  }

  /**
   * Calcula o ponto inferido a partir do raycaster do mouse e ponto de partida opcional
   * @param {THREE.Raycaster} raycaster
   * @param {THREE.Vector3|null} startPoint
   * @param {MouseEvent} event
   * @param {THREE.Vector3|null} firstPoint (ponto inicial da cadeia de linhas para fechar face)
   * @returns {{ point: THREE.Vector3, type: string, label: string, color: number, isClosing: boolean }}
   */
  computeInference(raycaster, startPoint = null, event = null, firstPoint = null) {
    const rect = this.domElement.getBoundingClientRect();
    const mouseX = event ? event.clientX - rect.left : 0;
    const mouseY = event ? event.clientY - rect.top : 0;

    let bestPoint = null;
    let snapType = "none";
    let snapLabel = "";
    let snapColor = 0x000000;
    let minScreenDist = this.snapRadiusPx;
    let isClosing = false;

    // 1. Testa Snap ao Primeiro Ponto (Fechar Face / Extremidade Inicial)
    if (event && firstPoint && startPoint && firstPoint !== startPoint) {
      const screenPos = new THREE.Vector3();
      screenPos.copy(firstPoint).project(this.camera);
      if (screenPos.z <= 1.0) {
        const sx = ((screenPos.x + 1) * rect.width) / 2;
        const sy = ((-screenPos.y + 1) * rect.height) / 2;
        const dist = Math.hypot(mouseX - sx, mouseY - sy);
        if (dist < minScreenDist + 4) {
          minScreenDist = dist;
          bestPoint = firstPoint.clone();
          snapType = "endpoint";
          snapLabel = "Extremidade (Fechar Face)";
          snapColor = 0x00ff00;
          isClosing = true;
        }
      }
    }

    // 2. Testa Snap a Vértice Existente (Endpoint - Verde)
    if (!bestPoint && event && this.verticesCache.length) {
      const screenPos = new THREE.Vector3();
      for (const v of this.verticesCache) {
        screenPos.copy(v).project(this.camera);
        if (screenPos.z > 1.0) continue; // atrás da câmera

        const sx = ((screenPos.x + 1) * rect.width) / 2;
        const sy = ((-screenPos.y + 1) * rect.height) / 2;
        const dist = Math.hypot(mouseX - sx, mouseY - sy);

        if (dist < minScreenDist) {
          minScreenDist = dist;
          bestPoint = v.clone();
          snapType = "endpoint";
          snapLabel = "Extremidade";
          snapColor = 0x00ff00;
        }
      }
    }

    // 3. Testa Snap a Ponto Médio (Midpoint - Ciano)
    if (!bestPoint && event && this.midpointsCache.length) {
      const screenPos = new THREE.Vector3();
      for (const m of this.midpointsCache) {
        screenPos.copy(m).project(this.camera);
        if (screenPos.z > 1.0) continue;

        const sx = ((screenPos.x + 1) * rect.width) / 2;
        const sy = ((-screenPos.y + 1) * rect.height) / 2;
        const dist = Math.hypot(mouseX - sx, mouseY - sy);

        if (dist < minScreenDist) {
          minScreenDist = dist;
          bestPoint = m.clone();
          snapType = "midpoint";
          snapLabel = "Ponto médio";
          snapColor = 0x00ffff;
        }
      }
    }

    // 4. Testa Snap a Aresta (On Edge - Vermelho)
    if (!bestPoint && event && this.edgesCache.length) {
      const p1Screen = new THREE.Vector3();
      const p2Screen = new THREE.Vector3();

      for (const edge of this.edgesCache) {
        p1Screen.copy(edge.p1).project(this.camera);
        p2Screen.copy(edge.p2).project(this.camera);
        if (p1Screen.z > 1.0 && p2Screen.z > 1.0) continue;

        const sx1 = ((p1Screen.x + 1) * rect.width) / 2;
        const sy1 = ((-p1Screen.y + 1) * rect.height) / 2;
        const sx2 = ((p2Screen.x + 1) * rect.width) / 2;
        const sy2 = ((-p2Screen.y + 1) * rect.height) / 2;

        const lineLen = Math.hypot(sx2 - sx1, sy2 - sy1);
        if (lineLen < 1) continue;

        // Projeção paramétrica t na linha de tela
        const t = Math.max(0, Math.min(1, ((mouseX - sx1) * (sx2 - sx1) + (mouseY - sy1) * (sy2 - sy1)) / (lineLen * lineLen)));
        const projX = sx1 + t * (sx2 - sx1);
        const projY = sy1 + t * (sy2 - sy1);
        const dist = Math.hypot(mouseX - projX, mouseY - projY);

        if (dist < minScreenDist - 2) {
          minScreenDist = dist;
          bestPoint = new THREE.Vector3().lerpVectors(edge.p1, edge.p2, t);
          snapType = "edge";
          snapLabel = "Na aresta";
          snapColor = 0xdd2222;
        }
      }
    }

    // 5. Testa Snap a Superfície de Malha 3D Existente (On Face)
    if (!bestPoint && this.meshTargets.length) {
      const hits = raycaster.intersectObjects(this.meshTargets, false);
      if (hits.length > 0) {
        bestPoint = hits[0].point.clone();
        snapType = "face";
        snapLabel = "Na face";
        snapColor = 0x2b6cb0;
      }
    }

    // 6. Se não houver snap a objeto ou face, calcula ponto no chão horizontal
    if (!bestPoint) {
      const groundHit = new THREE.Vector3();
      if (raycaster.ray.intersectPlane(this.groundPlane, groundHit)) {
        bestPoint = groundHit;
        snapType = "ground";
        snapLabel = "No plano horizontal";
      } else {
        // Fallback: plano perpendicular à câmera
        const camDir = this.camera.getWorldDirection(new THREE.Vector3());
        const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(
          camDir.clone().negate(),
          this.camera.position.clone().add(camDir.clone().multiplyScalar(5))
        );
        bestPoint = new THREE.Vector3();
        raycaster.ray.intersectPlane(plane, bestPoint);
      }
    }

    // 7. Inferência Inteligente de Eixos Cartesianos com ponto de partida (Rubberband)
    if (startPoint && bestPoint && !isClosing) {
      const forcedAxis = this.lockedAxis;

      // Cria plano vertical passando por startPoint e voltado para a câmera para capturar altura Y (Eixo Azul)
      const camPos = this.camera.position;
      const normalH = new THREE.Vector3(camPos.x - startPoint.x, 0, camPos.z - startPoint.z).normalize();
      const verticalPlane = new THREE.Plane().setFromNormalAndCoplanarPoint(normalH, startPoint);
      const verticalHit = new THREE.Vector3();
      const hasVerticalHit = raycaster.ray.intersectPlane(verticalPlane, verticalHit);

      const delta = bestPoint.clone().sub(startPoint);
      const absX = Math.abs(delta.x);
      const absZ = Math.abs(delta.z); // Verde (Y do SketchUp)

      let verticalDy = 0;
      if (hasVerticalHit) {
        verticalDy = verticalHit.y - startPoint.y;
      }

      // Projeção na tela do deslocamento do mouse a partir do startPoint
      const startScreen = startPoint.clone().project(this.camera);
      const startSx = ((startScreen.x + 1) * rect.width) / 2;
      const startSy = ((-startScreen.y + 1) * rect.height) / 2;
      const screenDx = mouseX - startSx;
      const screenDy = mouseY - startSy;
      const isScreenVertical = Math.abs(screenDy) > 1.8 * Math.abs(screenDx) && Math.abs(screenDy) > 20;

      // 7.1 EIXO AZUL (Vertical - Z do SketchUp / Y do Three.js)
      if (forcedAxis === "blue" || (!forcedAxis && hasVerticalHit && (isScreenVertical || Math.abs(verticalDy) > Math.max(absX, absZ) * 1.5))) {
        bestPoint.x = startPoint.x;
        bestPoint.z = startPoint.z;
        bestPoint.y = hasVerticalHit ? verticalHit.y : bestPoint.y;
        snapType = "axis_blue";
        snapLabel = "No Eixo Azul (Vertical Z)";
        snapColor = 0x2244ff;
        this._showGuideLine(startPoint, new THREE.Vector3(0, 1, 0), snapColor);
      }
      // 7.2 EIXO VERMELHO (X do SketchUp / X do Three.js)
      else if (forcedAxis === "red" || (!forcedAxis && absX > 0.12 && absZ < 0.3 * absX)) {
        bestPoint.y = startPoint.y;
        bestPoint.z = startPoint.z;
        snapType = "axis_red";
        snapLabel = "No Eixo Vermelho (X)";
        snapColor = 0xff2222;
        this._showGuideLine(startPoint, new THREE.Vector3(1, 0, 0), snapColor);
      }
      // 7.3 EIXO VERDE (Y do SketchUp / Z do Three.js)
      else if (forcedAxis === "green" || (!forcedAxis && absZ > 0.12 && absX < 0.3 * absZ)) {
        bestPoint.x = startPoint.x;
        bestPoint.y = startPoint.y;
        snapType = "axis_green";
        snapLabel = "No Eixo Verde (Y)";
        snapColor = 0x22aa22;
        this._showGuideLine(startPoint, new THREE.Vector3(0, 0, 1), snapColor);
      } else {
        this.guideLine.visible = false;
      }
    } else {
      this.guideLine.visible = false;
    }

    // 8. Atualiza o Marcador Visual de Snap
    if (snapType === "endpoint" || snapType === "midpoint" || snapType === "edge") {
      this.snapMarker.position.copy(bestPoint);
      this.snapMaterial.color.setHex(snapColor);
      this.snapMarker.visible = true;
    } else {
      this.snapMarker.visible = false;
    }

    return {
      point: bestPoint,
      type: snapType,
      label: snapLabel,
      color: snapColor,
      isClosing: isClosing,
    };
  }

  _showGuideLine(origin, dir, color) {
    const pts = [
      origin.clone().addScaledVector(dir, -100),
      origin.clone().addScaledVector(dir, 100),
    ];
    this.guideLine.geometry.setFromPoints(pts);
    this.guideLine.computeLineDistances();
    this.guideMaterial.color.setHex(color);
    this.guideLine.visible = true;
  }

  hideHelpers() {
    this.snapMarker.visible = false;
    this.guideLine.visible = false;
  }

  setLockedAxis(axis) {
    this.lockedAxis = axis; // "red", "green", "blue" ou null
  }
}
