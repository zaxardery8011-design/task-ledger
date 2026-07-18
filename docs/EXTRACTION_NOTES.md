# Extraction notes — task-ledger

| Field | Value |
|-------|-------|
| Package public name | **task-ledger** |
| Staging path | `staging/task-ledger/` (private only — not published) |
| License | Apache-2.0 |
| Current slice | **3 accepted** + **private ship-prep** (atomic IO, ship_readiness gate) |
| Tasks | slice-2/3 done · continue-build `a-opensource-slice4-prep-go-001` (not ship) |

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

Private host mapping (source of algorithms; **not** copied wholesale):

| Private host (not shipped) | Public surface |
|----------------------------|----------------|
| Host dialogue classify + must-become-task | `classify/`, `enqueue/` |
| Host progress hard table | `progress/hard_table.py` |
| Host deferred follow-up link | `deferred/` |
| Host tick / long-job resume | `tick/` (engine behind port) |
| Full chat bridge, heart control plane | **out of package** |

## Sanitization applied

- No private machine roots (host-absolute paths rewritten to `$Root` / `TASK_LEDGER_ROOT`)
- No bot tokens / live chat ids / schtask service names
- **Public-line lexicon (locked):** neutral technical terms only — `orchestrator`, `operator`, `user`, `owner`. Never private operator nicknames or fleet brain-facing labels in README, comments, or commit-facing prose.
- Queue names: `inbox` / `processing` / `outbox`
- Kill flags: `ORDER_OFF`, `HARD_TABLE_OFF`, `DEFERRED_OFF`
- Example task ids: `task-*`, `followup-*`, `demo-task-001`
- Hard gate: `scripts/sanitize_gate.py` (must stay GREEN)

## Conflict report (Python-first vs PS core)

**Guideline:** Python is the front door; PowerShell is optional adapter.

**Reality:** Production hosts may still run large PS orchestration for chat ingress, tick services, and worker launch. This package **did not** port those host scripts wholesale into Python.

**Resolution:**

- Pure algorithms + durable ledger contracts → Python package (pip surface).
- Thin PS samples under `adapters/powershell/` for hosts that call PS.
- Full host bridge / control plane remain **out of package**.
- **Slice-3:** public Python is SSOT; **no** dual-run host-PS parity matrix.

## Slice-3 (done under private staging)

- LIGHT fixtures: `classify_vectors.json`, `deferred_vectors.json`, `hard_table_vectors.json`, `kill_resume_scenario.json`
- Contract tests: classify / hard-table / deferred / kill-resume
- Offline pipeline: `tests/test_offline_selftest.py`
- One-shot: `scripts/run_offline_selftest.py` (+ host `scripts/Run-TaskLedgerOfflineSelftest.ps1`)
- Policy: `docs/SLICE3_SELFTEST.md`
- External CLI adapter: **docs-only** `docs/EXTERNAL_CLI_ADAPTER.md`
- Lexicon lock: neutral technical terms only on public-line

## Private continue-build after slice-3 accept (not ship)

- Atomic text writes for resume / work-order / outbox (`util/atomic.py`)
- Claim path race tolerance (skip lost moves; do not crash tick)
- `scripts/ship_readiness_gate.py` — expected **BLOCKED** until owner fill-ins
- `NOTICE` + `docs/SHIP_PREP.md` — homepage + copyright TBD still explicit
- Package surface tests + version **0.1.0a3**

## Not done (slice-4 — blocked)

- **Slice-4:** public repo + CI on remote — **owner ship-OK only** (do not skip ladder)
- Homepage URL real org (placeholder remains until ship-OK)
- Apache-2.0 copyright holder string for public NOTICE history
- Creating `SHIP_OK.flag` without explicit owner ship-OK is **forbidden**

---

## Decisions locked (slice-3 answers from A)

| # | Topic | Decision |
|---|-------|----------|
| 1 | Name | **task-ledger** final for PyPI + GitHub intent (owner may still rename only before first public remote) |
| 2 | Soft lexicon | **NO** private nicknames on public-line; neutral technical terms only |
| 3 | Fixture depth | **LIGHT** — public contracts only; not host-PS line parity |
| 4 | External CLI sample | **docs-only first**; no in-tree sample adapter unless concrete need |
| 5 | Homepage URL | still placeholder until ship-OK |
| 6 | Apache copyright string | still TBD for public history |
