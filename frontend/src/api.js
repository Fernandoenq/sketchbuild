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


/** Gera geometria 3D de telhado de 4 aguas ou piramidal (Frente 56). */
export function generateHipRoof(baseWidthM = 2.40, baseLengthM = 3.20, baseHeightM = 2.80, pitchDeg = 30.0, overhangM = 0.35) {
  return postJson("/api/v1/scene/geometry/hip-roof", "POST", {
    base_width_m: baseWidthM,
    base_length_m: baseLengthM,
    base_height_m: baseHeightM,
    pitch_deg: pitchDeg,
    overhang_m: overhangM,
  });
}

/** Simula impacto HIC e piso amortecedor NBR 16071-3 (Frente 57). */
export function simulateHicImpact(fallHeightM = 1.80, surfaceType = "areia_lavada", installedThicknessMm = 300.0) {
  return postJson("/api/v1/scene/engineering/hic-impact", "POST", {
    fall_height_m: fallHeightM,
    surface_type: surfaceType,
    installed_thickness_mm: installedThicknessMm,
  });
}

/** Exporta etiqueta termica industrial Zebra ZPL II e SVG (Frente 58). */
export function exportZebraLabel(partName = "Pilar Eucalipto", partSku = "PKL-EUC-16-220", dimensionsMm = "D160 x L2200 mm", lotBatch = "LOTE-2026-X84") {
  return postJson("/api/v1/scene/export/zebra-label", "POST", {
    part_name: partName,
    part_sku: partSku,
    dimensions_mm: dimensionsMm,
    lot_batch: lotBatch,
    output_zpl_filename: "etiqueta_zebra.zpl",
    output_svg_filename: "etiqueta_zebra.svg",
  });
}

/** Calcula linhas tracejadas de trajetoria para vista explodida (Frente 59). */
export function calculateExplodedTrails(parts, dashSizeM = 0.05, gapSizeM = 0.03) {
  return postJson("/api/v1/scene/geometry/exploded-trails", "POST", {
    parts: parts,
    dash_size_m: dashSizeM,
    gap_size_m: gapSizeM,
  });
}

/** Calcula balanco de carbono e sustentabilidade florestal (Frente 60). */
export function calculateCarbonFootprint(timberVolumeM3 = 2.80, steelWeightKg = 95.0, plasticWeightKg = 45.0, transportDistanceKm = 350.0) {
  return postJson("/api/v1/scene/engineering/carbon-footprint", "POST", {
    timber_volume_m3: timberVolumeM3,
    steel_weight_kg: steelWeightKg,
    plastic_weight_kg: plasticWeightKg,
    transport_distance_km: transportDistanceKm,
  });
}


/** Manipula dicionarios de atributos nativos e componentes dinamicos (Frente 61). */
export function manageAttributeDictionary(dictName = "dynamic_attributes", key = "_lenx_formula", value = "=100 * 2", evaluateFormula = false, contextVars = {}) {
  return postJson("/api/v1/scene/attributes/dictionary", "POST", {
    dict_name: dictName,
    key: key,
    value: value,
    evaluate_formula: evaluateFormula,
    context_vars: contextVars,
  });
}

/** Cria e gerencia pastas de tags hierarquicas (Frente 62). */
export function manageTagFolder(folderId, name, parentId = null, visible = true, tagsToAdd = []) {
  return postJson("/api/v1/scene/tags/folder", "POST", {
    folder_id: folderId,
    name: name,
    parent_id: parentId,
    visible: visible,
    tags_to_add: tagsToAdd,
  });
}

/** Configura opcoes nativas de estilos de arestas do SketchUp (Frente 63). */
export function configureEdgeStyles(settings = {}) {
  return postJson("/api/v1/scene/styles/edge-rendering", "POST", settings);
}

/** Calcula matriz de camera com Perspectiva de Dois Pontos (Frente 64). */
export function calculateTwoPointPerspective(eye, target, fovDeg = 35.0, aspectRatio = 1.777) {
  return postJson("/api/v1/scene/camera/two-point-perspective", "POST", {
    eye: eye,
    target: target,
    fov_deg: fovDeg,
    aspect_ratio: aspectRatio,
  });
}

/** Calcula coordenadas UV analiticas para projecao planar ou cilindrica (Frente 65). */
export function projectTextureUv(vertices, projectionType = "planar", planeNormal = [0, 0, 1], scaleUM = 1.0, scaleVM = 1.0, rotationDeg = 0.0) {
  return postJson("/api/v1/scene/materials/project-uv", "POST", {
    vertices: vertices,
    projection_type: projectionType,
    plane_normal: planeNormal,
    scale_u_m: scaleUM,
    scale_v_m: scaleVM,
    rotation_deg: rotationDeg,
  });
}


/** Solda arestas contiguas em curvas SUCurveRef (Frente 66). */
export function weldCurveEdges(edges, tolerance = 0.0001) {
  return postJson("/api/v1/scene/curves/weld", "POST", { edges, tolerance });
}

/** Cria arco analitico parametrico SUArcCurveRef (Frente 66). */
export function createArcCurve(center, radius, normal = [0, 0, 1], startAngleRad = 0.0, endAngleRad = 6.283185, numSegments = 24) {
  return postJson("/api/v1/scene/curves/arc", "POST", {
    center,
    radius,
    normal,
    start_angle_rad: startAngleRad,
    end_angle_rad: endAngleRad,
    num_segments: numSegments,
  });
}

/** Cria ou configura plano de corte SUSectionPlaneRef (Frente 67). */
export function createOrReverseSectionPlane(name = "Corte Transversal", symbol = "A", normal = [0, 0, -1], distance = 1.0, isActive = true) {
  return postJson("/api/v1/scene/section-planes/create", "POST", {
    name,
    symbol,
    normal,
    distance,
    is_active: isActive,
  });
}

/** Fatia malha 3D gerando contornos e loops de corte transversal (Frente 67). */
export function sliceGeometryByPlane(vertices, faces, planeEquation) {
  return postJson("/api/v1/scene/section-planes/slice", "POST", {
    vertices,
    faces,
    plane_equation: planeEquation,
  });
}

/** Resolve shaders e propriedades PBR de estilos de faces (Frente 68). */
export function resolveFaceRenderStyle(mode = "SHADED_WITH_TEXTURES", materialColor = null, texturePath = null, opacity = 1.0, isBackFace = false) {
  return postJson("/api/v1/scene/styles/face-rendering", "POST", {
    mode,
    material_color: materialColor,
    texture_path: texturePath,
    opacity,
    is_back_face: isBackFace,
  });
}

/** Cria material de vidro fisico PBR (Frente 68). */
export function createGlassPbrMaterial(name = "Vidro Arquitetônico Transparente", color = "#dff9fb", opacity = 0.3, refractionIndex = 1.52) {
  return postJson("/api/v1/scene/materials/glass-pbr", "POST", {
    name,
    color,
    opacity,
    refraction_index: refractionIndex,
  });
}

