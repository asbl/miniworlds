import miniworlds.tools.method_caller as method_caller
import miniworlds.worlds.manager.collision_event_view as collision_event_view
from miniworlds.worlds.manager.event_sensor_dispatcher import EventSensorDispatcher


class CollisionManager:
    """The class handles all collisions of actors.

    The method ``_handle_all_collisions`` is called every frame (in World.update())
    """

    def __init__(self, world):
        self.world = world

    def _get_event_view(self) -> collision_event_view.CollisionEventView:
        event_manager = self.world.event_manager
        if hasattr(event_manager, "get_collision_event_view"):
            return event_manager.get_collision_event_view()
        return collision_event_view.CollisionEventView(event_manager)

    def _handle_all_collisions(self):
        self._handle_actor_detecting_actor_methods()
        self._handle_actor_not_detecting_actor_methods()
        self._handle_actor_detecting_border_methods()
        self._handle_actor_detecting_on_the_world_methods()
        self._handle_actor_detecting_not_on_the_world_methods()
        self._handle_sensor_events()

    def _handle_sensor_events(self):
        """
        Handles all 'sensor' events for actors.

        Iterates through all registered 'sensor' event handlers in the world and 
        calls the corresponding method if the actor's sensor manager detects 
        another actor matching the event's filter target.
        """
        EventSensorDispatcher(self._get_event_view()).dispatch()

    def _handle_on_detecting_all_actors(self, actor, method):
        """
        Calls the given method for each actor detected by the given actor's sensor.

        Ensures that:
        - The actor does not respond to detecting itself.
        - All detected actors are passed to the method along with their class.

        Args:
            actor: The actor performing the detection.
            method: The method to call for each detected actor.
        """
        # Detect all actors in range (no filter)
        found_actors = actor.sensor_manager.detect_actors(filter=None) or []

        # Avoid detecting self
        if actor in found_actors:
            found_actors.remove(actor)

        # Call method for each detected actor
        for target in found_actors:
            method_caller.call_method(method, target, target.__class__)


    def _handle_on_detecting_actors_by_filter(self, actor, method, actor_type_name):
        """
        Calls the given method for each detected actor of a specific type,
        excluding the detecting actor itself.

        Args:
            actor: The actor performing the detection.
            method: The method to be called on detection.
            actor_type_name: The name of the actor class (as string) to filter detection.
        """
        # Detect actors of the given type
        found_actors = actor.sensor_manager.detect_actors(filter=actor_type_name) or []

        # Exclude self from detection results
        if actor in found_actors:
            found_actors.remove(actor)

        for target in found_actors:
            method_caller.call_method(method, target, target.__class__)

    def _handle_actor_detecting_actor_methods(self):
        """
        Handles all 'on_detecting' event methods for actors, including both
        general detection and filtered detection by specific actor types.

        This includes:
        - Methods named 'on_detecting' (i.e., detect all other actors)
        - Methods named like 'on_detecting_<target>' (i.e., filtered detection)
        """
        for event, methods in self._get_event_view().iter_registered_methods("on_detecting"):
            for method in methods:
                actor = method.__self__
                method_name_parts = method.__name__.split("_")

                if method.__name__ == "on_detecting":
                    self._handle_on_detecting_all_actors(actor, method)
                    continue

                # Expecting method name format like "on_detecting_<target>"
                if len(method_name_parts) == 3:
                    target_actor_type = method_name_parts[2]
                    self._handle_on_detecting_actors_by_filter(actor, method, target_actor_type)


    def _handle_actor_not_detecting_actor_methods(self):
        """
        Handles 'on_not_detecting_<actor_type>' methods. These methods are triggered
        when an actor does not detect any other actor of a specific type.

        Iterates over registered 'on_not_detecting' events and executes the corresponding
        method only if:
        - No actors of the specified type are detected.
        - OR only irrelevant actors (e.g., self) or unrelated subclasses are found.
        """
        for event, methods in self._get_event_view().iter_registered_methods("on_not_detecting"):
            for method in methods:
                actor = method.__self__
                method_name_parts = method.__name__.split("_")

                if len(method_name_parts) != 4:
                    continue  # Skip malformed method names

                actor_type = method_name_parts[3]
                found_actors = actor.sensor_manager.detect_actors(filter=actor_type)

                # If nothing found or only irrelevant matches (like self or unrelated subclasses)
                if not found_actors:
                    method_caller.call_method(method, None)
                    continue

                # Remove self if present
                if actor in found_actors:
                    found_actors.remove(actor)

                if found_actors:
                    continue  # At least one valid actor is still present, don't call method

                # No relevant actor found
                method_caller.call_method(method, None)


    def _handle_actor_detecting_border_methods(self):
        """
        Handles actor methods that respond to border detection events.
        
        Iterates over all registered border-related methods. If the method name is
        'on_detecting_borders' and borders are detected, the method is called with 
        the detected borders. Otherwise, delegates to the more specific handler.
        """
        for event, methods in self._get_event_view().iter_registered_methods("border"):
            for method in methods:
                actor = method.__self__
                sensed_borders = actor.detect_borders()

                if method.__name__ == "on_detecting_borders":
                    if sensed_borders:
                        method_caller.call_method(method, (sensed_borders,))
                else:
                    self._handle_actor_sensing_specific_border_methods(method, sensed_borders)


    def _handle_actor_sensing_specific_border_methods(self, method, sensed_borders):
        for border in sensed_borders:
            if border in method.__name__:
                method_caller.call_method(method, None)

    def _handle_actor_detecting_on_the_world_methods(self):
        methods = self._get_event_view().copy_registered_methods("on_detecting_world")
        for method in methods:
            # get detect world method from actor
            is_inside_world = method.__self__.is_inside_world()
            # call listener if no world detected
            if is_inside_world:
                method_caller.call_method(method, None)
        del methods

    def _handle_actor_detecting_not_on_the_world_methods(self):
        methods = self._get_event_view().copy_registered_methods("on_not_detecting_world")
        for method in methods:
            # get detect world method from actor
            is_not_inside_world = not method.__self__.is_inside_world()
            # call listener if no world detected
            if is_not_inside_world:
                method_caller.call_method(method, None)
        del methods
