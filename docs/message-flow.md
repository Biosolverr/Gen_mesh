# Message Flow & Consensus Integration

## Transactions in One Run

| # | Contract | Method | Type | Trigger |
|---|---|---|---|---|
| 1 | Coordinator | `submit_task` | non-det | user |
| 2 | Aggregator | `register_task` | det | `emit()` from tx 1 |
| 3 | Aggregator | `add_expected_agent` ×N | det | `emit()` from tx 1 |
| 4 | SecurityAgent | `execute` | non-det | `emit()` from tx 1 |
| 5 | FinanceAgent | `execute` | non-det | `emit()` from tx 1 |
| 6 | Aggregator | `submit_result` (Security) | det | `emit()` from tx 4 |
| 7 | Aggregator | `submit_result` (Finance) | det | `emit()` from tx 5, triggers `_finalize` |

**The order of 2–3 relative to 4–5 is guaranteed by the code, not
incidental.** `Coordinator.submit_task` fully registers the manifest
first (steps 2–3), and only then dispatches tasks to agents (steps
4–5) — a task can never exist in Aggregator later than the first agent
is able to report on it.

The order of 4–5 relative to each other, and 6–7 relative to each
other, is not guaranteed (agents run in parallel) — which is why
Aggregator counts completion by `len(submissions) >= expected_count`,
not by a specific arrival order.

## Idempotency

An `emit(on='accepted')` message can be re-sent on appeal (up to ~6
times). This project uses `on='finalized'` everywhere, which removes
the need for complex idempotency on intermediate steps, but
`Aggregator.submit_result` still deduplicates by `agent_address` (taken
from the sender, see below) — in case some future path switches to
`accepted` for lower latency.

## Trust Boundaries

1. **`submit_result` identity comes from the transaction sender, not a
   parameter.** There is no `agent_address` argument in the method
   signature — a caller has nothing to set to a value other than their
   own address, so there's nothing to forge.

2. **`register_task`/`add_expected_agent` are restricted to a single
   bound Coordinator.** Aggregator stores a `coordinator_address`, set
   once by its owner via `set_coordinator()` after Coordinator is
   deployed — a two-step bootstrap, since Coordinator and Aggregator
   reference each other's address and can't both be constructed with
   the other's address available at the same deploy step. Both methods
   require `gl.message.sender_address == self.coordinator_address`.

## Why No Separate "Mesh Consensus" Is Needed

No new consensus mechanism was created. Two existing GenVM modes are
used:

- strict deterministic validation (for `register_task` and
  conflict-free `submit_result`);
- the standard Equivalence Principle (`gl.eq_principle.prompt_comparative`)
  — the same mechanism Coordinator uses for capability matching and
  each Agent uses for domain inference — applied again at the
  Aggregator level when a genuine disagreement arises.
