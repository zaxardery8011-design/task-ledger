# Slice-3 offline selftest (LIGHT)

| Field | Value |
|-------|-------|
| Schema | `task_ledger.slice3.selftest.v1` |
| Package | **task-ledger** |
| Repository state | Published alpha |
| Depth | **LIGHT** (locked) |

## Goal

Prove the **public core contracts** run offline on a clean temp root with a
scripted/fake engine:

| Contract | What green means |
|----------|------------------|
| **classify** | Fixture vectors → expected kind + `should_enqueue` |
| **hard-table** | Queue counts from disk; **no** fabricated `N%` |
| **deferred** | Promise detect + follow-up/promise files on disk |
| **kill-resume** | Claim → `resume_waiting` → next tick finishes outbox |

## How to run

```bash
cd path/to/task-ledger
python -m pytest tests -q
python scripts/sanitize_gate.py --root .
# or one shot:
python scripts/run_offline_selftest.py
# host wrapper (from host root):
# powershell -File scripts/Run-TaskLedgerOfflineSelftest.ps1
```

## Explicit non-goals

- Line-by-line parity with production host automation.  
- Live channels, secrets, or private deployment topology language.  
- In-tree external CLI adapter (see `EXTERNAL_CLI_ADAPTER.md` docs-only).  
- PyPI publish workflow.

## Honesty

`code_done` on this suite != `live_green` on a production host. This suite only
claims offline contract green on the package tree.
