from task_ledger.adapters.engine import ScriptedEngine
from task_ledger.enqueue.work_order import write_work_order
from task_ledger.tick.resume_ledger import ResumeLedger
from task_ledger.tick.worker import claim_next, run_once, simulate_kill_mid_task


def test_kill_then_resume(tmp_path):
    order = write_work_order("long demo work", root=tmp_path)
    claimed = claim_next(tmp_path)
    assert claimed is not None
    assert claimed["task_id"] == order.task_id

    st = simulate_kill_mid_task(tmp_path, order.task_id)
    assert st.status == "resume_waiting"

    # inbox empty; resume path should still run
    result = run_once(root=tmp_path, engine=ScriptedEngine())
    assert result["ok"] is True
    assert result["task_id"] == order.task_id
    assert (tmp_path / "outbox" / f"{order.task_id}.result.md").is_file()

    ledger = ResumeLedger(tmp_path)
    assert ledger.is_done(order.task_id)
