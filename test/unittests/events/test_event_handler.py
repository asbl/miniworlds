from collections import defaultdict

from miniworlds.base.exceptions import MissingActorPartsError
from miniworlds.worlds.manager.event_handler import EventHandler


class Recorder:
    """Captures dispatcher callbacks so tests can assert exact event delivery."""

    def __init__(self):
        self.calls = []
        self.hovered = True

    def on_key_down(self, keys):
        self.calls.append(("key", tuple(keys)))

    def on_key_pressed(self, keys):
        self.calls.append(("key_pressed", tuple(keys)))

    def on_key_down_a(self):
        self.calls.append(("key_specific", None))

    def on_message_saved(self, message):
        self.calls.append(("message", message))

    def on_message(self, message):
        self.calls.append(("on_message", message))

    def on_mouse_middle_up(self, position):
        self.calls.append(("mouse_middle_up", position))

    def on_mouse_enter(self, position):
        self.calls.append(("mouse_enter", position))

    def on_mouse_leave(self, position):
        self.calls.append(("mouse_leave", position))

    def on_mouse_over(self, position):
        self.calls.append(("mouse_over", position))

    def detect_pixel(self, position):
        return self.hovered


class BrokenRecorder(Recorder):
    """Recorder variant that simulates actors with incomplete runtime state."""

    def __init__(self, actor_id=99):
        super().__init__()
        self.actor_id = actor_id

    def detect_pixel(self, position):
        raise MissingActorPartsError("missing parts")


