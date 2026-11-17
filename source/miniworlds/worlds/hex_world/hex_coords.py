"""Coordinate mathematics for hexagonal worlds.

HexWorld uses a pointy-top layout with odd-r offset coordinates: Students
address hexes with `(column, row)` tuples, exactly like tiles in a TiledWorld.
Odd rows are shifted half a hex to the right.

Internally, cube coordinates `(q, r, s)` with `q + r + s = 0` are used for
neighbor and distance calculations, because they are uniform across rows.

All functions are pure and free of pygame or world dependencies.
"""

import functools
import math
from typing import Dict, List, Tuple

import miniworlds.base.exceptions as miniworlds_exception

SQRT3 = math.sqrt(3.0)

Cube = Tuple[int, int, int]
Offset = Tuple[int, int]

# Cube direction vectors of the six neighbor hexes (pointy-top).
CUBE_DIRECTIONS: Dict[str, Cube] = {
    "o": (+1, 0, -1),
    "so": (0, +1, -1),
    "sw": (-1, +1, 0),
    "w": (-1, 0, +1),
    "nw": (0, -1, +1),
    "no": (+1, -1, 0),
}

# Corner vectors in tripled cube coordinates:
# corner position = 3 * cube(tile) + vector.
# A corner is shared by up to three hexes; every hex reaches the same
# corner position through its own direction name.
CORNER_DIRECTIONS: Dict[str, Cube] = {
    "n": (+1, -2, +1),
    "no": (+2, -1, -1),
    "so": (+1, +1, -2),
    "s": (-1, +2, -1),
    "sw": (-2, +1, +1),
    "nw": (-1, -1, +2),
}

# Edge vectors in doubled cube coordinates:
# edge position = 2 * cube(tile) + vector.
# Edge names match the neighbor direction the edge points to; the values
# are the plain neighbor direction vectors.
EDGE_DIRECTIONS: Dict[str, Cube] = {
    "o": (+1, 0, -1),
    "so": (0, +1, -1),
    "sw": (-1, +1, 0),
    "w": (-1, 0, +1),
    "nw": (0, -1, +1),
    "no": (+1, -1, 0),
}

# Corner names in clockwise order, starting at the top tip (for rendering).
CORNER_ORDER: List[str] = ["n", "no", "so", "s", "sw", "nw"]

# Edge names in clockwise order, starting at the north-east edge.
EDGE_ORDER: List[str] = ["no", "o", "so", "sw", "w", "nw"]

# Scratch-style degrees (0 = up, clockwise) of the six neighbor
# directions in a pointy-top layout. Used to move actors along hex
# axes: `actor.move_in_direction("no")` moves to the north-east
# neighbor.
DIRECTION_DEGREES: Dict[str, int] = {
    "no": 30,
    "o": 90,
    "so": 150,
    "sw": 210,
    "w": 270,
    "nw": 330,
}

# Reverse of DIRECTION_DEGREES: scratch-style degrees to direction name.
DEGREE_DIRECTIONS: Dict[int, str] = {
    degrees: name for name, degrees in DIRECTION_DEGREES.items()
}


def nearest_axis_degrees(direction: float) -> int:
    """Return the hex axis degree nearest to `direction` (scratch-style degrees).

    The six hex axes are 30, 90, 150, 210, 270 and 330 degrees (0 = up,
    clockwise). Any other angle is snapped to the nearest axis, so one
    movement step is always exactly one hex. Ties round towards the next
    higher axis.
    """
    index = math.floor((float(direction) - 30) / 60 + 0.5)
    return (30 + 60 * index) % 360

# The two corners that enclose an edge, keyed by edge direction.
EDGE_CORNERS: Dict[str, Tuple[str, str]] = {
    "o": ("no", "so"),
    "so": ("so", "s"),
    "sw": ("s", "sw"),
    "w": ("sw", "nw"),
    "nw": ("nw", "n"),
    "no": ("n", "no"),
}


