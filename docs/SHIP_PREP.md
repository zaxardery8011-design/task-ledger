# Ship prep — owner decisions still open (private staging)

| Field | Value |
|-------|-------|
| Schema | `task_ledger.ship_prep.v1` |
| Package | **task-ledger** |
| Staging | private only — **not published** |
| Slice-4 | **blocked** until explicit owner ship-OK |
| Related task | continue-build after slice-3 accept (`a-opensource-slice4-prep-go-001`) |

## Policy (hard)

- Slice-3 offline selftest green ≠ permission to open a public remote.
- Operator **"continue building"** authorizes **private staging work only**.
- It is **not** ship-OK. Ship-OK must be an explicit, unambiguous instruction
  (relayed via the dispatch channel), separate from keep-building language.
- Automated gate: `scripts/ship_readiness_gate.py` — **expected RED** on this tree
  until the owner decisions below land **and** `SHIP_OK.flag` exists.

## Owner decision table

| # | Decision | Current | Who fills | Where |
|---|----------|---------|-----------|-------|
| 1 | Explicit ship-OK | **missing** | owner | create `SHIP_OK.flag` (one line + date) only after verbatim ship-OK |
| 2 | Public homepage URL | placeholder `https://github.com/example/task-ledger` | owner | `pyproject.toml` → `[project.urls] Homepage` |
| 3 | Apache-2.0 copyright holder string | `COPYRIGHT_HOLDER_TBD` | owner | `NOTICE` + LICENSE appendix line if desired |
| 4 | Human leak-read of every shipped file | open | A / owner designee | spot-check vs `SANITIZATION_CHECKLIST.md` |

## Commands

```bash
# Private staging daily gates (must stay GREEN):
python -m pytest tests -q
python scripts/sanitize_gate.py --root .
python scripts/run_offline_selftest.py

# Ship gate (expected BLOCKED / FAIL until owner decisions):
python scripts/ship_readiness_gate.py --root .
python scripts/ship_readiness_gate.py --root . --json
```

## What is already ready (no ship claim)

- Core contracts: classify / hard-table / deferred / kill-resume (LIGHT)
- Sanitize hard gate GREEN on private tree
- Atomic resume + work-order writes (crash mid-write hardening)
- Claim path tolerates concurrent move races (skip + continue)
- Package surface tests (required files, version consistency)
- Engine honesty disclosure + neutral public-line lexicon lock

## Explicit non-actions (this prep slice)

- No public remote, no `git push` to public, no PyPI upload
- No inventing a real org homepage or copyright legal name
- No creating `SHIP_OK.flag` without owner ship-OK
- No changing live host bridge / heart / secrets

## Ladder reminder

```text
private staging → offline selftest (slice-3, accepted)
               → ship prep (this doc; private continue-build)
               → owner ship-OK + fill-ins → ship_readiness GREEN
               → then slice-4 publish steps
```

`code_done` ≠ `live_green` ≠ `ship_ok`.
