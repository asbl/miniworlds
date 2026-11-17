import pygame
import pygame

import miniworlds.appearances.managers.transformations_manager as transformations_manager
import miniworlds.worlds.hex_world.hex_coords as hex_coords


class TransformationsBackgroundManager(transformations_manager.TransformationsManager):
    def __init__(self, appearance):
        super().__init__(appearance)
        self.transformations_pipeline.extend([
            # Highlights come before the grid, so the grid lines stay visible on top.
            {"key": "tile_highlights", "func": self.transformation_tile_highlights, "attr": "_has_tile_highlights", "is_optional": False},
            {"key": "grid", "func": self.transformation_grid, "attr": "grid", "is_optional": False},
        ])

    def get_size(self):
        size = (self.appearance.parent.camera.width, self.appearance.parent.camera.height)
        return size

    def transformation_tile_highlights(self, image: pygame.Surface, appearance) -> pygame.Surface:
        """Draw the translucent highlights of hex tiles (camera-local)."""
        parent = self.appearance.parent
        highlights = getattr(parent, "_tile_highlights", None)
        if not highlights:
            return image
        camera_rect = parent.camera.get_rect()
        tile_size = parent.tile_size
        offsets = list(hex_coords.corner_pixel_offsets(tile_size).values())
        margin = hex_coords.hex_width(tile_size)
        overlay = pygame.Surface(image.get_size(), pygame.SRCALPHA)
        for position, color in highlights.items():
            x, y = hex_coords.hex_center(position, tile_size)
            x -= camera_rect.left
            y -= camera_rect.top
            if (x < -margin or y < -margin
                    or x > image.get_width() + margin or y > image.get_height() + margin):
                continue
            pygame.draw.polygon(
                overlay, color, [(x + dx, y + dy) for dx, dy in offsets], 0
            )
        image.blit(overlay, (0, 0))
        return image

    def transformation_grid(self, image: pygame.Surface, appearance) -> pygame.Surface:
        parent = self.appearance.parent
        if getattr(parent, "is_hex", False):
            return self._transformation_grid_hex(image, appearance)
        i = 0
        j = 0
        while i <= parent.height:
            pygame.draw.line(image, appearance._grid_color, (0, i), (self.get_width(), i), 1)
            i += parent.tile_size
        while j <= parent.width:
            pygame.draw.line(image, appearance._grid_color, (j, 0), (j, self.get_height()), 1)
            j += parent.tile_size

        return image

    def _transformation_grid_hex(self, image: pygame.Surface, appearance) -> pygame.Surface:
        parent = self.appearance.parent
        # Draw only the hexes visible in the camera window: the background
        # image is a camera-sized window anchored at the camera topleft, and
        # redraws happen on every camera move. Drawing every tile of the
        # world scales the redraw with the world size instead of the view.
        camera_rect = parent.camera.get_rect()
        tile_size = parent.tile_size
        width = hex_coords.hex_width(tile_size)
        row_height = 1.5 * tile_size
        left = camera_rect.left
        top = camera_rect.top
        col0 = int((camera_rect.left - 2 * width) // width)
        col1 = int(camera_rect.right // width) + 1
        row0 = int((camera_rect.top - 2 * tile_size) // row_height)
        row1 = int(camera_rect.bottom // row_height) + 1
        color = appearance._grid_color
        offsets = list(hex_coords.corner_pixel_offsets(tile_size).values())
        tiles = parent.tiles
        for row in range(row0, row1 + 1):
            row_shift = 0.5 * (row & 1) * width
            y = row_height * row + tile_size - top
            for col in range(col0, col1 + 1):
                if (col, row) not in tiles:
                    continue
                x = width * col + width / 2 + row_shift - left
                pygame.draw.polygon(
                    image, color,
                    [(x + offset[0], y + offset[1]) for offset in offsets],
                    1,
                )
        return image
