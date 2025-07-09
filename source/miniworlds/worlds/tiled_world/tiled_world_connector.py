import miniworlds.worlds.tiled_world.tiled_world_position_manager as tiledpositionmanager
import miniworlds.worlds.tiled_world.tiled_world_sensor_manager as tiledworldsensor
import miniworlds.worlds.manager.world_connector as world_connector


class TiledWorldConnector(world_connector.WorldConnector):
    """
    WorldConnector implementation for TiledWorlds.
    Handles actor integration into static actor structures and provides
    the appropriate sensor and position manager classes.
    """

    @staticmethod
    def get_sensor_manager_class():
        """
        Returns:
            The class used for sensor management in tiled worlds.
        """
        return tiledworldsensor.TiledWorldSensorManager

    @staticmethod
    def get_position_manager_class():
        """
        Returns:
            The class used for position management in tiled worlds.
        """
        return tiledpositionmanager.TiledWorldPositionManager

    def remove_actor_from_world(self, kill=False):
        """
        Removes the actor from both static and dynamic world representations.

        Args:
            kill (bool): Whether the actor should be permanently removed.
        """
        self.remove_static_actor()
        self.remove_dynamic_actor()
        super().remove_actor_from_world()

    def add_static_actor(self):
        """
        Adds the actor to the static actor list at its current position,
        and queues it for costume reload if necessary.
        """
        pos = self.actor.position
        # Ensure the position key exists
        if pos not in self.world.static_actors_dict:
            self.world.static_actors_dict[pos] = []

        if self.actor not in self.world.static_actors_dict[pos]:
            self.world.static_actors_dict[pos].append(self.actor)
            if hasattr(self.world, "mainloop"):
                self.world.mainloop.reload_costumes_queue.append(self.actor)

    def remove_static_actor(self):
        """
        Removes the actor from the static actor list at its current position,
        if present.
        """
        pos = self.actor.position
        if pos in self.world.static_actors_dict:
            if self.actor in self.world.static_actors_dict[pos]:
                self.world.static_actors_dict[pos].remove(self.actor)

    def set_static(self, value: bool):
        """
        Sets whether the actor is considered static in the world.

        Args:
            value (bool): Whether the actor is static.
        """
        super().set_static(value)
        if getattr(self.actor, "_static", False):
            self.add_static_actor()
        else:
            self.remove_static_actor()
