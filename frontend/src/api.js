// Cliente HTTP fino contra o backend FastAPI -- sem logica de UI aqui.

export class ApiError extends Error {
  /** `detail` e o valor bruto de `errorBody.detail` -- normalmente uma
   * string, mas pode ser um objeto estruturado (ex.: `{code: "...", ...}`,
   * ver SceneOverwriteConfirmationRequiredError) quando o backend precisa
   * mandar mais do que uma mensagem pro chamador decidir o que fazer. */
  constructor(message, status, detail) {
    super(message);
    this.status = status;
    this.detail = detail !== undefined ? detail : message;
  }
}

async function postJson(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const errorBody = await res.json();
      detail = errorBody.detail ?? detail;
    } catch {
      // resposta nao era JSON -- mantem o statusText
    }
    const message = typeof detail === "string" ? detail : detail?.message || res.statusText;
    throw new ApiError(message, res.status, detail);
  }

  return res.json();
}

export function openScene(path) {
  return postJson("/api/v1/scene/open", "POST", { path });
}

/** Abre um .skp usando o leitor nativo binario Pure Python (Zero DLL),
 * renderizando malha, UVs analiticas, materiais PBR e instâncias no Three.js. */
export function openBinaryScene(path) {
  return postJson("/api/v1/scene/open-binary", "POST", { path });
}

/** Abre um .skp enviado via upload real do navegador (`<input
 * type="file">`) -- o unico jeito de um app web usar o seletor NATIVO de
 * arquivos do SO sem o usuario digitar/colar o caminho a mao. Por
 * seguranca padrao de toda a web (nao so deste app), o navegador nunca
 * expoe o caminho real em disco de um arquivo escolhido assim, so o seu
 * conteudo -- por isso a sessao resultante fica sem `model_path`, igual
 * `newSceneFromTemplate()`, exigindo "Salvar Como" no primeiro Salvar. */
export async function openUploadedScene(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/api/v1/scene/open-upload", { method: "POST", body: formData });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const errorBody = await res.json();
      detail = errorBody.detail ?? detail;
    } catch {
      // resposta nao era JSON -- mantem o statusText
    }
    const message = typeof detail === "string" ? detail : detail?.message || res.statusText;
    throw new ApiError(message, res.status, detail);
  }
  return res.json();
}

/** Cria um modelo novo a partir de um template real da Trimble (ver
 * "Criar novo modelo" na Pagina Inicial). O DTO volta com `model_path:
 * null` -- o modelo ainda nao tem arquivo no disco, precisa de "Salvar
 * Como" antes do primeiro save. */
export function newSceneFromTemplate(templateId) {
  return postJson("/api/v1/scene/new", "POST", { template_id: templateId });
}

/** `transform`: array de 16 floats, matriz 4x4 column-major em espaco de
 * MUNDO -- mesma convencao do campo `transform` do DTO de /scene/open. */
export function updateInstanceTransform(instanceId, transform) {
  return postJson(
    `/api/v1/scene/instances/${encodeURIComponent(instanceId)}/transform`,
    "PATCH",
    { transform }
  );
}

/** Duplica nativamente uma instância na sessão aberta (Zero DLL / Pure Python SkpBinaryWriter). */
export function duplicateInstance(instanceId, { transform = null, offsetDeltaCm = null } = {}) {
  return postJson(
    `/api/v1/scene/instances/${encodeURIComponent(instanceId)}/duplicate`,
    "POST",
    { transform, offset_delta_cm: offsetDeltaCm }
  );
}

/** `path` vazio/undefined sobrescreve o arquivo que foi aberto.
 * `overwriteConfirmed`: so precisa ser `true` quando uma chamada anterior
 * devolveu 409 com `detail.code === "overwrite_confirmation_required"` e
 * o usuario confirmou que quer sobrescrever o arquivo existente mesmo
 * assim (ver handleSave() em main.js e a trava em
 * app/repositories/skp_engine_repository.py save()). */
export function saveScene(path, overwriteConfirmed = false) {
  return postJson("/api/v1/scene/save", "POST", {
    path: path || null,
    overwrite_confirmed: overwriteConfirmed,
  });
}

