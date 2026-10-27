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
