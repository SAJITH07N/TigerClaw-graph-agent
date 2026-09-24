/**
 * Main Application Logic for TigerGraph Fraud Investigation Dashboard.
 * Includes interactive 8-step live stepper, typology filtering, batch benchmarks,
 * SAR export/copying, and real-time human-in-the-loop action controls.
 */

let allCases = [];
let activeCaseId = "CASE-BM-01";
let currentCaseData = null;
let currentStepIndex = 8;
let activeTypologyFilter = "all";
let isAnimatingStepper = false;
let currentActionTab = "after";
let matrixCases = [];
let matrixRiskFilter = "all";
let matrixSarFilter = "all";

const STEP_DEFINITIONS = [
  { step: 1, name: "Trigger", icon: "fa-bell", desc: "Ingestion & Normalization" },
  { step: 2, name: "Investigate", icon: "fa-magnifying-glass", desc: "Entity Resolution & BFS" },
  { step: 3, name: "Graph Evidence", icon: "fa-circle-nodes", desc: "GSQL & GraphRAG Evidence" },
  { step: 4, name: "Uncertainty", icon: "fa-scale-balanced", desc: "4-Pillar Completeness & Conflict" },
  { step: 5, name: "Gather More", icon: "fa-arrows-rotate", desc: "Controlled Verification Loop" },
  { step: 6, name: "NBA Decision", icon: "fa-shield-halved", desc: "Next-Best Action & Gating" },
  { step: 7, name: "Explain", icon: "fa-file-lines", desc: "Grounded Audit Explanation" },
  { step: 8, name: "Memory Update", icon: "fa-database", desc: "Graph & TigerVector Persistence" },
];

document.addEventListener("DOMContentLoaded", async () => {
  initCytoscapeGraph("cy");
  await Promise.all([
    fetchEngineHealth(),
    fetchLlmStatus(),
    loadCases(),
  ]);
  if (allCases.length > 0) {
    selectCase(allCases[0].case_id);
  }

  // Keyboard shortcut listener
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const matrixModal = document.getElementById("benchmark-matrix-modal");
      const sarModal = document.getElementById("sar-modal");
      if (matrixModal && !matrixModal.classList.contains("hidden")) {
        toggleBenchmarkMatrixModal();
      } else if (sarModal && !sarModal.classList.contains("hidden")) {
        toggleSarModal();
      }
    }
  });
});

async function fetchLlmStatus() {
  try {
    const res = await fetch("/api/llm/status");
    const data = await res.json();
    const elem = document.getElementById("llm-mode-text");
    if (elem) {
      if (data.configured) {
        elem.innerText = `Groq ${data.model || 'LLM'}`;
        elem.className = "text-bau-blue font-semibold";
      } else {
        elem.innerText = "GraphRAG grounded";
        elem.className = "text-mute";
      }
    }
  } catch (e) {
    console.warn("Could not reach LLM status endpoint:", e);
  }
}

async function fetchEngineHealth() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    document.getElementById("engine-mode-text").innerText = `${data.mode} (${data.vertex_count} Vertices, ${data.edge_count} Edges)`;
  } catch (e) {
    console.warn("Could not reach health endpoint:", e);
  }
}

async function loadCases() {
  try {
    const res = await fetch("/api/cases");
    allCases = await res.json();
    renderCaseList(getFilteredCases());
  } catch (e) {
    console.error("Failed to load cases:", e);
  }
}

function getFilteredCases() {
  const query = (document.getElementById("case-search-input")?.value || "").toLowerCase();
  return allCases.filter(c => {
    const matchesQuery = !query ||
      c.case_id.toLowerCase().includes(query) ||
      c.case_title.toLowerCase().includes(query) ||
      (c.typology && c.typology.toLowerCase().includes(query));

    if (!matchesQuery) return false;

    if (activeTypologyFilter === "all") return true;
    if (activeTypologyFilter === "ATO") return (c.typology || "").includes("ATO") || c.case_title.includes("Takeover");
    if (activeTypologyFilter === "Mule") return (c.typology || "").includes("Mule") || c.case_title.includes("Mule");
    if (activeTypologyFilter === "Card") return (c.typology || "").includes("Card") || c.case_title.includes("Card");
    if (activeTypologyFilter === "Synthetic") return (c.typology || "").includes("Synthetic") || c.case_title.includes("Synthetic");
    if (activeTypologyFilter === "Vacation") return (c.typology || "").includes("Vacation") || c.case_title.includes("Vacation");
    return true;
  });
}

