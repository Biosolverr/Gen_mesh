# Key evidence — quick reference

Full raw files are included alongside this summary. This file points to the
exact lines that matter, in chronological order, so the relevant evidence
doesn't require searching through the full logs.

## 1. Environment versions (versions.txt)

Confirms this was run on a clean install, latest available CLI/backend at
the time — not a stale or misconfigured environment.

## 2. Transaction submitted and activated (stuck_transaction_receipt.json)

The transaction was signed, broadcast, and accepted onto the network
(`"status": "0x1"`). This is a real transaction, not a mock — it can be
independently verified against the same RPC endpoint.

Note: this receipt shows only L1 acceptance. It does not by itself prove
successful contract execution — see point 4 below for that.

## 3. Provider/model configuration (providers.json)

Confirms the LLM provider (Google Gemini) and model used were valid and
correctly configured — ruling out a bad API key or invalid model as the
cause of the stall.

## 4. The actual stall — validator votes never committed (gltest_run.log)

Search for `votes_committed` in gltest_run.log. Relevant excerpt:

```
"result_name": "NO_MAJORITY",
"last_round": {
  ...
  "votes_committed": "0",
  "votes_revealed": "0",
  ...
},
"status_name": "PENDING"
```

Despite the transaction being accepted (point 2), no validator ever
committed a vote on it.

## 5. Backend's own processing loop confirms the transaction was never picked up (jsonrpc_full.log)

Search for `Contracts with pending` in jsonrpc_full.log. The backend's own
transaction scheduler logged `Contracts with pending: 0` on every single
iteration, for the full ~13-minute duration of the run (21:11:39 →
21:24:25, 77 consecutive occurrences), even while the transaction sat with
status PENDING in the database:

```
2026-07-24 21:11:39 | INFO | ... [TX_MAIN] Status - Iteration: 20, Active tasks: 0, Total spawned: 0, Contracts with pending: 0
...
2026-07-24 21:24:25 | INFO | ... [TX_MAIN] Status - Iteration: 1540, Active tasks: 1, Total spawned: 1, Contracts with pending: 0
```

This confirms the stall is on the backend's own transaction queue/scheduler
— the submitted transaction was never picked up for execution, independent
of contract code, LLM provider, or validator count.

## 6. Full narrative and additional bugs found along the way (bug_log.md)

See bug_log.md for the complete write-up, including three additional
independent bugs found and worked around before reaching this final,
unresolved backend issue (provider name mismatch on init, gltest config
schema drift, undersized /dev/shm crashing the web-access subprocess).
