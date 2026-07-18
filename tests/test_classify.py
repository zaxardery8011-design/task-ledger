from task_ledger.classify.order_class import classify_order, is_status_probe


def test_execution_order_enqueues():
    c = classify_order("Fix the resume path and write evidence")
    assert c.kind == "execution_order"
    assert c.should_enqueue is True


def test_status_probe_no_enqueue():
    assert is_status_probe("進度呢")
    c = classify_order("進度呢")
    assert c.kind == "status_probe"
    assert c.should_enqueue is False


def test_vague_ack():
    c = classify_order("ok")
    assert c.kind == "vague_ack"


def test_confirm():
    c = classify_order("confirm")
    assert c.kind == "confirm"
    assert c.should_enqueue is True
