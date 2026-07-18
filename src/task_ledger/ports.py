"""Adapter ports — engine-agnostic boundaries.

Core never imports a chat network client or a specific LLM CLI.
Production origins may wire real adapters; selftests use fakes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Protocol, runtime_checkable


@dataclass
class WorkUnit:
    """One durable work unit on the ledger."""

    task_id: str
    instruction: str
    kind: str = "task"
    origin: str = "operator"
    meta: Optional[dict[str, Any]] = None


@dataclass
class NotifyMessage:
    text: str
    channel_id: str = ""
    meta: Optional[dict[str, Any]] = None


@runtime_checkable
class NotifyPort(Protocol):
    """Outbound notification (chat, webhook, log). Optional at runtime."""

    def send(self, message: NotifyMessage) -> bool: ...


@runtime_checkable
class ChatIngressPort(Protocol):
    """Inbound operator text. Optional — core can be driven programmatically."""

    def poll(self) -> list[str]: ...


@runtime_checkable
class EnginePort(Protocol):
    """Worker engine that executes a WorkUnit body.

    Selftests MUST use a fake engine (no network, no API keys).
    Optional sample adapters may wrap an external CLI — never a hard dependency.
    """

    def run(self, unit: WorkUnit, work_dir: Path) -> dict[str, Any]: ...


@runtime_checkable
class FollowupCompletePort(Protocol):
    """Called when a deferred follow-up finishes — push must not evaporate."""

    def on_complete(self, task_id: str, result_text: str) -> bool: ...


@runtime_checkable
class ControlPlanePort(Protocol):
    """Optional control plane (HTTP heart, etc.). Not required for core use."""

    def health(self) -> dict[str, Any]: ...


class NullNotify:
    def send(self, message: NotifyMessage) -> bool:
        return True


class FakeEngine:
    """Scripted engine for offline selftests."""

    def __init__(self, body: str = "done", status: str = "PASS") -> None:
        self.body = body
        self.status = status
        self.calls: list[WorkUnit] = []

    def run(self, unit: WorkUnit, work_dir: Path) -> dict[str, Any]:
        self.calls.append(unit)
        return {
            "ok": True,
            "task_id": unit.task_id,
            "status": self.status,
            "result": self.body,
            "work_dir": str(work_dir),
        }
