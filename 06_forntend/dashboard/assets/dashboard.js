const VIEW_METADATA = {
  "work-plan": ["Program control", "Work Plan"],
  process: ["Operating protocol", "Process"],
  flow: ["System relationships", "Flow"],
  harness: ["Deterministic authority", "Harness Rules"],
  tools: ["Pinned capability registry", "Tools"],
  "owner-gates": ["Canonical governance ledger", "Owner Gates"],
  artifacts: ["Allowlisted metadata", "Artifacts"],
};

const GATE_LABELS = {
  G0: "Integrity / Migration",
  G1: "Reproduction",
  G2: "Track C Development",
  G3: "Track C Freeze",
  G4: "Track R Development",
  G5: "Optional HarnessOpt",
  G6: "External Confirmation",
  G7: "External Transfer",
  G8: "Publication",
};

const ACTIONS_BY_GATE = {
  G0: ["approve_implementation", "approve_documentation_migration", "approve_cleanup", "anchor_pdf_receipt_chain"],
  G1: ["authorize_reproduction"],
  G2: ["authorize_track_c_development"],
  G3: ["freeze_track_c"],
  G4: ["authorize_track_r_development"],
  G5: ["authorize_harnessopt"],
  G6: ["authorize_confirmation"],
  G7: ["authorize_transfer"],
  G8: ["authorize_publication"],
};

const state = {
  csrfToken: "",
  sessionReady: false,
  activePhaseId: "F0",
  previewToken: "",
  previewRecord: null,
  snapshot: null,
};

const elements = {};

document.addEventListener("DOMContentLoaded", initialize);

async function initialize() {
  cacheElements();
  bindNavigation();
  bindActions();
  populateDecisionOptions();
  setInitialView();
  renderLoadingStates();
  await refreshAll();
}

function cacheElements() {
  elements.viewTitle = document.querySelector("#view-title");
  elements.viewKicker = document.querySelector("#view-kicker");
  elements.syncState = document.querySelector("#sync-state");
  elements.refreshButton = document.querySelector("#refresh-button");
  elements.phaseSpine = document.querySelector("#phase-spine");
  elements.planDetail = document.querySelector("#plan-detail");
  elements.processContent = document.querySelector("#process-content");
  elements.harnessContent = document.querySelector("#harness-content");
  elements.flowList = document.querySelector("#flow-list");
  elements.flowCanvas = document.querySelector("#flow-canvas");
  elements.flowCaption = document.querySelector("#flow-caption");
  elements.toolsContent = document.querySelector("#tools-content");
  elements.gateSummary = document.querySelector("#gate-summary");
  elements.decisionTableBody = document.querySelector("#decision-table-body");
  elements.artifactGrid = document.querySelector("#artifact-grid");
  elements.newDecisionButton = document.querySelector("#new-decision-button");
  elements.decisionDialog = document.querySelector("#decision-dialog");
  elements.decisionForm = document.querySelector("#decision-form");
  elements.decisionFormStep = document.querySelector("#decision-form-step");
  elements.decisionPreviewStep = document.querySelector("#decision-preview-step");
  elements.decisionFormError = document.querySelector("#decision-form-error");
  elements.decisionConfirmError = document.querySelector("#decision-confirm-error");
  elements.recordPreview = document.querySelector("#record-preview");
  elements.previewButton = document.querySelector("#decision-preview-button");
  elements.confirmButton = document.querySelector("#decision-confirm-button");
  elements.backButton = document.querySelector("#decision-back-button");
  elements.explicitConfirmation = document.querySelector("#explicit-confirmation");
  elements.toastRegion = document.querySelector("#toast-region");
}

function bindNavigation() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => activateView(button.dataset.view, true));
  });
  window.addEventListener("hashchange", setInitialView);
}

function bindActions() {
  elements.refreshButton.addEventListener("click", refreshAll);
  elements.newDecisionButton.addEventListener("click", openDecisionDialog);
  document.querySelector("#close-decision-button").addEventListener("click", closeDecisionDialog);
  elements.decisionForm.addEventListener("submit", previewDecision);
  elements.confirmButton.addEventListener("click", confirmDecision);
  elements.backButton.addEventListener("click", showDecisionFormStep);
  elements.explicitConfirmation.addEventListener("change", () => {
    elements.confirmButton.disabled = !elements.explicitConfirmation.checked;
  });
  elements.decisionForm.elements.gate_id.addEventListener("change", updateActionOptions);
  elements.decisionDialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    closeDecisionDialog();
  });
}