/** Cria definicao canonica de cena SUSceneRef (Frente 69). */
export function createPresentationScene(name, eye, target, up = [0, 1, 0], fov = 35.0, isOrthographic = false, transitionTime = 1.5, delayTime = 1.0, includeInAnimation = true) {
  return postJson("/api/v1/scene/scenes/create", "POST", {
    name,
    eye,
    target,
    up,
    fov,
    is_orthographic: isOrthographic,
    transition_time: transitionTime,
    delay_time: delayTime,
    include_in_animation: includeInAnimation,
  });
}

/** Gera timeline continua de transicao entre cenas (Frente 69). */
export function generateSceneAnimationTimeline(scenes, fps = 30, loop = true) {
  return postJson("/api/v1/scene/scenes/animate", "POST", { scenes, fps, loop });
}

/** Calcula parametros de iluminacao solar e sombreamento SUShadowInfoRef (Frente 70). */
export function calculateShadowAndSunInfo(params = {}) {
  return postJson("/api/v1/scene/shadows/heliodon", "POST", {
    year: params.year ?? 2026,
    month: params.month ?? 3,
    day: params.day ?? 21,
    hour: params.hour ?? 14,
    minute: params.minute ?? 0,
    latitude: params.latitude ?? -23.5505,
    longitude: params.longitude ?? -46.6333,
    tz_offset: params.tz_offset ?? -3.0,
    north_angle: params.north_angle ?? 0.0,
    light_intensity: params.light_intensity ?? 80,
    dark_intensity: params.dark_intensity ?? 45,
    display_shadows: params.display_shadows ?? true,
    use_sun_for_shading: params.use_sun_for_shading ?? true,
    edges_cast_shadows: params.edges_cast_shadows ?? false,
  });
}


/** Cria anotacao de texto 2D fixada em tela HUD (Frente 71). */
export function createScreenText(text, screenX = 20.0, screenY = 20.0, fontName = "Arial", fontSizePt = 12, colorHex = "#000000", bold = false, italic = false) {
  return postJson("/api/v1/scene/text/screen", "POST", {
    text,
    screen_x: screenX,
    screen_y: screenY,
    font_name: fontName,
    font_size_pt: fontSizePt,
    color_hex: colorHex,
    bold,
    italic,
  });
}

/** Cria rotulo anotativo com linha de chamada 3D (Frente 71). */
export function createLeaderText(text, anchorPoint, offsetVector = [0.5, 0.5, 0.5], arrowType = "ARROW", fontName = "Arial", fontSizePt = 10, colorHex = "#000000") {
  return postJson("/api/v1/scene/text/leader", "POST", {
    text,
    anchor_point: anchorPoint,
    offset_vector: offsetVector,
    arrow_type: arrowType,
    font_name: fontName,
    font_size_pt: fontSizePt,
    color_hex: colorHex,
  });
}

/** Calcula cota linear com linhas de extensao e tiques arquitetonicos (Frente 72). */
export function createDimensionLinear(startPt, endPt, offsetDistance = 0.2, planeNormal = null, arrowType = "SLASH", unit = "m", precision = 2, customText = null) {
  return postJson("/api/v1/scene/dimensions/linear", "POST", {
    start_pt: startPt,
    end_pt: endPt,
    offset_distance: offsetDistance,
    plane_normal: planeNormal,
    arrow_type: arrowType,
    unit,
    precision,
    custom_text: customText,
  });
}

/** Cria linha de guia infinita ou finita SUGuideLineRef (Frente 73). */
export function createGuideLineInfinite(point, direction = null, endPoint = null, isInfinite = true, extentM = 500.0) {
  return postJson("/api/v1/scene/guides/infinite", "POST", {
    point,
    direction,
    end_point: endPoint,
    is_infinite: isInfinite,
    extent_m: extentM,
  });
}

/** Cria ponto de construcao SUGuidePointRef (Frente 73). */
export function createGuidePointRef(point) {
  return postJson("/api/v1/scene/guides/point", "POST", { point });
}

/** Calcula intersecao 3D analitica entre duas linhas de guia (Frente 73). */
export function intersectGuideLines(line1, line2, tolerance = 0.001) {
  return postJson("/api/v1/scene/guides/intersect", "POST", {
    line1,
    line2,
    tolerance,
  });
}

/** Configura material com canal alfa e recorte de profundidade (Frente 74). */
export function configureAlphaMaterial(name, texturePath, alphaMode = "MASK", alphaThreshold = 0.5, doubleSided = true) {
  return postJson("/api/v1/scene/materials/alpha-mask", "POST", {
    name,
    texture_path: texturePath,
    alpha_mode: alphaMode,
    alpha_threshold: alphaThreshold,
    double_sided: doubleSided,
  });
}

/** Calcula matriz de rotacao Face-Me para componente de vegetacao/figura humana (Frente 74). */
export function calculateFaceMeMatrix(instancePosition, cameraPosition, axialOnly = true) {
  return postJson("/api/v1/scene/components/face-me", "POST", {
    instance_position: instancePosition,
    camera_position: cameraPosition,
    axial_only: axialOnly,
  });
}

/** Resolve matriz mundial acumulada e decomposicao de no aninhado (Frente 75). */
export function resolveNestedHierarchyNode(nodeId, pathToNode) {
  return postJson("/api/v1/scene/hierarchy/resolve", "POST", {
    node_id: nodeId,
    path_to_node: pathToNode,
  });
}

/** Converte matriz mundial de edicao para matriz local de no aninhado (Frente 75). */
export function convertWorldTransformToLocal(desiredWorldMatrix, parentWorldMatrix) {
  return postJson("/api/v1/scene/hierarchy/world-to-local", "POST", {
    desired_world_matrix: desiredWorldMatrix,
    parent_world_matrix: parentWorldMatrix,
  });
}


/** Calcula cota radial ou diametrica SUDimensionRadialRef (Frente 76). */
export function createDimensionRadial(center, radius, normal = [0, 0, 1], angleDeg = 45.0, isDiameter = false, leaderLength = 0.3, unit = "m", precision = 2) {
  return postJson("/api/v1/scene/dimensions/radial", "POST", {
    center,
    radius,
    normal,
    angle_deg: angleDeg,
    is_diameter: isDiameter,
    leader_length: leaderLength,
    unit,
    precision,
  });
}

/** Configura parametros de nevoa de cena SUStyleFog (Frente 77). */
export function configureFogStyle(enabled = true, startDistM = 10.0, endDistM = 100.0, colorHex = "#dcdde1") {
  return postJson("/api/v1/scene/styles/fog", "POST", {
    enabled,
    start_dist_m: startDistM,
    end_dist_m: endDistM,
    color_hex: colorHex,
  });
}

/** Calcula parametros ideais de nevoa a partir da Bounding Box (Frente 77). */
export function calculateAutoFogFromBbox(minPoint, maxPoint, colorHex = "#dcdde1") {
  return postJson("/api/v1/scene/styles/auto-fog", "POST", {
    min_point: minPoint,
    max_point: maxPoint,
    color_hex: colorHex,
  });
}

/** Calcula suavizacao de arestas Soft & Smooth e normais de vertices (Frente 78). */
export function processMeshSmoothing(vertices, faces, angleThresholdDeg = 35.0) {
  return postJson("/api/v1/scene/geometry/smoothing", "POST", {
    vertices,
    faces,
    angle_threshold_deg: angleThresholdDeg,
  });
}

