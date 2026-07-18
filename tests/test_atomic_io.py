"""Atomic write + resume durability after mid-write style updates."""

from __future__ import annotations

import json
from pathlib import Path

from task_ledger.enqueue.work_order import write_work_order
from task_ledger.tick.resume_ledger import ResumeLedger, ResumeState
from task_ledger.tick.worker import claim_next, run_once
from task_ledger.adapters.engine import ScriptedEngine
from task_ledger.util.atomic import atomic_write_text


def test_atomic_write_text_creates_file(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "note.txt"
    out = atomic_write_text(target, "hello\n")
    assert out == target
    assert target.read_text(encoding="utf-8") == "hello\n"
    # no leftover temps
    leftovers = list((tmp_path / "sub").glob("*.tmp"))
    assert leftovers == []


def test_atomic_write_overwrites_cleanly(tmp_path: Path) -> None:
    target = tmp_path / "x.json"
    atomic_write_text(target, '{"v":1}\n')
    atomic_write_text(target, '{"v":2}\n')
    assert json.loads(target.read_text(encoding="utf-8"))["v"] == 2


def test_resume_save_roundtrip_atomic(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    root.mkdir()
    ledger = ResumeLedger(root)
    st = ResumeState(
        task_id="demo-task-001",
        status="running",
        instruction="do the thing",
        attempt=1,
    )
    path = ledger.save(st)
    assert path.is_file()
    loaded = ledger.load("demo-task-001")
    assert loaded is not None
    assert loaded.status == "running"
    assert loaded.instruction == "do the thing"
    # rewrite
    st.status = "resume_waiting"
    ledger.save(st)
    assert ledger.load("demo-task-001").status == "resume_waiting"  # type: ignore[union-attr]


def test_work_order_atomic_on_disk(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    order = write_work_order("Atomic enqueue path", root=root)
    path = root / "inbox" / f"{order.task_id}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["task_id"] == order.task_id
    assert data["instruction"] == "Atomic enqueue path"


def test_claim_missing_file_race_skips(tmp_path: Path) -> None:
    """If inbox candidate disappears before move, claim_next returns None/next."""
    root = tmp_path / "ledger"
    root.mkdir()
    # empty inbox → idle claim
    assert claim_next(root) is None

    order = write_work_order("race target", root=root)
    # remove after write to simulate another worker winning
    (root / "inbox" / f"{order.task_id}.json").unlink()
    assert claim_next(root) is None


def test_outbox_written_atomically_via_run_once(tmp_path: Path) -> None:
    root = tmp_path / "ledger"
    order = write_work_order("finish me", root=root)
    result = run_once(root=root, engine=ScriptedEngine())
    assert result["ok"] is True
    assert result["task_id"] == order.task_id
    meta = json.loads((root / "outbox" / f"{order.task_id}.meta.json").read_text(encoding="utf-8"))
    assert meta["status"] == "done"
