from task_ledger.enqueue.must_become_task import order_to_task


def test_order_enqueues_receipt(tmp_path):
    act = order_to_task("Implement hard table formatter", root=tmp_path)
    assert act.action == "enqueued"
    assert act.task_id
    assert act.path
    assert "task_id=" in (act.reply or "")


def test_status_uses_hard_table(tmp_path):
    act = order_to_task("進度呢", root=tmp_path)
    assert act.action == "status_probe"
    assert "hard table" in (act.reply or "").lower() or "Queues" in (act.reply or "")
