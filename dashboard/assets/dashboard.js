const state = { tab: "overview", model: null, dashboard: null, presentation: null, csrf: "", presenting: false, selectedTaskId: null };
const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", async () => {
  document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => selectTab(button.dataset.tab)));
  $("refresh").addEventListener("click", refresh);
  $("present-toggle").addEventListener("click", () => {
    state.presenting = !state.presenting;
    document.body.classList.toggle("presentation-mode", state.presenting);
    $("present-toggle").textContent = state.presenting ? "กลับสู่ dashboard" : "สลับโหมดนำเสนอ";
    renderPresentation();
  });
  await refresh();
});

async function refresh() {
  $("sync-state").textContent = "กำลังอ่านข้อมูล";
  try {
    const session = await fetchJson("/api/v1/session");
    state.csrf = session.csrf_token;
    [state.model, state.dashboard, state.presentation] = await Promise.all([
      fetchJson("/api/v1/read-model"), fetchJson("/api/v1/dashboard"), fetchJson("/api/v1/presentation"),
    ]);
    renderAll();
    $("sync-state").textContent = `อัปเดต ${new Date().toLocaleTimeString("th-TH")}`;
  } catch (error) {
    $("sync-state").textContent = `อ่านข้อมูลไม่ได้: ${error.message}`;
  }
}

function selectTab(tab) {
  state.tab = tab;
  document.querySelectorAll("[data-tab]").forEach((button) => button.classList.toggle("is-active", button.dataset.tab === tab));
  document.querySelectorAll(".panel").forEach((panel) => panel.classList.toggle("is-visible", panel.id === tab));
  if (tab === "presentation") renderPresentation();
}

function renderAll() {
  const model = state.model || {};
  const campaign = model.campaigns?.[0] || {};
  const dashboard = state.dashboard || {};
  $("campaign-title").textContent = campaign.title || "SCOPE / AutoIndex";
  $("campaign-status").textContent = `สถานะ: ${campaign.status || "preparation"} · metric หลัก: ${campaign.primary_metric || "recall_at_100/out"}`;
  $("revision").textContent = model.projection_revision ? `read-model ${short(model.projection_revision)}` : "read-model —";
  renderRibbon();
  renderStatusCards();
  renderInbox();
  renderReadiness();
  renderFlow();
  renderEvidence();
  renderDatasets();
  renderPresentation();
}

function renderRibbon() {
  const phases = state.model?.phases || [];
  const current = state.dashboard?.current_phase;
  $("phase-ribbon").innerHTML = phases.map((phase) => {
    const tone = statusTone(phase.status);
    const stateLabel = tone === "ready" ? "complete" : tone === "locked" ? "locked" : phase.status || "planned";
    return `<div class="phase-ribbon-item ${phase.phase_id === current ? "is-current" : ""} ${tone === "ready" ? "is-done" : ""}"><span class="phase-ribbon-id">${escapeHtml(phase.phase_id)}</span><span class="phase-ribbon-label">${escapeHtml(phaseTitle(phase.phase_id))}</span><span class="phase-ribbon-status">${escapeHtml(stateLabel)}</span></div>`;
  }).join("");
}

function renderStatusCards() {
  const dashboard = state.dashboard || {};
  const model = state.model || {};
  const tasks = model.tasks || [];
  const done = tasks.filter((task) => ["complete", "measured"].includes(task.status)).length;
  const readiness = model.publication_readiness || {};
  const cost = model.cost || {};
  $("status-cards").innerHTML = [
    card("Current phase", dashboard.current_phase || "P0_FOUNDATION", "phase ที่ยังทำงานอยู่", "◈"),
    card("Task progress", `${done}/${tasks.length || 0}`, "งานที่มีสถานะ complete / measured", "✓"),
    card("Runs / metrics", `${model.runs?.length || 0} / ${model.metrics?.length || 0}`, "จาก validated manifest และ aggregate", "∿"),
    card("Readiness", readiness.status || "blocked", cost.actual == null ? `budget ${cost.budget || 100} ${cost.currency || "USD"}` : `${cost.actual} ${cost.currency || "USD"}`, "□"),
  ].join("");
}

