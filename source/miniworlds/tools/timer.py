import miniworlds.base.app as app
import miniworlds.tools.method_caller as method_caller


class Timed():
    """Base class for all timer objects.

    Registered timers are ticked once per frame by the world's main loop.
    You normally use `ActionTimer` or `LoopActionTimer` (or their decorator
    shortcuts `@timer` and `@loop`) instead of subclassing `Timed` directly.
    """

    def __init__(self):
        self.world = app.App.get_running_world()
        self.world._timed_objects.append(self)
        self.running = True

    def tick(self):
        """Advances the timer by one frame.

        Subclasses override this method when they need special timing logic.
        """
        self.time = self.time - 1

    def unregister(self):
        """Removes the timer from the current world.

        Use this to stop a running timer before it fires again.
        """
        if self in self.world._timed_objects:
            self.world._timed_objects.remove(self)
        del (self)


class Timer(Timed):
    """Timer that calls `act()` repeatedly after a frame interval.

    Subclass this and override `act()` when you need custom timer logic. For
    most use-cases prefer `ActionTimer` or the `@timer` decorator.

    Args:
        time: Frame interval.

    Examples:
        ::

            class BlinkTimer(Timer):
                def act(self):
                    actor.visible = not actor.visible
    """

    @staticmethod
    def _validate_interval(time: int) -> None:
        if not isinstance(time, int):
            raise TypeError(f"Timer interval must be int, got {type(time)}")
        if time <= 0:
            raise ValueError(f"Timer interval must be > 0, got {time}")

    def __init__(self, time: int):
        self._validate_interval(time)
        super().__init__()
        self.time = time
        self.actual_time = 0

    def tick(self):
        """Count frames and call `act()` when the interval is reached.

        This method is called automatically once per frame by the world.
        """
        self.actual_time += 1
        if self.actual_time % self.time == 0:
            self.act()

    def act(self):
        """Hook method that is executed when the timer interval is reached.

        Subclasses override this method with the action that should happen
        after the configured number of frames.
        """
        pass


class ActionTimer(Timer):
    """Calls a method after `time` frames.

    Args:
        time: Frames to wait before calling the method.
        method: Method to call.
        arguments: Optional single argument passed to the method.

    Examples:
        ::

            ActionTimer(48, player.move, 2)

            @timer(frames=24)
            def moving():
                player.move()
    """

    def __init__(self, time: int, method: callable, arguments=None):
        """Create a one-shot action timer.

        Args:
            time: Frames to wait before calling the method.
            method: Method to call.
            arguments: Optional single argument passed to the method.
        """
        super().__init__(time)
        self.method: callable = method
        if arguments or arguments == 0:
            self.arguments = [arguments]
        else:
            self.arguments = None

    def act(self):
        """Calls the stored method once and then unregisters the timer.

        This is the behavior behind `@timer` and one-shot delayed actions.
        """
        self._call_method()
        self.unregister()
        
    def _call_method(self):
        method_caller.call_method(self.method, self.arguments, allow_none=False)


class LoopActionTimer(ActionTimer):
    """Calls a method after `time` frames repeatedly until the timer is unregistered.

    Examples:
        ::

            LoopActionTimer(48, player.move, 2)

            @loop(frames=24)
            def moving():
                player.move()
    """

    def act(self):
        self._call_method()


def timer(*args, **kwargs):
    """Decorate a function to run once after a number of frames.

    Args:
        frames: Frames to wait before the function runs.

    Examples:
        ::

            @timer(frames=24)
            def moving():
                player.move()
    """

    def inner(method):
        timer = ActionTimer(kwargs["frames"], method)
        return timer

    return inner


def loop(*args, **kwargs):
    """Decorate a function to run repeatedly after a frame interval.

    Args:
        frames: Frames between function calls.

    Examples:
        ::

            @loop(frames=24)
            def moving():
                player.move()
    """

    def inner(method):
        timer = LoopActionTimer(kwargs["frames"], method)
        return timer

    return inner
