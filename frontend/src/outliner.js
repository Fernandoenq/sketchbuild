// Monta a arvore do painel "Outliner" (estilo SketchUp) a partir do mesmo
// DTO que o sceneBuilder.js usa pra montar a cena 3D -- nenhuma chamada de
// rede aqui, so manipulacao de DOM. A hierarquia vem do campo
// `parent_instance_id` de cada instancia (ver core/mesh_extractor.py).
//
// `inst_root` (pseudo-instancia sintetica do Entities raiz do Model, sem
// geometria propria) fica oculta -- so os filhos dela aparecem no nivel 0
// da arvore.

/**
 * @param {object} sceneDTO - DTO de /api/v1/scene/open
 * @param {(instanceId: string) => void} onSelect - chamado ao clicar numa linha
 * @returns {{ element: HTMLElement, setSelected: (instanceId: string|null) => void }}
 */
export function buildOutlinerTree(sceneDTO, onSelect) {
  const definitionNameById = new Map(
    sceneDTO.definitions.map((d) => [d.definition_id, d.name])
  );

  const childrenByParentId = new Map();
  for (const instance of sceneDTO.instances) {
    if (instance.instance_id === "inst_root") continue;
    const key = instance.parent_instance_id ?? "inst_root";
    if (!childrenByParentId.has(key)) childrenByParentId.set(key, []);
    childrenByParentId.get(key).push(instance);
  }

  const rowByInstanceId = new Map();
  let selectedRow = null;

  function buildNode(instance) {
    const children = childrenByParentId.get(instance.instance_id) || [];
    const label = definitionNameById.get(instance.definition_id) || instance.definition_id;

    const nodeEl = document.createElement("div");
    nodeEl.className = "outliner-node";

    const rowEl = document.createElement("div");
    rowEl.className = "outliner-row";
    rowEl.title = instance.instance_id;

    const toggleEl = document.createElement("span");
    toggleEl.className = "outliner-toggle";
    toggleEl.textContent = children.length ? "▾" : "";

    const labelEl = document.createElement("span");
    labelEl.className = "outliner-label";
    labelEl.textContent = label;

    rowEl.appendChild(toggleEl);
    rowEl.appendChild(labelEl);
    nodeEl.appendChild(rowEl);
    rowByInstanceId.set(instance.instance_id, rowEl);

    rowEl.addEventListener("click", (event) => {
      event.stopPropagation();
      onSelect(instance.instance_id);
    });

    if (children.length) {
      const childrenEl = document.createElement("div");
      childrenEl.className = "outliner-children";
      for (const child of children) {
        childrenEl.appendChild(buildNode(child));
      }
      nodeEl.appendChild(childrenEl);

      toggleEl.addEventListener("click", (event) => {
        event.stopPropagation();
        childrenEl.classList.toggle("collapsed");
        toggleEl.textContent = childrenEl.classList.contains("collapsed") ? "▸" : "▾";
      });
    }

    return nodeEl;
  }

  const root = document.createElement("div");
  for (const instance of childrenByParentId.get("inst_root") || []) {
    root.appendChild(buildNode(instance));
  }

  function setSelected(instanceId) {
    if (selectedRow) selectedRow.classList.remove("selected");
    selectedRow = instanceId ? rowByInstanceId.get(instanceId) || null : null;
    if (selectedRow) {
      selectedRow.classList.add("selected");
      // expande os pais, se a selecao veio do clique numa peca 3D
      // aninhada dentro de um ramo colapsado
      let parentChildren = selectedRow.closest(".outliner-children");
      while (parentChildren) {
        parentChildren.classList.remove("collapsed");
        const parentRow = parentChildren.previousElementSibling;
        const toggleEl = parentRow?.querySelector(".outliner-toggle");
        if (toggleEl) toggleEl.textContent = "▾";
        parentChildren = parentChildren.parentElement?.closest(".outliner-children");
      }
      selectedRow.scrollIntoView({ block: "nearest" });
    }
  }

  return { element: root, setSelected };
}
