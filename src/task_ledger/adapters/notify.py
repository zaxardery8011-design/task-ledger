"""Notify adapters — LogNotify is safe default; chat networks are host-provided."""

from __future__ import annotations

from pathlib import Path

from task_ledger.ports import NotifyMessage


class LogNotify:
    """Append notifications to a local log file (no network)."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, message: NotifyMessage) -> bool:
        line = f"{message.channel_id}\t{message.text}\n"
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line)
        return True
