"""Resume ledger — durable job state so long work survives process death.

Schema only; no live private prompts in fixtures.
code_done on disk ≠ live_green verification.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from task_ledger.enqueue.work_order import default_root, ensure_queue_dirs
from task_ledger.util.atomic import atomic_write_text


SCHEMA = "task_ledger.resume.v1"
TERMINAL = frozenset({"done", "failed", "cancelled"})


@dataclass
class ResumeState:
    task_id: str
    status: str = "queued"  # queued|running|resume_waiting|done|failed|cancelled
    instruction: str = ""
    attempt: int = 0
    max_attempts: int = 2
    engine: str = "fake"
    result_path: Optional[str] = None
    error: Optional[str] = None
    updated_at: str = ""
    created_at: str = ""
    schema: str = SCHEMA
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResumeState":
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        kwargs = {k: v for k, v in data.items() if k in known}
        return cls(**kwargs)


class ResumeLedger:
    """JSON-per-task resume store under root/resume/."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = Path(root) if root else default_root()
        self.dirs = ensure_queue_dirs(self.root)
        self.resume_dir = self.dirs["resume"]
        self.done_file = self.dirs["ledger"] / "done_task_ids.txt"

    def path_for(self, task_id: str) -> Path:
        return self.resume_dir / f"{task_id}.json"

    def load(self, task_id: str) -> Optional[ResumeState]:
        p = self.path_for(task_id)
        if not p.is_file():
            return None
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return ResumeState.from_dict(data)
        except (OSError, json.JSONDecodeError, TypeError):
            return None

    def save(self, state: ResumeState) -> Path:
        state.updated_at = datetime.now(timezone.utc).isoformat()
        if not state.created_at:
            state.created_at = state.updated_at
        p = self.path_for(state.task_id)
        # Atomic write: kill mid-save must not leave a half JSON file.
        return atomic_write_text(
            p,
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2) + "\n",
        )

    def is_done(self, task_id: str) -> bool:
        if not self.done_file.is_file():
            return False
        try:
            lines = self.done_file.read_text(encoding="utf-8").splitlines()
            return task_id in {ln.strip() for ln in lines if ln.strip()}
        except OSError:
            return False

    def mark_done(self, task_id: str) -> None:
        self.dirs["ledger"].mkdir(parents=True, exist_ok=True)
        with self.done_file.open("a", encoding="utf-8") as fh:
            fh.write(task_id + "\n")

    def list_resumable(self) -> list[ResumeState]:
        out: list[ResumeState] = []
        if not self.resume_dir.is_dir():
            return out
        for p in sorted(self.resume_dir.glob("*.json")):
            st = self.load(p.stem)
            if st and st.status in ("resume_waiting", "running") and not self.is_done(st.task_id):
                out.append(st)
        return out

    def mark_resume_waiting(self, task_id: str, reason: str = "process_exit") -> ResumeState:
        st = self.load(task_id) or ResumeState(task_id=task_id)
        st.status = "resume_waiting"
        st.meta = {**(st.meta or {}), "wait_reason": reason}
        self.save(st)
        return st
