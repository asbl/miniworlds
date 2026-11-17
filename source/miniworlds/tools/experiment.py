"""Backend-side object bank for IDE experiments; never import into an IDE UI."""
from uuid import uuid4


class ExperimentSession:
    """Bind object handles to one loaded program generation.

    Create a new session after each successful backend restart. Editor changes
    only update the source version; they never reload classes in living objects.
    All runtime operations must execute on the mainloop thread.
    """

    def __init__(self, world, source_version: str):
        self.world = world
        self.loaded_version = source_version
        self.source_version = source_version
        self.generation = uuid4().hex
        self._objects = {}
        self._next_id = 0
        self._closed = False
        self.world.pause()

    @property
    def is_stale(self) -> bool:
        return self.source_version != self.loaded_version

    def mark_source_changed(self, source_version: str) -> None:
        """Record an editor revision (for example a hash of project sources)."""
        self.source_version = source_version

    def register(self, obj) -> str:
        """Keep an object alive and return a handle unique to this session."""
        self._ensure_open()
        handle = f"{self.generation}:{self._next_id}"
        self._next_id += 1
        self._objects[handle] = obj
        return handle

    def release(self, handle: str) -> None:
        """Forget an object; its handle is never reused in this session."""
        self._objects.pop(handle, None)

    def resolve(self, handle: str):
        self._ensure_open()
        return self._objects[handle]

    def describe(self, handle: str) -> dict:
        obj = self.resolve(handle)
        return {
            "handle": handle,
            "type": type(obj).__name__,
            "generation": self.generation,
            "loaded_version": self.loaded_version,
            "source_version": self.source_version,
            "is_stale": self.is_stale,
        }

    def invoke(self, handle: str, method: str, *args, **kwargs):
        """Invoke an object method; errors propagate to the IDE command handler."""
        return self.world.invoke(getattr(self.resolve(handle), method), *args, **kwargs)

    def close(self) -> None:
        """Invalidate every handle when the backend is stopped or replaced."""
        self._objects.clear()
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Experiment session has ended; create a new session")
