const state = { tab: "overview", model: null, dashboard: null, presentation: null, csrf: "", presenting: false };
const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", async () => {
  document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => selectTab(button.dataset.tab)));
  $("refresh").addEventListener("click", refresh);
  $("present-toggle").addEventListener("click", () => {
    state.presenting = !state.presenting;
    document.body.classList.toggle("presentation-mode", state.presenting);
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
      fetchJson("/api/v1/read-model"),
      fetchJson("/api/v1/dashboard"),
      fetchJson("/api/v1/presentation"),
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
  const readiness = model.publication_readiness || {};
  const cost = model.cost || {};
  const dashboard = state.dashboard || {};
  $("campaign-title").textContent = campaign.title || "SCOPE / AutoIndex";
  $("campaign-status").textContent = `สถานะ: ${campaign.status || "preparation"} | metric หลัก: ${campaign.primary_metric || "recall_at_100/out"}`;
  $("revision").textContent = `read-model ${short(model.projection_revision)}`;
  $("status-cards").innerHTML = [
    card("Current phase", dashboard.current_phase || "P0_FOUNDATION", "จาก phase/task ที่เป็น canonical"),
    card("Runs", String(model.runs?.length || 0), "จาก manifest ที่ validate แล้ว"),
    card("Cost", cost.actual == null ? "ยังไม่วัด" : `${cost.actual} ${cost.currency || "USD"}`, `budget ${cost.budget || 100} USD`),
    card("Publication", readiness.status || "blocked", "ยังไม่ใช่ release approval"),
  ].join("");
  renderInbox();
  renderFlow();
  renderEvidence();
  renderPresentation();
}

function renderInbox() {
  const dashboard = state.dashboard || {};
  const done = dashboard.done || [];
  const next = dashboard.next || [];
  const owner = dashboard.waiting_owner || ["D2_OPEN_FINAL", "D3_SUBMIT_RELEASE"];
  const command = dashboard.waiting_command || [];
  $("owner-inbox").innerHTML = [
    inboxRow("ready", "ทำแล้ว", done.length ? done.join("; ") : "ยังไม่มีงานที่ปิดด้วย evidence"),
    inboxRow("next", "ทำต่อได้ทันที", next.length ? next.join("; ") : "รอข้อมูลจากขั้นก่อนหน้า"),
    inboxRow("owner", "รอ Owner ตัดสินใจ", owner.join("; ")),
    inboxRow("owner", "รอ Owner ออกคำสั่ง", command.length ? command.join("; ") : "ไม่มีคำสั่งค้าง")
  ].join("");
}

function inboxRow(kind, title, body) {
  return `<div class="inbox-row"><span class="state-dot state-${kind}"></span><div><strong>${escapeHtml(title)}</strong><p>${escapeHtml(body)}</p></div></div>`;
}

function renderFlow() {
  const phases = state.model?.phases || [];
  $("phase-flow").innerHTML = phases.map((phase) => `<article class="phase-card"><div class="phase-head"><span class="phase-id">${escapeHtml(phase.phase_id)}</span><span class="phase-status ${statusClass(phase.status)}">${escapeHtml(phase.status)}</span></div><h3>${escapeHtml(phaseTitle(phase.phase_id))}</h3><p>${escapeHtml(phaseDescription(phase.phase_id))}</p><div class="task-line">${(phase.tasks || []).map((task) => `<span title="${escapeHtml(task.task_id)}">${escapeHtml(task.task_id)} ${escapeHtml(task.status)}</span>`).join("") || "เตรียมตาม contract"}</div>${phase.phase_id === "P3_FINAL" ? `<div class="owner-gate">Owner: D2_OPEN_FINAL</div>` : ""}${phase.phase_id === "P4_PUBLICATION" ? `<div class="owner-gate">Owner: D3_SUBMIT_RELEASE</div>` : ""}</article>`).join("");
}

function renderEvidence() {
  const rows = state.model?.runs || [];
  const metrics = state.model?.metrics || [];
  $("evidence-table").innerHTML = `<table><thead><tr><th>Run / Experiment</th><th>Stage</th><th>Arm</th><th>Metrics</th><th>Receipt</th></tr></thead><tbody>${rows.map((run) => `<tr><td>${escapeHtml(run.run_id)}<small>${escapeHtml(run.experiment_id || "-")}</small></td><td>${escapeHtml(run.stage || "-")}</td><td>${escapeHtml(run.arm || "-")}</td><td>${metrics.filter((metric) => metric.run_id === run.run_id).map((metric) => `${escapeHtml(metric.name || "metric")}: ${escapeHtml(String(metric.value ?? "-"))}`).join("<br>") || "pending"}</td><td>${run.owner_local_receipt_sha256 ? short(run.owner_local_receipt_sha256) : "blocked / fixture"}</td></tr>`).join("") || `<tr><td colspan="5" class="empty">ยังไม่มี measured run ระบบไม่สร้างตัวเลขแทนหลักฐาน</td></tr>`}</tbody></table>`;
}

function renderPresentation() {
  const sections = state.presentation?.sections || [];
  $("presentation-content").innerHTML = sections.map((section) => `<article class="slide"><p class="eyebrow">${escapeHtml(section.title_en)}</p><h3>${escapeHtml(section.title_th)}</h3><p>${typeof section.body === "string" ? escapeHtml(section.body) : `<strong>Phase:</strong> ${escapeHtml(section.body?.phase || "-")}<br><strong>Runs:</strong> ${escapeHtml(String(section.body?.runs || 0))}<br><strong>Readiness:</strong> ${escapeHtml(section.body?.readiness || "blocked")}`}</p></article>`).join("");
}

function card(label, value, detail) { return `<article class="metric-card"><p class="eyebrow">${escapeHtml(label)}</p><strong>${escapeHtml(value)}</strong><span>${escapeHtml(detail)}</span></article>`; }
function phaseTitle(id) { return ({ P0_FOUNDATION: "Foundation & control", P1_CPU_BASELINE: "CPU baseline", P2_SCOPE_DEVELOPMENT: "SCOPE / AutoIndex", P3_FINAL: "Final evaluation", P4_PUBLICATION: "Publication" })[id] || id; }
function phaseDescription(id) { return ({ P0_FOUNDATION: "สคีมาและกติกากลางพร้อมตรวจซ้ำได้", P1_CPU_BASELINE: "R0 และ R0-W บน CPU กับ protected bundle", P2_SCOPE_DEVELOPMENT: "R1 representation search ผ่าน compiler", P3_FINAL: "เปิด final split ได้เมื่อ D2 ผ่าน", P4_PUBLICATION: "สร้าง package และ release เมื่อ D3 ผ่าน" })[id] || ""; }
function statusClass(status) { return status?.includes("locked") || status?.includes("waiting") ? "locked" : status === "complete" || status === "measured" ? "ready" : "next"; }
function short(value) { return value ? `${value.slice(0, 10)}...` : "-"; }
function escapeHtml(value) { return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]); }
async function fetchJson(path) { const response = await fetch(path, { credentials: "same-origin" }); if (!response.ok) throw new Error(`${response.status} ${path}`); return response.json(); }
