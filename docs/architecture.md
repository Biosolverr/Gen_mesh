# GenMesh Core — Architecture

## The Idea

GenMesh Core doesn't add another application on top of GenLayer — it
extends the execution model of Intelligent Contracts itself: the unit
of execution stops being equal to one contract with one non-det block
and becomes a runtime-composed graph of Intelligent Contracts, where
every node independently goes through Optimistic Democracy.

> GenMesh Core doesn't orchestrate AI agents on top of GenLayer — it
> extends what counts as a single unit of GenVM execution, from one
> Intelligent Contract to a runtime-composed graph of Intelligent
> Contracts, each independently secured by Optimistic Democracy.

## Flow Diagram

```
User
 │
 ▼
[TX 1] Coordinator.submit_task()  [@gl.public.write]
 │  ├─ AgentRegistry.view().findByCapability(...)   ← deterministic read
 │  └─ run_nondet_unsafe(leader_fn, validator_fn)
 │        gl.nondet.exec_prompt(planning_prompt, response_format='json')
 │        → required_capabilities: [...]
 │  └─ emit(on='finalized').register_task(...) → Aggregator (manifest — FIRST)
 │  └─ emit(on='finalized').add_expected_agent(..., capability) → Aggregator, once per agent
 │  └─ emit(on='finalized').execute(...) → each selected Agent IC (AFTER the manifest)
 │
 ▼
[TX 2..N] Agent_i.execute(task_id, task_description, capability, aggregator_address)
 │  ├─ sender must be the Agent's bound Coordinator address, checked first
 │  └─ run_nondet_unsafe(leader_fn, validator_fn)
 │        domain-specific gl.nondet.exec_prompt(...)
 │  └─ emit(on='finalized').submit_result(...) → Aggregator, no address parameter —
 │        Aggregator derives identity from the transaction sender itself
 │
 ▼
[TX N+1..] Aggregator.submit_result(...)  (once per agent)
 │  ├─ verifies sender is an expected participant for this task_id
 │  ├─ verifies the submitted capability matches the one Coordinator
 │  │     registered for this sender via add_expected_agent
 │  ├─ priority: deterministic composition
 │  ├─ fallback: gl.eq_principle.prompt_comparative(...) on a verdict conflict
 │  └─ finalization: final_verdict, final_summary
 │
 ▼
User / dApp reads Aggregator.view().get_result(task_id)
```

The manifest is registered in Aggregator **before** any agent receives
the task. This ordering is a guarantee enforced by `Coordinator.submit_task`
itself, not an artifact of network timing — a task can never exist in
Aggregator later than the first agent is able to report on it. See
`docs/message-flow.md` for the full transaction-level breakdown.

## Roles

| Role | Non-det operations | Knows about | Who can write to its state |
|---|---|---|---|
| **AgentRegistry** | none | nobody — pure discovery | the agent itself (self) or the owner |
| **Coordinator** | capability matching | Registry, Aggregator — does NOT know specific agents | anyone calls `submit_task` (that's the entry point) |
| **Agent (N of them)** | domain inference | only its own capability, plus the single Coordinator address it's bound to | only that bound Coordinator calls `execute` (see invariant 2 below); `set_coordinator` — owner only |
| **Aggregator** | only on a verdict conflict | nothing beyond what it was told in the manifest | `register_task`/`add_expected_agent` — Coordinator only (`set_coordinator`); `submit_result` — only an address from the manifest, determined by the transaction sender, and only for the capability that address was actually registered under |

## Why This Is Native to GenLayer

- Every node is a full `gl.Contract` using only standard GenVM
  primitives: `@gl.public.write`/`view`, `gl.get_contract_at()`,
  `emit()`/`view()`, `run_nondet_unsafe`, `gl.eq_principle.prompt_comparative`.
- Discovery is `AgentRegistry.view()` — a deterministic read of on-chain
  state, not an HTTP call to an external service.
- No hop in the graph is taken out of consensus: planning, each
  agent-inference call, and conflict-time aggregation are three
  independent non-det operations, each with its own Leader→Validators
  cycle.

## Three Invariants Verified at Stage 4 (Agents)

1. The agent doesn't know about Coordinator's planning logic — zero
   references to how a task's capabilities were selected, only a
   single stored address it's willing to accept `execute()` calls from.
2. The agent doesn't trust an incoming call any more than it would
   trust any other IC — but "any other IC" here means "the bound
   Coordinator," not "anyone." An earlier version left `execute()` open
   to any caller, on the reasoning that the agent holds no state a
   malicious call could corrupt directly. That reasoning missed a
   real attack: a caller could pass fabricated `task_description` for
   an already-registered `task_id`, and the agent — using its own
   genuine, registered address — would submit that fabricated result
   to Aggregator, silently pre-empting the real submission Coordinator's
   own dispatch would have produced (Aggregator deduplicates
   submissions per `task_id` + sender address, so the first one in
   wins). Restricting `execute()` to the agent's bound Coordinator
   closes this: task content now only reaches an agent through a
   dispatch path that is itself gated (see invariant below on
   Aggregator's manifest-first ordering) — an attacker can no longer
   inject arbitrary task content into a legitimate agent's inference at
   all, regardless of what `task_id` they target.
3. The agent hands off its result only through the contract interface
   (`aggregator.emit().submit_result(...)`), no external channel.
   Aggregator, in turn, doesn't trust a parameter for this — sender
   identity comes from `gl.message.sender_address`, not from an
   argument a caller could forge, and the submitted `capability` is
   checked against the one Coordinator registered for that sender on
   that task, so a submission can't be misattributed to a capability
   the agent wasn't actually assigned.

## Integration with Optimistic Democracy (Stage 5)

Aggregator doesn't add a separate "mesh consensus." It uses exactly two
standard GenVM modes:

- **Deterministic branch** (`register_task`, conflict-free
  `submit_result`) — ordinary `@gl.public.write` transactions, verified
  by strict-equality re-execution, the same way any non-LLM transaction
  is verified in the network today.
- **Non-det branch** (`_llm_aggregate` on a verdict conflict) — the
  standard GenLayer Equivalence Principle mechanism
  (`gl.eq_principle.prompt_comparative`) for checking equivalence of a
  non-deterministic result.

The full chain for one task is a set of several independent
transactions (Coordinator.submit_task, register_task,
N×add_expected_agent, N×Agent.execute, N×submit_result), each of which
independently goes through Optimistic Democracy and can be appealed —
the same as any single IC transaction today.

## Extensibility

Adding a new agent = deploying a contract with the same interface
(`execute(task_id, task_description, capability, aggregator_address)`)
+ calling `register_self()` + calling `set_coordinator()` with the
address of whichever Coordinator should be allowed to dispatch to it.
Coordinator doesn't store a list of known capabilities and doesn't
store agent addresses — both are read fresh from Registry on every
`submit_task()`. See `agent-integration-guide.md`.