function setTypologyFilter(filter) {
  activeTypologyFilter = filter;
  document.querySelectorAll(".typology-filter-btn").forEach(btn => {
    const isActive = btn.getAttribute("data-filter") === filter;
    btn.className = isActive ? "typology-filter-btn pill pill-active" : "typology-filter-btn pill";
  });
  renderCaseList(getFilteredCases());
}

function filterCases() {
  renderCaseList(getFilteredCases());
}

function renderCaseList(cases) {
  const container = document.getElementById("case-list");
  container.innerHTML = "";

  if (cases.length === 0) {
    container.innerHTML = `<div class="text-xs text-mute p-6 text-center">No cases match your search. Try a different term or clear the filter.</div>`;
    return;
  }

  cases.forEach(c => {
    const isSelected = c.case_id === activeCaseId;

    const div = document.createElement("div");
    div.className = `case-row flex items-center justify-between ${isSelected ? 'case-row-active' : ''}`;
    div.onclick = () => selectCase(c.case_id);

    div.innerHTML = `
      <div class="space-y-1 min-w-0 pr-2">
        <div class="flex items-center gap-2">
          <span class="font-mono text-[10px] text-mute font-bold">${c.case_id}</span>
          <span class="risk-chip ${getRiskChipClass(c.risk_level)}">${c.risk_level}</span>
          ${c.has_sar ? '<i class="fa-solid fa-file-shield text-[10px] text-bau-yellow" title="FinCEN SAR"></i>' : ''}
        </div>
        <div class="text-xs font-semibold text-chalk truncate">${c.case_title}</div>
        <div class="text-[11px] text-mute">${c.typology || 'Investigating'}</div>
      </div>
      <div class="text-right flex-shrink-0">
        <div class="text-xs font-mono font-bold text-chalk">$${parseFloat(c.amount || 0).toLocaleString()}</div>
        <div class="text-[10px] font-mono text-mute">${c.action_count} actions</div>
      </div>
    `;
    container.appendChild(div);
  });

  document.getElementById("case-count-badge").innerText = `${cases.length} Total`;
}

async function selectCase(caseId) {
  activeCaseId = caseId;
  renderCaseList(getFilteredCases());

  try {
    const [caseRes, graphRes] = await Promise.all([
      fetch(`/api/cases/${caseId}`),
      fetch(`/api/cases/${caseId}/subgraph`)
    ]);

    currentCaseData = await caseRes.json();
    const graphData = await graphRes.json();

    currentStepIndex = 8;
    updateCaseView(currentCaseData);
    if (graphData && graphData.elements) {
      renderSubgraphData(graphData.elements);
    }
  } catch (e) {
    console.error("Error loading case detail:", e);
    showToast("Error", `Failed to load case ${caseId}`, "error");
  }
}

