# Fixtures (slice-3 LIGHT)

Offline only. No live channel ids, no secrets, no deployment-specific paths.

## Policy (locked for slice-3)

| Rule | Value |
|------|-------|
| Depth | **LIGHT** — prove public core contracts only |
| Contracts | classify · hard-table · deferred · kill-resume |
| Host parity | **Not required** - public Python is SSOT; do not couple to deployment regexes |
| Engine | Fake / Scripted only (no network, no API keys) |
| Ids | `demo-task-*`, `followup-*`, `task-*` |
| Channel fixtures | `111111111` style only if needed |

## Files

| File | Contract |
|------|----------|
| `classify_vectors.json` | order classification kinds + enqueue flag |
| `deferred_vectors.json` | deferred promise detect + should-enqueue |
| `hard_table_vectors.json` | facts-only queue counts + flag-off + no `%` |
| `kill_resume_scenario.json` | kill → resume_waiting → outbox done |

## Anti-goals

- Line-by-line parity with production host automation.
- Shipping live operational data or private identity labels.
- Requiring an external CLI adapter in-tree (docs-only sample is enough).
