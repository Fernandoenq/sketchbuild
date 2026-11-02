// Motor de Inferência e Snapping Oficial do SketchUp Classic para Three.js
//
// Implementa com fidelidade matemática e visual absoluta:
// 1. Cursor de precisão com Tooltip flutuante clássico ("No Eixo Vermelho", "Extremidade", etc.)
// 2. Snap a Vértices (Extremidade / Endpoint - Quadradinho verde 2D)
// 3. Snap a Ponto Médio de Arestas (Midpoint - Bolinha ciano 2D)
// 4. Snap a Arestas Existentes (On Edge - Quadradinho vermelho 2D)
// 5. Snap a Faces Existentes (On Face)
// 6. Inferência de Eixos em Espaço de Tela 2D (Screen-Space 1:1 Pixel Tracking):
//    - Vermelho (X): Y e Z rigorosamente travados (a linha move-se exclusivamente para os lados)
//    - Verde (Y SketchUp / Z Three.js): X e Y rigorosamente travados (profundidade pura)
//    - Azul (Z SketchUp / Y vertical Three.js): X e Z rigorosamente travados (altura pura)
//    - A velocidade de estiramento da linha segue 1:1 o movimento do cursor na tela (sem disparar para o infinito)
// 7. Plano de Trabalho Confortável para movimento livre (fora dos eixos):
//    - Mantém coplanaridade perfeita com o plano horizontal do ponto de início (Y = start.y)
// 8. Sem linhas tracejadas invasivas nem esferas 3D flutuantes no vazio

import * as THREE from "three";

export class InferenceEngine {
  constructor(camera, scene, domElement) {
    this.camera = camera;
    this.scene = scene;
    this.domElement = domElement;

    this.snapRadiusPx = 14;
    this.lockedAxis = null; // "red", "green", "blue" ou null
    this.lastInferredAxis = null;

    this.verticesCache = [];
    this.midpointsCache = [];
    this.edgesCache = [];
    this.meshTargets = [];

    // Plano horizontal do chão (Z=0 no SketchUp / Y=0 no Three.js)
    this.groundPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

    // Helpers Visuais Limpos (Apenas o marcador pontual 2D de snap real)
    this._initVisualHelpers();
  }

  _initVisualHelpers() {
    this.helperGroup = new THREE.Group();
    this.helperGroup.name = "inference_helpers";

    // Marcador pontual compacto (só aparece quando faz snap real a vértice, aresta ou ponto médio)
    const markerGeom = new THREE.BufferGeometry();
    // Pequeno quadrado plano de 0.05m voltado para a câmera
    const size = 0.025;
    const vertices = new Float32Array([
      -size, -size, 0,
       size, -size, 0,
       size,  size, 0,
      -size, -size, 0,
       size,  size, 0,
      -size,  size, 0,
    ]);
    markerGeom.setAttribute("position", new THREE.BufferAttribute(vertices, 3));

    this.snapMaterial = new THREE.MeshBasicMaterial({
      color: 0x00ff00,
      depthTest: false,
      transparent: true,
      opacity: 0.95,
      side: THREE.DoubleSide,
    });
    this.snapMarker = new THREE.Mesh(markerGeom, this.snapMaterial);
    this.snapMarker.visible = false;
    this.snapMarker.renderOrder = 9999;
    this.helperGroup.add(this.snapMarker);

    this.scene.add(this.helperGroup);
  }

