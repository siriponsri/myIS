const VIEW_METADATA = {
  "work-plan": ["Program control", "Work Plan"],
  process: ["Operating protocol", "Research Process"],
  flow: ["Canonical PLAN order", "Interactive Phase → Task Flow"],
  harness: ["Deterministic boundary", "Harness Rules"],
  tools: ["Pinned capability registry", "Tools"],
  "owner-gates": ["Canonical governance ledger", "Owner Gates"],
  artifacts: ["Allowlisted metadata", "Evidence"],
};

const GATE_LABELS = {
  G0: "Integrity & Migration",
  G1: "Reproduction",
  G2: "Track C Development",
  G3: "Track C Freeze",
  G4: "Track S Preflight",
  G5: "Track S Freeze",
  G6: "Joint Test",
  G7: "External Transfer",
  G8: "Publication",
};

const ACTIONS_BY_GATE = {
  G0: ["approve_implementation", "approve_documentation_migration", "approve_cleanup", "anchor_pdf_receipt_chain"],
  G1: ["authorize_reproduction"],
  G2: ["authorize_track_c_development"],
  G3: ["freeze_track_c"],
  G4: ["authorize_track_s"],
  G5: ["freeze_track_s"],
  G6: ["authorize_joint_confirmation"],
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
  governanceCatalog: null,
  gateLedger: null,
  activeGateId: "G0",
  flowFilter: "all",
  refreshing: false,
};

const AUTO_REFRESH_MS = 60000;

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
  window.setInterval(() => {
    if (!document.hidden && !elements.decisionDialog.open) {
      refreshAll();
    }
  }, AUTO_REFRESH_MS);
}