function renderInbox() {
  const dashboard = state.dashboard || {};
  const done = dashboard.done || [];
  const next = dashboard.next || [];
  const owner = dashboard.waiting_owner || ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"];
  const command = dashboard.waiting_command || [];
  $("owner-inbox").innerHTML = [
    inboxRow("ready", "ทำแล้ว", done.length ? done.slice(0, 3).join("; ") : "ยังไม่มี measured evidence", done.length),
    inboxRow("next", "ทำต่อได้ทันที", next.length ? next.join("; ") : "รอข้อมูลจากขั้นก่อนหน้า", next.length),
    inboxRow("owner", "รอ Owner ตัดสินใจ", owner.length ? owner.join("; ") : "ไม่มี decision ค้าง", owner.length),
    inboxRow("owner", "รอ Owner ออกคำสั่ง", command.length ? command.join("; ") : "ไม่มีคำสั่งค้าง", command.length),
  ].join("");
}

function renderReadiness() {
  const readiness = state.model?.publication_readiness || {};
  const checks = readiness.checks || [];
  $("readiness-summary").innerHTML = `<div class="readiness-status"><strong>${escapeHtml(readiness.status || "blocked")}</strong><span>${checks.filter((check) => check.status === "clear" || check.status === "complete").length}/${checks.length} checks clear</span></div><ul class="readiness-list">${checks.map((check) => `<li class="${["clear", "complete"].includes(check.status) ? "is-clear" : ""}"><span>${escapeHtml(check.id || "check")}</span><small>${escapeHtml(check.status || "unknown")}</small></li>`).join("") || `<li>ยังไม่มี readiness check</li>`}</ul>`;
}

function renderFlow() {
  const phases = state.model?.phases || [];
  const current = state.dashboard?.current_phase;
  $("phase-flow").innerHTML = phases.map((phase) => `<article class="phase-card ${phase.phase_id === current ? "is-current" : ""} ${statusTone(phase.status) === "ready" ? "is-done" : ""}"><div class="phase-head"><span class="phase-id">${escapeHtml(phase.phase_id)}</span><span class="phase-status ${statusTone(phase.status)}">${escapeHtml(phase.status || "planned")}</span></div><h3>${escapeHtml(phaseTitle(phase.phase_id))}</h3><p>${escapeHtml(phaseDescription(phase.phase_id))}</p><div class="task-list">${(phase.tasks || []).map((task) => `<button type="button" class="task-row ${task.task_id === state.selectedTaskId ? "is-selected" : ""}" data-task-id="${escapeHtml(task.task_id)}"><span class="task-row-label"><span class="task-row-id">${escapeHtml(task.task_id)}</span> ${escapeHtml(task.title || "Untitled task")}</span><span class="task-status ${statusTone(task.status)}">${escapeHtml(shortStatus(task.status))}</span></button>`).join("") || `<span class="muted">ยังไม่มี task ตาม contract</span>`}</div>${gateForPhase(phase.phase_id)}</article>`).join("");
  document.querySelectorAll("[data-task-id]").forEach((button) => button.addEventListener("click", () => {
    state.selectedTaskId = button.dataset.taskId;
    renderFlow();
  }));
  renderTaskDetail();
}

