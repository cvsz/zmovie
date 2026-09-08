const $ = (selector) => document.querySelector(selector);

const generateButton = $("#generate");
const refreshButton = $("#refresh-history");
const statusEl = $("#status");
const resultsEl = $("#results");
const historyEl = $("#history-list");

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderParams(params) {
  return Object.entries(params)
    .map(([key, value]) => `<div class="param"><strong>${escapeHtml(key.replaceAll("_", " "))}</strong><br>${escapeHtml(value)}</div>`)
    .join("");
}

function renderResult(item) {
  const variations = (item.variation_ideas || []).map((x, i) => `${i + 1}. ${x}`).join("\n");
  return `
    <article class="card">
      <div class="card-head">
        <div>
          <p class="eyebrow">GENERATION${item.history_id ? ` #${item.history_id}` : ""}</p>
          <h2>${escapeHtml(item.title)}</h2>
        </div>
      </div>
      <div class="card-body">
        <div class="block">
          <div class="block-head"><h3>MAIN PROMPT</h3><button class="copy" data-copy="main">Copy</button></div>
          <pre data-value="main">${escapeHtml(item.main_prompt)}</pre>
        </div>
        <div class="block">
          <div class="block-head"><h3>NEGATIVE PROMPT</h3><button class="copy" data-copy="negative">Copy</button></div>
          <pre data-value="negative">${escapeHtml(item.negative_prompt)}</pre>
        </div>
        <div class="block">
          <h3>PARAMETER BREAKDOWN</h3>
          <div class="params">${renderParams(item.parameter_breakdown)}</div>
        </div>
        <div class="block">
          <h3>VARIATION IDEAS</h3>
          <pre>${escapeHtml(variations)}</pre>
        </div>
      </div>
    </article>`;
}

async function copyText(card, name, button) {
  const node = card.querySelector(`[data-value="${name}"]`);
  if (!node) return;
  await navigator.clipboard.writeText(node.textContent);
  const original = button.textContent;
  button.textContent = "Copied";
  setTimeout(() => { button.textContent = original; }, 900);
}

resultsEl.addEventListener("click", (event) => {
  const button = event.target.closest("[data-copy]");
  if (!button) return;
  copyText(button.closest(".card"), button.dataset.copy, button).catch(() => {
    statusEl.textContent = "Clipboard access was blocked by the browser.";
  });
});

async function generate() {
  generateButton.disabled = true;
  statusEl.textContent = "Generating…";
  try {
    const seedRaw = $("#seed").value.trim();
    const count = Number.parseInt($("#count").value, 10) || 1;
    const payload = {
      count: Math.min(Math.max(count, 1), 20),
      seed: seedRaw === "" ? null : Number.parseInt(seedRaw, 10),
      save_history: $("#history").checked,
    };

    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const data = await response.json();
    resultsEl.innerHTML = data.results.map(renderResult).join("");
    statusEl.textContent = `Generated ${data.count} prompt${data.count === 1 ? "" : "s"}${data.seed === null ? "" : ` with seed ${data.seed}`}.`;
    if (payload.save_history) await loadHistory();
  } catch (error) {
    statusEl.textContent = `Generation failed: ${error.message}`;
  } finally {
    generateButton.disabled = false;
  }
}

async function loadHistory() {
  try {
    const response = await fetch("/api/history?limit=20");
    if (!response.ok) throw new Error(`API returned ${response.status}`);
    const data = await response.json();
    if (!data.items.length) {
      historyEl.innerHTML = '<div class="empty">No saved generations yet.</div>';
      return;
    }
    historyEl.innerHTML = data.items.map((item) => `
      <div class="history-item">
        <div>
          <strong>${escapeHtml(item.title)}</strong>
          <div class="history-meta">#${item.id} · ${escapeHtml(item.created_at)} · seed ${item.seed ?? "random"}</div>
        </div>
      </div>`).join("");
  } catch (error) {
    historyEl.innerHTML = `<div class="empty">History unavailable: ${escapeHtml(error.message)}</div>`;
  }
}

generateButton.addEventListener("click", generate);
refreshButton.addEventListener("click", loadHistory);
loadHistory();