/** Gera hachuras graficas normativas NBR 6492 / ISO 128 em cortes (Frente 79). */
export function generateSectionHatchLines(closedLoop3d, pattern = "WOOD", spacingM = 0.05, angleDeg = 45.0) {
  return postJson("/api/v1/scene/section-planes/hatch", "POST", {
    closed_loop_3d: closedLoop3d,
    pattern,
    spacing_m: spacingM,
    angle_deg: angleDeg,
  });
}

/** Define georreferenciamento e calcula coordenadas UTM WGS84 (Frente 80). */
export function setGeoLocation(latitude, longitude, altitudeM = 0.0, northAngleDeg = 0.0, city = "São Paulo", country = "Brasil") {
  return postJson("/api/v1/scene/geo/reference", "POST", {
    latitude,
    longitude,
    altitude_m: altitudeM,
    north_angle_deg: northAngleDeg,
    city,
    country,
  });
}

/** Converte ponto 3D local em coordenadas geograficas WGS84 (Frente 80). */
export function localPointToWgs84(localXyzM, originLat, originLon, originAltM = 0.0, northAngleDeg = 0.0) {
  return postJson("/api/v1/scene/geo/local-to-wgs84", "POST", {
    local_xyz_m: localXyzM,
    origin_lat: originLat,
    origin_lon: originLon,
    origin_alt_m: originAltM,
    north_angle_deg: northAngleDeg,
  });
}

/** Triangula face plana com furos internos SUPolyMeshRef (Frente 81). */
export function triangulateFaceWithHoles(outerLoop3d, innerLoops3d = null) {
  return postJson("/api/v1/scene/polymesh/triangulate", "POST", {
    outer_loop_3d: outerLoop3d,
    inner_loops_3d: innerLoops3d,
  });
}

/** Calcula parâmetros de câmera perpendicular à face (Align View) (Frente 82). */
export function calculateAlignView(faceVertices, fovDeg = 35.0, marginFactor = 1.25) {
  return postJson("/api/v1/scene/camera/align-view", "POST", {
    face_vertices: faceVertices,
    fov_deg: fovDeg,
    margin_factor: marginFactor,
  });
}

/** Configura estilos de céu, solo e horizonte SUStyleRef (Frente 83). */
export function configureBackgroundSky(skyEnabled = true, groundEnabled = true, skyColor = "#b4d5fe", groundColor = "#c2b8a3", horizonColor = "#95afc0", backgroundColor = "#ffffff", groundTransparencyPercent = 50, showHorizon = true) {
  return postJson("/api/v1/scene/styles/background-sky", "POST", {
    sky_enabled: skyEnabled,
    ground_enabled: groundEnabled,
    sky_color: skyColor,
    ground_color: groundColor,
    horizon_color: horizonColor,
    background_color: backgroundColor,
    ground_transparency_percent: groundTransparencyPercent,
    show_horizon: showHorizon,
  });
}

/** Calcula tolerâncias dimensionais ISO 2768 / NBR 6492 (Frente 84). */
export function calculateDimensionTolerance(nominalVal, unit = "mm", toleranceType = "BILATERAL", upperTol = 0.1, lowerTol = 0.1, isoClass = "m", precision = 2) {
  return postJson("/api/v1/scene/dimensions/tolerance", "POST", {
    nominal_val: nominalVal,
    unit,
    tolerance_type: toleranceType,
    upper_tol: upperTol,
    lower_tol: lowerTol,
    iso_class: isoClass,
    precision,
  });
}

/** Registra operação reversível na pilha transacional (Frente 85). */
export function recordUndoOperation(name, actionType, targetId, beforeState = {}, afterState = {}) {
  return postJson("/api/v1/scene/history/record", "POST", {
    name,
    action_type: actionType,
    target_id: targetId,
    before_state: beforeState,
    after_state: afterState,
  });
}

/** Desfaz a última operação registrada (Frente 85). */
export function executeUndo() {
  return postJson("/api/v1/scene/history/undo", "POST", {});
}

/** Refaz a última operação desfeita (Frente 85). */
export function executeRedo() {
  return postJson("/api/v1/scene/history/redo", "POST", {});
}

/** Retorna histórico e profundidade das pilhas de Undo e Redo (Frente 85). */
export function getUndoRedoStatus() {
  return getJson("/api/v1/scene/history/status");
}

/** Aplica subdivisão Catmull-Clark sobre malha de controle QuadFace (Frente 86). */
export function subdivideQuadMesh(vertices, faces, iterations = 1) {
  return postJson("/api/v1/scene/geometry/subd", "POST", {
    vertices,
    faces,
    iterations,
  });
}

/** Gera cotas ortogonais e marcas de nível NBR 6492 em cortes (Frente 87). */
export function generateAutoSectionDimensions(cutLoops3d, offsetM = 0.25, unit = "m", precision = 2) {
  return postJson("/api/v1/scene/section-planes/dimensions", "POST", {
    cut_loops_3d: cutLoops3d,
    offset_m: offsetM,
    unit,
    precision,
  });
}

/** Calcula cubemap de 6 câmeras e malha de raios equirretangulares 360° (Frente 88). */
export function calculateSphericalPanorama(eyePosition, horizontalSamples = 16, verticalSamples = 8, sphereRadiusM = 10.0) {
  return postJson("/api/v1/scene/camera/panorama-360", "POST", {
    eye_position: eyePosition,
    horizontal_samples: horizontalSamples,
    vertical_samples: verticalSamples,
    sphere_radius_m: sphereRadiusM,
  });
}

/** Detecta colisões físicas (Hard Clash) e folgas (Clearance Clash) entre componentes (Frente 89). */
export function detectComponentClashes(components, clearanceToleranceM = 0.01) {
  return postJson("/api/v1/scene/clash/detect", "POST", {
    components,
    clearance_tolerance_m: clearanceToleranceM,
  });
}

/** Calcula volume, massa, Centro de Gravidade e inércia de malha B-Rep fechada (Frente 90). */
export function calculateMeshMassProperties(vertices, triangles, materialType = "madeira_eucalipto", customDensityKgM3 = 0.0) {
  return postJson("/api/v1/scene/engineering/mass-properties", "POST", {
    vertices,
    triangles,
    material_type: materialType,
    custom_density_kg_m3: customDensityKgM3,
  });
}

/** Gera casca sólida volumétrica B-Rep a partir de superfícies (Frente 91). */
export function createSolidShell(vertices, faces, thicknessM = 0.05, inwards = false) {
  return postJson("/api/v1/scene/geometry/solid-shell", "POST", {
    vertices,
    faces,
    thickness_m: thicknessM,
    inwards,
  });
}

/** Configura parâmetros de holofote fotométrico spot Three.js (Frente 92). */
export function configureSpotLight(position, target, lumens = 1200.0, colorTemperatureK = 3000.0, beamAngleDeg = 45.0, penumbraPercent = 25.0, maxDistanceM = 20.0, castShadows = true) {
  return postJson("/api/v1/scene/lighting/spotlight", "POST", {
    position,
    target,
    lumens,
    color_temperature_k: colorTemperatureK,
    beam_angle_deg: beamAngleDeg,
    penumbra_percent: penumbraPercent,
    max_distance_m: maxDistanceM,
    cast_shadows: castShadows,
  });
}