function updateCaseView(data) {
  const results = data.investigation_results || {};
  const trigger = data.trigger || {};
  const tData = trigger.data || {};

  // Header Elements
  document.getElementById("case-id-badge").innerText = data.case_id;
  document.getElementById("case-title-text").innerText = data.case_title || "Investigation Case";
  document.getElementById("case-typology-text").innerHTML = `Classified Typology: <strong class="text-chalk font-semibold">${results.top_typology_match?.name || 'Unknown'}</strong> (${results.top_typology_match?.typology_id || 'N/A'})`;
  document.getElementById("case-amount-text").innerText = `$${parseFloat(tData.amount || 0).toLocaleString(undefined, {minimumFractionDigits: 2})}`;
  document.getElementById("case-confidence-text").innerText = `${(parseFloat(results.composite_confidence || 0.8) * 100).toFixed(1)}%`;

  // Risk Badge
  const riskBadge = document.getElementById("case-risk-badge");
  const risk = (results.risk_level || "medium").toLowerCase();
  riskBadge.className = `risk-chip ${getRiskChipClass(risk)}`;
  riskBadge.innerText = risk;

  // SAR Badge & Button
  const sarBadge = document.getElementById("case-sar-badge");
  const sarBtn = document.getElementById("view-sar-btn");
  if (data.sar_filing) {
    sarBadge.classList.remove("hidden");
    sarBtn.classList.remove("hidden");
  } else {
    sarBadge.classList.add("hidden");
    sarBtn.classList.add("hidden");
  }

  // Stepper
  renderStepper(currentStepIndex);

  // 4-Pillar Completeness
  const pillars = results.evidence_pillars || { p_txn: 0.8, p_dev: 0.8, p_behav: 0.7, p_prior: 0.8 };
  document.getElementById("completeness-score-text").innerText = `${(parseFloat(results.data_completeness || 0.85) * 100).toFixed(0)}%`;
  updatePillarBar("pillar-txn", pillars.p_txn);
  updatePillarBar("pillar-dev", pillars.p_dev);
  updatePillarBar("pillar-behav", pillars.p_behav);
  updatePillarBar("pillar-prior", pillars.p_prior);

  document.getElementById("conflict-score-text").innerText = parseFloat(results.signal_conflict || 0.1).toFixed(2);
  document.getElementById("composite-confidence-metric").innerText = `${(parseFloat(results.composite_confidence || 0.85) * 100).toFixed(1)}%`;

  // Trajectory Delta
  document.getElementById("trajectory-delta-text").innerText = data.evidence_trajectory?.what_changed || "Baseline evidence assessed.";

  // Next Best Actions
  switchActionTab(currentActionTab || 'after');

  // Grounded Explanation
  document.getElementById("grounded-explanation-text").innerText = data.grounded_explanation || "No explanation synthesized.";
}

function updatePillarBar(prefix, val) {
  const v = parseFloat(val || 0);
  const valElem = document.getElementById(`${prefix}-val`);
  const barElem = document.getElementById(`${prefix}-bar`);
  if (valElem) valElem.innerText = v.toFixed(2);
  if (barElem) barElem.style.width = `${Math.min(v * 100, 100)}%`;
}

function renderStepper(visibleStepCount = 8) {
  const container = document.getElementById("stepper-container");
  container.innerHTML = "";

  STEP_DEFINITIONS.forEach(def => {
    const isDone = def.step <= visibleStepCount;
    const isCurrent = def.step === visibleStepCount;

    const div = document.createElement("div");
    div.className = `step-cell ${isCurrent ? 'step-current' : isDone ? 'step-done' : 'step-idle'}`;
    div.onclick = () => setStep(def.step);
    div.title = def.desc;
    div.innerHTML = `
      <div class="step-num">${String(def.step).padStart(2, "0")}</div>
      <div class="step-name">${def.name}</div>
    `;
    container.appendChild(div);
  });

  const indicator = document.getElementById("active-step-indicator");
  if (indicator) {
    if (visibleStepCount >= 8) {
      indicator.innerText = "All 8 steps completed";
      indicator.className = "text-[10px] font-mono font-bold text-bau-green px-2 py-0.5 border border-line rounded-sm";
    } else {
      const activeDef = STEP_DEFINITIONS[visibleStepCount - 1] || STEP_DEFINITIONS[0];
      indicator.innerText = `${String(visibleStepCount).padStart(2, "0")} · ${activeDef.desc}`;
      indicator.className = "text-[10px] font-mono font-bold text-bau-blue px-2 py-0.5 border border-line rounded-sm";
    }
  }
}

function setStep(stepNum) {
  currentStepIndex = Math.max(1, Math.min(8, stepNum));
  renderStepper(currentStepIndex);
}

function stepForward() {
  if (currentStepIndex < 8) {
    setStep(currentStepIndex + 1);
  } else {
    showToast("Stepper", "Already at the final step (Step 8)", "info");
  }
}

function stepBackward() {
  if (currentStepIndex > 1) {
    setStep(currentStepIndex - 1);
  }
}

async function playStepperAnimation() {
  if (isAnimatingStepper) return;
  isAnimatingStepper = true;
  for (let i = 1; i <= 8; i++) {
    setStep(i);
    await new Promise(r => setTimeout(r, 450));
  }
  isAnimatingStepper = false;
  showToast("Investigation Complete", `Executed full 8-step workflow for ${activeCaseId}`, "success");
}

