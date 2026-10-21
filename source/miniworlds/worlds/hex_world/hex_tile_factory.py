import miniworlds.worlds.hex_world.hex_corner as hex_corner_mod
import miniworlds.worlds.hex_world.hex_edge as hex_edge_mod
import miniworlds.worlds.hex_world.hex_tile as hex_tile_mod
import miniworlds.worlds.tiled_world.tile_factory as tile_factory


class HexTileFactory(tile_factory.TileFactory):
    def __init__(self):
        self.tile_cls = hex_tile_mod.HexTile
        self.corner_cls = hex_corner_mod.HexCorner
        self.edge_cls = hex_edge_mod.HexEdge
