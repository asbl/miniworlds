# Tutorial: Hex Worlds

In a `HexWorld`, actors can stand on hexagonal tiles, on the corners of
those tiles, or on their edges. The examples below are complete scripts.
Run them one at a time. Each `world.run()` starts the window and the event loop.

If this is your first Miniworlds program, start with
the chapter “Die erste Welt” in the [interactive course](index.md).

## Create a world and place an actor

`HexWorld(7, 5, tile_size=40)` creates seven columns and five rows. The
first tile is `(0, 0)` and the last is `(6, 4)`. The hexagons have a
point at the top. Here `tile_size=40` means 40 pixels from the center of
a hexagon to a vertex.

```python
from miniworlds import Actor, HexWorld

world = HexWorld(7, 5, tile_size=40)
world.background.grid = True

marker = Actor((2, 3))
marker.fill_color = (0, 120, 0)

world.run()
```

You will see a green hexagon in column 2, row 3. The actor provides the
visible marker. The tile at the same position belongs to the grid and
can store game data such as terrain, movement cost, or a resource.

## Read positions and move between neighbors

Tile positions have the form `(column, row)`. Columns increase to the
right and rows increase downwards. Odd rows (1, 3, 5, …) are shifted
half a hex width to the right. For example, northeast of `(2, 2)` is
`(2, 1)`, and northeast of `(2, 3)` is `(3, 2)`.

| Direction | Name | Angle | Neighbor of `(2, 2)` | Neighbor of `(2, 3)` |
| --- | --- | --- | --- | --- |
| `"no"` | Northeast | 30° | `(2, 1)` | `(3, 2)` |
| `"o"` | East | 90° | `(3, 2)` | `(3, 3)` |
| `"so"` | Southeast | 150° | `(2, 3)` | `(3, 4)` |
| `"sw"` | Southwest | 210° | `(1, 3)` | `(2, 4)` |
| `"w"` | West | 270° | `(1, 2)` | `(1, 3)` |
| `"nw"` | Northwest | 330° | `(1, 1)` | `(2, 2)` |

`world.get_tile(position)` returns the tile at a known position and
raises `TileNotFoundError` for a missing tile. Use
`tile.get_neighbour(direction)` to look up a neighbor. It returns
`None` at the board boundary or beside a gap. Use
`tile.get_neighbour_tiles()` to get all existing neighbors.

Press the right or left arrow to move one tile east or west. The
neighbor check keeps the actor on the board. The angle equivalents in
the table can also be passed to `move_in_direction`.

```python
from miniworlds import Actor, HexWorld

world = HexWorld(7, 5, tile_size=40)
world.background.grid = True

robot = Actor((2, 3))
robot.fill_color = (200, 30, 30)

@robot.register
def on_key_down(self, keys):
    directions = {"right": "o", "left": "w"}
    for key in keys:
        direction = directions.get(key.lower())
        if direction is not None:
            tile = world.get_tile(self.position)
            if tile.get_neighbour(direction) is not None:
                self.move_in_direction(direction)
            break

world.run()
```

## Measure distance, radius, and lines

`world.get_distance(a, b)` gives the number of steps on an open hex grid.
It accounts for the staggered rows and ignores obstacles and movement
costs. You can supply tile positions, tiles, or actors standing on tiles.
A tile also offers `tile.get_distance_to(other)`.

`world.get_tiles_in_radius(center, 2)` returns existing tiles up to two
steps away, starting with the center. Pass `include_center=False` to
leave it out. The tile method `center.get_tiles_in_radius(2)` leaves the
center out by default. A ring contains tiles at exactly the given
distance. Radii must be whole numbers, and negative radii give an empty list.

The example marks tiles within two steps in blue and tiles exactly three
steps away in orange. A gray wall interrupts the straight line between
`(1, 4)` and `(7, 4)`. The terminal shows a distance of 6 and
`Visible: False`.