def offset_to_cube(position: Tuple[int, int]) -> Cube:
    """Convert odd-r offset coordinates `(column, row)` to cube coordinates."""
    column, row = int(position[0]), int(position[1])
    q = column - (row - (row & 1)) // 2
    r = row
    return (q, r, -q - r)


def cube_to_offset(cube: Tuple[float, float, float]) -> Offset:
    """Convert cube coordinates `(q, r, s)` to odd-r offset coordinates."""
    q, r = cube[0], cube[1]
    column = q + (r - (r & 1)) // 2
    return (int(round(column)), int(round(r)))


def cube_distance(a: Tuple[float, float, float], b: Tuple[float, float, float]) -> int:
    """Return the hex distance (number of hexes) between two cube positions."""
    return int((abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])) / 2)


def cube_ring(center: Cube, radius: int) -> List[Cube]:
    """Return all cube positions at exactly `radius` hex distance.

    The positions are returned in ring traversal order, starting at the
    westernmost hex of the ring and walking clockwise. For `radius` 0,
    only the center is returned; for negative `radius`, nothing is
    returned.
    """
    if radius < 0:
        return []
    if radius == 0:
        return [center]
    positions: List[Cube] = []
    cube = (center[0] - radius, center[1], center[2] + radius)
    for side in ("no", "o", "so", "sw", "w", "nw"):
        vector = CUBE_DIRECTIONS[side]
        for _ in range(radius):
            positions.append(cube)
            cube = (cube[0] + vector[0], cube[1] + vector[1], cube[2] + vector[2])
    return positions


# Offset deltas of rings and discs. In odd-r offset coordinates the offset
# of a neighbour depends only on the row parity, so the deltas of a ring
# around any hex are the same for all hexes of one parity. They are
# computed once per `(parity, radius)` and turn every ring/radius query
# into plain tuple additions and dictionary lookups, without converting
# between offset and cube coordinates for each hex.
OffsetDeltas = Tuple[Offset, ...]


def neighbour_offset_deltas(row_parity: int) -> OffsetDeltas:
    """Return the offset deltas of the six neighbours for a row parity.

    The deltas follow the order of `CUBE_DIRECTIONS`: `"o"`, `"so"`,
    `"sw"`, `"w"`, `"nw"`, `"no"`. Any integer row can be passed; only its
    parity counts.
    """
    return _neighbour_offset_deltas(row_parity & 1)


def ring_offset_deltas(row_parity: int, radius: int) -> OffsetDeltas:
    """Return the offset deltas of all hexes at exactly `radius` distance.

    The order is the ring traversal order of `cube_ring`. For `radius` 0
    the only delta is `(0, 0)`; for negative `radius` it is empty. Any
    integer row can be passed; only its parity counts.
    """
    return _ring_offset_deltas(row_parity & 1, max(int(radius), -1))


def disc_offset_deltas(row_parity: int, radius: int) -> OffsetDeltas:
    """Return the offset deltas of all hexes within `radius` distance.

    The center comes first, followed by the rings from the inside out,
    each in `cube_ring` order.
    """
    return _disc_offset_deltas(row_parity & 1, max(int(radius), -1))


@functools.lru_cache(maxsize=2)
def _neighbour_offset_deltas(row_parity: int) -> OffsetDeltas:
    origin = (0, row_parity)
    origin_cube = offset_to_cube(origin)
    deltas = []
    for vector in CUBE_DIRECTIONS.values():
        target = cube_to_offset(
            (origin_cube[0] + vector[0], origin_cube[1] + vector[1], origin_cube[2] + vector[2])
        )
        deltas.append((target[0] - origin[0], target[1] - origin[1]))
    return tuple(deltas)


@functools.lru_cache(maxsize=256)
def _ring_offset_deltas(row_parity: int, radius: int) -> OffsetDeltas:
    origin = (0, row_parity)
    return tuple(
        (target[0] - origin[0], target[1] - origin[1])
        for target in map(cube_to_offset, cube_ring(offset_to_cube(origin), radius))
    )


