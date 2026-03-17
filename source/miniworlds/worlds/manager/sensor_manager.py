import math
from typing import List, Union, Type, Optional, Tuple, TYPE_CHECKING
import pygame
import inspect

import miniworlds.positions.rect as world_rect
import miniworlds.positions.vector as world_vector
import miniworlds.tools.actor_class_inspection as actor_class_inspection


import miniworlds.base.exceptions as exceptions
import miniworlds.actors.actor as actor_mod

if TYPE_CHECKING:
    import miniworlds.worlds.world as world_mod
    

ActorFilterType = Union[str, "actor_mod.Actor", Type["actor_mod.Actor"], List["actor_mod.Actor"]]


class SensorManager:
    """A Sensor manager connects an actor to a world.

    The sensor manager behaves differently depending on the world it is connected to.
    It is overwritten in World subclasses
    """

    def __init__(self, actor: "actor_mod.Actor", world: "world_mod.World"):
        self.actor: "actor_mod.Actor" = actor
        self.world:  "world_mod.World" = world

    def self_remove(self):
        """
        Method is overwritten in subclasses
        """
        pass

    @staticmethod
    def _is_valid_point(point: Tuple[float, float]) -> bool:
        return (
            isinstance(point, tuple)
            and len(point) == 2
            and all(isinstance(value, (int, float)) for value in point)
        )

    def filter_actors(
        self,
        detected_actors: List["actor_mod.Actor"],
        actors: Optional[ActorFilterType]
    ) -> List["actor_mod.Actor"]:
        """
        Filters a list of detected actors based on a given filter.

        Args:
            detected_actors (List[Actor]): The list of actors to be filtered.
            actors (Optional[FilterType]): The filter criteria, which can be:
                - a string (e.g. actor tag or name),
                - a single Actor instance,
                - an Actor class,
                - a list of Actor instances.

        Returns:
            List[Actor]: A filtered list of actors matching the criteria.
        """
        filtered = self._filter_actor_list(detected_actors, actors)
        return filtered if filtered else []


    def filter_first_actor(
        self,
        detected_actors: List["actor_mod.Actor"],
        actors: Union[str, "actor_mod.Actor", Type["actor_mod.Actor"]],
    ):
        detected_actors = self._filter_actor_list(detected_actors, actors)
        if detected_actors and len(detected_actors) >= 1:
            return_value = detected_actors[0]
            del detected_actors
            return return_value
        else:
            return []

    def _resolve_detectable_actor_filter(
        self,
        actor_filter: Optional[ActorFilterType],
    ) -> Tuple[Optional[ActorFilterType], bool]:
        if actor_filter is None:
            return None, False

        if isinstance(actor_filter, str):
            actor_type = self._resolve_actor_type_by_name(actor_filter)
            if actor_type is None:
                return None, False
            return actor_type, True

        if isinstance(actor_filter, actor_mod.Actor):
            return actor_filter, True

        if isinstance(actor_filter, list) and all(
            isinstance(actor, actor_mod.Actor) for actor in actor_filter
        ):
            return actor_filter, True

        if inspect.isclass(actor_filter) and issubclass(actor_filter, actor_mod.Actor):
            return actor_filter, True

        raise exceptions.WrongFilterType(actor_filter)

    def _filter_actor_list(
        self,
        actor_list: Optional[List["actor_mod.Actor"]],
        actor_filter: Optional[ActorFilterType]
    ) -> List["actor_mod.Actor"]:
        """
        Applies a filter to a list of actors. Supports filtering by:
        - class name (str),
        - actor instance,
        - actor class (type),
        - list of actor instances.

        Args:
            actor_list (Optional[List[Actor]]): The list of actors to filter.
            filter (FilterType): The filter condition.

        Returns:
            List[Actor]: The filtered list of actors.
        """
        resolved_filter, filter_applied = self._resolve_detectable_actor_filter(actor_filter)

        return self._filter_actor_list_by_resolved_filter(
            actor_list,
            resolved_filter,
            filter_applied,
        )

    def _filter_actor_list_by_resolved_filter(
        self,
        actor_list: Optional[List["actor_mod.Actor"]],
        resolved_filter: Optional[ActorFilterType],
        filter_applied: bool,
    ) -> List["actor_mod.Actor"]:
        actor_list = actor_list or []

        if not filter_applied:
            return actor_list

        if isinstance(resolved_filter, actor_mod.Actor):
            return self._filter_actors_by_instance(actor_list, resolved_filter)

        if isinstance(resolved_filter, list):
            return self._filter_actors_by_list(actor_list, resolved_filter)

        return self._filter_actors_by_class(actor_list, resolved_filter)

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
        actor_type = self._resolve_actor_type_by_name(actors)
        return self._filter_actors_by_class(actor_list, actor_type)

    def _resolve_actor_type_by_name(
        self, actor_name: str
    ) -> Optional[Type["actor_mod.Actor"]]:
        normalized_name = actor_name.lower()
        event_manager = getattr(self.world, "event_manager", None)
        definition = getattr(event_manager, "definition", None)
        actor_classes_by_name = getattr(definition, "actor_classes_by_name", None)

        if actor_classes_by_name is not None:
            actor_type = actor_classes_by_name.get(normalized_name)
            if actor_type is not None:
                return actor_type

        actor_type = actor_class_inspection.ActorClassInspection(
            self.actor
        ).find_actor_class_by_classname(actor_name)

        if actor_type is not None and actor_classes_by_name is not None:
            actor_classes_by_name[normalized_name] = actor_type

        return actor_type

    def _prefilter_detectable_actors(self, visible_actors, actor_filter):
        resolved_filter, filter_applied = self._resolve_detectable_actor_filter(actor_filter)
        if not filter_applied:
            return visible_actors, False

        return (
            self._filter_actor_list_by_resolved_filter(
                visible_actors,
                resolved_filter,
                filter_applied,
            ),
            True,
        )

    @staticmethod
    def _filter_actors_by_instance(actor_list: List["actor_mod.Actor"], actors):
        for actor in actor_list:
            if actor == actors:
                return [actor]
        return []

    @staticmethod
    def _filter_actors_by_list(actor_list: List["actor_mod.Actor"], actors: List["actor_mod.Actor"]) -> List[
        "actor_mod.Actor"]:
        """
        Filters the actor_list to include only those actors that are present in the 'actors' list.

        Args:
            actor_list: The list of detected actors.
            actors: The list of actors to match against.

        Returns:
            A list of actors that are present in both lists.
        """
        return [actor for actor in actor_list if actor in actors]

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

    def detect_color(
            self,
            source: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
            direction: Optional[int] = None,
            distance: int = 0,
    ) -> bool:
        """
        Checks if the color at a given direction and distance matches the target color.

        Args:
            source: The color to match, e.g. (255, 0, 0) or (255, 0, 0, 255)
            direction: The direction in which to check (in degrees)
            distance: How far ahead to check (default is 1 pixel)

        Returns:
            True if the color at the given location matches the source color, else False.
        """
        sampled_color = self.detect_color_at(direction, distance)
        return sampled_color == source

    def detect_colors(self, source: list) -> bool:
        for color in source:
            if self.detect_color_at(0, 0) == color:
                return True
        return False

    def detect_color_at(self, direction: Optional[int] = 0, distance: int = 0) -> list:
        # Overwritten in tiled_sensor_manager
        if not direction:
            direction = self.actor.direction
        destination = self.get_destination(self.actor.center, direction, distance)
        return self.world.background.get_color(destination)

    @staticmethod
    def get_destination(
        start: Tuple[float, float], direction: float, distance: float
    ) -> Tuple[float, float]:
        """
        Computes a new (x, y) position starting from `start`, moving `distance` units in the `direction` (degrees).

        Args:
            start (Tuple[float, float]): Starting position (x, y).
            direction (float): Direction in degrees (0° = north/up, 90° = east/right).
            distance (float): Distance to move.

        Returns:
            Tuple[float, float]: New position (x, y).
        """
        radians = math.radians(direction)
        x = start[0] + math.sin(radians) * distance
        y = start[1] - math.cos(radians) * distance
        return (x, y)


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

    def get_destination_rect(self, distance: Union[int, float]) -> world_rect.Rect:
        """
        Returns the rectangular area (Rect) at a position `distance` units away from the actor,
        in the direction the actor is currently facing.

        Args:
            distance (int | float): Distance to move from the actor's current position.

        Returns:
            world_rect.Rect: A rectangle at the destination position with the actor's size.
        """
        destination = self.get_destination(
            self.actor.position, self.actor.direction, distance
        )
        return world_rect.Rect.from_position(
            destination,
            dimensions=self.actor.size,
            world=self.world
        )

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
    def filter_actor_list(a_list: List["actor_mod.Actor"], actor_type: Type["actor_mod.Actor"]) -> List[
        "actor_mod.Actor"]:
        """
        Filters the actor list by class type, including subclasses.

        Args:
            a_list: List of Actor instances.
            actor_type: The class or superclass to match against.

        Returns:
            A list of actors that are instances of the given type or its subclasses.
        """
        return [actor for actor in a_list if isinstance(actor, actor_type)]

    def detect_actors(self, filter: Optional[ActorFilterType] = None) -> List["actor_mod.Actor"]:
        """
        Detects all actors in the current view that collide with this actor, optionally filtered by a given criterion.

        The method checks for sprite collisions between the current actor and all actors in the camera view,
        removes the actor itself from the result, optionally filters by collision type, and then applies
        a user-defined filter.

        Args:
            filter (Optional[FilterType]): A filter to narrow down detected actors. This can be:
                - a string tag
                - an actor instance
                - an actor class
                - a list of specific actors

        Returns:
            List[Actor]: A list of actors that collide with the current actor and match the filter.
        """
        if not self.world.backgrounds._is_display_initialized:
            self.world.backgrounds._init_display()

        visible_actors = self.world.camera.get_actors_in_view()
        collision_candidates, filter_applied = self._prefilter_detectable_actors(
            visible_actors, filter
        )
        if not collision_candidates:
            return []

        actor_rect = self.actor.position_manager.get_global_rect()
        detected_actors = [
            actor
            for actor in collision_candidates
            if actor is not self.actor
            and actor.position_manager.get_global_rect().colliderect(actor_rect)
        ]

        collision_type = self.actor.collision_type
        if detected_actors and collision_type not in ("rect", "static-rect"):
            detected_actors = self._detect_actor_by_collision_type(
                detected_actors,
                collision_type,
            )

        if filter_applied:
            return detected_actors

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

    def detect_blocking_actor_at_destination(
        self, destination: Tuple[float, float]
    ) -> Union["actor_mod.Actor", None]:
        return self.get_blocking_actor_at_position(destination)

    def detect_actor(self, filter) -> Union["actor_mod.Actor", None]:
        """
        Detects the first actor in view that collides with the current actor and matches the given filter.

        This method  collects all actors currently visible to the camera,
        checks for collisions with the current actor, and applies an optional filter to identify a relevant actor.

        Args:
            filter (Optional[Callable[[Actor], bool]]): A filter function that returns True for actors
                that should be considered. If no filter is provided, all colliding actors are considered.

        Returns:
            Optional[Actor]: The first detected actor that matches the filter, or None if no match is found.
        """
        if not self.world.backgrounds._is_display_initialized:
            return
        
        visible_actors = self.world.camera.get_actors_in_view()
        collision_candidates, filter_applied = self._prefilter_detectable_actors(
            visible_actors, filter
        )
        if not collision_candidates:
            return []

        actor_rect = self.actor.position_manager.get_global_rect()

        detected_actors = [
            actor for actor in collision_candidates
            if actor is not self.actor
            and actor.position_manager.get_global_rect().colliderect(actor_rect)
        ]

        collision_type = self.actor.collision_type
        if detected_actors and collision_type not in ("rect", "static-rect"):
            detected_actors = self._detect_actor_by_collision_type(
                detected_actors, collision_type
            )

        if filter_applied:
            return detected_actors[0] if detected_actors else []

        return self.filter_first_actor(detected_actors, filter)


    def _detect_actor_by_collision_type(self, actors, collision_type) -> List:
        if collision_type == "circle":
            return [
                actor
                for actor in actors
                if pygame.sprite.collide_circle(self.actor, actor)
            ]
        elif collision_type == "rect" or collision_type == "static-rect":
            return actors
        elif collision_type == "mask":
            return [
                actor
                for actor in actors
                if pygame.sprite.collide_mask(self.actor, actor)
            ]

    @staticmethod
    def _try_get_actor_global_rect(actor: "actor_mod.Actor") -> Optional[pygame.Rect]:
        position_manager = getattr(actor, "_position_manager", None)
        if position_manager is None:
            try:
                position_manager = actor.position_manager
            except (AttributeError, exceptions.MissingActorPartsError):
                return None
        try:
            return position_manager.get_global_rect()
        except (AttributeError, exceptions.MissingActorPartsError):
            return None

    def _get_cached_static_blocking_rects(
        self,
    ) -> List[Tuple["actor_mod.Actor", pygame.Rect]]:
        frame = getattr(self.world, "frame", -1)
        version = getattr(self.world, "_blocking_registry_version", 0)
        cache = getattr(self.world, "_blocking_static_rect_cache", None)
        if (
            isinstance(cache, tuple)
            and len(cache) == 3
            and cache[0] == frame
            and cache[1] == version
        ):
            return cache[2]

        static_rects: List[Tuple["actor_mod.Actor", pygame.Rect]] = []
        for actor in getattr(self.world, "_blocking_actors", ()):
            if not getattr(actor, "_static", False):
                continue
            actor_rect = self._try_get_actor_global_rect(actor)
            if actor_rect is None:
                continue
            static_rects.append((actor, actor_rect))

        self.world._blocking_static_rect_cache = (frame, version, static_rects)
        return static_rects

    def get_blocking_actor_at_position(
        self, position: Tuple[float, float]
    ) -> Union["actor_mod.Actor", None]:
        if not self._is_valid_point(position):
            return None
        x, y = position

        for actor, actor_rect in self._get_cached_static_blocking_rects():
            if actor is self.actor:
                continue
            if actor_rect.collidepoint(x, y):
                return actor

        for actor in getattr(self.world, "_blocking_actors", ()):
            if actor is self.actor or getattr(actor, "_static", False):
                continue
            actor_rect = self._try_get_actor_global_rect(actor)
            if actor_rect is None:
                continue
            if actor_rect.collidepoint(x, y):
                return actor
        return None

    def get_actors_at_position(self, position):
        if not self._is_valid_point(position):
            return []
        x, y = position
        actors = []
        camera = getattr(self.world, "camera", None)
        if camera is not None and camera.rect.collidepoint((x, y)):
            candidates = camera.get_actors_in_view()
        else:
            candidates = self.world.actors
        for actor in candidates:
            if actor is self.actor:
                continue
            actor_rect = self._try_get_actor_global_rect(actor)
            if actor_rect is None:
                continue
            if actor_rect.collidepoint(x, y):
                actors.append(actor)
        return actors

    def get_distance_to(
        self, obj: Union["actor_mod.Actor", Tuple[float, float]]
    ) -> float:
        if isinstance(obj, actor_mod.Actor):
            vec = world_vector.Vector.from_actors(self.actor, obj)
        else:
            vec = world_vector.Vector.from_actor_and_position(self.actor, obj)
        return vec.length()

    def contains_rect_any(self, rect: Union[Tuple[int, int, int, int], pygame.Rect]) -> bool:
        """
        Returns True if any part of the rectangle is inside the world.

        Useful for detecting partial overlaps or visibility at the edges.
        """
        rectangle = world_rect.Rect.create(rect)
        return self.detect_position(rectangle.topleft) or self.detect_position(rectangle.bottomright)


    def contains_rect_all(self, rect: Union[Tuple[int, int, int, int], pygame.Rect]) -> bool:
        """
        Returns True if the entire rectangle is fully inside the world.

        Useful when ensuring that an object is completely within bounds.
        """
        rectangle = world_rect.Rect.create(rect)
        return self.detect_position(rectangle.topleft) and self.detect_position(rectangle.bottomright)

    
    def contains_position(self, pos):
        """Checks if position is in the world.

        Returns:
            True, if Position is in the world.
        """
        if 0 <= pos[0] < self.world.world_size_x and 0 <= pos[1] < self.world.world_size_y:
            return True
        else:
            return False