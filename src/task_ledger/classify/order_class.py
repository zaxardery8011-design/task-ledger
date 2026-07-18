"""Order classification — pure functions, no network, no machine paths.

Extracted substance (knife-1): operator text → kind + should_enqueue.
De-identified: no fleet node labels, no private product paths.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class OrderClass:
    kind: str
    note: str = ""
    should_enqueue: bool = False
    needs_confirm: bool = False
    is_standing_rule: bool = False
    is_progress_push: bool = False


_STOP = re.compile(
    r"(?i)(^\s*stop\b|^\s*halt\b|^\s*停\s*$|停止全部|全部停|hard\s*stop)"
)
_VAGUE_ACK = re.compile(
    r"(?i)^(ok|okay|好|好的|收到|了解|嗯|繼續|继续|go)[\s!！。\.]*$"
)
_GREETING = re.compile(
    r"(?i)^(哈+|嗨|hi|hello|在嗎|早安|午安|晚安)[\s!！。\.]*$"
)
_CONFIRM = re.compile(r"^(確認|是|對|做吧|confirm)[\s!！。\.]*$")
_CONFIRM_START = re.compile(r"^(開始|开始)[\s!！。\.]*$")
_PROGRESS_PUSH = re.compile(
    r"(?i)(進度推進|进度推进|progress\s*push|推進進度|推进进度|做下一刀|下一刀|next\s*knife|繼續推進|继续推进)"
)
_STANDING_RULE = re.compile(
    r"(?i)(standing\s*rule|常駐規則|以後都|今后都|from\s*now\s*on)"
)
_STATUS = re.compile(
    r"(?i)(現在什麼情況|什麼情況|待辦|status|現況|現在怎樣|"
    r"做到哪|到哪了|多遠了|現況如何|狀態呢|怎麼樣了|人呢|佇列|\bqueue\b|"
    r"進度呢|進度表|進度怎|進度如何|現在進度|查.*進度|看.*進度|\bprogress\b)"
)
_EXEC_HEAD = re.compile(
    r"(?i)^(請|然后|然後|再)?"
    r"(立刻|馬上|現在|先|再|然后|然後)?"
    r"(修|查|做|派|蓋|清|寫|改|實作|實裝|補|接|跑|執行|执行|開始|开始|"
    r"繼續|继续|準備|准备|推進|推进|搞定|處理|整理|歸檔|合併|建|加|刪|移|"
    r"更新|部署|實測|驗收|入單|接上|產出|產生|"
    r"consolidate|implement|fix|build|write|create|merge|archive)"
)
_EXEC_EMBED = re.compile(
    r"(?i)(把.{1,40}(修好|做完|蓋好|清掉|整理|歸檔|合併|寫進|寫入)|"
    r"請(立刻|馬上)?(修|做|蓋|清|派|寫|改|實作|接|準備|推进|推進)|"
    r"下一刀|下一步|下一個|下一个|立刻派|必入單|command-must-become|"
    r"開工|开工|動第一刀|開始刀|继续改|繼續改|do the next)"
)
_SOFT = re.compile(r"(要|必須|应该|應該|幫我|給我|麻煩)")
_LEAD_VERB = re.compile(
    r"^(請|然后|然後|再|先)?(立刻|馬上|現在|先|再|然后|然後)?"
    r"(修|查|做|派|蓋|清|寫|改|實作|實裝|補|接|跑|執行|执行|開始|开始|"
    r"繼續|继续|準備|准备|推進|推进|搞定|處理|整理|歸檔|合併|建|加|刪|移|"
    r"更新|部署|實測|驗收|入單|接上)"
)


def is_status_probe(text: str) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    if _PROGRESS_PUSH.search(t):
        return False
    if _STANDING_RULE.search(t):
        return False
    if re.match(r"^(繼續|继续)[\s!！。\.]*$", t):
        return False
    if _STATUS.search(t):
        return True
    if re.search(r"(?i)進度", t) and re.search(r"(呢|嗎|？|\?|怎樣|怎麼|哪|遠|表|狀況|状况)$", t):
        return True
    if len(t) <= 24 and re.search(r"(呢|嗎|？|\?)$", t) and re.search(
        r"(進度|狀態|現況|怎樣|怎麼|哪|遠)", t
    ):
        return True
    return False


def classify_order(text: str, chat_state: Optional[dict] = None) -> OrderClass:
    """Classify operator text into a command class.

    kind: stop | status_probe | vague_ack | greeting | confirm |
          execution_order | needs_confirm | rule_set | chat
    """
    del chat_state  # reserved for lock-aware callers
    t = (text or "").strip()
    if not t:
        return OrderClass(kind="chat", note="empty")

    if _STOP.search(t):
        return OrderClass(kind="stop", note="stop_order")
    if _VAGUE_ACK.match(t):
        return OrderClass(kind="vague_ack", note="vague_ack_not_auth")
    if _GREETING.match(t):
        return OrderClass(kind="greeting", note="greeting_only")
    if _CONFIRM.match(t):
        return OrderClass(kind="confirm", note="explicit_confirm", should_enqueue=True)
    if _CONFIRM_START.match(t):
        return OrderClass(
            kind="confirm", note="explicit_confirm_start", should_enqueue=True
        )

    has_standing = bool(_STANDING_RULE.search(t))
    has_progress = bool(_PROGRESS_PUSH.search(t))

    if has_progress:
        return OrderClass(
            kind="execution_order",
            note="progress_push_order",
            should_enqueue=True,
            is_progress_push=True,
            is_standing_rule=has_standing,
        )

    if is_status_probe(t):
        return OrderClass(
            kind="status_probe",
            note="status_or_progress_query",
            is_standing_rule=has_standing,
            is_progress_push=has_progress,
        )

    if has_standing:
        return OrderClass(
            kind="rule_set",
            note="standing_rule_persist",
            should_enqueue=False,
            is_standing_rule=True,
        )

    lead = bool(_LEAD_VERB.match(t))
    if t.endswith(("?", "？")) and not lead and not has_progress:
        if re.search(r"(修|做|蓋|清|派|寫|改|實作|部署|推進|准备|準備)", t):
            return OrderClass(
                kind="needs_confirm",
                note="question_with_work_hint",
                needs_confirm=True,
            )
        return OrderClass(kind="status_probe", note="question_mark_query")

    if _EXEC_HEAD.match(t) or _EXEC_EMBED.search(t):
        return OrderClass(
            kind="execution_order",
            note="progress_push_order" if has_progress else "imperative_work_verb",
            should_enqueue=True,
            is_progress_push=has_progress,
        )

    if len(t) >= 16 and _SOFT.search(t):
        return OrderClass(
            kind="needs_confirm",
            note="soft_request_needs_confirm",
            needs_confirm=True,
        )

    return OrderClass(kind="chat", note="normal_chat")
