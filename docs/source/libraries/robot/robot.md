# Robot

The `Robot` class is a restricted public facade for the internal actor.
Students interact with a `Robot` object rather than a full miniworlds `Actor`,
so the visible API is limited to the abilities defined in the current `WorldConfig`.

Attempting to call an ability that is not enabled for the current task raises
`AttributeError`, which gives the student clear feedback about what is allowed.

## Abilities

The default ability set is `{"step", "turn_left", "turn_right"}`.
The `"with_position"` config additionally grants `"position"`.
The `"leaf_line"` config additionally grants `"on_leaf"` and `"remove_leaf"`.

| Method / Property | Description |
|---|---|
| `step()` | Move one tile in the current heading. Does nothing if the tile is blocked. |
| `turn_left()` | Rotate 90 degrees counter-clockwise. |
| `turn_right()` | Rotate 90 degrees clockwise. |
| `on_leaf()` | Return `True` if there is a `Leaf` on the robot's current tile. |
| `remove_leaf()` | Remove one `Leaf` from the current tile; return `True` if successful. |
| `position` | Current `(column, row)` tile position (read-only). |

## API Reference

```{eval-rst}
.. autoclass:: miniworlds_robot.robot.Robot
   :members:
   :no-private-members:
```
