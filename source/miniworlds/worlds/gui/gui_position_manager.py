import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.manager.position_manager as actor_position_manager
import miniworlds.worlds.gui.gui as gui


class GUIPositionManager(actor_position_manager.Positionmanager):
    def __init__(
        self,
        actor: "actor_mod.Actor",
        world: "gui.GUI",
        position: [int, int],
    ) -> None:
        super().__init__(actor, world, position)
        self._origin = "topleft"