/** Roteia tubulação e dutos paramétricos 3D com cotovelos e curvas (Frente 93). */
export function generatePipeRoute(routePoints, outerDiameterMm = 114.3, wallThicknessMm = 6.02, radialSegments = 16, bendRadiusFactor = 1.5) {
  return postJson("/api/v1/scene/mep/piping-route", "POST", {
    route_points: routePoints,
    outer_diameter_mm: outerDiameterMm,
    wall_thickness_mm: wallThicknessMm,
    radial_segments: radialSegments,
    bend_radius_factor: bendRadiusFactor,
  });
}

/** Gera trajetória cinematográfica contínua de câmera (Orbit ou Flythrough) (Frente 94). */
export function generateCameraAnimationPath(mode = "ORBIT", targetPoint = [0, 0, 0], radiusM = 10.0, heightM = 3.5, startAngleDeg = 0.0, totalRotationDeg = 360.0, waypoints = null, durationSeconds = 10.0, fps = 30, fovDeg = 45.0) {
  return postJson("/api/v1/scene/animation/camera-path", "POST", {
    mode,
    target_point: targetPoint,
    radius_m: radiusM,
    height_m: heightM,
    start_angle_deg: startAngleDeg,
    total_rotation_deg: totalRotationDeg,
    waypoints,
    duration_seconds: durationSeconds,
    fps,
    fov_deg: fovDeg,
  });
}

/** Processa peças e produz tabela industrial de corte CNC com CSV (Frente 95). */
export function generateCncCutlist(parts, sawKerfMm = 4.0, trimMarginMm = 15.0, exportCsv = true) {
  return postJson("/api/v1/scene/factory/cutlist-cnc", "POST", {
    parts,
    saw_kerf_mm: sawKerfMm,
    trim_margin_mm: trimMarginMm,
    export_csv: exportCsv,
  });
}

/** Gera parede paramétrica 3D com vãos de portas e janelas (Frente 96). */
export function generateWallWithOpenings(startPt, endPt, heightM = 2.80, thicknessM = 0.15, openings = null) {
  return postJson("/api/v1/scene/architecture/wall", "POST", {
    start_pt: startPt,
    end_pt: endPt,
    height_m: heightM,
    thickness_m: thicknessM,
    openings,
  });
}

/** Calcula o blank planificado e linhas de dobra DIN 6935 (Frente 97). */
export function unfoldSheetMetal(baseLengthMm, baseWidthMm, thicknessMm = 2.0, innerRadiusMm = 2.0, kFactor = 0.44, flanges = null) {
  return postJson("/api/v1/scene/manufacturing/sheet-metal-unfold", "POST", {
    base_length_mm: baseLengthMm,
    base_width_mm: baseWidthMm,
    thickness_mm: thicknessMm,
    inner_radius_mm: innerRadiusMm,
    k_factor: kFactor,
    flanges,
  });
}

/** Calcula projeção de sombra do oclusor sobre o solo ou superfície (Frente 98). */
export function calculateProjectedShadow(occluderVertices, sunDirection, groundElevationZ = 0.0) {
  return postJson("/api/v1/scene/shadows/projected-surface", "POST", {
    occluder_vertices: occluderVertices,
    sun_direction: sunDirection,
    ground_elevation_z: groundElevationZ,
  });
}

/** Configura shader PBR de água, ondas Gerstner e cáusticas (Frente 99). */
export function configureWaterSurface(shallowColorHex = "#4db5ff", deepColorHex = "#004080", clarityPercent = 85.0, waveAmplitudeM = 0.05, waveWavelengthM = 1.2, waveSpeedMS = 1.0, ior = 1.333, causticsIntensity = 0.75, enableFoam = true) {
  return postJson("/api/v1/scene/materials/water-pbr", "POST", {
    shallow_color_hex: shallowColorHex,
    deep_color_hex: deepColorHex,
    clarity_percent: clarityPercent,
    wave_amplitude_m: waveAmplitudeM,
    wave_wavelength_m: waveWavelengthM,
    wave_speed_m_s: waveSpeedMS,
    ior,
    caustics_intensity: causticsIntensity,
    enable_foam: enableFoam,
  });
}

/** Gera cadeia de 3 níveis de detalhe (LOD0, LOD1, LOD2) para Three.js (Frente 100). */
export function generateMeshLodChain(vertices, triangles, lod1TargetRatio = 0.50, lod2TargetRatio = 0.25) {
  return postJson("/api/v1/scene/geometry/lod-chain", "POST", {
    vertices,
    triangles,
    lod1_target_ratio: lod1TargetRatio,
    lod2_target_ratio: lod2TargetRatio,
  });
}

/** Gera escada paramétrica 3D com ergonomia de Blondel NBR 9050 (Frente 101). */
export function generateStair(totalHeightM = 2.80, stairWidthM = 1.0, stairType = "STRAIGHT", originXyz = [0, 0, 0], addHandrail = true) {
  return postJson("/api/v1/scene/architecture/stair", "POST", {
    total_height_m: totalHeightM,
    stair_width_m: stairWidthM,
    stair_type: stairType,
    origin_xyz: originXyz,
    add_handrail: addHandrail,
  });
}

/** Gera painel arquitetônico vazado Voronoi 3D paramétrico (Frente 102). */
export function generateVoronoiPanel(widthM = 2.0, heightM = 3.0, thicknessM = 0.05, numSeeds = 25, seedRandomSeed = 42, cellInsetRatio = 0.15) {
  return postJson("/api/v1/scene/architecture/voronoi-panel", "POST", {
    width_m: widthM,
    height_m: heightM,
    thickness_m: thicknessM,
    num_seeds: numSeeds,
    seed_random_seed: seedRandomSeed,
    cell_inset_ratio: cellInsetRatio,
  });
}

/** Calcula pressão dinâmica e forças de arrasto de vento normativo NBR 6123 (Frente 103). */
export function calculateWindPressure(basicSpeedV0 = 45.0, terrainCategory = "IV", buildingHeightM = 12.0, facadeWidthM = 20.0, facadeLengthM = 15.0, s1 = 1.0, s3 = 1.0) {
  return postJson("/api/v1/scene/engineering/wind-pressure", "POST", {
    basic_speed_v0_m_s: basicSpeedV0,
    terrain_category: terrainCategory,
    building_height_m: buildingHeightM,
    facade_width_m: facadeWidthM,
    facade_length_m: facadeLengthM,
    topographic_s1: s1,
    statistical_s3: s3,
  });
}

/** Configura céu físico Rayleigh/Mie e uniformes para Three.js Sky (Frente 104). */
export function configureAtmosphericSky(solarElevationDeg = 35.0, solarAzimuthDeg = 135.0, turbidity = 3.0, rayleigh = 1.2, mieCoefficient = 0.005, mieDirectionalG = 0.82) {
  return postJson("/api/v1/scene/environment/atmospheric-sky", "POST", {
    solar_elevation_deg: solarElevationDeg,
    solar_azimuth_deg: solarAzimuthDeg,
    turbidity,
    rayleigh,
    mie_coefficient: mieCoefficient,
    mie_directional_g: mieDirectionalG,
  });
}

