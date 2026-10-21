"""Coordinate mathematics for hexagonal worlds.

HexWorld uses a pointy-top layout with odd-r offset coordinates: Students
address hexes with `(column, row)` tuples, exactly like tiles in a TiledWorld.
Odd rows are shifted half a hex to the right.

Internally, cube coordinates `(q, r, s)` with `q + r + s = 0` are used for
neighbor and distance calculations, because they are uniform across rows.

All functions are pure and free of pygame or world dependencies.
"""

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


def corner_pixel_offset(direction: str, tile_size: float) -> Tuple[float, float]:
    """Return the pixel offset of a hex corner, relative to the hex center."""
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
    return offsets[direction]


def corner_pixel_points(position: Tuple[int, int], tile_size: float) -> List[Tuple[float, float]]:
    """Return the six corner pixels of a hex, clockwise from the top tip."""
    center = hex_center(position, tile_size)
    points = []
    for direction in CORNER_ORDER:
        offset = corner_pixel_offset(direction, tile_size)
        points.append((center[0] + offset[0], center[1] + offset[1]))
    return points


def edge_pixel_offset(direction: str, tile_size: float) -> Tuple[float, float]:
    """Return the pixel offset of an edge center, relative to the hex center."""
    first, second = EDGE_CORNERS[direction]
    first_offset = corner_pixel_offset(first, tile_size)
    second_offset = corner_pixel_offset(second, tile_size)
    return (
        (first_offset[0] + second_offset[0]) / 2.0,
        (first_offset[1] + second_offset[1]) / 2.0,
    )


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


def world_pixel_size(columns: int, rows: int, tile_size: float) -> Tuple[float, float]:
    """Return the pixel size of a hex world with `columns` x `rows` hexes."""
    width = hex_width(tile_size) * (columns + 0.5)
    height = tile_size * (1.5 * rows + 0.5)
    return (width, height)
