"""Engine adapters.

Honest coupling disclosure:
- Production origin used an external CLI agent as worker engine.
- Core is engine-agnostic via EnginePort.
- Optional external-CLI adapters are samples, not hard dependencies.
- Selftests use ScriptedEngine / FakeEngine (no network, no API keys).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from task_ledger.ports import WorkUnit


class ScriptedEngine:
    """Deterministic engine for demos and CI (no network)."""

    def __init__(self, responses: dict[str, str] | None = None) -> None:
        self.responses = responses or {}
        self.default = (
            "Looked up facts from local ledger dirs.\n"
            "No self-invented percent. Receipts remain on disk."
        )

    def run(self, unit: WorkUnit, work_dir: Path) -> dict[str, Any]:
        body = self.responses.get(unit.task_id, self.default)
        result_file = Path(work_dir) / f"{unit.task_id}.worker.txt"
        result_file.write_text(body, encoding="utf-8")
        return {
            "ok": True,
            "task_id": unit.task_id,
            "status": "PASS",
            "result": body,
            "artifact": str(result_file),
        }
