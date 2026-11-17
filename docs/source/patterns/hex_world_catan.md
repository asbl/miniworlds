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
`world.get_edge_from_pixel(mouse_pos)` the nearest edge. All three
queries return `None` if the pixel is outside the world.

The example places a settlement (small circle) on the clicked corner and
a road (small rectangle) on the clicked edge:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

@world.register
def on_mouse_left(self, mouse_pos):
    tile = world.get_tile_from_pixel(mouse_pos)
    if tile is None:
        return
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

## Build rules with corners and edges

Corners and edges know their neighbours, so the placement rules of Catan
need only a few lines:

* `corner.get_neighbour_corners()` returns the up to three corners one
  hex side away,
* `corner.get_neighbour_edges()` returns the up to three edges that meet at
  the corner,
* `edge.get_neighbour_corners()` returns the two corners at the ends of an
  edge,
* `edge.get_neighbour_edges()` returns the edges that touch the edge,
* `tile.get_neighbour_corners()` and `tile.get_neighbour_edges()` return the
  six corners and edges of a hex.

The distance rule ("no settlement next to another settlement") and the
connection rule ("a road must touch one of your settlements") look like
this:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True
settlements = {}

def can_build_settlement(corner):
    if corner.position in settlements:
        return False
    for neighbour in corner.get_neighbour_corners():
        if neighbour.position in settlements:
            return False
    return True

def can_build_road(edge):
    for end in edge.get_neighbour_corners():
        if end.position in settlements:
            return True
    return False

@world.register
def on_mouse_left(self, mouse_pos):
    corner = world.get_corner_from_pixel(mouse_pos)
    if corner is not None and can_build_settlement(corner):
        settlement = miniworlds.Actor(corner.position)
        settlement.fill_color = (200, 30, 30)
        settlement.size = (0.3, 0.3)
        settlements[corner.position] = settlement

@world.register
def on_mouse_right(self, mouse_pos):
    edge = world.get_edge_from_pixel(mouse_pos)
    if edge is not None and can_build_road(edge):
        road = miniworlds.Actor(edge.position)
        road.fill_color = (90, 60, 30)
        road.size = (0.6, 0.15)

world.run()
```

## Resources and dice with tile data

Each hex can store its terrain and dice number in `tile.data`. After a dice
roll, the settlements on the corners of the matching hexes collect the
resource:

```python
import random

import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

for tile in world.get_tiles_in_radius((3, 3), 1):
    tile.terrain = "forest"
    tile.data["dice_number"] = random.randint(2, 12)

def collect(dice_roll, owners):
    """owners maps corner positions to player names."""
    gains = []
    for tile in world.tiles.values():
        if tile.data.get("dice_number") != dice_roll:
            continue
        for corner in tile.get_neighbour_corners():
            if corner.position in owners:
                gains.append((owners[corner.position], tile.terrain))
    return gains

print(collect(8, {}))

world.run()
```