function switchActionTab(tab) {
  currentActionTab = tab;
  const tabAfter = document.getElementById("nba-tab-after");
  const tabBefore = document.getElementById("nba-tab-before");

  if (tab === 'after') {
    if (tabAfter) tabAfter.className = "px-2.5 py-1 bg-line-strong text-chalk font-semibold transition-colors";
    if (tabBefore) tabBefore.className = "px-2.5 py-1 text-mute hover:text-chalk transition-colors";
    const actions = currentCaseData?.next_best_actions_after_evidence || currentCaseData?.next_best_actions || [];
    renderActionQueue(actions, 'after');
  } else {
    if (tabBefore) tabBefore.className = "px-2.5 py-1 bg-line-strong text-chalk font-semibold transition-colors";
    if (tabAfter) tabAfter.className = "px-2.5 py-1 text-mute hover:text-chalk transition-colors";
    const actions = currentCaseData?.next_best_actions_before_evidence || [];
    renderActionQueue(actions, 'before');
  }
}

function renderActionQueue(actions, mode = 'after') {
  const container = document.getElementById("action-queue");
  if (!container) return;
  container.innerHTML = "";

  if (!actions || actions.length === 0) {
    const emptyMsg = mode === 'before'
      ? 'No immediate actions proposed prior to evidence collection.'
      : 'No actions recommended for this case.';
    container.innerHTML = `<div class="text-xs text-mute p-6 text-center bau-inset">${emptyMsg}</div>`;
    return;
  }

  actions.forEach(act => {
    const isExecuted = act.status === "executed";
    const isPending = act.status === "pending_approval";
    const isHeld = act.status === "held" || (mode === 'before' && isPending);

    const div = document.createElement("div");
    div.className = `bau-inset p-3.5 flex items-start justify-between gap-3 ${isExecuted ? 'edge-green' : isPending ? 'edge-yellow' : 'edge-blue'}`;
    div.innerHTML = `
      <div class="space-y-1.5 flex-1 min-w-0">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="font-mono text-xs font-bold text-chalk">${act.action_type}</span>
          <span class="text-[10px] px-2 py-0.5 rounded-sm font-mono font-semibold ${
            isExecuted ? 'text-bau-green border border-line' : isPending ? 'text-bau-yellow border border-line' : 'text-bau-blue border border-line'
          }">${mode === 'before' ? (isExecuted ? 'PROPOSED' : 'PENDING EVAL') : act.status.toUpperCase()}</span>
          <span class="text-[10px] text-mute font-mono">→ ${act.target_entity}</span>
        </div>
        <p class="text-xs text-mute leading-relaxed">${act.rationale}</p>
        <div class="text-[10px] text-mute font-mono">
          <strong class="text-chalk">${act.permission_level}</strong> · ${act.policy_citation}
        </div>
      </div>
      <div class="flex items-center gap-1.5 flex-shrink-0">
        ${
          mode === 'after' && isPending
            ? `<button onclick="approveAction('${act.action_id}', 'approve')" class="bau-btn bau-btn-approve px-3 py-1.5">Approve</button>
               <button onclick="approveAction('${act.action_id}', 'reject')" class="bau-btn px-3 py-1.5">Reject</button>`
            : mode === 'after' && isExecuted
            ? `<span class="text-bau-green text-xs font-mono font-bold"><i class="fa-solid fa-check mr-1"></i>Active</span>`
            : `<span class="text-mute text-xs font-mono font-medium"><i class="fa-solid fa-clock-rotate-left mr-1"></i>Pre-Evidence</span>`
        }
      </div>
    `;
    container.appendChild(div);
  });
}

