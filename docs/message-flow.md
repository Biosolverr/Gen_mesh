# Message Flow & Consensus

## Overview

This document describes how a single request propagates through GenMesh
Core and how every execution step integrates with GenLayer's native
consensus model.

One important design principle should be kept in mind throughout this
document:

**GenMesh never introduces an additional execution protocol.**

Every step is simply another Intelligent Contract transaction executed
through the existing GenVM execution model.

---

# Complete Execution Timeline

A typical execution consists of several independent transactions.

```
User
 │
 ▼
Coordinator.submit_task()
 │
 ├──────────────► Registry.view()
 │
 ├──────────────► Agent.execute()
 │
 ├──────────────► Agent.execute()
 │
 └──────────────► Aggregator.register_task()
                          │
                          ▼
                 Agent.submit_result()
                          │
                          ▼
                 Agent.submit_result()
                          │
                          ▼
                  Aggregator.finalize()
                          │
                          ▼
                 Aggregator.get_result()
```

Each transaction is independently finalized through Optimistic
Democracy.

No transaction inherits trust from any previous transaction.

---

# Transaction Sequence

Example execution using the dashboard demonstration.

| # | Contract | Method | Type | Trigger |
|---|----------|--------|------|----------|
| 1 | Coordinator | `submit_task()` | Non-deterministic | User |
| 2 | Aggregator | `register_task()` | Deterministic | `emit()` |
| 3 | SecurityAgent | `execute()` | Non-deterministic | `emit()` |
| 4 | FinanceAgent | `execute()` | Non-deterministic | `emit()` |
| 5 | Aggregator | `submit_result()` | Deterministic | SecurityAgent |
| 6 | Aggregator | `submit_result()` | Deterministic | FinanceAgent |
| 7 | Aggregator | `_finalize()` | Deterministic or Non-deterministic | Automatic |

The exact ordering of Agent execution is **not guaranteed**.

Agents execute independently.

Results may arrive in any order.

---

# Coordinator Transaction

Coordinator performs one runtime planning operation.

Execution consists of:

```
submit_task()
        │
        ▼
Registry Discovery
        │
        ▼
Capability Planning
        │
        ▼
Execution Dispatch
```

Coordinator performs only one non-deterministic decision:

```
Which capabilities are required?
```

After dispatching execution it becomes inactive.

It does not monitor progress.

It does not retry execution.

It does not wait for results.

---

# Agent Transactions

Every selected Agent executes independently.

```
Coordinator
      │
      ▼
SecurityAgent

Coordinator
      │
      ▼
FinanceAgent

Coordinator
      │
      ▼
ResearchAgent
```

Each Agent performs:

```
execute()

↓

run_nondet_unsafe()

↓

Domain-specific inference

↓

submit_result()
```

Agents never communicate with each other.

Each Agent behaves as an isolated Intelligent Contract.

---

# Aggregator Transactions

Aggregator receives one transaction from every participating Agent.

```
Agent A
      │
      ▼

submit_result()

Agent B
      │
      ▼

submit_result()

Agent C
      │
      ▼

submit_result()
```

Only after all expected results have arrived does Aggregator begin
composition.

This separation keeps execution asynchronous while preserving
deterministic completion.

---

# Deterministic Execution

Most transactions are purely deterministic.

Examples include:

- Registry discovery
- Task registration
- Result submission
- Duplicate detection
- Completion checks
- Result storage

Every validator executes exactly the same code and must obtain exactly
the same state transition.

No Equivalence Principle is required.

---

# Non-Deterministic Execution

Only three operations may invoke LLM execution.

## Capability Planning

Performed by Coordinator.

Purpose:

```
User Request

↓

Required Capabilities
```

---

## Domain Inference

Performed independently by each Agent.

Purpose:

```
Task

↓

Specialized Result
```

---

## Semantic Aggregation

Performed only when deterministic aggregation cannot resolve conflicting
opinions.

Purpose:

```
Conflicting Results

↓

Semantic Synthesis
```

This operation uses the Equivalence Principle rather than strict
byte-for-byte equality.

---

# Deterministic-First Philosophy

Aggregation always follows the same priority.

```
Results

│

├────────► Compatible

│              │

│              ▼

│      Deterministic Composition

│

└────────► Conflict

               │

               ▼

      Equivalence Principle

               │

               ▼

        LLM Synthesis
```

LLM execution is considered the fallback path rather than the default
execution strategy.

---

# Consensus Integration

Every transaction follows the same protocol.

```
Leader

↓

Execution

↓

Validators

↓

Agreement

↓

Finalization
```

GenMesh introduces no additional consensus layer.

There is:

- no mesh consensus;
- no coordinator consensus;
- no agent voting;
- no quorum protocol.

The project relies entirely on Optimistic Democracy.

---

# Parallel Execution

Agents execute independently.

```
Coordinator

      │

 ┌────┴───────────┐

 ▼                ▼

Security      Finance

      │         │

      ▼         ▼

 submit      submit

      │         │

      └────┬────┘

           ▼

      Aggregator
```

Arrival order is intentionally ignored.

Aggregator waits until every expected participant has submitted exactly
one result.

---

# Idempotency

GenLayer may replay emitted transactions under specific conditions such
as appeals.

To remain safe under replay, Aggregator treats duplicate submissions as
no-ops.

```
Already Submitted?

      │

 ├── Yes → Ignore

 └── No → Store
```

This guarantees deterministic behavior regardless of replay order.

---

# Trust Boundary

The current MVP defines one explicit trust boundary.

Coordinator creates the execution manifest.

Aggregator accepts results only from addresses listed inside that
manifest.

```
Coordinator

↓

Expected Agents

↓

Aggregator

↓

Accept
```

Unknown contracts are rejected.

This prevents arbitrary Intelligent Contracts from injecting execution
results.

---

# Known MVP Simplification

Aggregator currently assumes the execution manifest is correct.

If Coordinator assigns an incorrect execution plan, Aggregator will
follow it.

Future versions could strengthen this assumption by introducing:

- signed execution manifests;
- capability verification;
- shared execution descriptors;
- independently verifiable planning metadata.

---

# Failure Scenarios

GenMesh intentionally keeps failure handling simple.

Possible situations include:

## Missing Agent

If no Agent supports a required capability:

```
Coordinator

↓

No Candidates

↓

Abort
```

---

## Duplicate Submission

If an Agent submits twice:

```
Submission

↓

Already Exists

↓

Ignored
```

---

## Unknown Agent

If a contract outside the execution plan submits a result:

```
Unknown Address

↓

Rejected
```

---

## Conflicting Opinions

If Agents disagree:

```
Conflict

↓

Equivalence Principle

↓

Semantic Synthesis
```

No manual arbitration layer exists.

---

# Why No Mesh Consensus Exists

A common misconception is that coordinating multiple Intelligent
Contracts requires a second consensus mechanism.

GenMesh demonstrates that this is unnecessary.

Every execution step is already secured individually.

```
Coordinator

↓

Optimistic Democracy

↓

SecurityAgent

↓

Optimistic Democracy

↓

FinanceAgent

↓

Optimistic Democracy

↓

Aggregator

↓

Optimistic Democracy
```

Rather than replacing consensus, GenMesh simply composes more
independently validated transactions.

This preserves GenLayer's native security model while enabling much
larger execution graphs.
