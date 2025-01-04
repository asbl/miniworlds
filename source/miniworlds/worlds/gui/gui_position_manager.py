import math
import pygame
from typing import Tuple, Union

import miniworlds.worlds.manager.position_manager as actor_position_manager
import miniworlds.worlds.tiled_world.tiled_world as tiled_world
import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.gui.gui as gui

class GUIPositionManager(actor_position_manager.Positionmanager):
    def __init__(
        self,
        actor: "actor_mod.Actor",
        world: "gui.GUI",
        position: [int, int],
    ):
        super().__init__(actor, world, position)
        self._origin = "topleft"
