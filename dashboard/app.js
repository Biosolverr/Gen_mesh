// GenMesh Core — Execution Trace Dashboard
// Simulated mode plays back a scripted run matching the actual contracts
// from Registry/Coordinator/Agents/Aggregator. Live mode reads real
// deployed contract state via genlayer-js (view calls only, no keys).

const REGISTRY_ADDR = "0x9F1c2A4e5B7d8C3f0A1b2C3d4E5f6A7b8C9d0E1f";
const COORDINATOR_ADDR = "0x2B4d6F8a0C1e3D5f7A9b1C3d5E7f9A1b3C5d7E9f";
const AGGREGATOR_ADDR = "0x7C1e3A5b7D9f1A3c5E7d9F1a3C5e7D9f1A3c5E7d";
const SECURITY_ADDR = "0xA1b2C3d4E5f6A7b8C9d0E1f2A3b4C5d6E7f8A9b0";
const RESEARCH_ADDR = "0xB2c3D4e5F6a7B8c9D0e1F2a3B4c5D6e7F8a9B0c1";
const FINANCE_ADDR  = "0xC3d4E5f6A7b8C9d0E1f2A3b4C5d6E7f8A9b0C1d2";

function short(addr){ return addr.slice(0,6) + "…" + addr.slice(-4); }

const REGISTRY_AGENTS = [
  { name: "SecurityAgent", address: SECURITY_ADDR, capability: "security-audit", version: "1.0.0", active: true },
  { name: "ResearchAgent", address: RESEARCH_ADDR, capability: "research", version: "1.0.0", active: true },
  { name: "FinanceAgent",  address: FINANCE_ADDR,  capability: "market-analysis", version: "1.0.0", active: true },
];

const AGENT_RESULTS = [
  {
    agent: "SecurityAgent", address: SECURITY_ADDR, capability: "security-audit",
    verdict: "high",
    summary: "No timelock on admin functions combined with high leverage creates significant rug-pull and liquidation cascade risk."
  },
  {
    agent: "FinanceAgent", address: FINANCE_ADDR, capability: "market-analysis",
    verdict: "neutral",
    summary: "TVL growth is healthy but insufficient on its own to offset structural risk; broader market conditions are stable but not clearly favorable."
  },
];

function stageHTML(index, title, tag){
  return `
    <div class="stage" data-stage="${index}">
      <div class="stage-dot"></div>
      <div class="stage-header">
        <span class="stage-index">${String(index).padStart(2,"0")}</span>
        <span class="stage-title">${title}</span>
        <span class="stage-tag">${tag}</span>
      </div>
      <div class="stage-body" id="stage-body-${index}"></div>
    </div>
  `;
}

const STAGES = [
  { title: "User Request", tag: "off-chain → tx" },
  { title: "Coordinator", tag: "Coordinator.submit_task()" },
  { title: "Registry Lookup", tag: "Registry.view().getAgents()" },
  { title: "Execution Plan", tag: "capability → agent binding" },
  { title: "Agent Calls", tag: "emit() fan-out" },
  { title: "Agent Responses", tag: "Agent.execute() → Aggregator" },
  { title: "Aggregation", tag: "Aggregator.submit_result()" },
  { title: "Optimistic Democracy", tag: "per-tx validation" },
  { title: "Final Result", tag: "Aggregator.get_result()" },
];

function renderSkeleton(container){
  container.innerHTML = STAGES.map((s,i)=>stageHTML(i+1, s.title, s.tag)).join("");
}

function bodyFor(i){ return document.getElementById("stage-body-"+i); }

