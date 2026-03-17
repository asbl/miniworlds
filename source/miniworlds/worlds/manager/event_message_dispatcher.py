from __future__ import annotations

from typing import Any

import miniworlds.tools.method_caller as method_caller


class EventMessageDispatcher:
    """Dispatches message events via exact message routes before falling back to generic handlers."""

    def __init__(self, event_registry):
        self.event_registry = event_registry

    def dispatch(self, event: str, data: Any) -> None:
        message = data
        payload = None
        if isinstance(data, tuple) and len(data) == 2:
            message, payload = data

        message_methods = self.event_registry.copy_message_methods(message)
        if message_methods:
            handler_data = message if payload is None else payload
            for method in message_methods:
                method_caller.call_method(method, (handler_data,))
            return

        for method in self.event_registry.copy_generic_message_methods():
            if event == method.__name__:
                method_caller.call_method(method, (message,))