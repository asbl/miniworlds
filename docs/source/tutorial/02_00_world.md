# The First World

In this section, we’ll create our first “world” in Miniworlds. A world is the basic building block for everything you want to see or control in your application — from a simple game field to more complex worlds like those in video games. Let’s dive right in:

## Getting Started

To create a world, you only need a few lines of code:

```python
from miniworlds import World

# Create a new world with dimensions 600x300 pixels
world = World(600, 300)

# Start the world to display it
world.run()
```

### What happens in this code?

* **Import the library**: The first line imports the Miniworlds library, which provides all the necessary functions.
* **Create a world**: The method `miniworlds.World(600, 300)` creates a new world. This defines the world’s size: 600 pixels wide and 300 pixels tall.
* **Start the world**: `world.run()` starts the world and displays it on screen. You can think of this line like pressing “Play” — the world becomes visible only after this.

Take a look at the following image showing the first step:

![First miniworlds Example](../_images/01firstworld.png)

## Adding a Background

To avoid having an empty world, you can add an image as a background.
You’ll need an image saved in the `images` folder of your project.
Your project structure might look like this:

```
project/
├── my_world.py  # file with your python code
└── images/
    └── grass.png
```

Once you’ve placed your image (e.g., `grass.png`) in the `images` folder,
you can add it to your world using the `add_background` method:

```python
import miniworlds

# Create world
world = miniworlds.World(600, 300)

# Add image as background
world.add_background("images/grass.png")

# Start world
world.run()
```

![First miniworlds Example](../_images/pixel_addbackground.png)

### What’s happening here?

* The method `add_background("images/grass.png")` loads the image `grass.png` from the specified path
  and sets it as the background for your world.

\:::{note}

There are different types of `Worlds` in Miniworlds.
The `TiledWorld` is specifically designed for games using tiled layouts, such as top-down RPGs.

\:::

\:::{seealso}
[Concept: Naming and Variables](../concepts/concept_naming)
\:::

\:::{seealso}
[Concept: Imports](../concepts/concept_imports)
\:::
