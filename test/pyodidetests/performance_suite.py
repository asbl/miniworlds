"""Everyday miniworlds performance measurements executed inside Pyodide."""

from __future__ import annotations

import asyncio
import json
import random
import statistics
import time
import traceback

import pygame

from miniworlds import Actor, ActorPool, App, Circle, Rectangle, Vector, World


def _reset() -> None:
    App.reset(unittest=True, file="/project/main.py")


def _measurement(name: str, elapsed: float, operations: int) -> dict:
    return {
        "name": name,
        "elapsed_ms": round(elapsed * 1000, 4),
        "operations": operations,
        "operations_per_s": round(operations / elapsed, 4),
    }


def benchmark_calibration() -> list[dict]:
    """Fixed pure-Python workload; budgets are expressed relative to it.

    This reduces CPU-speed differences between machines running the gate;
    browser rendering overhead can still vary independently.
    """
    best = None
    for _ in range(3):
        start = time.perf_counter()
        total = 0.0
        table: dict[int, float] = {}
        for index in range(200_000):
            value = (index * 31 % 977) * 0.5
            table[index % 512] = value
            total += value
        elapsed = time.perf_counter() - start
        best = elapsed if best is None else min(best, elapsed)
    assert best is not None and total > 0
    return [_measurement("pyodide calibration", best, 200_000)]


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
    # Regression guard: in the browser every draw exceeds pygame's default
    # 12.5 ms threshold; unless the threshold is lifted the group falls back
    # to repainting every sprite each frame (4.9 FPS instead of 60 FPS).
    assert world.actors._time_threshold >= 1000, "LayeredDirty threshold was lowered"
    assert world.actors._use_update, "LayeredDirty left dirty-rect mode"
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


async def benchmark_dense_canvas_updates() -> list[dict]:
    """Compare modes in one browser run, including identical canvas output."""
    measurements = []
    outputs = []
    for mode in ("dirty", "adaptive"):
        _reset()
        world = World(400, 400)
        world.add_background((20, 30, 40))
        actors = [
            Rectangle((12 + column * 24, 12 + row * 24), 18, 18, world=world)
            for row in range(16) for column in range(16)
        ]
        if mode == "dirty":
            def draw_dirty(surface, bgd=None):
                world.actors._use_update = True
                return pygame.sprite.LayeredDirty.draw(world.actors, surface, bgd)
            world.actors.draw = draw_dirty
        _configure_fast_browser_loop(world)
        _prepare_rendered_world(world)
        frame_times = []
        for frame in range(23):
            for actor in actors:
                actor.move(1 if frame % 2 else -1)
            start = time.perf_counter()
            await world.app._update()
            if frame >= 3:
                frame_times.append(time.perf_counter() - start)
        measurements.append(_measurement(
            f"pyodide dense canvas {mode}", sum(frame_times), len(frame_times)
        ))
        outputs.append(pygame.image.tostring(world.app.window.surface, "RGB"))
    assert outputs[0] == outputs[1], "adaptive redraw changed canvas pixels"
    return measurements


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


class SurvivorEnemy(Actor):
    def act(self):
        self.move_towards_fast((201, 199), 0.5)


class SurvivorShot(Actor):
    def on_detecting_survivorenemy(self, enemy):
        self.hits = getattr(self, "hits", 0) + 1


def benchmark_survivor_targeting_and_collisions():
    _reset()
    world = World(400, 400)
    enemies = [SurvivorEnemy((10 + i % 40 * 9, 10 + i // 40 * 14), world=world)
               for i in range(1000)]
    for enemy in enemies:
        enemy.size = (12, 12)
        enemy.collision_group = "enemy"
    player = Actor((201, 201), world=world)
    _prepare_rendered_world(world)
    expected = min(enemies, key=player.get_distance_to)
    # Warm the lazily created typed index outside the measured query loop.
    assert world.find_nearest(player, SurvivorEnemy) is expected
    start = time.perf_counter()
    for _ in range(100):
        assert world.find_nearest(player, SurvivorEnemy) is expected
    targeting = time.perf_counter() - start
    shots = [SurvivorShot((150 + i % 10 * 4, 150 + i // 10 * 4), world=world)
             for i in range(60)]
    for shot in shots:
        shot.size = (6, 6)
        shot.collision_type = "rect"
        shot.collision_targets = {"enemy"}
    world._collision_manager._handle_all_collisions()
    start = time.perf_counter()
    for _ in range(10):
        world._collision_manager._handle_all_collisions()
    collisions = time.perf_counter() - start
    assert sum(shot.hits for shot in shots) > 0
    return [_measurement("pyodide survivor nearest queries", targeting, 100),
            _measurement("pyodide survivor grouped collisions", collisions, 600)]


def benchmark_survivor_pool_lifecycle():
    _reset()
    world = World(400, 400)
    for i in range(500):
        SurvivorEnemy((10 + i % 25 * 14, 10 + i // 25 * 14), world=world)
    pool = ActorPool(lambda: SurvivorShot((20, 20), world=world), initial_size=100, max_size=100)
    _prepare_rendered_world(world)
    start = time.perf_counter()
    for _ in range(5):
        shots = [pool.acquire((30 + i % 20 * 16, 30 + i // 20 * 16)) for i in range(100)]
        for shot in shots:
            pool.release(shot)
    elapsed = time.perf_counter() - start
    assert pool.available == 100 and len(world.actors) == 500
    pool.clear()
    return [_measurement("pyodide survivor pooled lifecycle", elapsed, 500)]


async def benchmark_survivor_rendered_scene():
    _reset()
    world = World(400, 400)
    for i in range(500):
        enemy = SurvivorEnemy((20 + i % 25 * 14, 20 + i // 25 * 8), world=world)
        enemy.size = (16, 16)
    _configure_fast_browser_loop(world)
    _prepare_rendered_world(world)
    for _ in range(3):
        await world.app._update()
    times = []
    for _ in range(10):
        start = time.perf_counter()
        await world.app._update()
        times.append((time.perf_counter() - start) * 1000)
    return [{"name": "pyodide survivor rendered frames", "elapsed_ms": sum(times),
             "avg_ms": statistics.fmean(times), "operations": 10,
             "p95_ms": sorted(times)[-1]}]


BENCHMARKS = [
    benchmark_calibration,
    benchmark_actor_lifecycle,
    benchmark_world_queries,
    benchmark_event_communication,
    benchmark_canvas_frame_updates,
    benchmark_dense_canvas_updates,
    benchmark_solar_orbit_scene,
    benchmark_survivor_targeting_and_collisions,
    benchmark_survivor_pool_lifecycle,
    benchmark_survivor_rendered_scene,
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
