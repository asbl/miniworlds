"""Contracts used by IDE backends, independent of Thonny's UI."""
import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from miniworlds.worlds.manager.mainloop_manager import MainloopManager
from miniworlds.worlds.world_runtime_facade import WorldRuntimeFacade
from miniworlds.tools.experiment import ExperimentSession
from miniworlds.base.manager.app_event_manager import AppEventManager


def runtime():
    world = SimpleNamespace(is_running=True, refresh=MagicMock())
    facade = WorldRuntimeFacade(world)
    return world, facade


def test_invoke_returns_result_and_stays_paused_even_if_callback_starts_world():
    world, facade = runtime()
    def callback(value):
        facade.start()
        return value + 1
    assert facade.invoke(callback, 4) == 5
    assert facade.is_paused and not world.is_running
    world.refresh.assert_called_once()
    facade.resume()
    assert not facade.is_paused and world.is_running


def test_invoke_error_preserves_changes_and_refreshes():
    world, facade = runtime()
    def callback():
        world.changed = True
        raise ValueError('example')
    with pytest.raises(ValueError, match='example'):
        facade.invoke(callback)
    assert world.changed and facade.is_paused and not world.is_running
    world.refresh.assert_called_once()


def test_pause_at_frame_zero_never_advances_simulation():
    world = MagicMock(is_paused=True, frame=0, fps=60)
    manager = MainloopManager(world, MagicMock())
    assert asyncio.run(manager.update()) == 1 / 60
    assert world.frame == 0
    world.event_manager.act_all.assert_not_called()
    world.event_manager.update.assert_called_once()
    world._collision_manager._handle_all_collisions.assert_not_called()
    world.background.update.assert_not_called()


def test_refresh_does_not_animate_or_tick():
    actor = MagicMock()
    world = MagicMock(actors=[actor])
    app = MagicMock()
    manager = MainloopManager(world, app)
    manager.refresh()
    actor.costume.get_image.assert_called_once()
    actor.costume.update.assert_not_called()
    world.background.update.assert_not_called()
    world._collision_manager._handle_all_collisions.assert_not_called()
    app.display_repaint.assert_called_once()


def test_paused_world_drops_game_events_while_other_world_receives_them():
    paused = MagicMock(is_paused=True, is_listening=True)
    running = MagicMock(is_paused=False, is_listening=True)
    app = SimpleNamespace(worlds_manager=SimpleNamespace(worlds=[paused, running]))
    manager = AppEventManager(app)
    manager.to_event_queue('key_down', ['a'])
    manager.handle_event_queue()
    paused._mainloop.handle_event.assert_not_called()
    running._mainloop.handle_event.assert_called_once_with('key_down', ['a'])
    assert not manager.event_queue


def test_versions_and_handles_are_bound_to_loaded_generation():
    world = MagicMock()
    session = ExperimentSession(world, 'v1')
    obj = SimpleNamespace(move=MagicMock())
    handle = session.register(obj)
    session.mark_source_changed('v2')
    assert session.describe(handle)['is_stale']
    assert session.describe(handle)['loaded_version'] == 'v1'
    session.invoke(handle, 'move', 10)
    world.invoke.assert_called_once_with(obj.move, 10)
    session.mark_source_changed('v1')
    assert not session.is_stale
    session.close()
    with pytest.raises(RuntimeError):
        session.resolve(handle)
    replacement = ExperimentSession(world, 'v2')
    with pytest.raises(KeyError):
        replacement.resolve(handle)


def test_real_world_refresh_moves_actor_without_advancing_time():
    from miniworlds import App, World, Actor

    App.reset(unittest=True, file=__file__)
    try:
        world = World(100, 100)
        actor = Actor((10, 10))
        actor.size = (10, 10)
        actor.fill_color = (255, 0, 0)
        world.pause()
        world.refresh()
        frame = world.frame
        world.invoke(setattr, actor, 'position', (40, 40))
        assert world.frame == frame
        assert world.is_paused and not world.is_running
        assert world.background.surface.get_at((40, 40))[:3] == (255, 0, 0)
        assert world.background.surface.get_at((10, 10))[:3] != (255, 0, 0)
        asyncio.run(world._mainloop.update())
        assert world.frame == frame
    finally:
        App.reset()


def test_invoke_rejects_foreign_thread_before_mutating_world():
    from concurrent.futures import ThreadPoolExecutor
    world, facade = runtime()
    callback = MagicMock()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with pytest.raises(RuntimeError, match='thread'):
            pool.submit(facade.invoke, callback).result()
    callback.assert_not_called()
    assert world.is_running


def test_invoke_rejects_async_callback():
    world, facade = runtime()
    async def callback():
        pass
    with pytest.raises(TypeError, match='synchronous'):
        facade.invoke(callback)



def test_paused_toolbar_does_not_update_timed_widgets():
    from miniworlds.worlds.gui.toolbar_mainloop_manager import ToolbarMainloopManager

    widget = MagicMock()
    world = MagicMock(is_paused=True, fps=60, timed_widgets=[widget])
    manager = ToolbarMainloopManager(world, MagicMock())
    assert asyncio.run(manager.update()) == 1 / 60
    widget.update.assert_not_called()


def test_invoke_preserves_student_error_if_rendering_also_fails():
    world, facade = runtime()
    world.refresh.side_effect = RuntimeError('render failed')
    def callback():
        raise ValueError('student error')
    with pytest.raises(ValueError, match='student error') as caught:
        facade.invoke(callback)
    assert isinstance(caught.value.__cause__, RuntimeError)
    assert str(caught.value.__cause__) == 'render failed'
    assert facade.is_paused and not world.is_running


def test_successful_invoke_propagates_rendering_error():
    world, facade = runtime()
    world.refresh.side_effect = RuntimeError('render failed')
    with pytest.raises(RuntimeError, match='render failed'):
        facade.invoke(lambda: 42)
    assert facade.is_paused and not world.is_running


def test_resume_delivers_first_key_event_after_pause_inside_handler():
    from miniworlds import App, World

    App.reset(unittest=True, file=__file__)
    try:
        world = World(100, 100)
        calls = []
        @world.register
        def on_key_down(self, keys):
            calls.append(keys)
            self.pause()
        world.app.event_manager.to_event_queue('key_down', ['a'])
        world.app.event_manager.handle_event_queue()
        asyncio.run(world._mainloop.update())
        world.resume()
        world.app.event_manager.to_event_queue('key_down', ['b'])
        world.app.event_manager.handle_event_queue()
        assert calls == [['a'], ['b']]
    finally:
        App.reset()


def test_step_runs_exactly_n_frames_and_stays_paused():
    world = MagicMock(is_paused=True, is_running=False, frame=3, fps=60, tick_rate=1)
    facade = WorldRuntimeFacade(world)
    world._runtime_facade = facade
    manager = MainloopManager(world, MagicMock())
    facade.step(2)
    for _ in range(4):
        asyncio.run(manager.update())
    assert world.frame == 5  # only the two queued frames advanced
    assert world.event_manager.act_all.call_count == 2
    assert facade._pending_steps == 0


def test_step_rejects_invalid_frame_counts():
    _, facade = runtime()
    for bad in (0, -1, 1.5, True, "2"):
        with pytest.raises(ValueError):
            facade.step(bad)


def test_resume_discards_queued_steps():
    _, facade = runtime()
    facade.step(5)
    facade.resume()
    assert facade._pending_steps == 0 and not facade.is_paused
