# Stepper

`Stepper` drives a generator-based algorithm one visible step per frame.

Classical algorithms written as loops run to completion within a single frame,
so their intermediate states are never visible on screen. `Stepper` solves this by
letting the algorithm be written as a *generator* that `yield`s once per step;
the stepper advances it frame by frame (or on demand).

Each yielded value is a `(name, payload)` step tuple. The stepper records every step
so it can replay them forward and backward.

## Forward / backward navigation

```python
stepper.next_step()        # advance one step
stepper.prev_step()        # undo one step (requires on_reset callback)
stepper.reset()            # rewind to the start
stepper.goto(i)            # jump to step i (negative = rewind to start)
```

Backward navigation re-applies all steps from 0 to the target index using
the `on_reset` callback followed by sequential `on_step` calls, because
algorithm steps (like "swap") are not idempotent.

## Automatic frame-based driving

```python
stepper.run(world)         # register an act hook; advances one step per frame
stepper.on_frame()         # call from your own act hook
```

## Complete example

```python
from miniworlds_data import ListWorld, Stepper

world = ListWorld([5, 2, 4, 1, 3])
initial = list(world.values)

def bubble_sort(data):
    n = len(data.values)
    for i in range(n):
        for j in range(n - i - 1):
            yield "compare", (j, j + 1)
            if data.values[j] > data.values[j + 1]:
                yield "swap", (j, j + 1)
        yield "sorted", n - 1 - i

def apply_step(step):
    name, payload = step
    if name == "compare":
        world.compare(*payload)
    elif name == "swap":
        world.swap(*payload)
    elif name == "sorted":
        world.mark_sorted(payload)

def on_reset():
    for i, v in enumerate(initial):
        world.set_value(i, v)
    world.reset_all()

stepper = Stepper(
    bubble_sort(world),
    world,
    on_step=apply_step,
    on_reset=on_reset,
    frames_per_step=10,    # slow down: one step every 10 frames
)
stepper.run()
world.run()
```

## Constructor parameters

| Parameter | Description |
|---|---|
| `algorithm` | Generator that yields `(name, payload)` step tuples. |
| `world` | World to register the `act` hook on when `run()` is called. |
| `on_step` | Callback `(step) -> None` called when a step is applied. |
| `on_reset` | Callback `() -> None` that restores the visualization to its initial state. Required for backward navigation. |
| `frames_per_step` | Advance one step every N frames (default: 1). |

## Properties

| Property | Description |
|---|---|
| `steps` | All steps recorded so far, in execution order. |
| `step_index` | Index of the currently applied step (`-1` before the first step). |
| `finished` | `True` once the generator has been exhausted. |
| `auto_advance` | `True` after `run()` has been called. |

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_data.stepper.Stepper
   :members:
   :no-private-members:
```
