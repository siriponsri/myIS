const VIEW_METADATA = {
  overview: ["Owner control", "Today"],
  data: ["Data boundary", "Data"],
  presentation: ["Research briefing", "Presentation"],
  plan: ["Canonical execution order", "Plan & Tasks"],
  decisions: ["Immutable governance ledger", "Decisions"],
  evidence: ["Verified packages", "Evidence"],
  reference: ["Reference library", "Reference"],
};

const GATE_LABELS = {
  G0: "Integrity and migration",
  G1: "Reproduction",
  G2: "Shared split and Track C development",
  G3: "Track C freeze",
  G4: "Track S provider and baseline lock",
  G5: "Track S freeze",
  G6: "Joint confirmation",
  G7: "External transfer",
  G8: "Publication",
};

const state = {
  csrfToken: "",
  sessionReady: false,
  view: "overview",
  activePhaseId: "F0",
  activeTaskId: "F0.1",
  activeGateId: "G0",
  referenceTab: "process",
  flowFilter: "all",
  planDensity: "readable",
  audienceMode: "owner",
  deliveryMode: "explore",
  flowZoom: 100,
  flowFit: false,
  snapshot: null,
  governanceCatalog: null,
  gateLedger: null,
  artifacts: null,
  content: {},
  flows: null,
  tools: null,
  f1g1: null,
  ownerInbox: null,
  datasets: null,
  presentationTopics: null,
  previewToken: "",
  previewRecord: null,
  refreshing: false,
  lastRevision: "",
};

const AUTO_REFRESH_MS = 60000;
const COMPLETION_RULE = "Completion requires canonical Task evidence";
const elements = {};

document.addEventListener("DOMContentLoaded", initialize);

async function initialize() {
  cacheElements();
  bindNavigation();
  bindActions();
  setInitialRoute();
  renderLoadingStates();
  await refreshAll();
  window.setInterval(() => {
    if (!document.hidden && !elements.decision_dialog.open) refreshAll();
  }, AUTO_REFRESH_MS);
}

function cacheElements() {
  for (const id of [
    "view-title", "view-kicker", "sync-state", "refresh-button", "owner-focus", "overview-readiness", "f1-g1-panel", "overview-map-content",
    "overview-legend", "overview-metrics", "overview-blockers", "overview-recent", "overview-projections", "owner-inbox", "dataset-content",
    "owner-map", "task-workspace", "gate-index", "gate-detail", "ledger-summary", "decision-table-body",
    "evidence-summary", "evidence-grid", "reference-content", "new-decision-button", "decision-dialog",
    "decision-form", "decision-form-step", "decision-preview-step", "decision-form-error", "decision-confirm-error",
    "gate-decision-context", "scope-options", "evidence-options", "preview-approval-sentence", "record-preview",
    "technical-preview", "decision-preview-button", "decision-confirm-button", "decision-back-button",
    "explicit-confirmation", "toast-region", "presentation-content",
  ]) elements[id.replaceAll("-", "_")] = document.getElementById(id);
  elements.main = document.getElementById("main-content");
}

function bindNavigation() {
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => activateView(button.dataset.view, true));
  });
  window.addEventListener("hashchange", setInitialRoute);
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      state.flowFilter = button.dataset.filter;
      renderPlan(state.snapshot);
    });
  });
  document.querySelectorAll("[data-plan-density]").forEach((button) => {
    button.addEventListener("click", () => {
      state.planDensity = button.dataset.planDensity === "compact" ? "compact" : "readable";
      renderPlan();
    });
  });
  document.querySelectorAll("[data-reference]").forEach((button) => {
    button.addEventListener("click", () => {
      state.referenceTab = button.dataset.reference;
      renderReference();
    });
  });
  document.querySelectorAll("[data-audience-mode]").forEach((button) => button.addEventListener("click", () => {
    state.audienceMode = button.dataset.audienceMode;
    renderPresentation();
  }));
  document.querySelectorAll("[data-delivery-mode]").forEach((button) => button.addEventListener("click", () => {
    state.deliveryMode = button.dataset.deliveryMode;
    renderPresentation();
  }));
  const more = document.querySelector("[data-mobile-more]");
  more?.addEventListener("click", () => {
    const open = document.querySelector(".primary-nav").classList.toggle("is-open");
    more.setAttribute("aria-expanded", String(open));
  });
}

function bindActions() {
  elements.refresh_button.addEventListener("click", refreshAll);
  elements.new_decision_button.addEventListener("click", () => openDecisionDialog(state.activeGateId));
  document.getElementById("close-decision-button").addEventListener("click", closeDecisionDialog);
  elements.decision_form.addEventListener("submit", previewDecision);
  elements.decision_confirm_button.addEventListener("click", confirmDecision);
  elements.decision_back_button.addEventListener("click", showDecisionForm);
  elements.explicit_confirmation.addEventListener("change", () => {
    elements.decision_confirm_button.disabled = !elements.explicit_confirmation.checked;
  });
  elements.decision_form.elements.gate_id.addEventListener("change", () => {
    state.activeGateId = elements.decision_form.elements.gate_id.value;
    populateDecisionScope();
    updateDecisionSentence();
  });
  elements.decision_form.elements.status.addEventListener("change", updateDecisionSentence);
  elements.decision_form.elements.action.addEventListener("change", updateDecisionSentence);
  elements.scope_options.addEventListener("change", updateDecisionSentence);
  elements.evidence_options.addEventListener("change", updateDecisionSentence);
  elements.decision_dialog.addEventListener("cancel", (event) => { event.preventDefault(); closeDecisionDialog(); });
}

