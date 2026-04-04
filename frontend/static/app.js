const state = {
  overview: null,
  documents: [],
  selectedDocument: null,
  runs: [],
  selectedRun: null,
  cards: [],
  improvements: [],
  selectedExport: null,
};

const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  cacheElements();
  bindEvents();
  syncImprovementFields();
  refreshAll();
});

function cacheElements() {
  elements.messageBanner = document.getElementById("message-banner");
  elements.backendStatus = document.getElementById("backend-status");
  elements.overviewContent = document.getElementById("overview-content");
  elements.documentsList = document.getElementById("documents-list");
  elements.documentDetail = document.getElementById("document-detail");
  elements.runDocumentCheckboxes = document.getElementById("run-document-checkboxes");
  elements.runPluginSelect = document.getElementById("run-plugin-select");
  elements.runConfig = document.getElementById("run-config");
  elements.runsList = document.getElementById("runs-list");
  elements.runDetail = document.getElementById("run-detail");
  elements.cardsTableWrapper = document.getElementById("cards-table-wrapper");
  elements.improvementRunId = document.getElementById("improvement-run-id");
  elements.improvementAction = document.getElementById("improvement-action");
  elements.improvementCardId = document.getElementById("improvement-card-id");
  elements.improvementCardIds = document.getElementById("improvement-card-ids");
  elements.improvementFront = document.getElementById("improvement-front");
  elements.improvementBack = document.getElementById("improvement-back");
  elements.improvementRating = document.getElementById("improvement-rating");
  elements.improvementPrompt = document.getElementById("improvement-prompt");
  elements.singleCardField = document.getElementById("single-card-field");
  elements.multiCardField = document.getElementById("multi-card-field");
  elements.frontField = document.getElementById("front-field");
  elements.backField = document.getElementById("back-field");
  elements.ratingField = document.getElementById("rating-field");
  elements.promptField = document.getElementById("prompt-field");
  elements.improvementsList = document.getElementById("improvements-list");
  elements.exportRunId = document.getElementById("export-run-id");
  elements.exporterSelect = document.getElementById("exporter-select");
  elements.exportCardIds = document.getElementById("export-card-ids");
  elements.exportIdInput = document.getElementById("export-id-input");
  elements.exportDetail = document.getElementById("export-detail");
  elements.uploadForm = document.getElementById("upload-form");
  elements.runForm = document.getElementById("run-form");
  elements.improvementForm = document.getElementById("improvement-form");
  elements.exportForm = document.getElementById("export-form");
  elements.exportLookupForm = document.getElementById("export-lookup-form");
  elements.uploadFile = document.getElementById("upload-file");
  elements.uploadTitle = document.getElementById("upload-title");
  elements.uploadSourceType = document.getElementById("upload-source-type");
  elements.uploadDocumentId = document.getElementById("upload-document-id");
}

function bindEvents() {
  document.getElementById("refresh-all-button").addEventListener("click", refreshAll);
  document.getElementById("refresh-overview-button").addEventListener("click", refreshOverview);
  document.getElementById("refresh-documents-button").addEventListener("click", refreshDocuments);
  document.getElementById("refresh-runs-button").addEventListener("click", refreshRuns);
  document
    .getElementById("refresh-improvements-button")
    .addEventListener("click", () => refreshSelectedRunData(false));
  elements.improvementAction.addEventListener("change", syncImprovementFields);
  elements.uploadForm.addEventListener("submit", handleUploadSubmit);
  elements.runForm.addEventListener("submit", handleRunSubmit);
  elements.improvementForm.addEventListener("submit", handleImprovementSubmit);
  elements.exportForm.addEventListener("submit", handleExportSubmit);
  elements.exportLookupForm.addEventListener("submit", handleExportLookupSubmit);
}

async function refreshAll() {
  await Promise.all([refreshOverview(), refreshDocuments(), refreshRuns()]);
  if (state.selectedRun) {
    await refreshSelectedRunData(false);
  }
}