function setInitialView() {
  const requested = window.location.hash.replace(/^#\/?/, "");
  activateView(Object.hasOwn(VIEW_METADATA, requested) ? requested : "work-plan", false);
}

function activateView(viewId, updateHash) {
  document.querySelectorAll("[data-view-panel]").forEach((panel) => {
    panel.classList.toggle("is-visible", panel.dataset.viewPanel === viewId);
  });
  document.querySelectorAll("[data-view]").forEach((button) => {
    const active = button.dataset.view === viewId;
    button.classList.toggle("is-active", active);
    if (active) {
      button.setAttribute("aria-current", "page");
    } else {
      button.removeAttribute("aria-current");
    }
  });
  const metadata = VIEW_METADATA[viewId];
  elements.viewKicker.textContent = metadata[0];
  elements.viewTitle.textContent = metadata[1];
  document.title = `${metadata[1]} | IS1 Owner Console`;
  if (updateHash) {
    history.pushState(null, "", `#${viewId}`);
    document.querySelector("#main-content").focus({ preventScroll: true });
  }
}

function renderLoadingStates() {
  [elements.planDetail, elements.processContent, elements.harnessContent, elements.toolsContent, elements.gateSummary, elements.artifactGrid].forEach((target) => {
    target.replaceChildren(messageState("Loading local projection", "loading-state"));
  });
  elements.flowCanvas.replaceChildren(messageState("Loading flow catalog", "loading-state"));
}

async function refreshAll() {
  elements.refreshButton.disabled = true;
  setSyncState("Refreshing", false);
  try {
    await ensureSession();
    const results = await Promise.allSettled([
      fetchJson("/api/v1/dashboard-snapshot"),
      fetchJson("/api/v1/content/process"),
      fetchJson("/api/v1/content/harness"),
      fetchJson("/api/v1/flows"),
      fetchJson("/api/v1/tools"),
      fetchJson("/api/v1/owner-gates"),
      fetchJson("/api/v1/artifacts"),
    ]);
    if (results[0].status === "rejected") {
      elements.newDecisionButton.disabled = true;
      elements.newDecisionButton.title = "Decision entry is unavailable until the canonical plan and Git state can be verified";
    }
    renderResult(results[0], renderPlan, elements.planDetail, "Plan projection unavailable");
    renderResult(results[1], (data) => renderContentBrowser(elements.processContent, data), elements.processContent, "Process documents unavailable");
    renderResult(results[2], (data) => renderContentBrowser(elements.harnessContent, data), elements.harnessContent, "Harness documents unavailable");
    renderResult(results[3], renderFlowCatalog, elements.flowCanvas, "Flow catalog unavailable");
    renderResult(results[4], renderTools, elements.toolsContent, "Tool registry unavailable");
    renderResult(results[5], renderOwnerGates, elements.gateSummary, "Owner Gate ledger unavailable");
    renderResult(results[6], renderArtifacts, elements.artifactGrid, "Artifact catalog unavailable");
    const failures = results.filter((result) => result.status === "rejected").length;
    setSyncState(failures ? `${failures} view${failures === 1 ? "" : "s"} unavailable` : `Updated ${formatTime(new Date())}`, failures > 0);
  } catch (error) {
    elements.newDecisionButton.disabled = true;
    elements.newDecisionButton.title = "Decision entry is unavailable until the local session and Git state can be verified";
    setSyncState(readError(error), true);
  } finally {
    elements.refreshButton.disabled = false;
  }
}

function renderResult(result, renderer, target, fallback) {
  if (result.status === "fulfilled") {
    renderer(result.value);
  } else {
    target.replaceChildren(messageState(`${fallback}. ${readError(result.reason)}`, "error-state"));
  }
}

async function ensureSession(force = false) {
  if (state.sessionReady && !force) {
    return;
  }
  const response = await fetch("/api/v1/session", { credentials: "same-origin", cache: "no-store" });
  const payload = await parseResponse(response);
  state.csrfToken = payload.csrf_token;
  state.sessionReady = true;
}

async function fetchJson(url, options = {}, retrySession = true) {
  const response = await fetch(url, {
    credentials: "same-origin",
    cache: "no-store",
    ...options,
  });
  if (response.status === 401 && retrySession) {
    state.sessionReady = false;
    await ensureSession(true);
    return fetchJson(url, options, false);
  }
  return parseResponse(response);
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof payload === "object" && payload ? payload.detail : payload;
    throw new Error(typeof detail === "string" ? detail : `Request failed with status ${response.status}`);
  }
  return payload;
}