/** Compila modelo geométrico e emite arquivo STEP ISO-10303-21 IFC4 LOD 350 físico (Frente 105). */
export function exportIfc4Bim(projectName = "Projeto Executivo SketchBuild", elements = [], author = "SketchBuild Engineer", organization = "Parkelo & SketchBuild") {
  return postJson("/api/v1/scene/bim/export-ifc4", "POST", {
    project_name: projectName,
    elements,
    author,
    organization,
  });
}

/** Baixa os bytes brutos do modelo .skp atual para gravação in-place com File System Access API. */
export async function downloadCurrentSkpBytes() {
  const res = await fetch("/api/v1/scene/download-skp");
  if (!res.ok) throw new ApiError(res.statusText, res.status);
  return res.blob();
}

/** Simulação temporal de física newtoniana de corpos rígidos (Frente 106). */
export function simulateRigidBodyPhysics(bodies, steps = 60, timeStep = 0.016, gravity = [0, 0, -9.81]) {
  return postJson("/api/v1/scene/physics/simulate-rigid-body", "POST", {
    bodies,
    steps,
    time_step: timeStep,
    gravity,
  });
}

/** Fatiamento 3D FDM e exportação STL/3MF para impressão 3D (Frente 107). */
export function slice3dPrintFdm(geometry, layerHeightMm = 0.2, nozzleDiamMm = 0.4, printSpeedMmS = 50.0, infillPercent = 20.0, infillPattern = "grid", filamentDiamMm = 1.75, exportFormat = "stl_ascii") {
  return postJson("/api/v1/scene/manufacturing/slice-3d-print", "POST", {
    geometry,
    layer_height_mm: layerHeightMm,
    nozzle_diam_mm: nozzleDiamMm,
    print_speed_mm_s: printSpeedMmS,
    infill_percent: infillPercent,
    infill_pattern: infillPattern,
    filament_diam_mm: filamentDiamMm,
    export_format: exportFormat,
  });
}

/** Análise de estabilidade e B-Rep de muro de arrimo NBR 11682 (Frente 108). */
export function calculateRetainingWallStability(wallHeightM = 3.0, topWidthM = 0.3, baseWidthM = 1.8, stemThicknessM = 0.4, toeWidthM = 0.5, heelWidthM = 0.9, soilFrictionAngleDeg = 30.0, soilUnitWeightKnM3 = 18.0, soilCohesionKpa = 0.0, concreteUnitWeightKnM3 = 24.0, surchargeKpa = 5.0, baseFrictionAngleDeg = 25.0) {
  return postJson("/api/v1/scene/geotechnics/retaining-wall", "POST", {
    wall_height_m: wallHeightM,
    top_width_m: topWidthM,
    base_width_m: baseWidthM,
    stem_thickness_m: stemThicknessM,
    toe_width_m: toeWidthM,
    heel_width_m: heelWidthM,
    soil_friction_angle_deg: soilFrictionAngleDeg,
    soil_unit_weight_kn_m3: soilUnitWeightKnM3,
    soil_cohesion_kpa: soilCohesionKpa,
    concrete_unit_weight_kn_m3: concreteUnitWeightKnM3,
    surcharge_kpa: surchargeKpa,
    base_friction_angle_deg: baseFrictionAngleDeg,
  });
}

/** Dimensionamento de rede hidráulica predial NBR 5626 (Frente 109). */
export function calculateHydraulicPiping(pipeSegments = [], fittings = [], waterTempC = 20.0, roughnessC = 140.0, staticPressureMca = 15.0) {
  return postJson("/api/v1/scene/mep/hydraulic-piping", "POST", {
    pipe_segments: pipeSegments,
    fittings,
    water_temp_c: waterTempC,
    roughness_c: roughnessC,
    static_pressure_mca: staticPressureMca,
  });
}

/** Dimensionamento de eletroduto e taxa de ocupação NBR 5410 (Frente 110). */
export function calculateElectricalConduit(conductors = [], conduitNominalMm = 25.0, circuitType = "three_phase", voltageV = 220.0, powerW = 5000.0, powerFactor = 0.92, lengthM = 15.0, maxVoltageDropPct = 4.0, ambientTempC = 30.0) {
  return postJson("/api/v1/scene/mep/electrical-conduit", "POST", {
    conductors,
    conduit_nominal_mm: conduitNominalMm,
    circuit_type: circuitType,
    voltage_v: voltageV,
    power_w: powerW,
    power_factor: powerFactor,
    length_m: lengthM,
    max_voltage_drop_pct: maxVoltageDropPct,
    ambient_temp_c: ambientTempC,
  });
}

/** Conforto térmico, transmitância U e capacidade térmica NBR 15220 (Frente 111). */
export function calculateThermalComfort(envelopeElements = [], roomVolumeM3 = 60.0, airChangesPerHour = 1.5, bioclimaticZone = 3) {
  return postJson("/api/v1/scene/environment/thermal-comfort", "POST", {
    envelope_elements: envelopeElements,
    room_volume_m3: roomVolumeM3,
    air_changes_per_hour: airChangesPerHour,
    bioclimatic_zone: bioclimaticZone,
  });
}

/** Tempo de reverberação RT60 e acústica de salas NBR 10152 (Frente 112). */
export function calculateRoomAcoustics(roomDimensions = [6.0, 4.0, 2.8], surfaceAbsorptions = {}, occupancyPersons = 4, roomUsageType = "classroom") {
  return postJson("/api/v1/scene/environment/room-acoustics", "POST", {
    room_dimensions: roomDimensions,
    surface_absorptions: surfaceAbsorptions,
    occupancy_persons: occupancyPersons,
    room_usage_type: roomUsageType,
  });
}

/** Fator de Luz Diurna FLD % e iluminância natural NBR 15215 (Frente 113). */
export function calculateDaylightFactor(roomDimensions = [5.0, 4.0, 2.8], windows = [], internalReflectances = {}, externalObstructions = {}) {
  return postJson("/api/v1/scene/environment/daylight-factor", "POST", {
    room_dimensions: roomDimensions,
    windows,
    internal_reflectances: internalReflectances,
    external_obstructions: externalObstructions,
  });
}

/** Geração de perfil estrutural metálico NBR 8800 (Frente 114). */
export function generateSteelProfile(profileType = "w_shape", depthMm = 200.0, widthMm = 100.0, webThicknessMm = 5.5, flangeThicknessMm = 8.0, lengthMm = 3000.0, steelGrade = "ASTM A572 Gr 50") {
  return postJson("/api/v1/scene/structures/steel-profile", "POST", {
    profile_type: profileType,
    depth_mm: depthMm,
    width_mm: widthMm,
    web_thickness_mm: webThicknessMm,
    flange_thickness_mm: flangeThicknessMm,
    length_mm: lengthMm,
    steel_grade: steelGrade,
  });
}

