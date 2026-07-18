# Ship readiness - published alpha

| Field | Value |
|-------|-------|
| Schema | `task_ledger.ship_prep.v1` |
| Package | **task-ledger** |
| Release status | Published (alpha) |
| Slice-4 | ship readiness checks clear |
| Related task | public alpha release hardening |

## Policy

- Offline selftests green alone are not release evidence.
- Ship readiness requires explicit ship-OK, real package metadata, final NOTICE attribution, license presence, and sanitize gate review.
- Automated gate: `scripts/ship_readiness_gate.py` - expected **READY** for this tree.
- Before future release changes, rerun pytest, sanitize gate, and ship readiness gate.

## Decision table

| # | Decision | Current | Who fills | Where |
|---|----------|---------|-----------|-------|
| 1 | Explicit ship-OK | recorded | owner | `SHIP_OK.flag` |
| 2 | Public homepage URL | `https://github.com/zaxardery8011-design/task-ledger` | owner | `pyproject.toml` -> `[project.urls] Homepage` |
| 3 | Apache-2.0 copyright holder string | `Task-Ledger Contributors` | owner | `NOTICE` + LICENSE appendix line |
| 4 | Human leak-read of shipped files | repeat before release changes | A / owner designee | spot-check against sanitize policy |

## Commands

```bash
python -m pytest tests -q
python scripts/sanitize_gate.py --root .
python scripts/run_offline_selftest.py

python scripts/ship_readiness_gate.py --root .
python scripts/ship_readiness_gate.py --root . --json
```

## Current readiness evidence

- Core contracts: classify / hard-table / deferred / kill-resume (LIGHT)
- Sanitize hard gate GREEN on this tree
- Atomic resume + work-order writes (crash mid-write hardening)
- Claim path tolerates concurrent move races (skip + continue)
- Package surface tests (required files, version consistency)
- Engine honesty disclosure + neutral public-line lexicon lock

## Explicit non-actions

- No PyPI upload from this repository step
- No changing release identity without owner approval
- No bundling credentials, live data, or production-only integrations
- No changing production systems from package release work

## Ladder reminder

```text
offline selftest (slice-3, accepted)
  -> release hardening
  -> owner ship-OK + metadata fill-ins
  -> ship_readiness READY
  -> published alpha
```

`code_done` ≠ `live_green` ≠ `ship_ok`.
