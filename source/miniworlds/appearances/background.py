from typing import Union, Tuple

import miniworlds.worlds.world as world_mod
import miniworlds.appearances.appearance as appearance_mod
import miniworlds.appearances.managers.image_background_manager as image_background_manager
import miniworlds.appearances.managers.transformations_background_manager as transformations_background_manager
import miniworlds.base.app as app
import pygame
import miniworlds.worlds.world as world_mod


class Background(appearance_mod.Appearance):
    """
    The class describes the background of a world.

    A ``background`` can be an image or a color:

    Each world has one or more backgrounds that can be switched between.
    In addition, each background also has several pictures (or colors) between which you can switch.

    Examples:

        Add an image as background

        .. code-block:: python

            world = World()
            World.add_background(images/my_image.png)

        Add a color as background:

        .. code-block:: python

            world = World()
            World.add_background((255, 0,0, 0))

        ..or alternative way: Create background with property:

        .. code-block:: python

            from miniworlds import *

            world = World()
            world.background =(255,0,0)
            world.run()

    """

    def __init__(self, world=None):
        super().__init__()
        self._fill_color = (150, 150, 150, 255)  # for default image
        self.parent: "world_mod.World" = (
            world  #: The parent of a Background is the associated world.
        )
        "Background.parent The world to which the background belongs to"
        # Register image actions which you can be triggered
        self._grid = False
        self._grid_color = (255, 0, 255)
        self.surface = pygame.Surface(
            (self.world.camera.width, self.world.camera.height)
        )
        self._is_scaled_to_tile = False
        self._image = pygame.Surface(
            (self.parent.width, self.parent.height)
        )  # size set in image()-method
        self.is_scaled = True
        self.transformations_manager = (
            transformations_background_manager.TransformationsBackgroundManager(self)
        )
        self.image_manager = image_background_manager.ImageBackgroundManager(self)

    def set_dirty(self, value="all", status=1):
        super().set_dirty(value, status)
        self._blit_to_window_surface()
        if self.world and self.get_manager()._is_display_initialized:
            for actor in self.world.actors:
                actor.costume_manager._is_display_initialized = True
                if actor.costume:
                    actor.costume.set_dirty("all", self.LOAD_NEW_IMAGE)


    def get_manager(self):
        return self.world.backgrounds

    @property
    def world(self) -> "world_mod.World":
        return self.parent

    def show_grid(self):
        self.grid = True

    @property
    def grid(self) -> Union[bool, tuple]:
        """Shows a grid-overlay

        grid can be `True`, `False` or a color-tuple

        Examples:

            Show grid:

            .. code-block:: python

                from miniworlds import *

                world = TiledWorld(4,4)
                world.tile_margin = 10
                background = world.add_background("images/stone.png")
                background.is_textured = True
                actor = Actor()
                @actor.register
                def on_key_down(self, key):
                    self.move_right()
                background.grid = True
                world.run()

            .. image:: ../_images/grid.png
                :alt: Textured image

        """
        return self._grid

    @grid.setter
    def grid(self, value):
        self._grid = value
        self.set_dirty("all", Background.LOAD_NEW_IMAGE)

    def repaint(self):
        """Called 1/frame from world"""
        if self.world in app.App.running_worlds:
            self.world.actors.clear(self.surface, self.image)
            repaint_rects = self.world.actors.draw(self.surface)
            if self.world.camera.screen_topleft[0] != 0 or self.world.camera.screen_topleft[1] != 0:
                new_repaint_rects = []
                for rect in repaint_rects:
                    rect.topleft = (
                        self.world.camera.screen_topleft[0] + rect.topleft[0],
                        self.world.camera.screen_topleft[1] + rect.topleft[1],
                    )
                    new_repaint_rects.append(rect)
                repaint_rects = new_repaint_rects
            self.world.app.repaint_areas.extend(repaint_rects)

    def _after_transformation_pipeline(self) -> None:
        self.surface = pygame.Surface(
            (self.world.camera.width, self.world.camera.height)
        )
        self.surface.blit(self.image, self.surface.get_rect())
        self._blit_to_window_surface()
        for actor in self.world.camera.get_actors_in_view():
            actor.dirty = 1

    def _blit_to_window_surface(self):
        """Blits background to window surface"""
        if self.world in app.App.running_worlds:
            self.world.app.window.surface.blit(
                self.image, self.world.camera.screen_topleft
            ) 
            self.world.app.add_display_to_repaint_areas()
            self.repaint()

    def add_image(self, source: Union[str, Tuple, pygame.Surface]) -> int:
        super().add_image(source)
        self._blit_to_window_surface()

    def _inner_shape(self) -> tuple:
        """Returns inner shape of costume

        Returns:
            pygame.Rect: Inner shape (Rectangle with size of actor)
        """
        size = (self.parent.camera.width, self.parent.camera.height)
        return pygame.draw.rect, [pygame.Rect(0, 0, size[0], size[1]), 0]

    def _outer_shape(self) -> tuple:
        """Returns outer shape of costume

        Returns:
            pygame.Rect: Outer shape (Rectangle with size of actors without filling.)
        """
        size = (self.parent.camera.width, self.parent.camera.height)
        return pygame.draw.rect, [pygame.Rect(0, 0, size[0], size[1]), self.border]

    def get_rect(self):
        frame = self.world.frame if self.world else 0
        if frame < self._cached_rect[0]:
            return self._cached_rect[1]
        rect = self.image.get_rect()
        self._cached_rect = (frame, rect)
        return rect