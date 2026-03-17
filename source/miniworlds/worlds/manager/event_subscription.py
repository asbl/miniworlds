from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal, Optional


SubscriptionKind = Literal["event", "message", "sensor"]


@dataclass(frozen=True)
class EventSubscription:
    """Captures one restorable event binding for world-transfer safe re-registration."""

    kind: SubscriptionKind
    event_name: str
    method: Callable
    route_key: Optional[str] = None

    @classmethod
    def event(cls, event_name: str, method: Callable) -> "EventSubscription":
        return cls("event", event_name, method)

    @classmethod
    def message(cls, message: str, method: Callable) -> "EventSubscription":
        return cls("message", "message", method, message)

    @classmethod
    def sensor(cls, target: str, method: Callable) -> "EventSubscription":
        return cls("sensor", "sensor", method, target)