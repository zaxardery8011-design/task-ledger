# Filesystem adapter

Default layout under `$TASK_LEDGER_ROOT` (or `./.task-ledger`):

```text
inbox/         # new work units (JSON)
processing/    # claimed by tick worker
outbox/        # *.result.md + *.meta.json
ledger/        # done_task_ids.txt
resume/        # per-task resume JSON
flags/         # ORDER_OFF.flag, HARD_TABLE_OFF.flag, DEFERRED_OFF.flag
followups/     # deferred follow-up records
promises/      # promise watch files
workspace/     # engine working directory
```

No private host paths. PowerShell hosts may mirror this layout via
`adapters/powershell/TaskLedger.Queue.ps1`.
