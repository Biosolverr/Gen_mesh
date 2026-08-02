## Transactions in One Run

| # | Contract | Method | Type | Trigger |
|---|---|---|---|---|
| 1 | Coordinator | `submit_task` | non-det | user |
| 2 | Aggregator | `register_task` | det | `emit()` from tx 1 |
| 3 | Aggregator | `add_expected_agent` ×N (task_id, agent_address, capability) | det | `emit()` from tx 1 |
| 4 | SecurityAgent | `execute` | non-det | `emit()` from tx 1 (sender-checked: must be SecurityAgent's bound Coordinator) |
| 5 | FinanceAgent | `execute` | non-det | `emit()` from tx 1 (sender-checked: must be FinanceAgent's bound Coordinator) |
| 6 | Aggregator | `submit_result` (Security) | det | `emit()` from tx 4 |
| 7 | Aggregator | `submit_result` (Finance) | det | `emit()` from tx 5, triggers `_finalize` |

**The order of 2–3 relative to 4–5 is guaranteed by the code, not
incidental.** `Coordinator.submit_task` fully registers the manifest
first (steps 2–3), and only then dispatches tasks to agents (steps
4–5) — a task can never exist in Aggregator later than the first agent
is able to report on it.

**Steps 4–5 additionally require the caller to be each Agent's bound
Coordinator.** Prior to this check, any external caller could invoke
step 4 or 5 directly — outside this transaction chain entirely — with
its own fabricated task content, and because step 6/7's dedup is keyed
on `(task_id, sender address)`, that forged submission would silently
win over the real one this chain produces. The check does not change
the ordering guarantee above; it removes an entirely separate entry
point that bypassed steps 1–3 altogether.

The order of 4–5 relative to each other, and 6–7 relative to each
other, is not guaranteed (agents run in parallel) — which is why
Aggregator counts completion by `len(submissions) >= expected_count`,
not by a specific arrival order.

## One-Time Bootstrap (Before Any Task)

Before the transaction chain above can run at all, two binding steps
must complete once, after deployment:

| Step | Contract | Method | Restriction |
|---|---|---|---|
| A | Aggregator | `set_coordinator` | owner only |
| B×N | each Agent | `set_coordinator` | owner only, per agent |

Until step A runs, `register_task`/`add_expected_agent` reject every
caller (`coordinator_address` defaults to the zero address). Until step
B runs for a given agent, that agent's `execute()` rejects every caller,
including the legitimate Coordinator it will eventually be bound to.

## Idempotency

An `emit(on='accepted')` message can be re-sent on appeal (up to ~6
times). This project uses `on='finalized'` everywhere, which removes
the need for complex idempotency on intermediate steps, but
`Aggregator.submit_result` still deduplicates by `agent_address` (taken
from the sender, see below) — in case some future path switches to
`accepted` for lower latency. This same dedup is what made the
now-fixed `execute()` gap in step 4/5 exploitable: a forged submission
arriving before the legitimate one would occupy that dedup slot first.

## Trust Boundaries

1. **`execute()` accepts calls only from the Agent's bound
   Coordinator.** There is no whitelist of trusted callers, no per-task
   authorization — just one stored address, set once via
   `set_coordinator()` by the Agent's owner. This is checked before any
   other logic runs, including the capability check, so a rejected
   caller never reaches the LLM call or Aggregator at all.
2. **`submit_result` identity comes from the transaction sender, not a
   parameter.** There is no `agent_address` argument in the method
   signature — a caller has nothing to set to a value other than their
   own address, so there's nothing to forge.
3. **`submit_result`'s `capability` argument is checked against a
   stored commitment, not trusted at face value.** Aggregator records,
   per `(task_id, agent_address)`, exactly which capability Coordinator
   registered for that agent via `add_expected_agent`. A submission
   whose `capability` doesn't match that stored value is rejected,
   independent of whether the sender itself is legitimate — this
   prevents a submission from being counted toward, or reported as, a
   capability the sender was never actually assigned for that task.
4. **`register_task`/`add_expected_agent` are restricted to a single
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
Uploading message-flow.md…]()
