import miniworlds.actors.sensors.sensor_base as sensor_base
import miniworlds.actors.shapes.shapes as shapes
import miniworlds.actors.actor as actor_mod

class CircleSensor(shapes.Circle, sensor_base.SensorBase):
    """A circular invisible sensor attached to another actor.

    ``CircleSensor`` creates a circle of a given *distance* (radius) around
    the parent actor. Any actor that overlaps with this circle will be
    detected. The sensor itself is invisible and never detects the parent
    actor.

    Use ``actor.register_sensor(CircleSensor, distance=<pixels>)`` to attach.

    Args:
        actor: The parent actor this sensor belongs to.
        distance: Radius of the circular detection area in pixels.

    Examples:

        .. code-block:: python

            from miniworlds import *
            world = World()
            player = Actor((100, 100))
            player.add_costume("images/player.png")

            # Detect enemies within 50 pixels
            player.register_sensor(CircleSensor, distance=50)

            world.run()
    """

    def __init__(self, actor: "actor_mod.Actor", distance, **kwargs):
        super().__init__(actor=actor, distance=distance, **kwargs)

