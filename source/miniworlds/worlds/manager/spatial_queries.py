"""Camera-independent queries for simulation and targeting."""
import math

import pygame


class SpatialQueries:
    def __init__(self, world):
        self.world = world

    @staticmethod
    def _position(position):
        if hasattr(position, "center"):
            position = position.center
        if not isinstance(position, tuple) or len(position) != 2:
            raise TypeError("position must be a pair or an Actor")
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in position):
            raise TypeError("position components must be numbers")
        if not all(math.isfinite(v) for v in position):
            raise ValueError("position must be finite")
        return position

    @staticmethod
    def _radius(radius):
        if isinstance(radius, bool) or not isinstance(radius, (int, float)):
            raise TypeError("radius must be a number")
        if not math.isfinite(radius) or radius < 0:
            raise ValueError("radius must be finite and non-negative")

    def _index(self, actor_type, collision_group):
        if actor_type is not None:
            from miniworlds.actors.actor import Actor
            if not isinstance(actor_type, type) or not issubclass(actor_type, Actor):
                raise TypeError("actor_type must be an Actor class")
        if collision_group is not None and not isinstance(collision_group, str):
            raise TypeError("collision_group must be a string")
        if getattr(self.world, "is_tiled", False):
            raise ValueError("spatial simulation queries currently require a pixel World")
        return self.world._spatial_index.partition(actor_type, collision_group)

    def query_rect(self, rect, actor_type=None, collision_group=None, exclude=None):
        rect = pygame.Rect(rect)
        index = self._index(actor_type, collision_group)
        candidates = index.query_rect(rect) if index is not None else self.world.actors
        return [actor for actor in candidates
                if actor is not exclude and getattr(actor, "active", True)
                and (actor_type is None or isinstance(actor, actor_type))
                and (collision_group is None or actor.collision_group == collision_group)
                and actor.position_manager.get_global_rect().colliderect(rect)]

    def query_radius(self, position, radius, actor_type=None, collision_group=None, exclude=None):
        x, y = self._position(position)
        self._radius(radius)
        left, top = math.floor(x - radius), math.floor(y - radius)
        rect = pygame.Rect(left, top, math.ceil(x + radius) - left + 1,
                           math.ceil(y + radius) - top + 1)
        index = self._index(actor_type, collision_group)
        # Center queries include zero-size hitboxes too; rectangle overlap
        # would exclude them before the distance test.
        return [actor for actor in index.query_rect(rect)
                if actor is not exclude and getattr(actor, "active", True)
                and (actor.center[0] - x) ** 2 + (actor.center[1] - y) ** 2 <= radius ** 2]

    def find_nearest(self, position, actor_type=None, radius=None, collision_group=None, exclude=None):
        position = self._position(position)
        index = self._index(actor_type, collision_group)
        if radius is not None:
            self._radius(radius)
            candidates = self.query_radius(position, radius, actor_type, collision_group, exclude)
        elif index is None:
            candidates = [actor for actor in self.world.actors if actor is not exclude
                          and (actor_type is None or isinstance(actor, actor_type))
                          and (collision_group is None or actor.collision_group == collision_group)]
        else:
            if not len(index) or (len(index) == 1 and exclude in index):
                return None
            x, y = position
            left, top, right, bottom = index.extent
            size = index.cell_size
            limit = math.hypot(max(abs(x-left*size), abs(x-(right+1)*size)),
                               max(abs(y-top*size), abs(y-(bottom+1)*size))) + 1
            search_radius = size
            candidates = []
            while not candidates:
                candidates = self.query_radius(position, min(search_radius, limit),
                                               actor_type, collision_group, exclude)
                if search_radius >= limit:
                    break
                search_radius *= 2
        x, y = position
        return min(candidates, key=lambda actor: (
            (actor.center[0]-x)**2 + (actor.center[1]-y)**2, actor.actor_id
        ), default=None)