function renderPlan(snapshot) {
  state.snapshot = snapshot;
  elements.newDecisionButton.disabled = Boolean(snapshot.git_dirty);
  elements.newDecisionButton.title = snapshot.git_dirty
    ? "Commit or otherwise resolve the worktree before creating an Owner Gate preview"
    : "Preview a typed Owner Gate decision";
  const phases = Array.isArray(snapshot.phases) ? snapshot.phases : [];
  if (!phases.length) {
    elements.phaseSpine.replaceChildren();
    elements.planDetail.replaceChildren(messageState("No phases were projected from the canonical plan.", "empty-state"));
    return;
  }
  if (!phases.some((phase) => phase.phase_id === state.activePhaseId)) {
    state.activePhaseId = phases[0].phase_id;
  }
  const phaseButtons = phases.map((phase) => {
    const button = el("button", "phase-item");
    button.type = "button";
    button.dataset.phaseId = phase.phase_id;
    button.dataset.evidence = normalizeState(phase.evidence_state);
    button.dataset.gate = normalizeState(phase.governance_state);
    button.classList.toggle("is-active", phase.phase_id === state.activePhaseId);
    const node = el("span", "phase-node", phase.phase_id);
    node.setAttribute("aria-hidden", "true");
    const copy = el("span", "phase-copy");
    copy.append(el("strong", "", phase.title), el("small", "", `${phase.tasks.length} task${phase.tasks.length === 1 ? "" : "s"}`));
    const gate = el("span", "phase-gate-mark");
    gate.setAttribute("aria-hidden", "true");
    button.append(node, copy, gate);
    button.setAttribute("aria-label", `${phase.phase_id} ${phase.title}. Evidence ${humanize(phase.evidence_state)}. Authorization ${humanize(phase.governance_state)}.`);
    button.addEventListener("click", () => {
      state.activePhaseId = phase.phase_id;
      renderPlan(snapshot);
    });
    return button;
  });
  elements.phaseSpine.replaceChildren(...phaseButtons);
  renderPhaseDetail(phases.find((phase) => phase.phase_id === state.activePhaseId), snapshot);
}

function renderPhaseDetail(phase, snapshot) {
  const header = el("div", "phase-header");
  const titleBlock = el("div");
  titleBlock.append(el("p", "eyebrow", `Phase ${phase.phase_id}`), el("h2", "", phase.title));
  const dependencies = phase.dependencies?.length ? `Depends on ${phase.dependencies.join(", ")}` : "No prior phase dependency";
  titleBlock.append(el("p", "", dependencies));
  const statuses = el("div", "status-pair");
  statuses.append(statusBadge(`Evidence: ${humanize(phase.evidence_state)}`, phase.evidence_state));
  statuses.append(statusBadge(`Gate: ${humanize(phase.governance_state)}`, phase.governance_state));
  header.append(titleBlock, statuses);

  const context = el("div", "program-context");
  const contextText = el("p", "hash-line", `Plan ${shortHash(snapshot.plan_sha256)} | Git ${shortHash(snapshot.git_commit)} | ${snapshot.git_dirty ? "dirty worktree" : "clean worktree"}`);
  context.append(contextText);

  const taskList = el("div", "task-list");
  (phase.tasks || []).forEach((task, index) => taskList.append(renderTask(task, index === 0)));
  elements.planDetail.replaceChildren(header, context, taskList);
}

function renderTask(task, open) {
  const details = el("details", "task-card");
  details.open = open;
  const summary = el("summary");
  summary.append(el("span", "task-id", task.task_id), el("span", "task-title", task.title), el("span", "task-status", humanize(task.evidence_state)));
  const body = el("div", "task-body");
  const list = el("dl");
  appendDefinition(list, "Goal", task.goal);
  appendDefinition(list, "Model", task.model);
  appendDefinition(list, "Objective", task.objective);
  appendDefinition(list, "Acceptance", task.acceptance);
  appendDefinition(list, "Owner Gate", task.owner_gate_ids?.join(", ") || "Not required");
  appendDefinition(list, "Budget / stop", task.budget_stop);
  appendDefinition(list, "Rollback", task.rollback);
  appendDefinition(list, "Scientific risk", task.scientific_validity_risk);
  appendDefinition(list, "Dependencies", task.dependencies?.join(", ") || "None");
  if (task.evidence) {
    appendDefinition(list, "Evidence record", task.evidence.record_id, true);
    appendDefinition(list, "Evidence SHA-256", task.evidence.record_sha256, true);
  }
  body.append(list);
  details.append(summary, body);
  return details;
}

