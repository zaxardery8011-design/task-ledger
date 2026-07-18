from task_ledger.enqueue.work_order import write_work_order
from task_ledger.progress.hard_table import build_hard_table, format_hard_table


def test_hard_table_facts_only(tmp_path):
    write_work_order("do thing", root=tmp_path, task_id="demo-task-001")
    table = build_hard_table(tmp_path)
    assert table["queues"]["inbox"] >= 1
    text = format_hard_table(table)
    assert "demo-task-001" in text or "task_id=" in text
    assert "%" not in text or "percent" in text.lower()  # no fabricated xx%
    # stronger: no digit-percent token
    import re

    assert not re.search(r"\b\d{1,3}%", text)
    assert "fabricated" in text.lower() or "facts only" in text.lower()
