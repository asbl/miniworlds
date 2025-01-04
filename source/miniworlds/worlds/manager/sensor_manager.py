import math
from typing import List, Union, Type, Optional, Tuple
import pygame
import inspect

import miniworlds.positions.rect as world_rect
import miniworlds.positions.vector as world_vector
import miniworlds.tools.actor_class_inspection as actor_class_inspection
import miniworlds.worlds.world as world_mod
import miniworlds.actors.actor as actor_mod

import miniworlds.base.exceptions as exceptions


class SensorManager:
    """A Sensor manager connects an actor to a world.

    The sensor manager behaves differently depending on the world it is connected to.
    It is overwritten in World subclasses
    """

    def __init__(self, actor: "actor_mod.Actor", world: "world_mod.World"):
        super().__init__()
        self.actor: "actor_mod.Actor" = actor

    @property
    def world(self):
        return self.actor.world


    def self_remove(self):
        """
        Method is overwritten in subclasses
        """
        pass

    def filter_actors(
        self,
        detected_actors: List["actor_mod.Actor"],
        actors: Union[
            str, "actor_mod.Actor", Type["actor_mod.Actor"], List["actor_mod.Actor"]
        ],
    ):
        """
        Filters a list of actors
        :param detected_actors: a list of actors
        :param actors: list of actor filters
        :return:
        """
        if detected_actors:
            detected_actors = self._filter_actor_list(detected_actors, actors)
        if detected_actors and len(detected_actors) >= 1:
            return detected_actors
        else:
            return []

    def filter_first_actor(
        self,
        detected_actors: List["actor_mod.Actor"],
        actors: Union[str, "actor_mod.Actor", Type["actor_mod.Actor"]],
    ):
        if detected_actors:
            detected_actors = self._filter_actor_list(detected_actors, actors)
        if detected_actors and len(detected_actors) >= 1:
            return_value = detected_actors[0]
            del detected_actors
            return return_value
        else:
            return []

    def _filter_actor_list(
        self,
        actor_list: Optional[List["actor_mod.Actor"]],
        filter: Union[
            str, "actor_mod.Actor", Type["actor_mod.Actor"], List["actor_mod.Actor"]
        ],
    ) -> List["actor_mod.Actor"]:
        # if actor_list is None, return empty list
        if actor_list is None:
            return []
        # Filter actors by class name or type
        if not filter:
            return actor_list
        if isinstance(filter, str):
            actor_list = self._filter_actors_by_classname(actor_list, filter)
        elif isinstance(filter, actor_mod.Actor):
            actor_list = self._filter_actors_by_instance(actor_list, filter)
        elif isinstance(filter, list):
            actor_list = self._filter_actors_by_list(actor_list, filter)
        elif inspect.isclass(filter) and issubclass(filter, actor_mod.Actor):
            actor_list = self._filter_actors_by_class(actor_list, filter)
        else:
            raise exceptions.WrongFilterType(filter)

        if actor_list is None:
            return []

        return actor_list

    def _filter_actors_by_class(
        self,
        actor_list: List["actor_mod.Actor"],
        actors: Union[Type["actor_mod.Actor"], None],
    ) -> List["actor_mod.Actor"]:
        if actors is None:
            return actor_list
        if actors:
            actor_list = [
                actor
                for actor in actor_list
                if actor.__class__ == actors or issubclass(actor.__class__, actors)
            ]
            return actor_list
        else:
            return actor_list

    def _filter_actors_by_classname(
        self, actor_list: List["actor_mod.Actor"], actors: str
    ) -> List["actor_mod.Actor"]:
        actor_type = actor_class_inspection.ActorClassInspection(
            self.actor
        ).find_actor_class_by_classname(actors)
        return self._filter_actors_by_class(actor_list, actor_type)

    @staticmethod
    def _filter_actors_by_instance(actor_list: List["actor_mod.Actor"], actors):
        for actor in actor_list:
            if actor == actors:
                return [actor]
        return []

    @staticmethod
    def _filter_actors_by_list(actor_list: List["actor_mod.Actor"], actors):
        result = []
        for actor in actor_list:
            if actor in actors:
                return result.append(actor)
        return result

    def _remove_self_from_actor_list(self, actor_list: List["actor_mod.Actor"]):
        if actor_list and self.actor in actor_list:
            actor_list.remove(self.actor)
        return actor_list

    def detect_point(self, point) -> bool:
        return self.actor.position_manager.get_global_rect().collidepoint(point)

    def detect_pixel(self, pixel_position) -> bool:
        return self.actor.position_manager.get_screen_rect().collidepoint(
            pixel_position
        )

    def detect_rect(self, rect):
        return self.actor.position_manager.get_global_rect().colliderect(rect)

    def detect_color(self, source: Union[tuple, list]) -> bool:
        return self.detect_color_at(0, 0) == source

    def detect_colors(self, source: list) -> bool:
        for color in source:
            if self.detect_color_at(0, 0) == color:
                return True
        return False

    @staticmethod
    def get_destination(
        start, direction: float, distance: float
    ) -> Tuple[float, float]:
        exact_position_x = start[0] + math.sin(math.radians(direction)) * distance
        exact_position_y = start[1] - math.cos(math.radians(direction)) * distance
        return (exact_position_x, exact_position_y)

    def get_borders_from_rect(self, rect):
        """
        Gets all borders the rect ist touching.

        Returns: A list of borders as strings: "left", "bottom", "right", or "top"

        """
        rect = world_rect.Rect.create(rect)
        borders = []
        if rect.topleft[0] <= 0:
            borders.append("left")
        if rect.topleft[1] + rect.height >= self.world.height:
            borders.append("bottom")
        if rect.topleft[0] + rect.width >= self.world.width:
            borders.append("right")
        if rect.topleft[1] <= 0:
            borders.append("top")
        return borders

    def get_color(self, position: Tuple[float, float]):
        """Returns the world-color at the current world-position

        Returns: The world-color at the current world position as tuple
        with r,g,b value and transparency (e.g. (255, 0, 0, 100)
        """
        if self.world.detect_position(position):
            return self.world.background.get_color_from_pixel(position)
        else:
            return ()

    def detect_borders(self, distance: float = 0) -> list:
        """
        The function compares the rectangle (or alternatively the
        path that the rectangle of the object **distance** pixels travels)
        with the edges of the playing field.
        """
        for _ in range(distance + 1):
            target_rect = self.get_destination_rect(distance)
            borders = self.get_borders_from_rect(target_rect)
            if borders:
                return borders
            else:
                return []

    def detect_color_at(self, direction: int = 0, distance: int = 1) -> list:
        if not direction:
            direction = self.actor.direction
        destination = self.get_destination(self.actor.center, direction, distance)
        return self.world.background.get_color(destination)

    def get_destination_rect(self, distance: int) -> "world_rect.Rect":
        destination_pos = self.get_destination(
            self.actor.position, self.actor.direction, distance
        )
        rect = world_rect.Rect.from_position(
            destination_pos, dimensions=self.actor.size, world=self.world
        )
        return rect

    def get_line_in_direction(self, start, direction: Union[int, float], distance: int):
        return [self.get_destination(start, direction, i) for i in range(distance)]

    def get_line_to(
        self, start: Tuple[float, float], target: Tuple[float, float]
    ) -> List[Tuple[float, float]]:
        sampling_rate = int(
            math.sqrt((target[0] - start[0]) ** 2 + target[1] - start[1] ** 2)
        )
        x_spacing = (target[0] - start[0]) / (sampling_rate + 1)
        y_spacing = (target[1] - start[1]) / (sampling_rate + 1)
        return [
            (start[0] + i * x_spacing, start[1] + i * y_spacing)
            for i in range(1, sampling_rate + 1)
        ]

    @staticmethod
    def filter_actor_list(a_list, actor_type):
        return [actor for actor in a_list if type(actor_mod.Actor) == actor_type]

    def detect_actors(
        self,
        filter: Optional[
            Union[
                str, "actor_mod.Actor", Type["actor_mod.Actor"], List["actor_mod.Actor"]
            ]
        ] = None,
    ) -> list:
        self.actor.world.init_display()

        group = pygame.sprite.Group(self.actor.world.camera.get_actors_in_view())
        actors = pygame.sprite.spritecollide(
            self.actor, group, False, pygame.sprite.collide_rect
        )
        group.empty()
        detected_actors = self._remove_self_from_actor_list(actors)
        if detected_actors:
            detected_actors = self._detect_actor_by_collision_type(
                detected_actors, self.actor.collision_type
            )
        if filter:
            return self.filter_actors(detected_actors, filter)
        else:
            return self.filter_actors(detected_actors, filter)

    def detect_actors_at(
        self, filter=None, direction: int = 0, distance: int = 1
    ) -> list:
        if direction is None:
            direction = self.actor.direction
        destination = self.__class__.get_destination(self.actor, direction, distance)
        detected_actors = self.get_actors_at_position(destination)
        return self.filter_actors(detected_actors, filter)

    def detect_actors_at_destination(
        self,
        destination: Tuple[float, float],
        filter=None,
    ) -> list:
        detected_actors = self.get_actors_at_position(destination)
        return self.filter_actors(detected_actors, filter)

    def detect_actor(self, filter) -> Union["actor_mod.Actor", None]:
        self.actor.world.init_display()
        group = pygame.sprite.Group(self.actor.world.camera.get_actors_in_view())
        actors = pygame.sprite.spritecollide(
            self.actor, group, False, pygame.sprite.collide_rect
        )
        group.empty()
        detected_actors = self._remove_self_from_actor_list(actors)
        if detected_actors:
            detected_actors = self._detect_actor_by_collision_type(
                detected_actors, self.actor.collision_type
            )
        del actors
        return self.filter_first_actor(detected_actors, filter)

    def _detect_actor_by_collision_type(self, actors, collision_type) -> List:
        if collision_type == "circle":
            return [
                actor
                for actor in actors
                if pygame.sprite.collide_circle(self.actor, actor)
            ]
        elif collision_type == "rect" or collision_type == "static-rect":
            return [
                actor
                for actor in actors
                if pygame.sprite.collide_rect(self.actor, actor)
            ]
        elif collision_type == "mask":
            return [
                actor
                for actor in actors
                if pygame.sprite.collide_mask(self.actor, actor)
            ]

    def get_actors_at_position(self, position):
        actors = []
        for actor in self.world.actors:
            if actor.position_manager.get_global_rect().collidepoint(
                position[0], position[1]
            ):
                actors.append(actor)
        if self.actor in actors:
            actors.remove(self.actor)
        return actors

    def get_distance_to(
        self, obj: Union["actor_mod.Actor", Tuple[float, float]]
    ) -> float:
        if isinstance(obj, actor_mod.Actor):
            vec = world_vector.Vector.from_actors(self.actor, obj)
        else:
            vec = world_vector.Vector.from_actor_and_position(self.actor, obj)
        return vec.length()
