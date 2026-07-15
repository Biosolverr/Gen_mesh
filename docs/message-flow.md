# Message Flow & Consensus Integration

> **Updated after review (2026-07-05).** A reviewer found four real
> holes in this chain: `submit_result` didn't authenticate the sender,
> anyone could modify a task manifest, there was a race condition in
> emit ordering, and we didn't have a clean e2e run without manual
> re-sends. All four are fixed — details below. The old version of this
> section incorrectly called issue #2 "a deliberate MVP simplification,"
> when it was actually an access-control hole. The wording has been
> corrected.

## Transactions in One Run (current order)

| # | Contract | Method | Type | Trigger |
|---|---|---|---|---|
| 1 | Coordinator | `submit_task` | non-det | user |
| 2 | Aggregator | `register_task` | det | `emit()` from tx 1 |
| 3 | Aggregator | `add_expected_agent` ×N | det | `emit()` from tx 1 |
| 4 | SecurityAgent | `execute` | non-det | `emit()` from tx 1 |
| 5 | FinanceAgent | `execute` | non-det | `emit()` from tx 1 |
| 6 | Aggregator | `submit_result` (Security) | det | `emit()` from tx 4 |
| 7 | Aggregator | `submit_result` (Finance) | det | `emit()` from tx 5, triggers `_finalize` |

**The order of 2–3 relative to 4–5 is no longer incidental — it's
guaranteed by the code.** Coordinator used to dispatch `execute()` to
agents first and only register the manifest in Aggregator afterward.
That was a race: if an agent finished faster than
`register_task`/`add_expected_agent` reached Aggregator, its
`submit_result` would fail with `"Unknown task_id"` — which is exactly
what happened in our manual studionet tests, where an agent's
`execute()` had to be manually re-sent (documented as "manual
re-invocation" in `test/manual-runs/e2e_full_mesh_run.json`). Now
`Coordinator.submit_task` fully registers the manifest first (steps
2–3), and only then dispatches tasks to agents (steps 4–5) — so a task
can never exist in Aggregator later than the first agent is able to
report on it.

The order of 4–5 relative to each other, and 6–7 relative to each
other, is still not guaranteed (agents run in parallel) — which is why
Aggregator counts completion by `len(submissions) >= expected_count`,
not by a specific arrival order.

## Idempotency

An `emit(on='accepted')` message can be re-sent on appeal (up to ~6
times). This project uses `on='finalized'` everywhere, which removes
the need for complex idempotency on intermediate steps, but
`Aggregator.submit_result` still deduplicates by `agent_address` (taken
from the sender, see below) — in case some future path switches to
`accepted` for lower latency.

## Trust Boundaries (fixed after review)

This section used to describe two real access-control failures,
incorrectly framed as "deliberate MVP simplifications":

1. **`submit_result` didn't verify who actually called it.**
   `agent_address` was a plain string parameter — the caller specified
   it themselves, and the contract took it on faith. Any address could
   impersonate any agent and write an arbitrary verdict into Aggregator.
   **Fixed:** identity now comes only from `gl.message.sender_address`;
   the `agent_address` parameter is gone from the signature entirely —
   it can't be forged because it no longer exists as input.

2. **`register_task`/`add_expected_agent` were open to anyone.** Any
   address could register an arbitrary `task_id` or append an extra
   "expected" agent to someone else's manifest.
   **Fixed:** added a `coordinator_address` field and a
   `set_coordinator()` method (called once by Aggregator's owner after
   Coordinator is deployed — a two-step bootstrap, because Coordinator
   and Aggregator have a circular dependency on each other's address).
   Both methods now require `gl.message.sender_address ==
   self.coordinator_address`.

## Why No Separate "Mesh Consensus" Is Needed

No new consensus mechanism was created. Two existing GenVM modes are
used:

- strict deterministic validation (for `register_task` and
  conflict-free `submit_result`);
- the standard Equivalence Principle (`gl.eq_principle.prompt_comparative`)
  — the same mechanism Coordinator uses for capability matching and
  each Agent uses for domain inference — applied again at the
  Aggregator level when a genuine disagreement arises.
