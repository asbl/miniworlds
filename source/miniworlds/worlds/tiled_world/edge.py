import miniworlds.worlds.tiled_world.tile as tile
import miniworlds.worlds.tiled_world.tile_elements as tile_elements
import miniworlds.worlds.tiled_world.tiled_world as tiled_world_mod


class Edge(tile_elements.TileDelimiter):
    tile_vectors = {
        "w": [(-0.5, 0), (0.5, 0)],
        "n": [(0, 0.5), (0, -0.5)],
        "o": [(-0.5, 0), (0.5, 0)],
        "s": [(0, 0.5), (0, -0.5)],
    }

    direction_angles = {
        "o": 0,
        "s": 90,
        "w": 0,
        "n": 90,
    }

    angles = {
        "o": 0,
        "s": 1,
        "w": 2,
        "n": 3,
    }

    @staticmethod
    def direction_vectors():
        return tile.Tile.edge_vectors

    @staticmethod
    def get_position_pixel_dict(world):
        return world.get_edge_points()

    @classmethod
    def from_position(cls, position, world: "tiled_world_mod.TiledWorld"):
        return world.get_edge(position)

    def start_angle(self):
        return 0
