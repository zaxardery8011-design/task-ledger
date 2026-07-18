"""Small shared utilities (atomic IO, path safety)."""

from __future__ import annotations

from task_ledger.util.atomic import atomic_write_text

__all__ = ["atomic_write_text"]