@functools.lru_cache(maxsize=256)
def _disc_offset_deltas(row_parity: int, radius: int) -> OffsetDeltas:
    if radius < 0:
        return ()
    if radius == 0:
        return _ring_offset_deltas(row_parity, 0)
    return _disc_offset_deltas(row_parity, radius - 1) + _ring_offset_deltas(
        row_parity, radius
    )


def hex_distance(first: Tuple[int, int], second: Tuple[int, int]) -> int:
    """Return the hex distance between two offset positions `(column, row)`.

    The distance is the number of hex steps between the positions; it
    does not depend on the row parity.
    """
    return cube_distance(offset_to_cube(first), offset_to_cube(second))


def cube_line(start: Cube, end: Cube) -> List[Cube]:
    """Return the cubes of the straight line from `start` to `end`.

    Both ends are included; the line has `distance + 1` hexes. A tiny
    nudge makes the result deterministic when the line runs exactly along
    the border of two hexes.
    """
    distance = cube_distance(start, end)
    if distance == 0:
        return [start]
    nudge = (1e-6, 2e-6, -3e-6)
    return [
        cube_round(
            tuple(
                start[axis] + nudge[axis] + (end[axis] - start[axis]) * step / distance
                for axis in range(3)
            )
        )
        for step in range(distance + 1)
    ]


def to_offset(value) -> Offset:
    """Return the offset position of a position tuple, tile, or actor."""
    position = getattr(value, "position", value)
    try:
        return (int(position[0]), int(position[1]))
    except (TypeError, ValueError, IndexError):
        raise TypeError(
            f"Expected a position (column, row), a tile, or an actor, got {value!r}"
        ) from None


def cube_destination(start: Tuple[int, int], direction: str, distance: int) -> Offset:
    """Return the hex position reached from `start` moving along a hex axis.

    Args:
        start: Hex position as `(column, row)`.
        direction: Neighbor direction, e.g. `"no"`.
        distance: Number of hexes to move.

    Returns:
        The destination hex position. The destination is not checked
        against the world bounds.
    """
    cube = offset_to_cube(start)
    vector = direction_vector(direction, CUBE_DIRECTIONS)
    destination = (
        cube[0] + vector[0] * distance,
        cube[1] + vector[1] * distance,
        cube[2] + vector[2] * distance,
    )
    return cube_to_offset(destination)


def cube_round(cube: Tuple[float, float, float]) -> Cube:
    """Round fractional cube coordinates to the nearest hex center."""
    q, r, s = cube
    rq, rr, rs = round(q), round(r), round(s)
    q_diff, r_diff, s_diff = abs(rq - q), abs(rr - r), abs(rs - s)
    if q_diff > r_diff and q_diff > s_diff:
        rq = -rr - rs
    elif r_diff > s_diff:
        rr = -rq - rs
    else:
        rs = -rq - rr
    return (rq, rr, rs)


def hex_width(tile_size: float) -> float:
    """Return the pixel width of a hex (bounding box width)."""
    return SQRT3 * tile_size


def hex_height(tile_size: float) -> float:
    """Return the pixel height of a hex (bounding box height)."""
    return 2.0 * tile_size


def hex_center(position: Tuple[int, int], tile_size: float) -> Tuple[float, float]:
    """Return the pixel center of the hex at offset position `(column, row)`.

    The layout leaves half a hex margin at the top and left so that the
    top tip of the first row and the left edge of the first column are
    fully visible.
    """
    column, row = position[0], position[1]
    x = hex_width(tile_size) * (column + 0.5 * (row & 1)) + hex_width(tile_size) / 2
    y = 1.5 * tile_size * row + tile_size
    return (x, y)


def pixel_to_cube(pixel: Tuple[float, float], tile_size: float) -> Cube:
    """Return the cube coordinates of the hex containing a pixel position."""
    x = pixel[0] - hex_width(tile_size) / 2
    y = pixel[1] - tile_size
    q = (SQRT3 / 3.0 * x - 1.0 / 3.0 * y) / tile_size
    r = (2.0 / 3.0 * y) / tile_size
    return cube_round((q, r, -q - r))


