# Project Status

## Overview

GenMesh Core has been developed as a complete end-to-end proof of concept
demonstrating how multiple Intelligent Contracts can form a runtime
execution graph while remaining fully compatible with GenLayer's native
execution and consensus model.

The project intentionally avoids introducing:

- external orchestrators;
- backend services;
- custom consensus protocols;
- privileged coordinators;
- off-chain agent routing.

Instead, every component is implemented as a standard Intelligent
Contract.

---

# Development Timeline

The project was built incrementally through six development stages.

## Stage 1 — Architecture

Defined the overall concept.

Introduced the central idea:

> Extend the execution model of Intelligent Contracts from a single
> contract into a runtime-composed graph of Intelligent Contracts.

Major design decisions:

- composable execution;
- no external orchestration;
- native GenVM execution only;
- Optimistic Democracy at every execution step.

Status:

✅ Completed

---

## Stage 2 — Agent Registry

Implemented an on-chain discovery primitive.

Responsibilities:

- self-registration;
- capability discovery;
- deterministic execution;
- permissionless participation.

Important design choices:

- no LLM usage;
- no non-deterministic execution;
- self-registration only;
- discovery through contract interfaces.

Status:

✅ Completed

---

## Stage 3 — Coordinator

Implemented runtime planning.

Responsibilities:

- read Registry;
- determine required capabilities;
- dispatch execution;
- register execution manifest.

Coordinator intentionally does **not**:

- monitor execution;
- retry tasks;
- collect responses;
- maintain workflow state.

Its responsibility ends immediately after dispatch.

Status:

✅ Completed

---

## Stage 4 — Agents

Implemented multiple specialized Intelligent Contracts.

Current Agents:

- SecurityAgent
- FinanceAgent
- ResearchAgent

Each Agent:

- performs independent inference;
- owns one capability;
- returns structured output;
- accepts execution triggers only from the single Coordinator it is
  bound to via `set_coordinator()`, never from an arbitrary caller.

The interface is intentionally identical across all Agents.

Status:

✅ Completed

---

## Stage 5 — Aggregator

Implemented result composition.

Execution strategy:

```
Deterministic aggregation

↓

Semantic aggregation only if necessary
```

Important improvements:

- deterministic-first execution;
- Equivalence Principle used for semantic synthesis;
- duplicate protection;
- expected-agent validation;
- manifest changes restricted to a single bound Coordinator;
- results attributed to the transaction sender rather than a
  caller-supplied value.

Status:

✅ Completed

---

## Stage 6 — Dashboard

Implemented a control panel covering every contract in the mesh.

Features:

- complete execution timeline;
- transaction visualization;
- execution graph;
- direct read/write access to every contract method;
- a signed browser session (private key held only in tab memory, never
  persisted) for write calls;
- an activity log with real transaction hashes linked to the network
  explorer;
- Vercel deployment.

Status:

✅ Completed

---

# Current Architecture

The complete execution graph is now implemented.

```
User

↓

Coordinator

↓

Registry

↓

Agents

↓

Aggregator

↓

Result
```

Every node is an Intelligent Contract.

Every interaction is a contract interaction.

No external services participate.

---

# Repository Structure

```
genmesh-core/

├── contracts/
│
├── dashboard/
│
├── deploy/
│
├── docs/
│
├── test/
│
├── README.md
│
├── requirements.txt
│
├── package.json
│
└── gltest.config.yaml
```

---

# Technical Highlights

The project demonstrates:

- runtime capability discovery;
- dynamic execution planning;
- asynchronous contract composition;
- deterministic-first aggregation;
- semantic conflict resolution;
- independent Optimistic Democracy validation;
- permissionless Agent integration;
- sender-authenticated trust boundaries between Coordinator, Agents,
  and Aggregator.

---

# Known MVP Limitations

The current implementation intentionally leaves several improvements for
future versions.

## Single Bound Coordinator

Aggregator accepts manifest changes from exactly one Coordinator address
at a time, set via `set_coordinator()`. Supporting multiple concurrent
Coordinators over the same Aggregator, or independently signed
manifests instead of a single trusted address, is left for future work
(see `docs/future-work.md`).

---

## Multi-Capability Agents

The Registry currently stores one capability per Agent.

Future versions could support:

```
capabilities:

- research
- finance
- security
```

instead of a single capability string.

---

## Agent Selection

Coordinator currently selects available Agents from Registry results.

Future research could explore:

- ranking;
- reputation;
- specialization;
- historical performance.

These improvements are intentionally outside the MVP scope.

---

# Security Model

GenMesh inherits GenLayer's security model.