function renderContentBrowser(target, payload) {
  const documents = Array.isArray(payload.documents) ? payload.documents : [];
  if (!documents.length) {
    target.replaceChildren(messageState("No allowlisted documents are available.", "empty-state"));
    return;
  }
  const index = el("nav", "content-index");
  index.setAttribute("aria-label", `${payload.title || "Content"} documents`);
  const documentView = el("article", "document-view");
  const showDocument = (document, activeButton) => {
    index.querySelectorAll("button").forEach((button) => button.classList.toggle("is-active", button === activeButton));
    documentView.replaceChildren(renderDocument(document));
  };
  documents.forEach((document, indexValue) => {
    const button = el("button", indexValue === 0 ? "is-active" : "", document.title || document.source_id);
    button.type = "button";
    button.addEventListener("click", () => showDocument(document, button));
    index.append(button);
  });
  documentView.append(renderDocument(documents[0]));
  target.replaceChildren(index, documentView);
}

function renderDocument(sourceDocument) {
  const wrapper = el("div");
  wrapper.append(el("h2", "", sourceDocument.title || "Document"));
  wrapper.append(el("p", "hash-line", `${sourceDocument.source_id} | ${shortHash(sourceDocument.sha256)}`));
  (sourceDocument.sections || []).forEach((section) => {
    const block = el("section", "document-block");
    const heading = el(section.level <= 2 ? "h3" : "h4", "", section.heading || "Section");
    block.append(heading);
    appendPlainMarkdown(block, section.body || "");
    wrapper.append(block);
  });
  return wrapper;
}

function appendPlainMarkdown(target, source) {
  const lines = String(source).split(/\r?\n/);
  let list = null;
  let code = null;
  lines.forEach((rawLine) => {
    const line = rawLine.trim();
    if (line.startsWith("```")) {
      if (code) {
        target.append(code);
        code = null;
      } else {
        code = el("pre", "mono");
      }
      return;
    }
    if (code) {
      code.append(document.createTextNode(`${rawLine}\n`));
      return;
    }
    const bullet = line.match(/^[-*]\s+(.+)$/);
    if (bullet) {
      if (!list) {
        list = el("ul");
        target.append(list);
      }
      list.append(el("li", "", stripMarkdown(bullet[1])));
      return;
    }
    list = null;
    if (line) {
      target.append(el("p", "", stripMarkdown(line)));
    }
  });
  if (code) {
    target.append(code);
  }
}

function renderFlowCatalog(payload) {
  const flows = Array.isArray(payload.flows) ? payload.flows : [];
  if (!flows.length) {
    elements.flowList.replaceChildren();
    elements.flowCanvas.replaceChildren(messageState("No allowlisted flows are available.", "empty-state"));
    return;
  }
  const buttons = flows.map((flow, index) => {
    const button = el("button", index === 0 ? "is-active" : "", flow.title || flow.flow_id);
    button.type = "button";
    button.setAttribute("role", "listitem");
    button.addEventListener("click", () => {
      elements.flowList.querySelectorAll("button").forEach((item) => item.classList.toggle("is-active", item === button));
      loadFlow(flow);
    });
    return button;
  });
  elements.flowList.replaceChildren(...buttons);
  loadFlow(flows[0]);
}

async function loadFlow(flow) {
  elements.flowCanvas.replaceChildren(messageState("Loading flow", "loading-state"));
  elements.flowCaption.textContent = flow.description || flow.title || flow.flow_id;
  try {
    const response = await fetch(`/api/v1/flows/${encodeURIComponent(flow.flow_id)}`, { credentials: "same-origin", cache: "no-store" });
    if (response.status === 401) {
      state.sessionReady = false;
      await ensureSession(true);
      return loadFlow(flow);
    }
    if (!response.ok) {
      await parseResponse(response);
    }
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("image/svg+xml")) {
      const image = el("img");
      image.alt = flow.title || "Research flow";
      image.src = `/api/v1/flows/${encodeURIComponent(flow.flow_id)}`;
      elements.flowCanvas.setAttribute("aria-label", image.alt);
      elements.flowCanvas.replaceChildren(image);
      return;
    }
    const payload = await response.json();
    elements.flowCanvas.setAttribute("aria-label", payload.title || flow.title || "Research flow");
    elements.flowCaption.textContent = payload.description || flow.description || payload.title || flow.title || flow.flow_id;
    if (payload.image_url) {
      const image = el("img");
      image.alt = payload.title || flow.title || "Research flow";
      image.src = payload.image_url;
      elements.flowCanvas.replaceChildren(image);
      return;
    }
    elements.flowCanvas.replaceChildren(renderFlowGraph(payload));
  } catch (error) {
    elements.flowCanvas.replaceChildren(messageState(readError(error), "error-state"));
  }
}