# Corner and edge pixel offsets are pure functions of the tile size, but
# they are read on hot paths (corner/edge picking, grid rendering). They
# are cached per tile size (few distinct values per program).
_CORNER_OFFSETS_CACHE: Dict[float, Dict[str, Tuple[float, float]]] = {}
_EDGE_OFFSETS_CACHE: Dict[float, Dict[str, Tuple[float, float]]] = {}


def corner_pixel_offsets(tile_size: float) -> Dict[str, Tuple[float, float]]:
    """Return the pixel offsets of the six hex corners (relative to center)."""
    offsets = _CORNER_OFFSETS_CACHE.get(tile_size)
    if offsets is None:
        half_width = hex_width(tile_size) / 2.0
        half = tile_size / 2.0
        offsets = {
            "n": (0.0, -tile_size),
            "no": (half_width, -half),
            "so": (half_width, half),
            "s": (0.0, tile_size),
            "sw": (-half_width, half),
            "nw": (-half_width, -half),
        }
        _CORNER_OFFSETS_CACHE[tile_size] = offsets
    return offsets


def corner_pixel_offset(direction: str, tile_size: float) -> Tuple[float, float]:
    """Return the pixel offset of a hex corner, relative to the hex center."""
    return corner_pixel_offsets(tile_size)[direction]


def corner_pixel_points(position: Tuple[int, int], tile_size: float) -> List[Tuple[float, float]]:
    """Return the six corner pixels of a hex, clockwise from the top tip."""
    center = hex_center(position, tile_size)
    return [
        (center[0] + offset[0], center[1] + offset[1])
        for offset in corner_pixel_offsets(tile_size).values()
    ]


def edge_pixel_offsets(tile_size: float) -> Dict[str, Tuple[float, float]]:
    """Return the pixel offsets of the six edge centers (relative to center)."""
    offsets = _EDGE_OFFSETS_CACHE.get(tile_size)
    if offsets is None:
        corner_offsets = corner_pixel_offsets(tile_size)
        offsets = {
            direction: (
                (corner_offsets[first][0] + corner_offsets[second][0]) / 2.0,
                (corner_offsets[first][1] + corner_offsets[second][1]) / 2.0,
            )
            for direction, (first, second) in EDGE_CORNERS.items()
        }
        _EDGE_OFFSETS_CACHE[tile_size] = offsets
    return offsets


def edge_pixel_offset(direction: str, tile_size: float) -> Tuple[float, float]:
    """Return the pixel offset of an edge center, relative to the hex center."""
    return edge_pixel_offsets(tile_size)[direction]


def direction_vector(direction: str, vectors: Dict[str, Cube]) -> Cube:
    """Return the vector for a direction name, with a helpful error."""
    try:
        return vectors[direction]
    except KeyError:
        raise miniworlds_exception.DirectionNotFoundError(
            direction, list(vectors)
        ) from None


def corner_position(tile_position: Tuple[int, int], direction: str) -> Cube:
    """Return the unique position key of a corner.

    The key is expressed in tripled cube coordinates so that all hexes
    sharing the corner produce the same integer key.
    """
    cube = offset_to_cube(tile_position)
    vector = direction_vector(direction, CORNER_DIRECTIONS)
    return (3 * cube[0] + vector[0], 3 * cube[1] + vector[1], 3 * cube[2] + vector[2])


def edge_position(tile_position: Tuple[int, int], direction: str) -> Cube:
    """Return the unique position key of an edge.

    The key is expressed in doubled cube coordinates so that both hexes
    sharing the edge produce the same integer key.
    """
    cube = offset_to_cube(tile_position)
    vector = direction_vector(direction, EDGE_DIRECTIONS)
    return (2 * cube[0] + vector[0], 2 * cube[1] + vector[1], 2 * cube[2] + vector[2])


