import math
from typing import Any, Union, Tuple

import miniworlds.worlds.world as world_mod
import miniworlds.appearances.appearance as appearance_mod
import miniworlds.appearances.managers.image_background_manager as image_background_manager
import miniworlds.appearances.managers.transformations_background_manager as transformations_background_manager
import pygame
import miniworlds.worlds.world as world_mod


class Background(appearance_mod.Appearance):
    """Background appearance of a world.

    A background can be color-based or image-based, and each world can hold
    multiple background appearances that can be switched at runtime.

    Examples:
        Add an image background:
            world = World()
            world.add_background("images/my_image.png")

        Add a color background:
            world = World()
            world.add_background((255, 0, 0, 255))
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
        self._drawing_commands: list[dict[str, Any]] = []
        self.surface = pygame.Surface(
            (self.world.camera.width, self.world.camera.height)
        )
        self._is_scaled_to_tile = False
        self._pending_window_rects: list[pygame.Rect] = []
        self._image = pygame.Surface(
            (self.parent.width, self.parent.height)
        )  # size set in image()-method
        self.is_scaled = True
        self.transformations_manager = (
            transformations_background_manager.TransformationsBackgroundManager(self)
        )
        self.image_manager = image_background_manager.ImageBackgroundManager(self)

    def set_dirty(self, value="all", status=1):
        """Mark the background as dirty and refresh dependent actor visuals."""
        super().set_dirty(value, status)
        self._blit_to_window_surface()
        if self.world and self.get_manager()._is_display_initialized:
            for actor in self.world.actors:
                actor.costume_manager._is_display_initialized = True
                if actor.costume:
                    actor.costume.set_dirty("all", self.LOAD_NEW_IMAGE)


    def get_manager(self):
        """Return the owning `BackgroundsManager`."""
        return self.world.backgrounds

    @property
    def world(self) -> "world_mod.World":
        """Owning world of this background."""
        return self.parent

    def show_grid(self):
        """Enable grid rendering for this background."""
        self.grid = True

    @property
    def grid(self) -> Union[bool, tuple]:
        """Whether a grid overlay is shown.

        Accepts `True`, `False`, or a color tuple to set the grid color.
        """
        return self._grid

    @grid.setter
    def grid(self, value):
        self._grid = value
        self.set_dirty("all", Background.LOAD_NEW_IMAGE)

    def repaint(self):
        """Called 1/frame from world"""
        if self.world and self.world.app and self.world in self.world.app.running_worlds:
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
            self._pending_window_rects.extend(repaint_rects)

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
        if self.world and self.world.app and self.world in self.world.app.running_worlds:
            self.world.app.window.surface.blit(
                self.image, self.world.camera.screen_topleft
            ) 
            self.world.app.add_display_to_repaint_areas()
            self.repaint()

    def _before_transformation_pipeline(self) -> None:
        self._update_draw_shape()

    def _update_draw_shape(self) -> None:
        super()._update_draw_shape()
        for command in self._drawing_commands:
            shape, arguments = self._drawing_command_to_shape(command)
            self.draw_shape_append(shape, arguments)

    @property
    def drawing_commands(self) -> tuple[dict[str, Any], ...]:
        """Persistent drawing commands rendered onto this background."""
        return tuple(self._drawing_commands)

    def clear_drawing_layer(self, owner=None) -> None:
        """Clear persistent background drawings.

        Args:
            owner: If provided, only commands with this owner id are removed.
        """
        if owner is None:
            self._drawing_commands = []
        else:
            self._drawing_commands = [
                command for command in self._drawing_commands
                if command.get("owner") != owner
            ]
        self.set_dirty("draw_shapes", self.RELOAD_ACTUAL_IMAGE)

    def set_drawing_commands(self, commands) -> None:
        """Replace persistent drawing commands and re-render the background."""
        self._drawing_commands = [dict(command) for command in commands]
        self.set_dirty("draw_shapes", self.RELOAD_ACTUAL_IMAGE)

    def add_drawing_command(self, kind: str, *args, owner=None, **kwargs) -> dict[str, Any]:
        """Add a persistent drawing command to the active background image."""
        command = {"kind": kind, "args": args, "kwargs": kwargs, "owner": owner}
        self._drawing_commands.append(command)
        self.set_dirty("draw_shapes", self.RELOAD_ACTUAL_IMAGE)
        return command

    def draw_line(self, start, end, color, width: int = 1, owner=None):
        return self.add_drawing_command("line", start, end, color, width, owner=owner)

    def draw_polyline(self, points, color, width: int = 1, owner=None):
        return self.add_drawing_command("polyline", list(points), color, width, owner=owner)

    def draw_polygon(self, points, outline=None, fill=None, width: int = 1, owner=None):
        return self.add_drawing_command(
            "polygon", list(points), outline, fill, width, owner=owner
        )

    def draw_circle(self, center, radius, outline=None, fill=None, width: int = 1, owner=None):
        return self.add_drawing_command(
            "circle", center, radius, outline, fill, width, owner=owner
        )

    def draw_dot(self, center, size, color, owner=None):
        return self.add_drawing_command("dot", center, size, color, owner=owner)

    def draw_arc(self, rect, start, extent, color, width: int = 1, owner=None):
        return self.add_drawing_command("arc", rect, start, extent, color, width, owner=owner)

    def draw_text(self, position, text, color=(0, 0, 0), font=None, align="left", owner=None):
        return self.add_drawing_command(
            "text", position, str(text), color, font, align, owner=owner
        )

    def _drawing_command_to_shape(self, command):
        kind = command["kind"]
        args = command["args"]
        if kind == "line":
            start, end, color, width = args
            return pygame.draw.line, [color, start, end, int(width)]
        if kind == "polyline":
            points, color, width = args
            return self._draw_polyline, [points, color, int(width)]
        if kind == "polygon":
            points, outline, fill, width = args
            return self._draw_polygon, [points, outline, fill, int(width)]
        if kind == "circle":
            center, radius, outline, fill, width = args
            return self._draw_circle, [center, radius, outline, fill, int(width)]
        if kind == "dot":
            center, size, color = args
            return pygame.draw.circle, [color, center, max(1, int(size / 2)), 0]
        if kind == "arc":
            rect, start, extent, color, width = args
            return self._draw_arc_degrees, [rect, start, extent, color, int(width)]
        if kind == "text":
            position, text, color, font, align = args
            return self._draw_text, [position, text, color, font, align]
        raise ValueError(f"Unknown drawing command kind: {kind!r}")

    @staticmethod
    def _draw_polyline(surface, points, color, width):
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, width)

    @staticmethod
    def _draw_polygon(surface, points, outline, fill, width):
        if len(points) < 2:
            return
        if fill is not None and len(points) >= 3:
            pygame.draw.polygon(surface, fill, points, 0)
        if outline is not None:
            if len(points) >= 3:
                pygame.draw.polygon(surface, outline, points, width)
            else:
                pygame.draw.line(surface, outline, points[0], points[1], width)

    @staticmethod
    def _draw_circle(surface, center, radius, outline, fill, width):
        radius = abs(int(radius))
        if fill is not None:
            pygame.draw.circle(surface, fill, center, radius, 0)
        if outline is not None and width:
            pygame.draw.circle(surface, outline, center, radius, width)

    @staticmethod
    def _draw_arc_degrees(surface, rect, start, extent, color, width):
        start_radians = math.radians(start)
        end_radians = math.radians(start + extent)
        pygame.draw.arc(surface, color, pygame.Rect(rect), start_radians, end_radians, width)

    @staticmethod
    def _draw_text(surface, position, text, color, font, align):
        font_name, size, style = (font or ("Arial", 8, "normal"))
        del font_name, style
        rendered = pygame.font.Font(None, int(size)).render(text, True, color)
        rect = rendered.get_rect()
        if align == "center":
            rect.center = position
        elif align == "right":
            rect.topright = position
        else:
            rect.topleft = position
        surface.blit(rendered, rect)

    def add_image(self, source: Union[str, Tuple, pygame.Surface]) -> int:
        """Add an image source and immediately refresh the window surface."""
        index = super().add_image(source)
        self._blit_to_window_surface()
        return index

    def _inner_shape(self) -> tuple:
        """Return the inner background rectangle shape.

        Returns:
            pygame.Rect: Inner shape (Rectangle with size of actor)
        """
        size = (self.parent.camera.width, self.parent.camera.height)
        return pygame.draw.rect, [pygame.Rect(0, 0, size[0], size[1]), 0]

    def _outer_shape(self) -> tuple:
        """Return the outer background rectangle shape.

        Returns:
            pygame.Rect: Outer shape (Rectangle with size of actors without filling.)
        """
        size = (self.parent.camera.width, self.parent.camera.height)
        return pygame.draw.rect, [pygame.Rect(0, 0, size[0], size[1]), self.border]

    def get_rect(self):
        """Return the cached rect of the rendered background image."""
        frame = self.world.frame if self.world else 0
        if frame == self._cached_rect[0]:
            return self._cached_rect[1]
        rect = self.image.get_rect()
        self._cached_rect = (frame, rect)
        return rect