function renderFlowGraph(payload) {
  const svgNamespace = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNamespace, "svg");
  svg.setAttribute("viewBox", "0 0 960 560");
  svg.setAttribute("aria-hidden", "true");
  const nodes = Array.isArray(payload.nodes) ? payload.nodes : [];
  const edges = Array.isArray(payload.edges) ? payload.edges : [];
  const positions = new Map();
  const columns = Math.min(4, Math.max(1, Math.ceil(Math.sqrt(nodes.length))));
  const rows = Math.ceil(nodes.length / columns);
  nodes.forEach((node, index) => {
    const column = index % columns;
    const row = Math.floor(index / columns);
    positions.set(node.node_id, {
      x: 85 + column * (790 / Math.max(1, columns - 1)),
      y: 65 + row * (420 / Math.max(1, rows - 1)),
    });
  });
  const marker = document.createElementNS(svgNamespace, "marker");
  marker.setAttribute("id", "flow-arrow");
  marker.setAttribute("viewBox", "0 0 10 10");
  marker.setAttribute("refX", "9");
  marker.setAttribute("refY", "5");
  marker.setAttribute("markerWidth", "7");
  marker.setAttribute("markerHeight", "7");
  marker.setAttribute("orient", "auto-start-reverse");
  const arrow = document.createElementNS(svgNamespace, "path");
  arrow.setAttribute("d", "M 0 0 L 10 5 L 0 10 z");
  arrow.setAttribute("fill", "#8a949b");
  marker.append(arrow);
  const definitions = document.createElementNS(svgNamespace, "defs");
  definitions.append(marker);
  svg.append(definitions);
  edges.forEach((edge) => {
    const source = positions.get(edge.source);
    const target = positions.get(edge.target);
    if (!source || !target) {
      return;
    }
    const line = document.createElementNS(svgNamespace, "line");
    line.setAttribute("x1", String(source.x));
    line.setAttribute("y1", String(source.y));
    line.setAttribute("x2", String(target.x));
    line.setAttribute("y2", String(target.y));
    line.setAttribute("stroke", edge.kind?.includes("optional") ? "#9a6700" : "#8a949b");
    line.setAttribute("stroke-width", "2");
    if (edge.kind?.includes("optional")) {
      line.setAttribute("stroke-dasharray", "6 6");
    }
    line.setAttribute("marker-end", "url(#flow-arrow)");
    svg.append(line);
  });
  nodes.forEach((node) => {
    const position = positions.get(node.node_id);
    const group = document.createElementNS(svgNamespace, "g");
    const rect = document.createElementNS(svgNamespace, "rect");
    rect.setAttribute("x", String(position.x - 72));
    rect.setAttribute("y", String(position.y - 28));
    rect.setAttribute("width", "144");
    rect.setAttribute("height", "56");
    rect.setAttribute("rx", "4");
    rect.setAttribute("fill", node.kind === "protected" ? "#fbe9e7" : node.kind === "canonical" || node.kind === "authority" ? "#e7f3f1" : "#ffffff");
    rect.setAttribute("stroke", node.kind === "protected" ? "#b42318" : node.kind === "canonical" || node.kind === "authority" ? "#147d75" : "#b8c1c8");
    const idText = document.createElementNS(svgNamespace, "text");
    idText.setAttribute("x", String(position.x));
    idText.setAttribute("y", String(position.y - 7));
    idText.setAttribute("text-anchor", "middle");
    idText.setAttribute("font-family", "Cascadia Mono, Consolas, monospace");
    idText.setAttribute("font-size", "11");
    idText.setAttribute("font-weight", "700");
    idText.setAttribute("fill", "#147d75");
    idText.textContent = node.node_id;
    const label = document.createElementNS(svgNamespace, "text");
    label.setAttribute("x", String(position.x));
    label.setAttribute("y", String(position.y + 12));
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("font-family", "Segoe UI, Arial, sans-serif");
    label.setAttribute("font-size", "10");
    label.setAttribute("fill", "#182126");
    label.textContent = truncate(node.label || node.node_id, 24);
    group.append(rect, idText, label);
    svg.append(group);
  });
  return svg;
}

function renderTools(payload) {
  const tools = Array.isArray(payload.tools) ? payload.tools : [];
  if (!tools.length) {
    elements.toolsContent.replaceChildren(messageState("No tools are projected from the pinned registry.", "empty-state"));
    return;
  }
  const grid = el("div", "tool-grid");
  tools.forEach((tool) => {
    const card = el("article", "tool-card");
    card.append(statusBadge(humanize(tool.adoption || "unclassified"), tool.adoption));
    card.append(el("h2", "", humanize(tool.tool_id)));
    card.append(el("p", "mono", tool.version || "Version not recorded"));
    if (tool.license) {
      card.append(el("p", "", `License: ${tool.license}`));
    }
    if (tool.commit) {
      card.append(el("p", "hash-line", `Commit ${shortHash(tool.commit)}`));
    }
    grid.append(card);
  });
  const digest = el("p", "hash-line", `Source SHA-256 ${payload.source_sha256}`);
  const documentBrowser = el("div", "content-browser tool-governance-docs");
  renderContentBrowser(documentBrowser, {
    title: "Tool governance and bootstrap records",
    documents: Array.isArray(payload.documents) ? payload.documents : [],
  });
  elements.toolsContent.replaceChildren(digest, grid, documentBrowser);
}

