const state = {
  tab: "overview",
  model: null,
  dashboard: null,
  observatoryRegistry: null,
  observatoryGraph: null,
  presentation: null,
  csrf: "",
  reports: null,
  tools: null,
  selectedTaskId: null,
  selectedPhaseId: null,
  selectedNoteId: null,
  boardMode: "simple",
  resultFilter: "all",
  reportType: "",
  search: "",
  audience: "owner",
  presenting: false,
  slideIndex: 0,
};

const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", async () => {
  const requestedTab = location.hash.match(/^#\/(\w+)/)?.[1];
  if (requestedTab && document.getElementById(requestedTab)) state.tab = requestedTab;
  document.querySelector(".skip-link").addEventListener("click", () => {
    window.setTimeout(() => $("main-content").focus(), 0);
  });
  document.querySelectorAll("[data-tab]").forEach((button) => {
    button.addEventListener("click", () => selectTab(button.dataset.tab));
    button.addEventListener("keydown", handleTabKeydown);
  });
  document.querySelectorAll("[data-board-mode]").forEach((button) => button.addEventListener("click", () => setBoardMode(button.dataset.boardMode)));
  document.querySelectorAll("[data-result-filter]").forEach((button) => button.addEventListener("click", () => setResultFilter(button.dataset.resultFilter)));
  $("refresh").addEventListener("click", refresh);
  $("present-shortcut").addEventListener("click", () => selectTab("presentation"));
  $("global-search").addEventListener("input", (event) => {
    state.search = event.target.value.trim().toLocaleLowerCase("th");
    renderFlow();
    renderOutputsResults();
    if (state.reports) renderReports();
  });
  $("report-type").addEventListener("change", async (event) => {
    state.reportType = event.target.value;
    state.selectedNoteId = null;
    await loadReports();
  });
  $("audience").addEventListener("change", async (event) => {
    state.audience = event.target.value;
    state.slideIndex = 0;
    await loadPresentation();
  });
  $("present-toggle").addEventListener("click", togglePresentation);
  $("present-prev").addEventListener("click", () => moveSlide(-1));
  $("present-next").addEventListener("click", () => moveSlide(1));
  $("print-view").addEventListener("click", () => window.print());
  document.addEventListener("keydown", handleKeyboard);
  selectTab(state.tab, false);
  await refresh();
  window.setInterval(() => {
    if (!document.hidden && !state.presenting) refresh();
  }, 60000);
});

async function refresh() {
  $("sync-state").textContent = "กำลังอ่าน projection";
  try {
    const session = await fetchJson("/api/v1/session");
    state.csrf = session.csrf_token;
    [state.model, state.dashboard, state.presentation, state.tools] = await Promise.all([
      fetchJson("/api/v2/snapshot"),
      fetchJson("/api/v2/overview"),
      fetchJson(`/api/v2/presentation/${state.audience}`),
      fetchJson("/api/v2/tools"),
    ]);
    state.selectedTaskId ||= activeTasks()[0]?.task_id || null;
    state.selectedPhaseId ||= state.model?.armindex?.current_phase || activePhases()[0]?.phase_id || null;
    state.observatoryRegistry = null;
    state.observatoryGraph = null;
    renderAll();
    $("sync-state").textContent = `อัปเดต ${new Date().toLocaleTimeString("th-TH", { hour: "2-digit", minute: "2-digit" })}`;
    clearMessage();
  } catch (error) {
    $("sync-state").textContent = "Projection unavailable";
    showMessage(error.message, "error");
  }
}

function selectTab(tab, updateLocation = true) {
  if (!document.getElementById(tab)) return;
  state.tab = tab;
  document.querySelectorAll("[data-tab]").forEach((button) => {
    const active = button.dataset.tab === tab;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  });
  document.querySelectorAll(".panel").forEach((panel) => {
    const active = panel.id === tab;
    panel.classList.toggle("is-visible", active);
    panel.hidden = !active;
  });
  if (updateLocation) history.replaceState(null, "", `#/${tab}`);
  if (tab === "reports") loadReports();
  if (tab === "tools") loadTools();
  if (tab === "presentation") loadPresentation();
  if (["experiments", "artifacts", "prompts", "metrics", "graph"].includes(tab)) loadObservatoryDetails();
}

async function loadObservatoryDetails() {
  if (state.observatoryRegistry && state.observatoryGraph) {
    renderObservatoryDetails();
    return;
  }
  try {
    const [registryResponse, graphResponse] = await Promise.all([
      fetchJson("/api/v2/observatory/registry"),
      fetchJson("/api/v2/observatory/graph"),
    ]);
    state.observatoryRegistry = registryResponse.registry;
    state.observatoryGraph = graphResponse.graph;
    renderObservatoryDetails();
  } catch (error) {
    ["observatory-run-list", "observatory-artifact-list", "observatory-prompt-list", "observatory-metric-list", "observatory-graph"].forEach((id) => {
      const target = $(id);
      if (target) target.innerHTML = `<div class="empty-state">Observatory detail unavailable: ${escapeHtml(error.message)}</div>`;
    });
  }
}

function handleTabKeydown(event) {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  const tabs = [...document.querySelectorAll("[data-tab]")];
  let index = tabs.indexOf(event.currentTarget);
  if (event.key === 'Home') index = 0;
  if (event.key === 'End') index = tabs.length - 1;
  if (event.key === 'ArrowLeft') index = (index - 1 + tabs.length) % tabs.length;
  if (event.key === 'ArrowRight') index = (index + 1) % tabs.length;
  event.preventDefault();
  tabs[index].focus();
  selectTab(tabs[index].dataset.tab);
}