async function refreshOverview() {
  try {
    const [health, overview] = await Promise.all([apiRequest("/api/health"), apiRequest("/api/overview")]);
    state.overview = overview;
    elements.backendStatus.textContent = `Backend ${health.status}`;
    elements.backendStatus.classList.remove("error");
    renderOverview();
    renderPluginOptions();
    renderExporterOptions();
  } catch (err) {
    elements.backendStatus.textContent = "Backend unavailable";
    elements.backendStatus.classList.add("error");
    showMessage(String(err.message || err), "error");
  }
}

async function refreshDocuments() {
  try {
    state.documents = await apiRequest("/api/documents");
    renderDocuments();
    renderRunDocumentCheckboxes();
    if (state.selectedDocument) {
      await loadDocumentDetail(state.selectedDocument.document_id, false);
    }
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function refreshRuns() {
  try {
    state.runs = await apiRequest("/api/runs");
    renderRuns();
    if (state.selectedRun) {
      await refreshSelectedRunData(false);
    }
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function loadDocumentDetail(documentId, announce = true) {
  try {
    state.selectedDocument = await apiRequest(`/api/documents/${encodeURIComponent(documentId)}`);
    renderDocumentDetail();
    if (announce) {
      showMessage(`Loaded document ${documentId}.`, "success");
    }
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function loadRunDetail(runId, announce = true) {
  try {
    state.selectedRun = await apiRequest(`/api/runs/${encodeURIComponent(runId)}`);
    renderRunDetail();
    syncSelectedRunFields();
    if (announce) {
      showMessage(`Loaded run ${runId}.`, "success");
    }
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function refreshSelectedRunData(announce = true) {
  if (!state.selectedRun) {
    return;
  }

  const runId = state.selectedRun.run_id;
  try {
    const [run, cards, improvements] = await Promise.all([
      apiRequest(`/api/runs/${encodeURIComponent(runId)}`),
      apiRequest(`/api/runs/${encodeURIComponent(runId)}/cards`),
      apiRequest(`/api/runs/${encodeURIComponent(runId)}/improvements`),
    ]);
    state.selectedRun = run;
    state.cards = cards;
    state.improvements = improvements;
    renderRunDetail();
    renderCards();
    renderImprovementHistory();
    renderCardSelectors();
    syncSelectedRunFields();
    if (announce) {
      showMessage(`Refreshed run ${runId}.`, "success");
    }
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function loadExportDetail(exportId, announce = true) {
  try {
    state.selectedExport = await apiRequest(`/api/exports/${encodeURIComponent(exportId)}`);
    elements.exportIdInput.value = exportId;
    renderExportDetail();
    if (announce) {
      showMessage(`Loaded export ${exportId}.`, "success");
    }
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function handleUploadSubmit(event) {
  event.preventDefault();
  const file = elements.uploadFile.files[0];
  if (!file) {
    showMessage("Choose a TXT file before uploading.", "error");
    return;
  }

  try {
    const content = await file.text();
    const payload = {
      filename: file.name,
      content,
      source_type: elements.uploadSourceType.value || undefined,
      title: emptyToUndefined(elements.uploadTitle.value),
      document_id: emptyToUndefined(elements.uploadDocumentId.value),
    };
    const response = await apiRequest("/api/documents", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    elements.uploadForm.reset();
    showMessage(`Uploaded document ${response.document_id}.`, "success");
    await refreshDocuments();
    await loadDocumentDetail(response.document_id, false);
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function handleRunSubmit(event) {
  event.preventDefault();
  try {
    const selectedDocumentIds = Array.from(
      elements.runDocumentCheckboxes.querySelectorAll('input[type="checkbox"]:checked')
    ).map((input) => input.value);

    if (!selectedDocumentIds.length) {
      throw new Error("Select at least one uploaded document for the run.");
    }

    const workflowConfig = JSON.parse(elements.runConfig.value || "{}");
    const payload = {
      document_ids: selectedDocumentIds,
      workflow_plugin_id: elements.runPluginSelect.value,
      workflow_config: workflowConfig,
    };
    const response = await apiRequest("/api/runs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showMessage(`Created run ${response.run_id}.`, "success");
    await refreshRuns();
    await loadRunDetail(response.run_id, false);
    await refreshSelectedRunData(false);
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function handleImprovementSubmit(event) {
  event.preventDefault();
  if (!state.selectedRun) {
    showMessage("Select a run before applying improvements.", "error");
    return;
  }

  const actionType = elements.improvementAction.value;
  const action = { action_type: actionType };

  if (["edit_card", "delete_card", "rate_card"].includes(actionType)) {
    const cardId = elements.improvementCardId.value;
    if (!cardId) {
      showMessage("Select a target card for this improvement.", "error");
      return;
    }
    action.card_id = cardId;
  }

  if (actionType === "prompt_refine_selected") {
    const selectedIds = Array.from(elements.improvementCardIds.selectedOptions).map(
      (option) => option.value
    );
    if (!selectedIds.length) {
      showMessage("Select at least one target card for prompt refinement.", "error");
      return;
    }
    action.card_ids = selectedIds;
  }

  if (actionType === "edit_card") {
    if (elements.improvementFront.value.trim()) {
      action.front = elements.improvementFront.value.trim();
    }
    if (elements.improvementBack.value.trim()) {
      action.back = elements.improvementBack.value.trim();
    }
  }

  if (["rate_card", "rate_run"].includes(actionType)) {
    if (!elements.improvementRating.value) {
      showMessage("Choose a rating before submitting this improvement.", "error");
      return;
    }
    action.rating = elements.improvementRating.value;
  }

  if (["prompt_refine_selected", "prompt_refine_all"].includes(actionType)) {
    if (!elements.improvementPrompt.value.trim()) {
      showMessage("Enter a refinement prompt before submitting this improvement.", "error");
      return;
    }
    action.prompt = elements.improvementPrompt.value.trim();
  }

  try {
    await apiRequest(`/api/runs/${encodeURIComponent(state.selectedRun.run_id)}/improvements`, {
      method: "POST",
      body: JSON.stringify({ actions: [action] }),
    });
    showMessage(`Applied ${actionType} to run ${state.selectedRun.run_id}.`, "success");
    elements.improvementFront.value = "";
    elements.improvementBack.value = "";
    elements.improvementPrompt.value = "";
    elements.improvementRating.value = "";
    await refreshSelectedRunData(false);
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function handleExportSubmit(event) {
  event.preventDefault();
  if (!state.selectedRun) {
    showMessage("Select a run before creating an export.", "error");
    return;
  }

  const cardIds = Array.from(elements.exportCardIds.selectedOptions).map((option) => option.value);
  const payload = {
    exporter_id: elements.exporterSelect.value,
    card_ids: cardIds,
  };

  try {
    const response = await apiRequest(`/api/runs/${encodeURIComponent(state.selectedRun.run_id)}/exports`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    showMessage(`Created export ${response.export_id}.`, "success");
    await loadExportDetail(response.export_id, false);
  } catch (err) {
    showMessage(String(err.message || err), "error");
  }
}

async function handleExportLookupSubmit(event) {
  event.preventDefault();
  const exportId = elements.exportIdInput.value.trim();
  if (!exportId) {
    showMessage("Enter an export id to load export metadata.", "error");
    return;
  }
  await loadExportDetail(exportId, false);
}

function renderOverview() {
  if (!state.overview) {
    elements.overviewContent.innerHTML = '<div class="placeholder">No overview loaded.</div>';
    return;
  }

  const workflows = (state.overview.available_workflow_plugins || [])
    .map(
      (plugin) => `
        <div class="overview-card">
          <p class="eyebrow">Workflow</p>
          <strong>${escapeHtml(plugin.name || plugin.plugin_id)}</strong>
          <p>${escapeHtml(plugin.description || "")}</p>
          <p><strong>ID:</strong> ${escapeHtml(plugin.plugin_id)}</p>
          <p><strong>Inputs:</strong> ${escapeHtml((plugin.supported_input_types || []).join(", ") || "n/a")}</p>
          <p><strong>Ops:</strong> ${escapeHtml((plugin.supported_operations || []).join(", ") || "n/a")}</p>
        </div>
      `
    )
    .join("");

  const exporters = (state.overview.available_exporters || [])
    .map(
      (exporter) => `
        <div class="overview-card">
          <p class="eyebrow">Exporter</p>
          <strong>${escapeHtml(exporter.exporter_id)}</strong>
          <p><strong>Media type:</strong> ${escapeHtml(exporter.media_type)}</p>
          <p><strong>Extension:</strong> ${escapeHtml(exporter.file_extension)}</p>
        </div>
      `
    )
    .join("");

  elements.overviewContent.innerHTML = `
    <div class="overview-card">
      <p class="eyebrow">Input Formats</p>
      <strong>${escapeHtml((state.overview.supported_input_formats || []).join(", ") || "n/a")}</strong>
    </div>
    <div class="overview-card">
      <p class="eyebrow">API Resources</p>
      <strong>${escapeHtml((state.overview.api_resources || []).length.toString())}</strong>
      <p>${escapeHtml((state.overview.api_resources || []).join(", "))}</p>
    </div>
    ${workflows}
    ${exporters}
  `;
}

function renderDocuments() {
  if (!state.documents.length) {
    elements.documentsList.innerHTML = '<div class="empty-state">No documents uploaded yet.</div>';
    return;
  }

  elements.documentsList.innerHTML = state.documents
    .map(
      (document) => `
        <article class="collection-item">
          <div>
            <h3>${escapeHtml(document.title || document.filename)}</h3>
            <p>${escapeHtml(document.document_id)} · ${escapeHtml(document.source_type)} · ${document.block_count} blocks</p>
          </div>
          <div class="collection-item-actions">
            <button class="button secondary" type="button" data-document-id="${escapeHtml(document.document_id)}">Inspect</button>
          </div>
        </article>
      `
    )
    .join("");

  elements.documentsList.querySelectorAll("[data-document-id]").forEach((button) => {
    button.addEventListener("click", () => loadDocumentDetail(button.dataset.documentId));
  });
}

function renderDocumentDetail() {
  if (!state.selectedDocument) {
    elements.documentDetail.textContent = "Select a document to inspect its metadata.";
    elements.documentDetail.classList.add("empty-state");
    return;
  }
  const document = state.selectedDocument;
  elements.documentDetail.classList.remove("empty-state");
  elements.documentDetail.innerHTML = `
    <dl>
      <dt>Document ID</dt><dd>${escapeHtml(document.document_id)}</dd>
      <dt>Filename</dt><dd>${escapeHtml(document.filename)}</dd>
      <dt>Title</dt><dd>${escapeHtml(document.title)}</dd>
      <dt>Source type</dt><dd>${escapeHtml(document.source_type)}</dd>
      <dt>Created</dt><dd>${escapeHtml(formatDate(document.created_at))}</dd>
      <dt>Blocks</dt><dd>${escapeHtml(String(document.block_count))}</dd>
      <dt>Parsed content</dt><dd>${document.has_parsed_content ? "yes" : "no"}</dd>
      <dt>Warnings</dt><dd>${escapeHtml((document.warnings || []).join(", ") || "none")}</dd>
    </dl>
  `;
}

function renderRunDocumentCheckboxes() {
  if (!state.documents.length) {
    elements.runDocumentCheckboxes.innerHTML =
      '<div class="empty-state">Upload a document before creating runs.</div>';
    return;
  }

  elements.runDocumentCheckboxes.innerHTML = state.documents
    .map(
      (document) => `
        <label class="checkbox-item">
          <input type="checkbox" value="${escapeHtml(document.document_id)}" />
          <span>
            <strong>${escapeHtml(document.title || document.filename)}</strong><br />
            ${escapeHtml(document.document_id)}
          </span>
        </label>
      `
    )
    .join("");
}

function renderPluginOptions() {
  const plugins = state.overview?.available_workflow_plugins || [];
  elements.runPluginSelect.innerHTML = plugins
    .map(
      (plugin) =>
        `<option value="${escapeHtml(plugin.plugin_id)}">${escapeHtml(plugin.name || plugin.plugin_id)}</option>`
    )
    .join("");
}

function renderRuns() {
  if (!state.runs.length) {
    elements.runsList.innerHTML = '<div class="empty-state">No runs created yet.</div>';
    return;
  }

  elements.runsList.innerHTML = state.runs
    .map(
      (run) => `
        <article class="collection-item">
          <div>
            <h3>${escapeHtml(run.run_id)}</h3>
            <p>${escapeHtml(run.plugin_id)} · ${escapeHtml(run.status)} · ${run.card_count} cards</p>
          </div>
          <div class="collection-item-actions">
            <button class="button secondary" type="button" data-run-id="${escapeHtml(run.run_id)}">Inspect</button>
          </div>
        </article>
      `
    )
    .join("");

  elements.runsList.querySelectorAll("[data-run-id]").forEach((button) => {
    button.addEventListener("click", async () => {
      await loadRunDetail(button.dataset.runId);
      await refreshSelectedRunData(false);
    });
  });
}

function renderRunDetail() {
  if (!state.selectedRun) {
    elements.runDetail.textContent = "Select a run to inspect cards, improvements, and exports.";
    elements.runDetail.classList.add("empty-state");
    return;
  }
  const run = state.selectedRun;
  elements.runDetail.classList.remove("empty-state");
  elements.runDetail.innerHTML = `
    <dl>
      <dt>Run ID</dt><dd>${escapeHtml(run.run_id)}</dd>
      <dt>Plugin</dt><dd>${escapeHtml(run.plugin_id)}</dd>
      <dt>Status</dt><dd>${escapeHtml(run.status)}</dd>
      <dt>Documents</dt><dd>${escapeHtml((run.document_ids || []).join(", "))}</dd>
      <dt>Created</dt><dd>${escapeHtml(formatDate(run.created_at))}</dd>
      <dt>Updated</dt><dd>${escapeHtml(formatDate(run.updated_at))}</dd>
      <dt>Completed</dt><dd>${escapeHtml(formatDate(run.completed_at) || "n/a")}</dd>
      <dt>Warnings</dt><dd>${escapeHtml((run.warnings || []).join(", ") || "none")}</dd>
      <dt>Workflow config</dt><dd><pre>${escapeHtml(JSON.stringify(run.workflow_config || {}, null, 2))}</pre></dd>
    </dl>
  `;
}

function renderCards() {
  if (!state.cards.length) {
    elements.cardsTableWrapper.innerHTML = '<div class="empty-state">This run has no cards yet.</div>';
    return;
  }

  const rows = state.cards
    .map((card) => {
      const section = card.source?.section || "Document";
      const sourceSnippet = `${section}${card.source?.position ? ` · pos ${card.source.position}` : ""}`;
      return `
        <tr>
          <td>${escapeHtml(card.card_id)}</td>
          <td>${escapeHtml(card.front)}</td>
          <td>${escapeHtml(card.back)}</td>
          <td>${escapeHtml(sourceSnippet)}</td>
          <td>
            <span class="status-chip ${card.status === "deleted" ? "deleted" : ""}">
              ${escapeHtml(card.status)}
            </span>
          </td>
          <td>${escapeHtml(card.rating || "n/a")}</td>
          <td><div class="tag-list">${(card.tags || []).map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("")}</div></td>
        </tr>
      `;
    })
    .join("");

  elements.cardsTableWrapper.innerHTML = `
    <table>
      <thead>
        <tr>
          <th>Card ID</th>
          <th>Front</th>
          <th>Back</th>
          <th>Source</th>
          <th>Status</th>
          <th>Rating</th>
          <th>Tags</th>
        </tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

function renderCardSelectors() {
  const options = state.cards
    .map(
      (card) =>
        `<option value="${escapeHtml(card.card_id)}">${escapeHtml(card.card_id)} · ${escapeHtml(card.front.slice(0, 60))}</option>`
    )
    .join("");

  elements.improvementCardId.innerHTML = `<option value="">Select a card</option>${options}`;
  elements.improvementCardIds.innerHTML = options;
  elements.exportCardIds.innerHTML = options;
}

function renderImprovementHistory() {
  if (!state.selectedRun) {
    elements.improvementsList.innerHTML =
      '<div class="empty-state">Select a run to inspect its improvement history.</div>';
    return;
  }
  if (!state.improvements.length) {
    elements.improvementsList.innerHTML =
      '<div class="empty-state">No improvements recorded for this run yet.</div>';
    return;
  }

  elements.improvementsList.innerHTML = state.improvements
    .map(
      (record) => `
        <article class="collection-item">
          <div>
            <h3>${escapeHtml(record.action_type)}</h3>
            <p>${escapeHtml(record.summary)}</p>
            <p>${escapeHtml(formatDate(record.applied_at))}</p>
          </div>
        </article>
      `
    )
    .join("");
}

function renderExporterOptions() {
  const exporters = state.overview?.available_exporters || [];
  elements.exporterSelect.innerHTML = exporters
    .map(
      (exporter) =>
        `<option value="${escapeHtml(exporter.exporter_id)}">${escapeHtml(exporter.exporter_id)}</option>`
    )
    .join("");
}

function renderExportDetail() {
  if (!state.selectedExport) {
    elements.exportDetail.textContent = "Load an export to inspect metadata and download the artifact.";
    elements.exportDetail.classList.add("empty-state");
    return;
  }

  const exportArtifact = state.selectedExport;
  elements.exportDetail.classList.remove("empty-state");
  elements.exportDetail.innerHTML = `
    <dl>
      <dt>Export ID</dt><dd>${escapeHtml(exportArtifact.export_id)}</dd>
      <dt>Run ID</dt><dd>${escapeHtml(exportArtifact.run_id)}</dd>
      <dt>Exporter</dt><dd>${escapeHtml(exportArtifact.exporter_id)}</dd>
      <dt>Status</dt><dd>${escapeHtml(exportArtifact.status)}</dd>
      <dt>Filename</dt><dd>${escapeHtml(exportArtifact.filename)}</dd>
      <dt>Media type</dt><dd>${escapeHtml(exportArtifact.media_type)}</dd>
      <dt>Cards</dt><dd>${escapeHtml(String(exportArtifact.card_count))}</dd>
      <dt>Created</dt><dd>${escapeHtml(formatDate(exportArtifact.created_at))}</dd>
    </dl>
    <p style="margin-top: 16px;">
      <a class="button primary link-button" href="/api/exports/${encodeURIComponent(
        exportArtifact.export_id
      )}/download">Download Export</a>
    </p>
  `;
}

function syncSelectedRunFields() {
  const runId = state.selectedRun?.run_id || "";
  elements.improvementRunId.value = runId;
  elements.exportRunId.value = runId;
}

function syncImprovementFields() {
  const actionType = elements.improvementAction.value;
  toggleVisibility(elements.singleCardField, ["edit_card", "delete_card", "rate_card"].includes(actionType));
  toggleVisibility(elements.multiCardField, actionType === "prompt_refine_selected");
  toggleVisibility(elements.frontField, actionType === "edit_card");
  toggleVisibility(elements.backField, actionType === "edit_card");
  toggleVisibility(elements.ratingField, ["rate_card", "rate_run"].includes(actionType));
  toggleVisibility(elements.promptField, ["prompt_refine_selected", "prompt_refine_all"].includes(actionType));
}

function toggleVisibility(element, shouldShow) {
  element.classList.toggle("hidden", !shouldShow);
}

async function apiRequest(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  let payload;
  if (contentType.includes("application/json")) {
    payload = await response.json();
  } else {
    payload = await response.text();
  }

  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? payload.detail
        : String(payload);
    throw new Error(detail || `Request failed with status ${response.status}.`);
  }

  return payload;
}

function showMessage(message, kind) {
  elements.messageBanner.textContent = message;
  elements.messageBanner.className = `message ${kind}`;
}

function formatDate(value) {
  if (!value) {
    return "";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return date.toLocaleString();
}

function emptyToUndefined(value) {
  const trimmed = value.trim();
  return trimmed ? trimmed : undefined;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}
