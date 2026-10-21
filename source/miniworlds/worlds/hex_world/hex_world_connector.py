import miniworlds.worlds.hex_world.hex_costume as hex_costume
import miniworlds.worlds.hex_world.hex_world_position_manager as hex_position_manager
import miniworlds.worlds.hex_world.hex_world_sensor_manager as hex_sensor_manager
import miniworlds.worlds.tiled_world.tiled_world_connector as tiled_world_connector


class HexWorldConnector(tiled_world_connector.TiledWorldConnector):
    """WorldConnector for hex worlds.

    Uses the hex position manager, the hex costume, and the hex sensor
    manager.
    """

    @staticmethod
    def get_position_manager_class():
        return hex_position_manager.HexWorldPositionManager

    @staticmethod
    def get_sensor_manager_class():
        return hex_sensor_manager.HexWorldSensorManager

    @staticmethod
    def get_actor_costume_class():
        return hex_costume.HexCostume
