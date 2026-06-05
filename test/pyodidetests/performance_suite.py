"""Everyday miniworlds performance measurements executed inside Pyodide."""

from __future__ import annotations

import asyncio
import json
import random
import statistics
import time
import traceback

from miniworlds import Actor, App, Circle, Rectangle, Vector, World


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


def _configure_fast_browser_loop(world: World) -> None:
    world.app.platform.poll_events = lambda: []
    world.app.platform.get_mouse_pos = lambda: (0, 0)

    async def yield_without_delay():
        await asyncio.sleep(0)

    world.app.platform.yield_mainloop = yield_without_delay
    world.app._skip_frame_delay = True


def _prepare_rendered_world(world: World) -> None:
    world.app.prepare_mainloop()
    world.backgrounds._init_display()
    world._mainloop.dirty_all()


class SolarPlanet(Circle):
    def __init__(self, position, color, radius, sun, **kwargs):
        self.sun = sun
        super().__init__(position, radius, **kwargs)
        self.color = color
        self.border = 0

    def act(self) -> None:
        vector = Vector.from_actors(self.sun, self)
        normal = vector.get_normal()
        normal.normalize()
        self.move_vector(normal)


async def benchmark_solar_orbit_scene() -> list[dict]:
    _reset()
    rng = random.Random(1337)
    planet_count = 1000
    logic_frames = 20
    rendered_frames = 10

    start = time.perf_counter()
    world = World(400, 400)
    world.add_background("galaxy")
    sun = Circle((200, 200), 10, world=world)
    sun.color = (255, 255, 0)
    sun.static = True

    planets = []
    for _ in range(planet_count):
        color_value = rng.randint(0, 255)
        planets.append(
            SolarPlanet(
                (rng.randint(0, 400), rng.randint(0, 400)),
                (color_value, color_value, color_value),
                color_value / 40,
                sun,
                world=world,
            )
        )
    setup_elapsed = time.perf_counter() - start
    initial_positions = [planet.position for planet in planets]

    math_positions = list(initial_positions)
    start = time.perf_counter()
    for _ in range(logic_frames):
        for index, position in enumerate(math_positions):
            vector = Vector.from_positions((200, 200), position)
            normal = vector.get_normal()
            normal.normalize()
            math_positions[index] = normal.add_to_position(position)
    math_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for _ in range(logic_frames):
        for planet in planets:
            planet.act()
    logic_elapsed = time.perf_counter() - start

    _configure_fast_browser_loop(world)
    _prepare_rendered_world(world)
    frame_times = []
    for _ in range(rendered_frames):
        start = time.perf_counter()
        await world.app._update()
        frame_times.append((time.perf_counter() - start) * 1000)

    assert len(planets) == planet_count
    assert world.frame >= rendered_frames
    assert any(
        planet.position != initial_position
        for planet, initial_position in zip(planets, initial_positions)
    )

    rendered_elapsed_ms = sum(frame_times)
    return [
        _measurement("pyodide solar scene setup", setup_elapsed, planet_count),
        _measurement(
            "pyodide solar vector math",
            math_elapsed,
            planet_count * logic_frames,
        ),
        _measurement(
            "pyodide solar orbit logic",
            logic_elapsed,
            planet_count * logic_frames,
        ),
        {
            "name": "pyodide solar rendered frames",
            "elapsed_ms": round(rendered_elapsed_ms, 4),
            "operations": rendered_frames,
            "actors": planet_count + 1,
            "operations_per_s": round(rendered_frames / (rendered_elapsed_ms / 1000), 4),
            "avg_ms": round(statistics.fmean(frame_times), 4),
            "p95_ms": round(sorted(frame_times)[round((len(frame_times) - 1) * 0.95)], 4),
        },
    ]


BENCHMARKS = [
    benchmark_actor_lifecycle,
    benchmark_world_queries,
    benchmark_event_communication,
    benchmark_canvas_frame_updates,
    benchmark_solar_orbit_scene,
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
