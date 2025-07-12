from abc import ABC, ABCMeta
from typing import Set, Callable
from typing import Union, List, Tuple, Optional, cast, Type, TYPE_CHECKING
import pygame
import miniworlds.worlds.manager.world_connector as world_connector
import miniworlds.worlds.manager.event_manager as event_manager
import miniworlds.worlds.manager.camera_manager as world_camera_manager
import miniworlds.worlds.manager.mainloop_manager as mainloop_manager
import miniworlds.tools.world_inspection as world_inspection
import miniworlds.tools.actor_inspection as actor_inspection

class ActorWorldConnectorMeta(ABCMeta):
    """
    Why do we need a metaclass:

    the token should be added to a world, after __init__, even
    if __init__ was overwritten.
    """

    def __call__(
        cls, position: Optional[Tuple[float, float]] = (0, 0), *args, **kwargs
    ):
        instance = type.__call__(cls, position, *args, **kwargs)  # create a new Token
        world_connector = instance.world.get_world_connector(instance)
        world_connector.add_to_world(position)
        return instance


class ActorBase(pygame.sprite.DirtySprite, metaclass=ActorWorldConnectorMeta):
    @property
    def dirty(self) -> int:
        """If actor is dirty, it will be repainted.

        Returns:

            int: 1 if actor is dirty/0 otherwise
        """
        return self._dirty

    @dirty.setter
    def dirty(self, value: int):
        if (
            self.position_manager
            and self.world
            and self.world.camera
            and self._is_actor_repainted()
            and value == 1
        ):
            self._dirty = 1
        elif value == 0:
            self._dirty = 0
        else:
            pass

    def _is_actor_repainted(self) -> bool:
        return self.world.frame == 0 or self.world.camera.is_actor_in_view(self)

    def register(self, method: callable, force=False, name=None):
        """This method is used for the @register decorator. It adds a method to an object

        Args:
            method (callable): The method which should be added to the actor
            force: Should register forced, even if method is not handling a valid event?
            name: Registers method with specific name
        """
        if (not self.world.event_manager.can_register_to_actor(method) and not force):
            raise RegisterError(method.__name__, self)
        bound_method = actor_inspection.ActorInspection(self).bind_method(method, name)
        if method.__name__ == "on_setup" and not self._is_setup_completed:
            self.on_setup()
            self._is_setup_completed = True
        self.world.event_manager.register_event(method.__name__, self)
        return bound_method
            
    def register_message(self, *args, **kwargs):
        """
        Registers a method to an object to handle specific `on_message` events.

        This decorator links a method to a specific event message, triggering it
        automatically when the designated message is received.

        Examples:

            Example of two actors who are communicating.

            .. code-block::

                # Registering a method to trigger on a key-down event
                @player1.register_message("on_key_down")
                def on_key_down(self, keys):
                    if 'a' in keys:
                        self.move()
                        self.send_message("p1moved")

                # Registering a method to respond to the "p1moved" message
                @player2.register_message("p1moved")
                def follow(self, data):
                    print(move_towards(player1))

        Parameters:
            message (str): The specific message event this method will react to.
        """
        def decorator(method):
            if "method" in kwargs:                
                method = kwargs.pop("method")
                name = kwargs.pop("name")
            bound_method = actor_inspection.ActorInspection(self).bind_method(method, method.__name__)
            self.world.event_manager.register_message_event(method.__name__, self, args[0])
            return bound_method
        return decorator

    @property
    def rect(self) -> pygame.Rect:
        """The surrounding Rectangle as pygame.Rect. The rect coordinates describes the local coordinates and depend on the camera view.
        
        Warning: 
            If the actor is rotated, the rect vertices are not the vertices of the actor image.
        """
        return self.position_manager.get_local_rect()


    def __str__(self):
        try:
            if (
                self.world
                and hasattr(self, "position_manager")
                and self.position_manager
            ):
                return f"**Actor of type [{ self.__class__.__name__}]: ID: { self.actor_id} at pos {self.position} with size {self.size}**"
            else:
                return  f"**Actor of type [{ self.__class__.__name__}]: ID: { self.actor_id}**"
        except Exception:
            return f"**Actor: {self.__class__.__name__}**"

    def get_costume_class(self) -> type["costume_mod.Costume"]:
        return self.world.get_world_connector(self).get_actor_costume_class()


    @property
    def position_manager(self):
        try:
            return self._position_manager
        except AttributeError:
            raise MissingPositionManager(self)

    @property
    def sensor_manager(self):
        try:
            return self._sensor_manager
        except AttributeError:
            raise Missingworldsensor(self)

    @property
    def costume_manager(self):
        return self._costume_manager
