"""Deferred follow-up enqueue — durable record + promise watch.

Push-on-complete goes through FollowupCompletePort (not bundled chat).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from task_ledger.enqueue.work_order import default_root, ensure_queue_dirs, write_work_order


def format_enqueue_notice(followup_id: str, reason: str = "deferred_promise") -> str:
    del reason
    fid = (followup_id or "").strip()
    if not fid:
        return ""
    return f"(follow-up queued task_id={fid}, expect a substantive report soon)"


def new_followup_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"followup-{stamp}-{uuid4().hex[:6]}"


def enqueue_followup(
    operator_text: str,
    assistant_text: str = "",
    root: Optional[Path] = None,
    *,
    channel_id: str = "",
    reason: str = "deferred_promise",
) -> dict[str, Any]:
    """Write followup record + promise + work order. No network."""
    root = Path(root) if root else default_root()
    dirs = ensure_queue_dirs(root)
    fid = new_followup_id()
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "schema": "task_ledger.followup.v1",
        "id": fid,
        "channel_id": channel_id or "",
        "operator_text": operator_text,
        "ack_text": assistant_text,
        "reason": reason,
        "status": "queued",
        "push_on_complete": True,
        "created_at": now,
        "updated_at": now,
    }
    rec_path = dirs["followups"] / f"{fid}.json"
    rec_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    detail = (operator_text or "").strip()[:200]
    promise = {
        "schema": "task_ledger.promise.v1",
        "id": f"promise-{fid}",
        "title": f"follow-up {fid}",
        "status": "watching",
        "kind": "deferred_followup",
        "detail": detail,
        "due_hint": "~2min",
        "followup_id": fid,
        "check": "worker must complete and push; deferred must not evaporate",
        "alert_if": "status still watching after 3 min without push",
        "owner": "operator",
        "created_at": now,
        "updated_at": now,
    }
    promise_path = dirs["promises"] / f"promise-{fid}.json"
    promise_path.write_text(
        json.dumps(promise, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    instruction = (
        f"# Follow-up work — REAL EXECUTION\n"
        f"schema: task_ledger.followup.v1\n"
        f"followup_id: {fid}\n\n"
        f"Prior turn only ACKed / promised deferred work. Deliver the SUBSTANTIVE answer now.\n\n"
        f"## Operator asked\n{(operator_text or '').strip()[:800]}\n\n"
        f"## Prior orphan ack (do not repeat intent)\n{(assistant_text or '').strip()[:400]}\n"
    )
    order = write_work_order(
        instruction=instruction,
        root=root,
        channel_id=channel_id,
        origin="deferred_followup",
        kind="followup",
        task_id=fid,
        meta={"followup_record": str(rec_path), "promise": str(promise_path), "reason": reason},
    )

    notice = format_enqueue_notice(fid, reason)
    return {
        "ok": True,
        "followup_id": fid,
        "task_id": order.task_id,
        "record_path": str(rec_path),
        "promise_path": str(promise_path),
        "work_path": (order.meta or {}).get("path"),
        "notice": notice,
        "reason": reason,
    }
