# Tutorial: Hex Worlds

In this tutorial you build a world made of hexagons, step by step.
Hexagonal worlds are used for board games like *Catan*:
land hexes, settlements on corners, and roads on edges.

If you have never worked with worlds before, start with the chapter
[Die erste Welt](https://github.com/copilotstudent/course-sync/tree/main/courses/miniworlds_examples)
in the interactive course.

## Step 1: Create a hex world

A `HexWorld` is created with `(columns, rows)` and a `tile_size`:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

world.run()
```

Hexes are addressed with `(column, row)` coordinates, like tiles in a
`TiledWorld`. Odd rows are shifted half a hex to the right.

## Step 2: Place actors on hexes

An actor placed on a hex position is drawn as a hexagon:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

forest = miniworlds.Actor((2, 3))
forest.fill_color = (0, 120, 0)

desert = miniworlds.Actor((4, 2))
desert.fill_color = (230, 210, 160)

world.run()
```

## Step 3: Query neighbors

`world.get_tile(position)` returns a single hex.
`tile.get_neighbour_tiles()` returns the up to six neighboring hexes.

The example colors the center hex and all its neighbors:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

center = world.get_tile((3, 3))
center_actor = miniworlds.Actor(center.position)
center_actor.fill_color = (200, 30, 30)

for tile in center.get_neighbour_tiles():
    actor = miniworlds.Actor(tile.position)
    actor.fill_color = (0, 120, 0)

world.run()
```

`world.get_tiles_in_radius(position, radius)` returns all hexes within
a given hex distance, ordered from the center outwards.
`world.get_tiles_in_ring(position, radius)` returns only the hexes at
exactly the given distance, in ring traversal order.

## Step 4: Move actors from hex to hex

Actors move from hex to hex with the six hex directions `"no"`, `"o"`,
`"so"`, `"sw"`, `"w"`, and `"nw"`:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

robot = miniworlds.Actor((3, 3))
robot.fill_color = (200, 30, 30)

@robot.register
def act(self):
    if world.frame % 20 == 0:
        self.move_in_direction("no")

world.run()
```

Every `move_in_direction` call moves the actor exactly one hex,
independent of the row parity. The directions can also be given as
degrees: `"no"` is 30, `"o"` is 90, `"so"` is 150, `"sw"` is 210,
`"w"` is 270, and `"nw"` is 330.

## Step 5: React to clicks

With `@world.register` you can react to mouse clicks.
`world.get_tile_from_pixel(mouse_pos)` returns the hex under the mouse:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

@world.register
def on_mouse_left(self, mouse_pos):
    tile = world.get_tile_from_pixel(mouse_pos)
    actor = miniworlds.Actor(tile.position)
    actor.fill_color = (0, 120, 0)

world.run()
```

## Step 6: Settlements and roads

Corners and edges are positions, too.
`world.get_corner_from_pixel(mouse_pos)` returns the nearest corner,
`world.get_edge_from_pixel(mouse_pos)` the nearest edge.
Both return `None` if the pixel is outside the world, for example when
a toolbar or console is attached to the world.

A left click places a settlement (small circle) on a corner,
a right click places a road (small rectangle) on an edge:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

@world.register
def on_mouse_left(self, mouse_pos):
    corner = world.get_corner_from_pixel(mouse_pos)
    settlement = miniworlds.Actor(corner.position)
    settlement.fill_color = (200, 30, 30)
    settlement.size = (0.3, 0.3)

@world.register
def on_mouse_right(self, mouse_pos):
    edge = world.get_edge_from_pixel(mouse_pos)
    road = miniworlds.Actor(edge.position)
    road.fill_color = (90, 60, 30)
    road.size = (0.6, 0.15)

world.run()
```

## Step 7: A mini-Catan board

A Catan board has 19 land hexes, arranged in rows of 3, 4, 5, 4, and 3:

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

From here you can continue in the pattern
[Hex Worlds and a Mini-Catan Board](../patterns/hex_world_catan.md)
and add your own game rules: dice, resources, and trading are not part
of the framework — they belong in your game code.

The full interface is documented in the
[HexWorld API reference](../api/world_hex.md).
