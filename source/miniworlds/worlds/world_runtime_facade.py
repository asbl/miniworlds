from __future__ import annotations

import asyncio
import math
from typing import TYPE_CHECKING, Iterable, List, Optional, Tuple, cast

import miniworlds.actors.actor as actor_mod
import miniworlds.base.exceptions as exceptions
import miniworlds.tools.timer as timer
import miniworlds.worlds.manager.position_manager as position_manager

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod


class WorldRuntimeFacade:
    def __init__(self, world: "world_mod.World"):
        self.world = world

    def start(self) -> None:
        self.world.is_running = True

    def stop(self, frames: int = 0) -> None:
        if frames == 0:
            self.world.is_running = False
        else:
            timer.ActionTimer(frames, self.world.stop, 0)

    def run(
        self,
        fullscreen: bool = False,
        fit_desktop: bool = False,
        replit: bool = False,
        event: Optional[str] = None,
        data: Optional[object] = None,
    ) -> None:
        self.world.app.prepare_mainloop()
        self.world.backgrounds._init_display()
        self.world._mainloop.dirty_all()
        if not self.world._is_setup_completed:
            self.world.on_setup()
        if not (self.world.frame == 0 and self.world._default_start_running):
            self.world.is_running = True

        if event:
            self.world.app.event_manager.to_event_queue(event, data)

        async def main():
            await self.world.app.run(
                self.world.backgrounds.image,
                fullscreen=fullscreen,
                fit_desktop=fit_desktop,
                replit=replit,
            )

        try:
            asyncio.run(main())
        except RuntimeError as error:
            if "event loop is running" in str(error):
                loop = asyncio.get_event_loop()
                loop.create_task(main())
            else:
                raise

    def is_in_world(self, position: Tuple[float, float]) -> bool:
        x, y = position
        return 0 < x < self.world.camera.world_size_x and 0 < y < self.world.camera.world_size_y

    def send_message(self, message: str, data: Optional[object] = None) -> None:
        event_data = message if data is None else (message, data)
        self.world.app.event_manager.to_event_queue("message", event_data)

    def switch_world(self, new_world: "world_mod.World", reset: bool = False) -> None:
        self.world.camera.switch_world(new_world, reset)

    def load_world_from_db(self, file: str) -> "world_mod.World":
        return self.world.data.load_world_from_db(file)

    def load_actors_from_db(
        self, file: str, actor_classes: list[type[actor_mod.Actor]]
    ) -> list[actor_mod.Actor]:
        return self.world.data.load_actors_from_db(file, actor_classes)

    def save_to_db(self, file: str) -> None:
        return self.world.data.save_to_db(file)

    def quit(self, exit_code: int = 0) -> None:
        self.world.app.quit(exit_code)

    def reset(self) -> None:
        self.clear()
        if hasattr(self.world, "on_setup"):
            self.world._is_setup_completed = False
            self.world.on_setup()
            self.world._is_setup_completed = True

    def clear(self) -> None:
        self.world.app.event_manager.event_queue.clear()
        for background in list(self.world.backgrounds):
            self.world.backgrounds.remove_appearance(background)
        for actor in list(self.world.actors):
            actor.remove()

    @staticmethod
    def _is_valid_point(point: Tuple[float, float]) -> bool:
        return (
            isinstance(point, tuple)
            and len(point) == 2
            and all(isinstance(value, (int, float)) for value in point)
        )

    def get_from_pixel(
        self, position: Tuple[float, float]
    ) -> Optional[Tuple[float, float]]:
        if not self._is_valid_point(position):
            return None
        x, y = position
        if 0 <= x < self.world.camera.width and 0 <= y < self.world.camera.height:
            return x, y
        return None

    def to_pixel(self, position: Tuple[float, float]) -> Tuple[float, float]:
        return position

    def _iter_candidates_for_world_position(
        self, position: Tuple[float, float]
    ) -> Iterable[actor_mod.Actor]:
        camera = getattr(self.world, "camera", None)
        if camera is None:
            return self.world.actors
        camera_rect = getattr(camera, "rect", None)
        if camera_rect is not None and camera_rect.collidepoint(position):
            get_actors_in_view = getattr(camera, "get_actors_in_view", None)
            if callable(get_actors_in_view):
                return get_actors_in_view()
        return self.world.actors

    def _iter_candidates_for_pixel(
        self, pixel: Tuple[float, float]
    ) -> Iterable[actor_mod.Actor]:
        camera = getattr(self.world, "camera", None)
        if camera is None:
            return self.world.actors
        screen_rect = getattr(camera, "screen_rect", None)
        if screen_rect is not None and screen_rect.collidepoint(pixel):
            get_actors_in_view = getattr(camera, "get_actors_in_view", None)
            if callable(get_actors_in_view):
                return get_actors_in_view()
        return ()

    def detect_actors(self, position: Tuple[float, float]) -> List[actor_mod.Actor]:
        if not self._is_valid_point(position):
            return []
        detected_actors: List[actor_mod.Actor] = []
        for actor in self._iter_candidates_for_world_position(position):
            try:
                actor_rect = actor.position_manager.get_global_rect()
            except (AttributeError, exceptions.MissingActorPartsError):
                continue
            if actor_rect.collidepoint(position):
                detected_actors.append(actor)
        return cast(List[actor_mod.Actor], detected_actors)

    def get_actors_from_pixel(
        self, pixel: Tuple[float, float]
    ) -> List[actor_mod.Actor]:
        if not self._is_valid_point(pixel):
            return []
        detected_actors: List[actor_mod.Actor] = []
        for actor in self._iter_candidates_for_pixel(pixel):
            try:
                actor_rect = actor.position_manager.get_screen_rect()
            except (AttributeError, exceptions.MissingActorPartsError):
                continue
            if actor_rect.collidepoint(pixel):
                detected_actors.append(actor)
        return cast(List[actor_mod.Actor], detected_actors)

    @staticmethod
    def distance_to(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        return math.hypot(pos1[0] - pos2[0], pos1[1] - pos2[1])

    @staticmethod
    def direction_to(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        return position_manager.Positionmanager.direction_from_two_points(pos1, pos2)