function renderOwnerGates(payload) {
  const records = Array.isArray(payload.records) ? payload.records : [];
  const chain = payload.chain || { count: 0, head: null };
  const states = state.snapshot?.gate_states || deriveGateStates(records);
  const chainCard = el("article", "summary-card");
  chainCard.append(statusBadge(chain.count ? "Chain verified" : "Empty ledger", chain.count ? "approved" : "pending"));
  chainCard.append(el("h2", "", "Ledger integrity"));
  chainCard.append(el("p", "mono", `${chain.count || 0} immutable record${chain.count === 1 ? "" : "s"}`));
  chainCard.append(el("p", "hash-line", chain.head ? `Head ${shortHash(chain.head)}` : "No chain head"));
  const summaryCards = Object.entries(GATE_LABELS).map(([gateId, label]) => {
    const card = el("article", "summary-card");
    card.append(statusBadge(humanize(states[gateId] || "pending"), states[gateId] || "pending"));
    card.append(el("h2", "", `${gateId} ${label}`));
    return card;
  });
  elements.gateSummary.replaceChildren(chainCard, ...summaryCards);
  const rows = records.slice().reverse().map((record) => {
    const row = el("tr");
    const decisionCell = el("td");
    decisionCell.append(el("span", "mono", record.decision_id || "Unknown"));
    if (record.supersedes_decision_id) {
      decisionCell.append(el("p", "hash-line", `Supersedes ${record.supersedes_decision_id}`));
    }
    const details = el("details", "decision-audit");
    details.append(el("summary", "", "Audit details"));
    const audit = el("dl", "compact-definitions");
    appendDefinition(audit, "Action", humanize(record.scope?.action));
    appendDefinition(audit, "Scope", JSON.stringify(record.scope || {}), true);
    appendDefinition(audit, "Rationale", record.rationale);
    appendDefinition(audit, "Actor", record.actor, true);
    appendDefinition(audit, "Git commit", record.git_commit, true);
    appendDefinition(audit, "Scope SHA-256", record.scope_hash, true);
    appendDefinition(audit, "Record SHA-256", record.record_sha256, true);
    appendDefinition(audit, "Prior record", record.prior_record_hash || "Genesis record", true);
    details.append(audit);
    decisionCell.append(details);
    row.append(decisionCell, el("td", "mono", normalizeGateId(record.gate_id)), el("td", "", humanize(record.status)), el("td", "", formatDate(record.timestamp)), el("td", "mono", String(record.evidence_manifest_hashes?.length || 0)));
    return row;
  });
  if (!rows.length) {
    const row = el("tr");
    const cell = el("td", "", "No canonical Owner Gate decision is recorded. G0 remains pending.");
    cell.colSpan = 5;
    row.append(cell);
    rows.push(row);
  }
  elements.decisionTableBody.replaceChildren(...rows);
}

function deriveGateStates(records) {
  const states = Object.fromEntries(Object.keys(GATE_LABELS).map((gateId) => [gateId, "pending"]));
  records.forEach((record) => {
    const gateId = normalizeGateId(record.gate_id);
    if (Object.hasOwn(states, gateId) && ["approved", "rejected", "deferred"].includes(record.status)) {
      states[gateId] = record.status;
    }
  });
  return states;
}

function renderArtifacts(payload) {
  const artifacts = Array.isArray(payload.artifacts) ? payload.artifacts : [];
  const pdfs = Array.isArray(payload.approved_pdfs) ? payload.approved_pdfs : [];
  const cards = [];
  artifacts.forEach((artifact) => {
    const card = el("article", "artifact-card");
    card.append(statusBadge(humanize(artifact.artifact_class || "artifact"), artifact.artifact_class));
    card.append(el("h2", "", artifact.title || artifact.artifact_id));
    card.append(el("p", "", humanize(artifact.classification)));
    card.append(el("p", "hash-line", `SHA-256 ${artifact.sha256}`));
    card.append(el("p", "", formatBytes(artifact.size_bytes)));
    cards.push(card);
  });
  pdfs.forEach((pdf) => {
    const card = el("article", "artifact-card");
    card.append(statusBadge("Approved PDF", "approved"));
    card.append(el("h2", "", pdf.artifact_id));
    card.append(el("p", "", "Metadata only; access requires a separately receipted request."));
    card.append(el("p", "hash-line", `SHA-256 ${pdf.sha256}`));
    cards.push(card);
  });
  elements.artifactGrid.replaceChildren(...(cards.length ? cards : [messageState("No allowlisted artifact metadata is available.", "empty-state")]));
}