async function approveAction(actionId, decision) {
  try {
    const res = await fetch(`/api/actions/${actionId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action_id: actionId, decision: decision })
    });
    const data = await res.json();
    showToast("Action Updated", data.message, "success");
    if (activeCaseId) selectCase(activeCaseId);
  } catch (e) {
    console.error("Approval failed:", e);
    showToast("Error", "Action update failed", "error");
  }
}

async function reinvestigateCurrentCase() {
  if (!activeCaseId) return;
  try {
    const res = await fetch(`/api/cases/${activeCaseId}/investigate`, { method: "POST" });
    const data = await res.json();
    showToast("Re-Investigation", `Re-investigation for ${activeCaseId} complete.`, "success");
    await playStepperAnimation();
    selectCase(activeCaseId);
  } catch (e) {
    console.error("Reinvestigate failed:", e);
    showToast("Error", "Reinvestigation failed", "error");
  }
}

async function runBatchBenchmarks() {
  const btn = document.getElementById("batch-run-btn");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-bau-yellow"></i> <span>Running…</span>`;
  }
  try {
    const res = await fetch("/api/benchmark/run_all", { method: "POST" });
    const data = await res.json();
    showToast("Benchmark Suite", `Successfully evaluated all ${data.total_cases || 20} benchmark scenarios!`, "success");
    await loadCases();
    if (activeCaseId) selectCase(activeCaseId);
  } catch (e) {
    console.error("Batch benchmark run failed:", e);
    showToast("Error", "Batch benchmark execution failed", "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-list-check text-bau-green"></i> <span>Run All 20</span>`;
    }
  }
}

function toggleSarModal() {
  const modal = document.getElementById("sar-modal");
  const isHidden = modal.classList.contains("hidden");
  if (isHidden && currentCaseData && currentCaseData.sar_filing) {
    document.getElementById("sar-modal-body").innerHTML = `<pre class="whitespace-pre-wrap">${currentCaseData.sar_filing.full_narrative_text}</pre>`;
    modal.classList.remove("hidden");
  } else {
    modal.classList.add("hidden");
  }
}

function copySarNarrative() {
  if (currentCaseData && currentCaseData.sar_filing) {
    navigator.clipboard.writeText(currentCaseData.sar_filing.full_narrative_text);
    showToast("SAR Copied", "FinCEN Form 111 text copied to clipboard", "success");
  }
}

function downloadSarDocument() {
  if (!currentCaseData || !currentCaseData.sar_filing) return;
  const element = document.createElement("a");
  const file = new Blob([currentCaseData.sar_filing.full_narrative_text], { type: 'text/plain' });
  element.href = URL.createObjectURL(file);
  element.download = `FinCEN_SAR_${activeCaseId}.txt`;
  document.body.appendChild(element);
  element.click();
  document.body.removeChild(element);
  showToast("SAR Downloaded", `FinCEN_SAR_${activeCaseId}.txt saved.`, "info");
}

function showToast(title, message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) return;

  const edge = { success: "edge-green", error: "edge-red", info: "edge-blue" }[type] || "edge-blue";

  const toast = document.createElement("div");
  toast.className = `bau-toast ${edge} p-3.5 pl-4 text-xs pointer-events-auto transition-all transform translate-y-2 opacity-0 duration-200 min-w-[240px]`;
  toast.innerHTML = `
    <div class="space-y-0.5">
      <div class="font-bold text-chalk">${title}</div>
      <div class="text-[11px] text-mute">${message}</div>
    </div>
  `;

  container.appendChild(toast);
  requestAnimationFrame(() => {
    toast.classList.remove("translate-y-2", "opacity-0");
  });

  setTimeout(() => {
    toast.classList.add("opacity-0", "translate-y-2");
    setTimeout(() => toast.remove(), 250);
  }, 3000);
}

function getRiskChipClass(risk) {
  switch ((risk || "").toLowerCase()) {
    case "critical": return "risk-critical";
    case "high": return "risk-high";
    case "medium": return "risk-medium";
    case "low": return "risk-low";
    default: return "risk-unknown";
  }
}

/* ==============================================================================
 * BENCHMARK MATRIX MODAL LOGIC & COMPARISON TABLE
 * ============================================================================== */

async function toggleBenchmarkMatrixModal() {
  const modal = document.getElementById("benchmark-matrix-modal");
  if (!modal) return;
  const isHidden = modal.classList.contains("hidden");
  if (isHidden) {
    modal.classList.remove("hidden");
    await loadBenchmarkMatrix();
  } else {
    modal.classList.add("hidden");
  }
}

async function loadBenchmarkMatrix() {
  try {
    const res = await fetch("/api/benchmark/matrix");
    const data = await res.json();
    matrixCases = data.cases || [];
    renderMatrixSummaryKPIs(data.summary || {});
    renderBenchmarkMatrixTable(getFilteredMatrixCases());
  } catch (e) {
    console.error("Failed to load benchmark matrix:", e);
    showToast("Matrix Error", "Failed to fetch benchmark comparison data", "error");
  }
}

function renderMatrixSummaryKPIs(summary) {
  const container = document.getElementById("matrix-kpi-summary");
  if (!container) return;

  container.innerHTML = `
    <div class="kpi-chip">
      <span class="text-mute">Cases</span>
      <strong class="text-chalk">${summary.total_cases || 20}</strong>
    </div>
    <div class="kpi-chip edge-red">
      <span class="text-mute">Critical / High</span>
      <strong class="text-chalk">${(summary.critical_count || 0) + (summary.high_count || 0)}</strong>
    </div>
    <div class="kpi-chip edge-green">
      <span class="text-mute">Cleared</span>
      <strong class="text-chalk">${summary.low_count || 0}</strong>
    </div>
    <div class="kpi-chip edge-yellow">
      <span class="text-mute">SARs required</span>
      <strong class="text-chalk">${summary.sar_filings_required || 0}</strong>
    </div>
    <div class="kpi-chip edge-blue">
      <span class="text-mute">Avg confidence</span>
      <strong class="text-chalk">${((summary.avg_confidence || 0.85) * 100).toFixed(1)}%</strong>
    </div>
  `;
}

function getFilteredMatrixCases() {
  const query = (document.getElementById("matrix-search-input")?.value || "").toLowerCase();
  return matrixCases.filter(c => {
    // Search query match
    const matchesQuery = !query ||
      c.case_id.toLowerCase().includes(query) ||
      c.case_title.toLowerCase().includes(query) ||
      (c.typology && c.typology.toLowerCase().includes(query)) ||
      (c.trigger_type && c.trigger_type.toLowerCase().includes(query));

    if (!matchesQuery) return false;

    // Risk Level Filter
    if (matrixRiskFilter !== "all") {
      if ((c.risk_level || "").toLowerCase() !== matrixRiskFilter) return false;
    }

    // SAR Filter
    if (matrixSarFilter === "sar_only" && !c.has_sar) return false;
    if (matrixSarFilter === "no_sar" && c.has_sar) return false;

    return true;
  });
}

function renderBenchmarkMatrixTable(cases) {
  const tbody = document.getElementById("benchmark-matrix-tbody");
  const countElem = document.getElementById("matrix-filtered-count");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (countElem) {
    countElem.innerText = `Showing ${cases.length} of ${matrixCases.length} cases`;
  }

  if (cases.length === 0) {
    tbody.innerHTML = `<tr><td colspan="12" class="text-center p-10 text-mute">No scenarios match these filters. Clear a filter to see more.</td></tr>`;
    return;
  }

  cases.forEach(c => {
    const completeness = (parseFloat(c.data_completeness || 0.85) * 100).toFixed(0);
    const conflict = parseFloat(c.signal_conflict || 0.10).toFixed(2);
    const confidence = (parseFloat(c.confidence || 0.85) * 100).toFixed(1);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="font-mono font-bold text-chalk whitespace-nowrap">
        <div>${c.case_id}</div>
        <span class="text-[10px] text-mute">#${c.benchmark_index || '01'}</span>
      </td>
      <td class="text-chalk font-semibold max-w-[220px]">
        <div class="truncate" title="${c.case_title}">${c.case_title}</div>
      </td>
      <td class="whitespace-nowrap">
        <span class="text-[10px] px-2 py-0.5 rounded-sm font-mono text-mute border border-line">${c.trigger_type || 'ALERT'}</span>
      </td>
      <td class="text-right font-mono font-bold text-chalk whitespace-nowrap">
        $${parseFloat(c.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
      </td>
      <td class="text-mute whitespace-nowrap">
        <div class="font-medium text-chalk">${c.typology || 'Typology'}</div>
        <span class="text-[10px] font-mono">${c.typology_id || 'TYP-01'}</span>
      </td>
      <td class="text-center whitespace-nowrap">
        <span class="risk-chip ${getRiskChipClass(c.risk_level)}">${c.risk_level}</span>
      </td>
      <td class="text-center whitespace-nowrap">
        <div class="font-mono font-bold text-chalk">${completeness}%</div>
        <div class="pillar-track w-16 mx-auto mt-1" style="height:5px">
          <div class="pillar-fill" style="width:${completeness}%;background:var(--bau-blue)"></div>
        </div>
      </td>
      <td class="text-center font-mono text-mute whitespace-nowrap">${conflict}</td>
      <td class="text-center whitespace-nowrap">
        <span class="font-mono font-bold text-bau-green">${confidence}%</span>
      </td>
      <td class="max-w-[200px]">
        <div class="flex items-center gap-1 flex-wrap">
          <span class="text-[10px] font-mono text-chalk px-1.5 py-0.5 rounded-sm border border-line">${c.action_count}</span>
          ${(c.actions || []).slice(0, 2).map(a => `<span class="text-[9px] text-mute px-1 py-0.5 rounded-sm border border-line truncate max-w-[90px]">${a.action_type || ''}</span>`).join('')}
        </div>
      </td>
      <td class="text-center whitespace-nowrap">
        ${
          c.has_sar
            ? `<span class="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-sm border" style="color:var(--bau-yellow);border-color:var(--bau-yellow)">31 CFR §1020</span>`
            : `<span class="text-[10px] text-mute font-mono">Sub-threshold</span>`
        }
      </td>
      <td class="text-center whitespace-nowrap">
        <button onclick="inspectMatrixCase('${c.case_id}')" class="bau-btn bau-btn-primary px-2.5 py-1 mx-auto">
          <span>Open</span>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterMatrixCases() {
  renderBenchmarkMatrixTable(getFilteredMatrixCases());
}

function setMatrixRiskFilter(risk) {
  matrixRiskFilter = risk;
  document.querySelectorAll(".matrix-risk-btn").forEach(btn => {
    const isActive = btn.getAttribute("data-risk") === risk;
    btn.className = isActive ? "matrix-risk-btn pill pill-active" : "matrix-risk-btn pill";
  });
  filterMatrixCases();
}

function setMatrixSarFilter(sar) {
  matrixSarFilter = sar;
  document.querySelectorAll(".matrix-sar-btn").forEach(btn => {
    const isActive = btn.getAttribute("data-sar") === sar;
    btn.className = isActive ? "matrix-sar-btn pill pill-active" : "matrix-sar-btn pill";
  });
  filterMatrixCases();
}

function inspectMatrixCase(caseId) {
  toggleBenchmarkMatrixModal();
  selectCase(caseId);
}

function exportBenchmarkMatrixCSV() {
  if (!matrixCases || matrixCases.length === 0) {
    showToast("Export", "No matrix data available to export", "info");
    return;
  }

  const headers = [
    "Benchmark Index",
    "Case ID",
    "Scenario Title",
    "Trigger Type",
    "Amount ($)",
    "Typology",
    "Typology ID",
    "Risk Level",
    "Data Completeness (C_data)",
    "Signal Conflict (S_conf)",
    "Composite Confidence",
    "Action Count",
    "FinCEN SAR Required",
    "Suspicious SAR Volume ($)"
  ];

  const rows = matrixCases.map(c => [
    c.benchmark_index || "",
    `"${c.case_id}"`,
    `"${(c.case_title || '').replace(/"/g, '""')}"`,
    `"${c.trigger_type || ''}"`,
    parseFloat(c.amount || 0).toFixed(2),
    `"${(c.typology || '').replace(/"/g, '""')}"`,
    `"${c.typology_id || ''}"`,
    `"${c.risk_level || ''}"`,
    parseFloat(c.data_completeness || 0.85).toFixed(4),
    parseFloat(c.signal_conflict || 0.10).toFixed(4),
    parseFloat(c.confidence || 0.85).toFixed(4),
    c.action_count || 0,
    c.has_sar ? "YES (31 CFR § 1020.320)" : "NO",
    parseFloat(c.sar_amount || 0).toFixed(2)
  ]);

  const csvContent = [headers.join(","), ...rows.map(r => r.join(","))].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "TigerGraph_Fraud_Benchmark_Matrix.csv";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  showToast("CSV Exported", "TigerGraph_Fraud_Benchmark_Matrix.csv downloaded successfully.", "success");
}