/** Orçamento paramétrico BIM 5D com SINAPI e curva ABC (Frente 115). */
export function calculateBim5dSinapiBudget(budgetItems = [], bdiRatePct = 24.5, uf = "SP") {
  return postJson("/api/v1/scene/bim/5d-sinapi-budget", "POST", {
    budget_items: budgetItems,
    bdi_rate_pct: bdiRatePct,
    uf,
  });
}

// ----------------------------------------------------------------------------
// Frentes 116 a 145: Funções Client API
// ----------------------------------------------------------------------------
export function calculateStormwaterDrainage(roofAreaM2 = 120.0, rainfallIntensityMmH = 150.0) {
  return postJson("/api/v1/scene/mep/stormwater-drainage", "POST", { roof_area_m2: roofAreaM2, rainfall_intensity_mm_h: rainfallIntensityMmH });
}

export function calculatePermeablePavement(pavementAreaM2 = 250.0, designRainfallMm = 60.0) {
  return postJson("/api/v1/scene/environment/permeable-pavement", "POST", { pavement_area_m2: pavementAreaM2, design_rainfall_mm: designRainfallMm });
}

export function calculateSewerNetwork(pipeDiameterDnMm = 150.0, flowRateLS = 2.5) {
  return postJson("/api/v1/scene/mep/sewer-network", "POST", { pipe_diameter_dn_mm: pipeDiameterDnMm, flow_rate_l_s: flowRateLS });
}

export function calculateDetentionBasin(catchmentAreaHa = 5.0, allowableOutflowLS = 250.0) {
  return postJson("/api/v1/scene/hydrology/detention-basin", "POST", { catchment_area_ha: catchmentAreaHa, allowable_outflow_l_s: allowableOutflowLS });
}

export function calculateEarthworkBruckner(crossSections = null, bulkingFactor = 1.25) {
  return postJson("/api/v1/scene/infrastructure/earthwork-bruckner", "POST", { cross_sections: crossSections, bulking_factor: bulkingFactor });
}

export function calculateSlopeStabilityBishop(slopeHeightM = 8.0, slopeAngleDeg = 35.0) {
  return postJson("/api/v1/scene/geotechnics/slope-stability-bishop", "POST", { slope_height_m: slopeHeightM, slope_angle_deg: slopeAngleDeg });
}

export function calculateDeepFoundationsPiles(columnAxialLoadKn = 1800.0, pileDiameterMm = 500.0) {
  return postJson("/api/v1/scene/geotechnics/deep-foundations-piles", "POST", { column_axial_load_kn: columnAxialLoadKn, pile_diameter_mm: pileDiameterMm });
}

export function calculateShallowFootings(columnLoadKn = 650.0, soilAllowableStressMpa = 0.20) {
  return postJson("/api/v1/scene/structures/shallow-footings", "POST", { column_load_kn: columnLoadKn, soil_allowable_stress_mpa: soilAllowableStressMpa });
}

export function calculateGabionWall(wallHeightM = 4.0, baseWidthM = 2.5) {
  return postJson("/api/v1/scene/geotechnics/gabion-wall", "POST", { wall_height_m: wallHeightM, base_width_m: baseWidthM });
}

export function calculateConcreteFormwork(elementType = "COLUMN", heightOrSpanM = 3.20) {
  return postJson("/api/v1/scene/structures/concrete-formwork", "POST", { element_type: elementType, height_or_span_m: heightOrSpanM });
}

export function calculateReinforcedConcreteBeam(bendingMomentMkKnM = 120.0, shearForceVkKn = 85.0) {
  return postJson("/api/v1/scene/structures/reinforced-concrete-beam", "POST", { bending_moment_mk_kn_m: bendingMomentMkKnM, shear_force_vk_kn: shearForceVkKn });
}

export function calculateWaffleSlab(spanXM = 8.0, spanYM = 8.0) {
  return postJson("/api/v1/scene/structures/waffle-slab", "POST", { span_x_m: spanXM, span_y_m: spanYM });
}

export function calculatePrestressedConcrete(beamSpanM = 16.0, strandsCount = 8) {
  return postJson("/api/v1/scene/structures/prestressed-concrete", "POST", { beam_span_m: beamSpanM, strands_count: strandsCount });
}

export function calculateGlulamTimber(spanM = 9.0, distributedLoadKnM = 12.0) {
  return postJson("/api/v1/scene/structures/glulam-timber", "POST", { span_m: spanM, distributed_load_kn_m: distributedLoadKnM });
}

export function generateSpaceTruss(spanXM = 12.0, spanYM = 12.0) {
  return postJson("/api/v1/scene/structures/space-truss", "POST", { span_x_m: spanXM, span_y_m: spanYM });
}

export function calculateFuelGasPiping(totalPowerKw = 75.0, pipeLengthM = 25.0) {
  return postJson("/api/v1/scene/mep/fuel-gas-piping", "POST", { total_power_kw: totalPowerKw, pipe_length_m: pipeLengthM });
}

export function calculateLightningSpda(buildingWidthM = 20.0, buildingLengthM = 30.0, buildingHeightM = 18.0) {
  return postJson("/api/v1/scene/mep/lightning-spda", "POST", { building_width_m: buildingWidthM, building_length_m: buildingLengthM, building_height_m: buildingHeightM });
}

export function calculateFireEgress(floorPopulationPersons = 180, longestTravelDistanceM = 38.0) {
  return postJson("/api/v1/scene/safety/fire-egress", "POST", { floor_population_persons: floorPopulationPersons, longest_travel_distance_m: longestTravelDistanceM });
}

export function calculateHvacCoolingLoad(floorAreaM2 = 80.0, occupantsCount = 8) {
  return postJson("/api/v1/scene/mep/hvac-cooling-load", "POST", { floor_area_m2: floorAreaM2, occupants_count: occupantsCount });
}

export function calculatePhotometricLighting(roomLengthM = 10.0, roomWidthM = 6.0, targetLux = 500.0) {
  return postJson("/api/v1/scene/lighting/photometric-lumen", "POST", { room_length_m: roomLengthM, room_width_m: roomWidthM, target_lux: targetLux });
}

export function calculateSolarPv(roofAvailableAreaM2 = 150.0, latitudeDeg = -23.55) {
  return postJson("/api/v1/scene/energy/solar-photovoltaic", "POST", { roof_available_area_m2: roofAvailableAreaM2, latitude_deg: latitudeDeg });
}

export function calculateNaturalVentilation(roomVolumeM3 = 180.0, windSpeedMS = 3.5) {
  return postJson("/api/v1/scene/environment/natural-ventilation", "POST", { room_volume_m3: roomVolumeM3, wind_speed_m_s: windSpeedMS });
}

export function generateGlazingFenestration(fenestrationType = "CURTAIN_WALL", widthM = 3.0, heightM = 2.60) {
  return postJson("/api/v1/scene/architecture/glazing-fenestration", "POST", { fenestration_type: fenestrationType, width_m: widthM, height_m: heightM });
}

