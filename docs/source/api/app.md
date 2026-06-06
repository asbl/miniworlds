# App

`App` manages the pygame window and the active worlds. Most beginner projects
do not need to create an `App` directly because `world.run()` starts the default
application loop.

Use `App` only when you intentionally manage more than one world or need direct
control over the application lifecycle.

## API Reference

```{eval-rst}
.. autoclass:: miniworlds.base.app.App
   :members:
```

