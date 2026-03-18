from typing import Any, Callable

def bind_method(instance: Any, method: Callable) -> Callable:
    """Binds a method to an instance and sets it as an attribute.
    
    Args:
        instance: The object to bind the method to.
        method: The unbound method to bind.
    
    Returns:
        The bound method.
    """
    bound_method = method.__get__(instance, instance.__class__)
    setattr(instance, method.__name__, bound_method)
    return bound_method