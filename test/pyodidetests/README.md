# Pyodide tests

This suite runs core miniworlds behavior in a real Pyodide browser runtime:

- pixel-world actor movement and costumes
- collision detection and actor removal
- tiled-world movement and detection
- event dispatch
- the asynchronous web mainloop and canvas rendering
- uploaded multi-file student projects with local imports and JSON data
- relative, extensionless, missing, case-sensitive, and desktop-only asset paths
- project-validator warnings and errors relevant to browser export
- reset and reload behavior for uploaded assets
- nested Python packages and UTF-8 text files
- multiple-image costumes and animation setup
- timers, keyboard, mouse, and wheel events
- docked toolbars: clicking an input widget gives it focus, and typed
  text (TEXTINPUT events) reaches the focused widget
- screenshots written to Pyodide's virtual filesystem
- missing sound files and their error behavior

Run it from the repository root:

```sh
invoke tests.pyodide
```

The runner requires Python, Chromium, and network access to the pinned Pyodide
CDN. To use a local Pyodide distribution instead:

```sh
python test/pyodidetests/run.py --pyodide-base=http://localhost:8000/
```

The same override can be set through `MINIWORLDS_PYODIDE_BASE`. A non-standard
Chromium binary can be selected with `--chromium` or `MINIWORLDS_CHROMIUM`.

Run the separate everyday performance suite in Pyodide:

```sh
invoke benchmarks.pyodide
```

It measures actor creation/removal, repeated world queries, message broadcasts,
rendered canvas frame updates, and the objects-first solar scene with 1000
orbiting circles. Compare these values only on the same machine and browser
version.

## Performance regression gate

```sh
invoke tests.pyodide-gate        # in Docker, used by CI
python test/pyodidetests/run.py --check
```

`--check` runs the performance suite and compares every measurement with
`performance_budget.json`. Budgets are ratios against a fixed pure-Python
calibration workload measured in the same run, reducing differences in CPU speed.
Rendering and browser overhead can still vary; the budget keeps generous headroom
against CI noise. Missing measurements and measurements without a budget fail the
gate, as do non-finite timings or invalid calibration results. The suite also
asserts that the web render path stays in dirty-rect mode (the 4.9 FPS
regression fixed in 4.3.1.8). After an intentional performance change, record a
new baseline with `python test/pyodidetests/run.py --write-budget` and review
the diff.
