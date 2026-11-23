"""Path finding on hexagonal worlds.

The functions work on the tiles of a `HexWorld`. Stepping onto a tile
costs `tile.cost` (default `1`); tiles are impassable if their
`is_blocking` flag is set or a blocking actor (`actor.is_blocking`) stands on
them. Both rules can be replaced with the `blocked` and `cost` callbacks.

Path finding runs in plain Python on the neighbour cache of the tiles, so
it is meant for on-demand queries (a click, a turn), not for being called
for hundreds of actors in every frame.
"""

from __future__ import annotations

import heapq
import itertools
from numbers import Real
from typing import Callable, Dict, List, Optional, Set, Tuple, TYPE_CHECKING

import miniworlds.worlds.hex_world.hex_coords as hex_coords

if TYPE_CHECKING:
    from miniworlds.worlds.hex_world.hex_tile import HexTile
    from miniworlds.worlds.hex_world.hex_world import HexWorld

BlockedCallback = Callable[["HexTile"], bool]
CostCallback = Callable[["HexTile"], float]


def _to_position(value) -> Tuple[int, int]:
    """Return a hex position for a position tuple, tile, or actor.

    Raises the same `TypeError` as `hex_coords.to_offset` for anything
    that is not a `(column, row)` pair (in particular corner/edge keys).
    """
    return hex_coords.to_offset(value)


def _blocking_actor_positions(world: HexWorld) -> Set[Tuple[int, int]]:
    positions = set()
    for actor in getattr(world, "_blocking_actors", ()):
        try:
            positions.add((int(actor.position[0]), int(actor.position[1])))
        except (TypeError, ValueError, IndexError):
            continue
    return positions


def _make_blocked(world: HexWorld, blocked: Optional[BlockedCallback]) -> BlockedCallback:
    if blocked is not None:
        return blocked
    actor_positions = _blocking_actor_positions(world)
    return lambda tile: tile.is_blocking or tile.position in actor_positions


def _make_cost(cost: Optional[CostCallback]) -> CostCallback:
    if cost is not None:
        return cost
    return lambda tile: tile.cost


def _checked_cost(cost_callback: CostCallback, tile: HexTile) -> float:
    step_cost = cost_callback(tile)
    if isinstance(step_cost, bool) or not isinstance(step_cost, Real):
        raise TypeError(
            f"cost(tile) must return a number, got {step_cost!r} for {tile}.\n"
            "Try: cost=lambda tile: tile.cost"
        )
    if step_cost < 0:
        raise ValueError(
            f"The cost of {tile} is {step_cost}, but path finding needs costs >= 0."
        )
    return float(step_cost)


def _minimum_cost(world: HexWorld, cost: Optional[CostCallback], min_cost: Optional[float]):
    """Return the cheapest possible step, used to scale the A* heuristic."""
    if min_cost is not None:
        return min_cost
    if cost is not None:
        # A custom cost function: the cheapest step is unknown, fall back
        # to Dijkstra (heuristic 0) to stay correct.
        return 0.0
    return min((tile.cost for tile in world.tiles.values()), default=1.0)


