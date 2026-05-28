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

## Tests

The canonical test tasks run inside the Docker image configured by `tasks.py`.

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

The equivalent legacy task names are also available:

```sh
venv/bin/invoke run-unit-tests
venv/bin/invoke run-visual-tests
venv/bin/invoke run-tests
venv/bin/invoke run-tests-cached
```
