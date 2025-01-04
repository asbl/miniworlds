import pygame

import miniworlds.appearances.background as background
import miniworlds.worlds.manager.camera_manager as camera_manager
import miniworlds.actors.actor as actor_mod


class TiledCameraManager(camera_manager.CameraManager):

    @property
    def width(self):
        return self.view[0] * self.world.tile_size

    @width.setter
    def width(self, value):
        self._set_width(value)

    @property
    def height(self):
        return self.view[1] * self.world.tile_size

    @height.setter
    def height(self, value):
        self._set_height(value)

    @property
    def topleft(self):
        return (
            self._topleft[0] * self.world.tile_size,
            self._topleft[1] * self.world.tile_size,
        )

    @topleft.setter
    def topleft(self, value):
        self._set_topleft(value)

    def get_rect(self) -> pygame.Rect:
        """Gets rect of camera view."""
        return pygame.Rect(
            self.topleft[0],
            self.topleft[1],
            self.width,
            self.height,
        )

    def from_actor(self, actor: "actor_mod.Actor") -> None:
        """Gets camera from actor center-position"""
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

    def _limit_x(self, value):
        if value < 0:
            return 0
        elif value >= self.world_size_x - self.view[0]:
            return self.world_size_x - self.view[0]
        else:
            return value
