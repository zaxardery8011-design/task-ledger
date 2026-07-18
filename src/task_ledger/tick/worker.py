"""Tick worker loop — claim inbox → processing → engine → outbox.

Survives kill via ResumeLedger. Engine is injected (FakeEngine in selftests).
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from task_ledger.enqueue.work_order import default_root, ensure_queue_dirs
from task_ledger.ports import EnginePort, FakeEngine, WorkUnit
from task_ledger.tick.resume_ledger import ResumeLedger, ResumeState
from task_ledger.util.atomic import atomic_write_text


def claim_next(root: Optional[Path] = None) -> Optional[dict[str, Any]]:
    """Move one inbox item into processing. Returns envelope or None.

    Concurrent tickers: if move loses a race (FileNotFoundError / PermissionError),
    skip that candidate and try the next — do not crash the tick loop.
    """
    root = Path(root) if root else default_root()
    dirs = ensure_queue_dirs(root)
    ledger = ResumeLedger(root)

    try:
        candidates = sorted(
            [
                p
                for p in dirs["inbox"].iterdir()
                if p.is_file() and p.suffix == ".json" and not p.name.startswith("_")
            ],
            key=lambda p: p.stat().st_mtime,
        )
    except OSError:
        return None

    for src in candidates:
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        tid = str(data.get("task_id") or src.stem)
        if ledger.is_done(tid):
            # skip terminal
            archive = dirs["inbox"] / "_done"
            archive.mkdir(exist_ok=True)
            try:
                shutil.move(str(src), str(archive / src.name))
            except (OSError, shutil.Error):
                pass
            continue
        dest = dirs["processing"] / src.name
        try:
            # Prefer os.replace-style atomic claim when same volume.
            # shutil.move handles cross-device; either way race → try next.
            shutil.move(str(src), str(dest))
        except (FileNotFoundError, PermissionError, OSError, shutil.Error):
            continue
        data["_claimed_path"] = str(dest)
        data["_claimed_at"] = datetime.now(timezone.utc).isoformat()
        st = ResumeState(
            task_id=tid,
            status="running",
            instruction=str(data.get("instruction") or ""),
            attempt=int(data.get("attempt") or 1),
            max_attempts=int(data.get("max_attempts") or 2),
        )
        ledger.save(st)
        return data
    return None


def run_once(
    root: Optional[Path] = None,
    engine: Optional[EnginePort] = None,
    *,
    work_dir: Optional[Path] = None,
) -> dict[str, Any]:
    """Claim one task, run engine, write outbox result, update resume ledger."""
    root = Path(root) if root else default_root()
    dirs = ensure_queue_dirs(root)
    ledger = ResumeLedger(root)
    engine = engine or FakeEngine()
    work_dir = Path(work_dir) if work_dir else root / "workspace"
    work_dir.mkdir(parents=True, exist_ok=True)

    claimed = claim_next(root)
    if not claimed:
        # try resume_waiting
        for st in ledger.list_resumable():
            if st.status == "resume_waiting" and st.instruction:
                claimed = {
                    "task_id": st.task_id,
                    "instruction": st.instruction,
                    "attempt": st.attempt + 1,
                    "max_attempts": st.max_attempts,
                    "_resume": True,
                }
                st.status = "running"
                st.attempt = claimed["attempt"]
                ledger.save(st)
                break

    if not claimed:
        return {"ok": True, "action": "idle", "task_id": None}

    tid = str(claimed.get("task_id"))
    unit = WorkUnit(
        task_id=tid,
        instruction=str(claimed.get("instruction") or ""),
        kind=str(claimed.get("kind") or "task"),
        origin=str(claimed.get("origin") or "operator"),
        meta={k: v for k, v in claimed.items() if not k.startswith("_")},
    )

    try:
        result = engine.run(unit, work_dir)
        status = str(result.get("status") or "PASS")
        body = str(result.get("result") or "")
        ok = bool(result.get("ok", True))
    except Exception as exc:  # noqa: BLE001 — surface engine failures into ledger
        ok = False
        status = "FAIL"
        body = str(exc)
        result = {"ok": False, "error": body}

    out_result = dirs["outbox"] / f"{tid}.result.md"
    out_meta = dirs["outbox"] / f"{tid}.meta.json"
    atomic_write_text(
        out_result,
        f"## Deliverables\n- task_id={tid}\n\n## Status\n{status} — engine result\n\n{body}\n",
    )
    meta = {
        "schema": "task_ledger.outbox.meta.v1",
        "task_id": tid,
        "status": "done" if ok else "failed",
        "engine_status": status,
        "result_path": str(out_result),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    atomic_write_text(
        out_meta,
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n",
    )

    st = ledger.load(tid) or ResumeState(task_id=tid, instruction=unit.instruction)
    st.status = "done" if ok else "failed"
    st.result_path = str(out_result)
    st.error = None if ok else body
    ledger.save(st)
    if ok:
        ledger.mark_done(tid)

    # clear processing file if present
    claimed_path = claimed.get("_claimed_path")
    if claimed_path and Path(claimed_path).is_file():
        archive = dirs["processing"] / "_done"
        archive.mkdir(exist_ok=True)
        shutil.move(str(claimed_path), str(archive / Path(claimed_path).name))

    return {
        "ok": ok,
        "action": "ran",
        "task_id": tid,
        "status": status,
        "result_path": str(out_result),
        "meta_path": str(out_meta),
        "engine_result": result,
    }


def simulate_kill_mid_task(root: Path, task_id: str) -> ResumeState:
    """Demo helper: mark a running task as resume_waiting (kill-then-resume)."""
    ledger = ResumeLedger(root)
    return ledger.mark_resume_waiting(task_id, reason="simulated_kill")
