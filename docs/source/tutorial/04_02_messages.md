# Messages

## Sending Messages

With **`send_message(self, message)`**, you can send a message to all objects in your world.
These messages can be received and handled by other objects that are listening for that specific event.

### Example:

In this example, player 1 sends a message when they move:

```python
@player1.register
def on_key_down(self, keys):
    if 'a' in keys:
        self.move()  # Moves player1
        self.send_message("p1moved")  # Sends message "p1moved" to all
```

## Receiving Messages

You can register a handler for a message using the `@register_message("message")` decorator:

### Example:

In the following example, the message sent by player1 is received by player2.
Player2 then moves toward player1 whenever player1 moves.

```python
@player1.register
def on_key_down(self, keys):
    if 'a' in keys:
        self.move()  # Moves player1
        self.send_message("p1moved")  # Sends message "p1moved" to all

@player2.register_message("p1moved")  # Registers a handler for the "p1moved" message
def follow(self, data):  # The function name doesn't matter
    self.move_towards(player1)  # player2 moves toward player1
```

### Explanation:

* In this example, **player1** sends the message `"p1moved"` when the <kbd>A</kbd> key is pressed.
* **player2** has a method registered to listen for that message.
  As soon as **player1** moves, **player2** receives the message and moves toward **player1**.
