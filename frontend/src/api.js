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
