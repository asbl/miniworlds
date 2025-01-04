from typing import Union, Tuple, List, Optional, Type

import miniworlds.actors.sensors.sensor_base as sensor_base
import miniworlds.actors.actor as actor_mod



class Sensor(sensor_base.SensorBase):
    """A sensors attached to a actor.

    The sensors is not visible and will not detect the actor itself.
    """

    def __init__(self, actor: "actor_mod.Actor", *args, **kwargs):
        super().__init__(actor, *args, **kwargs)


