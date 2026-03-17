from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple, Type, Union

import pygame

if TYPE_CHECKING:
    import miniworlds.actors.actor as actor_mod


class ActorSensorFacade:
    """Provides a focused internal adapter for Actor sensor and collision helper methods."""

    def __init__(self, actor: "actor_mod.Actor"):
        self.actor = actor

    def detect_all(
        self,
        actors: Union[str, "actor_mod.Actor", Type["actor_mod.Actor"]] = None,
        direction: int = 0,
        distance: int = 0,
    ) -> List["actor_mod.Actor"]:
        if distance == 0:
            return self.actor.sensor_manager.detect_actors(actors)
        return self.actor.sensor_manager.detect_actors_at(actors, direction, distance)

    def detect(self, *args, **kwargs) -> Union["actor_mod.Actor", None]:
        if not args:
            actors = kwargs.pop("filter") if "filter" in kwargs else None
            distance = kwargs.pop("distance") if "distance" in kwargs else None
            direction = (
                kwargs.pop("direction")
                if "direction" in kwargs
                else self.actor.direction
            )
        else:
            actors = args[0] if len(args) > 0 else None
            distance = args[1] if len(args) >= 2 else None
            direction = args[2] if len(args) >= 3 else self.actor.direction
        if not distance:
            return self.actor.sensor_manager.detect_actor(filter=actors)
        return self.actor.sensor_manager.detect_actors_at(
            filter=actors,
            direction=direction,
            distance=distance,
        )

    def detect_borders(self, distance: int = 0) -> List[str]:
        return self.actor.sensor_manager.detect_borders(distance)

    def detect_left_border(self) -> bool:
        return "left" in self.actor.sensor_manager.detect_borders(0)

    def detect_right_border(self) -> bool:
        return "right" in self.actor.sensor_manager.detect_borders(0)

    def detect_top_border(self) -> bool:
        return "top" in self.actor.sensor_manager.detect_borders(0)

    def detecting_bottom_border(self) -> bool:
        return "bottom" in self.actor.sensor_manager.detect_borders(0)

    def detect_color(self, color: Tuple = None) -> bool:
        return self.actor.sensor_manager.detect_color(color)

    def detect_color_at(
        self,
        direction: int = None,
        distance: int = 0,
    ) -> Union[Tuple, List]:
        return self.actor.sensor_manager.detect_color_at(direction, distance)

    def detect_actors_at(self, direction=None, distance=0, actors=None) -> list:
        return self.actor.sensor_manager.detect_actors_at(actors, direction, distance)

    def detect_actor_at(
        self,
        direction=None,
        distance=0,
        actors=None,
    ) -> Union["actor_mod.Actor", None]:
        found_actors = self.actor.sensor_manager.detect_actors_at(
            actors,
            direction,
            distance,
        )
        if found_actors:
            return found_actors[0]
        return None

    def detect_actors_in_front(self, actors=None, distance=1) -> list:
        return self.actor.sensor_manager.detect_actors_at(
            actors,
            self.actor.direction,
            distance,
        )

    def detect_actor_in_front(
        self,
        actors=None,
        distance=1,
    ) -> Union["actor_mod.Actor", None]:
        found_actors = self.actor.sensor_manager.detect_actors_at(
            actors,
            self.actor.direction,
            distance,
        )
        if found_actors:
            return found_actors[0]
        return None

    def detect_point(self, position: Tuple[float, float]) -> bool:
        return self.actor.sensor_manager.detect_point(position)

    def detect_pixel(self, position: Tuple[float, float]) -> bool:
        return self.actor.sensor_manager.detect_pixel(position)

    def detect_rect(self, rect: Union[Tuple, pygame.rect.Rect]) -> bool:
        return self.actor.sensor_manager.detect_rect(rect)

    def is_inside_world(self) -> bool:
        return self.actor.sensor_manager.detect_rect(
            self.actor.world.camera.get_world_rect()
        )

    def get_distance_to(
        self,
        obj: Union["actor_mod.Actor", Tuple[float, float]],
    ) -> float:
        return self.actor.sensor_manager.get_distance_to(obj)

    def bounce_from_actor(self, other: "actor_mod.Actor") -> None:
        self.actor.position_manager.bounce_from_actor(other)