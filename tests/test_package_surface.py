"""Package surface checks — required files, version lock, public-line shape."""

from __future__ import annotations

import re
from pathlib import Path

import task_ledger

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    "LICENSE",
    "NOTICE",
    "pyproject.toml",
    "docs/ARCHITECTURE.md",
    "docs/ENGINE_COUPLING.md",
    "docs/SHIP_PREP.md",
    "docs/SLICE3_SELFTEST.md",
    "scripts/sanitize_gate.py",
    "scripts/ship_readiness_gate.py",
    "scripts/run_offline_selftest.py",
    "src/task_ledger/__init__.py",
    "src/task_ledger/util/atomic.py",
    "src/task_ledger/cli.py",
]


def test_required_files_present() -> None:
    missing = [p for p in REQUIRED_FILES if not (PACKAGE_ROOT / p).is_file()]
    assert missing == [], f"missing required files: {missing}"


def test_version_matches_pyproject() -> None:
    text = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.M)
    assert m, "version missing in pyproject.toml"
    assert task_ledger.__version__ == m.group(1)


def test_ship_ok_flag_present_for_published_alpha() -> None:
    """Published alpha package root records explicit ship readiness."""
    assert (PACKAGE_ROOT / "SHIP_OK.flag").is_file()


def test_notice_has_final_copyright_holder() -> None:
    notice = (PACKAGE_ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "COPYRIGHT_HOLDER_TBD" not in notice
    assert "Task-Ledger Contributors" in notice


def test_homepage_is_public_repo_url() -> None:
    text = (PACKAGE_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "github.com/example/task-ledger" not in text
    assert 'Homepage = "https://github.com/zaxardery8011-design/task-ledger"' in text


def test_public_exports() -> None:
    assert callable(task_ledger.classify_order)
    assert callable(task_ledger.order_to_task)
    assert callable(task_ledger.build_hard_table)
    assert callable(task_ledger.format_hard_table)
    assert callable(task_ledger.should_enqueue_deferred)
    assert task_ledger.ResumeLedger is not None