function bodies(){
  const task = document.getElementById("task-input").value.trim();

  return {
    1: () => `
      <div class="data-block">
        <div class="data-row"><span class="k">caller</span><span class="v addr">0xUser…demo</span></div>
        <div class="data-row"><span class="k">tx</span><span class="v">Coordinator.submit_task(task_description)</span></div>
        <div class="data-row"><span class="k">task_description</span><span class="v">"${task}"</span></div>
      </div>`,
    2: () => `
      <div class="data-block">
        <div class="data-row"><span class="k">contract</span><span class="v">Coordinator <span class="addr">(${short(COORDINATOR_ADDR)})</span></span></div>
        <div class="data-row"><span class="k">op type</span><span class="v"><span class="pill nondet">non-deterministic</span> run_nondet_unsafe(leader_fn, validator_fn)</span></div>
        <div class="data-row"><span class="k">purpose</span><span class="v">capability matching — grounded against Registry's currently active capability set</span></div>
      </div>`,
    3: () => `
      <div class="data-block">
        <div class="data-row"><span class="k">contract</span><span class="v">AgentRegistry <span class="addr">(${short(REGISTRY_ADDR)})</span></span></div>
        <div class="data-row"><span class="k">call</span><span class="v"><span class="pill det">deterministic</span> view().getAgents()</span></div>
      </div>
      <table>
        <thead><tr><th>Agent</th><th>Address</th><th>Capability</th><th>Active</th></tr></thead>
        <tbody>
          ${REGISTRY_AGENTS.map(a=>`<tr>
            <td>${a.name}</td><td class="addr">${short(a.address)}</td>
            <td>${a.capability}</td><td>${a.active ? "true" : "false"}</td>
          </tr>`).join("")}
        </tbody>
      </table>`,
    4: () => `
      <div class="data-block">
        <div class="data-row"><span class="k">required_capabilities</span><span class="v">["security-audit", "market-analysis"]</span></div>
        <div class="data-row"><span class="k">skipped</span><span class="v">"research" — not relevant to this task, ResearchAgent not called</span></div>
      </div>
      <table>
        <thead><tr><th>Capability</th><th>Assigned Agent</th><th>Task ID</th></tr></thead>
        <tbody>
          <tr><td>security-audit</td><td class="addr">${short(SECURITY_ADDR)}</td><td>task_id = 0</td></tr>
          <tr><td>market-analysis</td><td class="addr">${short(FINANCE_ADDR)}</td><td>task_id = 0</td></tr>
        </tbody>
      </table>`,
    5: () => `
      <div class="data-block">
        <div class="data-row"><span class="k">emit 1</span><span class="v">SecurityAgent.execute(0, task_description, "security-audit", aggregator_address)</span></div>
        <div class="data-row"><span class="k">emit 2</span><span class="v">FinanceAgent.execute(0, task_description, "market-analysis", aggregator_address)</span></div>
        <div class="data-row"><span class="k">emit 3</span><span class="v">Aggregator.register_task(0, [SecurityAgent, FinanceAgent])</span></div>
        <div class="data-row"><span class="k">on</span><span class="v">"finalized" — dispatched once, no retry/monitoring afterward</span></div>
      </div>`,
    6: () => `
      ${AGENT_RESULTS.map(r=>`
      <div class="data-block">
        <div class="data-row"><span class="k">agent</span><span class="v">${r.agent} <span class="addr">(${short(r.address)})</span></span></div>
        <div class="data-row"><span class="k">capability</span><span class="v">${r.capability}</span></div>
        <div class="data-row"><span class="k">verdict</span><span class="v"><span class="verdict ${r.verdict}">${r.verdict}</span></span></div>
        <div class="data-row"><span class="k">summary</span><span class="v">${r.summary}</span></div>
        <div class="data-row"><span class="k">tx</span><span class="v">→ Aggregator.submit_result(0, ${short(r.address)}, "${r.capability}", "${r.verdict}", summary)</span></div>
      </div>`).join("")}`,
    7: () => `
      <div class="data-block">
        <div class="data-row"><span class="k">conflict check</span><span class="v">security-audit: [high] · market-analysis: [neutral] → no capability has >1 distinct verdict</span></div>
        <div class="data-row"><span class="k">path taken</span><span class="v"><span class="pill det">deterministic</span> _deterministic_aggregate() — no LLM synthesis needed</span></div>
        <div class="data-row"><span class="k">final_verdict</span><span class="v"><span class="verdict flagged">flagged</span> (escalated — "high" present)</span></div>
      </div>`,
    8: () => `
      <table>
        <thead><tr><th>#</th><th>Contract</th><th>Method</th><th>Type</th><th>Status</th></tr></thead>
        <tbody>
          <tr><td>1</td><td>Coordinator</td><td>submit_task</td><td><span class="pill nondet">non-det</span></td><td>Finalized</td></tr>
          <tr><td>2</td><td>Aggregator</td><td>register_task</td><td><span class="pill det">det</span></td><td>Finalized</td></tr>
          <tr><td>3</td><td>SecurityAgent</td><td>execute</td><td><span class="pill nondet">non-det</span></td><td>Finalized</td></tr>
          <tr><td>4</td><td>FinanceAgent</td><td>execute</td><td><span class="pill nondet">non-det</span></td><td>Finalized</td></tr>
          <tr><td>5</td><td>Aggregator</td><td>submit_result (Security)</td><td><span class="pill det">det</span></td><td>Finalized</td></tr>
          <tr><td>6</td><td>Aggregator</td><td>submit_result (Finance)</td><td><span class="pill det">det</span></td><td>Finalized</td></tr>
        </tbody>
      </table>
      <div class="data-block" style="margin-top:10px;">
        6 independent transactions, each validated by GenLayer's standard Equivalence Principle /
        Optimistic Democracy flow. No separate "mesh consensus" — every hop reuses the same protocol
        primitive a single Intelligent Contract would use.
      </div>`,
    9: () => `
      <div class="final-result">
        <div class="data-row"><span class="k">task_id</span><span class="v">0</span></div>
        <div class="data-row"><span class="k">verdict</span><span class="v"><span class="verdict flagged">flagged</span></span></div>
        <div class="data-row"><span class="k">summary</span><span class="v">[security-audit] high: No timelock on admin functions combined with high leverage creates significant rug-pull and liquidation cascade risk. | [market-analysis] neutral: TVL growth is healthy but insufficient on its own to offset structural risk.</span></div>
        <div class="data-row"><span class="k">confirmed by network</span><span class="v">true</span></div>
        <div class="data-row"><span class="k">readable via</span><span class="v">Aggregator.view().get_result(0)</span></div>
      </div>`,
  };
}

