// Agrupa botões que já existem na barra de ferramentas em botões com seta (flyout), como no SketchUp: o botão
// principal mostra e ativa a última ferramenta usada do grupo e a seta abre a lista com todas.
// Os botões originais são movidos para a lista (os ouvintes de clique e o data-tool-mode continuam valendo).

const SETA = "▾";

function rotuloDe(b) {
  return (b.getAttribute("aria-label") || b.title || "").trim();
}

export function agruparBotoes(nome, botoes) {
  botoes = botoes.filter(Boolean);
  if (botoes.length < 2) return null;
  const caixa = document.createElement("div");
  caixa.className = "tool-group-split";
  const principal = document.createElement("button");
  principal.className = "toolbar-btn tool-icon-btn tool-group-main";
  const seta = document.createElement("button");
  seta.className = "toolbar-btn tool-group-arrow";
  seta.textContent = SETA;
  seta.title = `${nome}: escolher a ferramenta`;
  seta.setAttribute("aria-label", seta.title);
  seta.setAttribute("aria-haspopup", "true");
  const lista = document.createElement("div");
  lista.className = "tool-group-menu";
  lista.hidden = true;

  botoes[0].parentNode.insertBefore(caixa, botoes[0]);
  let atual = botoes.find((b) => !b.disabled) || botoes[0];
  const mostrar = (b) => {
    atual = b;
    principal.innerHTML = b.querySelector("svg")?.outerHTML ?? "";
    principal.title = b.title || rotuloDe(b);
    principal.setAttribute("aria-label", rotuloDe(b));
    principal.disabled = b.disabled;
    principal.classList.toggle("disabled", b.disabled);
  };
  mostrar(atual);
  for (const b of botoes) {
    const texto = document.createElement("span");
    texto.textContent = rotuloDe(b);
    b.appendChild(texto);
    b.classList.add("tool-group-item");
    lista.appendChild(b);
    b.addEventListener("click", () => {
      lista.hidden = true;
      mostrar(b);
    });
  }
  const fechar = () => {
    lista.hidden = true;
  };
  principal.addEventListener("click", () => atual.click());
  seta.addEventListener("click", (e) => {
    e.stopPropagation();
    lista.hidden = !lista.hidden;
    if (!lista.hidden) {
      const r = principal.getBoundingClientRect();
      lista.style.left = `${r.left}px`;
      lista.style.top = `${r.bottom + 2}px`;
    }
  });
  document.addEventListener("click", fechar);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") fechar();
  });
  // quando o modo da ferramenta muda por atalho, o principal acompanha a que estiver ativa
  setInterval(() => {
    const viva = botoes.find((b) => b.classList.contains("active"));
    if (viva && viva !== atual) mostrar(viva);
    principal.classList.toggle("active", !!viva);
  }, 300);
  caixa.append(principal, seta, lista);
  return caixa;
}

// Grupos do SketchUp para os botões antigos da barra (Construção e Câmera).
export function agruparBarraAntiga(barra) {
  const por = (sel) => barra.querySelector(sel);
  agruparBotoes("Construção", [
    por('[data-action="tool-measure"]'),
    por('[data-action="tool-dimension"]'),
    por('[data-action="tool-protractor"]'),
    por('[data-action="tool-text"]'),
    por('[data-action="tool-axes"]'),
    por('[data-action="tool-text3d"]'),
  ]);
  agruparBotoes("Câmera", [
    por('button[aria-label="Orbitar"]'),
    por('button[aria-label="Panorâmica"]'),
    por('button[aria-label="Zoom"]'),
  ]);
}
