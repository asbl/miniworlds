# World

The base class for all of your worlds.

Use `world.send_message("name")` for simple broadcasts between the
world, actors, and docked GUI worlds.

For beginner classes, set `world.learning_mode = True`.
This enables soft conversions for common mistakes in selected public APIs
(for example bool-like strings such as `"yes"`/`"no"` in some flags, and
list positions where tuple positions are expected).

Useful beginner aliases on World include:

- `contains(...)` for `contains_position(...)`
- `broadcast(...)` for `send_message(...)`
- `actors_at(...)` for `detect_actors(...)`
- `set_bg(...)`, `add_bg(...)`, `next_bg()` for background helpers

## API Reference

```{eval-rst}
.. autoclass:: miniworlds.worlds.world.World
   :members:
```

## Exceptions

These exceptions are exported by `miniworlds` for code that wants to catch
specific Miniworlds errors. They are documented here but intentionally do not
have their own navigation entry.

```{eval-rst}
.. autoexception:: miniworlds.base.exceptions.CostumeOutOfBoundsError
   :members:

.. autoexception:: miniworlds.base.exceptions.OriginException
   :members:
```
