import miniworlds.worlds.tiled_world.tile as tile_mod
import miniworlds.worlds.tiled_world.corner as corner_mod
import miniworlds.worlds.tiled_world.edge as edge_mod


class TileFactory:
    def __init__(self):
        self.tile_cls = tile_mod.Tile
        self.corner_cls = corner_mod.Corner
        self.edge_cls = edge_mod.Edge