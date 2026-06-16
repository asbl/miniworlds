"""
Performance comparison: TiledWorld with vs without TiledSpatialIndex

This script measures the performance improvement when using the TiledSpatialIndex
for actor detection in TiledWorld scenarios.

Run with: python -m miniworlds.test.performance.profile_tiled_world_spatial_index
"""

from __future__ import annotations

import time

from miniworlds import Actor, TiledWorld

# Test configuration - adjust these for faster/slower tests
GRID_COLUMNS = 15
GRID_ROWS = 10
ACTORS_PER_CELL = 2
ITERATIONS = 1000
QUERY_POSITIONS = [
    (5, 5),
    (10, 5),
    (7, 8),
    (0, 0),
    (14, 9),
]


def create_test_world(use_spatial_index: bool = True) -> TiledWorld:
    """Create a test TiledWorld with many actors."""
    world = TiledWorld(GRID_COLUMNS, GRID_ROWS)

    # Create many actors spread across the world
    for row in range(GRID_ROWS):
        for col in range(GRID_COLUMNS):
            for _ in range(ACTORS_PER_CELL):
                Actor((col, row), world=world)

    if not use_spatial_index:
        # Disable spatial index by setting it to None
        world._tiled_spatial_index = None

    return world


def benchmark_with_spatial_index():
    """Benchmark TiledWorld WITH TiledSpatialIndex."""
    world = create_test_world(use_spatial_index=True)

    # Warm up the spatial index
    for pos in QUERY_POSITIONS:
        world.detect_actors_at_position(pos)

    start = time.perf_counter()
    hits = 0
    for _ in range(ITERATIONS):
        for pos in QUERY_POSITIONS:
            actors = world.detect_actors_at_position(pos)
            hits += len(actors)
    elapsed = time.perf_counter() - start

    return {
        "name": "TiledWorld WITH TiledSpatialIndex",
        "actors": len(world.actors),
        "iterations": ITERATIONS * len(QUERY_POSITIONS),
        "hits": hits,
        "elapsed_ms": round(elapsed * 1000, 2),
        "queries_per_s": round((ITERATIONS * len(QUERY_POSITIONS)) / elapsed, 0),
    }


def benchmark_without_spatial_index():
    """Benchmark TiledWorld WITHOUT TiledSpatialIndex (using old method)."""
    world = create_test_world(use_spatial_index=False)

    # Force the old method by clearing spatial index
    # The detect_actors_at_position will fall back to _update_actor_positions

    start = time.perf_counter()
    hits = 0
    for _ in range(ITERATIONS):
        for pos in QUERY_POSITIONS:
            actors = world.detect_actors_at_position(pos)
            hits += len(actors)
    elapsed = time.perf_counter() - start

    return {
        "name": "TiledWorld WITHOUT TiledSpatialIndex (old method)",
        "actors": len(world.actors),
        "iterations": ITERATIONS * len(QUERY_POSITIONS),
        "hits": hits,
        "elapsed_ms": round(elapsed * 1000, 2),
        "queries_per_s": round((ITERATIONS * len(QUERY_POSITIONS)) / elapsed, 0),
    }


def print_results(results: list):
    """Print benchmark results in a formatted table."""
    print("\n" + "=" * 70)
    print("TILED WORLD SPATIAL INDEX PERFORMANCE COMPARISON")
    print("=" * 70)
    print()

    for result in results:
        print(f"Test: {result['name']}")
        print(f"  Actors: {result['actors']}")
        print(f"  Iterations: {result['iterations']}")
        print(f"  Total hits: {result['hits']}")
        print(f"  Time: {result['elapsed_ms']} ms")
        print(f"  Queries/sec: {result['queries_per_s']:,}")
        print()

    # Compare the two main methods
    if (
        len(results) >= 2
        and "queries_per_s" in results[0]
        and "queries_per_s" in results[1]
    ):
        with_spatial = results[0]["queries_per_s"]
        without_spatial = results[1]["queries_per_s"]
        speedup = with_spatial / without_spatial if without_spatial > 0 else 0

        print("=" * 70)
        print(f"SPEEDUP: {speedup:.2f}x faster with TiledSpatialIndex")
        if speedup > 1:
            print(f"PERFORMANCE GAIN: +{((speedup - 1) * 100):.1f}%")
        else:
            print(f"PERFORMANCE LOSS: {((1 - speedup) * 100):.1f}% slower")
        print("=" * 70)


def main():
    print("Running TiledWorld Spatial Index Performance Tests...")
    print(
        f"Configuration: {GRID_COLUMNS}x{GRID_ROWS} grid, {ACTORS_PER_CELL} actors/cell"
    )
    print()

    results = []

    # Test 1: With spatial index
    print("Test 1: TiledWorld WITH TiledSpatialIndex...")
    results.append(benchmark_with_spatial_index())

    # Test 2: Without spatial index
    print("Test 2: TiledWorld WITHOUT TiledSpatialIndex...")
    results.append(benchmark_without_spatial_index())

    print_results(results)


if __name__ == "__main__":
    main()
