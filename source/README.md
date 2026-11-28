# miniworlds

**miniworlds** lets you create 2D mini worlds and games in Python: pixel-based
scenes, tile worlds (e.g. rogue-likes), hex boards and processing-style
graphics.

It is a 2D engine inspired by Greenfoot and gamegrid, based on Python 3 and
pygame-ce (pymunk for physics). **miniworlds** is the successor of
*miniworldmaker*.

Requires Python 3.10 or newer.

## Installation

```sh
pip install miniworlds
```

`pygame-ce` and `numpy` are installed automatically.

## First program

Two actors that are controlled with the keyboard:

```python
from miniworlds import World, Actor

world = World(400, 400)
world.add_background("images/grass.jpg")

player = Actor((90, 90))
player.add_costume("images/player.png")
player.costume.orientation = -90

@player.register
def on_key_down_w(self):
    player.y = player.y - 1

player2 = Actor((180, 180))
player2.add_costume("images/player.png")
player2.costume.orientation = -90

@player2.register
def on_key_pressed_s(self):
    player2.y = player2.y - 1

world.run()
```

The images used above ship with the examples repository, see below.

## Documentation and tutorials

- Documentation (German default): <https://miniworldmaker.de/de/>
- Documentation (English): <https://miniworldmaker.de/en/>
- German tutorial overview: <https://miniworldmaker.de/de/tutorial/>
- Processing-style drawing: <https://miniworldmaker.de/de/processing/>
- Hex worlds: <https://miniworldmaker.de/en/tutorial/hex_world.html>
- Reference: <https://miniworldmaker.de/en/api/world.html>

## Examples

Runnable examples (both short scripts and class-based programs) live in
[asbl/miniworlds_examples](https://github.com/asbl/miniworlds_examples).

## Sub-libraries

| Library | Install |
| --- | --- |
| miniworlds-robot | `pip install miniworlds-robot` |
| miniworlds-data | `pip install miniworlds-data` |
| miniworlds-physics | `pip install miniworlds-physics` |
| miniworlds-turtle | `pip install miniworlds-turtle` |

## Browser editor

[miniworlds-editor](https://github.com/asbl/miniworlds-editor) is a browser
app that runs miniworlds programs without installation
(<https://editor.opencoding.de/>). Each editor project installs its engine
version from PyPI, so a released version becomes available there
automatically.

## Development

See [DEVELOP.md](https://github.com/asbl/miniworlds/blob/main/DEVELOP.md);
tests run through the Docker-based Invoke tasks:

```sh
invoke tests.run
invoke build.docs
```

## License

MIT, see
[LICENSE.txt](https://github.com/asbl/miniworlds/blob/main/LICENSE.txt).
Media in the examples repository has its own licenses.
