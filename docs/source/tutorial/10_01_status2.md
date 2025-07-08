## Stopping the Program

At the end of a game or during a level transition, certain actions often need to be performed —
like resetting the game field or pausing the game. The following commands are available for that purpose:

* **`world.stop()`**: Stops the world. No more actions will be executed and no events will be processed.
* **`world.start()`**: Resumes the game after a previous `stop()` command.
* **`world.is_running`**: A boolean variable you can use to check if the world is currently active.
* **`world.clear()`**: Removes all actors from the world.
* **`world.reset()`**: Clears the current world and re-creates it by calling everything defined in the `world.on_setup()` method.
