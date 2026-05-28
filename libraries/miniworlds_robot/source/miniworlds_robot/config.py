from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Tuple


Color = Tuple[int, int, int] | Tuple[int, int, int, int]


@dataclass(frozen=True)
class RobotConfig:
    name: str
    costume: Color = (214, 37, 37, 255)
    direction: int = 90


@dataclass(frozen=True)
class ObjectConfig:
    kind: str
    position: Tuple[int, int]


@dataclass(frozen=True)
class TargetConfig:
    robot_position: Tuple[int, int] | None = None
    robot_direction: int | None = None
    robot_steps: int | None = None
    objects: tuple[ObjectConfig, ...] | None = None


@dataclass(frozen=True)
class WorldConfig:
    name: str
    columns: int = 10
    rows: int = 10
    tile_size: int = 40
    background: Color = (221, 236, 203, 255)
    objects: tuple[ObjectConfig, ...] = ()
    target: TargetConfig = field(default_factory=TargetConfig)
    robot_abilities: frozenset[str] = field(
        default_factory=lambda: frozenset({"step", "turn_left", "turn_right"})
    )


WORLD_CONFIGS: Mapping[str, WorldConfig] = {
    "basic": WorldConfig(name="basic"),
    "sequence_path": WorldConfig(
        name="sequence_path",
        columns=6,
        rows=4,
        target=TargetConfig(robot_position=(4, 2), robot_direction=90, robot_steps=4),
    ),
    "variables_path": WorldConfig(
        name="variables_path",
        columns=6,
        rows=4,
        target=TargetConfig(robot_position=(3, 1), robot_direction=-90, robot_steps=5),
    ),
    "function_path": WorldConfig(
        name="function_path",
        columns=6,
        rows=4,
        target=TargetConfig(robot_position=(1, 2), robot_direction=-90, robot_steps=4),
    ),
    "loop_square": WorldConfig(
        name="loop_square",
        columns=6,
        rows=6,
        target=TargetConfig(robot_position=(1, 1), robot_direction=90, robot_steps=8),
    ),
    "leaf_line": WorldConfig(
        name="leaf_line",
        columns=7,
        rows=3,
        objects=(
            ObjectConfig("leaf", (1, 1)),
            ObjectConfig("leaf", (3, 1)),
            ObjectConfig("leaf", (5, 1)),
        ),
        target=TargetConfig(robot_position=(6, 1), robot_direction=90, robot_steps=6, objects=()),
        robot_abilities=frozenset(
            {"step", "turn_left", "turn_right", "on_leaf", "remove_leaf"}
        ),
    ),
    "obstacle_garden": WorldConfig(
        name="obstacle_garden",
        columns=7,
        rows=5,
        objects=(
            ObjectConfig("tree", (3, 1)),
            ObjectConfig("mushroom", (3, 2)),
            ObjectConfig("tree", (3, 3)),
        ),
        target=TargetConfig(
            objects=(
                ObjectConfig("tree", (3, 1)),
                ObjectConfig("mushroom", (3, 2)),
                ObjectConfig("tree", (3, 3)),
            )
        ),
    ),
    "with_position": WorldConfig(
        name="with_position",
        robot_abilities=frozenset({"step", "turn_left", "turn_right", "position"}),
    ),
}


ROBOT_CONFIGS: Mapping[str, RobotConfig] = {
    "standard": RobotConfig(name="standard"),
    "blue": RobotConfig(name="blue", costume=(38, 112, 201, 255)),
}
