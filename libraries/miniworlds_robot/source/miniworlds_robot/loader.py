from __future__ import annotations

from miniworlds_robot.config import ROBOT_CONFIGS, WORLD_CONFIGS, RobotConfig, WorldConfig
from miniworlds_robot.robot import Robot, create_robot
from miniworlds_robot.world import Leaf, Mushroom, Position, RobotWorld, Tree


OBJECT_TYPES = {
    "leaf": Leaf,
    "mushroom": Mushroom,
    "tree": Tree,
}


def _resolve_world_config(config: str | WorldConfig) -> WorldConfig:
    if isinstance(config, WorldConfig):
        return config
    try:
        return WORLD_CONFIGS[config]
    except KeyError:
        raise ValueError(f"Unknown RobotWorld config: {config!r}") from None


def _resolve_robot_config(config: str | RobotConfig) -> RobotConfig:
    if isinstance(config, RobotConfig):
        return config
    try:
        return ROBOT_CONFIGS[config]
    except KeyError:
        raise ValueError(f"Unknown Robot config: {config!r}") from None


def load_world(config: str | WorldConfig = "basic", **overrides) -> RobotWorld:
    world_config = _resolve_world_config(config)
    world = RobotWorld(world_config, **overrides)
    for obj in world_config.objects:
        try:
            object_cls = OBJECT_TYPES[obj.kind]
        except KeyError:
            raise ValueError(f"Unknown RobotWorld object kind: {obj.kind!r}") from None
        world.add_object(object_cls, obj.position)
    return world


def load_robot(
    config: str | RobotConfig = "standard",
    world: RobotWorld | None = None,
    *,
    position: Position = (0, 0),
) -> Robot:
    world = world or load_world()
    return create_robot(_resolve_robot_config(config), world, position)


class Loader:
    load_world = staticmethod(load_world)
    load_robot = staticmethod(load_robot)
