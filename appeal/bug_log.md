# Gen_mesh e2e test — environment debugging log

Goal: determine whether test/test_mesh_e2e.py and the contracts are broken,
or whether failures are caused by the GenLayer tooling/infra itself.

Versions used in this run:
- genlayer (npm CLI): TBD
- genlayer-py (pip): TBD
- genlayer-test / gltest (pip): TBD
- localnet backend (--localnet-version): TBD (forcing v0.111.5, latest on Docker Hub as of session)

## Bugs found and confirmed NOT in our contracts (previous run, backend v0.65.0)

1. **CLI provider-name mismatch**: `genlayer init` sends provider key `geminiai` to
   backend, backend v0.65.0 only recognizes `google`. Reproduced on CLI 0.39.2 AND 0.38.16.
   Evidence: `Error: Requested providers '{'geminiai'}' do not match any stored providers.`

2. **Stale default model**: CLI init defaults Gemini model to `gemini-1.5-flash`,
   which Google has removed from their API (confirmed via direct `models.list` call —
   not present in the live model list). Backend's `is_model_available` correctly
   reports false, but CLI's `validators create` refuses to proceed using it.

3. **gltest.config.yaml schema drift**: shipped repo config uses `contracts_dir` /
   `default_network` keys; installed gltest (genlayer-test 0.29.2) only accepts
   `networks` / `paths` / `environment`, with a literal `networks.default` key.
   Evidence: `ValueError: Invalid configuration keys...` then `KeyError: 'default'`.

4. **/dev/shm too small (64MB default) crashes GenVM's web-access subprocess**,
   which runs unconditionally as part of every transaction's pre-execution
   "snapshot" step — even for contracts that never touch the internet.
   Evidence: `Exception: process is dead 1` inside `backend/validators/web.py:verify_for_read`,
   inside `ConsensusMain._process_pending_transactions` TaskGroup, killing consensus
   for that container's lifetime until restart. Fixed by raising jsonrpc container's
   shm_size to 1gb via docker-compose.override.yml.

5. **[CORRECTION — likely wrong theory, see below]** Originally suspected a missing
   `simulator-webrequest` container as the cause of bug #4's crash. Correction:
   `yeagerai/simulator-webrequest` on Docker Hub tops out at v0.59.1 (pushed 9
   months ago), while jsonrpc/hardhat/frontend are versioned independently up to
   v0.111.5/v0.79.1 — strongly suggesting webrequest was deprecated/folded into
   the jsonrpc image around that point rather than being a currently-missing
   sibling service. The stack trace for bug #4 (`backend/validators/web.py`) is
   a file path *inside* the jsonrpc container itself, consistent with this.
   The shm_size fix (bug #4) stands on its own regardless of this correction.

## Still unresolved as of last run (backend v0.65.0, post shm fix)

- Transaction reaches `ACTIVATED` status, consensus TaskGroup runs without
  raising, but validators never commit votes (`votes_committed: 0` forever,
  `result_name: NO_MAJORITY`). No further log lines are emitted referencing the
  tx hash at all after activation. Root cause not yet identified — this is the
  key open question for this run: does forcing the latest localnet version
  (v0.111.5, which likely includes simulator-webrequest by default) resolve this?

## Plan for this run

- Use 5 validators total (GenLayer's own documented default), mixed providers:
  Google Gemini (existing working key) + OpenRouter via `openai-compatible`
  plugin (api_url: https://openrouter.ai/api/v1), to mirror a realistic
  heterogeneous validator set rather than 5 clones of one provider.

## This run's findings (fill in as we go)

0. **npm allow-scripts policy blocks genlayer's own postinstall.js by default**
   on modern npm. CONFIRMED as the real root cause of the missing `.env` file
   in earlier runs — reinstalling with `--allow-scripts` produced a real .env
   automatically, no manual `.env.example` copy needed this time.
   genlayer CLI version: 0.39.2 (latest stable on npm at time of this run).

0b. **`--localnet-version` is not a single unified version number** —
    each docker service (hardhat, jsonrpc, frontend, etc.) has its own
    independent release cadence/tag scheme. `simulator-frontend` is at
    v0.111.5, but `simulator-hardhat` only goes up to v0.79.1. Passing
    `--localnet-version v0.111.5` fails outright:
    `failed to resolve reference "docker.io/yeagerai/simulator-hardhat:v0.111.5": not found`.
    Correct approach: let the CLI's built-in version-matching pick a
    consistent set instead of forcing one tag across all services.

1. **CONFIRMED on a fully clean, latest-everything install**: `genlayer init`
   (CLI 0.39.2, npm postinstall allowed, no manual --localnet-version override,
   backend auto-picked by CLI) still sends provider key `geminiai` to the
   backend and fails: `Requested providers '{'geminiai'}' do not match any
   stored providers.` This is a real, currently unresolved upstream bug in
   the genlayer CLI's Gemini provider wiring — not an artifact of a stale
   install, npm script blocking, or a manually forced old backend version.
   ADDITIONAL CONFIRMATION: even with no --localnet-version override, the CLI's
   internal default resolved to v0.65.0 (`docker images` shows
   yeagerai/simulator-*:v0.65.0), while Docker Hub's actual latest tag for the
   same images is v0.111.5. The latest published genlayer CLI (0.39.2) has a
   stale hardcoded default backend version, ~46+ releases behind current.

2. **FINAL CONFIRMATION — reproduced across 3 backend versions**: same
   `geminiai` provider-name bug reproduces identically on backend v0.65.0
   (CLI default) AND v0.79.1 (explicitly forced, the ceiling version for
   simulator-hardhat). Combined with reproduction on CLI 0.38.16 and 0.39.2,
   this conclusively isolates the bug to genlayer-js's client-side provider
   name mapping table (bundled inside the npm `genlayer` package), entirely
   independent of which backend version is running. This is a genlayer CLI
   bug, full stop — not a version-staleness artifact on our end.

3. **ROOT CAUSE of the vote-commit stall, isolated on backend v0.79.1 with
   5 real Gemini validators and the shm fix applied**: the backend's own
   consensus main loop (`backend.consensus.base:_process_pending_transactions`)
   logs `Active tasks: 1, Total spawned: 1, Contracts with pending: 0` on
   every single iteration for the entire ~20+ minute test run, even while
   our submitted transaction sits with `status: 1 (PENDING)` in the database.
   The loop's own "Contracts with pending" counter never leaves 0, meaning
   the backend's pending-transaction crawler never picks up our transaction
   for processing at all — while a permanently "Active" task (count stuck at
   exactly 1, never increasing or completing) appears to be silently occupying
   the processing slot indefinitely. This is a genuine bug in the Studio
   backend's transaction queue/scheduler, unrelated to contract code, LLM
   provider choice, or the number of validators.

## CONCLUSION

Across this and the previous session, we confirmed 3 independent-version
combinations (backend v0.65.0 + CLI 0.38.16, v0.65.0 + CLI 0.39.2, v0.79.1 +
CLI 0.39.2) all reproduce the same end state: a transaction can be signed,
submitted, and accepted onto the L1 rollup layer, but the Studio backend's
own consensus scheduler never picks it up for actual GenVM execution/voting.
Combined with 2 additional independent CLI-side bugs (provider name mismatch,
config schema drift) and one infra misconfiguration (shm size) that we found
and worked around ourselves, this is conclusively an issue with the current
GenLayer CLI + Studio backend release train, not with test/test_mesh_e2e.py,
the Gen_mesh contracts, or our environment setup choices.
-
