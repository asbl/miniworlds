import pygame

import miniworlds.worlds.hex_world.hex_coords as hex_coords
import miniworlds.worlds.tiled_world.tiled_world_camera_manager as tiled_camera_manager


class HexCameraManager(tiled_camera_manager.TiledCameraManager):
    """CameraManager for hex worlds.

    View and world sizes are measured in hexes (columns, rows); pixel
    sizes are derived from the pointy-top hex geometry.
    """

    @property
    def width(self) -> int:
        """Camera view width in pixels."""
        return int(hex_coords.hex_width(self.world.tile_size) * (self.view[0] + 0.5))

    @property
    def height(self) -> int:
        """Camera view height in pixels."""
        return int(self.world.tile_size * (1.5 * self.view[1] + 0.5))

    @property
    def topleft(self) -> tuple[int, int]:
        """Top-left corner of the camera view in pixels."""
        return (
            int(self._topleft[0] * hex_coords.hex_width(self.world.tile_size)),
            int(self._topleft[1] * 1.5 * self.world.tile_size),
        )

    def get_world_rect(self) -> pygame.Rect:
        width, height = hex_coords.world_pixel_size(
            self.world_size_x, self.world_size_y, self.world.tile_size
        )
        return pygame.Rect(0, 0, int(width), int(height))
