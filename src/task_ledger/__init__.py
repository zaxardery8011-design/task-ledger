"""task-ledger — durable single-machine task core (receipts, resume, hard facts).

Public package name: task-ledger
Slice status: private staging (slice-3 accepted; ship prep hardening) — not published.
Public-line lexicon: operator / user / orchestrator / owner only.
Ship gate: blocked until explicit owner ship-OK (see docs/SHIP_PREP.md).
"""

from __future__ import annotations

__version__ = "0.1.0a3"
__schema__ = "task_ledger.core.v1"
__slice__ = "3-accepted-ship-prep-private"

from task_ledger.classify.order_class import classify_order
from task_ledger.deferred.detect import should_enqueue_deferred
from task_ledger.enqueue.must_become_task import order_to_task
from task_ledger.progress.hard_table import build_hard_table, format_hard_table
from task_ledger.tick.resume_ledger import ResumeLedger

__all__ = [
    "__version__",
    "__schema__",
    "classify_order",
    "order_to_task",
    "build_hard_table",
    "format_hard_table",
    "should_enqueue_deferred",
    "ResumeLedger",
]
