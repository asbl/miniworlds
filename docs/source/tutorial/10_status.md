# Text and Numbers

## Score / Game Status

In many games, you’ll want to display the current score or other status indicators.

**Miniworlds** provides special actor types like **Text** and **Number** actors that help you display this information easily.

---

### Creating Text

To display text, you can use the following:

```python
text = miniworlds.Text(position, string)
```

* `position`: A tuple that defines the top-left corner of the text.
* `string`: The text to display.

\:::{note}
In a regular **World**, the text is automatically scaled.
In a **TiledWorld**, the text is shown inside a tile, which can cause space issues for longer text.
\:::

#### Example:

```python
import miniworlds 

world = miniworlds.World(400, 400)
hallo_welt = Text((100, 100), "Hello World!")

world.run()
```

<img src="../_images/text1.png" width=260px alt="Text example"/>

---

### Changing Text

You can update the displayed text at any time using the `text` attribute.

The following example shows the most recently pressed key:

```python
from miniworlds import World, Text

world = World(400, 400)
key_display = Text((100, 100), "")

@key_display.register
def on_key_down(self, key):
    print(key)
    self.text = key[0]  # Displays the first letter of the key pressed

world.run()
```

<img src="../_images/text2.png" width=260px alt="Text with key input"/>

---

## Displaying Numbers

To show numbers on screen, you can use **Number actors**.
They work similarly to text actors.
In the following example, the number increases by 1 every time a key is pressed:

```python
from miniworlds import World, Number

world = World(400, 400)
show_number = Number((100, 100), 1)

@show_number.register
def on_key_down(self, key):
    n = self.get_number()
    self.set_number(n + 1)

world.run()
```
