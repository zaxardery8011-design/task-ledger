# Extraction notes — task-ledger

| Field | Value |
|-------|-------|
| Package public name | **task-ledger** |
| Repository state | Published alpha |
| License | Apache-2.0 |
| Current slice | **4 published alpha** |
| Tasks | slice-2/3 extraction done; slice-4 release checks present |

## Naming

Former working name `task-core` was dropped: PyPI already has a third-party `task-core` (v0.2.1).
Public name **task-ledger** is free on PyPI/npm at decision time; GitHub exact-name collisions were only 0-star practice repos. Ledger metaphor matches receipts + resume + facts-only progress.

**Name lock (slice-3):** A confirmed **task-ledger** unchanged.

## What was extracted (substance)

| Substance | Module |
|-----------|--------|
| order → task + receipt | `enqueue/must_become_task.py`, `enqueue/work_order.py` |
| classify | `classify/order_class.py` |
| progress hard table | `progress/hard_table.py` |
| deferred no-evaporate | `deferred/detect.py`, `deferred/enqueue.py` |
| tick + resume | `tick/worker.py`, `tick/resume_ledger.py` |
| ports | `ports.py`, `adapters/*` |

Design-origin mapping (production system de-identified; **not** copied wholesale):

| Extracted behavior | Public surface |
|--------------------|----------------|
| Order classification + durable receipt flow | `classify/`, `enqueue/` |
| Facts-only progress summary | `progress/hard_table.py` |
| Deferred follow-up persistence | `deferred/` |
| Long-job resume loop | `tick/` (engine behind port) |
| Production-specific integrations and control services | **out of package** |

## Sanitization applied

- No private machine roots (host-absolute paths rewritten to `$Root` / `TASK_LEDGER_ROOT`)
- No credentials, live channel ids, or internal service names
- **Public-line lexicon (locked):** neutral technical terms only — `orchestrator`, `operator`, `user`, `owner`. Never private operator nicknames or fleet brain-facing labels in README, comments, or commit-facing prose.
- Queue names: `inbox` / `processing` / `outbox`
- Kill flags: `ORDER_OFF`, `HARD_TABLE_OFF`, `DEFERRED_OFF`
- Example task ids: `task-*`, `followup-*`, `demo-task-001`
- Hard gate: `scripts/sanitize_gate.py` (must stay GREEN)

## Conflict report (Python-first vs PS core)

**Guideline:** Python is the front door; PowerShell is optional adapter.

**Reality:** The production origin uses additional private orchestration outside this package. This package **did not** port deployment scripts wholesale into Python.

**Resolution:**

- Pure algorithms + durable ledger contracts → Python package (pip surface).
- Thin PS samples under `adapters/powershell/` for hosts that call PS.
- Production-specific orchestration and integrations remain **out of package**.
- **Slice-3:** public Python is SSOT; **no** dual-run host-PS parity matrix.

## Extraction and selftest baseline

- LIGHT fixtures: `classify_vectors.json`, `deferred_vectors.json`, `hard_table_vectors.json`, `kill_resume_scenario.json`
- Contract tests: classify / hard-table / deferred / kill-resume
- Offline pipeline: `tests/test_offline_selftest.py`
- One-shot: `scripts/run_offline_selftest.py` (+ host `scripts/Run-TaskLedgerOfflineSelftest.ps1`)
- Policy: `docs/SLICE3_SELFTEST.md`
- External CLI adapter: **docs-only** `docs/EXTERNAL_CLI_ADAPTER.md`
- Lexicon lock: neutral technical terms only on public-line

## Release hardening after selftest accept

- Atomic text writes for resume / work-order / outbox (`util/atomic.py`)
- Claim path race tolerance (skip lost moves; do not crash tick)
- `scripts/ship_readiness_gate.py` — expected **READY** for this tree
- `NOTICE` + `docs/SHIP_PREP.md` — release attribution and readiness policy
- Package surface tests + version **0.1.0a3**

## Post-alpha candidates

- Remote CI packaging checks
- PyPI publishing workflow
- Additional adapter examples when a concrete integration need exists
- Human leak-read before each public release change

---

## Decisions locked (slice-3 answers from A)

| # | Topic | Decision |
|---|-------|----------|
| 1 | Name | **task-ledger** final for PyPI + GitHub intent (owner may still rename only before first public remote) |
| 2 | Soft lexicon | **NO** private nicknames on public-line; neutral technical terms only |
| 3 | Fixture depth | **LIGHT** — public contracts only; not host-PS line parity |
| 4 | External CLI sample | **docs-only first**; no in-tree sample adapter unless concrete need |
| 5 | Homepage URL | public repository URL |
| 6 | Apache copyright string | `Task-Ledger Contributors` |