def _divisible(cube: Cube, divisor: int) -> bool:
    return all(component % divisor == 0 for component in cube)


def corner_tile_references(corner_key: Cube) -> List[Tuple[Cube, str]]:
    """Return `(tile cube, corner direction)` for every hex sharing a corner.

    A corner key is `3 * cube + vector`. Subtracting each corner vector
    and testing divisibility by three finds the (up to) three hexes that
    reach the corner, independent of the world bounds.
    """
    references = []
    for direction, vector in CORNER_DIRECTIONS.items():
        difference = (
            corner_key[0] - vector[0],
            corner_key[1] - vector[1],
            corner_key[2] - vector[2],
        )
        if _divisible(difference, 3):
            references.append(
                ((difference[0] // 3, difference[1] // 3, difference[2] // 3), direction)
            )
    return references


def edge_tile_references(edge_key: Cube) -> List[Tuple[Cube, str]]:
    """Return `(tile cube, edge direction)` for both hexes sharing an edge.

    An edge key is `2 * cube + vector`; see `corner_tile_references`.
    """
    references = []
    for direction, vector in EDGE_DIRECTIONS.items():
        difference = (
            edge_key[0] - vector[0],
            edge_key[1] - vector[1],
            edge_key[2] - vector[2],
        )
        if _divisible(difference, 2):
            references.append(
                ((difference[0] // 2, difference[1] // 2, difference[2] // 2), direction)
            )
    return references


def _corner_key(cube: Cube, direction: str) -> Cube:
    vector = CORNER_DIRECTIONS[direction]
    return (3 * cube[0] + vector[0], 3 * cube[1] + vector[1], 3 * cube[2] + vector[2])


def _edge_key(cube: Cube, direction: str) -> Cube:
    vector = EDGE_DIRECTIONS[direction]
    return (2 * cube[0] + vector[0], 2 * cube[1] + vector[1], 2 * cube[2] + vector[2])


def _unique(keys: List[Cube]) -> List[Cube]:
    return list(dict.fromkeys(keys))


def corner_neighbour_corner_keys(corner_key: Cube) -> List[Cube]:
    """Return the keys of the three corners one hex side away from a corner.

    The keys are computed without a world, so they may lie outside the
    board; callers filter by the corners that exist.
    """
    keys = []
    for cube, direction in corner_tile_references(corner_key):
        index = CORNER_ORDER.index(direction)
        for step in (-1, 1):
            keys.append(_corner_key(cube, CORNER_ORDER[(index + step) % 6]))
    return _unique(keys)


def corner_edge_keys(corner_key: Cube) -> List[Cube]:
    """Return the keys of the three edges that meet at a corner."""
    keys = []
    for cube, direction in corner_tile_references(corner_key):
        for edge_direction, corners in EDGE_CORNERS.items():
            if direction in corners:
                keys.append(_edge_key(cube, edge_direction))
    return _unique(keys)


def edge_corner_keys(edge_key: Cube) -> List[Cube]:
    """Return the keys of the two corners at the ends of an edge."""
    keys = []
    for cube, direction in edge_tile_references(edge_key):
        for corner_direction in EDGE_CORNERS[direction]:
            keys.append(_corner_key(cube, corner_direction))
    return _unique(keys)


def edge_neighbour_edge_keys(edge_key: Cube) -> List[Cube]:
    """Return the keys of the (up to four) edges that touch an edge at a corner."""
    keys = []
    for corner_key in edge_corner_keys(edge_key):
        keys.extend(corner_edge_keys(corner_key))
    return [key for key in _unique(keys) if key != edge_key]


def world_pixel_size(columns: int, rows: int, tile_size: float) -> Tuple[float, float]:
    """Return the pixel size of a hex world with `columns` x `rows` hexes."""
    width = hex_width(tile_size) * (columns + 0.5)
    height = tile_size * (1.5 * rows + 0.5)
    return (width, height)
