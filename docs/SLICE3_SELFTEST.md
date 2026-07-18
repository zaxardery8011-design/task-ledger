# Slice-3 offline selftest (LIGHT)

| Field | Value |
|-------|-------|
| Schema | `task_ledger.slice3.selftest.v1` |
| Package | **task-ledger** |
| Staging | private only — not published |
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
cd staging/task-ledger   # or this package root
python -m pytest tests -q
python scripts/sanitize_gate.py --root .
# or one shot:
python scripts/run_offline_selftest.py
# host wrapper (from host root):
# powershell -File scripts/Run-TaskLedgerOfflineSelftest.ps1
```

## Explicit non-goals

- Line-by-line parity with private host PowerShell classify/deferred regexes.  
- Live chat, secrets, multi-node fleet language.  
- In-tree external CLI adapter (see `EXTERNAL_CLI_ADAPTER.md` docs-only).  
- Public remote / PyPI publish (slice-4 + owner ship-OK only).

## Honesty

`code_done` on this suite ≠ `live_green` on a production host. Slice-3 only claims
offline contract green on the private staging tree.
