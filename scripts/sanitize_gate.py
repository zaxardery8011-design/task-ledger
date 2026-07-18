#!/usr/bin/env python3
"""Sanitization CI regex hard gate — fail if private/leak patterns appear in shipped tree.

Authoritative rules: SANITIZATION_CHECKLIST.md (host docs) + this script.
Exit 0 = green; non-zero = red with hit list.
Public-line lexicon: neutral technical terms only (operator/user/orchestrator).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Fail CI if any of these match file content (case-insensitive unless noted).
FORBIDDEN_PATTERNS: list[tuple[str, str]] = [
    (r"bot_token", "secret-ish token field"),
    (r"api[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9_-]{8,}", "api key assignment"),
    (r"(?<![A-Za-z0-9_-])xai-[A-Za-z0-9_-]{8,}", "xai key-like token"),
    (r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{16,}", "sk- key-like token"),
    (r"8640\d{6}", "numeric chat-id-like fixture"),
    (r"C:\\\\AIWFF-C", "private machine root AIWFF-C"),
    (r"C:\\\\AIWFF(?!-)", "private machine root AIWFF"),
    (r"C:\\AIWFF-C", "private machine root AIWFF-C"),
    (r"C:\\AIWFF(?!-)", "private machine root AIWFF"),
    (r"AIWFF-C-TG-Bridge", "private schtask / service name"),
    (r"AIWFF-C-Tick", "private schtask name"),
    (r"HEART_TG_ON", "private control-plane flag"),
    (r"primary\s*promotion", "private ops term"),
    (r"\bSOUL\.md\b", "private identity file"),
    (r"TG_DIALOGUE_CONTRACT", "private contract name"),
    (r"captain_tg", "private source label"),
    (r"chat_id\s*=\s*['\"]?\d{8,}", "live-looking chat id"),
]

# Public-line lexicon (locked slice-3): neutral technical terms only
# (operator / user / orchestrator / owner). Soft hits warn; --soft-fail hardens.
SOFT_PATTERNS: list[tuple[str, str]] = [
    (r"\bcaptain\b", "prefer operator/owner lexicon"),
    (r"\bnode\s+[ABC]\b", "fleet topology language"),
    (r"\bmini[- ]?brain\b", "prefer neutral public product language"),
    (r"\bprimary\s*promotion\b", "private ops term (also hard-forbidden variant)"),
]

SKIP_DIR_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".pytest_basetemp",
    ".venv",
    "venv",
    "dist",
    "build",
    ".eggs",
    "node_modules",
    "task_ledger.egg-info",
    ".egg-info",
}
SKIP_SUFFIXES = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".zip"}
TEXT_SUFFIXES = {
    ".py",
    ".ps1",
    ".md",
    ".toml",
    ".txt",
    ".json",
    ".yml",
    ".yaml",
    ".ini",
    ".cfg",
    ".rst",
    "",
}


def iter_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIR_NAMES or part.endswith(".egg-info") for part in p.parts):
            continue
        if p.suffix.lower() in SKIP_SUFFIXES:
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES and p.suffix != "":
            # still scan common text-like without suffix filter if small
            if p.stat().st_size > 512_000:
                continue
        out.append(p)
    return out


def scan(root: Path, *, soft_fail: bool = False) -> tuple[list[str], list[str]]:
    hard: list[str] = []
    soft: list[str] = []
    hard_res = [(re.compile(p, re.I), label) for p, label in FORBIDDEN_PATTERNS]
    soft_res = [(re.compile(p, re.I), label) for p, label in SOFT_PATTERNS]

    for path in iter_files(root):
        # never scan this gate's own pattern table as a hit source incorrectly —
        # patterns include the forbidden strings by design; allow scripts/sanitize_gate.py
        rel = path.relative_to(root).as_posix()
        if rel in ("scripts/sanitize_gate.py", "scripts\\sanitize_gate.py"):
            continue
        if "SANITIZATION" in path.name.upper() and path.suffix.lower() == ".md":
            # checklist docs may mention patterns by name
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            hard.append(f"{rel}: read_fail {exc}")
            continue
        for cre, label in hard_res:
            for m in cre.finditer(text):
                # line number
                line_no = text.count("\n", 0, m.start()) + 1
                hard.append(f"{rel}:{line_no}: HARD [{label}] match={m.group(0)[:80]!r}")
        for cre, label in soft_res:
            for m in cre.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                soft.append(f"{rel}:{line_no}: SOFT [{label}] match={m.group(0)[:80]!r}")

    if soft_fail:
        hard.extend(soft)
        soft = []
    return hard, soft


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="task-ledger sanitization regex hard gate")
    ap.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Tree to scan (default: parent of scripts/)",
    )
    ap.add_argument(
        "--soft-fail",
        action="store_true",
        help="Treat soft lexicon hits as hard failures",
    )
    ap.add_argument("--json", action="store_true", help="Machine-readable summary")
    args = ap.parse_args(argv)

    root = args.root
    if root is None:
        root = Path(__file__).resolve().parent.parent
    root = root.resolve()

    hard, soft = scan(root, soft_fail=args.soft_fail)
    status = "GREEN" if not hard else "RED"
    summary = {
        "status": status,
        "root": str(root),
        "hard_hits": len(hard),
        "soft_hits": len(soft),
        "hard": hard,
        "soft": soft,
    }
    if args.json:
        import json

        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"sanitize_gate status={status} root={root}")
        print(f"hard_hits={len(hard)} soft_hits={len(soft)}")
        for h in hard:
            print(h)
        if soft and not hard:
            print("--- soft (warn only) ---")
            for s in soft:
                print(s)
        if status == "GREEN":
            print("PASS — sanitization regex hard gate green")
        else:
            print("FAIL — scrub hits before slice-4 publish gate")

    return 0 if not hard else 1


if __name__ == "__main__":
    sys.exit(main())
