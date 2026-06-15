# World > Dialogs

Every world has a built-in dialog service: `world.dialog`. Dialogs are
modal windows drawn over the world: while a dialog is open, the world
does not receive mouse or keyboard events.

There are four dialog types:

| Method                   | Purpose                       | Result for the callback          |
| ------------------------ | ----------------------------- | -------------------------------- |
| `world.dialog.msgbox`    | Show a message with OK button | `True` (or `None` on ESC)        |
| `world.dialog.ynbox`     | Ask a yes/no question         | `True` / `False` (`None` on ESC) |
| `world.dialog.choicebox` | Choose one item from a list   | the chosen text (`None` on ESC)  |
| `world.dialog.enterbox`  | Enter a line of text          | the text (`None` on cancel)      |

`world.dialog.alert` is an alias for `world.dialog.msgbox`.

## Dialogs do not block

Opening a dialog returns **immediately** — the program keeps running.
You receive the answer through a *callback function* that is called when
the dialog is closed:

```python
import miniworlds

world = miniworlds.World(400, 300)

def handle_answer(value):
    if value:
        print("Let's continue!")
    else:
        print("Stopped.")

@world.register
def on_key_down_q(self):
    world.dialog.ynbox("Do you want to continue?", "Question", callback=handle_answer)

world.run()
```

This will **not** work, because the dialog has not been answered yet when
the next line runs:

```{code-block} python
# Wrong: answer is a Dialog object, not the user's answer!
answer = world.dialog.ynbox("Continue?")
```

Cancelling a dialog with the ESC key always delivers `None` to the
callback — even for `ynbox` (so the possible results there are `True`,
`False` and `None`).

## Showing a message

```python
import miniworlds

world = miniworlds.World(400, 300)
world.dialog.msgbox("Welcome to miniworlds!", "Hello")
world.run()
```

The button label can be changed: `world.dialog.msgbox("Done", button="Weiter")`.

## Choosing from a list

```python
import miniworlds

world = miniworlds.World(400, 300)
label = miniworlds.Text((20, 20), "Press c to choose a color.")
label.font_size = 20

def set_color(value):
    if value is not None:
        label.text = f"You chose {value}"

@world.register
def on_key_down_c(self):
    world.dialog.choicebox(
        "Choose a color.",
        "Color",
        choices=["Red", "Green", "Blue", "Yellow"],
        callback=set_color,
    )

world.run()
```

Long lists scroll automatically (mouse wheel or arrow keys).

## Entering text

```python
import miniworlds

world = miniworlds.World(400, 300)
greeting = miniworlds.Text((20, 20), "Press n to enter your name.")
greeting.font_size = 20

def set_name(value):
    if value is not None:
        greeting.text = f"Hello, {value}!"

@world.register
def on_key_down_n(self):
    world.dialog.enterbox("What is your name?", "Name", default="Ada", callback=set_name)

world.run()
```

The input field supports a text cursor (arrow keys, Home/End, Delete,
Backspace) and international characters.

## Pausing the world

By default the world keeps running behind a dialog: actors keep acting,
timers keep ticking. Pass `pause=True` to stop the world's logic while
the dialog is open; it resumes automatically when the dialog closes:

```python
import miniworlds

world = miniworlds.World(400, 300)
player = miniworlds.Circle((50, 150), 20)

@player.register
def act(self):
    self.x += 2

def handle_answer(value):
    if not value:
        world.quit()

@world.register
def on_key_down_p(self):
    world.dialog.ynbox("Keep playing?", "Pause", callback=handle_answer, pause=True)

world.run()
```

## Chaining dialogs

To ask several questions in a row, open the next dialog inside the
callback of the previous one:

```python
import miniworlds

world = miniworlds.World(400, 300)
result = miniworlds.Text((20, 20), " ")
result.font_size = 20

def show_player(value):
    if value is not None:
        result.text = f"Player color: {value}"

def ask_color(name):
    if name is None:
        return
    world.dialog.choicebox(
        f"Choose a color for {name}.",
        choices=["Red", "Green", "Blue"],
        callback=show_player,
    )

@world.register
def on_key_down_s(self):
    world.dialog.enterbox("What is the player's name?", default="Ada", callback=ask_color)

world.run()
```

## Keyboard controls

While a dialog is open:

- `TAB` / `UP` / `DOWN` move the button focus (`LEFT` / `RIGHT` too,
  except in text dialogs, where they move the text cursor)
- `RETURN` activates the focused button
- `ESC` cancels the dialog (result `None`)
- The mouse wheel scrolls long choice lists

## API Reference

```{eval-rst}
.. autoclass:: miniworlds.worlds.dialog.DialogService
   :members:
```

```{eval-rst}
.. autoclass:: miniworlds.worlds.dialog.Dialog
   :members: close
```
