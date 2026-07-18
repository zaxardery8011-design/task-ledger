from task_ledger.deferred.detect import is_deferred_promise, should_enqueue_deferred
from task_ledger.deferred.enqueue import enqueue_followup, format_enqueue_notice


def test_deferred_promise_detect():
    assert is_deferred_promise("I'll check and report back")
    assert is_deferred_promise("我去查一下")
    assert not is_deferred_promise("Queued, task_id=demo-task-001, will report when done.")
    assert not is_deferred_promise("Progress hard table built=12:00:00\nhard-path=ON")


def test_should_enqueue_lookup_orphan():
    d = should_enqueue_deferred("how far are we?", "ok checking")
    assert d.should is True


def test_enqueue_followup(tmp_path):
    r = enqueue_followup("status?", "let me check", root=tmp_path)
    assert r["ok"] is True
    assert (tmp_path / "followups" / f"{r['followup_id']}.json").is_file()
    assert (tmp_path / "promises" / f"promise-{r['followup_id']}.json").is_file()
    assert "task_id=" in format_enqueue_notice(r["followup_id"])
