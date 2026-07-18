"""Atomic text writes — temp file in same directory, then replace.

Survives process kill mid-write better than open+write on a live path.
Windows-safe: uses Path.replace (os.replace under the hood).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path


def atomic_write_text(
    path: Path | str,
    text: str,
    *,
    encoding: str = "utf-8",
    newline: str | None = "\n",
) -> Path:
    """Write *text* to *path* via same-dir temp + os.replace.

    Creates parent directories. Returns the final Path.
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # NamedTemporaryFile(delete=False) so we can replace after close (Windows).
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{dest.name}.",
        suffix=".tmp",
        dir=str(dest.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline=newline) as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp_path), str(dest))
    except Exception:
        try:
            if tmp_path.is_file():
                tmp_path.unlink()
        except OSError:
            pass
        raise
    return dest
