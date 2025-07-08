import pygame
from typing import Tuple, Set, TYPE_CHECKING

import miniworlds.appearances.background as background

if TYPE_CHECKING:
    from miniworlds.actors.actor import Actor
    from miniworlds.worlds.world import World


class CameraManager(pygame.sprite.Sprite):
    """
    CameraManager defines a movable viewport into a 2D world and tracks visible actors.
    It is accessed via `world.camera` and is responsible for view positioning, actor visibility,
    and coordinate transformations.
    """

    def __init__(self, view_x: int, view_y: int, world: "World") -> None:
        # Initialize base class
        super().__init__()
        # Store reference to the world
        self.world: "World" = world

        # Initial top-left positions
        self.screen_topleft: Tuple[int, int] = (0, 0)
        self._topleft: Tuple[int, int] = (0, 0)

        # Set initial world and view dimensions
        self._world_size_x = view_x
        self._world_size_y = view_y
        self.view: Tuple[int, int] = (view_x, view_y)

        # Precompute rects for performance
        self._cached_rect = self.get_rect()
        self._cached_screen_rect = self.get_screen_rect()

        # Actor visibility tracking
        self.view_actors_last_frame: Set["Actor"] = set()
        self._view_actors_actual_frame: Set["Actor"] = set()
        self._view_active_actors: Set["Actor"] = set()
        self._view_update_frame: int = -1

        # Resize control flags
        self._resize = True
        self._status_disable_resize = False
        self._strict = True  # Prevent scrolling outside world bounds
        self.dirty = False

    def _disable_resize(self) -> None:
        """Disable automatic resize handling."""
        self._status_disable_resize = True

    def _enable_resize(self) -> None:
        """Re-enable automatic resize handling."""
        self._status_disable_resize = False
        self._reload_camera()

    @property
    def width(self) -> int:
        """Width of the camera viewport in pixels."""
        return self.view[0]

    @width.setter
    def width(self, value: int) -> None:
        self._set_width(value)

    def _set_width(self, value: int) -> None:
        if value > self._world_size_x:
            self._world_size_x = value
        self.view = (value, self.view[1])
        self._resize = True
        self.dirty = True
        self._reload_camera()

    @property
    def height(self) -> int:
        """Height of the camera viewport in pixels."""
        return self.view[1]

    @height.setter
    def height(self, value: int) -> None:
        self._set_height(value)

    def _set_height(self, value: int) -> None:
        if value > self._world_size_y:
            self._world_size_y = value
        self.view = (self.view[0], value)
        self._resize = True
        self.dirty = True
        self._reload_camera()

    @property
    def world_size_x(self) -> int:
        """Width of the world in pixels."""
        return self._world_size_x

    @world_size_x.setter
    def world_size_x(self, value: int) -> None:
        self.view = (min(self.view[0], value), self.view[1])
        self._world_size_x = value
        self.dirty = True
        self._reload_camera()

    @property
    def world_size_y(self) -> int:
        """Height of the world in pixels."""
        return self._world_size_y

    @world_size_y.setter
    def world_size_y(self, value: int) -> None:
        self.view = (self.view[0], min(self.view[1], value))
        self._world_size_y = value
        self.dirty = True
        self._reload_camera()

    @property
    def world_size(self) -> Tuple[int, int]:
        """Returns world size as (width, height)."""
        return self._world_size_x, self._world_size_y

    @world_size.setter
    def world_size(self, value: Tuple[int, int]) -> None:
        self._world_size_x, self._world_size_y = value

    @property
    def x(self) -> int:
        """Camera x-position (top-left corner in world coordinates)."""
        return self._topleft[0]

    @x.setter
    def x(self, value: int) -> None:
        self.topleft = (value, self._topleft[1])
        self.dirty = True

    @property
    def y(self) -> int:
        """Camera y-position (top-left corner in world coordinates)."""
        return self._topleft[1]

    @y.setter
    def y(self, value: int) -> None:
        self.topleft = (self._topleft[0], value)
        self.dirty = True

    @property
    def topleft(self) -> Tuple[int, int]:
        """Top-left corner of the camera in world coordinates."""
        return self._topleft

    @topleft.setter
    def topleft(self, value: Tuple[int, int]) -> None:
        self._set_topleft(value)

    def _set_topleft(self, value: Tuple[int, int]) -> None:
        if self._strict:
            value = (self._limit_x(value[0]), self._limit_y(value[1]))
        if value != self._topleft:
            self._topleft = value
            self._reload_actors_in_view()
        self.dirty = True

    def _limit_x(self, value: int) -> int:
        return max(0, min(value, self._world_size_x - self.view[0]))

    def _limit_y(self, value: int) -> int:
        return max(0, min(value, self._world_size_y - self.view[1]))

    @property
    def rect(self) -> pygame.Rect:
        """Returns camera rect in world coordinates."""
        return self.get_rect() if self.dirty else self._cached_rect

    @property
    def screen_rect(self) -> pygame.Rect:
        """Returns camera rect in screen coordinates."""
        return self.get_screen_rect() if self.dirty else self._cached_screen_rect

    @property
    def world_rect(self) -> pygame.Rect:
        """Returns the full world rect."""
        return self.get_world_rect()

    @property
    def center(self) -> Tuple[float, float]:
        """Returns center of camera in world coordinates."""
        return (self.topleft[0] + self.view[0] / 2, self.topleft[1] + self.view[1] / 2)

    def get_rect(self) -> pygame.Rect:
        """
        Returns the camera rectangle in world coordinates.

        Returns:
            A pygame.Rect representing the current viewport's world area.

        Examples:
            >>> world.camera.get_rect()
        """
        return pygame.Rect(*self._topleft, *self.view)

    def get_screen_rect(self) -> pygame.Rect:
        """
        Returns the camera rectangle in screen coordinates.

        Returns:
            A pygame.Rect representing where the camera appears on screen.

        Examples:
            >>> world.camera.get_screen_rect()
        """
        return pygame.Rect(*self.screen_topleft, *self.view)

    def get_world_rect(self) -> pygame.Rect:
        """
        Returns the full world rectangle from the camera's current origin.

        Returns:
            A pygame.Rect representing the visible and scrolled world area.

        Examples:
            >>> world.camera.get_world_rect()
        """
        return pygame.Rect(*self._topleft, self.world_size_x, self.world_size_y)

    def get_screen_position(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Convert world coordinates to screen coordinates.

        Args:
            pos: Position in world coordinates.

        Returns:
            Position in screen coordinates.

        Examples:
            >>> world.camera.get_screen_position((100, 200))
        """
        return (
            self.screen_topleft[0] + pos[0] - self.topleft[0],
            self.screen_topleft[1] + pos[1] - self.topleft[1]
        )

    def get_local_position(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Convert world coordinates to camera-local coordinates.

        Args:
            pos: Global position in the world.

        Returns:
            Local position relative to the camera.

        Examples:
            >>> world.camera.get_local_position((500, 400))
        """
        return pos[0] - self.topleft[0], pos[1] - self.topleft[1]

    def get_global_coordinates_for_world(self, pos: Tuple[int, int]) -> Tuple[int, int]:
        """
        Convert local camera position to global world position.

        Args:
            pos: Position relative to the camera.

        Returns:
            Global world position.

        Examples:
            >>> world.camera.get_global_coordinates_for_world((100, 50))
        """
        return pos[0] + self.topleft[0], pos[1] + self.topleft[1]

    def _reload_actors_in_view(self) -> None:
        """Marks actors in view as dirty for redraw."""
        for actor in self.get_actors_in_view():
            actor.dirty = 1

    def get_actors_in_view(self) -> Set["Actor"]:
        actor_rect_pairs = [
            (actor, actor.position_manager.get_global_rect())
            for actor in self.world.actors
        ]
        current_frame_actors = {
            actor for actor, rect in actor_rect_pairs
            if self.rect.colliderect(rect)
        }
        self.view_actors_last_frame = self._view_actors_actual_frame
        self._view_actors_actual_frame = current_frame_actors
        self._view_active_actors = current_frame_actors.union(self.view_actors_last_frame)
        self._view_update_frame = self.world.frame
        return self._view_active_actors

    def is_actor_in_view(self, actor: "Actor") -> bool:
        return actor.position_manager.get_global_rect().colliderect(self.rect)

    def from_actor(self, actor: "Actor") -> None:
        """
        Move camera to center on a given actor.

        Examples:
            >>> world.camera.from_actor(actor)
        """
        if actor.center:
            center = actor.center
            self.topleft = (
                center[0] - self.view[0] // 2 - actor.width // 2,
                center[1] - self.view[1] // 2 - actor.height // 2
            )
        else:
            self.topleft = (0, 0)

    def is_in_screen(self, pixel: Tuple[int, int]) -> bool:
        return bool(pixel) and self.screen_rect.collidepoint(pixel)

    def _reload_camera(self) -> None:
        """Internal: reloads geometry and triggers world resize."""
        self._clear_camera_cache()
        if self._resize and not self._status_disable_resize:
            self.world.app.resize()
            self._resize = False
        self.world.background.set_dirty("all", background.Background.RELOAD_ACTUAL_IMAGE)

    def _clear_camera_cache(self) -> None:
        """Clears view tracking for actor visibility."""
        self._view_actors_actual_frame.clear()
        self._view_update_frame = -1

    def _update(self) -> None:
        """Called each frame to refresh geometry if needed."""
        if self.dirty:
            self._cache_rects()
            self.dirty = False

    def _cache_rects(self) -> None:
        """Caches world and screen rects."""
        self._cached_rect = self.get_rect()
        self._cached_screen_rect = self.get_screen_rect()
