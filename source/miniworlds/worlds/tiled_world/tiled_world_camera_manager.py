import pygame

import miniworlds.appearances.background as background
import miniworlds.worlds.manager.camera_manager as camera_manager
import miniworlds.actors.actor as actor_mod


class TiledCameraManager(camera_manager.CameraManager):
    """
    CameraManager implementation for tile-based worlds.
    Converts tile coordinates into pixel-based camera viewports.
    """


    @property
    def width(self) -> int:
        """
        Returns:
            Camera view width in pixels.
        """
        return self.view[0] * self.world.tile_size

    @width.setter
    def width(self, value: int):
        """
        Sets the width of the camera view in tiles.

        Args:
            value (int): New width in tiles.
        """
        self._set_width(value)
        self.dirty = True

    @property
    def height(self) -> int:
        """
        Returns:
            Camera view height in pixels.
        """
        return self.view[1] * self.world.tile_size

    @height.setter
    def height(self, value: int):
        """
        Sets the height of the camera view in tiles.

        Args:
            value (int): New height in tiles.
        """
        self._set_height(value)
        self.dirty = True

    @property
    def topleft(self) -> tuple[int, int]:
        """
        Returns:
            Top-left corner of the camera view in pixels.
        """
        return (
            self._topleft[0] * self.world.tile_size,
            self._topleft[1] * self.world.tile_size,
        )

    @topleft.setter
    def topleft(self, value: tuple[int, int]):
        """
        Sets the top-left corner of the camera in tile coordinates.

        Args:
            value (tuple): Tile coordinates for top-left corner.
        """
        self._set_topleft(value)
        self.dirty = True

    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(*self.topleft, self.width, self.height)

    def get_world_rect(self) -> pygame.Rect:
        return pygame.Rect(*self._topleft, self.world_size_x * self.world.tile_size, self.world_size_y * self.world.tile_size) 

    def from_actor(self, actor: "actor_mod.Actor") -> None:
        """
        Centers the camera on the given actor's position.

        Args:
            actor (Actor): The actor to center the camera on.
        """
        if actor.center:
            position = actor.position
            width = self.view[0] // 2
            height = self.view[1] // 2
            self.topleft = (
                position[0] - width,
                position[1] - height,
            )
        else:
            self.topleft = (0, 0)

    def _limit_x(self, value: int) -> int:
        """
        Constrains horizontal camera movement within world bounds.

        Args:
            value (int): Proposed X tile index.

        Returns:
            int: Corrected X tile index within limits.
        """
        if value < 0:
            return 0
        elif value >= self.world_size_x - self.view[0]:
            return self.world_size_x - self.view[0]
        else:
            return value

    def _limit_y(self, value: int) -> int:
        if value < 0:
            return 0
        elif value >= self.world_size_y - self.view[1]:
            return self.world_size_y - self.view[1]
        else:
            return value

    def _update(self):
        self._reload_camera()
        self.dirty = True