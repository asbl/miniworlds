# Events

Events are methods that Miniworlds calls automatically. Register them on a
`World` or an `Actor` with the `@...register` decorator.

## Main Loop

```python
@world.register
def on_setup(self):
    self.add_background((255, 255, 255))

@world.register
def act(self):
    print(self.frame)
```

`on_setup` runs once before the world starts. `act` runs once per frame while
the world is running.

## Keyboard

Use a specific key handler when you only care about one key:

```python
@player.register
def on_key_down_w(self):
    self.move_up()

@player.register
def on_key_pressed_space(self):
    self.y -= 2
```

Use a generic handler when you need to inspect the currently pressed keys:

```python
@player.register
def on_key_pressed(self, keys):
    if "a" in keys:
        self.move_left()
    if "d" in keys:
        self.move_right()
```

Keyboard events:

- `on_key_down(self, keys)`: once when a key is pressed
- `on_key_pressed(self, keys)`: every frame while a key is held
- `on_key_up(self, keys)`: when a key is released
- `on_key_down_<key>(self)`, `on_key_pressed_<key>(self)`,
  `on_key_up_<key>(self)`: key-specific handlers without a `keys` parameter

Common key names include `w`, `a`, `s`, `d`, `space`, `left`, `right`, `up`,
and `down`.

## Mouse

```python
@circle.register
def on_mouse_left(self, position):
    if self.detect_point(position):
        self.center = position

@circle.register
def on_clicked_left(self, position):
    self.color = (255, 0, 0)
```

Mouse events:

- `on_mouse_left(self, position)`, `on_mouse_right(self, position)`,
  `on_mouse_middle(self, position)`: while a button is held
- `on_mouse_left_down(self, position)`, `on_mouse_left_up(self, position)`:
  press and release events
- `on_mouse_motion(self, position)`: mouse movement
- `on_clicked(self, position)`, `on_clicked_left(self, position)`,
  `on_clicked_right(self, position)`: actor click events
- `on_mouse_over(self, position)`, `on_mouse_enter(self, position)`,
  `on_mouse_leave(self, position)`: actor hover events
- `on_wheel_up(self, position)`, `on_wheel_down(self, position)`: mouse wheel

## Sensors And Borders

```python
@player.register
def on_detecting_actor(self, other):
    print("touching", other)

@player.register
def on_not_detecting_world(self):
    self.remove()
```

Sensor and collision events:

- `on_detecting(self, other)`: any detected actor
- `on_detecting_actor(self, other)`: any actor on the same position
- `on_detecting_<ClassName>(self, other)`: actors of a specific class, for
  example `on_detecting_wall`
- `on_not_detecting(self)`: no actor detected
- `on_not_detecting_<ClassName>(self)`: no actor of that class detected
- `on_detecting_world(self)`: actor is inside the world
- `on_not_detecting_world(self)`: actor is outside the world
- `on_detecting_not_on_world(self)`: alias for `on_not_detecting_world`
- `on_detecting_borders(self, borders)`: receives a list like `["left"]`
- `on_detecting_left_border(self)`, `on_detecting_right_border(self)`,
  `on_detecting_top_border(self)`, `on_detecting_bottom_border(self)`

Both `on_not_detecting_world` and `on_detecting_not_on_world` are accepted.

## Messages

Messages are useful when actors should communicate without holding direct
references to each other.

```python
@button.register
def on_clicked_left(self, position):
    self.send_message("open_door")

@door.register_message("open_door")
def open(self, sender):
    self.switch_costume("open")
```

Use `send_message(message, data=None)` to broadcast a message. Use
`@actor.register_message("message")` or `@world.register_message("message")`
to react to it.

## Focus

Actors can react when they receive or lose focus after a click:

- `on_focus(self)`
- `on_focus_lost(self)`