def find_path(
    world: HexWorld,
    start,
    goal,
    blocked: Optional[BlockedCallback] = None,
    cost: Optional[CostCallback] = None,
    max_cost: Optional[float] = None,
    min_cost: Optional[float] = None,
) -> List[HexTile]:
    """Return the cheapest path between two hexes (A*).

    Args:
        world: The hex world.
        start: Start hex (position, tile, or actor).
        goal: Goal hex (position, tile, or actor).
        blocked: Optional `blocked(tile) -> bool`; replaces the default
            rule (tile flag or blocking actor).
        cost: Optional `cost(tile) -> float` for entering a tile; replaces
            `tile.cost`. Costs must not be negative.
        max_cost: Optional budget; paths that cost more are not returned.
        min_cost: Cheapest step cost, used to speed up the search. Only
            needed together with a custom `cost`; a too large value can
            return a path that is not the cheapest.

    Returns:
        The tiles from start to goal, both included, or an empty list if
        the goal is blocked, unreachable, or too expensive.
    """
    start_tile = world.get_tile(_to_position(start))
    goal_tile = world.get_tile(_to_position(goal))
    is_blocked = _make_blocked(world, blocked)
    cost_callback = _make_cost(cost)
    if start_tile is goal_tile:
        return [start_tile]
    if is_blocked(goal_tile):
        return []

    factor = _minimum_cost(world, cost, min_cost)
    goal_cube = hex_coords.offset_to_cube(goal_tile.position)

    def heuristic(tile: HexTile) -> float:
        if factor <= 0:
            return 0.0
        return factor * hex_coords.cube_distance(
            hex_coords.offset_to_cube(tile.position), goal_cube
        )

    counter = itertools.count()
    open_heap = [(heuristic(start_tile), next(counter), start_tile)]
    best_cost: Dict[Tuple[int, int], float] = {start_tile.position: 0.0}
    came_from: Dict[Tuple[int, int], HexTile] = {}
    closed: Set[Tuple[int, int]] = set()

    while open_heap:
        _priority, _order, current = heapq.heappop(open_heap)
        if current.position in closed:
            continue
        if current is goal_tile:
            return _reconstruct(came_from, goal_tile)
        closed.add(current.position)
        current_cost = best_cost[current.position]
        for neighbour in current._neighbour_tiles_shared():
            if neighbour.position in closed or is_blocked(neighbour):
                continue
            new_cost = current_cost + _checked_cost(cost_callback, neighbour)
            if max_cost is not None and new_cost > max_cost:
                continue
            if new_cost < best_cost.get(neighbour.position, float("inf")):
                best_cost[neighbour.position] = new_cost
                came_from[neighbour.position] = current
                heapq.heappush(
                    open_heap, (new_cost + heuristic(neighbour), next(counter), neighbour)
                )
    return []


def _reconstruct(came_from: Dict[Tuple[int, int], HexTile], goal_tile: HexTile) -> List[HexTile]:
    path = [goal_tile]
    while path[-1].position in came_from:
        path.append(came_from[path[-1].position])
    path.reverse()
    return path


def get_reachable_tiles(
    world: HexWorld,
    start,
    max_cost: float,
    blocked: Optional[BlockedCallback] = None,
    cost: Optional[CostCallback] = None,
) -> List[HexTile]:
    """Return all hexes reachable within a movement budget (Dijkstra).

    Args:
        world: The hex world.
        start: Start hex (position, tile, or actor).
        max_cost: Movement budget; with default costs this is the number
            of steps.
        blocked: Optional `blocked(tile) -> bool`, see `find_path`.
        cost: Optional `cost(tile) -> float`, see `find_path`.

    Returns:
        The reachable tiles including the start tile, ordered from the
        cheapest to the most expensive.
    """
    start_tile = world.get_tile(_to_position(start))
    is_blocked = _make_blocked(world, blocked)
    cost_callback = _make_cost(cost)

    counter = itertools.count()
    open_heap = [(0.0, next(counter), start_tile)]
    best_cost: Dict[Tuple[int, int], float] = {start_tile.position: 0.0}
    reached: List[HexTile] = []
    closed: Set[Tuple[int, int]] = set()

    while open_heap:
        current_cost, _order, current = heapq.heappop(open_heap)
        if current.position in closed:
            continue
        closed.add(current.position)
        reached.append(current)
        for neighbour in current._neighbour_tiles_shared():
            if neighbour.position in closed or is_blocked(neighbour):
                continue
            new_cost = current_cost + _checked_cost(cost_callback, neighbour)
            if new_cost > max_cost:
                continue
            if new_cost < best_cost.get(neighbour.position, float("inf")):
                best_cost[neighbour.position] = new_cost
                heapq.heappush(open_heap, (new_cost, next(counter), neighbour))
    return reached


