import miniworlds.worlds.gui.gui_position_manager as gui_position_manager
import miniworlds.worlds.manager.world_connector as world_connector


class GUIConnector(world_connector.WorldConnector):
    def __init__(self, world, actor):
        super().__init__(world, actor)

    @staticmethod
    def get_position_manager_class():
        return gui_position_manager.GUIPositionManager
