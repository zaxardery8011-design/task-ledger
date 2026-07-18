"""Slice-3 LIGHT contract: kill-then-resume via resume ledger."""

from __future__ import annotations

import json
from pathlib import Path

from task_ledger.adapters.engine import ScriptedEngine
from task_ledger.enqueue.work_order import write_work_order
from task_ledger.ports import FakeEngine
from task_ledger.tick.resume_ledger import ResumeLedger
from task_ledger.tick.worker import claim_next, run_once, simulate_kill_mid_task

_SCENARIO = Path(__file__).parent / "fixtures" / "kill_resume_scenario.json"


def test_kill_then_resume_completes(tmp_path) -> None:
    scen = json.loads(_SCENARIO.read_text(encoding="utf-8"))["scenario"]
    order = write_work_order(
        scen["instruction"], root=tmp_path, task_id=scen["task_id"]
    )
    claimed = claim_next(tmp_path)
    assert claimed is not None
    assert claimed["task_id"] == order.task_id

    st = simulate_kill_mid_task(tmp_path, order.task_id)
    assert st.status == scen["expect_after_kill"]

    # inbox empty after claim; resume path must still finish
    assert not list((tmp_path / "inbox").glob("*.json"))
    result = run_once(root=tmp_path, engine=ScriptedEngine())
    assert result["ok"] is bool(scen["expect_after_resume_ok"])
    assert result["task_id"] == order.task_id
    if scen.get("expect_outbox_result"):
        assert (tmp_path / "outbox" / f"{order.task_id}.result.md").is_file()
    if scen.get("expect_outbox_meta"):
        assert (tmp_path / "outbox" / f"{order.task_id}.meta.json").is_file()

    ledger = ResumeLedger(tmp_path)
    if scen.get("expect_ledger_done"):
        assert ledger.is_done(order.task_id)
    final = ledger.load(order.task_id)
    assert final is not None
    assert final.status == "done"



def test_idle_when_empty(tmp_path) -> None:
    result = run_once(root=tmp_path, engine=FakeEngine())
    assert result["ok"] is True
    assert result["action"] == "idle"
    assert result["task_id"] is None


def test_claim_skips_already_done(tmp_path) -> None:
    order = write_work_order("already finished", root=tmp_path, task_id="demo-task-done-001")
    ledger = ResumeLedger(tmp_path)
    ledger.mark_done(order.task_id)
    claimed = claim_next(tmp_path)
    assert claimed is None
    # archived out of inbox
    assert not (tmp_path / "inbox" / f"{order.task_id}.json").exists()
