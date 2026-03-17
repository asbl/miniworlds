from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Tuple, Union

from miniworlds.base.exceptions import MiniworldsError

if TYPE_CHECKING:
    import miniworlds.actors.actor as actor_mod


logger = logging.getLogger(__name__)


class ActorMovementFacade:
    """Keeps actor movement, direction, and position helpers in one internal unit."""

    def __init__(self, actor: "actor_mod.Actor"):
        self.actor = actor

    def get_direction(self) -> float:
        return self.actor.position_manager.get_direction()

    def set_direction(self, value: int) -> None:
        self.actor.position_manager.set_direction(value)

    def get_direction_at_unit_circle(self) -> int:
        return self.actor.position_manager.dir_to_unit_circle(self.actor.direction)

    def set_direction_at_unit_circle(self, value: int) -> None:
        self.actor.direction = self.actor.position_manager.unit_circle_to_dir(value)

    def turn_left(self, degrees: int = 90) -> int:
        return self.actor.position_manager.turn_left(degrees)

    def turn_right(self, degrees: Union[int, float] = 90):
        return self.actor.position_manager.turn_right(degrees)

    def set_direction_value(self, direction: Union[str, int, float]) -> float:
        return self.actor.position_manager.set_direction(direction)

    def point_towards_position(self, destination: Tuple[float, float]) -> Union[int, float]:
        return self.actor.position_manager.point_towards_position(destination)

    def point_towards_actor(self, other: "actor_mod.Actor") -> int:
        pos = other.position_manager.get_global_rect().center
        return self.point_towards_position(pos)

    def get_x(self) -> float:
        return self.actor.position_manager.position[0]

    def set_x(self, value: float) -> None:
        self.actor.position_manager.set_position((value, self.get_y()))

    def get_y(self) -> float:
        return self.actor.position_manager.position[1]

    def set_y(self, value: float) -> None:
        self.actor.position_manager.set_position((self.get_x(), value))

    def get_topleft_x(self) -> float:
        return self.actor.get_global_rect().get_topleft()[0]

    def set_topleft_x(self, value: float) -> None:
        self.actor.position_manager.set_topleft((value, self.get_topleft_y()))

    def get_topleft_y(self) -> float:
        return self.actor.position_manager.get_topleft()[1]

    def set_topleft_y(self, value: float) -> None:
        self.actor.position_manager.set_topleft((self.get_topleft_x(), value))

    def get_topleft(self) -> Tuple[float, float]:
        return self.actor.position_manager.get_topleft()

    def set_topleft(self, value: Tuple[float, float]) -> None:
        self.actor.position_manager.set_topleft(value)

    def get_local_center(self) -> Tuple[float, float]:
        return self.actor.position_manager.local_center

    def get_center_x(self) -> float:
        return self.actor.position_manager.get_center()[0]

    def set_center_x(self, value: float) -> None:
        self.actor.position_manager.set_center((value, self.get_center_y()))

    def get_center_y(self) -> float:
        return self.actor.position_manager.get_center()[1]

    def set_center_y(self, value: float) -> None:
        self.actor.position_manager.set_center((self.get_center_x(), value))

    def get_center(self) -> Tuple[float, float]:
        return self.actor.position_manager.get_center()

    def set_center(self, value: Tuple[float, float]) -> None:
        self.actor.position_manager.set_center(value)

    def move(self, distance: int = 0, direction: int = 0):
        if direction != 0:
            self.actor.position_manager.set_direction(direction)
        return self.actor.position_manager.move(distance)

    def move_vector(self, vector):
        return self.actor.position_manager.move_vector(vector)

    def move_back(self, distance):
        return self.actor.position_manager.move(-distance)

    def undo_move(self):
        logger.debug("Undoing last move for actor %s", self.actor.actor_id)
        return self.actor.position_manager.undo_move()

    def move_towards(self, target: Union[Tuple[float, float], "actor_mod.Actor"]):
        from miniworlds.actors.actor import Actor

        if isinstance(target, Actor):
            target = target.position
        return self.actor.position_manager.move_towards_position(target)

    def move_in_direction(
        self,
        direction: Union[int, str, Tuple[float, float]],
        distance=1,
    ):
        if type(direction) in [int, str]:
            return self.actor.position_manager.move_in_direction(direction, distance)
        elif type(direction) == tuple:
            return self.actor.position_manager.move_towards_position(direction, distance)
        else:
            raise MiniworldsError(
                f"Expected direction or position, got f{type(direction)}, ({direction})"
            )

    def move_to(self, position: Tuple[float, float]):
        return self.actor.position_manager.move_to(position)

    def get_position(self) -> Tuple[float, float]:
        return self.actor.position_manager.position

    def set_position(self, value: Tuple[float, float]) -> None:
        self.actor.position_manager.set_position(value)
