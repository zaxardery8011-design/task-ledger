#!/usr/bin/env python3
"""Ship readiness gate — intentionally RED until owner decisions land.

This is NOT the sanitization gate. Sanitize can be GREEN while ship stays RED.
Slice-4 public remote is blocked until every check below is satisfied AND the
owner has given explicit ship-OK (not implied from "continue building").

Exit 0 = ready to consider publish steps.
Exit 1 = blocked (expected on private staging).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PLACEHOLDER_HOMEPAGE_MARKERS = (
    "github.com/example/",
    "example.com",
    "TODO_HOMEPAGE",
    "placeholder",
)

TBD_COPYRIGHT_MARKERS = (
    "COPYRIGHT_HOLDER_TBD",
    "Copyright 2026 TBD",
    "[copyright holder TBD]",
    "copyright holder TBD",
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"__READ_FAIL__:{exc}"


def check(root: Path) -> dict:
    root = root.resolve()
    blockers: list[str] = []
    notes: list[str] = []

    # 1) Explicit ship-OK flag (owner-created only; never auto-create here)
    ship_flag = root / "SHIP_OK.flag"
    if not ship_flag.is_file():
        blockers.append(
            "SHIP_OK.flag missing — requires explicit owner ship-OK "
            "(not implied from continue-building)"
        )
    else:
        notes.append("SHIP_OK.flag present")

    # 2) Homepage URL in pyproject.toml must not be placeholder
    pyproject = root / "pyproject.toml"
    if not pyproject.is_file():
        blockers.append("pyproject.toml missing")
    else:
        text = _read(pyproject)
        m = re.search(
            r'^\s*Homepage\s*=\s*["\']([^"\']+)["\']',
            text,
            re.M | re.I,
        )
        if not m:
            blockers.append("pyproject.toml Homepage URL missing")
        else:
            url = m.group(1).strip()
            low = url.lower()
            if any(marker in low for marker in PLACEHOLDER_HOMEPAGE_MARKERS):
                blockers.append(
                    f"Homepage still placeholder: {url!r} "
                    "(owner must set real public org/repo URL)"
                )
            elif not low.startswith("https://"):
                blockers.append(f"Homepage must be https URL, got {url!r}")
            else:
                notes.append(f"Homepage looks non-placeholder: {url}")

    # 3) NOTICE copyright holder string
    notice = root / "NOTICE"
    if not notice.is_file():
        blockers.append(
            "NOTICE missing — required for Apache-2.0 public history attribution"
        )
    else:
        ntext = _read(notice)
        if any(marker.lower() in ntext.lower() for marker in TBD_COPYRIGHT_MARKERS):
            blockers.append(
                "NOTICE still has TBD copyright holder "
                "(owner must set final copyright string)"
            )
        elif "Copyright" not in ntext:
            blockers.append("NOTICE has no Copyright line")
        else:
            notes.append("NOTICE copyright line present and not TBD-marked")

    # 4) LICENSE present
    if not (root / "LICENSE").is_file():
        blockers.append("LICENSE missing")
    else:
        notes.append("LICENSE present")

    # 5) Sanitize still expected green (advisory note only — not re-run here)
    notes.append(
        "Run scripts/sanitize_gate.py separately; ship readiness does not replace it"
    )

    status = "READY" if not blockers else "BLOCKED"
    return {
        "schema": "task_ledger.ship_readiness.v1",
        "status": status,
        "root": str(root),
        "blocker_count": len(blockers),
        "blockers": blockers,
        "notes": notes,
        "policy": (
            "Operator 'continue building' is NOT ship-OK. "
            "Public remote only after explicit owner ship-OK + blockers cleared."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="task-ledger ship readiness gate")
    ap.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Package root (default: parent of scripts/)",
    )
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    root = args.root
    if root is None:
        root = Path(__file__).resolve().parent.parent
    summary = check(root)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"ship_readiness status={summary['status']} root={summary['root']}")
        print(f"blocker_count={summary['blocker_count']}")
        for b in summary["blockers"]:
            print(f"BLOCKER: {b}")
        for n in summary["notes"]:
            print(f"NOTE: {n}")
        print(f"POLICY: {summary['policy']}")
        if summary["status"] == "READY":
            print("PASS — ship readiness checks clear (still need operator publish steps)")
        else:
            print("FAIL — expected on private staging until owner ship-OK + fill-ins")

    return 0 if summary["status"] == "READY" else 1


if __name__ == "__main__":
    sys.exit(main())
