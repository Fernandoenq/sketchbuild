// Monta a grade "Arquivos recentes" da tela de Pagina Inicial -- nenhuma
// chamada de rede aqui, so manipulacao de DOM a partir do DTO que ja veio
// de GET /api/v1/recent-files (ver api.js). Mesmo padrao do outliner.js:
// modulo puro de construcao de DOM, a orquestracao (fetch, show/hide, abrir
// o arquivo clicado) fica em main.js.

/** Icone generico (placeholder) pra arquivos que ainda nao tem thumbnail
 * real (nenhuma sessao desta app os abriu ainda pra capturar o snapshot). */
const PLACEHOLDER_ICON_SVG = `
  <svg viewBox="0 0 24 24" class="recent-card-placeholder-icon">
    <polygon points="12,3 20,7.5 20,16.5 12,21 4,16.5 4,7.5" />
    <line x1="12" y1="3" x2="12" y2="12" />
    <line x1="4" y1="7.5" x2="12" y2="12" />
    <line x1="20" y1="7.5" x2="12" y2="12" />
  </svg>
`;

function formatDateTime(isoString) {
  if (!isoString) return "";
  try {
    return new Date(isoString).toLocaleString("pt-BR", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

/**
 * @param {HTMLElement} container - onde a grade e renderizada (limpo antes)
 * @param {Array<object>} entries - lista de RecentFileEntry (ver schemas/recent_files.py)
 * @param {(path: string) => void} onOpen - chamado ao clicar num card
 */
export function renderRecentFiles(container, entries, onOpen) {
  container.innerHTML = "";

  if (!entries.length) {
    const emptyEl = document.createElement("div");
    emptyEl.className = "welcome-recent-empty";
    emptyEl.textContent = "Nenhum arquivo aberto por este app ainda.";
    container.appendChild(emptyEl);
    return;
  }

  for (const entry of entries) {
    const card = document.createElement("div");
    card.className = "recent-card";
    card.title = entry.path;

    const thumbEl = document.createElement("div");
    thumbEl.className = "recent-card-thumb";
    if (entry.thumbnail_url) {
      const img = document.createElement("img");
      img.src = entry.thumbnail_url;
      img.alt = entry.name;
      thumbEl.appendChild(img);
    } else {
      thumbEl.innerHTML = PLACEHOLDER_ICON_SVG;
    }

    const nameEl = document.createElement("div");
    nameEl.className = "recent-card-name";
    nameEl.textContent = entry.name;

    const dateEl = document.createElement("div");
    dateEl.className = "recent-card-date";
    dateEl.textContent = entry.last_modified
      ? `Ultima alteracao: ${formatDateTime(entry.last_modified)}`
      : "Arquivo nao encontrado no disco";

    card.appendChild(thumbEl);
    card.appendChild(nameEl);
    card.appendChild(dateEl);
    card.addEventListener("click", () => onOpen(entry.path));

    container.appendChild(card);
  }
}

/**
 * Monta a grade "Recuperar sessão não salva" (rascunhos reais de
 * autosave, ver app/repositories/autosave_repository.py) -- cada card
 * tem botão Recuperar (reabre a sessão com as edições ainda não salvas)
 * e Descartar (apaga o rascunho sem recuperar), diferente de
 * renderRecentFiles() que só abre com um clique no card inteiro.
 * @param {HTMLElement} container
 * @param {Array<object>} entries - lista de AutosaveDraftDTO (ver schemas/scene.py)
 * @param {(draftId: string) => void} onRecover
 * @param {(draftId: string) => void} onDiscard
 */
export function renderAutosaveDrafts(container, entries, onRecover, onDiscard) {
  container.innerHTML = "";

  for (const entry of entries) {
    const card = document.createElement("div");
    card.className = "recent-card autosave-card";
    card.title = entry.original_path;

    const thumbEl = document.createElement("div");
    thumbEl.className = "recent-card-thumb";
    thumbEl.innerHTML = PLACEHOLDER_ICON_SVG;

    const nameEl = document.createElement("div");
    nameEl.className = "recent-card-name";
    nameEl.textContent = entry.name;

    const dateEl = document.createElement("div");
    dateEl.className = "recent-card-date";
    dateEl.textContent = `Nao salvo -- rascunho de ${formatDateTime(entry.saved_at)}`;

    const actionsEl = document.createElement("div");
    actionsEl.className = "autosave-card-actions";

    const recoverBtn = document.createElement("button");
    recoverBtn.textContent = "Recuperar";
    recoverBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      onRecover(entry.id);
    });

    const discardBtn = document.createElement("button");
    discardBtn.textContent = "Descartar";
    discardBtn.className = "autosave-discard-btn";
    discardBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      onDiscard(entry.id);
    });

    actionsEl.appendChild(recoverBtn);
    actionsEl.appendChild(discardBtn);

    card.appendChild(thumbEl);
    card.appendChild(nameEl);
    card.appendChild(dateEl);
    card.appendChild(actionsEl);

    container.appendChild(card);
  }
}
