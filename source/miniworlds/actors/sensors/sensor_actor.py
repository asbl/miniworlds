from typing import Union, Tuple, List, Optional, Type

import miniworlds.actors.sensors.sensor_base as sensor_base
import miniworlds.actors.actor as actor_mod



class Sensor(sensor_base.SensorBase):
    """An invisible sensor attached to another actor.

    A ``Sensor`` follows the actor it is attached to and detects nearby
    objects. The sensor itself is not visible and will never detect the actor
    it belongs to.

    Use ``actor.register_sensor(Sensor)`` to attach a sensor to an actor.

    Args:
        actor: The parent actor this sensor is attached to.

    Examples:

        .. code-block:: python

            from miniworlds import *
            world = World()
            player = Actor((100, 100))

            # Attach a sensor that detects enemies 30 pixels ahead
            player.register_sensor(Sensor)

            world.run()
    """

    def __init__(self, actor: "actor_mod.Actor", *args, **kwargs):
        super().__init__(actor, *args, **kwargs)


