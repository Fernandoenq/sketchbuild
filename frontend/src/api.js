// Cliente HTTP fino contra o backend FastAPI -- sem logica de UI aqui.

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
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
      detail = errorBody.detail || detail;
    } catch {
      // resposta nao era JSON -- mantem o statusText
    }
    throw new ApiError(detail, res.status);
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

/** `path` vazio/undefined sobrescreve o arquivo que foi aberto. */
export function saveScene(path) {
  return postJson("/api/v1/scene/save", "POST", { path: path || null });
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