def find_nearest(
    world: HexWorld,
    start,
    is_target: Callable[["HexTile"], bool],
    blocked: Optional[BlockedCallback] = None,
    cost: Optional[CostCallback] = None,
    max_cost: Optional[float] = None,
    include_start: bool = False,
) -> List[HexTile]:
    """Return the cheapest path to the nearest hex that satisfies `is_target`.

    A target may be blocked, for example an enemy that blocks its own hex:
    the path ends on the target. Only the hexes on the way must be
    passable.

    Args:
        world: The hex world.
        start: Start hex (position, tile, or actor).
        is_target: Function `is_target(tile) -> bool`.
        blocked: Optional `blocked(tile) -> bool`, see `find_path`.
        cost: Optional `cost(tile) -> float`, see `find_path`.
        max_cost: Optional budget; targets that cost more are ignored.
        include_start: If `True`, the start hex itself can be the target.

    Returns:
        The tiles from start to the nearest target, both included, or an
        empty list if no target is reachable.
    """
    start_tile = world.get_tile(_to_position(start))
    is_blocked = _make_blocked(world, blocked)
    cost_callback = _make_cost(cost)
    if include_start and is_target(start_tile):
        return [start_tile]

    counter = itertools.count()
    open_heap = [(0.0, next(counter), start_tile)]
    best_cost: Dict[Tuple[int, int], float] = {start_tile.position: 0.0}
    came_from: Dict[Tuple[int, int], HexTile] = {}
    closed: Set[Tuple[int, int]] = set()

    while open_heap:
        current_cost, _order, current = heapq.heappop(open_heap)
        if current.position in closed:
            continue
        if current is not start_tile and is_target(current):
            return _reconstruct(came_from, current)
        closed.add(current.position)
        for neighbour in current._neighbour_tiles_shared():
            if neighbour.position in closed:
                continue
            # A blocked target ends the path, but is never walked through
            # (targets are returned when popped, before being expanded).
            if is_blocked(neighbour) and not is_target(neighbour):
                continue
            new_cost = current_cost + _checked_cost(cost_callback, neighbour)
            if max_cost is not None and new_cost > max_cost:
                continue
            if new_cost < best_cost.get(neighbour.position, float("inf")):
                best_cost[neighbour.position] = new_cost
                came_from[neighbour.position] = current
                heapq.heappush(open_heap, (new_cost, next(counter), neighbour))
    return []


def has_line_of_sight(
    world: HexWorld, start, goal, blocked: Optional[BlockedCallback] = None
) -> bool:
    """Return whether no blocked hex lies between two hexes.

    Only the hexes strictly between start and goal count, so a blocked
    goal (for example an enemy that blocks its own hex) can be seen.
    """
    is_blocked = _make_blocked(world, blocked)
    line = world.get_tiles_in_line(start, goal)
    return not any(is_blocked(tile) for tile in line[1:-1])


def get_path_cost(path, cost: Optional[CostCallback] = None) -> float:
    """Return the cost of a path: the sum of the costs of all hexes but the first.

    Args:
        path: A list of tiles, for example the result of `find_path`.
        cost: Optional `cost(tile) -> float`, see `find_path`.

    Raises:
        TypeError: If `path` is not an iterable of tiles.
    """
    if path is None or isinstance(path, (str, bytes)) or not hasattr(path, "__iter__"):
        raise TypeError(
            f"path must be a list of tiles, for example the result of "
            f"world.find_path(...), got {path!r}"
        )
    cost_callback = _make_cost(cost)
    tiles = list(path)
    if cost is None:
        for tile in tiles:
            if not hasattr(tile, "cost"):
                raise TypeError(
                    f"path must contain tiles (with a .cost attribute), got {tile!r}.\n"
                    "Try: path = world.find_path(start, goal)"
                )
    total = 0.0
    for tile in tiles[1:]:
        total += _checked_cost(cost_callback, tile)
    return total