It does not introduce trusted validators, and identity for manifest
changes, execution triggers, and result submissions is verified at the
contract level rather than assumed from the caller:

- `Aggregator.register_task` / `add_expected_agent` require the sender
  to be the bound Coordinator address;
- each Agent's `execute()` requires the sender to be that Agent's own
  bound Coordinator address;
- `Aggregator.submit_result` attributes a result to the transaction
  sender, not to any value the caller supplies, and checks the
  submitted capability against the one Coordinator registered for that
  sender via `add_expected_agent`.

The `execute()` restriction was added after external review (Pavel
Kolosov, Jul 31 2026) identified that an earlier, unrestricted
`execute()` let any caller supply fabricated task data to a registered
Agent and pre-empt the Coordinator's own dispatch for that task_id,
since Aggregator's per-agent submission dedup would silently keep
whichever submission arrived first. A regression test
(`test_execute_rejects_non_coordinator_caller`) covers this path in
`test/test_mesh_e2e.py`.

Every execution step remains independently verifiable through
Optimistic Democracy.

These boundaries have been verified directly against the live studionet
deployment, not only in source: a manual `register_task` call from a
non-Coordinator session reverted with `"Only the coordinator can modify
a task manifest"`, `get_task_count` was unchanged afterward, and a
manual `add_expected_agent` call from the same session reverted
identically.

---

# Dashboard

The included dashboard is a control panel for the complete execution
lifecycle — every read and write method on all six contracts, connected
directly to studionet with no backend in between.

A signed browser session enables write calls (registering an agent,
submitting a task, and so on); the private key involved is held only in
the browser tab's memory and is never persisted. Read calls work
without a session at all. Every call is recorded in an activity log
with, for writes, a real transaction hash linked to the network
explorer.

---

# Testing

`test/test_mesh_e2e.py` is committed to the repository and runs via
`gltest --network studionet` (or `localnet`). It deploys the full mesh,
submits a task through Coordinator, and polls Aggregator until the task
is finalized — no manual resends, no manual reads from the dashboard.
Three additional regression tests in the same file cover sender
authentication (`submit_result` rejecting an unregistered caller), the
coordinator-only manifest restriction (`register_task` rejecting a
non-Coordinator caller), and the coordinator-only execution restriction
(`execute` rejecting a direct call from a non-Coordinator caller with
fabricated task data).

Completing an automated run of this test currently requires a full
local GenLayer Studio environment (Docker, multiple containers, a live
validator set), which has not been possible to finish end to end so
far — not due to any issue in the contracts or the test itself, but
because of a combination of local hardware limits and several
independent, reproducible bugs found in the current GenLayer CLI and
Studio backend release along the way (provider name mismatch on
`genlayer init`, a stale default model, a `gltest.config.yaml` schema
change, an undersized `/dev/shm` crashing a GenVM subprocess, and
finally the backend's own transaction scheduler never picking up an
otherwise correctly `ACTIVATED` transaction). Full reproduction details,
logs, and version information are documented separately.

In place of a completed automated run, the same behavior the test
checks for — full mesh completion, sender authentication, and the
coordinator-only manifest restriction — has been verified directly
against the live studionet deployment through the dashboard: two
separate tasks were submitted and finalized with distinct,
non-cached LLM-generated results persisted on-chain, and both
`register_task` and `add_expected_agent` were confirmed to revert with
the expected error when called from a non-Coordinator session.

---

# Project Goal

GenMesh Core is not intended to be another AI Agent framework.

Its objective is to demonstrate that:

- execution graphs can be composed entirely from Intelligent Contracts;
- every execution step can remain independently secured;
- no additional consensus layer is required;
- GenLayer's existing execution model naturally supports composable
  execution.

---

# Current Status

Architecture

✅ Complete

Registry

✅ Complete

Coordinator

✅ Complete

Agents

✅ Complete

Aggregator

✅ Complete

Dashboard

✅ Complete

Documentation

✅ Complete

Deployment

✅ Complete

Testing

🟡 Test written and manually verified against live studionet;
automated run blocked by external GenLayer tooling bugs (see "Testing"
above for details)

---

# Future Work

Potential research directions include:

- multiple Coordinators operating over the same Registry and Aggregator;
- Agent reputation systems;
- capability version negotiation;
- richer execution planning;
- independently verifiable execution manifests;
- advanced deterministic aggregation strategies;
- multi-capability Agents;
- execution graph optimization.

These extensions can be added without changing the core architecture,
demonstrating that GenMesh is designed as an extensible execution
primitive rather than a fixed application.
