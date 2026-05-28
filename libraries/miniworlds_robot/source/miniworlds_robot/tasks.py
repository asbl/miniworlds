from __future__ import annotations

from miniworlds_robot.loader import load_robot, load_world


def task(name: str, robot: str = "standard"):
    world = load_world(name)
    robot_actor = load_robot(robot, world, position=_start_position(name))
    return world, robot_actor


def _start_position(name: str) -> tuple[int, int]:
    starts = {
        "sequence_path": (1, 1),
        "variables_path": (0, 1),
        "function_path": (1, 2),
        "loop_square": (1, 1),
        "leaf_line": (0, 1),
    }
    return starts.get(name, (0, 0))
