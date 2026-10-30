// Motor de Inferência e Snapping do SketchUp para Three.js (Frente 22)
//
// Implementa:
// 1. Snap a Vértices (Extremidade / Endpoint - Marcador Verde)
// 2. Snap a Ponto Médio (Midpoint - Marcador Ciano)
// 3. Inferência de Eixos Cartesianos com Trava Automática e Linhas Guia:
//    - Eixo Vermelho: X (Vermelho #ff2222)
//    - Eixo Verde: Y do SketchUp (Z do Three.js #22aa22)
//    - Eixo Azul: Z do SketchUp (Y do Three.js #2244ff)
// 4. Trava manual de eixo via Setas do teclado ou tecla Shift

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

    // Plano horizontal do chão (Z=0 no SketchUp / Y=0 no Three.js)
    this.groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

    // Helpers Visuais
    this._initVisualHelpers();
  }

  _initVisualHelpers() {
    this.helperGroup = new THREE.Group();
    this.helperGroup.name = "inference_helpers";

    // 1. Marcador de Snap (ponto pontual iluminado)
    const snapGeom = new THREE.SphereGeometry(0.04, 8, 8);
    this.snapMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ff00,
      depthTest: false,
      transparent: true,
      opacity: 0.9,
    });
    this.snapMarker = new THREE.Mesh(snapGeom, this.snapMaterial);
    this.snapMarker.visible = false;
    this.helperGroup.add(this.snapMarker);

    // 2. Linha Guia Tracejada do Eixo Inferido
    const guideGeom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-100, 0, 0),
      new THREE.Vector3(100, 0, 0),
    ]);
    this.guideMaterial = new THREE.LineDashedMaterial({
      color: 0xff0000,
      dashSize: 0.15,
      gapSize: 0.1,
      depthTest: false,
    });
    this.guideLine = new THREE.Line(guideGeom, this.guideMaterial);
    this.guideLine.computeLineDistances();
    this.guideLine.visible = false;
    this.helperGroup.add(this.guideLine);

    this.scene.add(this.helperGroup);
  }

  /** Atualiza o índice espacial de vértices e pontos médios do modelo */
  updateGeometryIndex(group) {
    this.verticesCache = [];
    this.midpointsCache = [];
    if (!group) return;

    const tempV = new THREE.Vector3();
    const tempV2 = new THREE.Vector3();

    group.traverse((obj) => {
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

        // Pontos médios dos triângulos/arestas
        const indices = geom.index ? geom.index.array : null;
        if (indices) {
          for (let i = 0; i < indices.length; i += 3) {
            const i0 = indices[i];
            const i1 = indices[i + 1];
            const i2 = indices[i + 2];
            if (objVerts[i0] && objVerts[i1]) {
              this.midpointsCache.push(new THREE.Vector3().addVectors(objVerts[i0], objVerts[i1]).multiplyScalar(0.5));
            }
            if (objVerts[i1] && objVerts[i2]) {
              this.midpointsCache.push(new THREE.Vector3().addVectors(objVerts[i1], objVerts[i2]).multiplyScalar(0.5));
            }
            if (objVerts[i2] && objVerts[i0]) {
              this.midpointsCache.push(new THREE.Vector3().addVectors(objVerts[i2], objVerts[i0]).multiplyScalar(0.5));
            }
          }
        }
      }
    });
  }

  /**
   * Calcula o ponto inferido a partir do raycaster do mouse e ponto de partida opcional
   * @param {THREE.Raycaster} raycaster
   * @param {THREE.Vector3|null} startPoint
   * @param {MouseEvent} event
   * @returns {{ point: THREE.Vector3, type: string, label: string, color: number }}
   */
  computeInference(raycaster, startPoint = null, event = null) {
    const rect = this.domElement.getBoundingClientRect();
    const mouseX = event ? event.clientX - rect.left : 0;
    const mouseY = event ? event.clientY - rect.top : 0;

    let bestPoint = null;
    let snapType = "none";
    let snapLabel = "";
    let snapColor = 0x000000;
    let minScreenDist = this.snapRadiusPx;

    // 1. Testa Snap a Vértice Existente (Endpoint - Verde)
    if (event && this.verticesCache.length) {
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

    // 2. Testa Snap a Ponto Médio (Midpoint - Ciano)
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

    // 3. Se não houver snap a vértice/aresta, calcula ponto no chão horizontal
    if (!bestPoint) {
      const groundHit = new THREE.Vector3();
      if (raycaster.ray.intersectPlane(this.groundPlane, groundHit)) {
        bestPoint = groundHit;
        snapType = "ground";
        snapLabel = "No plano";
      } else {
        // Fallback: plano perpendicular à câmera a 5 metros
        const camDir = this.camera.getWorldDirection(new THREE.Vector3());
        const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(
          camDir.negate(),
          this.camera.position.clone().add(camDir.multiplyScalar(5))
        );
        raycaster.ray.intersectPlane(plane, bestPoint);
      }
    }

    // 4. Inferência de Eixos Cartesianos com ponto de partida (Rubberband)
    if (startPoint && bestPoint) {
      const delta = bestPoint.clone().sub(startPoint);
      const absX = Math.abs(delta.x);
      const absY = Math.abs(delta.y);
      const absZ = Math.abs(delta.z);

      const forcedAxis = this.lockedAxis;

      // Eixo Vermelho: X do SketchUp/Three.js
      if (forcedAxis === "red" || (!forcedAxis && absX > 0.1 && absY < 0.25 && absZ < 0.25)) {
        bestPoint.y = startPoint.y;
        bestPoint.z = startPoint.z;
        snapType = "axis_red";
        snapLabel = "No Eixo Vermelho";
        snapColor = 0xff2222;
        this._showGuideLine(startPoint, new THREE.Vector3(1, 0, 0), snapColor);
      }
      // Eixo Verde: Y do SketchUp (Z do Three.js)
      else if (forcedAxis === "green" || (!forcedAxis && absZ > 0.1 && absX < 0.25 && absY < 0.25)) {
        bestPoint.x = startPoint.x;
        bestPoint.y = startPoint.y;
        snapType = "axis_green";
        snapLabel = "No Eixo Verde";
        snapColor = 0x22aa22;
        this._showGuideLine(startPoint, new THREE.Vector3(0, 0, 1), snapColor);
      }
      // Eixo Azul: Z do SketchUp (Y vertical do Three.js)
      else if (forcedAxis === "blue" || (!forcedAxis && absY > 0.1 && absX < 0.25 && absZ < 0.25)) {
        bestPoint.x = startPoint.x;
        bestPoint.z = startPoint.z;
        snapType = "axis_blue";
        snapLabel = "No Eixo Azul";
        snapColor = 0x2244ff;
        this._showGuideLine(startPoint, new THREE.Vector3(0, 1, 0), snapColor);
      } else {
        this.guideLine.visible = false;
      }
    } else {
      this.guideLine.visible = false;
    }

    // 5. Atualiza o Marcador Visual de Snap
    if (snapType === "endpoint" || snapType === "midpoint") {
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
