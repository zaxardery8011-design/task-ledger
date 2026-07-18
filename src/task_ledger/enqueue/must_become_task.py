"""order → task + receipt (knife-1 public surface).

Status probes never invent progress percent.
Execution orders get a durable receipt id on disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from task_ledger.classify.order_class import OrderClass, classify_order
from task_ledger.enqueue.work_order import WorkOrder, write_work_order
from task_ledger.progress.hard_table import build_hard_table, format_hard_table


@dataclass
class OrderAction:
    action: str  # none | enqueued | needs_confirm | blocked | status_probe | rule_set
    order_class: Optional[OrderClass] = None
    task_id: Optional[str] = None
    path: Optional[str] = None
    reply: Optional[str] = None
    reason: str = ""
    work_order: Optional[WorkOrder] = None
    extra: dict[str, Any] = field(default_factory=dict)


def order_to_task(
    text: str,
    root: Optional[Path] = None,
    *,
    channel_id: str = "",
    locks: Optional[dict[str, Any]] = None,
    order_enabled: bool = True,
) -> OrderAction:
    """Classify and maybe hard-enqueue. Pure + filesystem; no chat network."""
    if not order_enabled:
        return OrderAction(action="none", reason="flag_off")

    cls = classify_order(text)
    base = OrderAction(action="none", order_class=cls, reason=f"class_{cls.kind}")

    if cls.kind == "rule_set":
        base.action = "rule_set"
        base.reason = "standing_rule_persisted"
        base.reply = "Standing rule noted (persist is host responsibility)."
        return base

    if cls.kind == "status_probe":
        table = build_hard_table(root)
        base.action = "status_probe"
        base.reason = "status_or_progress_query"
        base.reply = format_hard_table(table)
        base.extra["table"] = table
        return base

    if cls.kind in ("stop", "vague_ack", "greeting", "chat"):
        return base

    if locks:
        if locks.get("stop_lock") or locks.get("read_only_lock") or locks.get("audit_lock"):
            base.action = "blocked"
            base.reason = "locks_block_enqueue"
            snip = (text or "").strip()
            if len(snip) > 100:
                snip = snip[:100] + "..."
            base.reply = f"Order blocked by locks ({base.reason}). snip={snip}"
            return base

    if cls.kind == "needs_confirm" and not cls.should_enqueue:
        base.action = "needs_confirm"
        base.reason = cls.note
        base.reply = "Please confirm with a short explicit confirm (e.g. 'confirm' / '做吧')."
        return base

    if not cls.should_enqueue and cls.kind != "confirm":
        return base

    try:
        order = write_work_order(
            instruction=text,
            root=root,
            channel_id=channel_id,
            origin="must_become_task",
            kind="task",
        )
    except RuntimeError as exc:
        base.action = "none"
        base.reason = str(exc)
        return base

    path = (order.meta or {}).get("path")
    reply = f"Queued, task_id={order.task_id}, will report when done."
    return OrderAction(
        action="enqueued",
        order_class=cls,
        task_id=order.task_id,
        path=path,
        reply=reply,
        reason="enqueued",
        work_order=order,
    )
