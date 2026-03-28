# Development

## Setup development

1. Source `prepare.sh`

## Run tests

Run all tests with the canonical Docker path:

```sh
invoke run_tests
```

For repeated local development runs without rebuilding the image:

```sh
invoke run_tests_cached
```

If `invoke` is unavailable, run the equivalent Docker command from [tasks.py](tasks.py).

Run a single test:

Example:

```sh
pytest test/unittests/connectors/test_world_connector.py -v
```

Run a single visual test:

```sh
pytest test/visualtests/gui/test_610_toolbar_widgets.py -v
```

Unit tests are grouped by domain under `test/unittests/<area>/`.

## Docs

Upload new version to PyPI:

```sh
invoke release --version=3.5.0.1
invoke release --version=3.5.0.1 --dry-run
```

This task synchronizes the version in both packages, runs the Docker test suite,
creates the commits and tags in the main repository and the physics submodule,
and pushes branch plus tag so the GitHub PyPI workflows can publish both packages.
