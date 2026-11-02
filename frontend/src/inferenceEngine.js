// Motor de Inferência e Snapping do SketchUp para Three.js (Frente 22 - Fidelidade Matemática)
//
// Implementa a arquitetura de inferência exata do SketchUp Desktop Classic:
// 1. Snap a Vértices (Extremidade / Endpoint - Marcador Verde)
// 2. Snap a Fechamento de Polígono (Fechar Face - Ponto Verde preenchido com prioridade)
// 3. Snap a Ponto Médio de Arestas (Midpoint - Marcador Ciano)
// 4. Snap a Arestas Existentes (On Edge - Marcador Quadrado Vermelho)
// 5. Snap a Faces e Superfícies 3D Existentes (On Face - Ponto na Malha)
// 6. Inferência de Eixos em Espaço de Tela 2D (Screen-Space Angular Tolerance):
//    - Compara o vetor 2D do cursor com as projeções em tela dos 3 eixos cartesianos
//    - Eixo Vermelho: X (#ff2222) -> Trava Y e Z absolutos (a linha só vai para o lado!)
//    - Eixo Verde: Y do SketchUp / Z do Three.js (#22aa22) -> Trava X e Y absolutos
//    - Eixo Azul: Z do SketchUp / Y vertical do Three.js (#2244ff) -> Trava X e Z absolutos
//    - Projeção 3D calculada via menor distância entre o raio da câmera e a reta 3D do eixo
// 7. Plano de Trabalho Ativo (Active Working Plane) para movimento livre:
//    - Plano horizontal passando por startPoint (Y = startPoint.y), impedindo deriva para o infinito
// 8. Trava manual de eixo via Setas do teclado ou tecla Shift:
//    - Direita: Eixo Vermelho (X)
//    - Esquerda: Eixo Verde (Y SketchUp / Z Three.js)
//    - Cima: Eixo Azul (Z SketchUp / Y vertical)
//    - Baixo: Livre

import * as THREE from "three";

/**
 * Calcula o ponto mais próximo entre uma reta 3D e o raio da câmera
 * Reta: P(t) = lineOrigin + t * lineDir (lineDir normalizado)
 * Raio: R(s) = rayOrigin + s * rayDir (rayDir normalizado)
 */
function closestPointOnLineToRay(lineOrigin, lineDir, rayOrigin, rayDir) {
  const w0 = new THREE.Vector3().subVectors(lineOrigin, rayOrigin);
  const u = lineDir;
  const v = rayDir;
  const b = u.dot(v);
  const d = u.dot(w0);
  const e = v.dot(w0);
  const denom = 1.0 - b * b;

  if (Math.abs(denom) < 1e-6) {
    return lineOrigin.clone();
  }

  const t = (b * e - d) / denom;
  return new THREE.Vector3().copy(lineOrigin).addScaledVector(lineDir, t);
}

