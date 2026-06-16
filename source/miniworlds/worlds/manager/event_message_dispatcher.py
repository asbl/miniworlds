from __future__ import annotations

from typing import Any

import miniworlds.tools.method_caller as method_caller


def _iter_message_methods(event_registry, message: str):
    iter_message_methods = getattr(event_registry, "iter_message_methods", None)
    if callable(iter_message_methods):
        return iter_message_methods(message)
    return tuple(event_registry.copy_message_methods(message))


def _iter_generic_message_methods(event_registry):
    iter_generic_message_methods = getattr(
        event_registry,
        "iter_generic_message_methods",
        None,
    )
    if callable(iter_generic_message_methods):
        return iter_generic_message_methods()
    return tuple(event_registry.copy_generic_message_methods())


class EventMessageDispatcher:
    """Dispatches message events via exact message routes before falling back to generic handlers."""

    def __init__(self, event_registry):
        self.event_registry = event_registry

    def dispatch(self, event: str, data: Any) -> None:
        message = data
        payload = None
        if isinstance(data, tuple) and len(data) == 2:
            message, payload = data

        message_methods = _iter_message_methods(self.event_registry, message)
        if message_methods:
            handler_data = message if payload is None else payload
            for method in message_methods:
                method_caller.call_method(method, (handler_data,))
            return

        for method in _iter_generic_message_methods(self.event_registry):
            if event == method.__name__:
                method_caller.call_method(method, (message,))