function setInitialRoute() {
  const route = window.location.hash.replace(/^#\/?/, "");
  const [view, phase, task] = route.split("/");
  const viewId = Object.hasOwn(VIEW_METADATA, view) ? view : "overview";
  state.activePhaseId = phase || state.activePhaseId;
  state.activeTaskId = task || state.activeTaskId;
  activateView(viewId, false);
}

function activateView(viewId, updateHash) {
  state.view = Object.hasOwn(VIEW_METADATA, viewId) ? viewId : "overview";
  document.querySelectorAll("[data-view-panel]").forEach((panel) => panel.classList.toggle("is-visible", panel.dataset.viewPanel === state.view));
  document.querySelectorAll("[data-view]").forEach((button) => {
    const active = button.dataset.view === state.view;
    button.classList.toggle("is-active", active);
    if (active) button.setAttribute("aria-current", "page"); else button.removeAttribute("aria-current");
  });
  const [kicker, title] = VIEW_METADATA[state.view];
  elements.view_kicker.textContent = kicker;
  elements.view_title.textContent = title;
  document.title = `${title} | myIS Owner Console`;
  if (updateHash) {
    const suffix = state.view === "plan" ? `/${state.activePhaseId}/${state.activeTaskId}` : state.view === "decisions" ? `/${state.activeGateId}` : "";
    history.pushState(null, "", `#${state.view}${suffix}`);
    elements.main.focus({ preventScroll: true });
  }
}

function renderLoadingStates() {
  [elements.owner_focus, elements.overview_readiness, elements.overview_map_content, elements.overview_metrics, elements.overview_blockers, elements.overview_recent,
    elements.overview_projections, elements.owner_map, elements.task_workspace, elements.gate_index, elements.gate_detail,
    elements.evidence_summary, elements.evidence_grid, elements.reference_content, elements.f1_g1_panel,
    elements.presentation_content, elements.owner_inbox, elements.dataset_content].forEach((target) => target.replaceChildren(messageState("Loading local projection", "loading-state")));
}

async function refreshAll() {
  if (state.refreshing) return;
  state.refreshing = true;
  elements.refresh_button.disabled = true;
  setSyncState("Refreshing", false);
  try {
    await ensureSession();
    const results = await Promise.allSettled([
      fetchJson("/api/v1/dashboard-snapshot"), fetchJson("/api/v1/governance-catalog"), fetchJson("/api/v1/owner-gates"),
      fetchJson("/api/v1/artifacts"), fetchJson("/api/v1/content/process"), fetchJson("/api/v1/content/harness"),
      fetchJson("/api/v1/tools"), fetchJson("/api/v1/flows"), fetchJson("/api/v1/f1-g1-readiness"),
      fetchJson("/api/v1/presentation-topics"), fetchJson("/api/v1/owner-inbox"), fetchJson("/api/v1/datasets"),
    ]);
    applyResult(results[0], (value) => { state.snapshot = value; });
    applyResult(results[1], (value) => { state.governanceCatalog = value; });
    applyResult(results[2], (value) => { state.gateLedger = value; });
    applyResult(results[3], (value) => { state.artifacts = value; });
    applyResult(results[4], (value) => { state.content.process = value; });
    applyResult(results[5], (value) => { state.content.harness = value; });
    applyResult(results[6], (value) => { state.tools = value; });
    applyResult(results[7], (value) => { state.flows = value; });
    applyResult(results[8], (value) => { state.f1g1 = value; });
    applyResult(results[9], (value) => { state.presentationTopics = value; });
    applyResult(results[10], (value) => { state.ownerInbox = value; });
    applyResult(results[11], (value) => { state.datasets = value; });
    if (state.snapshot && state.lastRevision !== state.snapshot.projection_revision) {
      state.lastRevision = state.snapshot.projection_revision || "legacy";
      normalizeSelection();
      renderAll();
    } else {
      renderDecisions();
      renderEvidence();
      renderReference();
      renderPresentation();
      renderData();
    }
    const failures = results.filter((result) => result.status === "rejected").length;
    setSyncState(failures ? `${failures} view${failures === 1 ? "" : "s"} unavailable` : `Updated ${formatTime(new Date())}`, failures > 0);
  } catch (error) {
    setSyncState(readError(error), true);
  } finally {
    elements.refresh_button.disabled = false;
    state.refreshing = false;
  }
}

function applyResult(result, setter) { if (result.status === "fulfilled") setter(result.value); }

function normalizeSelection() {
  const phase = state.snapshot?.phases?.find((item) => item.phase_id === state.activePhaseId) || state.snapshot?.phases?.[0];
  state.activePhaseId = phase?.phase_id || "F0";
  const task = phase?.tasks?.find((item) => item.task_id === state.activeTaskId) || phase?.tasks?.[0];
  state.activeTaskId = task?.task_id || "";
  if (!state.governanceCatalog?.gates?.some((item) => item.gate_id === state.activeGateId)) state.activeGateId = "G0";
}

function renderAll() {
  renderOverview();
  renderPresentation();
  renderPlan();
  renderDecisions();
  renderEvidence();
  renderReference();
  renderData();
}

function renderOverview() {
  const snapshot = state.snapshot;
  if (!snapshot) {
    [elements.owner_focus, elements.overview_readiness, elements.overview_map_content, elements.overview_metrics, elements.overview_blockers, elements.overview_recent, elements.overview_projections].forEach((target) => target.replaceChildren(messageState("Project status unavailable. Refresh the local projection.", "error-state")));
    renderOwnerInbox();
    return;
  }
  const focus = snapshot.owner_focus || {};
  const gate = gateById(focus.next_gate_id);
  elements.owner_focus.replaceChildren(
    el("div", "attention-copy", el("p", "section-label", focus.mode === "decision" ? "Decision needed" : "Current focus"),
      el("h2", "", focus.headline_en || "Project status"), el("p", "detail-thai", focus.detail_th || "")),
    el("div", "attention-actions", gate ? el("span", "status-badge status-pending", `${gate.name_en} · ${gate.gate_id}`) : null,
      el("button", "button button-primary", focus.mode === "decision" ? "Review decision" : "Open plan", () => focus.mode === "decision" ? openDecisionDialog(focus.next_gate_id) : activateView("plan", true)))
  );
  renderOwnerInbox();
  renderReadiness(snapshot.readiness || {});
  renderF1G1Panel();
  elements.overview_legend.replaceChildren(statusLegend("complete", "Verified"), statusLegend("approved", "Gate approved"), statusLegend("waiting", "Needs attention"));
  renderResearchFlow(elements.overview_map_content);
  const progress = snapshot.progress || {};
  elements.overview_metrics.replaceChildren(
    metric("Verified tasks", `${progress.completed_task_count || 0}/${snapshot.task_count}`, "Canonical evidence only"),
    metric("Owner-approved Gates", `${Object.values(snapshot.gate_states || {}).filter((value) => value === "approved").length}/9`, "Immutable ledger"),
    metric("Phases", `${snapshot.phase_count}`, "PLAN order"),
  );
  const attentionTasks = snapshot.phases.flatMap((phase) => phase.tasks.filter((task) => !["complete"].includes(task.project_state))).slice(0, 5);
  elements.overview_blockers.replaceChildren(el("div", "section-heading", el("div", "", el("p", "section-label", "Attention"), el("h2", "", "What needs review"))), attentionTasks.length ? el("ul", "attention-items", ...attentionTasks.map((task) => el("li", "", el("button", "task-link", `${task.task_id} · ${humanState(task.project_state)}`, () => selectTask(task.phase_id, task.task_id))))) : el("p", "empty-state", "No outstanding task attention."));
  const records = state.gateLedger?.records || [];
  const latest = records[records.length - 1];
  elements.overview_recent.replaceChildren(el("div", "section-heading", el("div", "", el("p", "section-label", "Recent decision"), el("h2", "", latest ? friendlyDecision(latest) : "No decisions recorded"))), latest ? el("p", "muted", formatTime(latest.timestamp)) : el("p", "detail-thai", "ยังไม่มีบันทึกการตัดสินใจ"));
  renderProjectionHealth(snapshot);
}

function renderOwnerInbox() {
  const inbox = state.ownerInbox;
  if (!inbox) return elements.owner_inbox.replaceChildren(messageState("Owner inbox unavailable. Refresh the local projection.", "error-state"));
  const task = inbox.task;
  const gate = inbox.gate || {};
  const action = inbox.mode === "decision"
    ? el("button", "button button-primary", inbox.action_th, () => openDecisionDialog(gate.gate_id))
    : el("button", "button button-primary", inbox.action_th, () => task ? selectTask(task.phase_id, task.task_id) : activateView("plan", true));
  elements.owner_inbox.replaceChildren(
    el("div", "inbox-heading", el("p", "section-label", "สิ่งที่ต้องทำตอนนี้"), el("h2", "", inbox.headline_th), el("p", "muted", inbox.headline_en)),
    el("div", "inbox-grid",
      inboxCard("งาน", task ? `${task.task_id} · ${task.title}` : "ไม่มีงานที่เลือก", task?.goal || "ดูแผนงานเพื่อเลือกงานถัดไป"),
      inboxCard("Gate", gate.gate_id ? `${gate.gate_id} · ${humanState(gate.state)}` : "ยังไม่มี Gate", gate.reason_th || ""),
      inboxCard("ต้องใช้ต่อไป", "ทรัพยากรใน phase ถัดไป", inbox.next_phase_resources || "ไม่มี")
    ),
    el("div", "inbox-footer", action, el("p", "guardrail", inbox.scientific_results_note_th))
  );
}

function inboxCard(label, title, detail) {
  return el("article", "inbox-card", el("p", "section-label", label), el("h3", "", title), el("p", "", detail));
}

function renderResearchFlow(target) {
  if (!state.snapshot) return target.replaceChildren(messageState("Program status unavailable. Refresh the local projection.", "error-state"));
  target.replaceChildren(researchFlowList(false));
}

function researchFlowStatus(phase) {
  if (phase.project_state === "complete") return ["done", "Done"];
  if (phase.project_state === "in_progress") return ["doing", "Doing"];
  if (phase.project_state === "waiting_gate" && phase.tasks.some((task) => task.owner_gate_ids?.some((gateId) => state.snapshot.gate_readiness?.[gateId]?.ready))) return ["needs-owner", "Needs Owner"];
  if (["blocked_gate", "rejected", "conflict"].includes(phase.project_state)) return ["blocked", "Blocked"];
  return ["planned", "Planned"];
}

function researchFlowList(compact) {
  const phases = state.snapshot?.phases || [];
  return el("ol", `research-flow ${compact ? "is-compact" : ""}`, ...phases.map((phase) => {
    const [kind, label] = researchFlowStatus(phase);
    return el("li", `research-flow-step ${kind}`, el("button", "flow-step-button", el("span", "flow-step-state", label), el("strong", "", phase.phase_id), el("span", "", phase.title), { "aria-label": `${phase.phase_id}: ${phase.title}. ${label}.` }, () => selectPhase(phase.phase_id)));
  }));
}

function renderProjectionHealth(snapshot) {
  const alignment = state.governanceCatalog?.projection_alignment;
  const nodes = [
    ["PLAN", `${snapshot.phase_count} Phases · ${snapshot.task_count} Tasks`, "Canonical authority"],
    ["Dashboard", "Local projection", "Read-only view"],
    ["Linear", `${snapshot.linear?.task_count || snapshot.task_count} issues`, "Work tracking"],
    ["MLflow", `${alignment?.mlflow?.document_count ?? "—"} documents`, "Rebuildable mirror"],
  ];
  elements.overview_projections.replaceChildren(el("div", "section-heading", el("div", "", el("p", "section-label", "Projection health"), el("h2", "", "Four systems, one source"))), el("div", "projection-grid", ...nodes.map(([title, value, note]) => el("div", "projection-node", el("strong", "", title), el("span", "", value), el("small", "", note)))));
}

function renderReadiness(readiness) {
  const items = [
    ["F0", readiness.f0 || "review_required"],
    ["G0", readiness.g0 || "review_required"],
    ["F1", readiness.f1 || "review_required"],
    ["G1", readiness.g1 || "review_required"],
  ];
  elements.overview_readiness.replaceChildren(
    el("div", "readiness-copy", el("p", "section-label", "Verified readiness"), el("h2", "", readiness.project_label || "Readiness requires review"), el("p", "muted", "Dashboard projection only. Git and validated immutable artifacts remain authoritative.")),
    el("div", "readiness-states", ...items.map(([label, value]) => el("div", "readiness-state", el("span", "section-label", label), el("span", `status-badge status-${statusClass(value)}`, humanState(value))))),
  );
}

function renderF1G1Panel() {
  const data = state.f1g1;
  if (!data) return;
  if (!data.prepared) {
    elements.f1_g1_panel.replaceChildren(
      el("div", "f1-g1-copy", el("p", "section-label", "F1 / G1 preparation"), el("h2", "", "Owner-local batch not prepared"), el("p", "muted", "Run the dedicated local preparation command. G1 remains pending.")),
      el("span", "status-badge status-pending", "Not prepared"),
    );
    return;
  }
  const split = data.split?.counts || {};
  elements.f1_g1_panel.replaceChildren(
    el("div", "f1-g1-copy", el("p", "section-label", "F1 / G1 preparation"), el("h2", "", "Commitments ready for Owner review"), el("p", "detail-thai", "ข้อมูลจริงยังอยู่ภายนอก Git; หน้านี้แสดงเฉพาะ hash, count และสถานะ validation")),
    el("div", "f1-g1-facts", compactFact("Proposal", shortHash(data.proposal_sha256)), compactFact("Split", `${split.train}/${split.selection}/${split.joint_test}`), compactFact("MLflow", data.mlflow?.status || "not linked"), compactFact("G1", data.gate_status)),
  );
}

function renderPresentation() {
  const target = elements.presentation_content;
  const topic = state.presentationTopics?.topics?.find((item) => item.topic_id === "dapfam");
  if (!target || !topic) return;
  document.querySelectorAll("[data-audience-mode]").forEach((button) => {
    const active = button.dataset.audienceMode === state.audienceMode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  document.querySelectorAll("[data-delivery-mode]").forEach((button) => {
    const active = button.dataset.deliveryMode === state.deliveryMode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  const data = topic.data || {};
  const dataset = state.datasets?.datasets?.[0];
  const registeredCounts = dataset?.inventory_counts || {};
  const counts = data.inventory_counts || { corpus: registeredCounts.corpus || 45336, queries: registeredCounts.queries || 1247, qrels: registeredCounts.relations || 49869 };
  const split = data.split?.counts || { train: 250, selection: 125, joint_test: 872 };
  const domains = data.qrels_domain_distribution || { IN: 0, OUT: 0, NC: 0 };
  const awaiting = "ยังไม่รัน — รอ G1";
  const bodyFor = (section) => state.audienceMode === "peer" ? section.body_en : state.audienceMode === "advisor" ? `${section.body_th} / ${section.body_en}` : section.body_th;
  const sections = topic.sections.map((section) => el(
    "section", "presentation-section", el("p", "section-label", section.title_en), el("h2", "", section.title_th),
    el("p", "presentation-body", bodyFor(section)),
  ));
  target.classList.toggle("is-present-mode", state.deliveryMode === "present");
  target.replaceChildren(
    el("header", "dapfam-header", el("div", "", el("p", "section-label", "Family-level patent retrieval"), el("h2", "", topic.title), el("p", "dapfam-thesis", topic.subtitle_th)), el("span", "status-badge status-pending", data.prepared ? "Prepared / G1 pending" : "Not prepared")),
    el("section", "results-guardrail", el("strong", "", "ยังไม่มีผลการทดลองเชิงวิทยาศาสตร์"), el("p", "", "หน้านี้แสดง protocol, readiness และสถานะงานเท่านั้น ผลการวัดจะปรากฏหลังผ่าน Gate และ validation ที่เกี่ยวข้องเท่านั้น")),
    dataset ? datasetLineage(dataset, true) : null,
    state.snapshot ? el("section", "presentation-flow-scene", el("div", "section-heading", el("div", "", el("p", "section-label", "Done / current / planned"), el("h2", "", "Research program flow"))), researchFlowList(true)) : null,
    el("section", "dataset-ledger", compactFact("Corpus", formatNumber(counts.corpus)), compactFact("Queries", formatNumber(counts.queries)), compactFact("Qrels", formatNumber(counts.qrels))),
    el("section", "claim-boundary", el("strong", "", "ขอบเขตข้ออ้าง"), el("p", "", "DAPFAM วัด family-level retrieval relevance เท่านั้น ไม่ใช่ novelty, validity, infringement, FTO หรือข้อสรุปทางกฎหมาย")),
    el("section", "split-story", el("div", "section-heading", el("div", "", el("p", "section-label", "Seed 42"), el("h2", "", "Fresh governed split")), el("span", "hash-label", data.split ? shortHash(data.split.membership_sha256?.joint_test) : "hash pending")), el("div", "split-track", splitBlock("Train", split.train, 1247), splitBlock("Selection", split.selection, 1247), splitBlock("Joint test", split.joint_test, 1247))),
    el("section", "domain-summary", el("div", "section-heading", el("div", "", el("p", "section-label", "Qrels context"), el("h2", "", "IN / OUT / NC distribution"))), el("div", "domain-bars", domainBar("IN", domains.IN || 0, domains), domainBar("OUT", domains.OUT || 0, domains), domainBar("NC", domains.NC || 0, domains))),
    el("section", "baseline-table", el("div", "section-heading", el("div", "", el("p", "section-label", "Protocol-matched baselines"), el("h2", "", "B0 / B1 / B2")), el("span", "status-badge status-pending", awaiting)), el("div", "baseline-row", el("strong", "", "B0"), el("span", "", "TAC dense top-400"), el("small", "", awaiting)), el("div", "baseline-row", el("strong", "", "B1"), el("span", "", "Dense + BM25, 0.7 / 0.3"), el("small", "", awaiting)), el("div", "baseline-row", el("strong", "", "B2"), el("span", "", "TAC / Abstract / Claim1 RRF"), el("small", "", awaiting))),
    el("div", "presentation-sections", ...sections),
    el("footer", "presentation-footer", el("strong", "", "Decision support, not legal advice"), el("span", "", data.prepared ? `Proposal ${shortHash(data.proposal_sha256)} · scientific metrics 0` : "G1 pending · scientific metrics 0")),
  );
}

function renderData() {
  const target = elements.dataset_content;
  const datasets = state.datasets?.datasets;
  if (!datasets) return target.replaceChildren(messageState("Dataset metadata unavailable. Refresh the local projection.", "error-state"));
  target.replaceChildren(...datasets.map((dataset) => el("article", "dataset-card",
    el("div", "detail-header", el("div", "", el("p", "section-label", "Registered dataset"), el("h2", "", dataset.title)), el("span", "status-badge status-pending", dataset.availability.replaceAll("_", " "))),
    el("p", "detail-thai", dataset.summary_th),
    el("p", "", dataset.claim_boundary_th),
    el("section", "dataset-ledger", compactFact("Corpus", formatNumber(dataset.inventory_counts.corpus)), compactFact("Queries", formatNumber(dataset.inventory_counts.queries)), compactFact("Relations", formatNumber(dataset.inventory_counts.relations))),
    el("dl", "definition-grid", ...definition("Public revision", shortHash(dataset.public_source.revision)), ...definition("License", dataset.public_source.license), ...definition("Configs", dataset.public_source.configs.join(" / ")), ...definition("Access", "Metadata only; raw access disabled"), ...definition("Live fetch", dataset.live_fetch ? "Allowed" : "Disabled"), ...definition("Scientific results", "Not run"), ...definition("Gate", dataset.split_status)),
    el("a", "text-button", "Open public dataset", { href: dataset.public_source.url, target: "_blank", rel: "noopener noreferrer", referrerpolicy: "no-referrer" }),
    datasetLineage(dataset, false),
    el("section", "local-asset-list", el("div", "section-heading", el("div", "", el("p", "section-label", "Local processed assets"), el("h3", "", "ใช้จาก App แบบ pointer"))), ...dataset.local_assets.map((asset) => el("div", "local-asset-row", el("strong", "", asset.asset_id), el("span", "", asset.title), el("small", "", `${asset.disposition} · ${asset.copy_mode} · ${asset.byte_count ? formatBytes(asset.byte_count) : "in-place index"}`)))),
    el("p", "guardrail", "ไม่มี query ID, qrels, split membership, payload หรือผลราย query ใน Dashboard")
  )));
}

function datasetLineage(dataset, compact) {
  const labels = {
    "huggingface-public-card": "Hugging Face public card",
    "APP-DAPFAM-CORE": "App processed snapshot",
    "research-registry": "Research hash / pointer",
    "F1/G1-preparation": "F1 / G1 preparation",
    "B0/B1/B2": "Future B0 / B1 / B2",
  };
  const nodes = [dataset.lineage[0]?.from, ...dataset.lineage.map((edge) => edge.to)].filter(Boolean);
  return el("section", `dataset-lineage ${compact ? "is-compact" : ""}`,
    el("p", "section-label", "Data lineage"),
    el("ol", "lineage-track", ...nodes.map((node, index) => el("li", "lineage-node", el("span", "lineage-index", String(index + 1)), el("strong", "", labels[node] || node))))
  );
}

function formatBytes(value) {
  const bytes = Number(value || 0);
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes >= 1024 ** 2) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${formatNumber(bytes)} bytes`;
}

function compactFact(label, value) { return el("div", "compact-fact", el("span", "section-label", label), el("strong", "", value ?? "—")); }
function shortHash(value) { return value ? `${value.slice(0, 12)}…${value.slice(-8)}` : "pending"; }
function formatNumber(value) { return Number(value || 0).toLocaleString("en-US"); }
function splitBlock(label, value, total) { return el("div", "split-block", el("strong", "", formatNumber(value)), el("span", "", label), el("progress", "split-meter", { max: total, value: Number(value), "aria-label": `${label}: ${value} of ${total}` })); }
function domainBar(label, value, values) { const total = Math.max(1, Object.values(values).reduce((sum, item) => sum + Number(item || 0), 0)); return el("div", "domain-bar", el("span", "", label), el("progress", "domain-meter", { max: total, value: Number(value), "aria-label": `${label}: ${value} of ${total}` }), el("strong", "", formatNumber(value))); }

function renderPlan() {
  if (!state.snapshot) return;
  document.querySelectorAll("[data-filter]").forEach((button) => button.classList.toggle("is-active", button.dataset.filter === state.flowFilter));
  document.querySelectorAll("[data-plan-density]").forEach((button) => {
    const active = button.dataset.planDensity === state.planDensity;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  renderMap(elements.owner_map, state.planDensity === "compact");
  const phase = state.snapshot.phases.find((item) => item.phase_id === state.activePhaseId);
  if (!phase) return;
  const visible = phase.tasks.filter((task) => state.flowFilter === "all" || (state.flowFilter === "complete" ? task.project_state === "complete" : task.project_state !== "complete"));
  const selected = visible.find((task) => task.task_id === state.activeTaskId) || phase.tasks.find((task) => task.task_id === state.activeTaskId) || visible[0] || phase.tasks[0];
  state.activeTaskId = selected?.task_id || "";
  const taskButtons = visible.map((task) => el("button", `task-row ${task.task_id === state.activeTaskId ? "is-active" : ""}`, el("span", "task-row-id", task.task_id), el("span", "task-row-title", task.title), el("span", `status-badge status-${statusClass(task.project_state)}`, humanState(task.project_state)), () => selectTask(phase.phase_id, task.task_id)));
  const detail = selected ? renderTaskDetail(selected) : el("p", "empty-state", "No tasks match this filter.");
  elements.task_workspace.replaceChildren(el("div", "task-list-panel", el("div", "section-heading", el("div", "", el("p", "section-label", `${phase.phase_id} · ${phase.title}`), el("h2", "", `${phase.completed_task_count}/${phase.tasks.length} verified`))), el("div", "task-list", ...taskButtons)), el("article", "task-detail-panel", detail));
}

function renderTaskDetail(task) {
  const gate = task.owner_gate_ids?.map(gateById).find(Boolean);
  return el("div", "", el("div", "detail-header", el("div", "", el("p", "section-label", task.task_id), el("h2", "", task.title)), el("span", `status-badge status-${statusClass(task.project_state)}`, humanState(task.project_state))),
    el("p", "task-goal", task.goal), el("p", "detail-thai", taskDetailThai(task)),
    el("dl", "definition-grid", ...definition("Acceptance", task.acceptance), ...definition("Inputs", task.inputs), ...definition("Outputs", task.outputs), ...definition("Tests", task.tests), ...definition("Dependencies", task.dependencies?.join(", ") || "None"), ...definition("Waiting for", task.unmet_dependencies?.join(", ") || "None"), ...definition("Gate", gate ? `${gate.name_en} (${gate.gate_id})` : "None"), ...definition("Linear", `${task.linear_issue_id} · ${task.linear_status}`)),
    el("details", "detail-drawer", el("summary", "", "Budget, rollback, risk and evidence"), el("dl", "definition-grid", ...definition("Budget / stop", task.budget_stop), ...definition("Rollback", task.rollback), ...definition("Risk", task.risk), ...definition("Evidence contract", task.evidence_contract), ...definition("Evidence state", humanState(task.evidence_state)))),
    task.evidence ? el("details", "technical-audit", el("summary", "", "Technical evidence audit"), el("pre", "", JSON.stringify(task.evidence, null, 2))) : null);
}

function taskDetailThai(task) {
  const stateText = {
    complete: "เสร็จแล้วตามหลักฐาน canonical ของ Task",
    in_progress: "กำลังดำเนินการและยังไม่ถือว่าเสร็จจนกว่าจะมีหลักฐาน canonical",
    ready: "พร้อมเริ่มเมื่อ dependency และ Gate ที่เกี่ยวข้องผ่าน",
    waiting_dependency: "ยังเริ่มไม่ได้เพราะต้องรอ Task ก่อนหน้า",
    waiting_gate: "ยังเริ่มไม่ได้เพราะต้องรอ Owner อนุมัติ Gate",
    blocked_gate: "ถูกหยุดไว้จนกว่า Owner จะแก้หรืออนุมัติ Gate ที่เกี่ยวข้อง",
    verification_needed: "มีสัญญาณงานแล้ว แต่ต้องตรวจหลักฐาน canonical ก่อนนับว่าเสร็จ",
  }[task.project_state] || "สถานะนี้อ้างอิงจาก PLAN, หลักฐาน canonical และ Gate ที่ตรวจสอบแล้ว";
  return `${task.task_id}: ${stateText} ระบบใช้ Linear เป็นตัวติดตามงานเท่านั้น ไม่ใช้แทนหลักฐาน`;
}

function renderMap(target, compact) {
  if (!state.snapshot || !target) return;
  const groups = state.snapshot.plan_graph?.groups || [];
  const phases = state.snapshot.phases || [];
  const rows = groups.map((group) => {
    const phaseButtons = group.phase_ids.map((phaseId) => {
      const phase = phases.find((item) => item.phase_id === phaseId);
      if (!phase) return null;
      const accessibleName = `${phase.phase_id}: ${phase.title}. ${humanState(phase.project_state)}. ${phase.completed_task_count} of ${phase.tasks.length} verified.`;
      return el("button", `phase-node phase-${statusClass(phase.project_state)} ${phase.phase_id === state.activePhaseId ? "is-active" : ""}`, el("span", "phase-code", phase.phase_id), el("span", "phase-name", phase.title), el("span", "phase-progress", `${phase.completed_task_count}/${phase.tasks.length}`), { "aria-label": accessibleName }, () => selectPhase(phase.phase_id));
    }).filter(Boolean);
    return el("div", `map-group ${group.group_id}`, el("div", "map-group-label", group.title_en), el("div", "map-phase-row", ...phaseButtons));
  });
  target.replaceChildren(el("div", `owner-map ${compact ? "is-compact" : ""}`, ...rows), compact ? el("p", "map-caption", "Main path, parallel S1 arms, and CT transfer are shown in the full plan.") : el("p", "map-caption", "Select a Phase to open its Task lane. Dependency relations are validated from the PLAN/Linear projection."));
}

function renderDecisions() {
  const gates = state.governanceCatalog?.gates || [];
  elements.new_decision_button.disabled = !state.snapshot || Boolean(state.snapshot.git_dirty);
  elements.gate_index.replaceChildren(...gates.map((gate) => el("button", gate.gate_id === state.activeGateId ? "is-active" : "", el("span", "gate-code", gate.gate_id), el("span", "gate-name", gate.title_en || gate.name_en), el("span", `status-badge status-${statusClass(state.snapshot?.gate_states?.[gate.gate_id])}`, humanState(state.snapshot?.gate_states?.[gate.gate_id] || "pending")), () => { state.activeGateId = gate.gate_id; renderDecisions(); history.replaceState(null, "", `#decisions/${gate.gate_id}`); })));
  const gate = gateById(state.activeGateId);
  if (!gate) return;
  const stateValue = state.snapshot?.gate_states?.[gate.gate_id] || "pending";
  const evidence = (state.governanceCatalog?.evidence_packages || []).filter((item) => gate.evidence_package_ids?.includes(item.evidence_id));
  elements.gate_detail.replaceChildren(el("div", "detail-header", el("div", "", el("p", "section-label", gate.gate_id), el("h2", "", gate.title_en || gate.name_en)), el("span", `status-badge status-${statusClass(stateValue)}`, humanState(stateValue))), el("p", "gate-purpose", gate.purpose_en || `This Gate controls the ${gate.title_en || gate.name_en} scope.`), el("p", "detail-thai", gate.purpose_th || "รายละเอียด Gate ภาษาไทย"), el("div", "gate-scope-grid", scopeBlock("Opens", gate.opens_scope?.phase_ids?.join(", ") || "Named scope", gate.opens_scope?.action || "Typed action"), scopeBlock("Reviews this work", gate.reviews_scope?.phase_ids?.join(", ") || "Named tasks", `${gate.reviews_scope?.task_ids?.length || 0} Tasks`)), el("section", "gate-section", el("h3", "", "Required evidence"), evidence.length ? el("ul", "clean-list", ...evidence.map((item) => el("li", "", el("strong", "", item.title_en), el("span", "detail-thai", item.title_th), el("small", "", `${item.evidence_role} · ${item.check_count ?? 0} checks`)))) : el("p", "empty-state", "No evidence package is registered for this Gate.")), el("section", "gate-section", el("h3", "", "Still locked"), el("p", "", gate.still_locked_en || "Later phases remain locked until their own Gate.")), el("button", "button button-primary", stateValue === "approved" ? "Record a correction" : "Review this decision", () => openDecisionDialog(gate.gate_id)));
  renderDecisionHistory();
}

function renderDecisionHistory() {
  const records = state.gateLedger?.records || [];
  elements.ledger_summary.textContent = `${records.length} immutable record${records.length === 1 ? "" : "s"}`;
  elements.decision_table_body.replaceChildren(...records.slice().reverse().map((record) => el("tr", "", cell(friendlyDecision(record)), cell(`${record.gate_id} · ${GATE_LABELS[record.gate_id] || "Gate"}`), cell(humanState(record.status)), cell(formatTime(record.timestamp)), cell(`${record.evidence_manifest_hashes?.length || 0} verified package${record.evidence_manifest_hashes?.length === 1 ? "" : "s"}`))));
}

function renderEvidence() {
  const packages = state.governanceCatalog?.evidence_packages || [];
  const roles = ["fixture", "development", "descriptive", "confirmation"];
  elements.evidence_summary.replaceChildren(...roles.map((role) => metric(role[0].toUpperCase() + role.slice(1), packages.filter((item) => item.evidence_role === role).length, role === "confirmation" ? "Not assessable until Owner evaluator" : "Registered package")));
  const artifacts = state.artifacts?.artifacts || [];
  elements.evidence_grid.replaceChildren(...packages.map((item) => el("article", "evidence-item", el("div", "detail-header", el("div", "", el("p", "section-label", item.evidence_role), el("h2", "", item.title_en)), el("span", "status-badge status-complete", "Verified")), el("p", "detail-thai", item.title_th), el("p", "", item.summary_en), el("p", "muted", `${item.gate_ids.join(", ") || "No Gate"} · ${item.phase_ids.join(", ") || "No Phase"}`), el("details", "technical-audit", el("summary", "", "Technical audit"), el("pre", "", JSON.stringify({ evidence_id: item.evidence_id, sha256: item.sha256, schema_version: item.schema_version, source_git_commit: item.source_git_commit }, null, 2))))), artifacts.length ? el("section", "artifact-strip", el("h2", "", "Allowlisted artifacts"), ...artifacts.map((item) => el("p", "", `${item.title_en || item.artifact_id} · ${item.artifact_class || "metadata"}`))) : null);
}

function renderReference() {
  document.querySelectorAll("[data-reference]").forEach((button) => button.classList.toggle("is-active", button.dataset.reference === state.referenceTab));
  const target = elements.reference_content;
  if (state.referenceTab === "alignment") return renderAlignment(target);
  if (state.referenceTab === "flows") return renderFlows(target);
  if (state.referenceTab === "tools") return renderTools(target);
  const payload = state.content[state.referenceTab];
  if (!payload) return target.replaceChildren(messageState("Reference unavailable", "error-state"));
  target.replaceChildren(renderDocumentBrowser(payload));
}

function renderDocumentBrowser(payload) {
  const index = el("nav", "document-index", ...payload.documents.map((document, index) => el("button", index === 0 ? "is-active" : "", document.title, () => showDocument(document, index))));
  const view = el("article", "document-view");
  const showDocument = (document, index) => { view.replaceChildren(el("div", "document-heading", el("p", "section-label", document.source_id), el("h2", "", document.title)), ...document.sections.map((section) => el("section", "document-section", el("h3", "", section.heading), el("pre", "document-body", section.body)))); indexButtons(index); };
  const indexButtons = (active) => index.querySelectorAll("button").forEach((button, position) => button.classList.toggle("is-active", position === active));
  if (payload.documents[0]) showDocument(payload.documents[0], 0);
  return el("div", "document-browser", index, view);
}

function renderTools(target) {
  if (!state.tools) return target.replaceChildren(messageState("Tool registry unavailable", "error-state"));
  target.replaceChildren(el("div", "tool-grid", ...state.tools.tools.map((tool) => el("article", "tool-item", el("p", "section-label", tool.tool_id), el("h2", "", tool.version || "Pinned tool"), el("p", "", tool.adoption || "Registered capability"), el("small", "", tool.commit || tool.repository || "Local registry")))));
}

async function renderFlows(target) {
  if (!state.flows) return target.replaceChildren(messageState("System maps unavailable", "error-state"));
  const list = el("nav", "flow-index", ...state.flows.flows.map((flow, index) => el("button", index === 0 ? "is-active" : "", flow.title, () => loadFlow(flow, list, canvas, caption))));
  const canvas = el("div", "flow-canvas", "", { tabindex: "0", "aria-label": "Flow diagram viewport. Use scrollbars or mouse drag to pan.", "aria-describedby": "flow-caption" });
  const caption = el("p", "flow-caption", "Select a system map.", { id: "flow-caption" });
  const zoomLabel = el("output", "flow-zoom-label", "100%", { "aria-live": "polite", "aria-label": "Flow zoom" });
  const updateViewport = () => applyFlowViewport(canvas, zoomLabel);
  const zoom = (change) => {
    state.flowFit = false;
    state.flowZoom = Math.max(75, Math.min(200, state.flowZoom + change));
    updateViewport();
  };
  const toolbar = el("div", "flow-toolbar",
    el("div", "flow-zoom-actions",
      el("button", "icon-button flow-control", "-", { type: "button", title: "Zoom out", "aria-label": "Zoom out" }, () => zoom(-25)),
      el("button", "button button-secondary flow-reset", "100%", { type: "button", title: "Reset to native size", "aria-label": "Reset to native size" }, () => { state.flowFit = false; state.flowZoom = 100; updateViewport(); }),
      el("button", "icon-button flow-control", "+", { type: "button", title: "Zoom in", "aria-label": "Zoom in" }, () => zoom(25)),
      el("button", "button button-secondary flow-fit", "Fit", { type: "button", title: "Fit diagram to viewport", "aria-label": "Fit diagram to viewport" }, () => { state.flowFit = true; updateViewport(); }),
    ), zoomLabel,
  );
  bindFlowPan(canvas);
  target.replaceChildren(el("div", "flow-browser", list, el("figure", "flow-stage", toolbar, canvas, caption)));
  if (state.flows.flows[0]) loadFlow(state.flows.flows[0], list, canvas, caption);
}

async function loadFlow(flow, list, canvas, caption) {
  list.querySelectorAll("button").forEach((button, index) => button.classList.toggle("is-active", state.flows.flows[index].flow_id === flow.flow_id));
  state.flowFit = false;
  state.flowZoom = 100;
  try {
    const detail = await fetchJson(flow.detail_url);
    canvas.replaceChildren(el("img", "flow-image", "", { src: detail.image_url, alt: detail.title, draggable: "false" }));
    caption.textContent = detail.title;
    applyFlowViewport(canvas, document.querySelector(".flow-zoom-label"));
  } catch (error) { canvas.replaceChildren(messageState(readError(error), "error-state")); }
}

function applyFlowViewport(canvas, zoomLabel) {
  const image = canvas.querySelector(".flow-image");
  if (!image) return;
  image.classList.toggle("is-fit", state.flowFit);
  image.style.width = state.flowFit ? "100%" : `${960 * state.flowZoom / 100}px`;
  zoomLabel.textContent = state.flowFit ? "Fit" : `${state.flowZoom}%`;
}

function bindFlowPan(canvas) {
  let pan = null;
  canvas.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "touch" || event.button !== 0) return;
    pan = { pointerId: event.pointerId, x: event.clientX, y: event.clientY, left: canvas.scrollLeft, top: canvas.scrollTop };
    canvas.setPointerCapture(event.pointerId);
    canvas.classList.add("is-panning");
  });
  canvas.addEventListener("pointermove", (event) => {
    if (!pan || event.pointerId !== pan.pointerId) return;
    canvas.scrollLeft = pan.left - (event.clientX - pan.x);
    canvas.scrollTop = pan.top - (event.clientY - pan.y);
  });
  const stopPan = (event) => {
    if (!pan || event.pointerId !== pan.pointerId) return;
    pan = null;
    canvas.classList.remove("is-panning");
  };
  canvas.addEventListener("pointerup", stopPan);
  canvas.addEventListener("pointercancel", stopPan);
}

function renderAlignment(target) {
  const alignment = state.governanceCatalog?.projection_alignment;
  if (!alignment) return target.replaceChildren(messageState("Alignment unavailable", "error-state"));
  const rows = [["PLAN", `${alignment.plan.phase_count} Phases · ${alignment.plan.task_count} Tasks`, "Canonical execution authority"], ["Dashboard", alignment.dashboard.registry, "Loopback read-only projection"], ["Linear", `${alignment.linear.task_count} tracked issues`, "Work tracking projection"], ["MLflow", `${alignment.mlflow.document_count} governed documents`, alignment.mlflow.experiments.join(", ")]];
  target.replaceChildren(el("section", "alignment-table", el("h2", "", "System alignment"), ...rows.map((row) => el("div", "alignment-row", el("strong", "", row[0]), el("span", "", row[1]), el("small", "", row[2])))));
}

function openDecisionDialog(gateId, supersedes = "") {
  if (!state.governanceCatalog) return;
  state.activeGateId = gateId || state.activeGateId;
  elements.decision_form.reset();
  elements.decision_form.elements.gate_id.value = state.activeGateId;
  elements.decision_form.elements.display_label.value = "";
  elements.decision_form.elements.supersedes_decision_id.value = supersedes;
  populateDecisionOptions();
  populateDecisionScope();
  showDecisionForm();
  elements.decision_dialog.showModal();
}

function populateDecisionOptions() {
  const select = elements.decision_form.elements.gate_id;
  select.replaceChildren(...(state.governanceCatalog?.gates || []).map((gate) => el("option", "", `${gate.title_en || gate.name_en} (${gate.gate_id})`, null, { value: gate.gate_id })));
  select.value = state.activeGateId;
  updateActionOptions();
  const supersede = elements.decision_form.elements.supersedes_decision_id;
  supersede.replaceChildren(el("option", "", "No correction", null, { value: "" }), ...(state.gateLedger?.records || []).filter((record) => record.gate_id === state.activeGateId).map((record) => el("option", "", `${friendlyDecision(record)} · ${formatTime(record.timestamp)}`, null, { value: record.decision_id })));
}

function updateActionOptions() {
  const gate = gateById(elements.decision_form.elements.gate_id.value);
  elements.decision_form.elements.action.replaceChildren(...(gate?.actions || []).map((action) => el("option", "", action.replaceAll("_", " "), null, { value: action })));
}

function populateDecisionScope() {
  const gate = gateById(elements.decision_form.elements.gate_id.value);
  const phases = gate?.reviews_scope?.phase_ids || gate?.phase_ids || [];
  elements.scope_options.replaceChildren(...phases.map((phaseId) => el("label", "scope-choice", el("input", "", "", null, { type: "checkbox", name: "phase_ids", value: phaseId, checked: true }), el("span", "", el("strong", "", phaseId), el("small", "", phaseTitle(phaseId))))));
  const evidence = (state.governanceCatalog?.evidence_packages || []).filter((item) => gate?.evidence_package_ids?.includes(item.evidence_id));
  elements.evidence_options.replaceChildren(...evidence.map((item) => el("label", "evidence-choice", el("input", "", "", null, { type: "checkbox", name: "evidence_manifest_hashes", value: item.sha256, checked: true }), el("span", "", el("strong", "", item.title_en), el("small", "", `${item.evidence_role} · ${item.summary_en}`)))));
  elements.gate_decision_context?.replaceChildren();
  if (gate) elements.gate_decision_context.replaceChildren(el("p", "section-label", `${gate.title_en || gate.name_en} · ${gate.gate_id}`), el("h3", "", `This decision opens ${gate.opens_scope?.phase_ids?.join(", ") || "the named scope"}`), el("p", "detail-thai", gate.purpose_th || "รายละเอียด Gate ภาษาไทย"));
}

async function previewDecision(event) {
  event.preventDefault();
  elements.decision_form_error.textContent = "";
  const form = elements.decision_form;
  const phase_ids = [...form.querySelectorAll("input[name=phase_ids]:checked")].map((input) => input.value).sort();
  const task_ids = [...form.querySelectorAll("input[name=task_ids]:checked")].map((input) => input.value).sort();
  const evidence_manifest_hashes = [...form.querySelectorAll("input[name=evidence_manifest_hashes]:checked")].map((input) => input.value).sort();
  const payload = { gate_id: form.elements.gate_id.value, status: form.elements.status.value, rationale: form.elements.rationale.value.trim(), display_label: form.elements.display_label.value.trim() || null, supersedes_decision_id: form.elements.supersedes_decision_id.value || null, evidence_manifest_hashes, scope: { action: form.elements.action.value, phase_ids, task_ids, targets: [] } };
  try {
    const response = await fetchJson("/api/v1/owner-gates/preview", { method: "POST", headers: { "X-CSRF-Token": state.csrfToken, "Origin": window.location.origin, "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    state.previewToken = response.preview_token; state.previewRecord = response.record;
    elements.preview_approval_sentence.textContent = approvalSentence(response.record);
    elements.record_preview.replaceChildren(...definition("Decision", friendlyDecision(response.record)), ...definition("Gate", `${response.record.gate_id} · ${GATE_LABELS[response.record.gate_id]}`), ...definition("Scope", scopeSummary(response.record.scope)), ...definition("Evidence", `${response.record.evidence_manifest_hashes.length} verified package(s)`));
    elements.technical_preview.textContent = JSON.stringify(response.record, null, 2);
    elements.decision_form_step.hidden = true; elements.decision_preview_step.hidden = false; elements.decision_preview_button.hidden = true; elements.decision_confirm_button.hidden = false; elements.decision_back_button.hidden = false; elements.explicit_confirmation.checked = false; elements.decision_confirm_button.disabled = true;
  } catch (error) { elements.decision_form_error.textContent = readError(error); }
}

async function confirmDecision() {
  elements.decision_confirm_error.textContent = "";
  try { const result = await fetchJson("/api/v1/owner-gates/confirm", { method: "POST", headers: { "X-CSRF-Token": state.csrfToken, "Origin": window.location.origin, "Content-Type": "application/json" }, body: JSON.stringify({ preview_token: state.previewToken, confirm: true }) }); closeDecisionDialog(); toast(`Decision recorded: ${result.decision_id}`); await refreshAll(); } catch (error) { elements.decision_confirm_error.textContent = readError(error); }
}

function showDecisionForm() { elements.decision_form_step.hidden = false; elements.decision_preview_step.hidden = true; elements.decision_preview_button.hidden = false; elements.decision_confirm_button.hidden = true; elements.decision_back_button.hidden = true; }
function closeDecisionDialog() { elements.decision_dialog.close(); state.previewToken = ""; }
function updateDecisionSentence() { if (state.previewRecord) elements.preview_approval_sentence.textContent = approvalSentence(state.previewRecord); }

function selectPhase(phaseId) { state.activePhaseId = phaseId; const phase = state.snapshot?.phases.find((item) => item.phase_id === phaseId); state.activeTaskId = phase?.tasks?.[0]?.task_id || ""; activateView("plan", true); renderPlan(); }
function selectTask(phaseId, taskId) { state.activePhaseId = phaseId; state.activeTaskId = taskId; activateView("plan", true); renderPlan(); }

async function ensureSession(force = false) {
  if (state.sessionReady && !force) return;
  const response = await fetch("/api/v1/session", { credentials: "same-origin", cache: "no-store" });
  const payload = await parseResponse(response); state.csrfToken = payload.csrf_token; state.sessionReady = true;
}

async function fetchJson(url, options = {}) { const response = await fetch(url, { credentials: "same-origin", cache: "no-store", ...options }); return parseResponse(response); }
async function parseResponse(response) { const payload = await response.json().catch(() => ({})); if (!response.ok) throw new Error(payload.detail || `Request failed (${response.status})`); return payload; }
function setSyncState(text, error) { elements.sync_state.textContent = text; elements.sync_state.classList.toggle("is-error", Boolean(error)); }
function gateById(id) { return state.governanceCatalog?.gates?.find((gate) => gate.gate_id === id); }
function phaseTitle(id) { return state.snapshot?.phases.find((phase) => phase.phase_id === id)?.title || id; }
function humanState(value) { return ({ closed: "Closed", complete: "Complete", approved: "Approved", in_progress: "In progress", ready: "Ready", waiting_dependency: "Waiting on dependency", waiting_gate: "Waiting for Gate", blocked_gate: "Gate blocked", verification_needed: "Verify evidence", stale: "Stale", incomplete: "Incomplete", not_recorded: "Not recorded", pending: "Pending", deferred: "Deferred", rejected: "Rejected", conflict: "Conflict", review_required: "Review required" })[value] || "Needs attention"; }
function statusClass(value) { return ["closed", "complete", "approved"].includes(value) ? "complete" : ["in_progress", "ready"].includes(value) ? "active" : ["pending", "waiting_dependency", "waiting_gate"].includes(value) ? "pending" : "blocked"; }
function statusLegend(status, label) { return el("span", "legend-item", el("i", `legend-mark ${statusClass(status)}`, ""), label); }
function metric(label, value, note) { return el("div", "metric-node", el("span", "section-label", label), el("strong", "", value), el("small", "", note)); }
function scopeBlock(title, value, note) { return el("div", "scope-block", el("span", "section-label", title), el("strong", "", value), el("small", "", note)); }
function definition(term, value) { return [el("dt", "", term), el("dd", "", value || "None")]; }
function cell(value) { return el("td", "", value); }
function scopeSummary(scope) { return [...(scope?.phase_ids || []), ...(scope?.task_ids || [])].join(", ") || (scope?.targets || []).join(", "); }
function approvalSentence(record) { return `${record.status === "approved" ? "Approve" : record.status === "deferred" ? "Defer" : "Reject"} ${GATE_LABELS[record.gate_id] || record.gate_id} for ${scopeSummary(record.scope)}.`; }
function friendlyDecision(record) { if (record.display_label) return record.display_label; return `${record.status === "approved" ? "Approved" : record.status === "deferred" ? "Deferred" : "Rejected"} ${GATE_LABELS[record.gate_id] || record.gate_id} (${scopeSummary(record.scope)})`; }
function formatTime(value) { if (!value) return "Unknown date"; try { return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value)); } catch { return value; } }
function readError(error) { return error instanceof Error ? error.message : String(error); }
function toast(message) { const node = el("div", "toast", message); elements.toast_region.append(node); window.setTimeout(() => node.remove(), 5000); }
function messageState(message, className) { return el("p", className, message); }

function el(tag, className = "", ...children) {
  let listener = null; let attributes = {};
  if (children.length && typeof children[children.length - 1] === "function") listener = children.pop();
  if (children.length && children[children.length - 1] && typeof children[children.length - 1] === "object" && !children[children.length - 1].nodeType && !Array.isArray(children[children.length - 1])) attributes = children.pop();
  const node = document.createElement(tag); if (className) node.className = className;
  Object.entries(attributes).forEach(([key, value]) => { if (value === true) node.setAttribute(key, ""); else if (value !== false && value != null) node.setAttribute(key, value); });
  children.flat(Infinity).filter((child) => child !== null && child !== undefined).forEach((child) => node.append(child instanceof Node ? child : document.createTextNode(String(child))));
  if (listener) node.addEventListener("click", listener); return node;
}
