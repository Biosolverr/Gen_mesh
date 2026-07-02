# GenMesh Core Architecture

## Overview

GenMesh Core is an infrastructure pattern for GenLayer that extends how
Intelligent Contracts cooperate during execution.

Rather than introducing a new execution environment, orchestration
framework or consensus protocol, GenMesh demonstrates how existing
GenLayer primitives can be composed into a runtime execution graph where
each Intelligent Contract remains independently validated through
Optimistic Democracy.

The project is built entirely from native GenVM components.

No external orchestrator exists.

No centralized scheduler exists.

No off-chain coordination layer exists.

---

# Core Idea

Traditional GenLayer execution can be viewed as:

```
User
    │
    ▼
Intelligent Contract
    │
    ▼
run_nondet_unsafe()
    │
    ▼
Optimistic Democracy
```

GenMesh extends this execution model into:

```
User
    │
    ▼
Coordinator
    │
    ▼
Registry Discovery
    │
    ▼
Runtime Execution Plan
    │
    ▼
Multiple Intelligent Contracts
    │
    ▼
Aggregator
    │
    ▼
Final Result
```

Every node remains an ordinary Intelligent Contract.

Every non-deterministic operation remains independently validated.

No execution step bypasses consensus.

---

# Vision

GenMesh Core is not another AI-agent framework deployed on a blockchain.

Instead, it explores a different execution model for Intelligent
Contracts.

Rather than treating a single Intelligent Contract as the only unit of
execution, GenMesh demonstrates that a complete task can be represented
as a runtime-composed graph of Intelligent Contracts while preserving
GenLayer's existing trust model.

This idea can be summarized as:

> GenMesh Core doesn't orchestrate AI agents on top of GenLayer. It
> extends what can be treated as the effective execution unit of a
> complex task—from a single Intelligent Contract to a runtime-composed
> graph of Intelligent Contracts, each independently secured through
> Optimistic Democracy.

---

# Design Goals

GenMesh was designed around several principles.

## Native GenLayer Integration

Every component must be an ordinary Intelligent Contract.

No privileged backend may exist.

No off-chain scheduler may exist.

---

## Protocol Compatibility

The project must use existing GenLayer primitives only.

Examples include:

- `@gl.public.write`
- `@gl.public.view`
- `gl.get_contract_at()`
- `emit()`
- `view()`
- `run_nondet_unsafe()`
- `gl.eq_principle.prompt_comparative()`

No custom protocol extensions are introduced.

---

## Runtime Composition

Execution plans are created dynamically.

No workflow is predefined.

No execution graph is hardcoded.

The set of participating contracts is determined separately for every
user request.

---

## Independent Validation

Every non-deterministic execution step is validated independently.

Planning.

Inference.

Aggregation.

Each follows the standard Optimistic Democracy process.

---

# Non-Goals

GenMesh intentionally does **not** attempt to become:

- a workflow engine;
- an AI orchestration framework;
- a custom consensus protocol;
- an off-chain coordination service;
- a blockchain operating system.

Its purpose is significantly narrower:

to demonstrate composable execution using native Intelligent Contracts.

---

# System Components

The architecture consists of four contract types.

```
Coordinator
      │
      ▼
Registry
      │
      ▼
Agents
      │
      ▼
Aggregator
```

Each component has a single responsibility.

---

## AgentRegistry

Responsibilities:

- capability discovery;
- agent registration;
- capability lookup.

Registry contains no LLM execution.

Registry contains no workflow logic.

Registry contains no execution planning.

It is intentionally deterministic.

---

## Coordinator

Coordinator performs exactly one intelligent task:

runtime capability planning.

Responsibilities:

- inspect Registry;
- determine required capabilities;
- create execution plan;
- dispatch execution.

Coordinator does **not**:

- monitor execution;
- retry failed tasks;
- maintain workflow state;
- aggregate results.

This distinction prevents Coordinator from becoming a workflow engine.

---

## Agent Contracts

Each Agent is an independent Intelligent Contract.

Responsibilities:

- perform one specialized inference;
- return one structured result.

Agents know nothing about Coordinator.

Agents trust no caller more than any other Intelligent Contract.

Agents expose a standard execution interface.

Any compatible contract can become part of the mesh.

---

## Aggregator

Aggregator performs result composition.

Responsibilities:

- receive Agent results;
- detect completion;
- aggregate outputs;
- publish final result.

Aggregator never:

- discovers agents;
- creates execution plans;
- dispatches contracts.

Its role begins only after execution has already started.

---

# Architectural Invariants

The project enforces several architectural rules.

## Registry is deterministic

Registry never executes LLM inference.

Its purpose is deterministic discovery.

---

## Coordinator plans only

Coordinator decides:

"What should execute?"

It never decides:

"What happened afterwards?"

---

## Agents remain independent

Agents never reference Coordinator.

They remain reusable Intelligent Contracts that can be invoked by any
compatible contract.

---

## Aggregator composes only

Aggregation never becomes orchestration.

Planning belongs to Coordinator.

Composition belongs to Aggregator.

---

# Native GenLayer Integration

Every architectural decision follows existing GenLayer primitives.

Discovery uses deterministic on-chain state.

Planning uses non-deterministic execution.

Inference uses non-deterministic execution.

Aggregation uses deterministic composition whenever possible and falls
back to the Equivalence Principle only when semantic synthesis is
required.

Nothing in the architecture requires modifications to GenVM.

---

# Extensibility

Adding a new capability requires only two operations:

1. Deploy a compatible Intelligent Contract.
2. Call `register_self()`.

Coordinator automatically discovers the new capability during the next
execution.

No Coordinator upgrade is required.

No Registry modification is required.

No Aggregator modification is required.

This demonstrates runtime composability rather than static integration.

---

# Current MVP Limitations

The current implementation intentionally remains minimal.

Known limitations include:

- single-agent selection per capability;
- trusted execution manifest;
- no reputation system;
- no staking;
- no incentive layer;
- deterministic provider selection.

These limitations simplify the implementation while preserving the
architectural idea being validated.

---

# Conclusion

GenMesh Core demonstrates that complex execution can emerge from the
composition of ordinary Intelligent Contracts without introducing a new
execution environment or consensus mechanism.

Every component remains independently secured by Optimistic Democracy.

Every component remains reusable.

Every component follows a single responsibility.

Rather than replacing GenLayer's execution model, GenMesh explores how
that model can be composed into larger execution graphs while preserving
the protocol's native trust assumptions.

