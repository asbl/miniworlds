from __future__ import annotations

from typing import Tuple, Type

from miniworlds import Actor, TiledWorld

from miniworlds_robot.config import WorldConfig


Position = Tuple[float, float]


class RobotWorld(TiledWorld):
    """A miniworlds tiled world with a configuration-driven Robot API."""

    def __init__(self, config: WorldConfig | None = None, **overrides):
        config = config or WorldConfig(name="custom")
        self.robot_config = config
        columns = overrides.pop("columns", config.columns)
        rows = overrides.pop("rows", config.rows)
        tile_size = overrides.pop("tile_size", config.tile_size)
        super().__init__(columns, rows, tile_size=tile_size, **overrides)
        self.tile_size = tile_size
        self.grid = True
        self.background.fill_color = config.background

    @property
    def robot_abilities(self) -> frozenset[str]:
        return self.robot_config.robot_abilities

    def is_blocked(self, position: Position) -> bool:
        if not self.is_tile(position):
            return True
        return any(getattr(actor, "blocks_robot", False) for actor in self.detect_actors(position))

    def add_object(self, actor_cls: Type[Actor], position: Position) -> Actor:
        return actor_cls(position, world=self)

    def run(self, *args, **kwargs) -> bool:
        """Return whether the current world state matches the task target."""
        return self.is_solved()

    def is_solved(self) -> bool:
        target = self.robot_config.target
        if target.robot_position is not None and self._robot_positions() != (target.robot_position,):
            return False
        if target.robot_direction is not None and self._robot_directions() != (target.robot_direction,):
            return False
        if target.robot_steps is not None and self._robot_steps() != (target.robot_steps,):
            return False
        if target.objects is not None and self._object_state() != self._object_target_state(target.objects):
            return False
        return True

    def _robot_positions(self) -> tuple[tuple[int, int], ...]:
        return tuple(
            sorted(
                actor.position
                for actor in self.actors
                if getattr(actor, "is_robot_body", False)
            )
        )

    def _robot_directions(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                actor.direction
                for actor in self.actors
                if getattr(actor, "is_robot_body", False)
            )
        )

    def _robot_steps(self) -> tuple[int, ...]:
        return tuple(
            sorted(
                actor.robot_steps
                for actor in self.actors
                if getattr(actor, "is_robot_body", False)
            )
        )

    def _object_state(self) -> tuple[tuple[str, tuple[int, int]], ...]:
        return tuple(
            sorted(
                (actor.robot_object_kind, actor.position)
                for actor in self.actors
                if hasattr(actor, "robot_object_kind")
            )
        )

    @staticmethod
    def _object_target_state(objects) -> tuple[tuple[str, tuple[int, int]], ...]:
        return tuple(sorted((obj.kind, obj.position) for obj in objects))


class RobotObject(Actor):
    blocks_robot = False
    collectable = False
    costume_color = (255, 255, 255, 255)
    robot_object_kind = "object"

    def __init__(self, position: Position = (0, 0), *, world=None):
        super().__init__(position, world=world)
        self.size = (1, 1)
        self.add_costume(self.costume_color)


class Tree(RobotObject):
    blocks_robot = True
    costume_color = (33, 120, 58, 255)
    robot_object_kind = "tree"


class Mushroom(RobotObject):
    blocks_robot = True
    costume_color = (192, 43, 48, 255)
    robot_object_kind = "mushroom"


class Leaf(RobotObject):
    collectable = True
    costume_color = (74, 159, 65, 255)
    robot_object_kind = "leaf"