```python
from miniworlds import HexWorld

world = HexWorld(9, 9, tile_size=30)
world.background.grid = True

center = world.get_tile((4, 4))
world.highlight_tiles(world.get_tiles_in_radius(center, 2), (0, 120, 255, 90))
world.highlight_tiles(world.get_tiles_in_ring(center, 3), (255, 120, 0, 90))

start, goal = (1, 4), (7, 4)
line = world.get_tiles_in_line(start, goal)
world.highlight_tiles(line, (200, 0, 0, 90))
center.is_blocking = True
center.highlight((90, 90, 90, 200))

print("Distance:", world.get_distance(start, goal))
print("Visible:", world.has_line_of_sight(start, goal))

world.run()
```

`get_tiles_in_line` returns the existing tiles along the straight line,
including both endpoints when present. `has_line_of_sight` checks for
blockers strictly between those endpoints. A blocked target can still
be visible.

## Pick tiles, corners, and edges with the mouse

Mouse handlers receive a window pixel `(x, y)`. Use
`world.get_tile_from_pixel(mouse_pos)` for the tile under the pointer,
`world.get_corner_from_pixel(mouse_pos)` for a nearby vertex, or
`world.get_edge_from_pixel(mouse_pos)` for a nearby edge midpoint.
Check for `None` before accessing the result. Use
`world.get_from_pixel(mouse_pos)` when you only need the tile position
within the visible camera area.

From a known tile you can also get a corner with `tile.get_corner("n")`
or an edge with `tile.get_edge("o")`. Corner directions are `"n"`,
`"no"`, `"so"`, `"s"`, `"sw"`, and `"nw"`. Edge directions are the
same as the six movement directions. Adjacent tiles share the same
corner or edge object where they meet. Use its `.position` as a key
in a dictionary for that type of board element.

In the example, left-click near a corner to place a red marker and
right-click near an edge to place a brown marker. The camera shows
only part of the board. Click positions still resolve to the visible
tiles, corners, and edges.

```python
from miniworlds import Actor, HexWorld

world = HexWorld(12, 10, tile_size=36)
world.background.grid = True
world.camera.width = 7
world.camera.height = 5
world.camera.topleft = (2, 2)

@world.register
def on_mouse_left_down(self, mouse_pos):
    corner = self.get_corner_from_pixel(mouse_pos)
    if corner is None:
        return
    settlement = Actor(corner.position)
    settlement.fill_color = (200, 30, 30)
    settlement.size = (0.25, 0.25)

@world.register
def on_mouse_right_down(self, mouse_pos):
    edge = self.get_edge_from_pixel(mouse_pos)
    if edge is None:
        return
    x, y = edge.to_pixel()
    left, top = self.camera.topleft
    self.background.draw_dot((x - left, y - top), 10, (90, 60, 30))

world.run()
```

Set `camera.width`, `camera.height`, and `camera.topleft` in grid units.
Reading those properties gives pixel values. Read `camera.x` and
`camera.y` for the camera offset in grid units.
`world.to_pixel((column, row))` gives the tile center in **world pixels**.
On a corner or edge object, `.to_pixel()` gives the vertex or edge
midpoint. The example subtracts the fixed camera offset before drawing
the dot because background drawings use pixels relative to the camera.
The mouse methods take **window pixels**. When scrolling or docking the
world, pass them the original event position.

## Store terrain and find a route

Use `tile.data` as a dictionary for your game. Setting `tile.terrain`
stores a value under `tile.data["terrain"]`. In this example, water
blocks the route and entering a swamp costs three movement points.
Every other tile costs one point to enter.

Click a destination to show the cheapest route in yellow and move the
robot along it. Clicking water clears the old route and stops the robot.

