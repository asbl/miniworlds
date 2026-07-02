# ListWorld

`ListWorld` visualizes a list of numeric values as a row of vertical bars.
Each bar's height is proportional to its value. Use it to animate sorting and
search algorithms step by step.

## Operations

| Method | Description |
|---|---|
| `compare(i, j)` | Highlight cells `i` and `j` with the `compare` state; return `True` if `values[i] > values[j]`. |
| `swap(i, j)` | Swap the values of cells `i` and `j`; both are colored with `swap` during the operation. |
| `highlight(index, state)` | Color one cell with a named state (default: `"compare"`). |
| `mark_sorted(index)` | Mark a cell as having reached its final sorted position (`"sorted"` state). |
| `reset_color(index)` | Reset one cell back to `"default"`. |
| `reset_all()` | Reset every cell to `"default"`. |
| `set_value(index, value)` | Change a cell's value and relayout all bars. |
| `values` | `list[int \| float]`: current values left-to-right (property). |
| `length` | Number of cells (property). |
| `is_sorted()` | Return `True` when the values are non-decreasing. |

## Example

```python
from miniworlds_data import ListWorld

world = ListWorld([8, 3, 6, 1, 4])
world.compare(0, 1)     # highlight two cells yellow
world.swap(0, 1)        # swap their values
world.mark_sorted(4)    # mark the last position as done
world.run()
```

## API Reference

```{eval-rst}
.. py:class:: miniworlds_data.list_world.ListWorld(values=None, *, cell_width=50, bar_height=200, label_height=30, margin=10, background=(245, 245, 245, 255))

   Visualizes a list of numeric values as bars. The table above lists the
   public operations intended for lesson and algorithm examples.
```
