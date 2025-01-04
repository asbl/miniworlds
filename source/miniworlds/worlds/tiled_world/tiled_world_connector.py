import miniworlds.worlds.tiled_world.tiled_world_position_manager as tiledpositionmanager
import miniworlds.worlds.tiled_world.tiled_world_sensor_manager as tiledworldsensor
import miniworlds.worlds.manager.world_connector as world_connector


class TiledWorldConnector(world_connector.WorldConnector):
    def __init__(self, world, actor):
        super().__init__(world, actor)

    @staticmethod
    def get_sensor_manager_class():
        return tiledworldsensor.TiledWorldSensorManager

    @staticmethod
    def get_position_manager_class():
        return tiledpositionmanager.TiledWorldPositionManager

    def remove_actor_from_world(self, kill = False):
        self.remove_static_actor()
        self.remove_dynamic_actor()
        super().remove_actor_from_world()

    def add_static_actor(self):
        if self.actor not in self.world.static_actors_dict[self.actor.position]:
            self.world.static_actors_dict[self.actor.position].append(self.actor)
            self.world.reload_costumes_queue.append(self.actor)

    def remove_static_actor(self):
        if (
            self.actor.position in self.world.static_actors_dict
            and self.actor in self.world.static_actors_dict[self.actor.position]
        ):
            self.world.static_actors_dict[self.actor.position].remove(self.actor)

    def set_static(self, value):
        super().set_static(value)
        if self.actor._static:
            self.add_static_actor()
        else:
            self.remove_static_actor()
