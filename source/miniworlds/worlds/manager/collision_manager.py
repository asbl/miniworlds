import miniworlds.tools.method_caller as method_caller
import miniworlds.worlds.manager.collision_event_view as collision_event_view
from miniworlds.worlds.manager.event_sensor_dispatcher import EventSensorDispatcher


class CollisionManager:
    """The class handles all collisions of actors.

    The method ``_handle_all_collisions`` is called every frame (in World.update())
    """

    def __init__(self, world):
        self.world = world
        # detect_actors(filter=None) results cached per actor for the duration
        # of one _handle_all_collisions call (once per frame).
        self._detect_cache = {}

    def _detected_actors(self, actor):
        """Unfiltered detect_actors result for this frame, cached per actor.

        Multiple handlers (on_detecting, on_detecting_<Type>,
        on_not_detecting_<Type>, sensor events) for the same actor derive
        their filtered lists from this cache instead of re-running the
        collision checks for every handler. The actor itself is held in the
        cache entry so the id-key cannot be recycled while cached.
        """
        key = id(actor)
        cached = self._detect_cache.get(key)
        if cached is None or cached[0] is not actor:
            result = actor.sensor_manager.detect_actors(filter=None) or []
            self._detect_cache[key] = (actor, result)
            return result
        return cached[1]

    def _detected_actors_filtered(self, actor, actor_filter):
        """Filtered view of the cached detection result.

        Equivalent to detect_actors(filter=actor_filter): the cached result
        already applied rect/collision-type checks to all candidates, so
        filtering it afterwards yields the same set.
        """
        sensor_manager = actor.sensor_manager
        filter_actors = getattr(sensor_manager, "filter_actors", None)
        if filter_actors is None:
            return sensor_manager.detect_actors(filter=actor_filter)
        return filter_actors(self._detected_actors(actor), actor_filter)

    def _get_event_view(self) -> collision_event_view.CollisionEventView:
        event_manager = self.world.event_manager
        if hasattr(event_manager, "get_collision_event_view"):
            return event_manager.get_collision_event_view()
        return collision_event_view.CollisionEventView(event_manager)

    def _handle_all_collisions(self):
        self._detect_cache = {}
        event_view = self._get_event_view()
        if event_view.has_group_methods("on_detecting"):
            self._handle_actor_detecting_actor_methods(event_view)
        if event_view.has_group_methods("on_not_detecting"):
            self._handle_actor_not_detecting_actor_methods(event_view)
        if event_view.has_group_methods("border"):
            self._handle_actor_detecting_border_methods(event_view)
        if event_view.has_event_methods("on_detecting_world"):
            self._handle_actor_detecting_on_the_world_methods(event_view)
        if (
            event_view.has_event_methods("on_not_detecting_world")
            or event_view.has_event_methods("on_detecting_not_on_world")
        ):
            self._handle_actor_detecting_not_on_the_world_methods(event_view)
        if event_view.has_sensor_methods():
            self._handle_sensor_events(event_view)

    def _handle_sensor_events(self, event_view=None):
        """
        Handles all 'sensor' events for actors.

        Iterates through all registered 'sensor' event handlers in the world and 
        calls the corresponding method if the actor's sensor manager detects 
        another actor matching the event's filter target.
        """
        dispatcher = EventSensorDispatcher(
            event_view or self._get_event_view(),
            detect=self._detected_actors_filtered,
        )
        dispatcher.dispatch()

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
        # Detect all actors in range (no filter), cached per frame
        found_actors = list(self._detected_actors(actor))

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
        # Detect actors of the given type (derived from the cached unfiltered result)
        found_actors = list(self._detected_actors_filtered(actor, actor_type_name))

        # Exclude self from detection results
        if actor in found_actors:
            found_actors.remove(actor)

        for target in found_actors:
            method_caller.call_method(method, target, target.__class__)

    def _handle_actor_detecting_actor_methods(self, event_view=None):
        """
        Handles all 'on_detecting' event methods for actors, including both
        general detection and filtered detection by specific actor types.

        This includes:
        - Methods named 'on_detecting' (i.e., detect all other actors)
        - Methods named like 'on_detecting_<target>' (i.e., filtered detection)
        """
        view = event_view or self._get_event_view()
        for event, methods in view.iter_registered_methods("on_detecting"):
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


    def _handle_actor_not_detecting_actor_methods(self, event_view=None):
        """
        Handles 'on_not_detecting_<actor_type>' methods. These methods are triggered
        when an actor does not detect any other actor of a specific type.

        Iterates over registered 'on_not_detecting' events and executes the corresponding
        method only if:
        - No actors of the specified type are detected.
        - OR only irrelevant actors (e.g., self) or unrelated subclasses are found.
        """
        view = event_view or self._get_event_view()
        for event, methods in view.iter_registered_methods("on_not_detecting"):
            for method in methods:
                actor = method.__self__
                method_name_parts = method.__name__.split("_")

                if len(method_name_parts) != 4:
                    continue  # Skip malformed method names

                actor_type = method_name_parts[3]
                found_actors = list(self._detected_actors_filtered(actor, actor_type))

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


    def _handle_actor_detecting_border_methods(self, event_view=None):
        """
        Handles actor methods that respond to border detection events.
        
        Iterates over all registered border-related methods. If the method name is
        'on_detecting_borders' and borders are detected, the method is called with 
        the detected borders. Otherwise, delegates to the more specific handler.
        """
        view = event_view or self._get_event_view()
        for event, methods in view.iter_registered_methods("border"):
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

    def _handle_actor_detecting_on_the_world_methods(self, event_view=None):
        view = event_view or self._get_event_view()
        methods = view.copy_registered_methods("on_detecting_world")
        for method in methods:
            # get detect world method from actor
            is_inside_world = method.__self__.is_inside_world()
            # call listener if no world detected
            if is_inside_world:
                method_caller.call_method(method, None)
        del methods

    def _handle_actor_detecting_not_on_the_world_methods(self, event_view=None):
        view = event_view or self._get_event_view()
        methods = view.copy_registered_methods(
            "on_not_detecting_world"
        ).union(view.copy_registered_methods("on_detecting_not_on_world"))
        for method in methods:
            # get detect world method from actor
            is_not_inside_world = not method.__self__.is_inside_world()
            # call listener if no world detected
            if is_not_inside_world:
                method_caller.call_method(method, None)
        del methods
