import inspect
import types
import functools
from typing import Any, Optional, Callable


class Inspection:

    def __init__(self, generator: Any) -> None:
        self.instance = generator

    def get_instance_method(self, name: str) -> Optional[Callable]:
        """If a (actor-)object has method this returns the method by a given name.
        
        Args:
            name: The name of the method to retrieve.
        
        Returns:
            The bound method, or None if not found or not callable.
        """
        if hasattr(self.instance, name):
            if callable(getattr(self.instance, name)):
                _method = getattr(self.instance, name)
                _bound_method = _method.__get__(self.instance, self.instance.__class__)
                return _bound_method
            else:
                return None
        else:
            return None

    def bind_method(self, method, name=None):
        bound_method = method.__get__(self.instance, self.instance.__class__)
        if name is None:
            setattr(self.instance, method.__name__, bound_method)
        else:
            setattr(self.instance, name, bound_method)
        return bound_method


    def unbind_method(self, method):
        delattr(self.instance, method.__name__, method)

    def get_and_call_method(self, name, args, errors=False):
        method = self.get_instance_method(name)
        if method:
            self.call_instance_method(method, args)
        elif errors:
            raise AttributeError(
                f"Method '{name}' not found on {type(self.instance).__name__}.\n"
                f"Did you remember to define `def {name}(self):` in your class?\n"
                f"Event methods must be named exactly: {name}\n"
                f"Hint: Check the spelling!"
            )