  /**
   * Atualiza o índice espacial de geometria (apenas vértices e arestas reais)
   */
  updateGeometryIndex(groups) {
    this.verticesCache = [];
    this.midpointsCache = [];
    this.edgesCache = [];
    this.meshTargets = [];

    if (!groups) return;
    const groupList = Array.isArray(groups) ? groups : [groups];

    const tempV = new THREE.Vector3();

    for (const group of groupList) {
      if (!group) continue;
      group.traverse((obj) => {
        // Ignora os próprios helpers visuais de inferência
        if (obj === this.helperGroup || obj === this.snapMarker) return;

        // Coleta malhas para raycasting de faces (On Face)
        if (obj.isMesh && obj.visible && obj.geometry && obj.name !== "user_drawings_dot") {
          this.meshTargets.push(obj);

          const geom = obj.geometry;
          const posAttr = geom.getAttribute("position");
          if (!posAttr) return;

          obj.updateWorldMatrix(true, false);
          const matrixWorld = obj.matrixWorld;

          // Processa faces e arestas de malhas B-Rep / importadas
          const objVerts = [];
          for (let i = 0; i < posAttr.count; i++) {
            tempV.fromBufferAttribute(posAttr, i).applyMatrix4(matrixWorld);
            const vClone = tempV.clone();
            this.verticesCache.push(vClone);
            objVerts.push(vClone);
          }

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

        // Processa arestas desenhadas pelo usuário (Line / LineSegments puras)
        if (obj.isLine && obj.visible && obj.geometry && obj.name !== "rubberband_line") {
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
   * Converte coordenadas 3D para pixels (x, y) na tela
   */
  _projectToScreen(worldPos, rect) {
    const p = worldPos.clone().project(this.camera);
    return {
      x: ((p.x + 1) * rect.width) / 2,
      y: ((-p.y + 1) * rect.height) / 2,
      inFront: p.z <= 1.0,
      rawZ: p.z,
    };
  }

  /**
   * Calcula a inferência de ponto de desenho idêntica ao SketchUp Desktop
   */
  computeInference(raycaster, startPoint = null, event = null, firstPoint = null) {
    const rect = this.domElement.getBoundingClientRect();
    const mouseX = event ? event.clientX - rect.left : rect.width / 2;
    const mouseY = event ? event.clientY - rect.top : rect.height / 2;

    let bestPoint = null;
    let snapType = "none";
    let snapLabel = "";
    let snapColor = 0x111111;
    let minScreenDist = this.snapRadiusPx;
    let isClosing = false;

    // ------------------------------------------------------------------------
    // FASE 1: Snaps em Geometria Existente (Prioridade Máxima)
    // ------------------------------------------------------------------------

    // 1.1 Fechar Face com o Primeiro Ponto
    if (event && firstPoint && startPoint && firstPoint !== startPoint) {
      const sPos = this._projectToScreen(firstPoint, rect);
      if (sPos.inFront) {
        const dist = Math.hypot(mouseX - sPos.x, mouseY - sPos.y);
        if (dist < minScreenDist + 6) {
          minScreenDist = dist;
          bestPoint = firstPoint.clone();
          snapType = "endpoint";
          snapLabel = "Extremidade";
          snapColor = 0x00aa00;
          isClosing = true;
        }
      }
    }

    // 1.2 Extremidade (Endpoint - Verde)
    if (!bestPoint && event && this.verticesCache.length) {
      for (const v of this.verticesCache) {
        const sPos = this._projectToScreen(v, rect);
        if (!sPos.inFront) continue;

        const dist = Math.hypot(mouseX - sPos.x, mouseY - sPos.y);
        if (dist < minScreenDist) {
          minScreenDist = dist;
          bestPoint = v.clone();
          snapType = "endpoint";
          snapLabel = "Extremidade";
          snapColor = 0x00aa00;
        }
      }
    }

    // 1.3 Ponto Médio (Midpoint - Ciano)
    if (!bestPoint && event && this.midpointsCache.length) {
      for (const m of this.midpointsCache) {
        const sPos = this._projectToScreen(m, rect);
        if (!sPos.inFront) continue;

        const dist = Math.hypot(mouseX - sPos.x, mouseY - sPos.y);
        if (dist < minScreenDist) {
          minScreenDist = dist;
          bestPoint = m.clone();
          snapType = "midpoint";
          snapLabel = "Ponto médio";
          snapColor = 0x00cccc;
        }
      }
    }

    // 1.4 Na Aresta (On Edge - Vermelho)
    if (!bestPoint && event && this.edgesCache.length) {
      for (const edge of this.edgesCache) {
        const s1 = this._projectToScreen(edge.p1, rect);
        const s2 = this._projectToScreen(edge.p2, rect);
        if (!s1.inFront && !s2.inFront) continue;

        const lineLen = Math.hypot(s2.x - s1.x, s2.y - s1.y);
        if (lineLen < 2) continue;

        const t = Math.max(0, Math.min(1, ((mouseX - s1.x) * (s2.x - s1.x) + (mouseY - s1.y) * (s2.y - s1.y)) / (lineLen * lineLen)));
        const projX = s1.x + t * (s2.x - s1.x);
        const projY = s1.y + t * (s2.y - s1.y);
        const dist = Math.hypot(mouseX - projX, mouseY - projY);

        if (dist < minScreenDist - 2) {
          minScreenDist = dist;
          bestPoint = new THREE.Vector3().lerpVectors(edge.p1, edge.p2, t);
          snapType = "edge";
          snapLabel = "Na aresta";
          snapColor = 0xcc2222;
        }
      }
    }

    // 1.5 Na Face (On Face)
    if (!bestPoint && this.meshTargets.length) {
      const hits = raycaster.intersectObjects(this.meshTargets, false);
      if (hits.length > 0) {
        bestPoint = hits[0].point.clone();
        snapType = "face";
        snapLabel = "Na face";
        snapColor = 0x2244aa;
      }
    }

    // ------------------------------------------------------------------------
    // FASE 2: Inferência de Eixos Cartesianos 1:1 com Movimento do Mouse
    // ------------------------------------------------------------------------
    if (startPoint && !isClosing && (!bestPoint || snapType === "face")) {
      const sStart = this._projectToScreen(startPoint, rect);

      // Definição dos 3 eixos do SketchUp no Three.js:
      // Red: X (+X e -X) -> #ff2222
      // Green: Y do SketchUp (+Z e -Z do Three.js) -> #22aa22
      // Blue: Z do SketchUp (+Y e -Y vertical do Three.js) -> #2244ff
      const axes = [
        {
          id: "red",
          dir: new THREE.Vector3(1, 0, 0),
          label: "No Eixo Vermelho",
          color: 0xee2222,
        },
        {
          id: "green",
          dir: new THREE.Vector3(0, 0, 1),
          label: "No Eixo Verde",
          color: 0x22aa22,
        },
        {
          id: "blue",
          dir: new THREE.Vector3(0, 1, 0),
          label: "No Eixo Azul",
          color: 0x2244ee,
        },
      ];

      // Vetor 2D do mouse a partir do startPoint na tela
      const mouseVec = new THREE.Vector2(mouseX - sStart.x, mouseY - sStart.y);
      const mouseDistPx = mouseVec.length();

      let activeLockedAxis = this.lockedAxis;
      if (!activeLockedAxis && event && event.shiftKey && this.lastInferredAxis) {
        activeLockedAxis = this.lastInferredAxis;
      }

      let chosenAxis = null;
      let axisProjectionT = 0;

      for (const axis of axes) {
        // Projeta 1 metro ao longo do eixo na tela para calcular vetor e escala
        const testPt = startPoint.clone().addScaledVector(axis.dir, 1.0);
        const sTest = this._projectToScreen(testPt, rect);
        const axisVec = new THREE.Vector2(sTest.x - sStart.x, sTest.y - sStart.y);
        const pxPerMeter = axisVec.length();

        if (pxPerMeter < 1.0) continue; // Câmera olhando exatamente ao longo do eixo

        const axisUnit = axisVec.clone().normalize();
        // Projeção escalar do mouse ao longo do eixo na tela
        const projScreenPx = mouseVec.dot(axisUnit);
        // Distância perpendicular do mouse ao eixo na tela
        const perpDistPx = Math.abs(mouseVec.x * axisUnit.y - mouseVec.y * axisUnit.x);

        // Se o usuário travou o eixo via seta/shift OU o cursor estiver dentro da tolerância de ~16 graus
        const isLocked = activeLockedAxis === axis.id;
        const isMagnetic = perpDistPx < 22 && mouseDistPx > 16 && Math.abs(projScreenPx) > mouseDistPx * 0.92;

        if (isLocked || (!activeLockedAxis && isMagnetic)) {
          chosenAxis = axis;
          // Distância no espaço 3D calculada 1:1 a partir dos pixels da tela!
          axisProjectionT = projScreenPx / pxPerMeter;
          break;
        }
      }

      if (chosenAxis) {
        // Posição 3D rigorosamente travada no eixo
        const pt = startPoint.clone().addScaledVector(chosenAxis.dir, axisProjectionT);

        // Limpeza analítica de coordenadas (zero desvio)
        if (chosenAxis.id === "red") {
          pt.y = startPoint.y;
          pt.z = startPoint.z;
        } else if (chosenAxis.id === "green") {
          pt.x = startPoint.x;
          pt.y = startPoint.y;
        } else if (chosenAxis.id === "blue") {
          pt.x = startPoint.x;
          pt.z = startPoint.z;
        }

        bestPoint = pt;
        snapType = `axis_${chosenAxis.id}`;
        snapLabel = chosenAxis.label;
        snapColor = chosenAxis.color;
        this.lastInferredAxis = chosenAxis.id;
      } else {
        if (!activeLockedAxis) this.lastInferredAxis = null;
      }
    }

    // ------------------------------------------------------------------------
    // FASE 3: Desenho Livre Fora dos Eixos (Plano de Visão / Plano do Ponto)
    // ------------------------------------------------------------------------
    if (!bestPoint) {
      if (startPoint) {
        // Desenho livre quando já há um ponto:
        // Projeta no plano horizontal na altura de startPoint (Y = startPoint.y)
        const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -startPoint.y);
        const hit = new THREE.Vector3();
        if (raycaster.ray.intersectPlane(plane, hit)) {
          // Se a interseção for razoavelmente próxima da câmera (< 80 metros):
          if (hit.distanceTo(this.camera.position) < 80) {
            bestPoint = hit;
            bestPoint.y = startPoint.y;
            snapType = "horizontal_plane";
            snapLabel = "";
          }
        }

        // Se olhar quase paralelo ao chão, projeta no plano perpendicular à câmera passando por startPoint
        if (!bestPoint) {
          const camDir = this.camera.getWorldDirection(new THREE.Vector3());
          const viewPlane = new THREE.Plane().setFromNormalAndCoplanarPoint(camDir.clone().negate(), startPoint);
          bestPoint = new THREE.Vector3();
          raycaster.ray.intersectPlane(viewPlane, bestPoint);
          snapType = "view_plane";
          snapLabel = "";
        }
      } else {
        // Primeiro clique no vazio: intersecta o chão horizontal do mundo (Y=0)
        const hit = new THREE.Vector3();
        if (raycaster.ray.intersectPlane(this.groundPlane, hit)) {
          bestPoint = hit;
          bestPoint.y = 0;
          snapType = "ground";
          snapLabel = "";
        } else {
          const camDir = this.camera.getWorldDirection(new THREE.Vector3());
          const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(
            camDir.clone().negate(),
            this.camera.position.clone().add(camDir.clone().multiplyScalar(5))
          );
          bestPoint = new THREE.Vector3();
          raycaster.ray.intersectPlane(plane, bestPoint);
          snapType = "space";
          snapLabel = "";
        }
      }
      snapColor = 0x111111;
    }

    // ------------------------------------------------------------------------
    // FASE 4: Marcador Visual de Snap (Apenas para vértices, pontos médios e arestas)
    // ------------------------------------------------------------------------
    if (snapType === "endpoint" || snapType === "midpoint" || snapType === "edge") {
      this.snapMarker.position.copy(bestPoint);
      // Alinha o marcador com a câmera para ficar plano na tela
      this.snapMarker.quaternion.copy(this.camera.quaternion);
      // Escala o marcador proporcionalmente à distância da câmera para manter tamanho em pixels
      const distToCam = this.camera.position.distanceTo(bestPoint);
      const markerScale = Math.max(0.2, distToCam * 0.025);
      this.snapMarker.scale.set(markerScale, markerScale, markerScale);
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
      screenPos: { x: mouseX, y: mouseY },
    };
  }

  hideHelpers() {
    this.snapMarker.visible = false;
  }

  setLockedAxis(axis) {
    this.lockedAxis = axis; // "red", "green", "blue" ou null
  }
}
