"""Slice-3 LIGHT contract: classify order kinds (fixture-driven)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from task_ledger.classify.order_class import classify_order

_FIXTURE = Path(__file__).parent / "fixtures" / "classify_vectors.json"


def _vectors() -> list[dict]:
    data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    return list(data["vectors"])


@pytest.mark.parametrize("vec", _vectors(), ids=lambda v: v["id"])
def test_classify_vector(vec: dict) -> None:
    c = classify_order(vec["text"])
    assert c.kind == vec["expect_kind"], f"id={vec['id']} note={c.note}"
    assert c.should_enqueue is bool(vec["should_enqueue"])
    if vec.get("is_progress_push"):
        assert c.is_progress_push is True


def test_status_probe_never_enqueues() -> None:
    for text in ("進度呢", "progress?", "status", "queue"):
        c = classify_order(text)
        assert c.kind == "status_probe"
        assert c.should_enqueue is False


def test_execution_order_enqueues() -> None:
    c = classify_order("Fix the resume path and write evidence")
    assert c.kind == "execution_order"
    assert c.should_enqueue is True
