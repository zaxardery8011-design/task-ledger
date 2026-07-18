"""Slice-3 LIGHT contract: progress hard table is facts-only."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from task_ledger.enqueue.work_order import write_work_order
from task_ledger.progress.hard_table import build_hard_table, format_hard_table

_FIXTURE = Path(__file__).parent / "fixtures" / "hard_table_vectors.json"


def _cases() -> list[dict]:
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return list(data["cases"])


def _seed_root(tmp_path: Path, seed: dict) -> None:
    for tid in seed.get("inbox") or []:
        write_work_order(f"work for {tid}", root=tmp_path, task_id=tid)
    proc = tmp_path / "processing"
    proc.mkdir(parents=True, exist_ok=True)
    for tid in seed.get("processing") or []:
        (proc / f"{tid}.json").write_text(
            json.dumps({"task_id": tid, "instruction": "proc"}, ensure_ascii=False),
            encoding="utf-8",
        )
    out = tmp_path / "outbox"
    out.mkdir(parents=True, exist_ok=True)
    for tid in seed.get("outbox_meta") or []:
        (out / f"{tid}.meta.json").write_text(
            json.dumps({"task_id": tid, "status": "done"}, ensure_ascii=False),
            encoding="utf-8",
        )
    for flag in seed.get("flags") or []:
        flags = tmp_path / "flags"
        flags.mkdir(parents=True, exist_ok=True)
        (flags / f"{flag}.flag").write_text("", encoding="utf-8")


@pytest.mark.parametrize("case", _cases(), ids=lambda c: c["id"])
def test_hard_table_fixture_case(tmp_path, case: dict) -> None:
    _seed_root(tmp_path, case.get("seed") or {})
    table = build_hard_table(tmp_path)
    if "expect_enabled" in case:
        assert table["enabled"] is bool(case["expect_enabled"])
    if case.get("expect_queues") is not None:
        for k, v in case["expect_queues"].items():
            assert table["queues"][k] == v, f"queue {k}"
    if case.get("expect_task_ids"):
        ids = {t["task_id"] for t in table["tasks"]}
        for tid in case["expect_task_ids"]:
            assert tid in ids
    if case.get("forbid_percent_in_text"):
        text = format_hard_table(table)
        assert not re.search(r"\b\d{1,3}%", text)


def test_hard_table_counts_queues(tmp_path) -> None:
    write_work_order("work unit one", root=tmp_path, task_id="demo-task-001")
    write_work_order("work unit two", root=tmp_path, task_id="demo-task-002")
    table = build_hard_table(tmp_path)
    assert table["schema"].startswith("task_ledger.progress.hard_table")
    assert table["queues"]["inbox"] == 2
    assert table["queues"]["processing"] == 0
    assert table["enabled"] is True
    ids = {t["task_id"] for t in table["tasks"]}
    assert "demo-task-001" in ids
    assert "demo-task-002" in ids


def test_hard_table_no_fabricated_percent(tmp_path) -> None:
    write_work_order("do thing", root=tmp_path, task_id="demo-task-001")
    text = format_hard_table(build_hard_table(tmp_path))
    assert "demo-task-001" in text
    assert not re.search(r"\b\d{1,3}%", text)
    assert "facts only" in text.lower() or "fabricated" in text.lower()


def test_hard_table_flag_off(tmp_path) -> None:
    flags = tmp_path / "flags"
    flags.mkdir(parents=True)
    (flags / "HARD_TABLE_OFF.flag").write_text("", encoding="utf-8")
    table = build_hard_table(tmp_path)
    assert table["enabled"] is False
    text = format_hard_table(table)
    assert "OFF" in text
    assert not re.search(r"\b\d{1,3}%", text)


def test_hard_table_notes_honesty(tmp_path) -> None:
    table = build_hard_table(tmp_path)
    notes = " ".join(table.get("notes") or [])
    assert "no_fabricated_pct" in notes or "honest" in notes
    assert "code_done" in notes and "live_green" in notes
