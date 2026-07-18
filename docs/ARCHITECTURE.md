# Architecture — task-ledger

## What it is

A **durable single-machine task core** that prevents AI agent progress hallucination:

1. **Receipt discipline** — execution orders become durable work units with a `task_id`.
2. **Hard progress** — status probes render disk facts only; no self-invented percent.
3. **Deferred promises** — "I'll check" enqueues a follow-up that cannot evaporate.
4. **Resume ledger** — long work survives process death via on-disk state.

## Layout

```text
src/task_ledger/
  classify/     # order vs status vs ack
  enqueue/      # work order + must-become-task
  progress/     # hard table
  deferred/     # detect + follow-up enqueue
  tick/         # claim/run + resume ledger
  adapters/     # filesystem / notify / engine
  ports.py      # Protocol boundaries
  cli.py        # pip entry point
adapters/
  powershell/   # optional PS examples (not required for core)
  filesystem/   # layout notes
```

## Ports

| Port | Role |
|------|------|
| `EnginePort` | Run a work unit body (fake in selftests) |
| `NotifyPort` | Optional outbound notify |
| `FollowupCompletePort` | Push when deferred work finishes |
| `ControlPlanePort` | Optional host control plane |

## Verification culture

- `code_done` ≠ `live_green`
- Self-reported percent is forbidden in hard table
- Release ladder: selftest -> owner ship-OK -> published alpha

## Out of scope

Production-specific integrations, private deployment topology, identity material, and live operational data.
