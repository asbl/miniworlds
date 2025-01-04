from typing import Union, Tuple


import miniworlds.worlds.world as world
import miniworlds.worlds.gui.gui_connector as gui_connector


class GUI(world.World):

    @staticmethod
    def _get_world_connector_class():
        return gui_connector.GUIConnector

    def add(self, actor):
        actor.world = self
        return actor
