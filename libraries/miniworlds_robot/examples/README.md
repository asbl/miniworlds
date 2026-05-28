# Miniworlds Robot Examples

These examples are starter files for students. The complete versions live in
`../solutions`.

Run an example from the repository root with:

```bash
PYTHONPATH=libraries/miniworlds_robot/source:source python libraries/miniworlds_robot/examples/01_sequence.py
```

## Concepts

- `01_sequence.py`: commands run in order
- `02_variables.py`: values give names to decisions
- `03_functions.py`: repeated command groups become functions
- `04_loops.py`: loops repeat a known pattern
- `05_conditions.py`: `if` reacts to what the robot senses

Every file ends with `world.run()`. It returns `True` when the current world
matches the target configuration, otherwise `False`.

