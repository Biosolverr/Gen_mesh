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

# Repository Structure

```
genmesh-core/
├── contracts/
│   ├── registry/
│   │   └── AgentRegistry.py
│   │
│   ├── coordinator/
│   │   └── Coordinator.py
│   │
│   ├── aggregator/
│   │   └── Aggregator.py
│   │
│   └── agents/
│       ├── SecurityAgent.py
│       ├── ResearchAgent.py
│       └── FinanceAgent.py
│
├── deploy/
│   └── deployScript.ts
│
├── test/
│   ├── test_registry.py
│   ├── test_coordinator.py
│   └── test_e2e_flow.py
│
├── dashboard/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── README.md
│
├── docs/
│   ├── architecture.md
│   ├── message-flow.md
│   └── agent-integration-guide.md
│
├── gltest.config.yaml
├── package.json
├── requirements.txt
└── README.md
```

---

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

The deployment script automatically deploys contracts in dependency
order:

```
Registry
    ↓
Aggregator
    ↓
Coordinator
    ↓
Agents
    ↓
Self-registration
```

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

The repository contains a standalone execution trace dashboard.

```
dashboard/
```

The dashboard is intentionally separated from the contracts.

Its purpose is **not** to become a wallet or transaction interface.

Its purpose is to visualize the execution flow of GenMesh Core.

Two modes are provided:

### Simulated Run

Demonstrates the complete execution pipeline using deterministic sample
data matching the implemented contracts.

This mode exists specifically so reviewers can understand the
architecture without deploying a test network.

### Live Read

Uses `genlayer-js` to call:

- Registry.getAgents()
- Aggregator.get_result()

against deployed contracts.

Only read operations are supported.

Transaction submission intentionally remains outside the dashboard.

Embedding private keys into a public Vercel deployment would violate the
same trust model GenMesh is designed to preserve.

Deployment instructions are available in:

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
| End-to-End Flow | ✅ Implemented |
| Vercel Deployment | ✅ Documented |
| Final Validation Against Latest SDK | ⚠ Pending |

The architecture is complete and fully documented.

Remaining work primarily consists of validating implementation details
against the latest released versions of the GenLayer SDK, CLI and
supporting libraries.

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

### Trusted execution manifest

Aggregator trusts the task manifest received from Coordinator.

Specifically:

```
expected_agents
```

is accepted as the authoritative execution plan.

This keeps the MVP architecture simple while still preserving the
Coordinator → Agent → Aggregator separation.

Future versions could independently verify execution plans or use
signed manifests.

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
- no planning responsibilities.

---

### Stage 6 — Dashboard

Goal:

Visualize the complete execution trace.

Key decisions:

- static frontend;
- simulated execution mode;
- read-only live mode;
- Vercel deployment.

---

# Roadmap

Short-term priorities:

- validate against latest SDK versions;
- deploy on testnet/studionet;
- publish dashboard;
- record demonstration video;
- gather reviewer feedback.

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
