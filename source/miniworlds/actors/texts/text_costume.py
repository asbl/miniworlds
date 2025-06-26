import pygame
import math

import miniworlds.appearances.costume as costume
import miniworlds.actors.texts.text_transformation_manager as text_transformation_manager

class TextCostume(costume.Costume):
    def __init__(self, actor):
        super().__init__(actor)
        self.set_image((0, 0, 0, 0))
        self.transformations_manager = (
            text_transformation_manager.TextTransformationsCostumeManager(self)
        )

    def _set_actor_default_values(self):
        self.fill_color = (255, 255, 255, 255)
        self.border = 0
        self.is_rotatable = True
        self.border_color = (100, 100, 100, 255)
        self.border = 0

    def _inner_shape(self):
        return None

    def _outer_shape(self):
        return pygame.draw.rect, [
            pygame.Rect(0, 0, self.parent.size[0], self.parent.size[1]),
            self.border,
        ]
        
    def _update_draw_shape(self):
        super()._update_draw_shape()
        """Sets self.size by costume.font_size"""
        if not self.actor.world.actors_fixed_size or (
            hasattr(self.actor, "fixed_size") and self.actor.fixed_size
        ):  # fixed size e.g. on Tiledworlds
            if self.actor.max_width != 0:
                width = min(self.get_text_width(), self.actor.max_width)
            else:
                width = self.get_text_width()
            height = self.get_text_height()
            self.actor.set_size((width, height))
        if self.actor.world.actors_fixed_size:
            self.scale_to_size()

    def scale_to_size(self, width=None, height=None):
        if not width:
            width = self.actor.size[0]
        if width == 0:
            width = math.inf
        if not height:
            height = self.actor.size[1]
        if height == 0:
            height = math.inf
        _font_size = 0
        self.font_manager.set_font_size(_font_size, update=False)
        while self.get_text_width() < width and self.get_text_height() < height:
            _font_size += 1
            self.font_manager.set_font_size(_font_size, update=False)
        return _font_size

    @property
    def text(self):
        """Sets text of appearance
        Examples:

            .. code-block:: python

                explosion = Explosion(position=other.position.up(40).left(40))
                explosion.costume.is_animated = True
                explosion.costume.text_position = (100, 100)
                explosion.costume.text = "100"
        """
        return self.font_manager.text

    @text.setter
    def text(self, value):
        self.set_text(value)
        
    def get_text_width(self):
        return self.font_manager.get_text_width()

    def get_text_height(self):
        return self.font_manager.get_text_height()

    def set_text(self, value):
        if value == "":
            self.font_manager.text = ""
            self.set_dirty("write_text", self.__class__.RELOAD_ACTUAL_IMAGE)
        else:
            self.font_manager.text = value
        self.set_dirty("write_text", self.__class__.RELOAD_ACTUAL_IMAGE)