export function calculateVentilatedFacade(facadeHeightM = 15.0, facadeWidthM = 20.0) {
  return postJson("/api/v1/scene/architecture/ventilated-facade", "POST", { facade_height_m: facadeHeightM, facade_width_m: facadeWidthM });
}

export function simulateWindCfd2d(buildingWidthM = 12.0, windInflowSpeedMS = 10.0) {
  return postJson("/api/v1/scene/aerodynamics/mini-wind-cfd-2d", "POST", { building_width_m: buildingWidthM, wind_inflow_speed_m_s: windInflowSpeedMS });
}

export function generateBim4dSchedule(projectStartDate = "2026-11-01", totalBudgetBrl = 450000.0) {
  return postJson("/api/v1/scene/bim/4d-gantt-schedule", "POST", { project_start_date: projectStartDate, total_budget_brl: totalBudgetBrl });
}

export function generateBim7dCobie(facilityName = "Edifício Corporativo SketchBuild") {
  return postJson("/api/v1/scene/bim/7d-cobie-assets", "POST", { facility_name: facilityName });
}

export function calculateSiteLogistics(siteWidthM = 60.0, siteLengthM = 80.0, dailyWorkersCount = 65) {
  return postJson("/api/v1/scene/safety/construction-site-logistics", "POST", { site_width_m: siteWidthM, site_length_m: siteLengthM, daily_workers_count: dailyWorkersCount });
}

export function auditUniversalAccessibility(doorClearWidthCm = 85.0, rampSlopePercent = 8.33) {
  return postJson("/api/v1/scene/accessibility/universal-audit", "POST", { door_clear_width_cm: doorClearWidthCm, ramp_slope_percent: rampSlopePercent });
}

export function calculateLcaEmissions(grossFloorAreaM2 = 850.0, buildingLifespanYears = 50) {
  return postJson("/api/v1/scene/sustainability/lca-emissions", "POST", { gross_floor_area_m2: grossFloorAreaM2, building_lifespan_years: buildingLifespanYears });
}


// ============================================================================
// OPÇÃO A: FUNÇÕES NATIVAS DO SKETCHUP
// ============================================================================

export function positionCameraNative(eyeX = 0.0, eyeY = -5.0, eyeZ = 0.0, targetX = 0.0, targetY = 0.0, targetZ = 1.0, eyeHeightM = 1.68) {
  return postJson("/api/v1/scene/camera/position-camera", "POST", {
    eye_x: eyeX, eye_y: eyeY, eye_z: eyeZ,
    target_x: targetX, target_y: targetY, target_z: targetZ,
    eye_height_m: eyeHeightM, use_eye_height_offset: true
  });
}

export function lookAroundNative(eye = [0.0, -5.0, 1.68], currentYawDeg = 0.0, currentPitchDeg = 0.0, deltaYawDeg = 5.0, deltaPitchDeg = 0.0) {
  return postJson("/api/v1/scene/camera/look-around", "POST", {
    eye: eye,
    current_yaw_deg: currentYawDeg,
    current_pitch_deg: currentPitchDeg,
    delta_yaw_deg: deltaYawDeg,
    delta_pitch_deg: deltaPitchDeg,
    target_distance_m: 10.0
  });
}

export function walkStepNative(currentEye = [0.0, -5.0, 1.68], yawDeg = 0.0, moveForward = 0.5, moveStrafe = 0.0, obstaclesAabb = null, terrainZ = null, eyeHeightM = 1.68) {
  return postJson("/api/v1/scene/camera/walk-step", "POST", {
    current_eye: currentEye,
    yaw_deg: yawDeg,
    move_forward: moveForward,
    move_strafe: moveStrafe,
    obstacles_aabb: obstaclesAabb,
    terrain_elevation_z: terrainZ,
    eye_height_m: eyeHeightM,
    enable_collision: true
  });
}

export function sandboxSmoove(vertices = [], centerX = 0.0, centerY = 0.0, radiusM = 5.0, offsetZM = 1.5) {
  return postJson("/api/v1/scene/sandbox/smoove", "POST", {
    vertices: vertices,
    center_x: centerX,
    center_y: centerY,
    radius_m: radiusM,
    offset_z_m: offsetZM
  });
}

export function sandboxStamp(vertices = [], footprintPoly = [], plateauElevationZ = 1.0, skirtOffsetM = 1.5) {
  return postJson("/api/v1/scene/sandbox/stamp", "POST", {
    vertices: vertices,
    footprint_poly: footprintPoly,
    plateau_elevation_z: plateauElevationZ,
    skirt_offset_m: skirtOffsetM
  });
}

export function sandboxDrape(pathPoints2d = [], triangles = []) {
  return postJson("/api/v1/scene/sandbox/drape", "POST", {
    path_points_2d: pathPoints2d,
    triangles: triangles
  });
}

export function sandboxFlipEdge(triA, triB) {
  return postJson("/api/v1/scene/sandbox/flip-edge", "POST", {
    tri_a: triA,
    tri_b: triB
  });
}

export function matchPhotoCalibrate(imageWidthPx = 1920, imageHeightPx = 1080, redLine1, redLine2, greenLine1, greenLine2, refHeightM = 3.0) {
  return postJson("/api/v1/scene/match-photo/calibrate", "POST", {
    image_width_px: imageWidthPx,
    image_height_px: imageHeightPx,
    red_line_1: redLine1,
    red_line_2: redLine2,
    green_line_1: greenLine1,
    green_line_2: greenLine2,
    reference_height_m: refHeightM
  });
}

export function watermarkStyleConfigure(name = "Selo Oficial", imageUrl = "/static/watermarks/parkelo_stamp.png", layer = "overlay", placement = "screen_position", anchor = "bottom-right", opacityPct = 85.0) {
  return postJson("/api/v1/scene/styles/watermark", "POST", {
    name: name,
    image_url: imageUrl,
    layer: layer,
    placement: placement,
    anchor: anchor,
    opacity_pct: opacityPct,
    scale_pct: 100.0,
    lock_aspect_ratio: true,
    blend_mode: "normal",
    offset_px: [20, 20]
  });
}

export function dynamicComponentInteract(instanceId = "inst_1", dynamicAttributes = {}, onclickFormula = null) {
  return postJson("/api/v1/scene/components/interact", "POST", {
    instance_id: instanceId,
    dynamic_attributes: dynamicAttributes,
    onclick_formula: onclickFormula
  });
}

export function trimbleSolidToolsExecute(operation = "subtract", solidA, solidB) {
  return postJson("/api/v1/scene/solid-tools/execute", "POST", {
    operation: operation,
    solid_a: solidA,
    solid_b: solidB
  });
}


// ============================================================================
// OPÇÃO A (PARTE 2): CLIENT API DAS FERRAMENTAS NATIVAS ADICIONAIS DO SKETCHUP
// ============================================================================

export function ifcClassifyComponent(instanceId = "inst_1", definitionName = "Viga", schemaName = "IFC4", ifcClass = "IfcBeam", predefinedType = "NOTDEFINED", description = "", tag = null) {
  return postJson("/api/v1/scene/bim/ifc/classify", "POST", {
    instance_id: instanceId,
    definition_name: definitionName,
    schema_name: schemaName,
    ifc_class: ifcClass,
    predefined_type: predefinedType,
    description: description,
    tag: tag
  });
}

