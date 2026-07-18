# External CLI adapter — docs-only sample

| Field | Value |
|-------|-------|
| Status | **docs-only** (slice-3 lock) |
| In-tree adapter code | **No** — keep public surface minimal |
| When to promote | Only if a concrete near-term need appears after ship-OK |

Selftests and demos use `FakeEngine` / `ScriptedEngine` under `task_ledger.ports` and
`task_ledger.adapters.engine`. An external CLI agent is **not** required to install
or test this package.

## Port contract

```python
from pathlib import Path
from typing import Any
from task_ledger.ports import EnginePort, WorkUnit

class ExternalCliEngine:
    """Illustrative sketch — do not treat as shipped production code.

    Wire your own process runner. Never hard-code private host paths or secrets.
    """

    def __init__(self, binary: str = "agent-cli") -> None:
        self.binary = binary

    def run(self, unit: WorkUnit, work_dir: Path) -> dict[str, Any]:
        # Pseudocode only:
        #   subprocess.run([self.binary, "run", "--task", unit.task_id,
        #                   "--work-dir", str(work_dir)], check=False)
        #   read artifacts from work_dir; return ok/status/result
        return {
            "ok": True,
            "task_id": unit.task_id,
            "status": "PASS",
            "result": f"external-cli sketch for {unit.task_id}",
        }

# Structural note: ExternalCliEngine satisfies EnginePort if it implements run().
_engine: EnginePort  # type: ignore[assignment]
```

## Rules for any real adapter (host-side)

1. No network inside core; adapter owns I/O.  
2. No secrets in package tree — env vars only on the host.  
3. Map results into `{ok, status, result}` so resume ledger stays honest.  
4. Do not import private host bridge / control-plane modules into the public package.

## Why docs-only first

Slice-3 decision: keep the initial public surface minimal. Optional in-tree samples
under `adapters/engine/` can wait until there is a concrete integration need and
owner ship-OK for broader packaging.