function populateDecisionOptions() {
  const gateSelect = elements.decisionForm.elements.gate_id;
  Object.entries(GATE_LABELS).forEach(([gateId, label]) => {
    const option = el("option", "", `${gateId} - ${label}`);
    option.value = gateId;
    gateSelect.append(option);
  });
  updateActionOptions();
}

function updateActionOptions() {
  const gateId = elements.decisionForm.elements.gate_id.value || "G0";
  const actionSelect = elements.decisionForm.elements.action;
  const options = (ACTIONS_BY_GATE[gateId] || []).map((action) => {
    const option = el("option", "", humanize(action));
    option.value = action;
    return option;
  });
  actionSelect.replaceChildren(...options);
}

function openDecisionDialog() {
  resetDecisionDialog();
  elements.decisionDialog.showModal();
  elements.decisionForm.elements.gate_id.focus();
}

function closeDecisionDialog() {
  state.previewToken = "";
  state.previewRecord = null;
  elements.decisionDialog.close();
}

function resetDecisionDialog() {
  elements.decisionForm.reset();
  updateActionOptions();
  showDecisionFormStep();
  elements.decisionFormError.textContent = "";
  elements.decisionConfirmError.textContent = "";
  elements.explicitConfirmation.checked = false;
  elements.confirmButton.disabled = true;
}

function showDecisionFormStep() {
  elements.decisionFormStep.hidden = false;
  elements.decisionPreviewStep.hidden = true;
  elements.previewButton.hidden = false;
  elements.confirmButton.hidden = true;
  elements.backButton.hidden = true;
  state.previewToken = "";
  state.previewRecord = null;
}

async function previewDecision(event) {
  event.preventDefault();
  elements.decisionFormError.textContent = "";
  elements.previewButton.disabled = true;
  try {
    const body = decisionRequestBody(new FormData(elements.decisionForm));
    const payload = await fetchJson("/api/v1/owner-gates/preview", {
      method: "POST",
      headers: { "content-type": "application/json", "x-csrf-token": state.csrfToken },
      body: JSON.stringify(body),
    });
    state.previewToken = payload.preview_token;
    state.previewRecord = payload.record;
    renderRecordPreview(payload.record);
    elements.decisionFormStep.hidden = true;
    elements.decisionPreviewStep.hidden = false;
    elements.previewButton.hidden = true;
    elements.confirmButton.hidden = false;
    elements.backButton.hidden = false;
    elements.explicitConfirmation.checked = false;
    elements.confirmButton.disabled = true;
    elements.explicitConfirmation.focus();
  } catch (error) {
    elements.decisionFormError.textContent = readError(error);
  } finally {
    elements.previewButton.disabled = false;
  }
}

function decisionRequestBody(formData) {
  const budget = compactObject({
    max_cost_usd: numberOrNull(formData.get("max_cost_usd"), false),
    max_tokens: numberOrNull(formData.get("max_tokens"), true),
    max_wall_clock_minutes: numberOrNull(formData.get("max_wall_clock_minutes"), true),
    max_trials: numberOrNull(formData.get("max_trials"), true),
  });
  const scope = {
    action: String(formData.get("action") || ""),
    phase_ids: sortedValues(formData.get("phase_ids"), /[,\n]/),
    task_ids: sortedValues(formData.get("task_ids"), /[,\n]/),
    targets: sortedValues(formData.get("targets"), /\r?\n/),
  };
  if (Object.keys(budget).length) {
    scope.budget = budget;
  }
  return compactObject({
    gate_id: String(formData.get("gate_id") || ""),
    status: String(formData.get("status") || ""),
    rationale: String(formData.get("rationale") || "").trim(),
    evidence_manifest_hashes: sortedValues(formData.get("evidence_hashes"), /\r?\n/),
    scope,
    supersedes_decision_id: emptyToNull(formData.get("supersedes_decision_id")),
    display_label: emptyToNull(formData.get("display_label")),
  });
}

