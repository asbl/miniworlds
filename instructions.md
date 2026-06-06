# Development Instructions

## Environment Setup

Use the project setup script from the repository root:

```sh
source prepare.sh
```

The script creates `venv` if needed, activates it, installs `requirements.txt`,
prepends `venv/bin` to `PATH`, and lists the available Invoke tasks.

If the shell was not prepared in the current session, call Invoke through the
venv explicitly:

```sh
venv/bin/invoke --list
```

The same setup is also available as Invoke tasks, which call `source prepare.sh`
internally:

```sh
venv/bin/invoke env.prepare
venv/bin/invoke env.check
```

Use `env.check` when a task needs the local Miniworlds and
`miniworlds_physics` imports to work outside Docker. It verifies the venv,
`pygame`, `pymunk`, `miniworlds`, and `miniworlds_physics` with the correct
`PYTHONPATH`.

## Tests

Always start Miniworlds tests through Invoke so they run inside the Docker
environment defined in `tasks.py`. Do not run `pytest` directly for validation,
including focused or single-file test runs.

The canonical test tasks run inside the Docker image configured by `tasks.py`.
Use these Docker tasks when evaluating test failures. In particular, visual
test output depends on the operating system, fonts, and rendering libraries, so
visual baselines must only be compared or updated from the Docker environment.
Do not accept or regenerate visual baselines from a direct local `pytest` run.

Run all unit tests:

```sh
venv/bin/invoke tests.unit
```

Run all visual tests:

```sh
venv/bin/invoke tests.visual
```

Run the full test suite and rebuild the Docker image first:

```sh
venv/bin/invoke tests.run
```

Run the full test suite against the current Docker image without rebuilding:

```sh
venv/bin/invoke tests.cached
```

Run the focused `miniworlds_physics` integration tests locally with the prepared
venv and the required `PYTHONPATH`:

```sh
venv/bin/invoke tests.physics
```

The equivalent legacy task names are also available:

```sh
venv/bin/invoke run-unit-tests
venv/bin/invoke run-visual-tests
venv/bin/invoke run-tests
venv/bin/invoke run-tests-cached
venv/bin/invoke run-physics-tests
```
