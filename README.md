# GenMesh Core

> **Composable execution layer for Intelligent Contracts on GenLayer.**

GenMesh Core is **not** a dApp, not an AI-agents framework, and not an
AutoGen/CrewAI/LangGraph orchestration layer deployed on a blockchain.

Instead, GenMesh Core extends the execution model of GenVM itself:
the effective execution unit for complex tasks becomes a **runtime-composed
graph of Intelligent Contracts**, while every individual contract
continues to execute independently under GenLayer's native Optimistic
Democracy protocol.

```
Registry → Coordinator → Agent IC(s) → Aggregator
```

Every hop of the graph remains an ordinary Intelligent Contract.
GenMesh does not introduce a new consensus mechanism, external workflow
engine, privileged orchestrator or backend service. It composes existing
GenLayer primitives into a reusable execution pattern.

---

# Why GenLayer?

GenMesh Core is designed specifically around GenLayer's native execution
model.

Instead of replacing protocol primitives, it composes them.

GenLayer already provides:

- Intelligent Contracts capable of deterministic and non-deterministic execution;
- Optimistic Democracy for validating non-deterministic execution;
- Equivalence Principle for semantic agreement instead of strict byte equality;
- native Intelligent Contract → Intelligent Contract interaction.

GenMesh Core demonstrates that these primitives are sufficient to build
higher-level execution graphs without introducing a second coordination
layer.

Rather than creating "AI agents on a blockchain", GenMesh shows how
existing Intelligent Contracts can be dynamically discovered, composed
and executed as one logical workflow while each contract remains an
independent participant of Optimistic Democracy.

---

# Architecture

```
                   User Request
                         │
                         ▼
                  Coordinator IC
               (Capability Planning)
                         │
                         ▼
                  Registry Lookup
              (Discovery Primitive)
                         │
                         ▼
                Execution Plan Created
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 SecurityAgent      FinanceAgent     ResearchAgent
     IC                 IC                IC
        └────────────────┼────────────────┘
                         ▼
                  Aggregator IC
             (Deterministic First)
                         │
                         ▼
              Optimistic Democracy
                         │
                         ▼
                  Final Result
```

Every component has a single responsibility.

| Contract | Responsibility |
|-----------|----------------|
| Registry | On-chain capability discovery |
| Coordinator | Runtime planning |
| Agent IC | Domain-specific execution |
| Aggregator | Result composition |

---

# Design Principles

The architecture intentionally follows several strict design principles.

### 1. Native GenLayer primitives only

No external orchestrator.

No backend.

No off-chain workflow engine.

Everything is implemented using ordinary Intelligent Contracts.

---

### 2. One responsibility per contract

Registry performs discovery.

Coordinator performs planning.

Agents perform execution.

Aggregator performs composition.

Responsibilities never overlap.

---

### 3. Deterministic whenever possible

Non-deterministic execution is used only where deterministic logic is
objectively insufficient.

Whenever deterministic aggregation is possible, it has priority.

LLM-based synthesis is only a fallback.

---

### 4. Permissionless extensibility

Adding a new capability never requires changing Coordinator.

Deploy:

```
New Agent IC
```

Register:

```
register_self()
```

The new capability immediately becomes discoverable through Registry.

---

### 5. No custom consensus

GenMesh introduces **zero** additional consensus logic.

Every execution step is independently secured through the existing
Optimistic Democracy mechanism already provided by GenLayer.

---

### 6. Sender-authenticated trust boundaries

Aggregator never accepts caller-supplied identity as fact.

Task-manifest changes (`register_task`, `add_expected_agent`) are
restricted to the single Coordinator contract Aggregator is bound to.
Results (`submit_result`) are attributed to the transaction sender
itself, never to a parameter the caller could set to any value, and the
submitted capability is checked against the one Coordinator actually
registered for that sender on that task.

Each Agent's `execute()` is likewise restricted to the single
Coordinator it's bound to via `set_coordinator()` — task content only
ever reaches an Agent through that trusted dispatch, never from an
arbitrary external caller.

Identity verification lives inside the protocol layer — no contract
takes a caller's word for who it is.

---

# Repository Structure