function renderRecordPreview(record) {
  const fields = [
    ["Decision ID", record.decision_id, true],
    ["Gate", normalizeGateId(record.gate_id), true],
    ["Status", record.status, false],
    ["Scope", JSON.stringify(record.scope), true],
    ["Scope SHA-256", record.scope_hash, true],
    ["Rationale", record.rationale, false],
    ["Actor", record.actor, true],
    ["Timestamp", record.timestamp, true],
    ["Git commit", record.git_commit, true],
    ["Evidence hashes", record.evidence_manifest_hashes?.join("\n") || "None", true],
    ["Prior record hash", record.prior_record_hash || "First ledger record", true],
    ["Supersedes", record.supersedes_decision_id || "None", true],
  ];
  const items = [];
  fields.forEach(([label, value, mono]) => {
    const term = el("dt", "", label);
    const definition = el("dd", "", String(value ?? "Not supplied"));
    if (mono) {
      definition.dataset.mono = "true";
    }
    items.push(term, definition);
  });
  elements.recordPreview.replaceChildren(...items);
}

async function confirmDecision() {
  if (!elements.explicitConfirmation.checked || !state.previewToken) {
    return;
  }
  elements.decisionConfirmError.textContent = "";
  elements.confirmButton.disabled = true;
  try {
    const payload = await fetchJson("/api/v1/owner-gates/confirm", {
      method: "POST",
      headers: { "content-type": "application/json", "x-csrf-token": state.csrfToken },
      body: JSON.stringify({ preview_token: state.previewToken, confirm: true }),
    });
    closeDecisionDialog();
    toast(`Decision ${payload.decision_id} appended to the canonical ledger.`, false);
    await refreshAll();
  } catch (error) {
    elements.decisionConfirmError.textContent = readError(error);
    elements.confirmButton.disabled = false;
  }
}

function appendDefinition(list, label, value, mono = false) {
  const term = el("dt", "", label);
  const definition = el("dd", mono ? "mono" : "", value || "Not recorded");
  list.append(term, definition);
}

function statusBadge(text, status) {
  return el("span", `status-badge ${normalizeState(status)}`, text);
}

function messageState(message, className) {
  return el("div", className, message);
}

function el(tagName, className = "", text = "") {
  const node = document.createElement(tagName);
  if (className) {
    node.className = className;
  }
  if (text !== "") {
    node.textContent = String(text);
  }
  return node;
}

function sortedValues(value, separator) {
  return [...new Set(String(value || "").split(separator).map((item) => item.trim()).filter(Boolean))].sort();
}

function compactObject(value) {
  return Object.fromEntries(Object.entries(value).filter(([, item]) => item !== null && item !== undefined && item !== ""));
}

function numberOrNull(value, integer) {
  const text = String(value || "").trim();
  if (!text) {
    return null;
  }
  const number = Number(text);
  return integer ? Math.trunc(number) : number;
}

function emptyToNull(value) {
  const text = String(value || "").trim();
  return text || null;
}

function normalizeGateId(value) {
  const match = String(value || "").match(/G[0-8]$/);
  return match ? match[0] : String(value || "Unknown");
}

function normalizeState(value) {
  return String(value || "unknown").toLowerCase().replaceAll("_", "-").replaceAll(" ", "-");
}

function humanize(value) {
  const text = String(value || "Not recorded").replaceAll("_", " ").replaceAll("-", " ");
  return text.replace(/\b\w/g, (character) => character.toUpperCase());
}

function stripMarkdown(value) {
  return String(value).replace(/\*\*|__|`/g, "").replace(/^>\s*/, "");
}

function shortHash(value) {
  const text = String(value || "unknown");
  return text.length > 12 ? `${text.slice(0, 12)}...` : text;
}

function truncate(value, maxLength) {
  const text = String(value);
  return text.length > maxLength ? `${text.slice(0, maxLength - 3)}...` : text;
}

function formatTime(date) {
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(date);
}

function formatDate(value) {
  if (!value) {
    return "Not recorded";
  }
  const date = new Date(value);
  return Number.isNaN(date.valueOf()) ? String(value) : new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(date);
}

function formatBytes(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) {
    return "Size not recorded";
  }
  if (number < 1024) {
    return `${number} B`;
  }
  if (number < 1024 * 1024) {
    return `${(number / 1024).toFixed(1)} KB`;
  }
  return `${(number / (1024 * 1024)).toFixed(1)} MB`;
}

function setSyncState(message, error) {
  elements.syncState.textContent = message;
  elements.syncState.classList.toggle("is-error", error);
}

function toast(message, error) {
  const item = el("div", error ? "toast error" : "toast", message);
  elements.toastRegion.append(item);
  window.setTimeout(() => item.remove(), 5000);
}

function readError(error) {
  return error instanceof Error ? error.message : String(error || "Unknown local error");
}
