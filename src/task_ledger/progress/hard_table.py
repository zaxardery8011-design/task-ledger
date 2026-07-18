"""Progress hard table — facts only; never invents percentages.

Public contract:
- queues: real file counts under inbox / processing / outbox
- tasks: task_id + state + mtime from disk
- notes: honest_states_only_no_fabricated_pct
- code_done != live_green (verification culture)
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from task_ledger.enqueue.work_order import default_root, ensure_queue_dirs


SCHEMA = "task_ledger.progress.hard_table.v1"


def _task_id_from_name(name: str) -> Optional[str]:
    if not name:
        return None
    base = Path(name).stem
    m = re.match(r"^\d{8}_\d+_(.+)$", base)
    if m:
        return m.group(1)
    base = re.sub(r"\.(meta|result|ack)$", "", base)
    return base or None


def build_hard_table(
    root: Optional[Path] = None,
    *,
    max_task_rows: int = 8,
    max_ready_recent: int = 4,
) -> dict[str, Any]:
    root = Path(root) if root else default_root()
    dirs = ensure_queue_dirs(root)
    built_at = datetime.now(timezone.utc).isoformat()
    errors: list[str] = []

    enabled = not (root / "flags" / "HARD_TABLE_OFF.flag").is_file()
    hard_path_on = not (root / "flags" / "ORDER_OFF.flag").is_file()

    tasks: list[dict[str, Any]] = []
    q_in = q_proc = q_ready = 0

    try:
        in_files = sorted(
            [
                p
                for p in dirs["inbox"].iterdir()
                if p.is_file() and not p.name.startswith("_") and not p.name.endswith(".attempt.json")
            ],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        q_in = len(in_files)
        for p in in_files[:max_task_rows]:
            tid = _task_id_from_name(p.name) or p.stem
            tasks.append(
                {
                    "task_id": tid,
                    "state": "queued",
                    "source": "inbox",
                    "mtime": datetime.fromtimestamp(
                        p.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
            )
    except OSError:
        errors.append("inbox_fail")

    try:
        proc_files = sorted(
            [p for p in dirs["processing"].iterdir() if p.is_file() and not p.name.startswith("_")],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        q_proc = len(proc_files)
        for p in proc_files[:max_task_rows]:
            tid = _task_id_from_name(p.name) or p.stem
            tasks.append(
                {
                    "task_id": tid,
                    "state": "processing",
                    "source": "processing",
                    "mtime": datetime.fromtimestamp(
                        p.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
            )
    except OSError:
        errors.append("processing_fail")

    try:
        ready_metas = sorted(
            [
                p
                for p in dirs["outbox"].iterdir()
                if p.is_file() and (p.name.endswith(".meta.json") or p.suffix == ".json")
            ],
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        q_ready = len(ready_metas)
        for p in ready_metas[:max_ready_recent]:
            tid = None
            st = "ready"
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                tid = data.get("task_id")
                st = data.get("status") or st
            except (OSError, json.JSONDecodeError):
                pass
            if not tid:
                tid = _task_id_from_name(p.name)
            if not tid:
                continue
            tasks.append(
                {
                    "task_id": tid,
                    "state": st,
                    "source": "outbox",
                    "mtime": datetime.fromtimestamp(
                        p.stat().st_mtime, tz=timezone.utc
                    ).isoformat(),
                }
            )
    except OSError:
        errors.append("outbox_fail")

    # Dedup preferring processing > queued > ready
    rank = {"processing": 3, "queued": 2}
    by_id: dict[str, dict[str, Any]] = {}
    for t in tasks:
        tid = str(t["task_id"])
        if tid not in by_id:
            by_id[tid] = t
            continue
        prev = by_id[tid]
        r_new = rank.get(str(t["state"]), 1)
        r_old = rank.get(str(prev["state"]), 1)
        if r_new > r_old:
            by_id[tid] = t

    def sort_key(item: dict[str, Any]) -> tuple:
        s = str(item.get("state"))
        pri = 0 if s == "processing" else 1 if s == "queued" else 2
        return (pri, str(item.get("mtime") or ""),)

    task_list = sorted(by_id.values(), key=sort_key)[:max_task_rows]

    return {
        "schema": SCHEMA,
        "built_at": built_at,
        "enabled": enabled,
        "stale": bool(errors),
        "stale_reason": ",".join(errors) if errors else None,
        "flags": {
            "hard_path": "ON" if hard_path_on else "OFF",
            "hard_table": "ON" if enabled else "OFF",
        },
        "queues": {
            "inbox": q_in,
            "processing": q_proc,
            "outbox": q_ready,
        },
        "tasks": task_list,
        "notes": [
            "honest_states_only_no_fabricated_pct",
            "code_done_neq_live_green",
            "no_self_invented_master_percent",
        ],
        "errors": errors,
    }


def format_hard_table(table: Optional[dict[str, Any]] = None, root: Optional[Path] = None) -> str:
    """Compact operator-facing hard table. Never invents %."""
    if table is None:
        table = build_hard_table(root)
    if not table.get("enabled", True):
        hp = (table.get("flags") or {}).get("hard_path", "?")
        return (
            f"Progress query received. Hard table flag=OFF. hard-path={hp}. "
            "No long work enqueued."
        )

    built = table.get("built_at") or "?"
    try:
        built_short = datetime.fromisoformat(built.replace("Z", "+00:00")).strftime("%H:%M:%S")
    except (TypeError, ValueError):
        built_short = str(built)[-8:] if built else "?"

    fresh = "STALE" if table.get("stale") else "fresh"
    q = table.get("queues") or {}
    lines = [
        f"Progress hard table built={built_short} ({fresh})",
        f"Queues inbox={q.get('inbox', 0)} proc={q.get('processing', 0)} outbox={q.get('outbox', 0)}",
        f"hard-path={(table.get('flags') or {}).get('hard_path', '?')}",
    ]
    for t in (table.get("tasks") or [])[:6]:
        lines.append(f"  task_id={t.get('task_id')} state={t.get('state')}")
    if not table.get("tasks"):
        lines.append("  (no open tasks on disk)")
    lines.append("Note: facts only — no fabricated percent.")
    return "\n".join(lines)