function renderTaskDetail() {
  const tasks = state.model?.tasks || [];
  const task = tasks.find((item) => item.task_id === state.selectedTaskId) || tasks[0];
  if (!task) {
    $("task-detail").innerHTML = `<p class="eyebrow">Task detail</p><h3>ยังไม่มี task</h3><p>read-model ยังไม่ส่ง task ที่แสดงผลได้</p>`;
    return;
  }
  state.selectedTaskId = task.task_id;
  const phase = task.phase_id || "—";
  const evidence = task.evidence_ids?.length ? task.evidence_ids.join(", ") : "ยังไม่มี evidence pointer";
  const waiting = ["waiting_owner", "locked_owner_D2", "locked_owner_D3"].includes(task.status);
  const nextAction = waiting ? (task.status === "locked_owner_D2" ? "รอ D2_OPEN_FINAL" : task.status === "locked_owner_D3" ? "รอ D3_SUBMIT_RELEASE" : "รอ Owner" ) : statusTone(task.status) === "ready" ? "ตรวจ evidence และไป task ถัดไป" : "รันตาม execution envelope";
  $("task-detail").innerHTML = `<p class="eyebrow">Task detail / ${escapeHtml(phase)}</p><h3>${escapeHtml(task.title || task.task_id)}</h3><p>${escapeHtml(phaseDescription(phase))}</p><div class="detail-grid"><div class="detail-row"><span class="detail-label">Task ID</span><span class="detail-value">${escapeHtml(task.task_id)}</span></div><div class="detail-row"><span class="detail-label">Status</span><span class="detail-value">${escapeHtml(task.status || "planned")}</span></div><div class="detail-row"><span class="detail-label">Gate</span><span class="detail-value">${escapeHtml(gateName(task))}</span></div><div class="detail-row"><span class="detail-label">Evidence</span><span class="detail-value">${escapeHtml(evidence)}</span></div><div class="detail-row"><span class="detail-label">Next action</span><span class="detail-value">${escapeHtml(nextAction)}</span></div></div>`;
}

function renderEvidence() {
  const rows = state.model?.runs || [];
  const metrics = state.model?.metrics || [];
  $("evidence-table").innerHTML = `<table><thead><tr><th>Run / Experiment</th><th>Stage / Arm</th><th>Metrics</th><th>Lineage receipt</th></tr></thead><tbody>${rows.map((run) => `<tr><td><strong>${escapeHtml(run.run_id)}</strong><small>${escapeHtml(run.experiment_id || "—")}</small></td><td>${escapeHtml(run.stage || "—")}<small>${escapeHtml(run.arm || "—")}</small></td><td>${metrics.filter((metric) => metric.run_id === run.run_id).map((metric) => `${escapeHtml(metric.name || "metric")}: ${escapeHtml(String(metric.value ?? "—"))}`).join("<br>") || "pending"}</td><td>${run.owner_local_receipt_sha256 ? `<code>${escapeHtml(short(run.owner_local_receipt_sha256))}</code>` : "blocked / fixture"}</td></tr>`).join("") || `<tr><td colspan="4" class="empty">ยังไม่มี measured run ระบบจะไม่สร้างตัวเลขแทนหลักฐาน</td></tr>`}</tbody></table>`;
}

function renderDatasets() {
  const datasets = state.model?.datasets || [];
  $("dataset-table").innerHTML = `<table><thead><tr><th>Dataset</th><th>Role / representation</th><th>Classification</th><th>Count</th><th>Source hash</th></tr></thead><tbody>${datasets.map((dataset) => {
    const counts = Object.entries(dataset.counts || {}).map(([key, value]) => `${key}: ${value ?? "-"}`).join("<br>");
    return `<tr><td><strong>${escapeHtml(dataset.dataset_id || "dataset")}</strong></td><td>${escapeHtml(dataset.role || "-")}<small>${escapeHtml(dataset.representation || "-")}</small></td><td><span class="status-chip ${dataset.classification === "incompatible" ? "is-warning" : ""}">${escapeHtml(dataset.classification || "unknown")}</span><small>${escapeHtml(dataset.constraint || dataset.protection || "")}</small></td><td>${counts || "-"}</td><td><code>${escapeHtml(short(dataset.sha256 || "not recorded"))}</code></td></tr>`;
  }).join("") || `<tr><td colspan="5" class="empty">ยังไม่มี dataset inventory ใน read-model</td></tr>`}</tbody></table>`;
}

