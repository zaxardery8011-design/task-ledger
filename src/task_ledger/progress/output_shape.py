"""Output shape helpers — protect task_id lines from casual rewrites."""

from __future__ import annotations

import re

_TASK_ID_LINE = re.compile(r"(?im)^(.*\btask_id\s*=\s*[a-zA-Z0-9_.-]+.*)$")


def protect_task_id_lines(text: str) -> list[str]:
    """Return lines that must survive formatting (receipt discipline)."""
    if not text:
        return []
    return [m.group(1).strip() for m in _TASK_ID_LINE.finditer(text)]
