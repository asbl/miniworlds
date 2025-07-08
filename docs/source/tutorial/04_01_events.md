# Events

## Make Your Game Interactive

In this section, you'll learn how to make your game interactive by responding to keyboard input, mouse actions, or collisions.

## What Are Events?

**Events** are the key to interactive games.
They allow your game to respond to user actions such as key presses or mouse movements, and dynamically change the behavior of your actors.

* **`on_setup()`**: Called at the beginning to initialize and prepare your world.
* **`act()`**: Called on every frame to update the world and its actors.
* There are special event methods like **`on_key_pressed`**, **`on_mouse_left`**, or **`on_clicked_left`** to respond to user actions.

## Registering Events

For an actor or the world to respond to an event, the corresponding method must be **registered** — just like with the `act()` method.

### Example: Simple Keyboard Input

```python
@player.register  # Registers the method as an event
def on_key_down_w(self):
    self.y -= 1  # Moves the player upward
```

#### Explanation:

This method is executed when the <kbd>w</kbd> key is pressed. The `player` actor moves up by one step.

## Example: Multi-Key Movement

In the next example, an actor is controlled using the <kbd>W</kbd>, <kbd>A</kbd>, <kbd>S</kbd>, and <kbd>D</kbd> keys:

```python
import miniworlds

world = miniworlds.TiledWorld()
world.columns = 20
world.rows = 8
world.tile_size = 42
world.add_background("images/soccer_green.jpg")

player = miniworlds.Actor()
player.add_costume("images/player_1.png")

@player.register
def on_key_down_w(self):
    self.y = self.y - 1  # Move actor up

@player.register
def on_key_down_a(self):
    self.x = self.x - 1  # Move actor left

@player.register
def on_key_down_d(self):
    self.x = self.x + 1  # Move actor right

@player.register
def on_key_down_s(self):
    self.y = self.y + 1  # Move actor down

world.run()
```

#### Explanation:

In this example, the actor is controlled as follows:

* <kbd>W</kbd>: Move up
* <kbd>A</kbd>: Move left
* <kbd>D</kbd>: Move right
* <kbd>S</kbd>: Move down

### Difference: `on_key_down` vs. `on_key_pressed`

There are two types of keyboard events for handling key input:

* **`on_key_down(self, key)`**: Called once when the key is initially pressed.
* **`on_key_pressed(self, key)`**: Continuously called while the key is being held down.

### Example: Different Keyboard Events

```python
import miniworlds 

world = miniworlds.World()
world.add_background("images/grass.jpg")

player = miniworlds.Actor((90, 90))
player.add_costume("images/player.png")
player.costume.orientation = -90 

@player.register
def on_key_down_w(self):
    self.y -= 1  # Moves player 1 upward

player2 = miniworlds.Actor((180, 180))
player2.add_costume("images/player.png")
player2.costume.orientation = -90 

@player2.register
def on_key_pressed_s(self):
    self.y -= 1  # Continuously moves player 2 downward while key is held

world.run()
```

```{note}
You can either define specific keys like `on_key_down_b(self)`  
or handle all key input using `on_key_down(self, key)` for general keyboard event handling.
```
