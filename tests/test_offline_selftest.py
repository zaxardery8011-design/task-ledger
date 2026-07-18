"""Slice-3 offline selftest — full public core path on a clean temp root.

No network. No API keys. Fake/scripted engine only.
Proves: order→receipt → claim → kill → resume → hard table → deferred follow-up.
"""

from __future__ import annotations

import re

from task_ledger.adapters.engine import ScriptedEngine
from task_ledger.classify.order_class import classify_order
from task_ledger.deferred.detect import should_enqueue_deferred
from task_ledger.deferred.enqueue import enqueue_followup
from task_ledger.enqueue.must_become_task import order_to_task
from task_ledger.progress.hard_table import build_hard_table, format_hard_table
from task_ledger.tick.resume_ledger import ResumeLedger
from task_ledger.tick.worker import claim_next, run_once, simulate_kill_mid_task


def test_offline_pipeline_light(tmp_path) -> None:
    root = tmp_path / "ledger"
    root.mkdir()

    # 1) status probe → hard table (no enqueue, no %)
    status = order_to_task("進度呢", root=root)
    assert status.action == "status_probe"
    assert status.task_id is None
    assert not re.search(r"\b\d{1,3}%", status.reply or "")

    # 2) execution order → receipt on disk
    act = order_to_task("Implement resume retry and report paths", root=root)
    assert act.action == "enqueued"
    assert act.task_id
    assert "task_id=" in (act.reply or "")
    assert (root / "inbox" / f"{act.task_id}.json").is_file()

    # 3) claim + simulated kill
    claimed = claim_next(root)
    assert claimed is not None
    assert claimed["task_id"] == act.task_id
    st = simulate_kill_mid_task(root, act.task_id)
    assert st.status == "resume_waiting"

    # 4) resume finishes to outbox
    ran = run_once(root=root, engine=ScriptedEngine())
    assert ran["ok"] is True
    assert ran["task_id"] == act.task_id
    assert (root / "outbox" / f"{act.task_id}.result.md").is_file()
    assert ResumeLedger(root).is_done(act.task_id)

    # 5) hard table reflects outbox facts
    table = build_hard_table(root)
    assert table["queues"]["outbox"] >= 1
    text = format_hard_table(table)
    assert not re.search(r"\b\d{1,3}%", text)

    # 6) deferred promise → follow-up + promise files
    dec = should_enqueue_deferred("how far?", "I'll check and report back", root=root)
    assert dec.should is True
    fu = enqueue_followup("how far?", "I'll check and report back", root=root)
    assert fu["ok"] is True
    fid = fu["followup_id"]
    assert (root / "followups" / f"{fid}.json").is_file()
    assert (root / "promises" / f"promise-{fid}.json").is_file()

    # 7) classify still pure after FS work
    c = classify_order("confirm")
    assert c.kind == "confirm" and c.should_enqueue is True