function renderPresentation() {
  const sections = state.presentation?.sections || [];
  const dashboard = state.dashboard || {};
  const signal = dashboard.waiting_command?.length ? "Awaiting owner command" : dashboard.waiting_owner?.length ? "Awaiting owner decision" : dashboard.current_phase === "P2_SCOPE_DEVELOPMENT" ? "Awaiting review before P2" : "Execution in progress";
  const intro = `<article class="slide slide-lead"><p class="eyebrow">myIS Research / ${escapeHtml(dashboard.current_phase || "P0_FOUNDATION")}</p><h3>Grounded evidence compilers for patent retrieval</h3><p>${escapeHtml(state.model?.campaigns?.[0]?.primary_metric || "recall_at_100/out")} เป็น metric หลักที่ใช้ติดตามเมื่อ evidence พร้อม</p><div class="slide-signal"><strong>${escapeHtml(signal)}</strong><span>${escapeHtml(dashboard.waiting_owner?.join(" · ") || "Standing authorization D1")}</span></div></article>`;
  $("presentation-content").innerHTML = intro + sections.map((section) => `<article class="slide"><p class="eyebrow">${escapeHtml(section.title_en)}</p><h3>${escapeHtml(section.title_th)}</h3><p>${typeof section.body === "string" ? escapeHtml(section.body) : `<strong>Phase:</strong> ${escapeHtml(section.body?.phase || "—")}<br><strong>Runs:</strong> ${escapeHtml(String(section.body?.runs || 0))}<br><strong>Readiness:</strong> ${escapeHtml(section.body?.readiness || "blocked")}`}</p></article>`).join("");
}

function card(label, value, detail, icon) { return `<article class="metric-card"><div class="metric-kicker"><p class="eyebrow">${escapeHtml(label)}</p><span class="metric-icon" aria-hidden="true">${icon}</span></div><strong>${escapeHtml(value)}</strong><span>${escapeHtml(detail)}</span></article>`; }
function inboxRow(kind, title, body, count) { return `<div class="inbox-row"><span class="state-dot state-${kind}"></span><div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(body)}</p></div><span class="inbox-count">${escapeHtml(String(count || 0))}</span></div>`; }
function phaseTitle(id) { return ({ P0_FOUNDATION: "Foundation & control", P1_CPU_BASELINE: "CPU baseline", P2_SCOPE_DEVELOPMENT: "SCOPE / AutoIndex", P3_FINAL: "Final evaluation", P4_PUBLICATION: "Publication" })[id] || id; }
function phaseDescription(id) { return ({ P0_FOUNDATION: "Schema, integrity และ projection contracts ที่ตรวจซ้ำได้", P1_CPU_BASELINE: "R0 และ R0-W บน CPU กับ protected bundle", P2_SCOPE_DEVELOPMENT: "R1 representation search ผ่าน SCOPE compiler", P3_FINAL: "เปิด final split ได้เมื่อ D2 ผ่านเท่านั้น", P4_PUBLICATION: "สร้าง manuscript และ release package เมื่อ D3 ผ่าน" })[id] || "ทำตาม execution envelope ของ phase นี้"; }
function statusTone(status) { return ["complete", "measured"].includes(status) ? "ready" : ["waiting_owner", "waiting_external_data", "locked_owner_D2", "locked_owner_D3", "blocked_until_p1"].includes(status) || String(status || "").includes("locked") ? "locked" : "next"; }
function shortStatus(status) { return status === "complete" || status === "measured" ? "done" : status === "waiting_external_data" ? "waiting" : status === "in_progress" ? "active" : status === "planned" ? "planned" : statusTone(status); }
function gateForPhase(id) { return id === "P3_FINAL" ? `<div class="owner-gate">Owner decision · D2_OPEN_FINAL</div>` : id === "P4_PUBLICATION" ? `<div class="owner-gate">Owner decision · D3_SUBMIT_RELEASE</div>` : ""; }
function gateName(task) { return task.status === "locked_owner_D2" || task.phase_id === "P3_FINAL" ? "D2_OPEN_FINAL" : task.status === "locked_owner_D3" || task.phase_id === "P4_PUBLICATION" ? "D3_SUBMIT_RELEASE" : "No owner decision required"; }
function short(value) { const text = String(value || ""); return text ? `${text.slice(0, 12)}…` : "—"; }
function escapeHtml(value) { return String(value ?? "").replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]); }
async function fetchJson(path) { const response = await fetch(path, { credentials: "same-origin" }); if (!response.ok) throw new Error(`${response.status} ${path}`); return response.json(); }