export class InferenceEngine {
  constructor(camera, scene, domElement) {
    this.camera = camera;
    this.scene = scene;
    this.domElement = domElement;

    this.snapRadiusPx = 14;
    this.lockedAxis = null; // "red", "green", "blue" ou null
    this.lastInferredAxis = null; // Mantém histórico para trava via Shift

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

    // 1. Marcador de Snap (esfera com depthTest=false para ficar sempre visível em cima do modelo)
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

    // 2. Linha Guia Tracejada Infinita do Eixo Inferido
    const guideGeom = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(-500, 0, 0),
      new THREE.Vector3(500, 0, 0),
    ]);
    this.guideMaterial = new THREE.LineDashedMaterial({
      color: 0xff0000,
      dashSize: 0.25,
      gapSize: 0.15,
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

    for (const group of groupList) {
      if (!group) continue;
      group.traverse((obj) => {
        // Coleta malhas para raycasting de faces (On Face)
        if (obj.isMesh && obj.visible && obj.geometry) {
          this.meshTargets.push(obj);

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
        if (obj.isLine && obj.visible && obj.geometry) {
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
   * Converte coordenadas 3D de mundo para pixels (x, y) na tela
   * @param {THREE.Vector3} worldPos
   * @param {DOMRect} rect
   * @returns {{x: number, y: number, inFront: boolean}}
   */
  _projectToScreen(worldPos, rect) {
    const p = worldPos.clone().project(this.camera);
    return {
      x: ((p.x + 1) * rect.width) / 2,
      y: ((-p.y + 1) * rect.height) / 2,
      inFront: p.z <= 1.0,
    };
  }

  /**
   * Calcula o ponto inferido a partir do raycaster do mouse e ponto de partida opcional
   * @param {THREE.Raycaster} raycaster
   * @param {THREE.Vector3|null} startPoint
   * @param {MouseEvent|PointerEvent|null} event
   * @param {THREE.Vector3|null} firstPoint (ponto inicial da cadeia de linhas para fechar face)
   * @returns {{ point: THREE.Vector3, type: string, label: string, color: number, isClosing: boolean }}
   */
  computeInference(raycaster, startPoint = null, event = null, firstPoint = null) {
    const rect = this.domElement.getBoundingClientRect();
    const mouseX = event ? event.clientX - rect.left : rect.width / 2;
    const mouseY = event ? event.clientY - rect.top : rect.height / 2;

    let bestPoint = null;
    let snapType = "none";
    let snapLabel = "";
    let snapColor = 0x222222;
    let minScreenDist = this.snapRadiusPx;
    let isClosing = false;

    // ------------------------------------------------------------------------
    // FASE 1: Snaps em Geometria Física Existente (Prioridade Máxima)
    // ------------------------------------------------------------------------

    // 1.1 Snap ao Primeiro Ponto (Fechar Face)
    if (event && firstPoint && startPoint && firstPoint !== startPoint) {
      const sPos = this._projectToScreen(firstPoint, rect);
      if (sPos.inFront) {
        const dist = Math.hypot(mouseX - sPos.x, mouseY - sPos.y);
        if (dist < minScreenDist + 6) {
          minScreenDist = dist;
          bestPoint = firstPoint.clone();
          snapType = "endpoint";
          snapLabel = "Extremidade (Fechar Face)";
          snapColor = 0x00ff00;
          isClosing = true;
        }
      }
    }

    // 1.2 Snap a Vértice Existente (Endpoint - Verde)
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
          snapColor = 0x00ff00;
        }
      }
    }

    // 1.3 Snap a Ponto Médio (Midpoint - Ciano)
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
          snapColor = 0x00ffff;
        }
      }
    }

    // 1.4 Snap a Aresta (On Edge - Vermelho)
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
          snapColor = 0xdd2222;
        }
      }
    }

    // 1.5 Snap a Superfície de Malha 3D Existente (On Face)
    if (!bestPoint && this.meshTargets.length) {
      const hits = raycaster.intersectObjects(this.meshTargets, false);
      if (hits.length > 0) {
        bestPoint = hits[0].point.clone();
        snapType = "face";
        snapLabel = "Na face";
        snapColor = 0x2b6cb0;
      }
    }

    // ------------------------------------------------------------------------
    // FASE 2: Inferência de Eixos em Espaço de Tela 2D (Canônica do SketchUp)
    // ------------------------------------------------------------------------
    // Se o usuário já definiu o ponto inicial (Rubberband ativo) e não fechou polígono:
    if (startPoint && !isClosing) {
      // Determina se há eixo travado manualmente (Setas ou Shift)
      let activeLockedAxis = this.lockedAxis;
      if (!activeLockedAxis && event && event.shiftKey && this.lastInferredAxis) {
        activeLockedAxis = this.lastInferredAxis;
      }

      // Projeta o startPoint na tela 2D
      const sStart = this._projectToScreen(startPoint, rect);

      // Definição dos 3 eixos cartesianos:
      // Red: X do SketchUp / X do Three.js (#ff2222)
      // Green: Y do SketchUp / Z do Three.js (#22aa22)
      // Blue: Z vertical do SketchUp / Y vertical do Three.js (#2244ff)
      const axes = [
        {
          id: "red",
          dir: new THREE.Vector3(1, 0, 0),
          label: "No Eixo Vermelho (X)",
          color: 0xff2222,
        },
        {
          id: "green",
          dir: new THREE.Vector3(0, 0, 1),
          label: "No Eixo Verde (Y)",
          color: 0x22aa22,
        },
        {
          id: "blue",
          dir: new THREE.Vector3(0, 1, 0),
          label: "No Eixo Azul (Vertical Z)",
          color: 0x2244ff,
        },
      ];

      // Vetor do mouse na tela a partir do startPoint
      const mouseScreenVec = new THREE.Vector2(mouseX - sStart.x, mouseY - sStart.y);
      const mouseDistPx = mouseScreenVec.length();

      let detectedAxis = null;

      if (activeLockedAxis) {
        // Trava forçada pelo usuário (Setas ou Shift)
        detectedAxis = axes.find((a) => a.id === activeLockedAxis) || null;
      } else if (mouseDistPx > 10) {
        // Tolerância Angular em Tela: testa alinhamento com a projeção 2D de cada eixo
        const normMouseScreen = mouseScreenVec.clone().normalize();
        let maxAlignment = 0;
        let candidateAxis = null;

        for (const axis of axes) {
          // Projeta um ponto 2 metros à frente ao longo do eixo na tela
          const ptAlongAxis = startPoint.clone().addScaledVector(axis.dir, 2.0);
          const sAxisPt = this._projectToScreen(ptAlongAxis, rect);
          const axisScreenVec = new THREE.Vector2(sAxisPt.x - sStart.x, sAxisPt.y - sStart.y);
          const axisLenPx = axisScreenVec.length();

          // Se o eixo estiver de frente para a câmera (degenerado na tela), ignora
          if (axisLenPx < 3) continue;

          const normAxisScreen = axisScreenVec.normalize();
          // Produto escalar absoluto: a linha pode seguir no sentido positivo ou negativo do eixo
          const alignment = Math.abs(normMouseScreen.dot(normAxisScreen));

          // Tolerância angular do SketchUp: ~18 graus (cos(18°) ≈ 0.951)
          if (alignment > maxAlignment) {
            maxAlignment = alignment;
            if (alignment >= 0.94) {
              candidateAxis = axis;
            }
          }
        }

        if (candidateAxis) {
          detectedAxis = candidateAxis;
        }
      }

      // Se um eixo cartesiano foi detectado (ou travado) E não há snap em vértice/aresta física:
      if (detectedAxis && (!bestPoint || snapType === "face" || snapType === "none")) {
        // Calcula a posição 3D exata usando a reta mais próxima ao raio da câmera
        const linePt = closestPointOnLineToRay(
          startPoint,
          detectedAxis.dir,
          raycaster.ray.origin,
          raycaster.ray.direction
        );

        bestPoint = linePt;

        // Limpeza estrita de coordenadas para fidelidade absoluta aos eixos:
        if (detectedAxis.id === "red") {
          // Eixo Vermelho: Y e Z NUNCA se alteram em relação ao startPoint!
          bestPoint.y = startPoint.y;
          bestPoint.z = startPoint.z;
        } else if (detectedAxis.id === "green") {
          // Eixo Verde: X e Y NUNCA se alteram em relação ao startPoint!
          bestPoint.x = startPoint.x;
          bestPoint.y = startPoint.y;
        } else if (detectedAxis.id === "blue") {
          // Eixo Azul: X e Z NUNCA se alteram em relação ao startPoint!
          bestPoint.x = startPoint.x;
          bestPoint.z = startPoint.z;
        }

        snapType = `axis_${detectedAxis.id}`;
        snapLabel = detectedAxis.label;
        snapColor = detectedAxis.color;
        this.lastInferredAxis = detectedAxis.id;

        // Exibe a linha guia infinita tracejada
        this._showGuideLine(startPoint, detectedAxis.dir, detectedAxis.color);
      } else {
        this.guideLine.visible = false;
        if (!detectedAxis) {
          this.lastInferredAxis = null;
        }
      }
    } else {
      this.guideLine.visible = false;
    }

    // ------------------------------------------------------------------------
    // FASE 3: Plano de Trabalho Ativo 2D para Movimento Livre (Fora dos Eixos)
    // ------------------------------------------------------------------------
    if (!bestPoint) {
      if (startPoint) {
        // Se já começou o desenho, o plano de trabalho horizontal fica na ALTURA do startPoint!
        // Impede completamente que a linha "afunde" para Y=0 ou derive obliquamente para o infinito.
        const activeHorizontalPlane = new THREE.Plane(new THREE.Vector3(0, 1, 0), -startPoint.y);
        const planeHit = new THREE.Vector3();
        if (raycaster.ray.intersectPlane(activeHorizontalPlane, planeHit)) {
          bestPoint = planeHit;
          bestPoint.y = startPoint.y; // Força coplanaridade perfeita
          snapType = "working_plane";
          snapLabel = "No plano de trabalho";
        } else {
          // Fallback se a câmera olhar paralela ao chão: plano perpendicular à câmera passando por startPoint
          const camDir = this.camera.getWorldDirection(new THREE.Vector3());
          const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(camDir.clone().negate(), startPoint);
          bestPoint = new THREE.Vector3();
          raycaster.ray.intersectPlane(plane, bestPoint);
          snapType = "view_plane";
          snapLabel = "No plano de visão";
        }
      } else {
        // Primeiro clique no vazio: intersecta o chão horizontal do mundo (Y=0)
        const groundHit = new THREE.Vector3();
        if (raycaster.ray.intersectPlane(this.groundPlane, groundHit)) {
          bestPoint = groundHit;
          snapType = "ground";
          snapLabel = "No plano horizontal";
        } else {
          const camDir = this.camera.getWorldDirection(new THREE.Vector3());
          const plane = new THREE.Plane().setFromNormalAndCoplanarPoint(
            camDir.clone().negate(),
            this.camera.position.clone().add(camDir.clone().multiplyScalar(5))
          );
          bestPoint = new THREE.Vector3();
          raycaster.ray.intersectPlane(plane, bestPoint);
          snapType = "view_plane";
          snapLabel = "No espaço";
        }
      }
    }

    // ------------------------------------------------------------------------
    // FASE 4: Atualiza o Marcador Visual de Snap
    // ------------------------------------------------------------------------
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
      origin.clone().addScaledVector(dir, -500),
      origin.clone().addScaledVector(dir, 500),
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
