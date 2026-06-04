"""Core miniworlds smoke tests executed inside Pyodide."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
import sys
import traceback

import pygame

from miniworlds import ActionTimer, Actor, App, LoopActionTimer, Rectangle, TiledWorld, World
from miniworlds.base.project_validator import IssueCode, ProjectValidator, Severity


def _reset() -> None:
    App.reset(unittest=True, file="/project/main.py")


def test_pixel_world_actor_and_costume() -> None:
    _reset()
    world = World(160, 120)
    actor = Actor((20, 30), world=world)
    actor.add_costume((255, 0, 0, 255))
    actor.size = (24, 18)
    actor.direction = 90
    actor.move(15)

    assert actor.position == (35, 30)
    assert actor.size == (24, 18)
    assert actor.costume is not None
    assert actor in world.actors


def test_collision_and_removal() -> None:
    _reset()
    world = World(160, 120)
    first = Rectangle((20, 20), 30, 30, world=world)
    second = Rectangle((35, 20), 30, 30, world=world)

    assert first.detect_actor_at() is second
    second.remove()
    assert second not in world.actors


def test_tiled_world_movement_and_detection() -> None:
    _reset()
    world = TiledWorld(6, 5)
    player = Actor((1, 2), world=world)
    target = Actor((3, 2), world=world)
    player.direction = 90
    player.move(distance=2)

    assert player.position == (3, 2)
    assert target in world.detect_actors((3, 2))
    player.undo_move()
    assert player.position == (1, 2)


def test_uploaded_project_supports_local_modules_and_data_files() -> None:
    _reset()
    sys.modules.pop("student_helper", None)
    helper = importlib.import_module("student_helper")
    levels = json.loads(Path("data/levels.json").read_text(encoding="utf-8"))

    assert Path.cwd() == Path("/project")
    assert helper.START_POSITION == (24, 36)
    assert helper.move_distance() == 12
    assert levels["start"] == "school-yard"
    assert levels["levels"][-1] == "library"


def test_nested_package_and_unicode_text_survive_upload() -> None:
    _reset()
    sys.modules.pop("game", None)
    game = importlib.import_module("game")
    dialog = Path("data/dialog_de.txt").read_text(encoding="utf-8").strip()

    assert game.PLAYER_NAME == "Ada"
    assert dialog == "Willkommen in der Schüler-Welt!"


def test_relative_image_paths_and_extension_lookup() -> None:
    _reset()
    world = World(160, 120)
    explicit = Actor((10, 10), world=world)
    extensionless = Actor((40, 10), world=world)
    leading_slash = Actor((70, 10), world=world)

    explicit.add_costume("images/player.png")
    extensionless.add_costume("player")
    leading_slash.add_costume("/images/player.png")

    assert explicit.costume.get_image().get_size() == (40, 40)
    assert extensionless.costume.get_image().get_size() == (40, 40)
    assert leading_slash.costume.get_image().get_size() == (40, 40)


def test_multiple_uploaded_images_can_be_switched_and_animated() -> None:
    _reset()
    world = World(160, 120)
    actor = Actor((10, 10), world=world)
    costume = actor.add_costume(["images/player.png", "images/ball.png"])

    assert len(costume.image_manager.images_list) == 2
    assert costume.set_image(1)
    assert costume.image_manager.image_index == 1
    assert costume.get_image().get_size() == (40, 40)
    costume.animate(loop=True)
    assert costume.is_animated
    assert costume.loop


def test_missing_case_sensitive_and_desktop_paths_fail_clearly() -> None:
    _reset()
    world = World(160, 120)
    actor = Actor((10, 10), world=world)

    for invalid_path in (
        "images/Player.png",
        "images/not-uploaded.png",
        "C:\\Users\\student\\Pictures\\player.png",
    ):
        try:
            actor.add_costume(invalid_path)
        except Exception as error:
            message = str(error)
            assert invalid_path in message or "File" in message
        else:
            raise AssertionError(f"Invalid browser path unexpectedly loaded: {invalid_path}")


def test_project_validator_reports_typical_web_export_problems() -> None:
    issues = ProjectValidator(Path("/project"), Path("/project/main.py")).validate()
    issue_codes = {issue.code for issue in issues}
    web_errors = {issue.code for issue in issues if issue.web_severity == Severity.ERROR}

    assert IssueCode.PROBLEMATIC_IMPORT in web_errors
    assert IssueCode.ABSOLUTE_PATH in web_errors
    assert IssueCode.FILE_WRITE_IO in issue_codes
    assert IssueCode.UNSUPPORTED_IMAGE_FORMAT in issue_codes


def test_reset_and_reload_of_uploaded_assets() -> None:
    _reset()
    first_world = World(100, 80)
    first_actor = Actor((10, 10), world=first_world)
    first_actor.add_costume("images/player.png")

    _reset()
    second_world = World(100, 80)
    second_actor = Actor((10, 10), world=second_world)
    second_actor.add_costume("images/player.png")

    assert second_actor.costume.get_image().get_size() == (40, 40)


async def test_timers_fire_during_browser_frame_updates() -> None:
    _reset()
    world = World(100, 80)
    calls = []
    ActionTimer(2, lambda: calls.append("once"))
    loop_timer = LoopActionTimer(2, lambda: calls.append("loop"))
    world.app.platform.poll_events = lambda: []
    world.app.platform.get_mouse_pos = lambda: (0, 0)

    for _ in range(5):
        await world.app._update()

    loop_timer.unregister()
    assert calls.count("once") == 1
    assert calls.count("loop") == 2


async def test_event_dispatch() -> None:
    _reset()

    class MessageWorld(World):
        def __init__(self):
            self.messages = []
            super().__init__(120, 80)

        def on_message(self, message):
            self.messages.append(message)

    world = MessageWorld()
    world.send_message("pyodide-message")
    world.app.platform.poll_events = lambda: []
    world.app.platform.get_mouse_pos = lambda: (0, 0)
    await world.app._update()

    assert world.messages == ["pyodide-message"]


async def test_browser_keyboard_event_reaches_student_handler() -> None:
    _reset()

    class KeyboardWorld(World):
        def __init__(self):
            self.keys = []
            super().__init__(120, 80)

        def on_key_down(self, keys):
            self.keys.extend(keys)

    world = KeyboardWorld()
    events = [pygame.event.Event(pygame.KEYDOWN, {"unicode": "a", "key": pygame.K_a})]
    world.app.platform.poll_events = lambda: events
    world.app.platform.get_mouse_pos = lambda: (0, 0)
    await world.app._update()

    assert "a" in world.keys


async def test_browser_mouse_click_and_wheel_reach_student_handlers() -> None:
    _reset()

    class MouseWorld(World):
        def __init__(self):
            self.events = []
            super().__init__(120, 80)

        def on_mouse_left_down(self, position):
            self.events.append(("left_down", position))

        def on_mouse_left_up(self, position):
            self.events.append(("left_up", position))

        def on_wheel_up(self, position):
            self.events.append(("wheel_up", position))

    world = MouseWorld()
    events = [
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (12, 15)}),
        pygame.event.Event(pygame.MOUSEBUTTONUP, {"button": 1, "pos": (12, 15)}),
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 4, "pos": (12, 15)}),
    ]
    world.app.platform.poll_events = lambda: events
    world.app.platform.get_mouse_pos = lambda: (12, 15)
    await world.app._update()

    assert ("left_down", (12, 15)) in world.events
    assert ("left_up", (12, 15)) in world.events
    assert ("wheel_up", (12, 15)) in world.events


async def test_screenshot_writes_to_virtual_browser_filesystem() -> None:
    _reset()
    output = Path("/project/student-screenshot.png")
    output.unlink(missing_ok=True)
    world = World(96, 64)
    world.add_background((15, 25, 35))
    world.app.platform.poll_events = lambda: []
    world.app.platform.get_mouse_pos = lambda: (0, 0)
    await world.app._update()
    world.screenshot(str(output))

    assert output.is_file()
    assert output.read_bytes().startswith(b"\x89PNG")
    output.unlink()


def test_missing_sound_reports_export_problem_without_crashing_app() -> None:
    _reset()
    world = World(100, 80)

    try:
        world.sound.play("sounds/not-uploaded.wav")
    except Exception as error:
        assert "sound" in str(error).lower() or "file" in str(error).lower()
    else:
        raise AssertionError("Missing browser sound unexpectedly played")

    assert world.app.running_world is world


async def test_world_run_schedules_inside_pyodide_loop() -> None:
    _reset()
    world = World(128, 96)
    app_run_called = False

    async def fake_app_run(*args, **kwargs):
        nonlocal app_run_called
        app_run_called = True

    world.app.run = fake_app_run
    world.run()
    await asyncio.sleep(0)

    assert app_run_called


async def test_web_frame_updates_and_canvas_rendering() -> None:
    _reset()
    world = World(128, 96)
    world.add_background((10, 20, 30))
    actor = Rectangle((20, 20), 30, 20, world=world)
    actor.fill_color = (220, 40, 50)
    yielded_frames = 0

    async def count_yield():
        nonlocal yielded_frames
        yielded_frames += 1
        await asyncio.sleep(0)

    world.app.platform.yield_mainloop = count_yield
    world.app.prepare_mainloop()
    world.backgrounds._init_display()
    world._mainloop.dirty_all()
    for _ in range(3):
        await world.app._update()

    assert world.app.platform.is_web()
    assert yielded_frames >= 3
    assert world.frame >= 3
    assert pygame.display.get_surface() is not None
    assert all(size > 0 for size in pygame.display.get_surface().get_size())
    assert world.background.surface.get_size() == (128, 96)


TESTS = [
    test_pixel_world_actor_and_costume,
    test_collision_and_removal,
    test_tiled_world_movement_and_detection,
    test_uploaded_project_supports_local_modules_and_data_files,
    test_nested_package_and_unicode_text_survive_upload,
    test_relative_image_paths_and_extension_lookup,
    test_multiple_uploaded_images_can_be_switched_and_animated,
    test_missing_case_sensitive_and_desktop_paths_fail_clearly,
    test_project_validator_reports_typical_web_export_problems,
    test_reset_and_reload_of_uploaded_assets,
    test_timers_fire_during_browser_frame_updates,
    test_event_dispatch,
    test_browser_keyboard_event_reaches_student_handler,
    test_browser_mouse_click_and_wheel_reach_student_handlers,
    test_screenshot_writes_to_virtual_browser_filesystem,
    test_missing_sound_reports_export_problem_without_crashing_app,
    test_world_run_schedules_inside_pyodide_loop,
    test_web_frame_updates_and_canvas_rendering,
]


def _report_progress(name: str) -> None:
    try:
        from js import window
    except ImportError:
        return
    window.pyodideTestProgress = name


async def run_suite() -> str:
    results = []
    for test in TESTS:
        _report_progress(test.__name__)
        try:
            result = test()
            if asyncio.iscoroutine(result):
                await asyncio.wait_for(result, timeout=15)
        except Exception:
            results.append(
                {
                    "name": test.__name__,
                    "status": "failed",
                    "traceback": traceback.format_exc(),
                }
            )
        else:
            results.append({"name": test.__name__, "status": "passed"})
        finally:
            _reset()

    _report_progress("finished")
    failed = sum(result["status"] == "failed" for result in results)
    return json.dumps(
        {
            "status": "failed" if failed else "passed",
            "passed": len(results) - failed,
            "failed": failed,
            "results": results,
        }
    )
