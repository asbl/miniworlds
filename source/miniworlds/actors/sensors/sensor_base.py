from typing import Union

import miniworlds.positions.vector as vector
import miniworlds.actors.actor as actor_mod


class SensorBase(actor_mod.Actor):
    def __init__(self, *args, **kwargs):
        """_summary_

        Args:
            actor (actor_mod.Actor): _description_
        """
        actor, distance, positioning, direction = self._get_from_args(args, kwargs)
        super().__init__(actor.position, *args, **kwargs)
        self.watch_actor = actor
        self.sensor_distance = distance
        self.sensor_direction = 0
        self.color = (255,255,255,150)
        self.positioning  = positioning
        self.direction = direction

    def _set_physics(self):
        self.physics.simulation = None

    def _get_from_args(self, args, kwargs):
        actor = args[0] if len(args) > 0 else None
        distance = args[1] if len(args) > 1 else 0
        positioning  = args[2] if len(args) > 2 else "relative"
        direction = args[3] if len(args) > 3 else 0

        actor = kwargs.pop("actor") if "actor" in kwargs else actor
        distance = kwargs.pop("distance") if "distance" in kwargs else distance
        direction = kwargs.pop("direction") if "direction" in kwargs else direction
        positioning  = kwargs.pop("positioning") if "positioning" in kwargs else positioning 
        if not (isinstance(actor, actor_mod.Actor)):
            raise TypeError(
                f"Error on creating Sensor: param actor must be instance of Actor, but is {type(actor)}"
            )
        if not (isinstance(distance, Union[float, int])):
            raise TypeError(
                f"Error on creating Sensor: param distance must be int or float but is {type(distance)} , (value [{distance}])"
            )

        return actor, distance, positioning , direction

    def act(self):
        
        if not self.watch_actor:
            self.remove()
        if self.positioning  == "relative":
            dir_vector = (
                vector.Vector.from_direction(self.watch_actor.direction).normalize()
                * self.sensor_distance
            )
            pos_vector = vector.Vector.from_position(self.watch_actor.center)
            self.position = (pos_vector + dir_vector).to_position()
        elif self.positioning == "absolute":
            dir_vector = (
                vector.Vector.from_direction(self.direction).normalize()
                * self.sensor_distance
            )
            pos_vector = vector.Vector.from_position(self.watch_actor.center)
            self.position = (pos_vector + dir_vector).to_position()