def test_key_dispatch_calls_generic_and_specific_handlers(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder(
        {
            "on_key_down": {recorder.on_key_down},
            "on_key_down_a": {recorder.on_key_down_a},
        }
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_event("key_down_a", ["a"])

    assert recorder.calls == [("key", ("a",)), ("key_specific", None)]


def test_key_dispatch_supports_keys_with_underscores(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder({"on_key_pressed": {recorder.on_key_pressed}})
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_event("key_pressed_page_up", ["page_up"])

    assert recorder.calls == [("key_pressed", ("page_up",))]


def test_message_dispatch_uses_message_registry(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder(
        {"message": defaultdict(set, {"saved": {recorder.on_message_saved}})}
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_event("message", "saved")

    assert recorder.calls == [("message", "saved")]


def test_message_payload_is_forwarded_to_specific_handlers(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder(
        {"message": defaultdict(set, {"saved": {recorder.on_message_saved}})}
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_event("message", ("saved", {"file": "save.db"}))

    assert recorder.calls == [("message", {"file": "save.db"})]


def test_generic_on_message_receives_message_name_when_payload_exists(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder({"on_message": {recorder.on_message}})
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_event("message", ("saved", {"file": "save.db"}))

    assert recorder.calls == [("on_message", "saved")]


def test_message_dispatch_ignores_unknown_message_key_when_registry_is_specific(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder(
        {"message": defaultdict(set, {"saved": {recorder.on_message_saved}})}
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_event("message", "missing")

    assert recorder.calls == []


def test_middle_mouse_event_dispatches_to_registered_handler(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder(
        {"on_mouse_middle_up": {recorder.on_mouse_middle_up}}
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_event("mouse_middle_up", (4, 5))

    assert recorder.calls == [("mouse_middle_up", (4, 5))]


def test_can_handle_mouse_left_when_focus_handlers_are_registered(
    event_handler_world_builder,
    event_registry_builder,
):
    handler = EventHandler(
        event_handler_world_builder(),
        event_registry_builder({"on_focus": set()}),
    )

    assert handler.can_handle_event("on_mouse_left") is True


def test_can_handle_specific_key_event_when_generic_handler_is_registered(
    event_handler_world_builder,
    event_registry_builder,
):
    handler = EventHandler(
        event_handler_world_builder(),
        event_registry_builder({"on_key_pressed": set()}),
    )

    assert handler.can_handle_event("on_key_pressed_page_up") is True


def test_can_handle_mouse_motion_when_hover_handlers_are_registered(
    event_handler_world_builder,
    event_registry_builder,
):
    handler = EventHandler(
        event_handler_world_builder(),
        event_registry_builder({"on_mouse_leave": set()}),
    )

    assert handler.can_handle_event("on_mouse_motion") is True


def test_mouse_enter_and_leave_dispatch_registered_handlers(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder(
        {
            "on_mouse_enter": {recorder.on_mouse_enter},
            "on_mouse_leave": {recorder.on_mouse_leave},
        }
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_mouse_enter_event("on_mouse_motion", (2, 3))
    handler.handle_mouse_leave_event("on_mouse_motion", (4, 5))

    assert recorder.calls == [
        ("mouse_enter", (2, 3)),
        ("mouse_leave", (4, 5)),
    ]


def test_mouse_over_dispatch_handles_multiple_hover_actors(
    event_handler_world_builder,
    event_registry_builder,
):
    first = Recorder()
    second = Recorder()
    registry = event_registry_builder(
        {
            "on_mouse_over": {first.on_mouse_over, second.on_mouse_over},
            "on_mouse_enter": {first.on_mouse_enter, second.on_mouse_enter},
            "on_mouse_leave": {first.on_mouse_leave, second.on_mouse_leave},
        }
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))

    assert first.calls == [
        ("mouse_enter", (7, 8)),
        ("mouse_over", (7, 8)),
    ]
    assert second.calls == [
        ("mouse_enter", (7, 8)),
        ("mouse_over", (7, 8)),
    ]


def test_default_event_handler_keeps_payload_shape_for_all_listeners(
    event_handler_world_builder,
    event_registry_builder,
):
    first = Recorder()
    second = Recorder()
    registry = event_registry_builder({"on_custom": {first.on_message_saved, second.on_message_saved}})
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_event("custom", ["a"])

    assert first.calls == [("message", ["a"])]
    assert second.calls == [("message", ["a"])]


def test_mouse_over_enter_is_only_called_on_first_hover_frame(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder(
        {
            "on_mouse_over": {recorder.on_mouse_over},
            "on_mouse_enter": {recorder.on_mouse_enter},
        }
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))
    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))

    assert recorder.calls == [
        ("mouse_enter", (7, 8)),
        ("mouse_over", (7, 8)),
        ("mouse_over", (7, 8)),
    ]


def test_mouse_over_leave_is_only_called_once_when_hover_ends(
    event_handler_world_builder,
    event_registry_builder,
):
    recorder = Recorder()
    registry = event_registry_builder(
        {
            "on_mouse_over": {recorder.on_mouse_over},
            "on_mouse_enter": {recorder.on_mouse_enter},
            "on_mouse_leave": {recorder.on_mouse_leave},
        }
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))
    recorder.hovered = False
    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))
    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))

    assert recorder.calls == [
        ("mouse_enter", (7, 8)),
        ("mouse_over", (7, 8)),
        ("mouse_leave", (7, 8)),
    ]


def test_mouse_over_skips_incomplete_actor_and_continues_dispatch(
    event_handler_world_builder,
    event_registry_builder,
):
    broken = BrokenRecorder()
    healthy = Recorder()
    registry = event_registry_builder(
        {
            "on_mouse_over": {broken.on_mouse_over, healthy.on_mouse_over},
            "on_mouse_enter": {broken.on_mouse_enter, healthy.on_mouse_enter},
            "on_mouse_leave": {broken.on_mouse_leave, healthy.on_mouse_leave},
        }
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))

    assert broken.calls == []
    assert healthy.calls == [
        ("mouse_enter", (7, 8)),
        ("mouse_over", (7, 8)),
    ]


def test_mouse_over_cache_rebuilds_after_registry_change(
    event_handler_world_builder,
    event_registry_builder,
):
    first = Recorder()
    second = Recorder()
    registry = event_registry_builder(
        {
            "on_mouse_over": {first.on_mouse_over},
            "on_mouse_enter": {first.on_mouse_enter},
        }
    )
    handler = EventHandler(event_handler_world_builder(), registry)

    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))

    registry.registered_events["on_mouse_over"].add(second.on_mouse_over)
    registry.registered_events["on_mouse_enter"].add(second.on_mouse_enter)
    registry.change_counter += 1

    handler.handle_mouse_over_event("on_mouse_motion", (7, 8))

    assert second.calls == [
        ("mouse_enter", (7, 8)),
        ("mouse_over", (7, 8)),
    ]