export function ifcAuditClassifications(instances = []) {
  return postJson("/api/v1/scene/bim/ifc/audit", "POST", { instances: instances });
}

export function generate3dText(text = "SKETCHBUILD", fontFamily = "Arial", heightM = 0.30, extrusionDepthM = 0.05, isFilled = true, isExtruded = true, alignment = "left", originXyz = [0, 0, 0]) {
  return postJson("/api/v1/scene/geometry/3d-text", "POST", {
    text: text,
    font_family: fontFamily,
    height_m: heightM,
    extrusion_depth_m: extrusionDepthM,
    is_filled: isFilled,
    is_extruded: isExtruded,
    alignment: alignment,
    origin_xyz: originXyz
  });
}

export function generateReport(instances = [], scope = "entire_model", groupByDefinition = true, selectedInstanceIds = null) {
  return postJson("/api/v1/scene/reports/generate", "POST", {
    instances: instances,
    scope: scope,
    group_by_definition: groupByDefinition,
    selected_instance_ids: selectedInstanceIds
  });
}

export function axesSetCustom(origin = [0, 0, 0], xPoint = [1, 0, 0], yPoint = [0, 1, 0]) {
  return postJson("/api/v1/scene/axes/custom", "POST", {
    origin: origin,
    x_point: xPoint,
    y_point: yPoint
  });
}

export function axesAlignToFace(faceVertices = []) {
  return postJson("/api/v1/scene/axes/align-face", "POST", { face_vertices: faceVertices });
}

export function axesReset() {
  return postJson("/api/v1/scene/axes/reset", "POST", {});
}

export function inspectEntityEdge(v1, v2, isSmooth = false, isSoft = false, isHidden = false, tag = "Layer0") {
  return postJson("/api/v1/scene/entity-info/edge", "POST", {
    v1: v1, v2: v2,
    is_smooth: isSmooth, is_soft: isSoft, is_hidden: isHidden, tag: tag
  });
}

export function inspectEntityFace(vertices, frontMaterial = null, backMaterial = null, tag = "Layer0") {
  return postJson("/api/v1/scene/entity-info/face", "POST", {
    vertices: vertices,
    front_material: frontMaterial,
    back_material: backMaterial,
    tag: tag
  });
}

export function inspectEntitySolid(definitionName = "Componente", instanceName = "inst_1", triangles = [], tag = "Layer0", dynamicAttributes = null) {
  return postJson("/api/v1/scene/entity-info/solid", "POST", {
    definition_name: definitionName,
    instance_name: instanceName,
    triangles: triangles,
    tag: tag,
    dynamic_attributes: dynamicAttributes
  });
}

export function componentEditModeApply(activeInstanceId = null, activeDefinitionName = null, allInstances = [], hideRest = false, hideSimilar = false, fadeRest = true, fadeSimilar = true, fadeOpacity = 0.25) {
  return postJson("/api/v1/scene/components/edit-mode", "POST", {
    active_instance_id: activeInstanceId,
    active_definition_name: activeDefinitionName,
    all_instances: allInstances,
    hide_rest_of_model: hideRest,
    hide_similar_components: hideSimilar,
    fade_rest_of_model: fadeRest,
    fade_similar_components: fadeSimilar,
    fade_opacity: fadeOpacity
  });
}

export function modelUnitsConfigure(formatType = "DECIMAL", unitLength = "METERS", precisionDigits = 2, enableLengthSnap = true, lengthSnapInterval = 0.01, enableAngleSnap = true, angleSnapDeg = 15.0) {
  return postJson("/api/v1/scene/units/configure", "POST", {
    format_type: formatType,
    unit_length: unitLength,
    precision_digits: precisionDigits,
    enable_length_snapping: enableLengthSnap,
    length_snap_interval_m: lengthSnapInterval,
    enable_angle_snapping: enableAngleSnap,
    angle_snap_degrees: angleSnapDeg
  });
}

export function modelUnitsFormat(lengthMeters = 1.0, unit = "METERS", precisionDigits = 2) {
  return postJson("/api/v1/scene/units/format", "POST", {
    length_meters: lengthMeters,
    unit: unit,
    precision_digits: precisionDigits
  });
}


// ============================================================================
// OPÇÃO A (PARTE 3): CLIENT API DAS FERRAMENTAS NATIVAS ADICIONAIS DO SKETCHUP
// ============================================================================

export function texturePinTransform(faceVertices = [], redPinOrigin = [0, 0], greenPinScaleRot = [1.0, 0.0], bluePinShear = 0.0, yellowPinDistortion = null) {
  return postJson("/api/v1/scene/textures/pin-transform", "POST", {
    face_vertices: faceVertices,
    red_pin_origin: redPinOrigin,
    green_pin_scale_rot: greenPinScaleRot,
    blue_pin_shear: bluePinShear,
    yellow_pin_distortion: yellowPinDistortion
  });
}

export function colorByTagApply(tags = [], instances = [], enabled = true) {
  return postJson("/api/v1/scene/styles/color-by-tag", "POST", {
    tags: tags,
    instances: instances,
    enabled: enabled
  });
}

export function purgeUnusedItems(componentDefinitions = [], instances = [], materials = [], tags = []) {
  return postJson("/api/v1/scene/cleanup/purge-unused", "POST", {
    component_definitions: componentDefinitions,
    instances: instances,
    materials: materials,
    tags: tags
  });
}

export function makeComponentDefinition(definitionName = "Novo Componente", description = "", glueTo = "NONE", cutOpening = false, alwaysFaceCamera = false, shadowsFaceSun = false, localOrigin = [0, 0, 0], openingLoop2d = null) {
  return postJson("/api/v1/scene/components/make-component", "POST", {
    definition_name: definitionName,
    description: description,
    glue_to: glueTo,
    cut_opening: cutOpening,
    always_face_camera: alwaysFaceCamera,
    shadows_face_sun: shadowsFaceSun,
    local_origin: localOrigin,
    opening_loop_2d: openingLoop2d
  });
}

export function advancedSelectionExecute(operation = "invert", allEntityIds = [], currentlySelectedIds = [], targetTag = null, targetMaterial = null, instances = [], seedFaceIndex = 0, facesVertices = []) {
  return postJson("/api/v1/scene/selection/advanced", "POST", {
    operation: operation,
    all_entity_ids: allEntityIds,
    currently_selected_ids: currentlySelectedIds,
    target_tag: targetTag,
    target_material: targetMaterial,
    instances: instances,
    seed_face_index: seedFaceIndex,
    faces_vertices: facesVertices
  });
}

export function hiddenGeometryConfigure(showHiddenGeometry = false, showHiddenObjects = false, instances = null, edges = null) {
  return postJson("/api/v1/scene/styles/hidden-geometry", "POST", {
    show_hidden_geometry: showHiddenGeometry,
    show_hidden_objects: showHiddenObjects,
    instances: instances,
    edges: edges
  });
}

export function modelStatisticsCalculate(params = {}) {
  return postJson("/api/v1/scene/model/statistics", "POST", params);
}
