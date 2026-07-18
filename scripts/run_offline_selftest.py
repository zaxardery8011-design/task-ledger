#!/usr/bin/env python3
"""Slice-3 offline selftest entry — pytest contracts + sanitize gate.

Exit 0 only if both GREEN. No network. No API keys.

Env:
  TASK_LEDGER_SANITIZE_SOFT_FAIL=1 — treat soft lexicon hits as hard failures
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _pytest_passed(stdout: str, stderr: str, code: int) -> bool:
    """True when test body is green.

    On Windows, pytest may exit non-zero solely because cleaning the
    ``pytest-current`` symlink under %TEMP% hits PermissionError after
    all tests already passed. Treat that cleanup-only failure as green.
    """
    text = f"{stdout}\n{stderr}"
    if re.search(r"(?m)^\s*\d+\s+failed", text):
        return False
    if re.search(r"(?m)^\s*\d+\s+error", text, re.I):
        return False
    passed = re.search(r"(\d+)\s+passed", text)
    if not passed:
        return code == 0
    if code == 0:
        return True
    if "PermissionError" in text and "pytest-current" in text:
        print(
            "WARN — pytest session cleanup PermissionError on Windows "
            f"(tests still {passed.group(0)}); treating as green"
        )
        return True
    return False


def main() -> int:
    print(f"offline_selftest root={ROOT}")
    env = {**dict(os.environ), "PYTHONPATH": str(ROOT / "src")}
    # Keep basetemp outside package tree so sanitize_gate never scans test debris.
    basetemp = Path(tempfile.mkdtemp(prefix=f"task-ledger-pytest-{int(time.time())}-"))
    try:
        r1 = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests",
                "-q",
                "--tb=short",
                f"--basetemp={basetemp}",
            ],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r1.stdout:
            print(r1.stdout, end="" if r1.stdout.endswith("\n") else "\n")
        if r1.stderr:
            print(r1.stderr, end="" if r1.stderr.endswith("\n") else "\n")
        pytest_ok = _pytest_passed(r1.stdout or "", r1.stderr or "", r1.returncode)
        print(f"pytest exit={r1.returncode} ok={pytest_ok}")
    finally:
        try:
            shutil.rmtree(basetemp, ignore_errors=True)
        except OSError:
            pass
        # Drop any leftover in-tree basetemp from earlier runs
        local_bt = ROOT / ".pytest_basetemp"
        if local_bt.is_dir():
            shutil.rmtree(local_bt, ignore_errors=True)

    gate_cmd = [
        sys.executable,
        str(ROOT / "scripts" / "sanitize_gate.py"),
        "--root",
        str(ROOT),
    ]
    if os.environ.get("TASK_LEDGER_SANITIZE_SOFT_FAIL", "").strip() in (
        "1",
        "true",
        "TRUE",
        "yes",
    ):
        gate_cmd.append("--soft-fail")
        print("sanitize_gate soft-fail mode ON (public-line lexicon hard)")
    r2 = subprocess.run(gate_cmd, cwd=str(ROOT))
    print(f"sanitize_gate exit={r2.returncode}")
    if (not pytest_ok) or r2.returncode != 0:
        print("FAIL — offline selftest not green")
        return 1
    print("PASS — offline selftest + sanitize gate green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