```
genmesh-core/
├── contracts/
│   ├── agents/
│   │   ├── FinanceAgent.py
│   │   ├── ResearchAgent.py
│   │   └── SecurityAgent.py
│   ├── aggregator/
│   │   └── Aggregator.py
│   ├── coordinator/
│   │   └── Coordinator.py
│   └── registry/
│       └── AgentRegistry.py
├── dashboard/
│   ├── README.md
│   └── index.html
├── deploy/
│   └── deployScript.ts
├── docs/
│   ├── agent-integration-guide.md
│   ├── architecture.md
│   ├── future-work.md
│   ├── message-flow.md
│   └── project-status.md
├── .gitignore
├── README.md
├── gltest.config.yaml
├── package.json
└── requirements.txt
```

# Quick Start (Localnet)

Requirements:

- Python 3.11+
- Docker
- GenLayer CLI

Install GenLayer CLI:

```bash
npm install -g genlayer
```

Start a local network:

```bash
genlayer up
```

Select localnet:

```bash
genlayer network set localnet
```

Deploy the complete execution mesh:

```bash
genlayer deploy
```

The deployment script deploys contracts in dependency order and wires
them together:

```
Registry
    ↓
Aggregator
    ↓
Coordinator
    ↓
Bind Aggregator ↔ Coordinator
    ↓
Agents
    ↓
Self-registration
    ↓
Bind each Agent ↔ Coordinator
```

Aggregator and Coordinator reference each other's address, so they
can't both be constructed in the same step — the deploy script deploys
Aggregator first, then Coordinator, then binds them together with one
write call before deploying the agents. Each Agent is bound to
Coordinator the same way, one write call per agent, after it
self-registers — until that call runs, the agent's `execute()` rejects
every caller, including Coordinator itself.

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the complete test suite:

```bash
gltest --network localnet
```

## Deployed Addresses (studionet)

| Contract | Address |
|---|---|
| AgentRegistry | `0xE9db8f162378258e8116DE2e3db57c9e58B4fF5d` |
| Coordinator | `0xe822a83B3EBF9f52c2Cdab3DCDE8f00D4bA0FD87` |
| Aggregator | `0x8c2714ea60FDc550Ff45C08c88D26e74Af4438E3` |
| SecurityAgent | `0xD0949F5529Be66d4eb4c5D7b5a35EBe1216409b3` |
| ResearchAgent | `0x7C2eFc70e337890aDfF35292A000fb2ce4A6efeA` |
| FinanceAgent | `0xc920C49c24ADda446602d5B8E04013f8ac9cd4Bf` |

These are studionet addresses and may be redeployed as the network
resets; treat them as the current reference deployment rather than a
permanent address.
---

# Submitting a Task

Example:

```bash
genlayer write <coordinator_address> submit_task \
  --args "Review this DeFi lending pool before listing: high leverage, no timelock on admin functions"
```

Retrieve the final aggregated result:

```bash
genlayer call <aggregator_address> get_result --args 0
```

---

# Dashboard

The repository contains a standalone control panel for the whole mesh.

```
dashboard/
```

It's a single `index.html` file — no build step, no dependencies beyond
`genlayer-js` loaded from a CDN. It gives direct access to every
read/write method on all six contracts, connected straight to
studionet, with no backend in between.

