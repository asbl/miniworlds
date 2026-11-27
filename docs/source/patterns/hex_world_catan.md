# Hex Worlds and a Mini-Catan Board

This example combines 19 land tiles with settlements on vertices and
roads on edges. It builds on the
[Hex Worlds tutorial](../tutorial/hex_world.md).

## Build the island

The grid is seven columns by seven rows. Only the positions listed in
`land_rows` belong to the island. The five land rows contain 3, 4, 5,
4, and 3 tiles. Both even rows start at column 2, so they are centered
between the shifted odd rows.

Each land tile stores a terrain name and a dice number. Its six corners
form the polygon that shows the terrain. The `land` dictionary also lets
the placement rules test whether a corner or edge touches the island.

## Place pieces on shared corners and edges

Run the script below and use these controls.

- Left-click near a land corner to place a settlement. The corner and
  its immediate neighbors must be free.
- Right-click near an edge to place a road. The edge must touch land,
  have a settlement at one end, and be free.
- Press Space to distribute resources for a sample roll of 8. The
  center tile has number 8. Place a settlement on one of its corners
  to see a gain printed in the terminal.

A shared corner has one `.position`, even if you look it up from
different land tiles. The same applies to edges. The script uses these
positions as keys in `settlements` and `roads`, so both sides of a tile
boundary refer to the same piece.

```python
from miniworlds import Actor, HexWorld

world = HexWorld(7, 7, tile_size=40)
world.background.grid = True

land_rows = [
    (1, range(2, 5)),
    (2, range(2, 6)),
    (3, range(1, 6)),
    (4, range(2, 6)),
    (5, range(2, 5)),
]
terrain_types = [
    ("forest", (0, 120, 0)),
    ("field", (220, 180, 60)),
    ("pasture", (120, 200, 60)),
    ("mountain", (150, 150, 150)),
    ("hill", (200, 90, 30)),
]
dice_numbers = (5, 6, 9, 10)
land = {}
settlements = {}
roads = {}

for row, columns in land_rows:
    for column in columns:
        position = (column, row)
        tile = world.get_tile(position)
        index = len(land)
        tile.terrain, color = terrain_types[index % len(terrain_types)]
        tile.data["dice_number"] = dice_numbers[index % len(dice_numbers)]
        land[position] = tile

        points = []
        for corner in tile.get_neighbour_corners():
            points.append(corner.to_pixel())
        world.background.draw_polygon(points, fill=color)

land[(3, 3)].data["dice_number"] = 8

def touches_land(part):
    for tile in part.get_neighbour_tiles():
        if tile.position in land:
            return True
    return False

def can_build_settlement(corner):
    if not touches_land(corner) or corner.position in settlements:
        return False
    for neighbour in corner.get_neighbour_corners():
        if neighbour.position in settlements:
            return False
    return True

def can_build_road(edge):
    if not touches_land(edge) or edge.position in roads:
        return False
    for endpoint in edge.get_neighbour_corners():
        if endpoint.position in settlements:
            return True
    return False

@world.register
def on_mouse_left_down(self, mouse_pos):
    corner = self.get_corner_from_pixel(mouse_pos)
    if corner is None or not can_build_settlement(corner):
        return

    marker = Actor(corner.position)
    marker.layer = 1
    marker.fill_color = (200, 30, 30)
    marker.size = (0.25, 0.25)
    settlements[corner.position] = "Red"

@world.register
def on_mouse_right_down(self, mouse_pos):
    edge = self.get_edge_from_pixel(mouse_pos)
    if edge is None or not can_build_road(edge):
        return

    first, second = edge.get_neighbour_corners()
    self.background.draw_line(first.to_pixel(), second.to_pixel(), (90, 60, 30), 6)
    roads[edge.position] = "Red"

def collect(dice_roll):
    gains = []
    for tile in land.values():
        if tile.data["dice_number"] != dice_roll:
            continue
        for corner in tile.get_neighbour_corners():
            owner = settlements.get(corner.position)
            if owner is not None:
                gains.append((owner, tile.terrain))
    return gains

@world.register
def on_key_down_space(self):
    print("Gains for roll 8:", collect(8))

world.run()
```

## Follow a placement or resource payout

`get_neighbour_tiles()` on a corner or edge answers which existing
tiles touch it. `corner.get_neighbour_corners()` follows one edge in
each direction from the corner. `edge.get_neighbour_corners()` gives
the two endpoints. The script draws the road as a line between them.
The full board is visible here, so the endpoints' world pixels can
be used directly on the background. These queries work both in the
middle of the island and on its coast.

For a payout, the script starts from the tile that matches the roll
and visits its six corners with `tile.get_neighbour_corners()`. Each
occupied corner contributes one `(owner, terrain)` pair. For example,
with one settlement on the center tile the output is
`Gains for roll 8: [('Red', 'hill')]`.

The example uses one player and a fixed roll so you can reproduce the
placement and payout. For a playable version, store the current
player in the piece dictionaries, apply ownership when checking
connections, roll two dice, and add the returned gains to inventories.

The [HexWorld API reference](../api/world_hex.md) lists the other
adjacency methods, including the edges incident to a corner and the
edges that share an endpoint.
