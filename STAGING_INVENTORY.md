# STAGING_INVENTORY — task-ledger (slice-3 accepted + ship-prep)

| Field | Value |
|-------|-------|
| Schema | `task_ledger.staging.inventory.v1` |
| Task | `a-opensource-slice4-prep-go-001` (extends accepted slice-3 tree) |
| Staging root | `staging/task-ledger/` (private; **not** published) |
| Public name | **task-ledger** |
| Inventory date | 2026-07-18 |

## Product files (exclude caches / egg-info)

| Path | Role |
|------|------|
| `README.md` | English quickstart + kill-then-resume + selftest + ship gate |
| `LICENSE` | Apache-2.0 |
| `NOTICE` | Apache attribution; copyright holder still TBD until owner |
| `pyproject.toml` | pip package metadata + `task-ledger` entry point (v0.1.0a3) |
| `.gitignore` | caches, venv, local ledger root |
| `docs/ARCHITECTURE.md` | public architecture |
| `docs/ENGINE_COUPLING.md` | required engine honesty disclosure |
| `docs/EXTRACTION_NOTES.md` | extract map + locked decisions |
| `docs/SLICE3_SELFTEST.md` | LIGHT selftest policy |
| `docs/SHIP_PREP.md` | owner decision table; ship-OK policy |
| `docs/EXTERNAL_CLI_ADAPTER.md` | docs-only external CLI sample (no in-tree code) |
| `scripts/sanitize_gate.py` | CI regex hard gate |
| `scripts/ship_readiness_gate.py` | ship blockers (expected RED on staging) |
| `scripts/run_sanitize_gate.ps1` | PS wrapper for gate |
| `scripts/run_offline_selftest.py` | one-shot pytest + sanitize gate |
| `src/task_ledger/**` | core package (+ `util/atomic` for crash-safe writes) |
| `adapters/powershell/*` | optional PS adapter samples |
| `adapters/filesystem/README.md` | layout notes |
| `tests/test_*.py` | smoke + contracts + atomic/ship/package surface |
| `tests/fixtures/*` | LIGHT classify/deferred/hard_table/kill_resume + policy |
| `STAGING_INVENTORY.md` | this file |
| host `scripts/Run-TaskLedgerOfflineSelftest.ps1` | host entry to offline selftest (outside package tree) |

## Explicitly not in tree

- Full chat bridge, bot tokens, live chat ids  
- Heart / control-plane daemon  
- Multi-node fleet ops language, private identity LIVE docs  
- Private machine roots / schtasks service names  
- Live evidence dumps / history samples  
- In-tree external CLI adapter implementation (docs-only)  

## Gate snapshot (re-runnable)

```text
python -m pytest tests -q
# expected: 50+ passed
python scripts/sanitize_gate.py --root .
# expected: status=GREEN hard_hits=0 soft_hits=0
python scripts/run_offline_selftest.py
# expected: PASS
python scripts/ship_readiness_gate.py --root .
# expected: status=BLOCKED (until owner ship-OK + fill-ins)
```
