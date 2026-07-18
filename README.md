# task-ledger

**Durable single-machine task core that prevents AI agent progress hallucination.**

Receipts on disk. Facts-only progress. Deferred promises that do not evaporate. Long work that survives kill.

> **Status:** private staging (slice-3 **accepted**; ship-prep hardening). Not published.  
> **Ship gate:** closed — owner ship-OK required (slice-4). "Continue building" ≠ ship-OK.  
> **License:** Apache-2.0  
> **Language:** Python 3.10+ (PowerShell optional adapter only)

---

## Quickstart (5 lines)

```bash
pip install -e .
export TASK_LEDGER_ROOT=/tmp/demo-ledger   # Windows: $env:TASK_LEDGER_ROOT=...
task-ledger order "Fix the flaky resume path and report paths"
task-ledger tick
task-ledger table
```

You get a durable `task_id` receipt, a worker result under `outbox/`, and a hard table built from **disk facts only** (never a self-invented percent).

---

## Kill-then-resume demo

AI agents die mid-turn. The ledger must not.

```bash
task-ledger demo-resume
```

What it proves:

1. A work unit is written to `inbox/` with a receipt id.  
2. The worker claims it into `processing/` and records **running** in `resume/`.  
3. A simulated process kill marks `resume_waiting`.  
4. The next `tick` reloads instruction from the resume ledger and finishes to `outbox/`.  

No network. No API key. Scripted engine only.

---

## Offline selftest (slice-3)

```bash
python -m pytest tests -q
python scripts/sanitize_gate.py --root .
# or:
python scripts/run_offline_selftest.py
```

LIGHT contracts covered: **classify · hard-table · deferred · kill-resume**.  
See `docs/SLICE3_SELFTEST.md`.

---

## Why this exists

| Failure mode | task-ledger response |
|--------------|----------------------|
| Agent says "done" with no artifact | Work units are files + `task_id` receipts |
| Status answer invents "64%" | Hard table: queue counts + task states only |
| "I'll check later" vanishes | Deferred detect → same-turn follow-up + promise watch |
| Long job dies with the turn | Resume ledger re-entry |

**Honesty rule:** `code_done` ≠ `live_green`. Selftests green offline are not production verification.

---

## Python API

```python
from pathlib import Path
from task_ledger import classify_order, order_to_task, build_hard_table, ResumeLedger
from task_ledger.deferred import should_enqueue_deferred, enqueue_followup
from task_ledger.tick import run_once
from task_ledger.ports import FakeEngine

root = Path("/tmp/demo-ledger")

cls = classify_order("Implement resume retry")
assert cls.should_enqueue

action = order_to_task("Implement resume retry", root=root)
print(action.task_id, action.reply)

print(order_to_task("status?", root=root).reply)  # hard table, no %

dec = should_enqueue_deferred("how far?", "I'll check and report back")
if dec.should:
    enqueue_followup("how far?", "I'll check and report back", root=root)

run_once(root=root, engine=FakeEngine(body="facts from disk"))
```

---

## Layout

```text
$TASK_LEDGER_ROOT/
  inbox/  processing/  outbox/
  resume/  ledger/  flags/
  followups/  promises/
```

See `docs/ARCHITECTURE.md` and `adapters/filesystem/README.md`.

---

## Engine coupling (honest)

1. Production origin used a **CLI agent worker** as the long-job engine.  
2. Core is **engine-agnostic** (`EnginePort`).  
3. Optional CLI adapters are **samples**, not hard dependencies.  
4. Selftests use a **fake/scripted** engine (no network).  
5. Chat networks are optional `NotifyPort` adapters — **not** required runtime.  
6. External CLI wiring is **docs-only** for now (`docs/EXTERNAL_CLI_ADAPTER.md`).

Details: `docs/ENGINE_COUPLING.md`.

---

## PowerShell

Optional examples under `adapters/powershell/`. **Not required** for core install or selftests. Prefer the Python front door for new integrations.

---

## Sanitization gate

```bash
python scripts/sanitize_gate.py --root .
# or: powershell -File scripts/run_sanitize_gate.ps1
```

Hard-fails on secrets, private machine roots, private service names, live-looking chat ids.  
Public docs use **neutral technical terms** only (`operator`, `user`, `orchestrator`) — no private identity nicknames.

---

## Ship readiness gate (expected RED on staging)

```bash
python scripts/ship_readiness_gate.py --root .
```

Checks owner fill-ins before any public remote:

1. `SHIP_OK.flag` present (only after **explicit** owner ship-OK)  
2. Real Homepage URL in `pyproject.toml` (not `github.com/example/...`)  
3. `NOTICE` copyright holder not TBD  
4. `LICENSE` present  

Private staging keeps this **BLOCKED** on purpose. Details: `docs/SHIP_PREP.md`.

---

## Positioning

- **Sibling public line** (ecosystem): composes with queue/runtime and honesty-lint tools; does not re-ship them.  
- **Not included:** full chat bridge, multi-node fleet control plane, private identity docs, live traffic dumps.

---

## Slice ladder

| Slice | Deliverable | This tree |
|-------|-------------|-----------|
| 1 | Plan + inventory + sanitize checklist | done (host docs) |
| 2 | Staging modules + adapters + README + gate | done |
| 3 | Offline selftest suite (LIGHT) | **accepted** |
| 3→4 prep | Atomic IO, claim race, ship_readiness gate, NOTICE | **here (private)** |
| 4 | Public repo | only after ship-OK |

---

## Remaining for slice-4 (blocked — not opened by continue-build)

1. Owner ship-OK for public remote (explicit; create `SHIP_OK.flag` only then).  
2. Real homepage URL (placeholder still in `pyproject.toml`).  
3. Apache-2.0 copyright holder string (`NOTICE` still `COPYRIGHT_HOLDER_TBD`).  
4. A human leak-read of every shipped file.  

See `docs/SHIP_PREP.md` + `python scripts/ship_readiness_gate.py`.