function setBoardMode(mode) {
  state.boardMode = mode;
  document.querySelectorAll("[data-board-mode]").forEach((button) => {
    const active = button.dataset.boardMode === mode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  renderFlow();
}

function setResultFilter(filter) {
  state.resultFilter = filter;
  document.querySelectorAll("[data-result-filter]").forEach((button) => {
    const active = button.dataset.resultFilter === filter;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });
  renderOutputsResults();
}

function renderAll() {
  const project = state.model?.project || {};
  const campaign = activeCampaign();
  const currentPhase = state.model?.armindex?.current_phase || project.active_phase;
  $("campaign-title").textContent = campaign.title || "ArmIndex";
  $("campaign-status").textContent = `${state.model?.armindex?.status || campaign.status || "migration"} · Phase ${currentPhase || "-"} · measured runs ${state.model?.armindex?.counters?.measured_runs || 0}`;
  $("breadcrumb").textContent = `myIS / ArmIndex / ${shortPhase(currentPhase)}`;
  $("revision").textContent = state.model?.read_model_revision ? short(state.model.read_model_revision, 16) : "ยังไม่โหลด";
  renderRibbon();
  renderStatusCards();
  renderObservatorySummary();
  renderObservatoryDetails();
  renderInbox();
  renderLatestEvidence();
  renderReadiness();
  renderP2Readiness();
  renderOverviewRisks();
  renderFlow();
  renderOutputsResults();
  renderEvidence();
  renderDatasets();
  renderGovernance();
  renderTools();
  renderPresentation();
}

function renderRibbon() {
  const current = state.model?.armindex?.current_phase;
  $("phase-ribbon").innerHTML = activePhases().map((phase) => {
    const tone = statusTone(phase.status);
    const selected = phase.phase_id === state.selectedPhaseId;
    return `<button type="button" class="phase-ribbon-item ${phase.phase_id === current ? "is-current" : ""} ${tone === "ready" ? "is-done" : ""} ${selected ? "is-selected" : ""}" data-phase-id="${escapeHtml(phase.phase_id)}" aria-pressed="${selected}"><span class="phase-ribbon-id">${escapeHtml(shortPhase(phase.phase_id))}</span><span class="phase-ribbon-label">${escapeHtml(phaseTitle(phase.phase_id))}</span><span class="phase-ribbon-status">${escapeHtml(phase.status || "planned")}</span></button>`;
  }).join("");
  document.querySelectorAll("[data-phase-id]").forEach((button) => button.addEventListener("click", () => {
    state.selectedPhaseId = button.dataset.phaseId;
    selectTab("flow");
    renderRibbon();
    renderPhaseDetail();
  }));
}

function renderStatusCards() {
  const tasks = activeTasks();
  const done = tasks.filter((task) => ["complete", "measured"].includes(task.status)).length;
  const health = state.model?.projection_health || {};
  const resources = state.model?.resources || {};
  $("status-cards").innerHTML = [
    card("Current Phase", shortPhase(state.model?.armindex?.current_phase), phaseTitle(state.model?.armindex?.current_phase), "A"),
    card("Task evidence", `${done}/${tasks.length}`, "เสร็จพร้อมหลักฐาน", "T"),
    card("ArmIndex evidence", `${state.model?.armindex?.counters?.measured_runs || 0} runs`, "migration only", "E"),
    card("Projection", health.status || "unknown", resources.cpu_only ? "CPU-only" : "ตรวจ execution envelope", "H"),
  ].join("");
}

function observatoryRecords(kind) {
  return state.observatoryRegistry?.records?.[kind] || [];
}

function renderObservatorySummary() {
  const target = $("observatory-summary");
  if (!target) return;
  const obs = state.model?.observatory || {};
  const counters = obs.real_counters || {};
  const boundary = $("observatory-boundary");
  if (boundary) {
    boundary.textContent = obs.scientific_authority ? "Scientific evidence" : obs.status === "ready" ? "Engineering evidence" : "Not yet measured";
    boundary.className = `evidence-badge ${obs.scientific_authority ? "is-scientific" : ""}`;
  }
  const counts = obs.record_counts || {};
  target.innerHTML = `
    <div class="observatory-kpis">
      <article class="observatory-kpi kpi-peach"><span>Lifecycle</span><strong>${escapeHtml(String(counts.runs || 0))}</strong><small>runs captured</small></article>
      <article class="observatory-kpi kpi-mint"><span>Artifacts</span><strong>${escapeHtml(String(obs.validated_artifact_count || 0))}</strong><small>validated pointers</small></article>
      <article class="observatory-kpi kpi-blue"><span>Failure / recovery</span><strong>${escapeHtml(String(obs.failed_child_count || 0))} / ${escapeHtml(String(obs.recovered_child_count || 0))}</strong><small>child branches</small></article>
      <article class="observatory-kpi kpi-lilac"><span>Integrity</span><strong>${escapeHtml(obs.integrity_status || "unknown")}</strong><small>${escapeHtml(String(obs.negative_check_count || 0))} negative checks</small></article>
      <article class="observatory-kpi kpi-ink"><span>ArmIndex counters</span><strong>${escapeHtml(String(state.model?.armindex?.counters?.measured_runs || 0))}</strong><small>measured runs; selection ${escapeHtml(String(state.model?.armindex?.counters?.selection_accesses || 0))}</small></article>
    </div>
    <div class="observatory-story"><div><span class="story-label">Claim boundary</span><strong>${escapeHtml(obs.claim_boundary || "no_measured_claim")}</strong></div><p>${escapeHtml(obs.narrative || "No validated Observatory fixture is available.")}</p><span class="story-next">Next: ${escapeHtml(obs.next_action || "Review the Observatory receipt")}</span></div>`;
}

function renderObservatoryDetails() {
  const runs = observatoryRecords("runs");
  const artifacts = observatoryRecords("artifacts");
  const prompts = observatoryRecords("prompts");
  const metrics = observatoryRecords("metrics");
  const runTarget = $("observatory-run-list");
  if (runTarget) runTarget.innerHTML = runs.map((run) => `<article class="observatory-row"><div><span class="row-kicker">${escapeHtml(run.execution_class || "run")}</span><h3>${escapeHtml(run.summary || run.record_id)}</h3><p><code>${escapeHtml(run.record_id)}</code> · ${escapeHtml(run.phase_id || "-")} · ${escapeHtml(run.task_id || "-")}</p></div><div class="row-meta"><span class="status-chip ${run.status === "succeeded" ? "is-good" : run.status === "failed" ? "is-warning" : ""}">${escapeHtml(run.status || "unknown")}</span><small>authority: ${run.scientific_authority ? "scientific" : "engineering"}</small></div></article>`).join("") || `<div class="empty-state">No validated run records</div>`;
  const artifactTarget = $("observatory-artifact-list");
  if (artifactTarget) artifactTarget.innerHTML = artifacts.map((artifact) => `<article class="observatory-card"><div class="card-topline"><span class="artifact-kind">${escapeHtml(artifact.artifact_type || "artifact")}</span><span class="status-chip is-good">${escapeHtml(artifact.validation_status || "unknown")}</span></div><h3>${escapeHtml(artifact.title || artifact.record_id)}</h3><p>${escapeHtml(artifact.summary || "Aggregate-safe artifact")}</p><dl><div><dt>Produced by</dt><dd><code>${escapeHtml(artifact.producing_run_id || "-")}</code></dd></div><div><dt>Size</dt><dd>${escapeHtml(String(artifact.size_bytes ?? 0))} bytes</dd></div><div><dt>Hash</dt><dd><code>${escapeHtml(short(artifact.content_sha256, 16))}</code></dd></div></dl></article>`).join("") || `<div class="empty-state">No validated artifact records</div>`;
  const promptTarget = $("observatory-prompt-list");
  if (promptTarget) promptTarget.innerHTML = prompts.map((prompt) => `<article class="observatory-card"><div class="card-topline"><span class="artifact-kind">${escapeHtml(prompt.family || "prompt")}</span><span class="status-chip ${prompt.frozen ? "is-good" : ""}">${prompt.frozen ? "frozen" : "mutable"}</span></div><h3>${escapeHtml(prompt.role || prompt.record_id)} <span class="version-tag">v${escapeHtml(prompt.version || "-")}</span></h3><p>${escapeHtml(prompt.summary || "Prompt lineage record")}</p><div class="lineage-chip">${prompt.parent_prompt_id ? `parent ${escapeHtml(prompt.parent_prompt_id)}` : "root prompt"}</div><code>${escapeHtml(short(prompt.content_sha256, 16))}</code></article>`).join("") || `<div class="empty-state">No prompt lineage records</div>`;
  const metricTarget = $("observatory-metric-list");
  if (metricTarget) metricTarget.innerHTML = metrics.map((metric) => `<article class="observatory-card metric-observatory-card"><div class="card-topline"><span class="artifact-kind">${escapeHtml(metric.name || "metric")} @${escapeHtml(String(metric.cutoff || "-"))}</span><span class="status-chip">fixture</span></div><strong class="metric-value">${escapeHtml(String(metric.value ?? "-"))}</strong><p>${escapeHtml(metric.scope || "-")} · ${escapeHtml(metric.data_role || "-")} · n=${escapeHtml(String(metric.n ?? "-"))}</p><small>${escapeHtml(metric.denominator || "aggregate denominator")} · not a scientific claim</small></article>`).join("") || `<div class="empty-state">No validated metric records</div>`;
  const graphTarget = $("observatory-graph");
  const graph = state.observatoryGraph;
  if (graphTarget) {
    if (!graph) graphTarget.innerHTML = `<div class="empty-state">Open Evidence Graph to load lineage detail</div>`;
    else {
      $("observatory-graph-count").textContent = `${graph.nodes?.length || 0} nodes · ${graph.edges?.length || 0} edges`;
      graphTarget.innerHTML = `<div class="graph-flow">${(graph.nodes || []).map((node) => `<div class="graph-node graph-${escapeHtml(node.kind || "record")}"><span>${escapeHtml(node.kind || "record")}</span><strong>${escapeHtml(node.label || node.id)}</strong><code>${escapeHtml(short(node.id, 18))}</code></div>`).join("")}</div><div class="graph-edge-list">${(graph.edges || []).slice(0, 16).map((edge) => `<div><code>${escapeHtml(short(edge.source, 16))}</code><span>${escapeHtml(edge.relation || "binds")}</span><code>${escapeHtml(short(edge.target, 16))}</code></div>`).join("")}</div>`;
    }
  }
}

function renderInbox() {
  const actions = state.model?.owner_inbox || [];
  $("owner-inbox").innerHTML = actions.map((action, index) => `<div class="inbox-row"><span class="action-index">${index + 1}</span><div><strong>${escapeHtml(action.label || action.action_id)}</strong><p>${escapeHtml(action.kind === "constraint" ? "ข้อจำกัดตาม protocol" : "Owner action")}</p></div><span class="task-status ${action.kind === "constraint" ? "locked" : "next"}">${escapeHtml(action.kind || "action")}</span></div>`).join("") || `<div class="empty-state">Agent ดำเนินงานต่อได้โดยไม่ต้องตัดสินใจจาก Owner</div>`;
}

function renderLatestEvidence() {
  const output = state.model?.outputs?.[0];
  const result = state.model?.results?.[0];
  const interpretation = state.model?.interpretations?.find((item) => item.result_id === result?.result_id) || state.model?.interpretations?.[0];
  $("latest-output").innerHTML = output
    ? `<strong>${escapeHtml(output.output_id)}</strong><p>${escapeHtml(output.status || "unknown")} · ${escapeHtml(output.evidence_class || "unclassified")}</p>`
    : `<strong>ยังไม่มี verified output</strong><p>ไม่มี artifact ที่ promote ได้</p>`;
  $("latest-result").innerHTML = result
    ? `<strong>${escapeHtml(result.validity === "valid" ? "Validated result" : "Not measured")}</strong><p>${escapeHtml(result.claim_boundary || "no claim")}</p>`
    : `<strong>Not measured</strong><p>ไม่มี result record</p>`;
  $("current-interpretation").innerHTML = interpretation
    ? `<strong>${escapeHtml(interpretation.status || "pending")}</strong><p>${escapeHtml(interpretation.statement || "ยังไม่มี reviewed interpretation")}</p>`
    : `<strong>ยังไม่มี reviewed interpretation</strong>`;
}

function renderReadiness() {
  const readiness = state.model?.publication_readiness || {};
  const checks = readiness.checks || [];
  const health = state.model?.projection_health || {};
  $("readiness-summary").innerHTML = `<div class="readiness-status"><strong>${escapeHtml(health.status || readiness.status || "blocked")}</strong><span>${checks.filter((check) => ["clear", "complete"].includes(check.status)).length}/${checks.length} checks clear</span></div><ul class="readiness-list">${checks.map((check) => `<li class="${["clear", "complete"].includes(check.status) ? "is-clear" : ""}"><span>${escapeHtml(check.id || "check")}</span><small>${escapeHtml(check.status || "unknown")}</small></li>`).join("") || `<li><span>${escapeHtml(health.reason || "No readiness receipt")}</span></li>`}</ul>`;
}

function renderP2Readiness() {
  const p2 = state.model?.p2_readiness || {};
  if (!p2.phase_id) return;
  const budget = p2.candidate_budget || {};
  const runtime = p2.runtime || {};
  const freeze = p2.freeze_barrier || {};
  const review = p2.official_review || {};
  const fixture = p2.fixture_pilot || {};
  const status = p2.status === "ready_planned_not_measured" ? "ready / planned; not measured" : p2.status || "unknown";
  const checks = [
    ["Official review", review.final_round ? `Round ${review.final_round} ${review.final_verdict || "unknown"} · ${review.evidence_class || "static_contract_review"}` : review.status || "not recorded"],
    ["Fixture pilot", `${fixture.status || "not_executed"} / ${fixture.evidence_class || "fixture"}`],
    ["Measured P2", p2.measured ? "started" : "not started"],
    ["Profile", `${p2.budget_profile_id || "-"} (${short(p2.budget_profile_sha256, 12)})`],
    ["Real candidates", `${p2.candidate_count || 0} / ${budget.max_candidates_total ?? "-"}`],
    ["Real shortlist", `${p2.shortlist_count || 0} / ${budget.max_selection_finalists ?? "-"}`],
    ["Real selection", `${p2.selection_accesses || 0} / ${budget.selection_exposure_limit ?? 1}`],
    ["Runtime", `${runtime.max_wall_clock_seconds ?? "-"}s wall / ${runtime.per_candidate_timeout_seconds ?? "-"}s candidate`],
    ["Freeze barrier", `${freeze.status || "not_started"}; selection ${p2.selection_accesses || 0}/${budget.selection_exposure_limit ?? 1}`],
    ["Protected access", fixture.protected_data_accessed ? "true" : "false"],
    ["Scientific claim", fixture.claim_boundary || "no_measured_claim"],
    ["Resources", `GPU ${p2.resources?.gpu_budget_usd ?? 0} USD; paid API ${p2.resources?.paid_api_budget_usd ?? 0} USD; download ${p2.resources?.network_model_download ? "on" : "off"}`],
    ["Next step", fixture.status === "passed" ? "Owner-local measured preflight" : "Repository-only fixture pilot"],
  ];
  const existing = document.querySelector("#readiness-summary .p2-readiness");
  const html = `<div class="p2-readiness"><div class="readiness-status"><strong>Historical SCOPE P2 · ${escapeHtml(status)}</strong><span>${p2.measured_runs || 0} measured run / ${p2.selection_accesses || 0} selection access</span></div><ul class="readiness-list">${checks.map(([label, value]) => `<li><span>${escapeHtml(label)}</span><small>${escapeHtml(String(value))}</small></li>`).join("")}</ul></div>`;
  if (existing) existing.outerHTML = html; else $("readiness-summary").insertAdjacentHTML("beforeend", html);
}

function renderOverviewRisks() {
  const risks = state.model?.raid || [];
  $("overview-risks").innerHTML = risks.slice(0, 3).map((item) => `<div class="rail-row"><span class="state-dot state-owner" aria-hidden="true"></span><div><strong>${escapeHtml(item.raid_id || item.kind)}</strong><p>${escapeHtml(item.summary || "No summary")}</p></div></div>`).join("") || `<div class="empty-state">ไม่มี active RAID item</div>`;
}

function renderFlow() {
  const tasks = activeTasks().filter((task) => matchesSearch(task.task_id, task.title, task.phase_id, task.status));
  const lanes = state.boardMode === "pm"
    ? [["Not ready", ["waiting_dependency"]], ["Ready", ["ready", "executable", "planned"]], ["In progress", ["in_progress"]], ["Verification", ["verification_needed"]], ["Waiting / blocked", ["waiting_owner", "waiting_external_data", "blocked", "blocked_until_p1", "locked_owner_D2", "locked_owner_D3"]], ["Done", ["complete", "measured"]]]
    : [["Planned", ["waiting_dependency", "ready", "executable", "planned", "waiting_owner", "waiting_external_data", "blocked", "blocked_until_p1", "locked_owner_D2", "locked_owner_D3"]], ["In process", ["in_progress", "verification_needed"]], ["Done", ["complete", "measured"]]];
  const board = lanes.map(([label, statuses]) => ({ label, tasks: tasks.filter((task) => statuses.includes(task.status)) }));
  const wip = activeTasks().filter((task) => ["in_progress", "verification_needed"].includes(task.status)).length;
  $("board-summary").textContent = `${state.boardMode === "pm" ? "PM detail" : "Simple"}: ${tasks.length} tasks · WIP ${wip}/3`;
  $("phase-flow").className = `board-lanes board-${state.boardMode}`;
  $("phase-flow").innerHTML = board.map((lane) => `<section class="board-lane"><header><h3>${escapeHtml(lane.label)}</h3><span>${lane.tasks.length}</span></header><div class="task-list">${lane.tasks.map(taskCard).join("") || `<p class="muted empty-lane">ไม่มี Task</p>`}</div></section>`).join("");
  document.querySelectorAll("[data-task-id]").forEach((button) => button.addEventListener("click", () => {
    state.selectedTaskId = button.dataset.taskId;
    state.selectedPhaseId = activeTasks().find((item) => item.task_id === state.selectedTaskId)?.phase_id || state.selectedPhaseId;
    renderFlow();
    renderRibbon();
  }));
  renderTaskDetail();
  renderPhaseDetail();
  renderMilestones();
}

function taskCard(task) {
  return `<button type="button" class="task-row ${task.task_id === state.selectedTaskId ? "is-selected" : ""}" data-task-id="${escapeHtml(task.task_id)}"><span class="task-row-label"><span class="task-row-id">${escapeHtml(task.task_id)}</span> ${escapeHtml(task.title || "Untitled task")}</span><span class="task-status ${statusTone(task.status)}">${escapeHtml(simpleStatus(task.status))}</span></button>`;
}

function renderTaskDetail() {
  const tasks = activeTasks();
  const task = tasks.find((item) => item.task_id === state.selectedTaskId) || tasks[0];
  if (!task) {
    $("task-detail").innerHTML = `<p class="muted">ไม่มี Task detail</p>`;
    return;
  }
  state.selectedTaskId = task.task_id;
  const evidence = task.evidence_ids || [];
  const next = ["waiting_owner", "locked_owner_D2", "locked_owner_D3"].includes(task.status)
    ? gateName(task)
    : task.status === "blocked" ? "แก้ blocker ตาม evidence record" : "ดำเนินการตาม execution envelope";
  $("task-detail").innerHTML = `<p class="eyebrow">${escapeHtml(task.phase_id)}</p><h3>${escapeHtml(task.task_id)} · ${escapeHtml(task.title || "Untitled")}</h3><div class="detail-grid"><div class="detail-row"><span class="detail-label">สถานะ</span><span class="detail-value">${escapeHtml(task.status || "planned")}</span></div><div class="detail-row"><span class="detail-label">Evidence</span><span class="detail-value">${escapeHtml(evidence.join(", ") || "ยังไม่มี acceptance evidence")}</span></div><div class="detail-row"><span class="detail-label">Definition of Done</span><span class="detail-value">required outputs, checks และ immutable evidence ผ่าน</span></div><div class="detail-row"><span class="detail-label">ขั้นถัดไป</span><span class="detail-value">${escapeHtml(next)}</span></div></div>`;
}

function renderPhaseDetail() {
  const phases = activePhases();
  const phase = phases.find((item) => item.phase_id === state.selectedPhaseId) || phases[0];
  if (!phase) {
    $("phase-detail").innerHTML = `<div class="empty-state">ไม่มี Phase record</div>`;
    return;
  }
  state.selectedPhaseId = phase.phase_id;
  const done = (phase.tasks || []).filter((task) => ["complete", "measured"].includes(task.status)).length;
  const milestone = (state.model?.milestones || []).find((item) => item.milestone_id === phase.phase_id) || {};
  const gate = phase.phase_id === "A5_FINAL_CONFIRMATION" ? "D2_OPEN_FINAL" : phase.phase_id === "A7_PUBLICATION_AND_RELEASE" ? "D3_SUBMIT_RELEASE" : "No Owner gate";
  $("phase-detail").innerHTML = `<div class="phase-detail-grid"><div><span class="detail-label">Phase</span><strong>${escapeHtml(shortPhase(phase.phase_id))} · ${escapeHtml(phaseTitle(phase.phase_id))}</strong></div><div><span class="detail-label">สถานะ</span><strong>${escapeHtml(phase.status || "planned")}</strong></div><div><span class="detail-label">Task evidence</span><strong>${done}/${(phase.tasks || []).length}</strong></div><div><span class="detail-label">Dependency</span><strong>${escapeHtml((milestone.depends_on || []).map(shortPhase).join(", ") || "None")}</strong></div><div><span class="detail-label">Gate</span><strong>${escapeHtml(gate)}</strong></div></div>`;
}

function renderMilestones() {
  const phases = activePhases();
  $("milestone-timeline").innerHTML = phases.map((item, index) => `<article class="milestone ${item.phase_id === state.model?.armindex?.current_phase ? "is-current" : ""}"><span class="milestone-index">${index + 1}</span><div><strong>${escapeHtml(shortPhase(item.phase_id))} · ${escapeHtml(phaseTitle(item.phase_id))}</strong><p>${escapeHtml(item.status || "planned")} · depends on ${index ? escapeHtml(shortPhase(phases[index - 1].phase_id)) : "none"}</p></div></article>`).join("") || `<div class="empty-state">ยังไม่มี milestone registry</div>`;
}

function activeCampaign() {
  return (state.model?.campaigns || []).find((item) => item.authority_status === "active") || {};
}

function activePhases() {
  return state.model?.armindex?.phases || [];
}

function activeTasks() {
  return activePhases().flatMap((phase) => (phase.tasks || []).map((task) => ({ ...task, phase_id: phase.phase_id, evidence_ids: task.evidence_ids || [] })));
}

function renderOutputsResults() {
  const outputs = (state.model?.outputs || []).filter((item) => resultFilterMatch(item.evidence_class || item.status)).filter((item) => matchesSearch(item.output_id, item.phase_id, item.task_id, item.status, item.evidence_class));
  const results = (state.model?.results || []).filter((item) => resultFilterMatch(item.evidence_maturity || item.validity)).filter((item) => matchesSearch(item.result_id, item.phase_id, item.task_id, item.validity, item.claim_boundary));
  $("outputs-grid").innerHTML = outputs.map((item) => `<article class="artifact-card"><div class="item-heading"><span class="status-chip ${item.promotable === false ? "is-warning" : ""}">${escapeHtml(item.evidence_class || item.status || "output")}</span><code>${escapeHtml(short(item.source_sha256, 12))}</code></div><h4>${escapeHtml(item.output_id)}</h4><p>${escapeHtml(item.status || "unknown")} · ${escapeHtml(item.promotable === false ? "not promotable" : "verified")}</p><small>${escapeHtml(item.phase_id || "-")} / ${escapeHtml(item.task_id || "-")}</small></article>`).join("") || `<div class="empty-state">ไม่มี Output ที่ตรงกับตัวกรอง</div>`;
  $("results-grid").innerHTML = results.map((item) => {
    const interpretation = (state.model?.interpretations || []).find((entry) => entry.result_id === item.result_id);
    const measured = item.validity === "valid" && (item.metric_ids || []).length > 0;
    return `<article class="result-card"><div class="item-heading"><span class="status-chip ${measured ? "" : "is-warning"}">${escapeHtml(item.evidence_maturity || "not_run")}</span><span>${escapeHtml(item.validity || "unknown")}</span></div><h4>${escapeHtml(item.result_id)}</h4><dl><div><dt>Metric</dt><dd>${escapeHtml(measured ? (item.metric_ids || []).join(", ") : "Not measured")}</dd></div><div><dt>Uncertainty</dt><dd>${escapeHtml(measured ? "See bound receipt" : "Not available")}</dd></div><div><dt>Controls</dt><dd>${escapeHtml(measured ? "See frozen protocol" : "Not run")}</dd></div><div><dt>Claim boundary</dt><dd>${escapeHtml(item.claim_boundary || "none")}</dd></div></dl><p>${escapeHtml(interpretation?.statement || "ยังไม่มี reviewed interpretation")}</p></article>`;
  }).join("") || `<div class="empty-state">ไม่มี Result ที่ตรงกับตัวกรอง</div>`;
  $("interpretation-ledger").innerHTML = (state.model?.interpretations || []).filter((item) => matchesSearch(item.interpretation_id, item.result_id, item.statement, item.status)).map((item) => `<article><div><strong>${escapeHtml(item.interpretation_id)}</strong><p>${escapeHtml(item.statement || "No statement")}</p></div><div class="claim-boundary"><span>รองรับ</span><strong>${escapeHtml(item.status === "blocked" ? "สถานะ blocked และ recovery evidence" : item.status)}</strong><span>ยังไม่รองรับ</span><strong>final หรือ publication claim</strong></div></article>`).join("") || `<div class="empty-state">ยังไม่มี reviewed interpretation</div>`;
}

function resultFilterMatch(value) {
  const normalized = String(value || "").toLowerCase();
  if (state.resultFilter === "all") return true;
  if (state.resultFilter === "not_run") return normalized.includes("not_run") || normalized === "blocked";
  if (state.resultFilter === "historical") return normalized.includes("historical") || normalized.includes("invalid") || normalized.includes("superseded");
  if (state.resultFilter === "measured") return normalized.includes("measured") || normalized.includes("selection") || normalized.includes("confirm") || normalized === "valid";
  return true;
}

function renderEvidence() {
  const rows = (state.model?.runs || []).filter((run) => matchesSearch(run.run_id, run.experiment_id, run.stage, run.arm));
  const metrics = state.model?.metrics || [];
  $("evidence-table").innerHTML = `<table><thead><tr><th>Run / experiment</th><th>Stage / arm</th><th>Metric</th><th>Receipt</th></tr></thead><tbody>${rows.map((run) => `<tr><td><strong>${escapeHtml(run.run_id)}</strong><small>${escapeHtml(run.experiment_id || "-")}</small></td><td>${escapeHtml(run.stage || "-")}<small>${escapeHtml(run.arm || "-")}</small></td><td>${metrics.filter((metric) => metric.run_id === run.run_id).map((metric) => `${escapeHtml(metric.name || "metric")}: ${escapeHtml(String(metric.value ?? "-"))}`).join("<br>") || "Not measured"}</td><td>${run.owner_local_receipt_sha256 ? `<code>${escapeHtml(short(run.owner_local_receipt_sha256))}</code>` : "No promoted receipt"}</td></tr>`).join("") || `<tr><td colspan="4" class="empty">ยังไม่มี P1 run ที่ promote ได้</td></tr>`}</tbody></table>`;
}

function renderDatasets() {
  const datasets = (state.model?.datasets || []).filter((dataset) => matchesSearch(dataset.dataset_id, dataset.role, dataset.representation, dataset.classification));
  $("dataset-table").innerHTML = `<table><thead><tr><th>Dataset</th><th>Role</th><th>Classification</th><th>Aggregate count</th><th>Source hash</th></tr></thead><tbody>${datasets.map((dataset) => `<tr><td><strong>${escapeHtml(dataset.dataset_id || "dataset")}</strong></td><td>${escapeHtml(dataset.role || "-")}<small>${escapeHtml(dataset.representation || "-")}</small></td><td><span class="status-chip ${dataset.classification === "incompatible" ? "is-warning" : ""}">${escapeHtml(dataset.classification || "unknown")}</span><small>${escapeHtml(dataset.constraint || dataset.protection || "")}</small></td><td>${escapeHtml(Object.entries(dataset.counts || {}).map(([key, value]) => `${key}: ${value}`).join("; ") || "-")}</td><td><code>${escapeHtml(short(dataset.sha256 || "not recorded"))}</code></td></tr>`).join("") || `<tr><td colspan="5" class="empty">ไม่มี safe dataset metadata</td></tr>`}</tbody></table>`;
}

function renderGovernance() {
  const gates = state.model?.gates || [];
  $("gate-grid").innerHTML = gates.map((gate) => `<article class="gate-card"><div class="item-heading"><span class="status-chip ${gate.status === "approved" ? "" : "is-warning"}">${escapeHtml(gate.status || "waiting_owner")}</span><span>Owner only</span></div><h3>${escapeHtml(gate.gate_id)}</h3><p>${escapeHtml(gate.gate_id === "D2_OPEN_FINAL" ? "เปิด final confirmation หลัง freeze audit" : "อนุมัติ submission หรือ external release")}</p><dl><div><dt>Approval unlocks</dt><dd>${escapeHtml(gate.gate_id === "D2_OPEN_FINAL" ? "one-shot final run" : "submission/release")}</dd></div><div><dt>ยังคงล็อก</dt><dd>protected payloads และ manual metric edits</dd></div></dl></article>`).join("") || `<div class="empty-state">ไม่มี Gate record</div>`;
  const raid = state.model?.raid || [];
  $("raid-list").innerHTML = raid.map((item) => `<article><span class="raid-kind">${escapeHtml(item.kind || "risk")}</span><div><strong>${escapeHtml(item.raid_id || "RAID")}</strong><p>${escapeHtml(item.summary || "No summary")}</p></div><span class="task-status ${item.status === "open" ? "locked" : "ready"}">${escapeHtml(item.status || "unknown")}</span></article>`).join("") || `<div class="empty-state">ไม่มี active RAID item</div>`;
  const resources = state.model?.resources || {};
  const resourceRows = [
    ["CPU-only", resources.cpu_only === true ? "Active" : "Review"],
    ["GPU", resources.gpu === true ? "Enabled" : "Locked"],
    ["Paid API", resources.paid_api === true ? "Enabled" : "Locked"],
    ["Budget", `${resources.actual_cost_usd ?? 0} / ${resources.budget_usd ?? "-"} USD`],
  ];
  $("resources-grid").innerHTML = resourceRows.map(([label, value]) => `<article><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></article>`).join("");
  const decisions = state.model?.decisions || [];
  $("decisions-table").innerHTML = `<table><thead><tr><th>Decision</th><th>Status</th><th>Timestamp</th><th>Record</th></tr></thead><tbody>${decisions.map((item) => `<tr><td>${escapeHtml(item.decision_id || "-")}</td><td>${escapeHtml(item.status || "-")}</td><td>${escapeHtml(item.timestamp || item.effective_at || "-")}</td><td><code>${escapeHtml(short(item.record_sha256 || item.sha256))}</code></td></tr>`).join("") || `<tr><td colspan="4" class="empty">ยังไม่มี D2/D3 decision record</td></tr>`}</tbody></table>`;
}

async function loadReports() {
  $("report-list").innerHTML = `<p class="muted">กำลังตรวจ report manifest</p>`;
  const query = state.reportType ? `?note_type=${encodeURIComponent(state.reportType)}` : "";
  try {
    state.reports = await fetchJson(`/api/v2/reports${query}`);
    $("report-revision").textContent = `Revision ${short(state.reports.read_model_revision)}`;
    renderReports();
  } catch (error) {
    $("report-list").innerHTML = `<p class="error-state">รายงานไม่พร้อม: ${escapeHtml(error.message)}</p>`;
    $("report-detail").innerHTML = `<p class="error-state">Report vault ไม่ตรงกับ shared revision</p>`;
    showMessage(error.message, "error");
  }
}

function renderReports() {
  const reports = (state.reports?.reports || []).filter((report) => matchesSearch(report.note_id, report.title, report.note_type, report.phase_id, report.task_id));
  $("report-list").innerHTML = reports.map((report) => `<button class="report-row ${report.note_id === state.selectedNoteId ? "is-selected" : ""}" type="button" data-note-id="${escapeHtml(report.note_id)}"><span><strong>${escapeHtml(report.title)}</strong><small>${escapeHtml(report.note_type)} · ${escapeHtml(report.status || "current")}</small></span><span class="report-badge ${report.stale ? "is-stale" : ""}">${report.stale ? "stale" : report.safe_to_present ? "safe" : "verified"}</span></button>`).join("") || `<p class="muted">ไม่มีรายงานที่ตรงกับตัวกรอง</p>`;
  document.querySelectorAll("[data-note-id]").forEach((button) => button.addEventListener("click", () => openReport(button.dataset.noteId)));
  if ((!state.selectedNoteId || !reports.some((report) => report.note_id === state.selectedNoteId)) && reports.length) openReport(reports[0].note_id);
}

async function openReport(noteId) {
  try {
    const report = await fetchJson(`/api/v2/reports/${encodeURIComponent(noteId)}`);
    state.selectedNoteId = report.note_id;
    renderReports();
    $("report-detail").innerHTML = `<header><p class="eyebrow">${escapeHtml(report.note_type)}</p><h3>${escapeHtml(report.title)}</h3><p class="muted">${escapeHtml(report.status || "current")} · ${escapeHtml(report.evidence_maturity || "non_scientific")} · ${short(report.sha256)}</p></header><div class="report-content">${report.html}</div><footer><button class="button" type="button" data-open-obsidian="${escapeHtml(report.note_id)}">เปิดใน Obsidian</button><button class="button" type="button" data-open-mlflow>เปิด MLflow archive</button></footer>`;
    $("report-detail").querySelector("[data-open-obsidian]").addEventListener("click", () => openObsidian(report.note_id));
    $("report-detail").querySelector("[data-open-mlflow]").addEventListener("click", () => invokeTool("mlflow-start"));
  } catch (error) {
    $("report-detail").innerHTML = `<p class="error-state">เปิดรายงานไม่ได้: ${escapeHtml(error.message)}</p>`;
    showMessage(error.message, "error");
  }
}

async function loadTools() {
  try {
    state.tools = await fetchJson("/api/v2/tools");
    renderTools();
  } catch (error) {
    $("tools-status").innerHTML = `<p class="error-state">Tool status unavailable: ${escapeHtml(error.message)}</p>`;
  }
}

function renderTools() {
  const tools = state.tools || {};
  const mlflow = tools.mlflow || { status: "unknown" };
  const obsidian = tools.obsidian || { status: "unknown" };
  const mlflowAction = mlflow.status === "ready" ? "Open" : "Start & Open";
  $("tools-status").innerHTML = `<article class="tool-card"><div><p class="eyebrow">Read-only evidence archive</p><h3>MLflow</h3><p class="tool-status">${escapeHtml(mlflow.status)}${mlflow.reason ? ` · ${escapeHtml(mlflow.reason)}` : ""}</p></div><div class="tool-actions"><button class="button button-primary" type="button" data-tool-action="mlflow-start">${mlflowAction}</button><details class="advanced-actions"><summary>Advanced</summary><button class="button" type="button" data-tool-action="mlflow-stop">Stop</button><button class="button" type="button" data-tool-action="mlflow-restart">Restart</button></details></div></article><article class="tool-card"><div><p class="eyebrow">Phase / Task report vault</p><h3>Obsidian</h3><p class="tool-status">${escapeHtml(obsidian.status)}${obsidian.note_count ? ` · ${escapeHtml(String(obsidian.note_count))} notes` : ""}${obsidian.reason ? ` · ${escapeHtml(obsidian.reason)}` : ""}</p></div><div class="tool-actions"><button class="button button-primary" type="button" data-tool-action="obsidian-home">Open Vault</button></div></article>`;
  document.querySelectorAll("[data-tool-action]").forEach((button) => button.addEventListener("click", () => invokeTool(button.dataset.toolAction)));
}

async function invokeTool(action) {
  const routes = {
    "mlflow-start": ["/api/v2/tools/mlflow/start", {}],
    "mlflow-stop": ["/api/v2/tools/mlflow/stop", {}],
    "mlflow-restart": ["/api/v2/tools/mlflow/restart", {}],
    "obsidian-home": ["/api/v2/tools/obsidian/open", { note_id: "HOME" }],
  };
  const [path, body] = routes[action] || [];
  if (!path) return;
  try {
    const result = await postJson(path, body);
    state.tools = await fetchJson("/api/v2/tools");
    renderTools();
    if (result.url) window.open(result.url, "_blank", "noopener");
    showMessage(result.status === "opened" ? "เปิด Obsidian แล้ว" : `สถานะเครื่องมือ: ${result.status}`, "success");
  } catch (error) {
    showMessage(`Tool action failed: ${error.message}`, "error");
  }
}

function openObsidian(noteId) {
  return postJson("/api/v2/tools/obsidian/open", { note_id: noteId })
    .then(() => showMessage("เปิด Obsidian แล้ว", "success"))
    .catch((error) => showMessage(`Obsidian unavailable: ${error.message}`, "error"));
}

async function loadPresentation() {
  try {
    state.presentation = await fetchJson(`/api/v2/presentation/${state.audience}`);
    state.slideIndex = 0;
    renderPresentation();
  } catch (error) {
    showMessage(`Presentation unavailable: ${error.message}`, "error");
  }
}

function renderPresentation() {
  const screens = state.presentation?.presentation?.screens || [];
  if (!screens.length) {
    $("presentation-progress").textContent = "0 / 0";
    $("presentation-content").innerHTML = `<div class="empty-state">ยังไม่มี presentation-safe story</div>`;
    return;
  }
  state.slideIndex = Math.max(0, Math.min(state.slideIndex, screens.length - 1));
  $("presentation-progress").textContent = `${state.slideIndex + 1} / ${screens.length}`;
  $("presentation-content").innerHTML = screens.map((screen, index) => `<article class="slide ${index === state.slideIndex ? "is-current-slide" : ""}" ${state.presenting && index !== state.slideIndex ? "hidden" : ""}><div class="slide-number">${String(screen.order).padStart(2, "0")}</div><p class="eyebrow">${escapeHtml(state.audience)} briefing</p><h3>${escapeHtml(screen.title_th)}</h3><p>${escapeHtml(screen.message_th)}</p><footer>${escapeHtml(state.model?.project?.state || "-")} · ${escapeHtml(short(state.model?.read_model_revision, 12))}</footer></article>`).join("");
}

function togglePresentation() {
  state.presenting = !state.presenting;
  document.body.classList.toggle("presentation-mode", state.presenting);
  $("present-toggle").textContent = state.presenting ? "ออกจากการนำเสนอ" : "เริ่มนำเสนอ";
  $("present-toggle").setAttribute("aria-pressed", String(state.presenting));
  renderPresentation();
}

function moveSlide(delta) {
  if (!state.presenting) return;
  const count = state.presentation?.presentation?.screens?.length || 0;
  state.slideIndex = Math.max(0, Math.min(state.slideIndex + delta, Math.max(0, count - 1)));
  renderPresentation();
}

function handleKeyboard(event) {
  if (state.presenting && event.key === "ArrowRight") {
    event.preventDefault();
    moveSlide(1);
  }
  if (state.presenting && event.key === "ArrowLeft") {
    event.preventDefault();
    moveSlide(-1);
  }
  if (state.presenting && event.key === "Escape") togglePresentation();
}

function matchesSearch(...values) {
  if (!state.search) return true;
  return values.some((value) => String(value ?? "").toLocaleLowerCase("th").includes(state.search));
}

function showMessage(message, kind) {
  const target = $("ui-message");
  target.hidden = false;
  target.className = `ui-message is-${kind}`;
  target.textContent = message;
}

function clearMessage() {
  $("ui-message").hidden = true;
}

function card(label, value, detail, icon) {
  return `<article class="metric-card"><div class="metric-kicker"><p class="eyebrow">${escapeHtml(label)}</p><span class="metric-icon" aria-hidden="true">${icon}</span></div><strong>${escapeHtml(value || "-")}</strong><span>${escapeHtml(detail)}</span></article>`;
}

function phaseTitle(id) {
  return ({ A0_MIGRATION_FOUNDATION: "Migration foundation", A1_BASELINES_AND_MULTI_ARM_SCREENING: "Baselines and screening", A2_PER_ARM_AUTOINDEX: "Per-arm AutoIndex", A3_TRANSFER_COMPLEMENTARITY_AND_HARNESSOPT: "Transfer and HarnessOpt", A4_PRODUCTION_TRANSFER_AND_SELECTION: "Production and Selection", A5_FINAL_CONFIRMATION: "Final confirmation", A6_FULL_DAPFAM_MATERIALIZATION_AND_SCALABILITY: "Full-DAPFAM materialization and scalability", A7_PUBLICATION_AND_RELEASE: "Publication and release", P0_FOUNDATION: "Historical foundation", P1_CPU_BASELINE: "Historical CPU baseline", P2_SCOPE_DEVELOPMENT: "Historical SCOPE development", P3_FINAL: "Historical final", P4_PUBLICATION: "Historical publication" })[id] || id || "-";
}

function shortPhase(id) {
  return String(id || "-").split("_", 1)[0];
}

function statusTone(status) {
  if (["complete", "measured", "current", "approved"].includes(status)) return "ready";
  if (["waiting_owner", "waiting_external_data", "blocked", "blocked_until_p1"].includes(status) || String(status || "").includes("locked")) return "locked";
  return "next";
}

function simpleStatus(status) {
  if (["complete", "measured"].includes(status)) return "Done";
  if (["in_progress", "verification_needed"].includes(status)) return "In Process";
  return "Planned";
}

function gateName(task) {
  if (task.status === "locked_owner_D2" || task.phase_id === "A5_FINAL_CONFIRMATION") return "รอ D2_OPEN_FINAL";
  if (task.status === "locked_owner_D3" || task.phase_id === "A7_PUBLICATION_AND_RELEASE") return "รอ D3_SUBMIT_RELEASE";
  return "รอ Owner review";
}

function short(value, length = 12) {
  const text = String(value || "");
  return text ? `${text.slice(0, length)}${text.length > length ? "…" : ""}` : "-";
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>\"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
}

async function fetchJson(path) {
  const response = await fetch(path, { credentials: "same-origin" });
  if (!response.ok) {
    let detail = "";
    try { detail = (await response.json()).detail || ""; } catch (_) {}
    throw new Error(detail || `${response.status} ${path}`);
  }
  return response.json();
}

async function postJson(path, body) {
  const response = await fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "x-csrf-token": state.csrf },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = "";
    try { detail = (await response.json()).detail || ""; } catch (_) {}
    throw new Error(detail || `${response.status} ${path}`);
  }
  return response.json();
}
