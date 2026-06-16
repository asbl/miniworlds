from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Set, Tuple, Union, cast

import pygame

import miniworlds.appearances.background as background_mod
import miniworlds.appearances.backgrounds_manager as backgrounds_manager
import miniworlds.base.app as app
import miniworlds.worlds.manager.collision_manager as coll_manager
import miniworlds.worlds.manager.data_manager as data_manager
import miniworlds.worlds.manager.draw_manager as draw_manager
import miniworlds.worlds.manager.layout_manager as layout_manager
import miniworlds.worlds.manager.mainloop_manager as mainloop_manager
import miniworlds.worlds.manager.mouse_manager as mouse_manager
import miniworlds.worlds.manager.music_manager as world_music_manager
import miniworlds.worlds.manager.sound_manager as world_sound_manager
import miniworlds.worlds.manager.spatial_index as spatial_index
import miniworlds.worlds.world_background_facade as world_background_facade
import miniworlds.worlds.world_runtime_facade as world_runtime_facade

if TYPE_CHECKING:
    import miniworlds.actors.actor as actor_mod
    import miniworlds.worlds.world as world_mod


class WorldInitializationFacade:
    """Builds the internal manager graph for World while keeping the public API stable."""

    def __init__(self, world: "world_mod.World"):
        self.world = world

    def initialize_pre_base_state(
        self, x: Union[int, Tuple[int, int]] = 400, y: int = 400
    ) -> None:
        x, y = self.world._normalize_constructor_dimensions(x, y)
        # pygame.init() runs once at miniworlds import time. When a host
        # (e.g. the web player) calls pygame.quit() between runs while the
        # interpreter keeps living, all pygame modules must be re-initialized
        # before a new world is built.
        if not pygame.get_init():
            pygame.init()
        self.world._validate_parameters(x, y)
        self.world.camera = self.world._get_camera_manager_class()(x, y, self.world)
        self.world.actors = pygame.sprite.LayeredDirty()
        # LayeredDirty falls back to redrawing every sprite plus a full-screen
        # update whenever one draw call exceeds its timing threshold (12.5 ms
        # by default). On slow targets (Pyodide/wasm) the first draw always
        # exceeds it, so the group would stay in full-redraw mode forever and
        # each frame would cost O(all actors) blits. miniworlds tracks dirty
        # state itself, so always keep the group in dirty-rect mode.
        self.world.actors.set_timing_threshold(1_000_000.0)

    def initialize_post_base_state(self) -> None:
        self._initialize_timing_state()
        self._initialize_actor_state()
        self._initialize_app()
        self._initialize_managers()
        self._initialize_facades()

    def _initialize_timing_state(self) -> None:
        self.world.clock = pygame.time.Clock()
        self.world._fps = 60
        self.world._tick_rate = 1
        self.world.frame = 0

    def _initialize_actor_state(self) -> None:
        self.world._timed_objects = []
        self.world._dynamic_actors = pygame.sprite.Group()
        # Use dynamic cell size based on world dimensions for optimal spatial indexing
        # Smaller worlds: smaller cells, larger worlds: larger cells
        # Formula: cell_size ≈ max_dimension / 16 (empirically determined)
        world_width = getattr(self.world, "columns", 400) or 400
        world_height = getattr(self.world, "rows", 400) or 400
        max_dim = max(world_width, world_height)
        cell_size = max(32, min(128, max_dim // 16))
        self.world._spatial_index = spatial_index.SpatialIndex(cell_size=cell_size)
        self.world._blocking_spatial_index = spatial_index.SpatialIndex(
            cell_size=cell_size
        )
        self.world._blocking_actors = cast(Set["actor_mod.Actor"], set())
        self.world._blocking_registry_version = 0
        self.world._blocking_static_rect_cache = (-1, -1, [])
        self.world._registered_methods = cast(list[Callable], [])

    def _initialize_app(self) -> None:
        if not app.App.get_running_app():
            self.world.app = app.App("miniworlds", self.world)
        else:
            self.world.app = cast("app.App", app.App.get_running_app())

    def _initialize_managers(self) -> None:
        self.world.backgrounds = backgrounds_manager.BackgroundsManager(self.world)
        self.world._layout = layout_manager.LayoutManager(self.world, self.world.app)
        self.world.data = data_manager.DataManager(self.world, self.world.app)
        self.world.background = background_mod.Background(self.world)
        self.world.background.update()
        self.world.mouse = mouse_manager.MouseManager(self.world)
        self.world.draw = draw_manager.DrawManager(self.world)
        self.world.music = world_music_manager.MusicManager(self.world.app)
        self.world.sound = world_sound_manager.SoundManager(self.world.app)
        self.world._mainloop = self.world._get_mainloopmanager_class()(
            self.world, self.world.app
        )
        self.world._collision_manager = coll_manager.CollisionManager(self.world)

    def _initialize_facades(self) -> None:
        self.world._background_facade = world_background_facade.WorldBackgroundFacade(
            self.world
        )
        self.world._runtime_facade = world_runtime_facade.WorldRuntimeFacade(self.world)
