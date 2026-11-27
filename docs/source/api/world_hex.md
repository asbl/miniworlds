# World > HexWorld

Start with the [Hex Worlds tutorial](../tutorial/hex_world.md) for
runnable examples or the [board game pattern](../patterns/hex_world_catan.md)
for an example that combines tiles, corners, and edges.

## Common operations

| Task | API |
| --- | --- |
| Look up a tile by grid position | `world.get_tile((column, row))` |
| Pick a tile, corner, or edge under the mouse | `get_tile_from_pixel`, `get_corner_from_pixel`, `get_edge_from_pixel` |
| Find a neighbor, corner, or edge of a tile | `tile.get_neighbour(direction)`, `tile.get_corner(direction)`, `tile.get_edge(direction)` |
| Measure distance and get a set of nearby tiles | `get_distance`, `get_tiles_in_radius`, `get_tiles_in_ring` |
| Plan movement with obstacles and a budget | `find_path`, `get_reachable_tiles`, `find_nearest`, `get_path_cost` |
| Test a straight line for blockers | `get_tiles_in_line`, `has_line_of_sight` |
| Display or remove tile overlays | `highlight_tiles`, `clear_highlights`, `tile.highlight()`, `tile.clear_highlight()` |

## World and board elements

`world.tiles`, `world.corners`, and `world.edges` map positions to
their registered objects. Tile positions are `(column, row)` pairs.
Corners and edges use three-number keys. Keep separate dictionaries
for corners and edges because a key can occur in both.

If a key occurs in both, actor placement and `world.to_pixel(key)`
resolve it as a corner. To get the midpoint of a specific edge, use
`edge.to_pixel()`. The [board game example](../patterns/hex_world_catan.md)
draws roads between the two corner objects returned by
`edge.get_neighbour_corners()`.

For a sparse board, create the world with `empty=True`. Add the
tiles with `add_tile_to_world(position)`, then register any needed
vertices and sides with `add_corner_to_world(position, direction)`
and `add_edge_to_world(position, direction)`. To use corner or edge
picking, register all six corners and edges for each tile. Shared
vertices and sides are merged by position.

```{eval-rst}
.. autoclass:: miniworlds.worlds.hex_world.hex_world.HexWorld
   :members:
```

Tiles also provide the inherited attributes `data` (a dictionary for
game data), `terrain` (the value stored under `data["terrain"]`),
`cost` (the nonnegative cost to enter a tile, default 1), and
`is_blocking` (whether the tile blocks pathfinding by default).

```{eval-rst}
.. autoclass:: miniworlds.worlds.hex_world.hex_tile.HexTile
   :members:
```

```{eval-rst}
.. autoclass:: miniworlds.worlds.hex_world.hex_corner.HexCorner
   :members:
```

```{eval-rst}
.. autoclass:: miniworlds.worlds.hex_world.hex_edge.HexEdge
   :members:
```

## Actor integration and camera

```{eval-rst}
.. autoclass:: miniworlds.worlds.hex_world.hex_world_sensor_manager.HexWorldSensorManager
   :members:
```

```{eval-rst}
.. autoclass:: miniworlds.worlds.hex_world.hex_world_position_manager.HexWorldPositionManager
   :members:
```

```{eval-rst}
.. autoclass:: miniworlds.worlds.hex_world.hex_camera_manager.HexCameraManager
   :members:
```

```{eval-rst}
.. autoclass:: miniworlds.worlds.hex_world.hex_costume.HexCostume
   :members:
```

## Geometry and pathfinding functions

```{eval-rst}
.. automodule:: miniworlds.worlds.hex_world.hex_coords
   :members:
```

```{eval-rst}
.. automodule:: miniworlds.worlds.hex_world.hex_pathfinding
   :members: find_path, get_reachable_tiles
```

