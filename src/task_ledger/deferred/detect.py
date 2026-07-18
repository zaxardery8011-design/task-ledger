"""Deferred promise detection — promises must not evaporate.

If the assistant says "I'll check" without substance, same-turn enqueue a follow-up.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


_ORDER_ACK = re.compile(
    r"(?i)(work order queued:\s*task_id=|Queued,\s*task_id=|已入單[^\n]*task_id\s*=)"
)
_SUBSTANCE = re.compile(
    r"(?i)(docs[/\\]|outbox|LastWriteTime|/api/health|quality_ok|## |"
    r"\|.+\|.+\||row\d|\d+\s*%|\d+%|hard-path\s*=|Progress hard table)"
)
_DEFERRED = re.compile(
    r"(?i)(我來查|我去查|我查一下|先查|稍後回報|稍後報告|等下回|等下報|回頭報|"
    r"會回報|接著會|先確認|立刻派工|下一刀|"
    r"let me check|i.?ll check|i will check|checking\b|looking up|"
    r"will report|report back|稍候|先看一下再|稍後給|等我查)"
)
_LOOKUP = re.compile(
    r"(?i)(進度|多遠|到哪|現況|狀態|表呢|人呢|怎麼樣|怎麼了|查一下|看一下|讀一下|"
    r"how far|status|progress|queue|佇列|卡在|卡住|結果呢|回報呢)"
)
_GREETING = re.compile(r"(?i)^(哈+|嗨|hi|hello|在嗎|早安|午安|晚安)[\s!！。\.]*$")


@dataclass(frozen=True)
class DeferredDecision:
    should: bool
    reason: str
    deferred: bool = False
    need_lookup: bool = False
    orphan: bool = False


def is_deferred_promise(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if _ORDER_ACK.search(t):
        return False
    if _SUBSTANCE.search(t):
        return False
    if _DEFERRED.search(t):
        return True
    if len(t) <= 40 and re.search(r"(?i)(進度|查|報|派工|確認|先)", t):
        if not re.search(
            r"(?i)(docs[/\\]|outbox|LastWriteTime|PASS|FAIL|PARTIAL|/api/|%\s*\||\d+%|row\d)",
            t,
        ):
            return True
    return False


def is_lookup_need(text: str) -> bool:
    t = (text or "").strip()
    if not t or _GREETING.match(t):
        return False
    if _LOOKUP.search(t):
        return True
    if len(t) <= 24 and re.search(r"[?？呢嗎]$", t):
        return True
    return False


def is_orphan_ack(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if _SUBSTANCE.search(t):
        return False
    if len(t) <= 120:
        return True
    if re.search(r"(?i)(我來|稍後|checking|先.*再|立刻派)", t) and not re.search(r"\d{2,}", t):
        return True
    return False


def deferred_flag_off(root: Optional[Path]) -> bool:
    if root is None:
        return False
    root = Path(root)
    return (root / "flags" / "DEFERRED_OFF.flag").is_file() or (
        root / "flags" / "FOLLOWUP_OFF.flag"
    ).is_file()


def should_enqueue_deferred(
    operator_text: str,
    assistant_text: str,
    root: Optional[Path] = None,
) -> DeferredDecision:
    if deferred_flag_off(root):
        return DeferredDecision(should=False, reason="link_off")

    deferred = is_deferred_promise(assistant_text)
    need = is_lookup_need(operator_text)
    orphan = is_orphan_ack(assistant_text)

    if deferred:
        return DeferredDecision(
            should=True,
            reason="deferred_promise",
            deferred=True,
            need_lookup=need,
            orphan=orphan,
        )
    if need and orphan:
        return DeferredDecision(
            should=True,
            reason="lookup_orphan_ack",
            deferred=False,
            need_lookup=True,
            orphan=True,
        )
    return DeferredDecision(
        should=False,
        reason="no_gap",
        deferred=deferred,
        need_lookup=need,
        orphan=orphan,
    )