function cacheElements() {
  elements.viewTitle = document.querySelector("#view-title");
  elements.viewKicker = document.querySelector("#view-kicker");
  elements.syncState = document.querySelector("#sync-state");
  elements.refreshButton = document.querySelector("#refresh-button");
  elements.phaseSpine = document.querySelector("#phase-spine");
  elements.planDetail = document.querySelector("#plan-detail");
  elements.projectionStrip = document.querySelector("#projection-strip");
  elements.programFlow = document.querySelector("#program-flow");
  elements.flowProgress = document.querySelector("#flow-progress");
  elements.processContent = document.querySelector("#process-content");
  elements.harnessContent = document.querySelector("#harness-content");
  elements.flowList = document.querySelector("#flow-list");
  elements.flowCanvas = document.querySelector("#flow-canvas");
  elements.flowCaption = document.querySelector("#flow-caption");
  elements.toolsContent = document.querySelector("#tools-content");
  elements.gateSummary = document.querySelector("#gate-summary");
  elements.gateDetail = document.querySelector("#gate-detail");
  elements.ledgerSummary = document.querySelector("#ledger-summary");
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
  elements.gateDecisionContext = document.querySelector("#gate-decision-context");
  elements.scopeOptions = document.querySelector("#scope-options");
  elements.evidenceOptions = document.querySelector("#evidence-options");
  elements.approvalSentence = document.querySelector("#approval-sentence");
  elements.previewApprovalSentence = document.querySelector("#preview-approval-sentence");
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
  elements.decisionForm.elements.status.addEventListener("change", updateDecisionSentence);
  elements.decisionForm.elements.action.addEventListener("change", updateDecisionSentence);
  elements.scopeOptions.addEventListener("change", updateDecisionSentence);
  elements.evidenceOptions.addEventListener("change", updateDecisionSentence);
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
  document.title = `${metadata[1]} | myIS Owner Console`;
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
  if (state.refreshing) {
    return;
  }
  state.refreshing = true;
  elements.refreshButton.disabled = true;
  setSyncState("Refreshing", false);
  try {
    await ensureSession();
    const results = await Promise.allSettled([
      fetchJson("/api/v1/dashboard-snapshot"),
      fetchJson("/api/v1/governance-catalog"),
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
    renderResult(results[1], renderGovernanceCatalog, elements.gateSummary, "Governance catalog unavailable");
    renderResult(results[2], (data) => renderContentBrowser(elements.processContent, data), elements.processContent, "Process documents unavailable");
    renderResult(results[3], (data) => renderContentBrowser(elements.harnessContent, data), elements.harnessContent, "Harness documents unavailable");
    renderResult(results[4], renderFlowCatalog, elements.flowCanvas, "Flow catalog unavailable");
    renderResult(results[5], renderTools, elements.toolsContent, "Tool registry unavailable");
    renderResult(results[6], renderOwnerGates, elements.gateSummary, "Owner Gate ledger unavailable");
    renderResult(results[7], renderArtifacts, elements.artifactGrid, "Artifact catalog unavailable");
    const failures = results.filter((result) => result.status === "rejected").length;
    setSyncState(failures ? `${failures} view${failures === 1 ? "" : "s"} unavailable` : `Updated ${formatTime(new Date())}`, failures > 0);
  } catch (error) {
    elements.newDecisionButton.disabled = true;
    elements.newDecisionButton.title = "Decision entry is unavailable until the local session and Git state can be verified";
    setSyncState(readError(error), true);
  } finally {
    elements.refreshButton.disabled = false;
    state.refreshing = false;
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
  renderProjectionAlignment(snapshot);
  renderProgramFlow(snapshot);
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
    button.dataset.progress = normalizeState(phase.project_state);
    button.classList.toggle("is-active", phase.phase_id === state.activePhaseId);
    const node = el("span", "phase-node", phase.phase_id);
    node.setAttribute("aria-hidden", "true");
    const copy = el("span", "phase-copy");
    copy.append(el("strong", "", phase.title), el("small", "", `${phase.completed_task_count || 0}/${phase.tasks.length} Tasks complete`));
    const gate = el("span", "phase-gate-mark");
    gate.setAttribute("aria-hidden", "true");
    button.append(node, copy, gate);
    button.setAttribute("aria-label", `${phase.phase_id} ${phase.title}. Progress ${projectStateLabel(phase.project_state)}. Evidence ${humanize(phase.evidence_state)}. Authorization ${humanize(phase.governance_state)}.`);
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
  const dependencies = phase.dependencies?.length ? `Depends on ${phase.dependencies.join(", ")} / ต้องผ่าน Phase ก่อนหน้า` : "Starting Phase / ไม่มี dependency ก่อนหน้า";
  titleBlock.append(el("p", "", dependencies));
  const statuses = el("div", "status-pair");
  statuses.append(statusBadge(projectStateLabel(phase.project_state), phase.project_state));
  statuses.append(statusBadge(`Evidence: ${statusLabel(phase.evidence_state)}`, phase.evidence_state));
  statuses.append(statusBadge(`Gate: ${statusLabel(phase.governance_state)}`, phase.governance_state));
  header.append(titleBlock, statuses);

  const context = el("div", "program-context");
  const contextText = el("p", "hash-line", `PLAN ${shortHash(snapshot.plan_sha256)} | Git ${shortHash(snapshot.git_commit)} | ${snapshot.git_dirty ? "Uncommitted files — decisions disabled / มีไฟล์ที่ยังไม่ commit" : "Git clean — preview available / สร้าง Preview ได้"}`);
  context.append(contextText);

  const taskList = el("div", "task-list");
  (phase.tasks || []).forEach((task, index) => taskList.append(renderTask(task, index === 0)));
  elements.planDetail.replaceChildren(header, context, taskList);
}

function renderTask(task, open) {
  const details = el("details", "task-card");
  details.open = open;
  const summary = el("summary");
  summary.append(el("span", "task-id", task.task_id), el("span", "task-title", task.title), el("span", "task-status", projectStateLabel(task.project_state)));
  const body = el("div", "task-body");
  const list = el("dl");
  appendDefinition(list, "Goal / เป้าหมาย", task.goal);
  appendDefinition(list, "Inputs / ข้อมูลเข้า", task.inputs);
  appendDefinition(list, "Outputs / ผลส่งมอบ", task.outputs);
  appendDefinition(list, "Tests / การทดสอบ", task.tests);
  appendDefinition(list, "Acceptance / เกณฑ์ผ่าน", task.acceptance);
  appendDefinition(list, "Owner Gate", task.owner_gate_ids?.join(", ") || "Not required / ไม่ต้องใช้");
  appendDefinition(list, "Budget / stop / งบและจุดหยุด", task.budget_stop);
  appendDefinition(list, "Rollback / วิธีย้อนกลับ", task.rollback);
  appendDefinition(list, "Risk / ความเสี่ยง", task.risk);
  appendDefinition(list, "Required evidence / หลักฐานที่ต้องมี", task.evidence_contract);
  appendDefinition(list, "Dependencies / งานก่อนหน้า", task.dependencies?.join(", ") || "None / ไม่มี");
  appendDefinition(list, "Current progress / สถานะปัจจุบัน", projectStateLabel(task.project_state));
  if (task.unmet_dependencies?.length) {
    appendDefinition(list, "Waiting for / กำลังรอ", task.unmet_dependencies.join(", "));
  }
  appendDefinition(list, "Linear", `${task.linear_issue_id} · ${task.linear_status}`);
  if (task.evidence) {
    appendDefinition(list, "Evidence record", task.evidence.record_id, true);
    appendDefinition(list, "Evidence SHA-256", task.evidence.record_sha256, true);
  }
  body.append(list);
  details.append(summary, body);
  return details;
}

function renderProjectionAlignment(snapshot) {
  const alignment = state.governanceCatalog?.projection_alignment;
  const nodes = [
    ["PLAN", `${snapshot.phase_count} Phase · ${snapshot.task_count} Task`, "Canonical authority"],
    ["Dashboard", `${snapshot.phase_count} Phase · ${snapshot.task_count} Task`, "Local read/decision view"],
    ["Linear", `${snapshot.linear?.task_count || snapshot.task_count} issues · ${snapshot.linear?.project?.status || "Unknown / ไม่ทราบสถานะ"}`, "Work tracking projection"],
    ["MLflow", `${alignment?.mlflow?.document_count ?? "—"} documents · ${alignment?.mlflow?.experiments?.length ?? 6} experiments`, "Rebuildable evidence mirror"],
  ].map(([name, value, role]) => {
    const node = el("div", "projection-node");
    node.append(el("strong", "", name), el("span", "", value), el("span", "", role));
    return node;
  });
  elements.projectionStrip.replaceChildren(...nodes);
}

function renderProgramFlow(snapshot) {
  const phases = Array.isArray(snapshot.phases) ? snapshot.phases : [];
  const allTasks = phases.flatMap((phase) => phase.tasks || []);
  renderFlowProgress(snapshot, phases, allTasks);
  const blocks = phases.map((phase) => {
    const block = el("section", "flow-phase");
    block.id = `flow-phase-${phase.phase_id}`;
    block.dataset.phaseId = phase.phase_id;
    const head = el("div", "flow-phase__head");
    head.append(el("code", "", `Phase ${phase.phase_id}`), el("h2", "", phase.title));
    const states = el("div", "flow-task__meta");
    states.append(statusBadge(projectStateLabel(phase.project_state), phase.project_state));
    states.append(statusBadge(`${phase.completed_task_count || 0}/${phase.tasks.length} Tasks`, phase.project_state));
    states.append(statusBadge(`Gate ${statusLabel(phase.governance_state)}`, phase.governance_state));
    head.append(states);
    const tasks = el("div", "flow-task-list");
    (phase.tasks || []).forEach((task) => {
      const row = el("article", "flow-task");
      row.dataset.projectState = task.project_state;
      row.append(el("div", "flow-task__id", task.task_id));
      const body = el("div", "flow-task__body");
      body.append(el("h3", "", task.title), el("p", "", task.goal));
      const meta = el("div", "flow-task__meta");
      meta.append(el("span", "meta-chip", `Gate ${task.owner_gate_ids?.join(", ") || "—"}`));
      meta.append(el("span", "meta-chip", `Depends on ${task.dependencies?.join(", ") || "none"}`));
      meta.append(el("span", "meta-chip", `${task.linear_issue_id} · ${task.linear_status}`));
      body.append(meta);
      const detail = el("details", "flow-task-details");
      detail.append(el("summary", "", "View full Task details / ดูรายละเอียดทั้งหมด"));
      const definitions = el("dl", "compact-definitions");
      appendDefinition(definitions, "Inputs / ข้อมูลเข้า", task.inputs);
      appendDefinition(definitions, "Outputs / ผลส่งมอบ", task.outputs);
      appendDefinition(definitions, "Tests / การทดสอบ", task.tests);
      appendDefinition(definitions, "Acceptance / เกณฑ์ผ่าน", task.acceptance);
      appendDefinition(definitions, "Budget / stop / งบและจุดหยุด", task.budget_stop);
      appendDefinition(definitions, "Rollback / วิธีย้อนกลับ", task.rollback);
      appendDefinition(definitions, "Risk / ความเสี่ยง", task.risk);
      appendDefinition(definitions, "Evidence / หลักฐาน", task.evidence_contract);
      appendDefinition(definitions, "Progress source / ที่มาสถานะ", task.project_state === "complete" ? "Canonical Task evidence / หลักฐาน Task ที่ตรวจแล้ว" : `Linear ${task.linear_status} + canonical evidence check`);
      if (task.unmet_dependencies?.length) {
        appendDefinition(definitions, "Waiting for / กำลังรอ", task.unmet_dependencies.join(", "));
      }
      detail.append(definitions);
      body.append(detail);
      row.append(body, statusBadge(projectStateLabel(task.project_state), task.project_state));
      tasks.append(row);
    });
    block.append(head, tasks);
    return block;
  });
  elements.programFlow.replaceChildren(...blocks);
  applyFlowFilter();
}

function renderFlowProgress(snapshot, phases, tasks) {
  const complete = Number(snapshot.progress?.completed_task_count || 0);
  const total = tasks.length;
  const percent = Number(snapshot.progress?.completion_percent || 0);
  const summary = el("div", "flow-progress__summary");
  const copy = el("div");
  copy.append(
    el("p", "section-label", "Verified program progress"),
    el("strong", "flow-progress__value", `${complete} of ${total} Tasks complete (${percent}%)`),
    el("p", "flow-progress__note", "Completion requires canonical Task evidence. Linear tracks work; Owner Gates authorize work. / งานจะขึ้น Complete เมื่อหลักฐาน canonical ผ่านแล้วเท่านั้น")
  );
  const meter = document.createElement("progress");
  meter.max = Math.max(total, 1);
  meter.value = complete;
  meter.setAttribute("aria-label", `${complete} of ${total} Tasks complete`);
  summary.append(copy, meter);

  const filters = el("div", "flow-filter");
  filters.setAttribute("role", "group");
  filters.setAttribute("aria-label", "Filter Tasks by project progress");
  const filterDefinitions = [
    ["all", "All / ทั้งหมด"],
    ["active", "Active / กำลังทำ"],
    ["complete", "Complete / เสร็จแล้ว"],
    ["waiting", "Waiting / รอเริ่ม"],
    ["blocked", "Gate blocked / ติด Gate"],
  ];
  filterDefinitions.forEach(([value, label]) => {
    const count = value === "all" ? total : tasks.filter((task) => flowFilterGroup(task.project_state) === value).length;
    const button = el("button", state.flowFilter === value ? "is-active" : "", `${label} · ${count}`);
    button.type = "button";
    button.dataset.flowFilter = value;
    button.setAttribute("aria-pressed", String(state.flowFilter === value));
    button.addEventListener("click", () => {
      state.flowFilter = value;
      renderProgramFlow(snapshot);
    });
    filters.append(button);
  });

  const phaseNav = el("nav", "flow-phase-nav");
  phaseNav.setAttribute("aria-label", "Jump to a PLAN Phase");
  phases.forEach((phase) => {
    const button = el("button", "", phase.phase_id);
    button.type = "button";
    button.title = `${phase.title}: ${phase.completed_task_count || 0}/${phase.tasks.length} Tasks complete`;
    button.addEventListener("click", () => {
      state.flowFilter = "all";
      renderProgramFlow(snapshot);
      document.querySelector(`#flow-phase-${phase.phase_id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
    phaseNav.append(button);
  });
  elements.flowProgress.replaceChildren(summary, filters, phaseNav, el("p", "flow-refresh-note", "Auto-refreshes every 60 seconds while this page is visible / อัปเดตอัตโนมัติทุก 60 วินาที"));
}

function applyFlowFilter() {
  document.querySelectorAll(".flow-task").forEach((row) => {
    const visible = state.flowFilter === "all" || flowFilterGroup(row.dataset.projectState) === state.flowFilter;
    row.hidden = !visible;
  });
  document.querySelectorAll(".flow-phase").forEach((phase) => {
    phase.hidden = !phase.querySelector(".flow-task:not([hidden])");
  });
}

function flowFilterGroup(projectState) {
  if (projectState === "complete") return "complete";
  if (["in_progress", "verification_needed"].includes(projectState)) return "active";
  if (["waiting_gate", "blocked_gate"].includes(projectState)) return "blocked";
  return "waiting";
}

function renderGovernanceCatalog(payload) {
  state.governanceCatalog = payload;
  populateDecisionOptions();
  if (state.snapshot) {
    renderProjectionAlignment(state.snapshot);
  }
  if (state.gateLedger) {
    renderOwnerGates(state.gateLedger);
  }
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
  const styles = getComputedStyle(document.documentElement);
  const colors = {
    faint: styles.getPropertyValue("--color-faint").trim(),
    warning: styles.getPropertyValue("--color-warning").trim(),
    danger: styles.getPropertyValue("--color-danger").trim(),
    dangerSoft: styles.getPropertyValue("--color-danger-soft").trim(),
    accent: styles.getPropertyValue("--color-accent").trim(),
    accentSoft: styles.getPropertyValue("--color-accent-soft").trim(),
    surface: styles.getPropertyValue("--color-surface").trim(),
    lineStrong: styles.getPropertyValue("--color-line-strong").trim(),
    ink: styles.getPropertyValue("--color-ink").trim(),
  };
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
  arrow.setAttribute("fill", colors.faint);
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
    line.setAttribute("stroke", edge.kind?.includes("optional") ? colors.warning : colors.faint);
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
    rect.setAttribute("fill", node.kind === "protected" ? colors.dangerSoft : node.kind === "canonical" || node.kind === "authority" ? colors.accentSoft : colors.surface);
    rect.setAttribute("stroke", node.kind === "protected" ? colors.danger : node.kind === "canonical" || node.kind === "authority" ? colors.accent : colors.lineStrong);
    const idText = document.createElementNS(svgNamespace, "text");
    idText.setAttribute("x", String(position.x));
    idText.setAttribute("y", String(position.y - 7));
    idText.setAttribute("text-anchor", "middle");
    idText.setAttribute("font-family", styles.getPropertyValue("--font-utility").trim());
    idText.setAttribute("font-size", "11");
    idText.setAttribute("font-weight", "700");
    idText.setAttribute("fill", colors.accent);
    idText.textContent = node.node_id;
    const label = document.createElementNS(svgNamespace, "text");
    label.setAttribute("x", String(position.x));
    label.setAttribute("y", String(position.y + 12));
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("font-family", styles.getPropertyValue("--font-body").trim());
    label.setAttribute("font-size", "10");
    label.setAttribute("fill", colors.ink);
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
  state.gateLedger = payload;
  const records = Array.isArray(payload.records) ? payload.records : [];
  const chain = payload.chain || { count: 0, head: null };
  const states = state.snapshot?.gate_states || deriveGateStates(records);
  elements.ledgerSummary.textContent = chain.count
    ? `Verified ${chain.count} immutable records · head ${shortHash(chain.head)}`
    : "No canonical decision record yet / ยังไม่มีคำตัดสินใจ";
  const gates = state.governanceCatalog?.gates || [];
  if (gates.length) {
    if (!gates.some((gate) => gate.gate_id === state.activeGateId)) {
      state.activeGateId = gates[0].gate_id;
    }
    const buttons = gates.map((gate) => {
      const button = el("button", gate.gate_id === state.activeGateId ? "is-active" : "");
      button.type = "button";
      const code = el("span", "gate-code", gate.gate_id);
      const name = el("span", "gate-index__name", GATE_LABELS[gate.gate_id] || gate.name_en);
      name.title = gate.name_en;
      button.append(code, name, statusBadge(statusLabel(states[gate.gate_id] || "pending"), states[gate.gate_id] || "pending"));
      button.addEventListener("click", () => {
        state.activeGateId = gate.gate_id;
        renderOwnerGates(payload);
      });
      return button;
    });
    elements.gateSummary.replaceChildren(...buttons);
    renderGateDetail(gates.find((gate) => gate.gate_id === state.activeGateId), states);
  } else {
    elements.gateSummary.replaceChildren(messageState("Governance catalog unavailable / ข้อมูล Gate ยังไม่พร้อม", "error-state"));
  }
  const rows = records.slice().reverse().map((record) => {
    const row = el("tr");
    const decisionCell = el("td");
    const gate = gates.find((item) => item.gate_id === normalizeGateId(record.gate_id));
    decisionCell.append(el("strong", "", record.display_label || `${statusLabel(record.status)} ${gate?.name_en || normalizeGateId(record.gate_id)}`));
    decisionCell.append(el("p", "hash-line", record.decision_id || "Unknown Decision ID / ไม่ทราบรหัส"));
    if (record.supersedes_decision_id) {
      decisionCell.append(el("p", "hash-line", `Supersedes ${record.supersedes_decision_id} / แก้ไขต่อจากรายการนี้`));
    }
    const details = el("details", "decision-audit");
    details.append(el("summary", "", "View audit data and hashes / ดูข้อมูลตรวจสอบ"));
    const audit = el("dl", "compact-definitions");
    appendDefinition(audit, "Action", actionLabel(record.scope?.action));
    appendDefinition(audit, "Scope", scopeLabel(record.scope));
    appendDefinition(audit, "Rationale / เหตุผล", record.rationale);
    appendDefinition(audit, "Actor hash", record.actor, true);
    appendDefinition(audit, "Git commit", record.git_commit, true);
    appendDefinition(audit, "Scope SHA-256", record.scope_hash, true);
    appendDefinition(audit, "Record SHA-256", record.record_sha256, true);
    appendDefinition(audit, "Prior record", record.prior_record_hash || "Genesis record", true);
    details.append(audit);
    decisionCell.append(details);
    const evidenceCell = el("td");
    const evidence = evidencePackagesForHashes(record.evidence_manifest_hashes || []);
    if (evidence.length) {
      evidence.forEach((item) => evidenceCell.append(el("span", "meta-chip", `${item.title_en} / ${item.title_th}`)));
    } else {
      evidenceCell.append(el("span", "hash-line", record.evidence_manifest_hashes?.length ? `${record.evidence_manifest_hashes.length} uncataloged hashes / hash ที่ไม่มีชื่อ` : "No linked evidence / ไม่มีหลักฐานที่ผูกไว้"));
    }
    const cells = [
      decisionCell,
      el("td", "mono", normalizeGateId(record.gate_id)),
      el("td", "", statusLabel(record.status)),
      el("td", "", formatDate(record.timestamp)),
      evidenceCell,
    ];
    ["Decision", "Gate", "Status", "Date", "Evidence"].forEach((label, index) => cells[index].dataset.label = label);
    row.append(...cells);
    return row;
  });
  if (!rows.length) {
    const row = el("tr");
    const cell = el("td", "", "No canonical Owner Gate decision yet / ยังไม่มีคำตัดสินใจ");
    cell.colSpan = 5;
    row.append(cell);
    rows.push(row);
  }
  elements.decisionTableBody.replaceChildren(...rows);
  populateSupersedesOptions();
}

function renderGateDetail(gate, states) {
  if (!gate) {
    elements.gateDetail.replaceChildren(messageState("Select a Gate to view details / เลือก Gate เพื่อดูรายละเอียด", "empty-state"));
    return;
  }
  const head = el("div", "gate-detail__head");
  const title = el("div");
  title.append(el("p", "eyebrow", gate.gate_id), el("h2", "", gate.name_en), el("p", "gate-name-th", gate.name_th));
  head.append(title, statusBadge(statusLabel(states[gate.gate_id] || "pending"), states[gate.gate_id] || "pending"));
  const purpose = el("p", "gate-purpose", gate.purpose_th);
  const grid = el("div", "gate-explanation-grid");
  const scope = el("section");
  scope.append(el("h3", "", "Covered Phase and Tasks / ขอบเขตงาน"));
  const phaseRow = el("div", "flow-task__meta");
  (gate.phase_ids || []).forEach((phaseId) => phaseRow.append(el("span", "meta-chip", `Phase ${phaseId}`)));
  scope.append(phaseRow);
  const taskList = el("ul");
  (gate.tasks || []).forEach((task) => taskList.append(el("li", "", `${task.task_id} — ${task.title}`)));
  scope.append(taskList);
  const evidence = el("section");
  evidence.append(el("h3", "", "Evidence the Owner should see / หลักฐานที่ต้องตรวจ"));
  const evidenceList = el("ul");
  (gate.required_evidence_th || []).forEach((item) => evidenceList.append(el("li", "", item)));
  evidence.append(evidenceList);
  grid.append(scope, evidence);
  const decision = el("p", "lock-note", `Decision / คำตัดสินใจ: ${gate.decision_th} Still locked / สิ่งที่ยังล็อก: ${gate.still_locked_th}`);
  const button = el("button", "button button-primary", `New ${gate.gate_id} decision`);
  button.type = "button";
  button.disabled = Boolean(state.snapshot?.git_dirty);
  button.addEventListener("click", () => openDecisionDialog(gate.gate_id));
  elements.gateDetail.replaceChildren(head, purpose, grid, decision, button);
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
  const current = gateSelect.value || state.activeGateId;
  const options = (state.governanceCatalog?.gates || []).map((gate) => {
    const option = el("option", "", `${gate.gate_id} — ${gate.name_en} / ${gate.name_th}`);
    option.value = gate.gate_id;
    return option;
  });
  gateSelect.replaceChildren(...options);
  if (options.some((option) => option.value === current)) {
    gateSelect.value = current;
  }
  updateActionOptions();
}

function updateActionOptions() {
  const gateId = elements.decisionForm.elements.gate_id.value || "G0";
  const actionSelect = elements.decisionForm.elements.action;
  const gate = gateById(gateId);
  const options = (gate?.actions || ACTIONS_BY_GATE[gateId] || []).map((action) => {
    const option = el("option", "", actionLabel(action));
    option.value = action;
    return option;
  });
  actionSelect.replaceChildren(...options);
  renderDecisionSelections(gate);
}

function openDecisionDialog(gateId = state.activeGateId) {
  resetDecisionDialog();
  if (gateId && [...elements.decisionForm.elements.gate_id.options].some((option) => option.value === gateId)) {
    elements.decisionForm.elements.gate_id.value = gateId;
    updateActionOptions();
  }
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
  populateDecisionOptions();
  updateActionOptions();
  showDecisionFormStep();
  elements.decisionFormError.textContent = "";
  elements.decisionConfirmError.textContent = "";
  elements.explicitConfirmation.checked = false;
  elements.confirmButton.disabled = true;
}

function renderDecisionSelections(gate) {
  if (!gate) {
    elements.gateDecisionContext.replaceChildren(messageState("Select a Gate / เลือก Gate ก่อน", "empty-state"));
    elements.scopeOptions.replaceChildren();
    elements.evidenceOptions.replaceChildren();
    return;
  }
  const context = el("div");
  context.append(el("h3", "", `${gate.gate_id} — ${gate.name_en}`), el("p", "", gate.name_th), el("p", "", gate.decision_th), el("p", "", `Still locked / ยังล็อก: ${gate.still_locked_th}`));
  elements.gateDecisionContext.replaceChildren(context);

  const phaseRow = el("div", "scope-phase-row");
  (gate.phase_ids || []).forEach((phaseId) => phaseRow.append(el("span", "meta-chip", `Phase ${phaseId}`)));
  const tasks = el("div", "scope-task-list");
  (gate.tasks || []).forEach((task) => {
    const label = el("label", "scope-choice");
    const input = el("input");
    input.type = "checkbox";
    input.name = "task_scope";
    input.value = task.task_id;
    input.dataset.phaseId = task.phase_id;
    input.checked = true;
    const copy = el("span");
    copy.append(el("strong", "", `${task.task_id} — ${task.title}`), el("small", "", `Phase ${task.phase_id}`));
    label.append(input, copy);
    tasks.append(label);
  });
  elements.scopeOptions.replaceChildren(phaseRow, tasks);

  const compatible = (state.governanceCatalog?.evidence_packages || []).filter((item) => (item.gate_ids || []).includes(gate.gate_id));
  if (!compatible.length) {
    elements.evidenceOptions.replaceChildren(el("p", "evidence-empty", "No verified evidence package is available for this Gate, so approval is unavailable. Reject or defer remains available. / ยังไม่มีหลักฐานที่ตรวจแล้ว"));
  } else {
    const list = el("div", "evidence-choice-list");
    compatible.forEach((item) => {
      const label = el("label", "evidence-choice");
      const input = el("input");
      input.type = "checkbox";
      input.name = "evidence_package";
      input.value = item.sha256;
      input.checked = true;
      const copy = el("span");
      copy.append(
        el("strong", "", item.title_en),
        el("small", "detail-thai", item.title_th),
        el("small", "", item.summary_en),
        el("small", "detail-thai", item.summary_th),
        el("small", "hash-line", `SHA-256 ${shortHash(item.sha256)} · ${item.check_count ?? "—"} checks`)
      );
      label.append(input, copy);
      list.append(label);
    });
    elements.evidenceOptions.replaceChildren(list);
  }
  populateSupersedesOptions();
  updateDecisionSentence();
}

function populateSupersedesOptions() {
  const select = elements.decisionForm?.elements.supersedes_decision_id;
  if (!select) {
    return;
  }
  const gateId = elements.decisionForm.elements.gate_id.value || state.activeGateId;
  const current = select.value;
  const first = el("option", "", "Not a correction / ไม่ใช่การแก้ไข record เดิม");
  first.value = "";
  const records = (state.gateLedger?.records || []).filter((record) => normalizeGateId(record.gate_id) === gateId);
  const options = records.map((record) => {
    const option = el("option", "", `${record.decision_id} — ${record.display_label || statusLabel(record.status)}`);
    option.value = record.decision_id;
    return option;
  });
  select.replaceChildren(first, ...options);
  if (options.some((option) => option.value === current)) {
    select.value = current;
  }
}

function updateDecisionSentence() {
  const gate = gateById(elements.decisionForm.elements.gate_id.value);
  if (!gate) {
    elements.approvalSentence.textContent = "Select a Gate to preview the decision sentence / เลือก Gate ก่อน";
    return;
  }
  const status = elements.decisionForm.elements.status.value;
  const selectedTasks = checkedValues("task_scope");
  const selectedEvidence = checkedValues("evidence_package");
  const verb = status === "approved" ? "approves / อนุมัติ" : status === "rejected" ? "rejects / ไม่อนุมัติ" : "defers / ขอข้อมูลเพิ่มสำหรับ";
  elements.approvalSentence.textContent = `Owner ${verb} ${gate.gate_id} — ${gate.name_en} (${gate.name_th}); ${selectedTasks.length} Tasks, ${selectedEvidence.length} verified evidence packages. Still locked / สิ่งที่ยังล็อก: ${gate.still_locked_th}`;
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
    if (!body.scope.task_ids.length && !body.scope.targets.length) {
      throw new Error("Select at least one Task or provide an exact target / เลือก Task หรือระบุ target");
    }
    if (body.status === "approved" && !body.evidence_manifest_hashes.length) {
      throw new Error("Approval requires at least one verified evidence package / ต้องผูกหลักฐานอย่างน้อยหนึ่งชุด");
    }
    const payload = await fetchJson("/api/v1/owner-gates/preview", {
      method: "POST",
      headers: { "content-type": "application/json", "x-csrf-token": state.csrfToken },
      body: JSON.stringify(body),
    });
    state.previewToken = payload.preview_token;
    state.previewRecord = payload.record;
    renderRecordPreview(payload.record);
    elements.previewApprovalSentence.textContent = elements.approvalSentence.textContent;
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
  const taskIds = checkedValues("task_scope").sort();
  const phaseIds = [...new Set(
    [...elements.scopeOptions.querySelectorAll('input[name="task_scope"]:checked')]
      .map((input) => input.dataset.phaseId)
      .filter(Boolean),
  )].sort();
  const scope = {
    action: String(formData.get("action") || ""),
    phase_ids: phaseIds,
    task_ids: taskIds,
    targets: sortedValues(formData.get("targets"), /\r?\n/),
  };
  if (Object.keys(budget).length) {
    scope.budget = budget;
  }
  return compactObject({
    gate_id: String(formData.get("gate_id") || ""),
    status: String(formData.get("status") || ""),
    rationale: String(formData.get("rationale") || "").trim(),
    evidence_manifest_hashes: checkedValues("evidence_package").sort(),
    scope,
    supersedes_decision_id: emptyToNull(formData.get("supersedes_decision_id")),
    display_label: emptyToNull(formData.get("display_label")),
  });
}

function renderRecordPreview(record) {
  const gate = gateById(normalizeGateId(record.gate_id));
  const evidence = evidencePackagesForHashes(record.evidence_manifest_hashes || []);
  const fields = [
    ["Decision / คำตัดสินใจ", record.display_label || `${statusLabel(record.status)} ${gate?.name_en || record.gate_id}`, false],
    ["Gate", `${normalizeGateId(record.gate_id)} — ${gate?.name_en || ""} / ${gate?.name_th || ""}`, false],
    ["Status / ผล", statusLabel(record.status), false],
    ["Scope / ขอบเขต", scopeLabel(record.scope), false],
    ["Evidence / หลักฐาน", evidence.map((item) => `${item.title_en} / ${item.title_th}`).join(" · ") || "No friendly catalog name", false],
    ["Still locked / สิ่งที่ยังล็อก", gate?.still_locked_th || "See OWNER_GATES.md", false],
    ["Decision ID", record.decision_id, true],
    ["Scope SHA-256", record.scope_hash, true],
    ["Rationale / เหตุผล", record.rationale, false],
    ["Actor hash", record.actor, true],
    ["Timestamp / เวลา", record.timestamp, true],
    ["Git commit", record.git_commit, true],
    ["Evidence SHA-256", record.evidence_manifest_hashes?.join("\n") || "None", true],
    ["Prior record hash", record.prior_record_hash || "Genesis record", true],
    ["Supersedes / แก้ไข record", record.supersedes_decision_id || "No", true],
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
    toast(`Recorded ${payload.decision_id} in the canonical ledger / บันทึกแล้ว`, false);
    await refreshAll();
  } catch (error) {
    elements.decisionConfirmError.textContent = readError(error);
    elements.confirmButton.disabled = false;
  }
}

function gateById(gateId) {
  return (state.governanceCatalog?.gates || []).find((gate) => gate.gate_id === gateId);
}

function evidencePackagesForHashes(hashes) {
  const wanted = new Set(hashes || []);
  return (state.governanceCatalog?.evidence_packages || []).filter((item) => wanted.has(item.sha256));
}

function checkedValues(name) {
  return [...elements.decisionForm.querySelectorAll(`input[name="${name}"]:checked`)].map((input) => input.value);
}

function statusLabel(value) {
  const labels = {
    approved: "Approved / อนุมัติแล้ว",
    rejected: "Rejected / ไม่อนุมัติ",
    deferred: "Deferred / รอข้อมูลเพิ่ม",
    pending: "Pending / ยังไม่ตัดสินใจ",
    partial: "Partially approved / อนุมัติบางส่วน",
    mixed: "Mixed states / มีหลายสถานะ",
    conflict: "Conflict / สถานะขัดแย้ง",
    complete: "Complete / ครบ",
    incomplete: "Incomplete / ยังไม่ครบ",
    not_recorded: "No record / ยังไม่มี record",
    stale: "Stale / ล้าสมัย",
    active: "Active / ใช้งานอยู่",
    passed: "Passed / ผ่าน",
    failed: "Failed / ไม่ผ่าน",
    not_required: "Not required / ไม่ต้องใช้",
  };
  return labels[String(value || "")] || humanize(value);
}

function projectStateLabel(value) {
  const labels = {
    complete: "Complete / เสร็จแล้ว",
    in_progress: "In progress / กำลังทำ",
    verification_needed: "Verify evidence / รอตรวจหลักฐาน",
    waiting_dependency: "Waiting on prior work / รองานก่อนหน้า",
    waiting_gate: "Waiting for Gate / รออนุมัติ",
    blocked_gate: "Gate blocked / ติด Gate",
    ready: "Ready to start / พร้อมเริ่ม",
  };
  return labels[String(value || "")] || humanize(value);
}

function actionLabel(value) {
  const labels = {
    approve_implementation: "Approve implementation / อนุมัติงานตาม scope",
    approve_documentation_migration: "Approve document migration / อนุมัติการย้ายเอกสาร",
    approve_cleanup: "Approve exact cleanup targets / อนุมัติรายการ cleanup",
    authorize_reproduction: "Authorize baseline reproduction / อนุญาตทำ baseline ซ้ำ",
    authorize_track_c_development: "Authorize Track C development / อนุญาตพัฒนา Track C",
    freeze_track_c: "Freeze Track C and C1 harness / ตรึง Track C",
    authorize_track_s: "Authorize Track S run / อนุญาตรัน Track S",
    freeze_track_s: "Freeze Track S finalists / ตรึงผล Track S",
    authorize_joint_confirmation: "Authorize one joint confirmation / อนุญาต confirmation หนึ่งครั้ง",
    authorize_transfer: "Authorize external transfer / อนุญาต external transfer",
    authorize_publication: "Approve publication package / อนุมัติชุดตีพิมพ์",
    anchor_pdf_receipt_chain: "Anchor PDF receipt chain / ผูก receipt chain",
  };
  return labels[String(value || "")] || humanize(value);
}

function scopeLabel(scope) {
  if (!scope || typeof scope !== "object") {
    return "No scope / ไม่มี scope";
  }
  const phases = Array.isArray(scope.phase_ids) && scope.phase_ids.length ? `Phase ${scope.phase_ids.join(", ")}` : "";
  const tasks = Array.isArray(scope.task_ids) && scope.task_ids.length ? `Task ${scope.task_ids.join(", ")}` : "";
  const targets = Array.isArray(scope.targets) && scope.targets.length ? `Target ${scope.targets.join(", ")}` : "";
  return [actionLabel(scope.action), phases, tasks, targets].filter(Boolean).join(" · ");
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
