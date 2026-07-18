"""Work order + receipt id — durable enqueue onto a filesystem queue.

Public names: inbox / processing / outbox (not private bridge labels).
Root is always injected (TASK_LEDGER_ROOT / Path) — never hard-coded machine paths.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from task_ledger.util.atomic import atomic_write_text


SCHEMA = "task_ledger.work_order.v1"


@dataclass
class WorkOrder:
    task_id: str
    instruction: str
    kind: str = "task"
    origin: str = "operator"
    channel_id: str = ""
    enqueued_at: str = ""
    schema: str = SCHEMA
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


def default_root() -> Path:
    env = os.environ.get("TASK_LEDGER_ROOT") or os.environ.get("TASK_CORE_ROOT")
    if env:
        return Path(env)
    return Path.cwd() / ".task-ledger"


def ensure_queue_dirs(root: Path) -> dict[str, Path]:
    paths = {
        "inbox": root / "inbox",
        "processing": root / "processing",
        "outbox": root / "outbox",
        "ledger": root / "ledger",
        "resume": root / "resume",
        "flags": root / "flags",
        "followups": root / "followups",
        "promises": root / "promises",
    }
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    return paths


def new_receipt_id(prefix: str = "task") -> str:
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%d%H%M%S")
    ms = f"{now.microsecond // 1000:03d}"
    raw = f"{prefix}-{stamp}{ms}-{uuid4().hex[:8]}"
    return re.sub(r"[^a-zA-Z0-9_-]", "-", raw)


def order_flag_off(root: Path) -> bool:
    """Kill-switch: flags/ORDER_OFF.flag present → hard path disabled."""
    return (root / "flags" / "ORDER_OFF.flag").is_file()


def write_work_order(
    instruction: str,
    root: Optional[Path] = None,
    *,
    channel_id: str = "",
    origin: str = "operator",
    kind: str = "task",
    task_id: Optional[str] = None,
    meta: Optional[dict[str, Any]] = None,
) -> WorkOrder:
    """Write a work unit into inbox/ and return it with a receipt task_id."""
    root = Path(root) if root else default_root()
    if order_flag_off(root):
        raise RuntimeError("order_hard_path_off")

    dirs = ensure_queue_dirs(root)
    tid = task_id or new_receipt_id("task")
    path = dirs["inbox"] / f"{tid}.json"
    n = 0
    while path.exists() and n < 20:
        n += 1
        tid = new_receipt_id("task") + f"-{n}"
        path = dirs["inbox"] / f"{tid}.json"

    instr = (instruction or "").strip()
    if len(instr) > 12000:
        instr = instr[:12000] + "..."

    order = WorkOrder(
        task_id=tid,
        instruction=instr,
        kind=kind,
        origin=origin,
        channel_id=channel_id or "",
        enqueued_at=datetime.now(timezone.utc).isoformat(),
        meta=meta or {},
    )
    atomic_write_text(
        path,
        json.dumps(order.to_dict(), ensure_ascii=False, indent=2) + "\n",
    )
    order.meta = {**(order.meta or {}), "path": str(path)}
    return order
