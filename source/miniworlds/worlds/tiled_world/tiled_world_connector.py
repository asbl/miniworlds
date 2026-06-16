from typing import TYPE_CHECKING

import miniworlds.worlds.manager.tiled_spatial_index as tiled_spatial_index
import miniworlds.worlds.manager.world_connector as world_connector
import miniworlds.worlds.tiled_world.tiled_world_position_manager as tiledpositionmanager
import miniworlds.worlds.tiled_world.tiled_world_sensor_manager as tiledworldsensor
import miniworlds.worlds.world as world_mod

if TYPE_CHECKING:
    import miniworlds.worlds.actor as actor_mod
    import miniworlds.worlds.tiled_world.tiled_world as world_mod


class TiledWorldConnector(world_connector.WorldConnector):
    """
    WorldConnector implementation for TiledWorlds.
    Handles actor integration into static actor structures and provides
    the appropriate sensor and position manager classes.
    """

    ACTORS_HAVE_FIXED_SIZE = True

    def __init__(self, world: "world_mod.TiledWorld", actor: "actor_mod.Actor"):
        super().__init__(world, actor)
        # Initialize tiled spatial index if not exists
        if getattr(world, "_tiled_spatial_index", None) is None:
            world._tiled_spatial_index = tiled_spatial_index.TiledSpatialIndex(
                chunk_size=8
            )

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
        # Remove actor from tiled spatial index
        tiled_spatial_index = getattr(self.world, "_tiled_spatial_index", None)
        if tiled_spatial_index is not None:
            tiled_spatial_index.remove(self.actor)
        return super().remove_actor_from_world(kill=kill)

    def add_to_world(self, position=(0, 0)):
        actor = super().add_to_world(position)
        self._auto_static_if_passive_tile_actor()
        # Add actor to tiled spatial index
        tiled_spatial_index = getattr(self.world, "_tiled_spatial_index", None)
        if tiled_spatial_index is not None:
            tiled_spatial_index.update(actor)
        return actor

    def _auto_static_if_passive_tile_actor(self):
        if self.actor.static:
            return
        if self.world.event_manager.registry.has_instance_handlers(self.actor):
            return
        costume = getattr(self.actor, "costume", None)
        if costume is not None and getattr(costume, "is_animated", False):
            return
        self.actor._mw_auto_static = True
        self.set_static(True)

    def _mark_static_tile_layer_dirty(self):
        if hasattr(self.world, "_static_tile_layer_dirty"):
            self.world._static_tile_layer_dirty = True

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
            self._mark_static_tile_layer_dirty()
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
                self._mark_static_tile_layer_dirty()

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
            self._mark_static_tile_layer_dirty()