let running = false;

async function runDemo(){
  if (running) return;
  running = true;
  document.getElementById("run-btn").disabled = true;

  const container = document.getElementById("trace");
  renderSkeleton(container);
  const content = bodies();
  const stages = container.querySelectorAll(".stage");

  for (let i=0;i<stages.length;i++){
    const el = stages[i];
    el.classList.add("active","running");
    bodyFor(i+1).innerHTML = content[i+1]();
    await sleep(550);
    el.classList.remove("running");
    el.classList.add("done");
    await sleep(180);
  }

  document.getElementById("run-btn").disabled = false;
  running = false;
}

function sleep(ms){ return new Promise(r=>setTimeout(r, ms)); }

function resetDemo(){
  if (running) return;
  const container = document.getElementById("trace");
  renderSkeleton(container);
}

// ---------- Live mode (genlayer-js, read-only) ----------

async function fetchLiveState(){
  const registryAddr = document.getElementById("registry-addr").value.trim();
  const aggregatorAddr = document.getElementById("aggregator-addr").value.trim();
  const taskId = document.getElementById("task-id-input").value.trim();
  const status = document.getElementById("live-status");
  const container = document.getElementById("live-trace");

  if (!registryAddr && !aggregatorAddr){
    status.textContent = "Enter at least one deployed contract address.";
    return;
  }

  status.textContent = "Connecting to GenLayer via genlayer-js…";
  container.innerHTML = "";

  try {
    const { createClient } = await import("https://esm.sh/genlayer-js");
    const { studionet } = await import("https://esm.sh/genlayer-js/chains");
    const client = createClient({ chain: studionet });

    let html = "";

    if (registryAddr){
      const agents = await client.readContract({
        address: registryAddr,
        functionName: "getAgents",
        args: [],
      });
      html += `<div class="stage active done"><div class="stage-dot"></div>
        <div class="stage-header"><span class="stage-title">Registry — live getAgents()</span></div>
        <div class="stage-body" style="display:block;">
          <table><thead><tr><th>Name</th><th>Address</th><th>Capability</th><th>Active</th></tr></thead>
          <tbody>${(agents||[]).map(a=>`<tr><td>${a.name}</td><td class="addr">${short(String(a.address))}</td><td>${a.capability}</td><td>${a.active}</td></tr>`).join("")}</tbody></table>
        </div></div>`;
    }

    if (aggregatorAddr && taskId !== ""){
      const result = await client.readContract({
        address: aggregatorAddr,
        functionName: "get_result",
        args: [Number(taskId)],
      });
      html += `<div class="stage active done"><div class="stage-dot"></div>
        <div class="stage-header"><span class="stage-title">Aggregator — live get_result(${taskId})</span></div>
        <div class="stage-body" style="display:block;">
          <div class="data-block">
            <div class="data-row"><span class="k">finalized</span><span class="v">${result?.finalized}</span></div>
            <div class="data-row"><span class="k">verdict</span><span class="v">${result?.verdict}</span></div>
            <div class="data-row"><span class="k">summary</span><span class="v">${result?.summary}</span></div>
          </div>
        </div></div>`;
    }

    container.innerHTML = html || "<p style='color:var(--muted)'>Nothing to show.</p>";
    status.textContent = "Live state loaded.";
  } catch (err){
    status.textContent = "Could not reach contract — check address, network, and that it's deployed on the target chain.";
    console.error(err);
  }
}

// ---------- wiring ----------

document.getElementById("run-btn").addEventListener("click", runDemo);
document.getElementById("reset-btn").addEventListener("click", resetDemo);
document.getElementById("fetch-live-btn").addEventListener("click", fetchLiveState);

document.querySelectorAll(".mode-btn").forEach(btn=>{
  btn.addEventListener("click", ()=>{
    document.querySelectorAll(".mode-btn").forEach(b=>b.classList.remove("active"));
    btn.classList.add("active");
    const mode = btn.dataset.mode;
    document.getElementById("sim-panel").classList.toggle("hidden", mode!=="sim");
    document.getElementById("live-panel").classList.toggle("hidden", mode!=="live");
  });
});

renderSkeleton(document.getElementById("trace"));
