import miniworlds.actors.sensors.sensor_base as sensor_base
import miniworlds.actors.shapes.shapes as shapes
import miniworlds.actors.actor as actor_mod

class CircleSensor(shapes.Circle, sensor_base.SensorBase):
    """A sensors attached to a actor.

    The sensors is not visible and will not detect the actor itself.
    """

    def __init__(self, actor: "actor_mod.Actor", distance, **kwargs):
        super().__init__(actor=actor, distance=distance, **kwargs)

