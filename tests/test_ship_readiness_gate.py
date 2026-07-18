"""Ship readiness gate — must stay BLOCKED on private staging defaults.

Also proves the gate can go READY only when owner fill-ins are present
(using a throwaway temp tree — never creates SHIP_OK.flag in package root).
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
GATE = PACKAGE_ROOT / "scripts" / "ship_readiness_gate.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("ship_readiness_gate", GATE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_package_root_is_blocked() -> None:
    """Private staging tree must not claim ship-ready."""
    mod = _load_gate_module()
    summary = mod.check(PACKAGE_ROOT)
    assert summary["status"] == "BLOCKED"
    assert summary["blocker_count"] >= 1
    joined = " ".join(summary["blockers"]).lower()
    assert "ship_ok" in joined or "placeholder" in joined or "tbd" in joined


def test_cli_exit_nonzero_on_package_root() -> None:
    r = subprocess.run(
        [sys.executable, str(GATE), "--root", str(PACKAGE_ROOT), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert r.returncode != 0
    data = json.loads(r.stdout)
    assert data["status"] == "BLOCKED"


def test_ready_when_all_fill_ins_present(tmp_path: Path) -> None:
    """Isolated tree: with real URL + copyright + SHIP_OK.flag → READY."""
    # Minimal package-shaped tree for the gate only
    (tmp_path / "LICENSE").write_text("Apache-2.0 stub\n", encoding="utf-8")
    (tmp_path / "NOTICE").write_text(
        "task-ledger\nCopyright 2026 Example Owner Org\n",
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project.urls]\nHomepage = "https://github.com/real-org/task-ledger"\n',
        encoding="utf-8",
    )
    (tmp_path / "SHIP_OK.flag").write_text(
        "owner ship-OK recorded for test only\n",
        encoding="utf-8",
    )
    mod = _load_gate_module()
    summary = mod.check(tmp_path)
    assert summary["status"] == "READY", summary
    assert summary["blocker_count"] == 0


def test_placeholder_homepage_blocks(tmp_path: Path) -> None:
    (tmp_path / "LICENSE").write_text("x\n", encoding="utf-8")
    (tmp_path / "NOTICE").write_text("Copyright 2026 Real Owner\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        'Homepage = "https://github.com/example/task-ledger"\n',
        encoding="utf-8",
    )
    (tmp_path / "SHIP_OK.flag").write_text("ok\n", encoding="utf-8")
    mod = _load_gate_module()
    summary = mod.check(tmp_path)
    assert summary["status"] == "BLOCKED"
    assert any("placeholder" in b.lower() for b in summary["blockers"])
