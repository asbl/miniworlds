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

You can pass a position, a tile, or an actor. With
`include_center=False` the hex itself is left out. A tile also knows its
surroundings:

```python
import miniworlds

world = miniworlds.HexWorld(9, 9, tile_size=30)
world.background.grid = True

center = world.get_tile((4, 4))
for tile in center.get_tiles_in_radius(2):
    tile.highlight((0, 120, 255, 90))
for tile in center.get_tiles_in_ring(3):
    tile.highlight((255, 120, 0, 90))

east = center.get_neighbour("o")
if east is not None:
    east.highlight((255, 0, 0, 120))

world.run()
```

`tile.get_neighbour(direction)` returns the neighbor in one direction
(`"o"`, `"so"`, `"sw"`, `"w"`, `"nw"`, `"no"`) or `None` at the border
of the world.

### Distances and lines

`world.get_distance(a, b)` returns the number of steps between two hexes.
It does not depend on the row parity, so it is the right way to measure
distances on a hex grid (`tile.get_distance_to(other)` does the same).
Do not compare the offset coordinates `(column, row)` directly, because
the shifted rows make them misleading.

`world.get_tiles_in_line(start, end)` returns the hexes on the straight
line between two hexes. Together with `tile.is_blocking` this answers
line-of-sight questions:

```python
import miniworlds

world = miniworlds.HexWorld(9, 7, tile_size=30)
world.background.grid = True

wall = world.get_tile((4, 3))
wall.is_blocking = True
wall.highlight((90, 90, 90, 200))

line = world.get_tiles_in_line((1, 3), (7, 3))
visible = world.has_line_of_sight((1, 3), (7, 3))
for tile in line:
    tile.highlight((0, 200, 0, 90) if visible else (200, 0, 0, 90))

print("Distance:", world.get_distance((1, 3), (7, 3)), "visible:", visible)

world.run()
```

The queries accept only whole numbers as radius; a negative radius
returns an empty list.

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
`world.get_tile_from_pixel(mouse_pos)` returns the hex under the mouse,
or `None` if the click is outside the world:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

@world.register
def on_mouse_left(self, mouse_pos):
    tile = world.get_tile_from_pixel(mouse_pos)
    if tile is None:
        return
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

## Step 8: Store data on hexes

Every hex can carry game data. `tile.data` is a dictionary for anything
your game needs, `tile.terrain` is a shortcut for `tile.data["terrain"]`:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

for position, tile in world.tiles.items():
    tile.terrain = "forest" if position[0] % 2 == 0 else "field"
    tile.data["dice_number"] = 2 + (position[0] + position[1]) % 11

tile = world.get_tile((3, 3))
print(tile.terrain, tile.data["dice_number"])

world.run()
```

## Step 9: Find paths

`world.find_path(start, goal)` returns the cheapest way from one hex to
another as a list of hexes. Stepping onto a hex costs `tile.cost`
(default `1`). A hex with `tile.is_blocking = True` cannot be entered, and
neither can a hex with a blocking actor (`actor.is_blocking = True`).

Click a hex to walk the robot there around the water:

```python
import miniworlds

world = miniworlds.HexWorld(9, 9, tile_size=36)
world.background.grid = True

for position in [(3, 3), (4, 3), (5, 3), (3, 4), (5, 4)]:
    water = world.get_tile(position)
    water.is_blocking = True
    water.highlight((0, 80, 200, 160))

robot = miniworlds.Actor((1, 4))
robot.fill_color = (200, 30, 30)
route = []

@world.register
def on_mouse_left(self, mouse_pos):
    goal = world.get_tile_from_pixel(mouse_pos)
    if goal is None:
        return
    route[:] = world.find_path(robot, goal)[1:]

@robot.register
def act(self):
    if route and world.frame % 10 == 0:
        self.position = route.pop(0).position

world.run()
```

`find_path` returns an empty list if there is no way. Slow terrain is just
a higher cost, for example `swamp.cost = 3`.

`world.get_reachable_tiles(start, max_cost)` returns every hex the actor
can reach with a movement budget, walking around blocked hexes:

```python
import miniworlds

world = miniworlds.HexWorld(9, 9, tile_size=36)
world.background.grid = True
world.get_tile((4, 3)).is_blocking = True

for tile in world.get_reachable_tiles((4, 4), 2):
    tile.highlight((0, 200, 0, 90))

world.run()
```

`world.find_nearest(start, is_target)` finds the cheapest way to the
nearest hex that satisfies a condition. The target may be blocked, for
example an enemy that blocks its own hex:

```python
import miniworlds

world = miniworlds.HexWorld(9, 9, tile_size=36)
world.background.grid = True

for position in [(7, 2), (2, 7)]:
    world.get_tile(position).terrain = "forest"
    world.get_tile(position).highlight((0, 120, 0, 150))

path = world.find_nearest((4, 4), lambda tile: tile.terrain == "forest")
for tile in path:
    tile.highlight((255, 255, 0, 120))
print("cost:", world.get_path_cost(path))

world.run()
```

`world.has_line_of_sight(start, goal)` answers whether a blocked hex hides
the goal on the straight line between two hexes:

```python
import miniworlds

world = miniworlds.HexWorld(9, 9, tile_size=36)
world.background.grid = True
world.get_tile((4, 4)).is_blocking = True
world.get_tile((4, 4)).highlight((0, 80, 200, 160))

print(world.has_line_of_sight((1, 4), (7, 4)))  # False: the wall is in the way
print(world.has_line_of_sight((1, 1), (7, 1)))  # True

world.run()
```

## Step 10: Highlight the hex under the mouse

A world can react when the mouse enters or leaves a hex.
`tile.highlight(color)` colors a hex below the actors;
`tile.clear_highlight()` removes the color again:

```python
import miniworlds

world = miniworlds.HexWorld(7, 7, tile_size=40)
world.background.grid = True

@world.register
def on_tile_enter(self, tile):
    tile.highlight((255, 255, 0, 100))

@world.register
def on_tile_leave(self, tile):
    tile.clear_highlight()

world.run()
```

`world.hovered_tile` always holds the hex under the mouse, or `None`.

From here you can continue in the pattern
[Hex Worlds and a Mini-Catan Board](../patterns/hex_world_catan.md)
and add your own game rules: dice, resources, and trading are not part
of the framework — they belong in your game code.

The full interface is documented in the
[HexWorld API reference](../api/world_hex.md).
