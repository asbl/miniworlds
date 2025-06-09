from typing import Union
import pygame

import miniworlds.base.app as app
from miniworlds.base.exceptions import NoValidWorldRectError



class Rect(pygame.Rect):
    @classmethod
    def create(cls, rect: Union[tuple, pygame.Rect]):
        if type(rect) == tuple:
            return cls(rect[0], rect[1], 1, 1)
        elif type(rect) == pygame.Rect:
            return cls(rect.x, rect.y, rect.width, rect.height)
        else:
            raise NoValidWorldRectError("No valid world direction")

    @classmethod
    def from_position(cls, position, dimensions=None, world=None):
        if world is None:
            world = app.App.running_world
        if dimensions is None:
            new_rect = pygame.Rect(0, 0, world.tile_size, world.tile_size)
        else:
            new_rect = pygame.Rect(0, 0, dimensions[0], dimensions[1])
        new_rect.topleft = position
        return new_rect

    @classmethod
    def from_actor(cls, actor):
        return Rect.create(actor.get_global_rect())

    @property
    def world(self):
        return app.App.running_world
