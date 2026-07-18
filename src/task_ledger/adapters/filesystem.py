"""Default filesystem layout adapter."""

from __future__ import annotations

from pathlib import Path

from task_ledger.enqueue.work_order import default_root, ensure_queue_dirs


class FilesystemLayout:
    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root else default_root()
        self.dirs = ensure_queue_dirs(self.root)

    @property
    def inbox(self) -> Path:
        return self.dirs["inbox"]

    @property
    def processing(self) -> Path:
        return self.dirs["processing"]

    @property
    def outbox(self) -> Path:
        return self.dirs["outbox"]

    @property
    def resume(self) -> Path:
        return self.dirs["resume"]
