# Fixtures (slice-3 LIGHT)

Offline only. No live channel ids, no secrets, no private host paths.

## Policy (locked for slice-3)

| Rule | Value |
|------|-------|
| Depth | **LIGHT** — prove public core contracts only |
| Contracts | classify · hard-table · deferred · kill-resume |
| Host PS parity | **Not required** — public Python is SSOT; do not couple to private host regexes |
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

- Line-by-line parity with private host PowerShell.
- Shipping live traffic dumps or private identity labels.
- Requiring an external CLI adapter in-tree (docs-only sample is enough).
