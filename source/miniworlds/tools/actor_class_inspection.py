import inspect
from typing import Union, Type

import miniworlds.actors.actor as actor_mod
import miniworlds.worlds.world as world_mod



class ActorClassInspection:
    def __init__(self, generator):
        """Inspects a actor or a actor class

        Args:
            generator: A instance of actor or a actor class
        """
        if not inspect.isclass(generator):
            if isinstance(generator, world_mod.World):
                self.instance = generator.actors.get_sprite(0)
                self.actor_class = generator.actors.get_sprite(0).__class__
            else:
                self.instance = generator
                self.actor_class = generator.__class__
        else:
            self.actor_class = generator

    def get_class_methods_starting_with(self, string):
        methods = [
            method
            for method in dir(self.actor_class)
            if callable(getattr(self.actor_class, method)) and method.startswith(string)
        ]
        return methods

    @staticmethod
    def get_all_actor_classes():
        actor_parent_class = actor_mod.Actor
        return ActorClassInspection(actor_parent_class).get_subclasses_for_cls()

    def get_actor_parent_class(self):
        return actor_mod.Actor

    def get_subclasses_for_cls(self):
        def all_subclasses(cls):
            # __subclasses__() returns subclasses in definition order, so
            # walking it depth-first (instead of collecting into a set)
            # keeps that order: if two classes share a name (e.g. after a
            # script restart redefines a class), the more recently defined
            # one comes last and wins when callers build a name -> class
            # dict from this result.
            ordered = []
            for subclass in cls.__subclasses__():
                ordered.append(subclass)
                ordered.extend(all_subclasses(subclass))
            return ordered

        classes = [self.actor_class] + all_subclasses(self.actor_class)
        return list(dict.fromkeys(classes))

    def find_actor_class_by_classname(
        self, class_name: str
    ) -> Union[None, Type["actor_mod.Actor"]]:
        class_name = class_name.lower()
        match = None
        for actor_cls in self.get_all_actor_classes():
            if actor_cls.__name__.lower() == class_name:
                # Keep the last match: get_all_actor_classes() returns
                # classes in definition order, so if a name was redefined
                # (e.g. after a script restart), the most recently defined
                # class wins here too, consistent with how
                # EventDefinition.setup_event_list() resolves name clashes.
                match = actor_cls
        return match
