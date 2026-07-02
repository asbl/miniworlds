# miniworlds-data

**miniworlds-data** provides animated data-structure visualizations built on top of miniworlds.
Each world renders one data structure and exposes high-level operations so algorithm
implementations stay readable; the visualization is a side-effect of calling the operations.

## Installation

```bash
pip install miniworlds-data
```

## Color language

All data worlds share the same color vocabulary:

| State | Color | Meaning |
|---|---|---|
| `default` | blue-grey | idle / unsorted |
| `compare` | yellow | currently being compared |
| `swap` | red | about to be swapped |
| `sorted` | green | final position reached |
| `pivot` | purple | pivot / current key |
| `mark` | dark blue | arbitrary marker, for example min/max index |
| `visited` | green | already visited node |
| `current` | yellow | node being processed right now |
| `frontier` | purple | discovered but not yet processed |
| `start` | red | search origin |
| `target` | blue | search goal |
| `path` | green | path edges |

## Quick start: Bubble Sort

```python
from miniworlds_data import ListWorld, Stepper

initial = [5, 2, 4, 1, 3]
world = ListWorld(initial)

def bubble_sort(data):
    n = len(data.values)
    for i in range(n):
        for j in range(n - i - 1):
            yield "compare", (j, j + 1)
            if data.values[j] > data.values[j + 1]:
                yield "swap", (j, j + 1)
        data.mark_sorted(n - 1 - i)

def apply_step(step):
    name, payload = step
    if name == "compare":
        world.compare(*payload)
    elif name == "swap":
        world.swap(*payload)

def on_reset():
    for i, value in enumerate(initial):
        world.set_value(i, value)
    world.reset_all()

stepper = Stepper(bubble_sort(world), world, on_step=apply_step, on_reset=on_reset)
stepper.run()
world.run()
```

## API Reference

```{toctree}
---
maxdepth: 1
---
list_world
stack_world
queue_world
tree_world
graph_world
stepper
```
