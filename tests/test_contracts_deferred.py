"""Slice-3 LIGHT contract: deferred promises do not evaporate."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from task_ledger.deferred.detect import is_deferred_promise, should_enqueue_deferred
from task_ledger.deferred.enqueue import enqueue_followup, format_enqueue_notice

_FIXTURE = Path(__file__).parent / "fixtures" / "deferred_vectors.json"


def _vectors() -> list[dict]:
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return list(data["vectors"])


@pytest.mark.parametrize("vec", _vectors(), ids=lambda v: v["id"])
def test_deferred_vector(vec: dict) -> None:
    assert is_deferred_promise(vec["assistant"]) is bool(vec["expect_is_deferred"])
    d = should_enqueue_deferred(vec["operator"], vec["assistant"])
    assert d.should is bool(vec["expect_should_enqueue"])
    if "expect_reason" in vec:
        assert d.reason == vec["expect_reason"]
    if "expect_reason_any" in vec:
        assert d.reason in vec["expect_reason_any"]


def test_enqueue_writes_followup_and_promise(tmp_path) -> None:
    r = enqueue_followup("status?", "let me check", root=tmp_path)
    assert r["ok"] is True
    fid = r["followup_id"]
    assert fid.startswith("followup-")
    assert (tmp_path / "followups" / f"{fid}.json").is_file()
    assert (tmp_path / "promises" / f"promise-{fid}.json").is_file()
    assert (tmp_path / "inbox" / f"{fid}.json").is_file()
    notice = format_enqueue_notice(fid)
    assert "task_id=" in notice
    assert fid in notice


def test_deferred_flag_off(tmp_path) -> None:
    flags = tmp_path / "flags"
    flags.mkdir(parents=True)
    (flags / "DEFERRED_OFF.flag").write_text("", encoding="utf-8")
    d = should_enqueue_deferred(
        "how far?", "I'll check and report back", root=tmp_path
    )
    assert d.should is False
    assert d.reason == "link_off"
