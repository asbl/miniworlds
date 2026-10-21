from typing import Tuple

import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.tiled_world_position_manager as tiled_position_manager


class HexWorldPositionManager(tiled_position_manager.TiledWorldPositionManager):
    """Position manager for actors on hex worlds.

    Actor sizes are derived from the hex bounding box instead of the
    square tile size.
    """

    def get_size(self) -> Tuple[int, int]:
        if self.actor.world:
            tile_size = self.actor.world.tile_size
            width = hex_coords.hex_width(tile_size) * self._scaled_size[0]
            height = hex_coords.hex_height(tile_size) * self._scaled_size[1]
            return (int(width), int(height))
        return (0, 0)
