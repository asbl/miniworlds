# Timers

With **timers**, you can execute events **with a delay**.
This means an action doesn’t happen immediately, but after a specified delay in milliseconds or frames.

Timers are useful, for example, if you want something to happen after a certain amount of time.

\:::{note}
Python’s `time` library offers the function `time.sleep(...)` to create delays.
However, you should **not** use it here, as it causes global pauses and may lead to unwanted side effects.
\:::

---

## Starting a Timer

To start a timer, you can use the following example:

```python
from miniworlds import ActionTimer
[...]
ActionTimer(24, player.move)
```

### Explanation

1. After 24 frames, the timer is triggered.
2. The method `player.move` is then executed.

---

## Different Timer Types

There are different types of timers, depending on your use case:

### ActionTimer

The **ActionTimer** executes a method once after a set amount of time, then removes itself automatically.
It’s ideal for one-time delayed actions.

```python
ActionTimer(24, player.move, None)
```

In this example, the `move` function of the `player` object is executed once after 24 frames.

---

### LoopActionTimer

The **LoopActionTimer** works similarly to the ActionTimer but repeats the action at regular intervals.
It’s ideal for actions that should occur continuously.

```python
LoopActionTimer(24, player.move)
```

Here, the `move` method of the `player` will be executed every 24 frames.

To stop a `LoopActionTimer`, you can unregister it:

```python
loopactiontimer = LoopActionTimer(24, player.move)
...
loopactiontimer.unregister()  # Stops the LoopActionTimer
```

---

## Linking Timers to Events

Just like with sensors, you can configure timers to trigger methods at specific times.
To do this, register methods that should be executed on a timer event.

Example of a one-time timer event:

```python
@timer(frames=24)
def moving():
    player.move()
```

In this case, the `moving` function is executed once after 24 frames, triggering `player.move()`.

To register a **looping timer** that repeats regularly, use:

```python
@loop(frames=48)
def moving():
    player.turn_left()
    player.move(2)
```

Here, the `moving` method is called every 48 frames, turning the actor left and moving it forward.
