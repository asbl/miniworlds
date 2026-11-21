"""Reusable pixel-world actors with explicit reset and lifetime ownership."""


class ActorPool:
    def __init__(self, factory, initial_size=0, max_size=None, reset=None):
        from miniworlds.actors.actor import Actor
        if not callable(factory) or (reset is not None and not callable(reset)):
            raise TypeError("factory and reset must be callable")
        for name, value in (("initial_size", initial_size), ("max_size", max_size)):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ValueError(f"{name} must be a non-negative integer")
        if max_size is not None and initial_size > max_size:
            raise ValueError("initial_size exceeds max_size")
        self.factory, self.reset, self.max_size = factory, reset, max_size
        self._available = []
        self._owned = set()
        self._in_use = set()
        self._actor_type = Actor
        for _ in range(initial_size):
            self._available.append(self._create())

    def _create(self):
        actor = self.factory()
        if not isinstance(actor, self._actor_type):
            raise TypeError("factory must return an Actor")
        if actor in self._owned:
            raise ValueError("factory must return a new Actor for each pool slot")
        actor.active = False
        self._owned.add(actor)
        return actor

    @property
    def available(self):
        return len(self._available)

    @property
    def in_use(self):
        return frozenset(self._in_use)

    def acquire(self, position=None, **state):
        """Activate a reset actor; return None if the configured capacity is exhausted."""
        if self._available:
            actor = self._available.pop()
        elif self.max_size is not None and len(self._owned) >= self.max_size:
            return None
        else:
            actor = self._create()
        try:
            if position is not None:
                actor.position = position
            if self.reset is not None:
                self.reset(actor, **state)
            elif state:
                raise TypeError("state requires a reset callback")
            actor.active = True
        except BaseException:
            if actor.active:
                actor.active = False
            self._cancel_bound_timers(actor)
            self._available.append(actor)
            raise
        self._in_use.add(actor)
        return actor

    def release(self, actor):
        if actor not in self._in_use:
            raise ValueError("actor is not active in this pool")
        actor.active = False
        self._cancel_bound_timers(actor)
        self._in_use.remove(actor)
        self._available.append(actor)

    @staticmethod
    def _cancel_bound_timers(actor):
        actor.world._timed_objects[:] = [timer for timer in actor.world._timed_objects
            if getattr(getattr(timer, "method", None), "__self__", None) is not actor]

    def clear(self):
        """Permanently remove all owned actors."""
        for actor in tuple(self._owned):
            actor.remove()
        self._available.clear()
        self._in_use.clear()
        self._owned.clear()
