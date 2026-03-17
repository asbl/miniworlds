# World

The base class for all of your worlds.

Use `world.send_message("name")` for simple broadcasts between the
world, actors, and docked GUI worlds.

For persistence, `world.save_to_db("game.db")` stores the current
scene and `world.load_world_from_db("game.db")` restores it again.

If you only want to restore actors, use
`world.load_actors_from_db(...)` with the actor classes that should be
recreated.

## API Reference

```{eval-rst}
.. autoclass:: miniworlds.worlds.world.World
   :members:

   .. autoclasstoc::
```
