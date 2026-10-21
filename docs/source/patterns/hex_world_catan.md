# Hex Worlds and a Mini-Catan Board

A `HexWorld` consists of hexagonal tiles. Hexes are addressed with
`(column, row)` coordinates, like tiles in a `TiledWorld`. Odd rows are
shifted half a hex to the right.

Actors can be placed on three kinds of positions:

* **Tiles** (the hexes themselves), e.g. `(2, 3)`
* **Corners** (shared by up to three hexes), e.g. the `"no"` corner of a hex
* **Edges** (shared by two hexes), e.g. the `"o"` edge of a hex

This is exactly the structure of a Catan board: land hexes, settlements
on corners, and roads on edges.

## Create a hex world

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True
world.run()
```

## Build a Catan-like board

The 19 land hexes of a Catan board are arranged in rows of 3, 4, 5, 4,
and 3 hexes. Actors placed on hexes are drawn as hexagons.

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

land_positions = [
    (2, 1), (3, 1), (4, 1),
    (2, 2), (3, 2), (4, 2), (5, 2),
    (1, 3), (2, 3), (3, 3), (4, 3), (5, 3),
    (1, 4), (2, 4), (3, 4), (4, 4),
    (2, 5), (3, 5), (4, 5),
]
terrain_colors = [
    (0, 120, 0),      # forest
    (220, 180, 60),   # field
    (120, 200, 60),   # meadow
    (150, 150, 150),  # mountain
    (200, 90, 30),    # hill
    (230, 210, 160),  # desert
]

for number, position in enumerate(land_positions):
    actor = miniworlds.Actor(position)
    actor.fill_color = terrain_colors[number % len(terrain_colors)]
    actor.border = 1

world.run()
```

## Click hexes, corners, and edges

`world.get_tile_from_pixel(mouse_pos)` returns the hex under the mouse,
`world.get_corner_from_pixel(mouse_pos)` the nearest corner, and
`world.get_edge_from_pixel(mouse_pos)` the nearest edge. The corner and
edge queries return `None` if the pixel is outside the world.

The example places a settlement (small circle) on the clicked corner and
a road (small rectangle) on the clicked edge:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

@world.register
def on_mouse_left(self, mouse_pos):
    tile = world.get_tile_from_pixel(mouse_pos)
    print("you clicked the hex", tile.position)

@world.register
def on_mouse_right(self, mouse_pos):
    corner = world.get_corner_from_pixel(mouse_pos)
    settlement = miniworlds.Actor(corner.position)
    settlement.fill_color = (200, 30, 30)
    settlement.size = (0.3, 0.3)

world.run()
```

## Query the neighborhood

`world.get_tiles_in_radius(position, radius)` returns all hexes within
a given hex distance. `tile.get_neighbour_tiles()` returns the up to six
neighbors of a hex. This is useful for Catan rules such as "the robber
blocks all hexes around the desert".

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

center = world.get_tile((3, 3))
for tile in world.get_tiles_in_radius(center.position, 1):
    actor = miniworlds.Actor(tile.position)
    actor.fill_color = (0, 120, 0)

world.run()
```