/** Exclui de verdade a instancia da sessao aberta (equivalente a "Editar
 * > Excluir"/Del do SketchUp real -- ver REVERSE_ENGINEERING_NOTES.md
 * secao 26). Irreversivel nesta sessao (ainda nao ha undo/redo). */
export async function deleteInstance(instanceId) {
  const res = await fetch(`/api/v1/scene/instances/${encodeURIComponent(instanceId)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const errorBody = await res.json();
      detail = errorBody.detail || detail;
    } catch {
      // resposta nao era JSON -- mantem o statusText
    }
    throw new ApiError(detail, res.status);
  }
  return res.json();
}

/** Exporta a sessao aberta pra um .obj (equivalente parcial de "Arquivo >
 * Exportar > Modelo 3D..." -- so OBJ por enquanto, ver core/obj_exporter.py). */
export function exportModelObj(path) {
  return postJson("/api/v1/scene/export/obj", "POST", { path });
}

/** Cria uma face retangular nova no chao da sessao aberta (equivalente
 * real de "Desenho > Formas > Retângulo" -- ver core/su_api.py add_face()
 * e REVERSE_ENGINEERING_NOTES.md secao 28). `widthM`/`heightM` em metros.
 * `asGroup` (opcional): cria a face dentro de um Grupo novo real
 * (equivalente a "Editar > Criar grupo", ver secao 28.17) em vez de solta
 * na raiz. Devolve a cena inteira pos-criacao (`{scene: SceneResponse}`). */
export function addRectangle(widthM, heightM, asGroup = false) {
  return postJson("/api/v1/scene/geometry/rectangle", "POST", {
    width_m: widthM,
    height_m: heightM,
    as_group: asGroup,
  });
}

/** Aplica uma Etiqueta (Tag) real numa instancia da sessao aberta
 * (equivalente real de "Ferramentas > Etiqueta" -- a API interna ainda
 * chama isso de "Layer", nome legado da Trimble; ver core/su_api.py
 * create_tag()/set_instance_tag() e REVERSE_ENGINEERING_NOTES.md secao
 * 28.17). So muda metadado (nao topologia/malha) -- nao devolve a cena
 * inteira. */
export function tagInstance(instanceId, name) {
  return postJson(
    `/api/v1/scene/instances/${encodeURIComponent(instanceId)}/tag`,
    "POST",
    { name }
  );
}

/** Aplica uma cor RGBA nova de verdade numa instancia da sessao aberta
 * (equivalente real de "Ferramentas > Pintura" -- ver core/su_api.py
 * paint_instance() e REVERSE_ENGINEERING_NOTES.md secao 28). So muda
 * aparencia (nao topologia/malha) -- nao devolve a cena inteira, o
 * chamador aplica a cor direto no mesh do Three.js. */
export function paintInstance(instanceId, r, g, b) {
  return postJson(
    `/api/v1/scene/instances/${encodeURIComponent(instanceId)}/material`,
    "POST",
    { r, g, b }
  );
}

/** Aplica uma cor RGBA nova de verdade numa FACE especifica (nao na
 * instancia inteira) -- equivalente real de pintar por face no SketchUp
 * (ver core/su_api.py paint_face() e REVERSE_ENGINEERING_NOTES.md secao
 * 28.19). A face pertence a geometria da DEFINICAO, entao a mudanca fica
 * gravada no .skp pra TODAS as instancias que compartilham essa
 * definicao. So muda aparencia (nao topologia/malha) -- nao devolve a
 * cena inteira. */
export function paintFace(faceId, r, g, b) {
  return postJson(
    `/api/v1/scene/faces/${encodeURIComponent(faceId)}/material`,
    "POST",
    { r, g, b }
  );
}

/** Lista TODAS as Cenas reais do modelo aberto (equivalente real de
 * "Janela > Bandeja padrão > Cenas" -- ver core/su_api.py get_scenes()
 * e REVERSE_ENGINEERING_NOTES.md seção 28.20). Inclui cenas que já
 * vinham salvas no .skp antes desta sessão. */
export async function listScenePages() {
  const res = await fetch("/api/v1/scene/pages");
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res.json();
}

/** Cria uma Cena real nova a partir do estado atual (SUSceneCreate/
 * SUModelAddScenes) -- NÃO captura câmera/estilo visual (limitação
 * documentada, ver REVERSE_ENGINEERING_NOTES.md seção 28.20). */
export function createScenePage(name) {
  return postJson("/api/v1/scene/pages", "POST", { name });
}

/** Ativa uma Cena real (SUSceneActivate) -- vira a "cena ativa" do
 * modelo, persistida ao salvar. Não move a câmera do viewer nesta
 * sessão (mesma limitação de createScenePage). */
export function activateScenePage(sceneId) {
  return postJson(
    `/api/v1/scene/pages/${encodeURIComponent(sceneId)}/activate`,
    "POST",
    {}
  );
}

/** Lista TODAS as Etiquetas reais do modelo aberto (equivalente real de
 * "Janela > Bandeja padrão > Etiquetas" -- ver core/su_api.py list_layers()
 * e REVERSE_ENGINEERING_NOTES.md seção 28.22). Inclui etiquetas que já
 * vinham salvas no .skp antes desta sessão, com visibilidade real. */
export async function listTags() {
  const res = await fetch("/api/v1/scene/tags");
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  const body = await res.json();
  return body.tags;
}

/** Alterna a visibilidade real de uma Etiqueta (SULayerSetVisibility --
 * equivalente ao ícone de olho da Bandeja padrão real). Estado persiste
 * na sessão (e no arquivo, se "Salvar" for chamado depois) -- não é só
 * um filtro cosmético client-side. */
export function setTagVisibility(tagName, visible) {
  return postJson(
    `/api/v1/scene/tags/${encodeURIComponent(tagName)}/visibility`,
    "PATCH",
    { visible }
  );
}

/** Redefine os eixos customizados (locais) da definicao por tras da
 * instancia/Grupo clicado -- equivalente real de "Ferramentas > Eixos"
 * (ver core/su_api.py create_custom_axes()/set_definition_axes() e
 * REVERSE_ENGINEERING_NOTES.md secao 28.21). `origin`/`xPoint`/`yPoint`
 * ja vem em POLEGADAS no espaco LOCAL dessa definicao (conversao feita
 * no frontend, ver sceneBuilder.js worldPointToLocalInches()) -- o
 * backend monta a base ortonormal real (Gram-Schmidt) antes de chamar a
 * DLL. Como e um metadado da DEFINICAO (nao da instancia), afeta todas
 * as instancias que a compartilham no .skp -- mesmo comportamento do
 * SketchUp real. */
export function setInstanceAxes(instanceId, origin, xPoint, yPoint) {
  return postJson(
    `/api/v1/scene/instances/${encodeURIComponent(instanceId)}/axes`,
    "POST",
    { origin, x_point: xPoint, y_point: yPoint }
  );
}

/** Reextrai a sessao JA ABERTA em memoria no backend (sem reler do disco)
 * -- cobre dar F5 na pagina com o backend ainda rodando, sem perder
 * edicoes ainda nao salvas (ver README.md "Persistencia de sessao").
 * `null` quando o backend nao tem nenhuma sessao aberta no momento
 * (acabou de reiniciar, ou ninguem abriu nada ainda nesta execucao). */
export async function getCurrentSession() {
  const res = await fetch("/api/v1/scene/session");
  if (res.status === 409) return null;
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res.json();
}

/** Lista rascunhos de autosave reais disponiveis pra recuperacao (ver
 * README.md "Persistencia de sessao") -- cobre o caso de o backend ter
 * reiniciado com edicoes ainda nao salvas. */
export async function listAutosaveDrafts() {
  const res = await fetch("/api/v1/scene/autosave");
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  const body = await res.json();
  return body.drafts;
}

/** Reabre um rascunho de autosave -- a sessao resultante fica associada
 * ao arquivo ORIGINAL (nao ao rascunho interno), entao "Salvar" continua
 * sobrescrevendo o arquivo de verdade do usuario. */
export function recoverAutosaveDraft(draftId) {
  return postJson(`/api/v1/scene/autosave/${encodeURIComponent(draftId)}/recover`, "POST", {});
}

/** Descarta um rascunho de autosave sem recuperar. */
export async function discardAutosaveDraft(draftId) {
  const res = await fetch(`/api/v1/scene/autosave/${encodeURIComponent(draftId)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res.json();
}

/** Lista de .skp recentemente abertos por este app (mais recente primeiro). */
export async function listRecentFiles() {
  const res = await fetch("/api/v1/recent-files");
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res.json();
}

/** Manda um snapshot real (PNG, data URL) do canvas 3D pra virar a
 * thumbnail do arquivo na Pagina Inicial. Best-effort -- chamador decide
 * se quer tratar falha ou so ignorar. */
export function uploadThumbnail(path, imageDataUrl) {
  return postJson("/api/v1/recent-files/thumbnail", "POST", {
    path,
    image_base64: imageDataUrl,
  });
}

// ============================================================================
// Frentes 13, 15, 19, 20 & Desmontador / Orçamento BIM (Opções 1 e 2)
// ============================================================================

/** Cria um bloco/sólido 3D manifold paramétrico na cena (Frente 13). */
export function createBox(widthM, lengthM, heightM, offsetXYZ = [0, 0, 0]) {
  return postJson("/api/v1/scene/box", "POST", {
    width_m: Number(widthM),
    length_m: Number(lengthM),
    height_m: Number(heightM),
    offset_xyz_cm: offsetXYZ,
  });
}

/** Configura o estilo técnico de renderização/exibição (Frente 19). */
export function setRenderingStyle({ mode = "textured", xray = false, profilesWidth = 2, backgroundRgb = null, skyRgb = null } = {}) {
  return postJson("/api/v1/scene/style", "POST", {
    mode,
    xray,
    profiles_width: profilesWidth,
    background_rgb: backgroundRgb,
    sky_rgb: skyRgb,
  });
}

/** Obtém a árvore hierárquica do Outliner e montagens aninhadas (Frente 15). */
export async function getAssemblyTree() {
  const res = await fetch("/api/v1/scene/assembly-tree");
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res.json();
}

/** Converte arquivo DXF para SKP (Frente 20). */
export function convertDxf(dxfPath, scaleFactor = 1.0) {
  return postJson("/api/v1/scene/convert-dxf", "POST", {
    dxf_path: dxfPath,
    scale_factor: scaleFactor,
  });
}

/** Obtém relatório analítico do Orçamento BIM e Lista de Materiais (BOM). */
export async function getBimReport() {
  const res = await fetch("/api/v1/scene/bim-report");
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res.json();
}

/** Calcula a matriz 4x4 de todas as instâncias na Vista Explodida. */
export function calculateExplodedView(expansionFactor = 0.5) {
  return postJson("/api/v1/scene/exploded-view", "POST", {
    expansion_factor: Number(expansionFactor),
  });
}

// ============================================================================
// Frente 21: Exportador Multi-formato (GLTF/GLB e IFC BIM)
// ============================================================================

/** Exporta a cena para glTF 2.0 Binary (.glb) com PBR (Frente 21). */
export function exportModelGlb(path) {
  return postJson("/api/v1/scene/export/glb", "POST", { path });
}

/** Exporta a cena para modelo BIM aberto IFC4 STEP ISO 10303-21 (Frente 21). */
export function exportModelIfc(path, projectName = "Projeto SketchBuild") {
  return postJson("/api/v1/scene/export/ifc", "POST", { path, project_name: projectName });
}

// ============================================================================
// Frente 22: Autoria Interativa de Desenho (Linhas e Faces B-Rep)
// ============================================================================

/** Adiciona uma aresta/linha nativa no modelo .skp aberto (Zero DLL). */
export function addLineGeometry(startM, endM) {
  return postJson("/api/v1/scene/geometry/line", "POST", {
    start_m: startM,
    end_m: endM,
  });
}

/** Adiciona uma face poligonal nativa B-Rep no modelo .skp aberto (Zero DLL). */
export function addFaceGeometry(pointsM) {
  return postJson("/api/v1/scene/geometry/face", "POST", {
    points_m: pointsM,
  });
}



// ============================================================================
// Frente 23: Integração Industrial Parkelô & Exportador Lista de Corte (.xlsx)
// ============================================================================

/** Exporta a lista de corte e orçamento para planilha Excel .xlsx (Frente 23). */
export function exportCutlistXlsx(path) {
  return postJson("/api/v1/scene/export/cutlist-xlsx", "POST", { path });
}

// ============================================================================
// Frente 14: Curvas, Círculos e Cilindros Paramétricos
// ============================================================================

/** Cria um círculo plano B-Rep paramétrico no modelo (Frente 14). */
export function addCircleGeometry(radiusM, centerM = [0.0, 0.0, 0.0], numSegments = 24) {
  return postJson("/api/v1/scene/geometry/circle", "POST", {
    radius_m: radiusM,
    center_xyz_m: centerM,
    num_segments: numSegments,
  });
}

/** Cria um cilindro 3D manifold paramétrico (Frente 14). */
export function addCylinderGeometry(radiusM, heightM, centerM = [0.0, 0.0, 0.0], numSegments = 16) {
  return postJson("/api/v1/scene/geometry/cylinder", "POST", {
    radius_m: radiusM,
    height_m: heightM,
    center_xyz_m: centerM,
    num_segments: numSegments,
  });
}

// ============================================================================
// Frente 24: Ferramenta Push/Pull Interativa no Canvas WebGL
// ============================================================================

/** Extrude uma face coplanar para sólido 3D Push/Pull (Frente 24). */
export function extrudeFaceGeometry(pointsM, distanceM, normal = null) {
  return postJson("/api/v1/scene/geometry/pushpull", "POST", {
    points_m: pointsM,
    distance_m: distanceM,
    normal: normal,
  });
}

// ============================================================================
// Frente 26: Sequenciador de Montagem e Manual Técnico 3D
// ============================================================================

/** Obtém as etapas sequenciais de montagem (Frente 26). */
export async function getAssemblySteps() {
  const res = await fetch("/api/v1/scene/assembly-steps");
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res.json();
}

/** Gera e salva manual de montagem em HTML (Frente 26). */
export function exportAssemblyManual(projectName = "Playground Parkelô", path = null) {
  return postJson("/api/v1/scene/export/assembly-manual", "POST", {
    project_name: projectName,
    path: path,
  });
}

// ============================================================================
// Frente 27: Desenho Técnico Vetorial 2D (Plantas Baixas e Elevações)
// ============================================================================

/** Exporta desenho técnico 2D vetorial em SVG (Frente 27). */
export function exportDrawing2D(path, viewType = "top", title = "Prancha Técnica de Engenharia", scale = "1:50") {
  return postJson("/api/v1/scene/export/drawing-2d", "POST", {
    path: path,
    view_type: viewType,
    title: title,
    scale: scale,
  });
}

// ============================================================================
// Frente 28: Estudo Solar e Sombras Analíticas (Heliodon)
// ============================================================================

/** Calcula o estudo solar, vetor de iluminação e conformidade NBR 16071 (Frente 28). */
export function calculateSolarStudy(dayOfYear = 80, hour = 14.0, latitude = -23.5505, longitude = -46.6333) {
  return postJson("/api/v1/scene/solar-study", "POST", {
    day_of_year: dayOfYear,
    hour: hour,
    latitude: latitude,
    longitude: longitude,
  });
}


// ============================================================================
// Frentes 17, 18, 25, 29 e 30: Seções, Guias, Booleanas, PDF e Offset
// ============================================================================

/** Adiciona um Plano de Corte de Seção (Frente 17). */
export function createSectionPlane(planeAbcd = [0, 0, 1, 0], name = "Corte A-A", symbol = "A1") {
  return postJson("/api/v1/scene/section-plane", "POST", {
    plane_abcd: planeAbcd,
    name: name,
    symbol: symbol,
  });
}

/** Lista todos os Planos de Corte de Seção (Frente 17). */
export function getSectionPlanes() {
  return getJson("/api/v1/scene/section-planes");
}

/** Cria uma Linha de Guia / Trena (Frente 18). */
export function createGuideLine(start, end, isInfinite = false) {
  return postJson("/api/v1/scene/geometry/guide-line", "POST", {
    start: start,
    end: end,
    is_infinite: isInfinite,
  });
}

/** Cria um Ponto de Construção (Frente 18). */
export function createGuidePoint(position) {
  return postJson("/api/v1/scene/geometry/guide-point", "POST", {
    position: position,
  });
}

/** Retorna todas as guias e pontos de construção da cena (Frente 18). */
export function getGuides() {
  return getJson("/api/v1/scene/geometry/guides");
}

/** Aplica operação booleana sólida CSG (Frente 25). */
export function applyBooleanOperation(operation, mainShape, toolShape) {
  return postJson("/api/v1/scene/geometry/boolean-operation", "POST", {
    operation: operation,
    main_shape: mainShape,
    tool_shape: toolShape,
  });
}

/** Exporta proposta executiva e prancha técnica em PDF (Frente 29). */
export function exportExecutivePdf(projectName = "Parque Infantil Parkelô", author = "Eng. Fernando", clientName = "Cliente Final", outputFilename = "proposta_executiva_parkelo.pdf") {
  return postJson("/api/v1/scene/export/executive-pdf", "POST", {
    project_name: projectName,
    author: author,
    client_name: clientName,
    output_filename: outputFilename,
  });
}

/** Cria face ou moldura equidistante via Offset (Frente 30). */
export function createOffsetFace(points, distance = 0.10, inside = true, createFrame = false) {
  return postJson("/api/v1/scene/geometry/offset", "POST", {
    points: points,
    distance: distance,
    inside: inside,
    create_frame: createFrame,
  });
}


// ============================================================================
// Frentes 31 a 35: Follow Me, Arcos 3D, Rotação, Auditoria NBR 16071 e OBJ
// ============================================================================

/** Extrusão 3D Follow Me ao longo de caminho (Frente 31). */
export function createFollowMe(pathPoints, profileType = "circle", radius = 0.10, profilePoints = null, closeCaps = true) {
  return postJson("/api/v1/scene/geometry/follow-me", "POST", {
    path_points: pathPoints,
    profile_type: profileType,
    radius: radius,
    profile_points: profilePoints,
    close_caps: closeCaps,
  });
}

/** Gera arco circular 3D paramétrico (Frente 32). */
export function createArc(start, end, sagitta = 0.30, numSegments = 12) {
  return postJson("/api/v1/scene/geometry/arc", "POST", {
    start: start,
    end: end,
    sagitta: sagitta,
    num_segments: numSegments,
  });
}

/** Aplica rotação analítica com transferidor (Frente 33). */
export function applyRotation(instanceId, pivot, axis, angleDegrees = 45.0) {
  return postJson("/api/v1/scene/geometry/rotate", "POST", {
    instance_id: instanceId,
    pivot: pivot,
    axis: axis,
    angle_degrees: angleDegrees,
  });
}

/** Audita conformidade normativa de segurança infantil NBR 16071 (Frente 34). */
export function auditNbr16071Safety() {
  return getJson("/api/v1/scene/safety-audit-nbr16071");
}

/** Importa arquivo Wavefront OBJ para a sessão do .SKP (Frente 35). */
export function importObj(filePath, scale = 1.0) {
  return postJson("/api/v1/scene/import-obj", "POST", {
    file_path: filePath,
    scale: scale,
  });
}


// ============================================================================
// Frentes 36 a 40: Nesting, Terrenos, FEA Estrutural, Escala e CAM DXF
// ============================================================================

/** Otimiza plano de corte de barras de madeira no chão de fábrica (Frente 36). */
export function calculateNesting(demandedPieces, stockBarLength = 3.00) {
  return postJson("/api/v1/scene/factory/nesting-optimizer", "POST", {
    demanded_pieces: demandedPieces,
    stock_bar_length_m: stockBarLength,
  });
}

/** Gera terreno paramétrico e malha topográfica Sandbox (Frente 37). */
export function createTerrain(widthM = 10.0, lengthM = 10.0, gridRes = 1.0, slopeX = 0.0, slopeY = 5.0) {
  return postJson("/api/v1/scene/geometry/terrain", "POST", {
    width_m: widthM,
    length_m: lengthM,
    grid_resolution_m: gridRes,
    slope_x_pct: slopeX,
    slope_y_pct: slopeY,
  });
}

/** Calcula tensões e flechas em vigas de eucalipto segundo NBR 7190 (Frente 38). */
export function calculateStructuralAnalysis(spanM = 2.0, loadKnM = 2.5, sectionType = "circular", diameterM = 0.16, widthM = 0.08, heightM = 0.16) {
  return postJson("/api/v1/scene/engineering/structural-analysis", "POST", {
    span_length_m: spanM,
    load_kn_per_m: loadKnM,
    section_type: sectionType,
    diameter_m: diameterM,
    width_m: widthM,
    height_m: heightM,
  });
}

/** Aplica escala paramétrica à instância (Frente 39). */
export function applyScale(instanceId, scaleFactors = [1.0, 1.0, 1.0], pivot = [0.0, 0.0, 0.0]) {
  return postJson("/api/v1/scene/geometry/scale", "POST", {
    instance_id: instanceId,
    scale_factors: scaleFactors,
    pivot: pivot,
  });
}

/** Exporta contornos para máquinas CNC e Corte a Laser em DXF (Frente 40). */
export function exportCamDxf(parts, outputFilename = "pecas_usinagem_cnc.dxf") {
  return postJson("/api/v1/scene/export/cam-dxf", "POST", {
    parts: parts,
    output_filename: outputFilename,
  });
}


/** Interpola sobrevoo suave de camera Catmull-Rom (Frente 41). */
export function calculateCameraPath(waypoints, framesPerSegment = 24) {
  return postJson("/api/v1/scene/camera-path", "POST", {
    waypoints: waypoints,
    frames_per_segment: framesPerSegment,
  });
}

/** Exporta nuvem de pontos LiDAR ASCII XYZ (Frente 42). */
export function exportPointCloudXyz(outputFilename = "nuvem_pontos_modelo.xyz") {
  return postJson("/api/v1/scene/export/point-cloud-xyz", "POST", {
    output_filename: outputFilename,
  });
}

/** Gera plano normativo de manutencao preventiva NBR 16071-7 (Frente 43). */
export function generateMaintenancePlan(installationDateIso = "2026-03-01", envType = "urban") {
  return postJson("/api/v1/scene/maintenance-plan", "POST", {
    installation_date_iso: installationDateIso,
    environment_type: envType,
  });
}

/** Aplica espelhamento e simetria 3D de Householder (Frente 44). */
export function applyMirror(instanceId, planeNormal = [1.0, 0.0, 0.0], planePoint = [0.0, 0.0, 0.0]) {
  return postJson("/api/v1/scene/geometry/mirror", "POST", {
    instance_id: instanceId,
    plane_normal: planeNormal,
    plane_point: planePoint,
  });
}

/** Exporta placa patrimonial com QR Code em SVG (Frente 45). */
export function exportQrTagSvg(serialNumber = "PKL-2026-X84", productName = "Playground Parkelo NBR 16071", outputFilename = "etiqueta_patrimonio.svg") {
  return postJson("/api/v1/scene/export/qr-tag-svg", "POST", {
    serial_number: serialNumber,
    product_name: productName,
    output_filename: outputFilename,
  });
}


/** Simula cinematica e envelope de impacto de balanco NBR 16071 (Frente 46). */
export function simulateSwingKinematics(chainLengthM = 2.20, userMassKg = 50.0, initialAngleDeg = 45.0, seatHeightAtRestM = 0.45) {
  return postJson("/api/v1/scene/engineering/swing-kinematics", "POST", {
    chain_length_m: chainLengthM,
    user_mass_kg: userMassKg,
    initial_angle_deg: initialAngleDeg,
    seat_height_at_rest_m: seatHeightAtRestM,
    damping_ratio: 0.05,
    total_time_s: 4.0,
    fps: 24,
  });
}

/** Gera minuta executiva de ART / RRT em PDF vetorial (Frente 47). */
export function generateArtPdf(professionalName = "Eng. Fernando Henrique", creaCau = "CREA-SP 5060708090/D", rnp = "2619087654", contractor = "Condominio Residencial Parque das Arvores", location = "Av. das Nacoes Unidas, 14261 - SP", projectName = "Playground Parkelo NBR 16071", outputFilename = "minuta_art_rrt.pdf") {
  return postJson("/api/v1/scene/export/art-report-pdf", "POST", {
    professional_name: professionalName,
    crea_cau: creaCau,
    rnp: rnp,
    contractor: contractor,
    location: location,
    project_name: projectName,
    output_filename: outputFilename,
  });
}

/** Inspeciona espessura de paredes de pecas rotomoldadas (Frente 48). */
export function inspectWallThickness(minThicknessMm = 6.0, maxThicknessMm = 14.0) {
  return postJson("/api/v1/scene/engineering/wall-thickness", "POST", {
    min_thickness_mm: minThicknessMm,
    max_thickness_mm: maxThicknessMm,
  });
}

/** Otimiza a cubagem e alocacao 3D de volumes no transporte (Frente 49). */
export function optimizeCargoLoad(packages, vehicleType = "caminhao_truck") {
  return postJson("/api/v1/scene/factory/cargo-load", "POST", {
    packages: packages,
    vehicle_type: vehicleType,
  });
}

/** Gera prancha em SVG com traco arquitetonico estilizado e overshoot (Frente 50). */
export function generateTechnicalSketch(dihedralAngleThresholdDeg = 25.0, overshootMm = 8.0, outputFilename = "esboco_tecnico_arquitetura.svg") {
  return postJson("/api/v1/scene/export/technical-sketch-svg", "POST", {
    dihedral_angle_threshold_deg: dihedralAngleThresholdDeg,
    overshoot_mm: overshootMm,
    output_filename: outputFilename,
  });
}


/** Gera geometria 3D de toboga espiral helicoidal (Frente 51). */
export function generateSpiralTube(radiusM = 1.20, heightM = 2.40, turns = 1.25, tubeRadiusM = 0.38, isOpenGutter = false) {
  return postJson("/api/v1/scene/geometry/spiral-tube", "POST", {
    radius_m: radiusM,
    height_m: heightM,
    turns: turns,
    tube_radius_m: tubeRadiusM,
    segments_per_turn: 16,
    tube_segments: 8,
    is_open_gutter: isOpenGutter,
  });
}

/** Calcula estabilidade ao tombamento sob acao de vento NBR 6123 (Frente 52). */
export function calculateOverturnStability(totalMassKg = 850.0, cgPosition = [1.5, 1.2, 1.45], windSpeedKmH = 100.0) {
  return postJson("/api/v1/scene/engineering/overturn-stability", "POST", {
    total_mass_kg: totalMassKg,
    cg_position: cgPosition,
    wind_speed_km_h: windSpeedKmH,
    exposed_frontal_area_m2: 6.50,
    lateral_live_load_n: 500.0,
    live_load_height_m: 1.80,
  });
}

/** Exporta checklist de inspecao de campo NBR 16071-7 em HTML5 offline (Frente 53). */
export function exportFieldInspectionHtml(parkName = "Parque Villa-Lobos", inspectorName = "Eng. Fernando Henrique", inspectionDate = "2026-03-01", outputFilename = "ficha_inspecao_nbr16071.html") {
  return postJson("/api/v1/scene/export/field-inspection-html", "POST", {
    park_name: parkName,
    inspector_name: inspectorName,
    inspection_date: inspectionDate,
    output_filename: outputFilename,
  });
}

/** Calcula cota angular e arco grafico 3D entre 3 pontos (Frente 54). */
export function calculateAngleDimension(vertexPoint, pointA, pointB, arcRadiusM = 0.60) {
  return postJson("/api/v1/scene/geometry/angle-dimension", "POST", {
    vertex_point: vertexPoint,
    point_a: pointA,
    point_b: pointB,
    arc_radius_m: arcRadiusM,
  });
}

/** Dimensiona fixador e calcula torque normativo NBR 7190 / ISO 898 (Frente 55). */
export function calculateFastenerTorque(timberThicknessMm = 160.0, steelPlateThicknessMm = 4.75, boltStandard = "1/2_POL", materialGrade = "Inox_304") {
  return postJson("/api/v1/scene/engineering/fastener-torque", "POST", {
    timber_thickness_mm: timberThicknessMm,
    steel_plate_thickness_mm: steelPlateThicknessMm,
    bolt_standard: boltStandard,
    material_grade: materialGrade,
    friction_factor_k: 0.18,
  });
}
