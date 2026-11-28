# miniworlds

**miniworlds** lets you create 2D mini worlds and games in Python: pixel-based
scenes, tile worlds (e.g. rogue-likes), hex boards and processing-style
graphics.

It is a 2D engine inspired by Greenfoot and gamegrid, based on Python 3 and
pygame-ce (pymunk for physics). **miniworlds** is the successor of
*[miniworldmaker][miniworldmaker]*.

[![PyPI version][badge-pypi]][pypi]

Requires Python 3.10 or newer.

## Contents

- [Features](#features)
- [Installation](#installation)
- [First program](#first-program)
- [Documentation](#documentation)
- [Tutorials](#tutorials)
- [Examples](#examples)
- [Where to find what](#where-to-find-what)
- [Sub-libraries](#sub-libraries)
- [Tools: browser editor, Thonny plugin, backend](#tools-browser-editor-thonny-plugin-backend)
- [This repository](#this-repository)
- [Development](#development)
- [License](#license)

## Features

- Pixel worlds, tile worlds (rogue-likes, jump'n'run) and hex worlds for
  board games
- Costumes, animations and processing-style drawing with shapes and
  pixel-level image processing
- Music and sound effects
- Built-in interface elements: console, toolbar, dialogs and widgets such as
  number displays, labels and buttons
- Camera scrolling, mouse and keyboard events, and a Greenfoot-like
  experimentation mode for IDEs
- Physics through the `miniworlds-physics` sub-library (pymunk)
- The same programs run on the desktop and in the browser (Pyodide), e.g. in
  [miniworlds-editor][editor]

## Installation

```sh
pip install miniworlds
```

Upgrade an existing installation:

```sh
pip install --upgrade miniworlds
```

`pygame-ce` and `numpy` are installed automatically. Optional add-ons such as
the robot, turtle, physics or data libraries are listed under
[Sub-libraries](#sub-libraries).

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

The images used above ship with the examples repository, see
[Examples](#examples). Larger programs are usually written class-based
(`class Player(miniworlds.Actor): ...`); both styles are supported and used
throughout the documentation.

Instead of `@actor.register` you can also define methods on a subclass:

```python
import miniworlds


class MyWorld(miniworlds.World):
    def on_setup(self):
        self.add_background("images/grass.jpg")
        Player(position=(90, 90))


class Player(miniworlds.Actor):
    def on_setup(self):
        self.add_costume("images/player.png")
        self.costume.orientation = -90

    def on_key_down_w(self):
        self.y = self.y - 1


world = MyWorld(400, 400)
world.run()
```

## Documentation

The documentation is bilingual; the German version is the default:

- German: <https://miniworldmaker.de/de/>
- English: <https://miniworldmaker.de/en/>

Reference:

- [World][api-world], [Actor][api-actor]
- [TiledWorld (tiles)][api-tiled], [HexWorld (hex boards)][api-hex],
  [physics worlds][api-physics]
- [Concepts for beginners][concept-imports]
- Guides: [drag & drop][g-drag], [scrolling][g-scrolling],
  [survivors-like][g-survivors], [maze (tiles)][g-maze],
  [Catan on a hex board][g-catan]

## Tutorials

- German step-by-step overview: <https://miniworldmaker.de/de/tutorial/>
- Hex worlds (board games like Catan): <https://miniworldmaker.de/en/tutorial/hex_world.html>
- Processing-style drawing: <https://miniworldmaker.de/de/processing/>
- First steps with the engine: <https://miniworldmaker.de/en/concepts/concept_imports.html>

The interactive German course ("Objects First") lives outside this repository
in the `course-sync` course folder; the German documentation links to it.

## Examples

The runnable examples live in a separate repository,
[asbl/miniworlds_examples][examples], with two styles per topic:
`objects_first` (short scripts) and `classes_first` (classes, one actor per
class). Snippets from the course are in `snippets`.

| Example | Preview | Source |
| --- | --- | --- |
| Top-down shooter | ![asteroids][img-asteroids] | [asteroids][ex-asteroids] |
| Tile-based RPG | ![rpg][img-rpg] | [rpg][ex-rpg] |
| Image processing (edges) | ![edges][img-edge] | [edge detection][ex-edge] |
| Physics sandbox | ![physics][img-physics] | [crazy machines][ex-crazy] |
| Joints | ![joints][img-joints] | [physics worlds][api-physics] |
| Angry-Birds-like | ![angry birds][img-angry] | [angry][ex-angry] |
| Hex boardgame | ![hex board][img-hex] | [hex tutorial][doc-hex] |

After a clone you can check out the examples into `libraries/examples` with
`git submodule update --init libraries/examples` (or clone with
`--recurse-submodules`). Other git-based workflows use
`invoke examples.checkout`.

## Where to find what

| I want to ... | Go to |
| --- | --- |
| read the manual | <https://miniworldmaker.de/en/> |
| follow a German tutorial | <https://miniworldmaker.de/de/tutorial/> |
| look up a class or method | [API reference][api-world] |
| see complete programs | [miniworlds_examples][examples] |
| learn tiles and hex boards | [TiledWorld][api-tiled], [HexWorld][api-hex] |
| use miniworlds in the browser | [miniworlds-editor][editor] |
| use miniworlds in Thonny | [thonny-miniworlds](libraries/thonny-miniworlds/README.md) |
| report a bug or ask a question | <https://github.com/asbl/miniworlds/issues> |
| work on the engine itself | [DEVELOP.md](DEVELOP.md) |

## Sub-libraries

Each library is optional and installed separately:

| Library | Install | Description |
| --- | --- | --- |
| [miniworlds-robot][lib-robot] | `pip install miniworlds-robot` | Grid robot for algorithmic thinking |
| [miniworlds-data][lib-data] | `pip install miniworlds-data` | Visual data structures (list, stack, tree) |
| [miniworlds-physics][lib-physics] | `pip install miniworlds-physics` | Physics simulation based on pymunk |
| [miniworlds-turtle][lib-turtle] | `pip install miniworlds-turtle` | Re-implementation of Python's `turtle` |

## Tools: browser editor, Thonny plugin, backend

### Browser editor: miniworlds-editor

**miniworlds-editor** is a static browser app (Pyodide, CodeMirror 6) for
writing and running miniworlds programs without any installation:

- Try it: <https://editor.opencoding.de/>
- Source: [asbl/miniworlds-editor][editor]
- Development, deployment and embedding: see its own README and `docs/`

How the editor and this engine fit together: each editor project pins an
engine version and installs it from PyPI (`micropip install
miniworlds==<version>`). Nothing in that build refers to this repository, so a
new engine release reaches the editor as soon as it is published to PyPI.
Editor features rely on stable engine interfaces: autocompletion and hints use
`miniworlds.tools.api_index`, `code_hints` and `class_model`; the Greenfoot-like
world view uses `ScenarioHost` (available from 4.4.0.15). Changes to those
interfaces should therefore be made compatible and mentioned in
[source/CHANGELOG.md](source/CHANGELOG.md).

### Optional classroom backend

For saving projects in class, project codes and administration there is a
separate, optional service: [asbl/miniworlds-editor-backend][backend]. It is
neither needed to run the editor nor part of this repository.

### Thonny plugin

A German learning plugin with E2/Q1 modes, project templates, event help,
media management and code checks is maintained in this repository under
[libraries/thonny-miniworlds](libraries/thonny-miniworlds/README.md).

## This repository

| Path | Content |
| --- | --- |
| `source/` | the Python package `miniworlds` and `CHANGELOG.md` |
| `docs/` | Sphinx sources of the documentation (German/English) |
| `libraries/` | Thonny plugin and optional sub-libraries as submodules |
| `test/` | unit, visual and browser (Pyodide) tests |
| `tasks.py` | Invoke tasks for tests, docs, release and Docker images |

The engine boundaries are documented in
[DEVELOP.md](DEVELOP.md#repository-boundaries): this checkout owns the Python
engine, its documentation and its desktop/Pyodide validation.

## Development

Everything runs through the Docker-based Invoke tasks, see
[DEVELOP.md](DEVELOP.md):

```sh
invoke tests.run        # all tests
invoke tests.unit       # unit tests only
invoke tests.visual     # rendering and behaviour tests
invoke build.docs       # build the documentation locally
```

## License

MIT, see [LICENSE.txt](LICENSE.txt). Media in the examples repository has its
own licenses, see there.

[miniworldmaker]: https://github.com/asbl/miniworldmaker
[examples]: https://github.com/asbl/miniworlds_examples
[editor]: https://github.com/asbl/miniworlds-editor
[backend]: https://github.com/asbl/miniworlds-editor-backend
[lib-robot]: https://github.com/asbl/miniworlds-robot
[lib-data]: https://github.com/asbl/miniworlds-data
[lib-physics]: https://github.com/asbl/miniworlds-physics
[lib-turtle]: https://github.com/asbl/miniworlds-turtle
[api-world]: https://miniworldmaker.de/en/api/world.html
[api-actor]: https://miniworldmaker.de/en/api/actor.html
[api-tiled]: https://miniworldmaker.de/en/api/world_tiled.html
[api-hex]: https://miniworldmaker.de/en/api/world_hex.html
[api-physics]: https://miniworldmaker.de/en/api/world_physics.html
[concept-imports]: https://miniworldmaker.de/en/concepts/concept_imports.html
[g-drag]: https://miniworldmaker.de/en/patterns/01_drag_and_drop.html
[g-scrolling]: https://miniworldmaker.de/en/patterns/02_scrolling.html
[g-survivors]: https://miniworldmaker.de/en/patterns/survivors.html
[g-maze]: https://miniworldmaker.de/en/patterns/maze_game.html
[g-catan]: https://miniworldmaker.de/en/patterns/hex_world_catan.html
[badge-pypi]: https://img.shields.io/pypi/v/miniworlds.svg
[pypi]: https://pypi.org/project/miniworlds/
[doc-hex]: https://miniworldmaker.de/en/tutorial/hex_world.html
[ex-asteroids]: https://github.com/asbl/miniworlds_examples/tree/main/classes_first/asteroids
[ex-rpg]: https://github.com/asbl/miniworlds_examples/tree/main/classes_first/rpg
[ex-edge]: https://github.com/asbl/miniworlds_examples/blob/main/processing/53_edge_detection.py
[ex-crazy]: https://github.com/asbl/miniworlds_examples/tree/main/classes_first/crazy_machines
[ex-angry]: https://github.com/asbl/miniworlds_examples/tree/main/classes_first/angry
[img-asteroids]: docs/source/_images/asteroids.png
[img-rpg]: docs/source/_images/examples_rpg.png
[img-edge]: docs/source/_images/sunflower9_edge.png
[img-physics]: docs/source/_images/physics_sim.png
[img-joints]: docs/source/_images/joints1.png
[img-angry]: docs/source/_images/angry_birds.png
[img-hex]: docs/source/_images/hexboard.png
