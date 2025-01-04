from typing import Optional, Union, Callable
import miniworlds.actors.actor as actor_mod
import miniworlds.tools.method_caller as method_caller
import miniworlds.tools.inspection as inspection


class ActorInspection(inspection.Inspection):

    def call_instance_method(self, method: Callable, args: Optional[Union[tuple, list]], allow_none=True):
        # Don't call method if actors are already removed:
        method = getattr(self.instance, method.__name__)
        if issubclass(self.instance.__class__, actor_mod.Actor) and not self.instance.world:
            return
        method_caller.check_signature(method, args, allow_none)
        if not args :
            method()
        else:
            method(*args)