A local signing session (studionet private key, held only in the
browser tab's memory, never persisted) enables write calls —
registering an agent, submitting a task, and so on. Read calls work
without a session key at all.

Every call made from the panel is recorded in an Activity Log, with a
real transaction hash and a link to the network explorer for writes.
Nothing shown in the panel is simulated — it reflects the live state of
whatever contracts you point it at.

Deployment instructions are available in `dashboard/README.md`.

---

# Current Status

Project maturity:

| Component | Status |
|------------|----------|
| Architecture | ✅ Complete |
| Registry | ✅ Implemented |
| Coordinator | ✅ Implemented |
| Agents | ✅ Implemented |
| Aggregator | ✅ Implemented |
| Dashboard | ✅ Implemented |
| Local Deployment | ✅ Documented |
| Automated Tests | ✅ Implemented |
| End-to-End Flow | ✅ Validated on studionet |
| Vercel Deployment | ✅ Documented |
| SDK Compatibility | ✅ Validated against current GenLayer Studio/SDK |

The architecture, contracts, and dashboard have all been exercised
end-to-end against a live GenLayer Studio deployment on studionet,
including the full path from a signed `submit_task` call through
Coordinator planning, parallel Agent execution, and Aggregator
composition to a finalized result.

---

# Automated End-to-End Test — Environment Blocker

`test/test_mesh_e2e.py` is committed to the repository and is written to
run via `gltest --network studionet`, driving the full mesh
(registration → `submit_task` → Coordinator fan-out → Agent execution →
Aggregator finalization) without any manual resends. It has been
executed against a real, live GenLayer Studio deployment — not a mock —
and reached a signed, `ACTIVATED` transaction on the network.

Running it end to end currently requires a full local GenLayer Studio
environment (Docker, multiple containers, a live validator set). This
has not been possible to complete in an automated CI/CLI run so far, for
reasons unrelated to the contracts:

- **Local hardware constraint.** The development machine cannot run
  Docker Desktop locally (insufficient virtualization-capable hardware),
  ruling out running the stack on localhost.
- **Cloud Docker environments hit unrelated GenLayer CLI/Studio bugs.**
  Testing moved through GitHub Codespaces and Google Cloud Shell to get
  a working Docker host. Along the way, several independent bugs were
  found and worked around in the current GenLayer CLI / Studio backend
  release, unrelated to this repository's contracts:
  - `genlayer init`'s Gemini provider setup sends the provider key as
    `geminiai`, while the backend only recognizes `google` — reproduced
    identically on CLI 0.38.16 and 0.39.2 (latest stable), and on
    backend versions v0.65.0 and v0.79.1.
  - The CLI's default Gemini model (`gemini-1.5-flash`) has been removed
    from Google's API.
  - The `gltest.config.yaml` schema shipped with this repository predates
    a breaking config-format change in the currently published
    `genlayer-test` package.
  - Docker's default 64MB `/dev/shm` is too small for a GenVM subprocess
    that runs unconditionally on every transaction, crashing it
    regardless of whether the contract touches the internet.
- **Remaining blocker: backend scheduler.** After working around all of
  the above (current backend version, valid provider/model, 5 live
  validators), a submitted transaction reaches `ACTIVATED` status, but
  the Studio backend's own transaction-processing loop
  (`backend.consensus.base:_process_pending_transactions`) never picks
  it up for execution — its internal `Contracts with pending` counter
  stays at 0 for the full duration of the run, even while the
  transaction sits with status `PENDING` in the database, so validators
  never commit a vote. This was reproduced identically across three
  independent backend/CLI version combinations, ruling out a stale or
  misconfigured environment.

**Correctness has instead been validated directly against the deployed
studionet contracts**, using the dashboard described above rather than
an automated harness:

- `Aggregator.get_result` was called for two separate finalized tasks,
  returning distinct, non-cached LLM-generated submissions from both
  agents for each task — confirming the full `submit_task` → Coordinator
  fan-out → Agent execution → Aggregator finalization path executes
  correctly and persists on-chain.
- A manual `register_task` call from a non-Coordinator session reverted
  with `"Only the coordinator can modify a task manifest"`, and
  `get_task_count` was unchanged afterward — confirming the
  coordinator-only manifest restriction is enforced on-chain, not only
  in source.
- A manual `add_expected_agent` call from the same non-Coordinator
  session reverted identically, confirming the restriction applies
  uniformly across both manifest-mutating methods.

Full logs, version information, and raw RPC output documenting the
environment issues above are available on request.

---

# Known MVP Limitations

The current version intentionally focuses on validating the execution
model rather than maximizing functionality.

The following limitations are known and documented.

### Single agent per capability

Coordinator currently selects the first matching registered agent for a
required capability.

Current routing:

```
Capability
     ↓
First Matching Agent
```

Future versions may support:

- multiple agents per capability;
- weighted routing;
- capability replication;
- consensus among agents sharing a capability.

---

### No reputation layer

Agents are discovered through capabilities only.

Current selection does not consider:

- historical performance;
- reputation;
- stake;
- trust score.

This omission is intentional.

The MVP validates composable execution, not agent economics.

---

### No incentive mechanism

GenMesh does not currently introduce:

- rewards;
- fees;
- staking;
- slashing.

Execution relies entirely on GenLayer's existing infrastructure.

---

### Deterministic routing

Capability matching is dynamic.

Agent selection is deterministic.

Future versions may support:

- ranking;
- weighted selection;
- semantic agent matching;
- reputation-aware routing.

---

# Why GenMesh Is Not an AI Agents Framework

Many systems already exist for orchestrating LLM agents.

Examples include:

- AutoGen
- CrewAI
- LangGraph
- LangChain

GenMesh is fundamentally different.

Traditional AI-agent frameworks:

```
Agent
   ↓
Agent
   ↓
Agent
```

operate inside a trusted execution environment controlled by the
application developer.

Consensus is not part of the model.

Trust is external.

GenMesh instead operates as:

```
Intelligent Contract
          ↓
Optimistic Democracy
          ↓
Intelligent Contract
          ↓
Optimistic Democracy
```

Every execution hop remains independently secured by the protocol.

The objective is not to orchestrate agents.

The objective is to compose Intelligent Contracts.

---

# Future Work

The current implementation intentionally focuses on validating the
architecture.

Several extensions naturally follow.

### Multi-agent capability replication

Instead of selecting one agent:

```
security-audit
      ↓
SecurityAgent
```

multiple independent agents could execute the same capability.

```
security-audit
      ↓
 ┌────┼────┐
 ▼    ▼    ▼
A    B    C
```

allowing Aggregator to compose multiple opinions.

---

### Reputation-aware discovery

Registry could evolve from:

```
capability → address
```

into:

```
capability → ranked providers
```

without changing Coordinator's role.

---

### Capability versioning

Future agents may expose:

```
market-analysis v1
market-analysis v2
market-analysis v3
```

allowing runtime selection among implementations.

---

### Domain-specific registries

Multiple registries could coexist:

```
Finance Registry

Security Registry

Research Registry
```

while preserving the same Coordinator pattern.

---

### Cross-mesh execution

Future Coordinators could invoke Agents registered in different meshes.

This would allow composition across independently managed capability
networks.

---

### Economic Layer

Potential future additions:

- staking;
- slashing;
- execution fees;
- reputation incentives.

These are intentionally excluded from the MVP.

---

# Development History

The project was developed incrementally.

Each stage introduced one architectural primitive while enforcing strict
constraints.

### Stage 1 — Architecture

Goal:

Define GenMesh as an execution-layer concept rather than an application.

Result:

```
Registry
     ↓
Coordinator
     ↓
Agents
     ↓
Aggregator
```

---

### Stage 2 — Registry

Goal:

Create a permissionless discovery primitive.

Key decisions:

- self-registration;
- deterministic only;
- no LLM;
- no external database.

---

### Stage 3 — Coordinator

Goal:

Introduce runtime planning.

Key decisions:

- capability matching only;
- no workflow state;
- no monitoring;
- no retry management.

---

### Stage 4 — Agents

Goal:

Prove that ordinary Intelligent Contracts can become execution nodes.

Key decisions:

- no Coordinator dependency;
- no trusted caller;
- standard IC interface only.

---

### Stage 5 — Aggregator

Goal:

Compose results without becoming a second Coordinator.

Key decisions:

- deterministic-first aggregation;
- Equivalence Principle only when necessary;
- no planning responsibilities;
- task-manifest changes restricted to the bound Coordinator, results
  attributed to the transaction sender rather than a caller-supplied
  parameter.

---

### Stage 6 — Dashboard

Goal:

Visualize and operate the complete execution trace.

Key decisions:

- single static file, no build step;
- session-based signing, private key held only in browser memory;
- direct read/write access to every contract method, not just a
  read-only visualization;
- activity log with real transaction hashes linked to the network
  explorer;
- Vercel deployment.

---

# Roadmap

Short-term priorities:

- broaden automated `gltest` coverage to mirror what has been validated
  manually on studionet;
- track GenLayer testnet/mainnet availability for eventual migration;
- refine dashboard convenience features around task-id retrieval after
  `submit_task`.

Medium-term priorities:

- capability replication;
- reputation layer;
- capability versioning;
- multi-registry support.

Long-term priorities:

- economic layer;
- mesh-to-mesh execution;
- protocol-level standardization patterns.

---

# Contributing

Contributions are welcome.

Particularly valuable areas include:

- SDK compatibility testing;
- deployment tooling;
- additional Agent implementations;
- dashboard improvements;
- documentation.

Before opening large architectural changes, please review:

```
docs/architecture.md
```

to ensure alignment with the project's design principles.

---

# License

MIT License.

---

# Conclusion

GenMesh Core does not attempt to replace GenLayer.

It attempts to demonstrate a new way of using the primitives GenLayer
already provides.

The project is built around a single idea:

> Complex tasks should not require a privileged orchestrator.

Instead, they can emerge from the composition of independently validated
Intelligent Contracts.

GenMesh Core does not orchestrate AI agents on top of GenLayer.

It extends what can be treated as the effective execution unit of a
complex task—from a single Intelligent Contract to a runtime-composed
graph of Intelligent Contracts, each independently secured through
Optimistic Democracy.

If Intelligent Contracts are GenLayer's fundamental building block,
GenMesh explores what happens when those blocks become composable.
