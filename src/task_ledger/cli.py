"""Minimal CLI front door: classify / enqueue / table / tick / demo-resume."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from task_ledger import __version__
from task_ledger.classify.order_class import classify_order
from task_ledger.deferred.detect import should_enqueue_deferred
from task_ledger.deferred.enqueue import enqueue_followup
from task_ledger.enqueue.must_become_task import order_to_task
from task_ledger.progress.hard_table import build_hard_table, format_hard_table
from task_ledger.tick.worker import run_once, simulate_kill_mid_task
from task_ledger.adapters.engine import ScriptedEngine
from task_ledger.enqueue.work_order import write_work_order


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="task-ledger",
        description="Durable single-machine task core (receipts, resume, hard facts).",
    )
    parser.add_argument("--version", action="version", version=f"task-ledger {__version__}")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Ledger root (or env TASK_LEDGER_ROOT). Default: ./.task-ledger",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cls = sub.add_parser("classify", help="Classify operator text")
    p_cls.add_argument("text")

    p_order = sub.add_parser("order", help="Order → task + receipt (or status hard table)")
    p_order.add_argument("text")

    p_table = sub.add_parser("table", help="Print progress hard table")

    p_tick = sub.add_parser("tick", help="Claim + run one task with scripted engine")

    p_demo = sub.add_parser(
        "demo-resume",
        help="Kill-then-resume demo: enqueue, claim mid-flight, resume",
    )

    p_def = sub.add_parser("deferred", help="Detect deferred promise")
    p_def.add_argument("--operator", required=True)
    p_def.add_argument("--assistant", required=True)
    p_def.add_argument("--enqueue", action="store_true")

    args = parser.parse_args(argv)
    root = args.root

    if args.cmd == "classify":
        c = classify_order(args.text)
        print(json.dumps(c.__dict__, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "order":
        act = order_to_task(args.text, root=root)
        out = {
            "action": act.action,
            "task_id": act.task_id,
            "path": act.path,
            "reply": act.reply,
            "reason": act.reason,
            "class": act.order_class.__dict__ if act.order_class else None,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    if args.cmd == "table":
        print(format_hard_table(build_hard_table(root), root))
        return 0

    if args.cmd == "tick":
        result = run_once(root=root, engine=ScriptedEngine())
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        return 0 if result.get("ok") else 1

    if args.cmd == "deferred":
        dec = should_enqueue_deferred(args.operator, args.assistant, root=root)
        out: dict = dec.__dict__.copy()
        if args.enqueue and dec.should:
            out["enqueued"] = enqueue_followup(
                args.operator, args.assistant, root=root, reason=dec.reason
            )
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))
        return 0

    if args.cmd == "demo-resume":
        # isolated temp root if none provided
        tmp: tempfile.TemporaryDirectory[str] | None = None
        if root is None:
            tmp = tempfile.TemporaryDirectory(prefix="task-ledger-demo-")
            root = Path(tmp.name)
        try:
            order = write_work_order(
                "Demo long work that must survive kill",
                root=root,
                origin="demo-resume",
            )
            # claim into processing / running
            from task_ledger.tick.worker import claim_next

            claimed = claim_next(root)
            assert claimed and claimed.get("task_id") == order.task_id
            simulate_kill_mid_task(root, order.task_id)
            # resume
            result = run_once(root=root, engine=ScriptedEngine())
            print(
                json.dumps(
                    {
                        "task_id": order.task_id,
                        "killed_mid_flight": True,
                        "resume_result": result,
                        "root": str(root),
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
            )
            return 0 if result.get("ok") else 1
        finally:
            if tmp is not None:
                tmp.cleanup()

    return 2


if __name__ == "__main__":
    sys.exit(main())