```python
from collections import deque

from miniworlds import Actor, HexWorld

world = HexWorld(9, 7, tile_size=36)
world.background.grid = True

for position in [(4, 2), (4, 3), (4, 4)]:
    water = world.get_tile(position)
    water.terrain = "water"
    water.is_blocking = True
    water.highlight((0, 80, 200, 160))

swamp = world.get_tile((3, 3))
swamp.terrain = "swamp"
swamp.cost = 3
swamp.highlight((120, 90, 30, 160))

robot = Actor((1, 3))
robot.fill_color = (200, 30, 30)
steps = deque()
shown_path = []

@world.register
def on_mouse_left_down(self, mouse_pos):
    goal = self.get_tile_from_pixel(mouse_pos)
    if goal is None:
        return

    self.clear_highlights(shown_path)
    swamp.highlight((120, 90, 30, 160))
    path = self.find_path(robot, goal)
    steps.clear()
    steps.extend(path[1:])
    shown_path[:] = path[1:]
    self.highlight_tiles(shown_path)

    if path:
        print("Movement cost:", self.get_path_cost(path))
    else:
        print("No route")

@robot.register
def act(self):
    if steps and world.frame % 10 == 0:
        self.position = steps.popleft().position

world.run()
```

`find_path` includes both the start and the goal, so `path[1:]`
contains the steps still to take. A start equal to the goal gives a
one-tile path. An unreachable goal gives an empty list. The start tile
is free, and later steps add their destination tile's cost. Costs can
be zero or fractional. The default search also treats a tile with a
blocking actor as blocked.

Path queries return a plan. The example advances along that plan by
assigning positions. If terrain or blockers change while a unit is
moving, recompute its route before taking the next step.

### Show a movement budget and find the cheapest target

`get_reachable_tiles(start, 3)` lists every tile you can reach with
three movement points, including the start. `find_nearest` accepts a
function that identifies eligible targets. It chooses by total
movement cost. Here the adjacent forest costs four points to enter,
so the search chooses the forest two steps away. The terminal shows
`Target: (3, 5) Cost: 2.0`.

```python
from miniworlds import HexWorld

world = HexWorld(7, 7, tile_size=40)
world.background.grid = True

start = world.get_tile((3, 3))
near_forest = world.get_tile((4, 3))
near_forest.terrain = "forest"
near_forest.cost = 4
far_forest = world.get_tile((3, 5))
far_forest.terrain = "forest"

reachable = world.get_reachable_tiles(start, 3)
world.highlight_tiles(reachable, (0, 120, 255, 100))
near_forest.highlight((0, 120, 0, 150))

def is_forest(tile):
    return tile.terrain == "forest"

path = world.find_nearest(start, is_forest, max_cost=3)
if path:
    world.highlight_tiles(path)
    print("Target:", path[-1].position, "Cost:", world.get_path_cost(path))

world.run()
```

With `find_nearest`, a blocked target can be the final tile. Stop one
step before it if you want the actor to stand next to the target.
For a unit with its own movement rules, pass `blocked(tile)` or
`cost(tile)` callbacks to replace the default rules for that query.
If you use a custom cost function, pass the same function to
`get_path_cost` when you total the route.

## Highlight the tile under the mouse

Register `on_tile_enter` and `on_tile_leave` to update the highlight as
the pointer crosses a tile boundary. The fourth color component
controls opacity. Each tile has one highlight, drawn below actors.
Applying a new highlight replaces its previous color.

```python
from miniworlds import HexWorld

world = HexWorld(7, 5, tile_size=40)
world.background.grid = True

@world.register
def on_tile_enter(self, tile):
    tile.highlight((255, 255, 0, 100))

@world.register
def on_tile_leave(self, tile):
    tile.clear_highlight()

world.run()
```

`world.hovered_tile` holds the current tile or `None` while hover is
tracked by a tile enter, tile leave, or mouse motion handler.

Continue with the [board game example](../patterns/hex_world_catan.md)
to combine tiles, corners, edges, and tile data. See the
[HexWorld API reference](../api/world_hex.md) for method signatures
and options.
