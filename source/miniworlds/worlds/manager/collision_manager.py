import miniworlds.tools.method_caller as method_caller
import miniworlds.tools.actor_class_inspection as actor_class_inspection


class CollisionManager:
    """The class handles all collisions of actors.

    The method ``handle_all_collisions`` is called every frame (in World.update())
    """

    def __init__(self, world):
        self.world = world

    def handle_all_collisions(self):
        self._handle_actor_detecting_actor_methods()
        self._handle_actor_not_detecting_actor_methods()
        self._handle_actor_detecting_border_methods()
        self._handle_actor_detecting_on_the_world_methods()
        self._handle_actor_detecting_not_on_the_world_methods()
        self._handle_sensor_events()

    def _handle_sensor_events(self):
        if self.world.event_manager.registry.registered_events["sensor"] == set():
            return
        for target, methods in self.world.event_manager.registry.registered_events[
            "sensor"
        ].items():
            for method in methods:
                actor = method.__self__
                if actor.sensor_manager.detect_actors(filter=target):
                    method_caller.call_method(method, (target,))

    def _handle_on_detecting_all_actors(self, actor, method):
        _all_found_actors = actor.sensor_manager.detect_actors(filter=None)
        if not _all_found_actors:  # found nothing
            _all_found_actors = []
        if actor in _all_found_actors:  # found self
            _all_found_actors.remove(actor)
        for found_actor in _all_found_actors:  # found other actor
            method_caller.call_method(method, found_actor, found_actor.__class__)

    def _handle_on_detecting_actors_by_filter(self, actor, method, actors):
        #  Get all actors which are colliding with actor
        _all_found_actors = actor.sensor_manager.detect_actors(filter=actors)
        if not _all_found_actors:  # found nothing
            _all_found_actors = []
        if actor in _all_found_actors:  # found self
            _all_found_actors.remove(actor)
        for found_actor in _all_found_actors:  # found other actor
            subclasses = (
                actor_class_inspection.ActorClassInspection.get_all_actor_classes()
            )
            if found_actor.__class__ in subclasses:
                method_caller.call_method(method, found_actor, found_actor.__class__)

    def _handle_actor_detecting_actor_methods(self):
        for event in self.world.event_manager.definition.class_events["on_detecting"]:
            registered_events_copy = list(
                self.world.event_manager.registry.registered_events[event].copy()
            )
            for method in registered_events_copy:
                actor = method.__self__
                if method.__name__ == "on_detecting":
                    self._handle_on_detecting_all_actors(actor, method)
                    continue
                elif len(method.__name__.split("_")) != 3:
                    continue
                else:
                    actors = method.__name__.split("_")[2]
                self._handle_on_detecting_actors_by_filter(actor, method, actors)
            del registered_events_copy

    def _handle_actor_not_detecting_actor_methods(self):
        for event in self.world.event_manager.definition.class_events[
            "on_not_detecting"
        ]:  # first level
            for method in self.world.event_manager.registry.registered_events[
                event
            ].copy():  # concrete method
                actor = method.__self__
                if len(method.__name__.split("_")) != 4:
                    return
                else:
                    actor_type_of_target = method.__name__.split("_")[3]
                found_actors_for_actor_type = actor.sensor_manager.detect_actors(
                    filter=actor_type_of_target
                )
                if found_actors_for_actor_type:
                    method_caller.call_method(method, None)
                    continue
                if actor in found_actors_for_actor_type:
                    found_actors_for_actor_type.remove(actor)
                for found_actor in found_actors_for_actor_type:
                    subclasses = actor_class_inspection.ActorClassInspection(
                        actor
                    ).get_all_actor_classes()
                    if found_actor.__class__ in subclasses:
                        continue
                method_caller.call_method(method, None)
                del method

    def _handle_actor_detecting_border_methods(self):
        for event in self.world.event_manager.definition.class_events["border"]:
            for method in self.world.event_manager.registry.registered_events[event]:
                sensed_borders = method.__self__.detect_borders()
                if method.__name__ == "on_detecting_borders" and sensed_borders:
                    method_caller.call_method(method, (sensed_borders,))
                else:
                    self._handle_actor_sensing_specific_border_methods(
                        method, sensed_borders
                    )

    def _handle_actor_sensing_specific_border_methods(self, method, sensed_borders):
        for border in sensed_borders:
            if border in method.__name__:
                method_caller.call_method(method, None)

    def _handle_actor_detecting_on_the_world_methods(self):
        methods = (
            self.world.event_manager.registry.registered_events["on_detecting_world"]
            .copy()
            .union(
                self.world.event_manager.registry.registered_events["on_detecting_world"].copy()
            )
        )
        for method in methods:
            # get detect world method from actor
            is_on_the_world = method.__self__.detect_world()
            # call listener if no world detected
            if is_on_the_world:
                method_caller.call_method(method, None)
        del methods

    def _handle_actor_detecting_not_on_the_world_methods(self):
        methods = (
            self.world.event_manager.copy_registered_events("on_not_detecting_world")
            #.copy()
            #.union(
            #    self.world.event_manager.registered_events[
            #        "on_not_detecting_world"
            #    ].copy()
            #)
        )
        for method in methods:
            # get detect world method from actor
            is_not_in_the_world = not method.__self__.detect_world()
            # call listener if no world detected
            if is_not_in_the_world:
                method_caller.call_method(method, None)
        del methods
