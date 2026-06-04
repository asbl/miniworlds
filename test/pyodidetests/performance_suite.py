"""Everyday miniworlds performance measurements executed inside Pyodide."""

from __future__ import annotations

import asyncio
import json
import statistics
import time
import traceback

from miniworlds import Actor, App, Rectangle, World


def _reset() -> None:
    App.reset(unittest=True, file="/project/main.py")


def _measurement(name: str, elapsed: float, operations: int) -> dict:
    return {
        "name": name,
        "elapsed_ms": round(elapsed * 1000, 4),
        "operations": operations,
        "operations_per_s": round(operations / elapsed, 4),
    }


class EverydayActor(Actor):
    def act(self) -> None:
        return None

    def on_message(self, message: str) -> None:
        return None


def benchmark_actor_lifecycle() -> list[dict]:
    _reset()
    world = World(320, 240)
    actor_count = 80

    start = time.perf_counter()
    actors = [
        EverydayActor(((index * 17) % 300, (index * 29) % 220), world=world)
        for index in range(actor_count)
    ]
    creation_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for actor in actors:
        actor.remove()
    removal_elapsed = time.perf_counter() - start

    assert not world.actors
    return [
        _measurement("pyodide actor creation", creation_elapsed, actor_count),
        _measurement("pyodide actor removal", removal_elapsed, actor_count),
    ]


def benchmark_world_queries() -> list[dict]:
    _reset()
    world = World(320, 240)
    for row in range(6):
        for column in range(8):
            Rectangle((10 + column * 25, 10 + row * 25), 18, 18, world=world)

    iterations = 1000
    positions = [
        (10 + (index % 8) * 25, 10 + (index % 6) * 25)
        for index in range(iterations)
    ]
    world.camera.get_actors_in_view()

    start = time.perf_counter()
    hits = sum(len(world.detect_actors(position)) for position in positions)
    elapsed = time.perf_counter() - start

    assert hits >= iterations
    return [_measurement("pyodide world queries", elapsed, iterations)]


def benchmark_event_communication() -> list[dict]:
    _reset()
    world = World(320, 240)
    for index in range(20):
        EverydayActor(((index * 17) % 300, (index * 29) % 220), world=world)

    iterations = 2000
    handler = world.event_manager.handler
    start = time.perf_counter()
    for _ in range(iterations):
        handler.handle_event("message", "ping")
        handler.executed_events.clear()
    elapsed = time.perf_counter() - start

    return [_measurement("pyodide message broadcasts", elapsed, iterations)]


async def benchmark_canvas_frame_updates() -> list[dict]:
    _reset()
    world = World(320, 240)
    world.add_background((20, 30, 40))
    for row in range(6):
        for column in range(8):
            actor = Rectangle((10 + column * 25, 10 + row * 25), 18, 18, world=world)
            actor.fill_color = (40, 130, 210)
            actor.static = True

    moving_actor = Rectangle((10, 220), 18, 18, world=world)
    moving_actor.fill_color = (240, 180, 30)
    world.app.platform.poll_events = lambda: []
    world.app.platform.get_mouse_pos = lambda: (0, 0)

    async def yield_without_delay():
        await asyncio.sleep(0)

    world.app.platform.yield_mainloop = yield_without_delay
    world.app._skip_frame_delay = True
    world.app.prepare_mainloop()
    world.backgrounds._init_display()
    world._mainloop.dirty_all()

    frame_times = []
    for _ in range(20):
        moving_actor.move(2)
        start = time.perf_counter()
        await world.app._update()
        frame_times.append((time.perf_counter() - start) * 1000)

    assert world.frame >= 20
    return [
        {
            "name": "pyodide canvas frame updates",
            "elapsed_ms": round(sum(frame_times), 4),
            "operations": len(frame_times),
            "operations_per_s": round(len(frame_times) / (sum(frame_times) / 1000), 4),
            "avg_ms": round(statistics.fmean(frame_times), 4),
            "p95_ms": round(sorted(frame_times)[round((len(frame_times) - 1) * 0.95)], 4),
        }
    ]


BENCHMARKS = [
    benchmark_actor_lifecycle,
    benchmark_world_queries,
    benchmark_event_communication,
    benchmark_canvas_frame_updates,
]


async def run_suite() -> str:
    results = []
    measurements = []
    for benchmark in BENCHMARKS:
        try:
            result = benchmark()
            if asyncio.iscoroutine(result):
                result = await result
            measurements.extend(result)
        except Exception:
            results.append(
                {
                    "name": benchmark.__name__,
                    "status": "failed",
                    "traceback": traceback.format_exc(),
                }
            )
        else:
            results.append({"name": benchmark.__name__, "status": "passed"})
        finally:
            _reset()

    failed = sum(result["status"] == "failed" for result in results)
    return json.dumps(
        {
            "status": "failed" if failed else "passed",
            "passed": len(results) - failed,
            "failed": failed,
            "results": results,
            "measurements": measurements,
        }
    )
