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
itself, never to a parameter the caller could set to any value.

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
```

Aggregator and Coordinator reference each other's address, so they
can't both be constructed in the same step — the deploy script deploys
Aggregator first, then Coordinator, then binds them together with one
write call before deploying the agents.

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Run the complete test suite:

```bash
gltest --network localnet
```

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
